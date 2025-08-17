import cv2 as cv2
from ultralytics import YOLO
import time

from utils_logs import save_logs, save_ids, save_plot, resume

# Load video
cap = cv2.VideoCapture('../data/sheepHerd4_1.mp4')

width = 640
height = 480

class_type = "sheep"  # Type of counting object
model_path = '../models/yolo11n.pt'
scan_type = "all"

# Load YOLO model
model = YOLO(model_path)
model.to('cuda')
names = model.names

# Tracking data
unique_ids = {}
sheep_count = 0

# Initialize FPS calculation
frame_count = 0
start_time = time.time()
prev_time = start_time

# List to save Log data
log_data = []

id_map = {}   # Maps YOLO IDs to Sequential IDs
next_id = 1   # Next sequential ID

while True:
    ret, frame = cap.read()
    if not ret:
        break

    frame = cv2.resize(frame, (width, height))

    # Detection + Tracking
    result = model.track(frame, persist=True, verbose=False)
    annotated_frame = frame.copy()

    visible_sheep = 0  # Counts how many sheep appear on the frame

    if result[0] is not None and result[0].boxes.id is not None:
        boxes = result[0].boxes
        xyxy = boxes.xyxy.cpu().tolist()
        ids = boxes.id.cpu().tolist()
        class_ids = boxes.cls.int().cpu().tolist()

        for box, track_id, class_id in zip(xyxy, ids, class_ids):
            class_name = names[class_id]
            if class_name != class_type:
                continue

            # ID converter (changed from a random id from YOLO to a sequential one)
            if track_id not in id_map:
                id_map[track_id] = next_id
                next_id += 1
            display_id = id_map[track_id]

            visible_sheep += 1

            x1, y1, x2, y2 = map(int, box)
            cx = int((x1 + x2) / 2)
            cy = int((y1 + y2) / 2)

            if display_id not in unique_ids: # New sheep appears
                unique_ids[display_id] = frame_count # Save the frame number
                sheep_count += 1
                print(f"New ID: {display_id}")

            cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), (255, 0, 0), 1)
            cv2.circle(annotated_frame, (cx, cy), 2, (255, 0, 0), -1)
            cv2.putText(annotated_frame, f'{class_name} {display_id}', (x1, y1 - 5),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 0, 0), 1)

    # FPS
    frame_count += 1
    curr_time = time.time()
    live_fps = 1 / (curr_time - prev_time)
    prev_time = curr_time

    cv2.putText(annotated_frame, f"FPS: {live_fps:.0f}", (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

    cv2.imshow('Camera', annotated_frame)

    # Save data for the log
    elapsed_time = curr_time - start_time
    log_data.append({
        "frame": frame_count,
        "time": elapsed_time,
        "sheep_visible": visible_sheep,
        "sheep_count": sheep_count,
        "fps": live_fps
    })

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Fechar
cap.release()
cv2.destroyAllWindows()


# No final:
df, log_filename, model_name, timestamp = save_logs(log_data, model_path, scan_type)
ids_filename = save_ids(unique_ids, model_path, scan_type, timestamp, model_name)
plot_filename = save_plot(df, model_name, scan_type, timestamp)
resume(df, frame_count, sheep_count, log_filename, ids_filename, plot_filename)
