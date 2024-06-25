import sys
import os
import torch
import cv2
import numpy as np
from PIL import Image
import pathlib
import easyocr
import time
import threading
import datetime as dt
from colorama import Fore

# Temporarily override PosixPath for compatibility on Windows
temp = pathlib.PosixPath
pathlib.PosixPath = pathlib.WindowsPath

# Añadir el directorio de YOLOv5 al PYTHONPATH
sys.path.append(os.path.abspath('yolov5'))

# Cargar el modelo YOLOv5 personalizado
model = torch.hub.load('ultralytics/yolov5', 'custom', path='ann/modelo_placas.pt', source='local')

# Restaurar PosixPath
pathlib.PosixPath = temp

# Verificar si se está utilizando la GPU
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
print(f'Usando dispositivo: {device}')

# Mover el modelo a la GPU
model.to(device)

# Configurar la cámara principal
cap = cv2.VideoCapture(1)
if not cap.isOpened():
    print("Error al abrir la cámara")
    sys.exit()

# Cargar el detector de texto EasyOCR
reader = easyocr.Reader(['en'], gpu=torch.cuda.is_available())  # Usar GPU si está disponible

raspberry_name = "MyRaspberry"
camera_number = 1

# Variables para el seguimiento del texto de la placa anterior
prev_license_number = None
prev_print_time = 0  # Tiempo de impresión del texto de la placa anterior
program_running = True

# Función para procesar fotogramas y realizar la inferencia
def process_frames():
    global prev_license_number, prev_print_time, program_running
    
    while program_running:
        ret, frame = cap.read()
        if not ret:
            print("Error al capturar el fotograma.")
            break
        
        # Redimensionar el fotograma para reducir la carga computacional
        frame = cv2.resize(frame, (640, 480))
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        im1 = Image.fromarray(frame_rgb)

        results = model(im1)

        for detection in results.pred[0]:
            conf = float(detection[4])
            if conf >= 0.8:  # Si la confianza es 80% o más
                bbox = detection[:4].tolist()
                x1, y1, x2, y2 = map(int, bbox)

                # Obtener la región de la placa del vehículo
                license_plate_crop = frame_rgb[y1:y2, x1:x2]
                # Realizar OCR en la región de la placa
                ocr_results = reader.readtext(license_plate_crop)

                if ocr_results:
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

                    # Actualizar el texto de la placa anterior y el tiempo de impresión
                    prev_license_number = license_number
                    prev_print_time = current_time

                # Dibujar el cuadro delimitador y el texto sobre el fotograma
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.putText(frame, license_number, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (36, 255, 12), 2)

        cv2.imshow('YOLOv5 Object Detection', frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            program_running = False

# Iniciar el procesamiento de fotogramas en un hilo separado
frame_thread = threading.Thread(target=process_frames)
frame_thread.start()

# Esperar a que el hilo de procesamiento termine
frame_thread.join()

# Liberar recursos de la cámara al terminar
cap.release()
cv2.destroyAllWindows()
