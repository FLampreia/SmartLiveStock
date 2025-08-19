import cv2 as cv2
from ultralytics import YOLO
import time
import numpy as np

from utils_logs import save_logs, save_ids, save_plot, resume

# -----------------------------
# Configurations
# -----------------------------
cap = cv2.VideoCapture('../data/sheepHerd1.mp4')
width, height = 640, 480

class_type = "sheep"  # Type of counting object
model_path = '../models/yolo11n.pt'
scan_type = "all" #all, line, area

valid_scan_types = ["all", "line", "area"]
if scan_type not in valid_scan_types:
    raise ValueError(f"Invalid scan_type: {scan_type}. Valid options are: {valid_scan_types}")

# -----------------------------
# Load YOLO model
# -----------------------------
model = YOLO(model_path)
model.to('cuda')
names = model.names

# -----------------------------
# Tracking + Counting
# -----------------------------
unique_ids = {}
sheep_count = 0
id_map = {}   # Maps YOLO IDs to Sequential IDs
next_id = 1   # Next sequential ID

# Line scan
last_positions = {}
line_y = 2 * height // 3

# Area scan
roi_polygon = np.array([
    [250, 130],
    [470, 130],
    [800, 400],
    [70, 400]
], np.int32)

# -----------------------------
# FPS
# -----------------------------
frame_count = 0
start_time = time.time()
prev_time = start_time

# -----------------------------
# Logs
# -----------------------------
log_data = []

# -----------------------------
# Main loop
# -----------------------------
while True:
    ret, frame = cap.read()
    if not ret:
        break

    frame = cv2.resize(frame, (width, height))
    result = model.track(frame, persist=True, verbose=False) # Detection + Tracking
    annotated_frame = frame.copy()

    visible_sheep = 0  # Counts how many sheep appear on the frame
    new_sheep_in_frame = 0 # Counts how many new sheep appear on the frame

    # Draw line if scan_type = line
    if scan_type == "line":
        cv2.line(annotated_frame, (0, line_y), (width, line_y), (0, 0, 255), 2)

    elif scan_type == "area":
        cv2.polylines(annotated_frame, [roi_polygon], isClosed=True, color=(0, 255, 255), thickness=2)

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

            # ID converter (changed from a random id from YOLO to a sequential one)
            if track_id not in id_map:
                id_map[track_id] = next_id
                next_id += 1
            display_id = id_map[track_id]

            visible_sheep += 1

            # -----------------------------
            # Counting
            # -----------------------------
            if scan_type == "all":
                if display_id not in unique_ids:
                    unique_ids[display_id] = frame_count
                    sheep_count += 1
                    new_sheep_in_frame += 1
                    print(f"New ID: {display_id}")

            elif scan_type == "line":
                last_y = last_positions.get(track_id, cy)
                if last_y < line_y <= cy and display_id not in unique_ids:
                    unique_ids[display_id] = frame_count
                    sheep_count += 1
                    new_sheep_in_frame += 1
                    print(f"({sheep_count}) Added: {display_id}")

            elif scan_type == "area":
                inside = cv2.pointPolygonTest(roi_polygon, (cx, cy), False)
                if inside >= 0 and display_id not in unique_ids:
                    unique_ids[display_id] = frame_count
                    sheep_count += 1
                    new_sheep_in_frame += 1
                    print(f"({sheep_count}) Added: {display_id}")

            last_positions[track_id] = cy # update last position

            # -----------------------------
            # Drawing bounding boxes
            # -----------------------------
            cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), (255, 0, 0), 1)
            cv2.circle(annotated_frame, (cx, cy), 2, (255, 0, 0), -1)
            cv2.putText(annotated_frame, f'{class_name} {display_id}', (x1, y1 - 5),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 0, 0), 1)

    # -----------------------------
    # FPS
    # -----------------------------
    frame_count += 1
    curr_time = time.time()
    live_fps = 1 / (curr_time - prev_time)

    cv2.putText(annotated_frame, f"FPS: {live_fps:.0f}", (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

    # -----------------------------
    # Display
    # -----------------------------
    cv2.imshow('Camera', annotated_frame)

    # -----------------------------
    # Logs data
    # -----------------------------
    elapsed_time = curr_time - start_time
    time_since_last_frame = curr_time - prev_time
    log_data.append({
        "frame": frame_count,
        "total_time": round(elapsed_time, 2),
        "time_since_last_frame": round(time_since_last_frame, 2),
        "sheep_visible": visible_sheep,
        "new_sheep_in_frame": new_sheep_in_frame,
        "sheep_total_count": sheep_count,
        "fps": round(live_fps, 2)
    })

    prev_time = curr_time

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# -----------------------------
# Close
# -----------------------------
cap.release()
cv2.destroyAllWindows()

# -----------------------------
# Save Logs
# -----------------------------
df, log_filename, model_name, timestamp = save_logs(log_data, model_path, scan_type)
ids_filename = save_ids(unique_ids, model_path, scan_type, timestamp, model_name)
# plot_filename = save_plot(df, model_name, scan_type, timestamp)
resume(df, frame_count, sheep_count)
