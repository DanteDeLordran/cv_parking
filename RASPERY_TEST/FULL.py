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
from datetime import datetime
import threading
import asyncio
from cryptography.fernet import Fernet
import httpx

# Variables de configuración
SERVER_URL = 'http://10.100.34.159:12345/api/decision'  # URL del servidor
KEY = b'K_nMxEqBhZtE4Jyo-KkIrs24DSV5wGuuu1F7-s0urbY='

# Configuración de cifrado
cipher_suite = Fernet(KEY)

# Enviar datos al servidor
async def send_to_server(data):
    encrypted_data = cipher_suite.encrypt(data.encode('utf-8'))
    async with httpx.AsyncClient() as client:
        response = await client.post(SERVER_URL, json={"data": encrypted_data.decode()})
        print(response.json())

# Preparación de los modelos y configuración de la cámara
temp = pathlib.PosixPath
pathlib.PosixPath = pathlib.WindowsPath
sys.path.append(os.path.abspath('yolov5'))

modelo_placas = r'C:\Users\fervi\Documents\Visual Studio\Proyects\Estacionamiento\modelo_placas.pt'
model = torch.hub.load('ultralytics/yolov5', 'custom', path=modelo_placas, force_reload=False)
pathlib.PosixPath = temp

reader = easyocr.Reader(['es'], gpu=False)

raspberry_name = "TEST"
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
                response_time = current_time.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
                response = f"RASPBERRY_{self.raspberry_name}_CAM-{self.cam_number}_QR_{code}_{response_time}"
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
                    response_time = current_time.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
                    result_string = f"RASPBERRY_{self.raspberry_name}_CAM-{self.cam_number}_PLATES_{license_number}_{response_time}"
                    print(result_string)
                    await send_to_server(result_string)

                cv2.rectangle(frame, (bbox[0], bbox[1]), (bbox[2], bbox[3]), (0, 255, 0), 2)
                cv2.putText(frame, license_number, (bbox[0], bbox[1] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (36, 255, 12), 2)

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
