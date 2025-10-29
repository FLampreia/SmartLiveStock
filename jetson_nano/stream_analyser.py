from ultralytics import YOLO
from jetson_nano import get_static
import cv2

cap = cv2.VideoCapture(get_static('detection', 'camera_path'))  # path ou ID da câmara

width = get_static('resize', 'width')
height = get_static('resize', 'height')
model = YOLO(get_static('detection', 'model_path'))
conf_threshold = get_static('detection', 'conf_threshold')
class_type = get_static('detection', 'class_type')

sheep_count = 0
tracked_ids = set()

while True:
    ret, frame = cap.read()
    if not ret:
        break

    frame = cv2.resize(frame, (width, height))
    result = model.track(frame, persist=True, verbose=False)  # Detection + Tracking
    annotated_frame = frame.copy()

    if result[0] is not None and result[0].boxes.id is not None:
        boxes = result[0].boxes
        xyxy = boxes.xyxy.cpu().tolist()
        ids = boxes.id.cpu().tolist()
        class_ids = boxes.cls.int().cpu().tolist()
        confs = boxes.conf.cpu().tolist()

        for box, track_id, class_id, conf in zip(xyxy, ids, class_ids, confs):
            class_name = model.names[class_id]
            if class_name != class_type:
                continue

            x1, y1, x2, y2 = map(int, box)

            if conf >= conf_threshold and track_id not in tracked_ids:
                tracked_ids.add(track_id)
                sheep_count += 1
                print(f"[{sheep_count}] Nova ovelha ID {track_id} | Confiança: {conf:.2f}")

            color = (0, 255, 0) if track_id in tracked_ids else (255, 0, 0)
            cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), color, 2)
            cv2.putText(annotated_frame, f"{class_name} #{track_id}", (x1, y1 - 5),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)

    cv2.imshow('Camera', annotated_frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()

print(f"Process finished. Total sheep counted: {sheep_count}")
