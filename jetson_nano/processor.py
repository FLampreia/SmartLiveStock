from jetson_nano import get_static
import cv2
from detector import SheepDetector

cap = cv2.VideoCapture(get_static('detection', 'camera_path'))  # path ou ID da câmara
# detector = SheepDetector()

width = get_static('resize', 'width')
height = get_static('resize', 'height')

while True:
    ret, frame = cap.read()
    if not ret:
        break

    frame = cv2.resize(frame, (width, height))

    # detections, frame_with_boxes = detector.analyze_frame(frame)

    # Aqui podes processar os resultados, ex.: contar ovelhas
    # sheep_count = len(detections)
    # cv2.putText(frame_with_boxes, f'Ovelhas: {sheep_count}', (10,30),
    #             cv2.FONT_HERSHEY_SIMPLEX, 1, (0,0,255), 2)

    cv2.imshow('Camera', frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
