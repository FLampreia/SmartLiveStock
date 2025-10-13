import torch.hub

from jetson_nano import get_static
import cv2


class SheepDetector:
    def __init__(self):
        model_path = get_static('detection', 'model_path')
        self.model = torch.hub.load('ultralytics/yolov5', 'custom', path=model_path)
        self.conf_threshold = get_static('detection', 'conf_threshold')
        self.class_type = get_static('detection', 'class_type')

    def analyze_frame(self, frame):
        """
        Recebe um frame (numpy array), retorna:
        - lista de detecções (x1, y1, x2, y2, conf, class)
        - frame com boxes desenhadas
        """
        # Inferência
        results = self.model(frame)

        detections = []
        for *box, conf, cls in results.xyxy[0]:
            if conf < self.conf_threshold:
                continue
            x1, y1, x2, y2 = map(int, box)
            detections.append({
                'bbox': (x1, y1, x2, y2),
                'conf': float(conf),
                'class': int(cls)
            })
            # Desenhar box no frame
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)

        return detections, frame
