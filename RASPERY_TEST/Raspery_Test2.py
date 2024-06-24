import sys
import os
import torch
import cv2
import numpy as np
from PIL import Image
import pathlib
import time
import easyocr
from pyzbar.pyzbar import decode
from datetime import datetime, timedelta
import threading
import asyncio
from cryptography.fernet import Fernet
import httpx
import RPi.GPIO as GPIO
import json

# Variables de configuración
SERVER_URL = 'http://10.100.34.159:12345/api/decision'  # URL del servidor
KEY = b'K_nMxEqBhZtE4Jyo-KkIrs24DSV5wGuuu1F7-s0urbY='
raspberry_name = "TEST"

# Configuración de cifrado
cipher_suite = Fernet(KEY)

# Configuración de GPIO
BUTTON_OPEN_PIN = 17
BUTTON_EXIT_PIN = 27
SENSOR_EXIT_PIN = 22
RELAY_OPEN_PIN = 23  # Pin GPIO para controlar la apertura de la pluma
RELAY_CLOSE_PIN = 24  # Pin GPIO para controlar el cierre de la pluma

GPIO.setmode(GPIO.BCM)
GPIO.setup(BUTTON_OPEN_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(BUTTON_EXIT_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(SENSOR_EXIT_PIN, GPIO.IN)
GPIO.setup(RELAY_OPEN_PIN, GPIO.OUT)
GPIO.setup(RELAY_CLOSE_PIN, GPIO.OUT)

# Enviar datos al servidor
async def send_to_server(data):
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    data_with_info = f"RASPBERRY_{raspberry_name}_{data}_{current_time}"
    encrypted_data = cipher_suite.encrypt(data_with_info.encode('utf-8'))
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(SERVER_URL, json={"data": encrypted_data.decode()})
            print(response.json())
        except httpx.RequestError as exc:
            print(f"Error al enviar datos: {exc}")
            save_log_to_file(data_with_info)

# Guardar datos en archivo de logs
def save_log_to_file(data):
    with open('offline_logs.json', 'a') as log_file:
        json.dump({"timestamp": datetime.now().isoformat(), "data": data}, log_file)
        log_file.write('\n')

# Reenviar logs almacenados
async def resend_logs():
    if os.path.exists('offline_logs.json'):
        with open('offline_logs.json', 'r') as log_file:
            logs = log_file.readlines()
        for log in logs:
            log_entry = json.loads(log)
            await send_to_server(log_entry['data'])
        os.remove('offline_logs.json')

# Preparación de los modelos y configuración de la cámara
temp = pathlib.PosixPath
pathlib.PosixPath = pathlib.WindowsPath
sys.path.append(os.path.abspath('yolov5'))

modelo_placas = r'C:\Users\fervi\Documents\Visual Studio\Proyects\Estacionamiento\modelo_placas.pt'
model = torch.hub.load('ultralytics/yolov5', 'custom', path=modelo_placas, force_reload=False)
pathlib.PosixPath = temp

reader = easyocr.Reader(['es'], gpu=False)

camera_qr = 0  
camera_placas = 1  

last_detected_qr = {'code': None, 'timestamp': None}
last_detected_plate = {'license_number': None, 'timestamp': None}

class CameraThread(threading.Thread):
    def __init__(self, raspberry_name, cam_number, cam_type):
        super(CameraThread, self).__init__()
        self.raspberry_name = raspberry_name
        self.cam_number = cam_number
        self.cam_type = cam_type  
        self.running = False

    def run(self):
        self.running = True
        cap = cv2.VideoCapture(self.cam_number)
        if not cap.isOpened():
            print(f"Error: No se pudo acceder a la cámara {self.cam_number}")
            return
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        while self.running:
            ret, frame = cap.read()
            if not ret:
                print(f"Error: No se pudo leer el cuadro de la cámara {self.cam_number}")
                break

            # Conversión a escala de grises
            gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            frame = cv2.cvtColor(gray_frame, cv2.COLOR_GRAY2BGR)

            if self.cam_type == 'qr':
                loop.run_until_complete(self.process_qr(frame))
            elif self.cam_type == 'placas':
                loop.run_until_complete(self.process_placas(frame))
                
            cv2.imshow(f"Cámara {self.cam_number} ({self.cam_type})", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                self.running = False
                break

        cap.release()
        cv2.destroyAllWindows()
        loop.close()

    async def process_qr(self, frame):
        global last_detected_qr
        decoded = decode(frame)
        if decoded:
            code = decoded[0].data.decode('utf-8')
            current_time = datetime.now()
            if code != last_detected_qr['code'] or \
               (last_detected_qr['timestamp'] and (current_time - last_detected_qr['timestamp']).total_seconds() > 10):
                last_detected_qr['code'] = code
                last_detected_qr['timestamp'] = current_time
                response = f"CAM-{self.cam_number}_QR_{code}"
                print(response)
                await send_to_server(response)

    async def process_placas(self, frame):
        global last_detected_plate
        results = model(frame)

        for detection in results.pred[0]:
            conf = float(detection[4])
            if conf >= 0.8:  
                bbox = detection[:4].tolist()
                bbox = [int(coord) for coord in bbox]

                license_plate_crop = frame[bbox[1]:bbox[3], bbox[0]:bbox[2]]

                ocr_results = reader.readtext(license_plate_crop, detail=0, paragraph=False, batch_size=1)

                if ocr_results:
                    license_number = ocr_results[0].replace(' ', '').replace('-', '')
                else:
                    license_number = "UNKNOWN"

                license_number = license_number.upper()
                current_time = datetime.now()
                if license_number != last_detected_plate['license_number'] or \
                   (last_detected_plate['timestamp'] and (current_time - last_detected_plate['timestamp']).total_seconds() > 10):
                    last_detected_plate['license_number'] = license_number
                    last_detected_plate['timestamp'] = current_time
                    response = f"CAM-{self.cam_number}_PLATES_{license_number}"
                    print(response)
                    await send_to_server(response)

                cv2.rectangle(frame, (bbox[0], bbox[1]), (bbox[2], bbox[3]), (0, 255, 0), 2)
                cv2.putText(frame, license_number, (bbox[0], bbox[1] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (36, 255, 12), 2)

# Callback para botón de apertura manual
def button_open_callback(channel):
    print("Botón de apertura manual presionado")
    open_barrier()
    asyncio.run(send_to_server("Manual open"))

# Callback para botón de salida
def button_exit_callback(channel):
    print("Botón de salida presionado")
    close_barrier()
    asyncio.run(send_to_server("Manual exit"))

# Callback para sensor de salida
def sensor_exit_callback(channel):
    if GPIO.input(SENSOR_EXIT_PIN) == GPIO.HIGH:
        print("Coche detectado en la salida")
        close_barrier()
        asyncio.run(send_to_server("Car detected at exit"))

# Configurar interrupciones
GPIO.add_event_detect(BUTTON_OPEN_PIN, GPIO.FALLING, callback=button_open_callback, bouncetime=300)
GPIO.add_event_detect(BUTTON_EXIT_PIN, GPIO.FALLING, callback=button_exit_callback, bouncetime=300)
GPIO.add_event_detect(SENSOR_EXIT_PIN, GPIO.BOTH, callback=sensor_exit_callback, bouncetime=300)

def save_logs():
    while True:
        now = datetime.now()
        next_midnight = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        sleep_time = (next_midnight - now).total_seconds()
        time.sleep(sleep_time)
        print("Guardando logs del día")
        asyncio.run(send_to_server("Daily logs saved"))

# Iniciar el hilo de guardado de logs
log_thread = threading.Thread(target=save_logs)
log_thread.daemon = True
log_thread.start()

# Hilo para reenviar logs al reconectar
resend_thread = threading.Thread(target=lambda: asyncio.run(resend_logs()))
resend_thread.daemon = True
resend_thread.start()

# Iniciar los hilos de las cámaras
thread_qr = CameraThread(raspberry_name, camera_qr, 'qr')
thread_placas = CameraThread(raspberry_name, camera_placas, 'placas')

thread_qr.start()
thread_placas.start()

try:
    thread_qr.join()
    thread_placas.join()
except KeyboardInterrupt:
    thread_qr.running = False
    thread_placas.running = False
    thread_qr.join()
    thread_placas.join()
finally:
    GPIO.cleanup()

# Funciones para control de la pluma
def open_barrier():
    GPIO.output(RELAY_OPEN_PIN, GPIO.HIGH)
    time.sleep(1)  # Tiempo para mantener el relé activado
    GPIO.output(RELAY_OPEN_PIN, GPIO.LOW)
    print("Pluma abierta")

def close_barrier():
    GPIO.output(RELAY_CLOSE_PIN, GPIO.HIGH)
    time.sleep(1)  # Tiempo para mantener el relé activado
    GPIO.output(RELAY_CLOSE_PIN, GPIO.LOW)
    print("Pluma cerrada")
