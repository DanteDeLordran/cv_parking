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
from .qr_reader import *
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

# Configurar la cámara
cap = cv2.VideoCapture(1)

# Verificar si se está utilizando la GPU
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
print(f'Usando dispositivo: {device}')

# Mover el modelo a la GPU
model.to(device)

# Variables para el seguimiento del texto de la placa anterior
prev_license_number = None
prev_print_time = 0  # Tiempo de impresión del texto de la placa anterior
program_running = True

read_qr_code()
main_camera()


# Función para procesar fotogramas y realizar la inferencia
def process_frames():
    global prev_license_number, prev_print_time, program_running
    
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
                x1, y1, x2, y2 = bbox
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
                if (license_number != prev_license_number or current_time - prev_print_time > 5):  # Imprimir solo si ha pasado más de 5 segundos
                    # Mostrar y/o imprimir el resultado formateado
                    result_string = f"RASPBERRY_{raspberry_name}CAM-{camera_number}_PLATES{license_number}_{time.strftime('%Y%m%d_%H%M%S')}"
                    print(result_string)

                    # Actualizar el texto de la placa anterior y el tiempo de impresión
                    prev_license_number = license_number
                    prev_print_time = current_time

                # Dibujar el cuadro delimitador y el texto sobre el fotograma
                cv2.rectangle(frame, (bbox[0], bbox[1]), (bbox[2], bbox[3]), (0, 255, 0), 2)
                cv2.putText(frame, license_number, (bbox[0], bbox[1] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (36, 255, 12), 2)

        rendered_frame = cv2.cvtColor(np.array(frame), cv2.COLOR_RGB2BGR)
        cv2.imshow('YOLOv5 Object Detection', rendered_frame)

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
