import cv2
from ultralytics import YOLO
import time

# Load video
cap = cv2.VideoCapture('../data/sheepHerd4.mp4')

# Object type to count
count_type = "sheep"

# Load YOLO model
model = YOLO('../models/yolo11n.pt')
names = model.names  # e.g., {0: 'person', 1: 'sheep', ...}

# Virtual line position (horizontal)
line_y = 300

# Tracking data
unique_ids = set()
prev_positions = {}
sheep_count = 0

while True:
    ret, frame = cap.read()
    if not ret:
        break

    start_time = time.time()

    # Run detection and tracking
    result = model.track(frame, persist=True, verbose=False)

    if result[0] is None or result[0].boxes.id is None:
        annotated_frame = frame.copy()
    else:
        boxes = result[0].boxes
        xyxy = boxes.xyxy.cpu().tolist()
        ids = boxes.id.cpu().tolist()
        class_ids = boxes.cls.int().cpu().tolist()

        annotated_frame = frame.copy()

        for box, track_id, class_id in zip(xyxy, ids, class_ids):
            class_name = names[class_id]

            if class_name != count_type:
                continue

            # Bounding box coordinates
            x1, y1, x2, y2 = map(int, box)
            cx = int((x1 + x2) / 2)
            cy = int((y1 + y2) / 2)

            # Check if sheep crossed the line (top to bottom)
            if track_id in prev_positions:
                prev_y = prev_positions[track_id]
                if prev_y < line_y <= cy and track_id not in unique_ids:
                    unique_ids.add(track_id)
                    sheep_count += 1

            # Update previous position
            prev_positions[track_id] = cy

            # Draw smaller, discreet bounding box and label
            cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), (0, 200, 0), 1)  # thin green box
            cv2.circle(annotated_frame, (cx, cy), 2, (0, 200, 0), -1)  # center point
            cv2.putText(annotated_frame, f'{class_name}', (x1, y1 - 5),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 200, 0), 1)

    # Draw counting line (always visible)
    cv2.line(annotated_frame, (0, line_y), (annotated_frame.shape[1], line_y), (0, 0, 255), 2)

    # Calculate FPS
    fps = 1 / (time.time() - start_time + 1e-5)

    # Display sheep count
    cv2.putText(annotated_frame, f"Sheep Count: {sheep_count}", (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

    # Display FPS
    cv2.putText(annotated_frame, f"FPS: {fps:.0f}", (10, 60),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 2)

    # Show result
    cv2.imshow('Result', annotated_frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Cleanup
cap.release()
cv2.destroyAllWindows()
