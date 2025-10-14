# from detector import SheepDetector
from ultralytics import YOLO
from jetson_nano import get_static
import cv2

cap = cv2.VideoCapture(get_static('detection', 'camera_path'))  # path ou ID da câmara

width = get_static('resize', 'width')
height = get_static('resize', 'height')
model = YOLO(get_static('detection', 'model_path'))
conf_threshold = get_static('detection', 'conf_threshold')
class_type = get_static('detection', 'class_type')

while True:
    ret, frame = cap.read()
    if not ret:
        break

    frame = cv2.resize(frame, (width, height))
    result = model.track(frame, persist=True, verbose=True)  # Detection + Tracking
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
            cx = int((x1 + x2) / 2)
            cy = int((y1 + y2) / 2)

            if conf >= conf_threshold:
                cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), (0, 255, 0), 1)
                cv2.circle(annotated_frame, (cx, cy), 2, (255, 0, 0), -1)
                cv2.putText(annotated_frame, f'{class_name} {track_id}', (x1, y1 - 5),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 0, 0), 1)
            else:
                cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), (255, 0, 0), 1)
                cv2.circle(annotated_frame, (cx, cy), 2, (255, 0, 0), -1)
                cv2.putText(annotated_frame, f'{class_name} {track_id}', (x1, y1 - 5),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 0, 0), 1)

    cv2.imshow('Camera', annotated_frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
