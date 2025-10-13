import cv2 as cv2
import time
import numpy as np



width, height = 640, 480
video = '/home/jetson/Projects/SmartLiveStock/data/sheepHerd1.mp4'
url = 'rtsp://Raspberry:projetorasppi5@192.168.1.113:554/stream1'
cap = cv2.VideoCapture(video) # 0 to camera (30 fps)
fps_video = round(cap.get(cv2.CAP_PROP_FPS), 1)
print(fps_video)

# -----------------------------
# FPS
# -----------------------------
frame_count = 0
start_time = time.time()
prev_time = start_time
fps_values = []

while True:
    ret, frame = cap.read()
    if not ret:
        break

    frame = cv2.resize(frame, (width, height))

    # -----------------------------
    # FPS
    # -----------------------------
    frame_count += 1
    curr_time = time.time()
    live_fps = frame_count / (curr_time - start_time)
    fps_values.append(live_fps)

    cv2.putText(frame, f"FPS: {live_fps:.1f}", (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

    # -----------------------------
    # Display
    # -----------------------------
    cv2.imshow('Camera', frame)

    prev_time = curr_time

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# -----------------------------
# Close
# -----------------------------
cap.release()
cv2.destroyAllWindows()

print(f"Average FPS: {np.mean(fps_values) if fps_values else 0:.2f}")