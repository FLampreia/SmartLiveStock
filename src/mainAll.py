import cv2 as cv2
from ultralytics import YOLO
import numpy as np
import torch
import time

# Load video
cap = cv2.VideoCapture('../data/sheepHerd4_1.mp4')
# cap = cv2.VideoCapture(0)

width = 640
height = 480

class_type = "sheep"  # Type of counting object

# Load YOLO model
model = YOLO('../models/yolo11x.pt')
model.to('cuda')
names = model.names

# Tracking data
unique_ids = set()          # Store counted sheep IDs
last_positions = {}         # Last Y coordinate from each ID
sheep_count = 0

# Initialize FPS calculation
frame_count = 0
start_time = time.time()
prev_time = start_time


while True:
    ret, frame = cap.read()
    if not ret:
        break

    frame = cv2.resize(frame, (width, height))

    # Detection + Tracking
    result = model.track(frame, persist=True, verbose=False)
    annotated_frame = frame.copy()


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

            # Contar cada novo ID único
            if track_id not in unique_ids:
                unique_ids.add(track_id)
                sheep_count += 1
                print(f"({sheep_count}) Novo ID contado: {track_id}")

            # (Opcional) Atualizar posição só se ainda precisares para algo
            last_positions[track_id] = cy

            # Desenhar bounding box
            cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), (255, 0, 0), 1)
            cv2.circle(annotated_frame, (cx, cy), 2, (255, 0, 0), -1)
            cv2.putText(annotated_frame, f'{class_name} {track_id}', (x1, y1 - 5),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 0, 0), 1)

    # Increment frame counter
    frame_count += 1

    # Calculate live FPS
    curr_time = time.time()
    live_fps = 1 / (curr_time - prev_time)
    prev_time = curr_time

    # Show live FPS on frame
    cv2.putText(annotated_frame, f"FPS: {live_fps:.0f}", (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

    # Show frames
    cv2.imshow('Camera', annotated_frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Calculate average FPS
end_time = time.time()
total_time = end_time - start_time
average_fps = frame_count / total_time

print(f"Total frames processed: {frame_count}")
print(f"Average FPS: {average_fps:.2f}")
print(sheep_count)
print(unique_ids)

# Close
cap.release()
cv2.destroyAllWindows()