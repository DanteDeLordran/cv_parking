import datetime as dt
import os
import pathlib
import sys
import threading
import time
import cv2
import easyocr
import numpy as np
import torch
from PIL import Image
from colorama import Fore
from pyzbar.pyzbar import decode
from ..app.main import get_all_employees_car_registry, get_employee_by_car_registry

# Temporarily override PosixPath for compatibility on Windows
temp = pathlib.PosixPath
pathlib.PosixPath = pathlib.WindowsPath

# Añadir el directorio de YOLOv5 al PYTHONPATH
sys.path.append(os.path.abspath('yolov5'))

# Cargar el modelo YOLOv5 personalizado
model = torch.hub.load('ultralytics/yolov5', 'custom', path='ann/modelo_placas.pt')

# Cargar el detector de texto EasyOCR
reader = easyocr.Reader(['en'])  # Especifica los idiomas que quieres soportar

raspberry_name = "MyRaspberry"
camera_number = 1

# Restaurar PosixPath
pathlib.PosixPath = temp

# Configurar la cámara principal
cap = cv2.VideoCapture(1)

# Configurar la segunda cámara para QR
cap_qr = cv2.VideoCapture(0)  # Suponiendo que la segunda cámara está en el índice 0

# Verificar si se está utilizando la GPU
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
print(f'Usando dispositivo: {device}')
model.to(device)

# Variables para el seguimiento del texto de la placa anterior
prev_license_number = None
prev_print_time = 0  # Tiempo de impresión del texto de la placa anterior
program_running = True


# Función para procesar fotogramas y realizar la inferencia
def process_frames():
    global prev_license_number, prev_print_time, program_running

    get_all_employees_car_registry()

    while program_running:
        ret, frame = cap.read()
        if not ret:
            print("Error al capturar el fotograma.")
            break

        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        im1 = Image.fromarray(frame)

        results = model(im1)

        for detection in results.pred[0]:
            conf = float(detection[4])
            if conf >= 0.8:  # Si la confianza es 80% o más
                bbox = detection[:4].tolist()
                bbox = [int(coord) for coord in bbox]

                # Obtener la región de la placa del vehículo
                license_plate_crop = frame[bbox[1]:bbox[3], bbox[0]:bbox[2]]
                # Realizar OCR en la región de la placa
                ocr_results = reader.readtext(license_plate_crop)

                if len(ocr_results) > 0:
                    license_number = ocr_results[0][1].replace(' ', '').replace('-', '')
                else:
                    license_number = "UNKNOWN"

                # Verificar si el texto de la placa ha cambiado desde la última vez
                current_time = time.time()
                if license_number != prev_license_number or current_time - prev_print_time > 5:  # Imprimir solo si ha pasado más de 5 segundos
                    # Mostrar y/o imprimir el resultado formateado
                    now = dt.datetime.now()
                    result_string = f"--RASPBERRY: {Fore.BLUE}{raspberry_name} --CAM: {Fore.CYAN}{camera_number} --PLATE: {Fore.GREEN}{license_number} --DATE: {Fore.MAGENTA}{now:%c}"
                    print(result_string)

                    if get_employee_by_car_registry(license_number):
                        print('Existing car!')
                    else:
                        print('Car not existing in database')

                    # Actualizar el texto de la placa anterior y el tiempo de impresión
                    prev_license_number = license_number
                    prev_print_time = current_time

                # Dibujar el cuadro delimitador y el texto sobre el fotograma
                cv2.rectangle(frame, (bbox[0], bbox[1]), (bbox[2], bbox[3]), (0, 255, 0), 2)
                cv2.putText(frame, license_number, (bbox[0], bbox[1] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9,(36, 255, 12), 2)

        rendered_frame = cv2.cvtColor(np.array(frame), cv2.COLOR_RGB2BGR)
        cv2.imshow('YOLOv5 Object Detection', rendered_frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            program_running = False


# Función para leer códigos QR
def read_qr_code(frame, last_data):
    # Decode QR codes in the frame
    qr_codes = decode(frame)
    current_data = None

    for qr in qr_codes:
        qr_data = qr.data.decode('utf-8')
        qr_type = qr.type
        current_data = qr_data

        # Draw a rectangle around the QR code
        points = qr.polygon
        if len(points) == 4:
            pts = np.array([[point.x, point.y] for point in points], dtype=np.int32)
            pts = pts.reshape((-1, 1, 2))
            cv2.polylines(frame, [pts], isClosed=True, color=(0, 255, 0), thickness=2)
        else:
            rect = qr.rect
            cv2.rectangle(frame, (rect.left, rect.top), (rect.left + rect.width, rect.top + rect.height), (0, 255, 0), 2)

        # Display the QR code data
        x, y, w, h = qr.rect
        cv2.putText(frame, qr_data, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

        if qr_data != last_data:
            print(f'Detected QR code: {qr_data} (Type: {qr_type})')

    return frame, current_data


# Función para procesar fotogramas y leer códigos QR
def process_qr_frames():
    last_data = None
    while program_running:
        ret, frame = cap_qr.read()
        if not ret:
            print("Error al capturar el fotograma de la cámara QR.")
            break

        frame, last_data = read_qr_code(frame, last_data)
        cv2.imshow('QR Code Scanner', frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break


def run():
# Iniciar el procesamiento de fotogramas en hilos separados
    frame_thread = threading.Thread(target=process_frames)
    qr_thread = threading.Thread(target=process_qr_frames)

    frame_thread.start()
    qr_thread.start()

# Esperar a que los hilos de procesamiento terminen
    frame_thread.join()
    qr_thread.join()

# Liberar recursos de las cámaras al terminar
    cap.release()
    cap_qr.release()
    cv2.destroyAllWindows()

run()