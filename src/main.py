import cv2 as cv2
from ultralytics import YOLO
import numpy as np
import torch

# Carregar vídeo
cap = cv2.VideoCapture('../data/sheepHerd4_1.mp4')

width = 640
height = 480

class_type = "sheep"  # Tipo de objeto a contar

# Carregar modelo YOLO
model = YOLO('../models/yolo11m.pt')
model.to('cuda')
names = model.names

# Dados de tracking
unique_ids = set()          # IDs de ovelhas já contadas
last_positions = {}         # Última coordenada Y de cada ID
sheep_count = 0

# Linha de contagem (posição vertical fixa)
line_y = 2*height // 3  # Meio do frame

while True:
    ret, frame = cap.read()
    if not ret:
        break

    frame = cv2.resize(frame, (width, height))

    # Detecção + Tracking
    result = model.track(frame, persist=True, verbose=False)
    annotated_frame = frame.copy()

    # Desenha linha fixa
    cv2.line(annotated_frame, (0, line_y), (width, line_y), (0, 0, 255), 2)

    if result[0] is not None and result[0].boxes.id is not None:
        boxes = result[0].boxes
        xyxy = boxes.xyxy.cpu().tolist()
        ids = boxes.id.cpu().tolist()
        class_ids = boxes.cls.int().cpu().tolist()

        for box, track_id, class_id in zip(xyxy, ids, class_ids):
            class_name = names[class_id]
            if class_name != class_type:
                continue

            x1, y1, x2, y2 = map(int, box)
            cx = int((x1 + x2) / 2)
            cy = int((y1 + y2) / 2)

            # Verifica se o ID já estava no frame anterior
            if track_id in last_positions:
                last_y = last_positions[track_id]

                # Condição: estava acima e agora passou para baixo
                if last_y < line_y <= cy and track_id not in unique_ids:
                    unique_ids.add(track_id)
                    sheep_count += 1
                    print(f"Added: {track_id}")

            # Atualiza última posição Y
            last_positions[track_id] = cy

            # Desenho da bounding box
            cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), (255, 0, 0), 1)
            cv2.circle(annotated_frame, (cx, cy), 2, (255, 0, 0), -1)
            cv2.putText(annotated_frame, f'{class_name} {track_id}', (x1, y1 - 5),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 0, 0), 1)

    # Mostrar número de ovelhas
    cv2.putText(annotated_frame, f"Sheep Count: {sheep_count}", (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 0, 0), 2)

    # Exibir resultado
    cv2.imshow('Result', annotated_frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

print(sheep_count)
print(unique_ids)

# Fechar
cap.release()
cv2.destroyAllWindows()
