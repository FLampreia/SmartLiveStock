import cv2 as cv2
from ultralytics import YOLO
import time

#abrir a camara
cap = cv2.VideoCapture(0)
#cap = cv2.VideoCapture('cars.mp4')

width = 640
height = 480

#download do algoritmo
model = YOLO('../models/yolo11n.pt')
#model = YOLO('yolo11s.pt')
#model = YOLO('yolo11m.pt')


names = model.names

# Dicionário para guardar ID -> classe
unique_objects = {}

# Inicializar tempo
prev_time = 0

while True:
    ret, frame = cap.read()

    if not ret:
        break

    frame = cv2.resize(frame, (width, height))

    # Início do tempo do frame
    start_time = time.time()

    result = model.track(frame, persist=True, verbose=False)

    if result[0] is None or result[0].boxes.id is None:
        continue

    boxes = result[0].boxes.xywh.cpu()
    track_ids = result[0].boxes.id.cpu().tolist()
    cls = result[0].boxes.cls.int().cpu().tolist()

    for track_id, class_id in zip(track_ids, cls):
        if track_id not in unique_objects:
            unique_objects[track_id] = names[class_id]

    annotated_frame = result[0].plot()

    # Calcular FPS
    end_time = time.time()
    fps = 1 / (end_time - start_time + 1e-5)  # evitar divisão por zero

    # Mostrar contagem de objetos únicos
    cv2.putText(annotated_frame, f"Total: {len(unique_objects)}", (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

    # Mostrar FPS
    cv2.putText(annotated_frame, f"FPS: {fps:.2f}", (10, 70),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)

    cv2.imshow('Result', annotated_frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()