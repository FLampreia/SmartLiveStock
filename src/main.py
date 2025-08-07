import cv2 as cv2
from ultralytics import YOLO
import time


# Open the camera (0 = default webcam)
# cap = cv2.VideoCapture(0)
# Alternatively, load a video file
cap = cv2.VideoCapture('../data/sheepHerd4.mp4')

# Set frame dimensions
width = 640
height = 480

#Set Type
count_type = "sheep"

# Load the YOLO model
model = YOLO('../models/yolo11n.pt')

names = model.names  # Class names

# Dictionary to store unique objects by ID
unique_objects = {}

# Initialize previous time for FPS calculation
prev_time = 0

while True:
    ret, frame = cap.read()  # Capture frame from the video/camera
    if not ret:
        break  # If frame not read correctly, exit loop

    # Start time for FPS measurement
    start_time = time.time()

    # Run tracking using the YOLO model
    result = model.track(frame, persist=True, verbose=False)

    # Skip frame if no detections or tracking IDs
    if result[0] is None or result[0].boxes.id is None:
        continue

    # Get all tracking data
    boxes = result[0].boxes
    track_ids = boxes.id.cpu().tolist()
    class_ids = boxes.cls.int().cpu().tolist()

    # Filter indices where class is 'sheep'
    sheep_indices = [i for i, class_id in enumerate(class_ids) if names[class_id] == count_type]

    # Save new unique sheep
    for i in sheep_indices:
        track_id = track_ids[i]
        if track_id not in unique_objects:
            unique_objects[track_id] = count_type

    # Filter only sheep boxes
    if sheep_indices:
        # Create filtered boxes object
        sheep_boxes = boxes[sheep_indices]
        result[0].boxes = sheep_boxes

        # Plot only sheep boxes
        annotated_frame = result[0].plot()
    else:
        annotated_frame = frame.copy()

    # FPS calculation
    end_time = time.time()
    fps = 1 / (end_time - start_time + 1e-5)

    # Show sheep count
    cv2.putText(annotated_frame, f"Sheep Count: {len(unique_objects)}", (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

    # Show FPS
    cv2.putText(annotated_frame, f"FPS: {fps:.0f}", (10, 70),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)

    # Display result
    cv2.imshow('Result', annotated_frame)

    # Press 'q' to exit the loop
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Cleanup
cap.release()
cv2.destroyAllWindows()

# # Mostrar os IDs e classes apenas no fim
# print("\nResumo final - Objetos únicos detetados:")
# for obj_id, class_name in unique_objects.items():
#     print(f"ID: {obj_id} - Classe: {class_name}")
#
# # Contar quantos objetos são da classe "sheep"
# num_sheep = sum(1 for class_name in unique_objects.values() if class_name == "sheep")
# print(f"\nNº de objetos 'sheep': {num_sheep}")
# print(f"Total de objetos únicos: {len(unique_objects)}")
