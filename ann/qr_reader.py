import cv2
import numpy as np
from pyzbar.pyzbar import decode

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

def main_camera():
    # Open the webcam
    cap = cv2.VideoCapture(1) #Select your device camera 0-2
    if not cap.isOpened():
        print("Error: Could not open video stream.")
        return

    print("Press 'q' to quit.")

    last_data = None
    
    while True:
        ret, frame = cap.read()
        if not ret:
            print("Error: Could not read frame.")
            break

        # Process the frame to read QR codes
        frame, last_data = read_qr_code(frame, last_data)

        # Display the resulting frame
        cv2.imshow('QR Code Scanner', frame)

        # Exit when 'q' is pressed
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # Release the capture and close windows
    cap.release()
    cv2.destroyAllWindows()

if __name__ == '__main__':
    main_camera()
