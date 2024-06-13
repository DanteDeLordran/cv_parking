import sys
import os
import torch
import cv2
import numpy as np
from PIL import Image
import pathlib
import easyocr
import time

# Temporarily override PosixPath for compatibility on Windows
temp = pathlib.PosixPath
pathlib.PosixPath = pathlib.WindowsPath

# Añadir el directorio de YOLOv5 al PYTHONPATH
sys.path.append(os.path.abspath('yolov5'))

# Cargar el modelo YOLOv5 personalizado
model = torch.hub.load('ultralytics/yolov5', 'custom', path='./modelo_placas.pt')

# Cargar el detector de texto EasyOCR
reader = easyocr.Reader(['en'])  # Especifica los idiomas que quieres soportar

raspberry_name = "MyRaspberry"  
camera_number = 1  

# Restaurar PosixPath
pathlib.PosixPath = temp

# Configurar la cámara
cap = cv2.VideoCapture(0)

# Verificar si se está utilizando la GPU
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
print(f'Usando dispositivo: {device}')

# Mover el modelo a la GPU
model.to(device)

# Variable para almacenar el último número de placa detectado
last_license_number = None

while cap.isOpened():
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

            # Comparar con el último número de placa detectado
            if license_number != last_license_number:
                # Formato de la cadena de resultado
                current_time = time.strftime("%Y%m%d_%H%M%S")
                result_string = f"RASPBERRY_{raspberry_name}CAM-{camera_number}_PLATES{license_number}_{current_time}"

                # Mostrar y/o imprimir el resultado formateado
                print(result_string)

                # Actualizar el último número de placa detectado
                last_license_number = license_number

            # Dibujar el cuadro delimitador y el texto sobre el fotograma
            cv2.rectangle(frame, (bbox[0], bbox[1]), (bbox[2], bbox[3]), (0, 255, 0), 2)
            cv2.putText(frame, license_number, (bbox[0], bbox[1] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (36, 255, 12), 2)

    rendered_frame = cv2.cvtColor(np.array(frame), cv2.COLOR_RGB2BGR)
    cv2.imshow('YOLOv5 Object Detection', rendered_frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
