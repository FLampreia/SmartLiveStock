import cv2, json, asyncio, numpy as np, base64
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from ultralytics import YOLO
from datetime import datetime

# ==============================================================
# Configs
# ==============================================================
SHOW_LOCAL = True
FRAME_WIDTH = 640
FRAME_HEIGHT = 480
CLASS_TYPE = "sheep"
CONF_THRESHOLD = 0.88
MODEL_PATH = "jetson_nano/models/yolo11s.pt"

app = FastAPI()

# ==============================================================
# Model Loading
# ==============================================================
model = YOLO(MODEL_PATH).to('cuda')

# ==============================================================
# Variables
# ==============================================================

# Shared state variables
shared_state = {
    "camera": None,
    "area": None,
    "detect": None
}

# Global variables
sheep_count = 0
tracked_ids = set()
flag_new_detections = False

# ==============================================================
# Auxiliar Functions
# ==============================================================
def create_mask(area_points):
    """Create a binary mask with the defined area points."""
    mask = np.zeros((FRAME_HEIGHT, FRAME_WIDTH), dtype=np.uint8)
    if not area_points:
        mask[:] = 255  # If there is no area points all frame is considered area
        return mask

    pts = np.array(area_points, np.int32)
    hull = cv2.convexHull(pts)
    cv2.fillPoly(mask, [hull], 255)
    return mask, hull

def annotate_frame(frame, detections, mask):
    """Draw boxes, IDs and detection area"""
    for det in detections:
        x1, y1, x2, y2 = det["bbox"]
        track_id = det["id"]
        class_name = det["class_name"]
        color = (0, 255, 0) if det["tracked"] else (255, 0, 0)
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
        cv2.putText(frame, f"{class_name} #{track_id}",
                    (x1, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
    if isinstance(mask, tuple):  # If contains the hull too
        _, hull = mask
        cv2.polylines(frame, [hull], isClosed=True, color=(255, 255, 0), thickness=2)
    return frame

async def send_frame(websocket, frame, new_detection_flag, camera_id):
    """Code and send the frame"""
    _, buffer = cv2.imencode(".jpg", frame)

    # Only sent the frame when necessary
    if new_detection_flag:
        frame_data = {
            "type": "frame",
            "camera_id": camera_id,
            "timestamp": datetime.utcnow().isoformat(),
            "new_detections": True,
            "image": base64.b64encode(buffer).decode("utf-8")
        }
        await websocket.send_text(json.dumps(frame_data))

    # Sent frame in bytes
    await websocket.send_bytes(buffer.tobytes())



# ==============================================================
# Streaming Function
# ==============================================================
async def stream_frames(websocket: WebSocket, capture: cv2.VideoCapture,
                        stop_event: asyncio.Event, shared_state):
    global sheep_count, tracked_ids, flag_new_detections

    sheep_count = 0
    flag_new_detections = False
    tracked_ids.clear()

    try:
        while not stop_event.is_set():
            success, frame = capture.read()

            # if not success:
            #     capture.set(cv2.CAP_PROP_POS_FRAMES, 0)
            #     await asyncio.sleep(0.1)
            #     continue

            if not success:
                print("Vídeo terminou.")
                stop_event.set()
                break

            frame = cv2.resize(frame, (FRAME_WIDTH, FRAME_HEIGHT))
            annotated_frame = frame.copy()

            area_points = shared_state.get("area")
            detect_enabled = shared_state.get("detect")

            # Creates defined area
            mask = create_mask(area_points)

            detections = []

            # Detection and tracking
            if detect_enabled:
                result = model.track(frame, persist=True, verbose=False)

                if result[0] is not None and result[0].boxes.id is not None:
                    boxes = result[0].boxes
                    for xyxy, track_id, class_id, conf in zip(
                            boxes.xyxy.cpu().tolist(),
                            boxes.id.cpu().tolist(),
                            boxes.cls.int().cpu().tolist(),
                            boxes.conf.cpu().tolist()
                    ):
                        class_name = model.names[class_id]

                        if class_name != CLASS_TYPE or conf < CONF_THRESHOLD:
                            continue

                        x1, y1, x2, y2 = map(int, xyxy)
                        cx, cy = (x1 + x2) // 2, (y1 + y2) // 2

                        inside_area = mask[0][cy, cx] > 0 if isinstance(mask, tuple) else mask[cy, cx] > 0

                        new_track = track_id not in tracked_ids and inside_area

                        if new_track:
                            tracked_ids.add(track_id)
                            sheep_count += 1
                            flag_new_detections = True
                            print(f"[{sheep_count}] Nova ovelha ID {track_id} | Confiança: {conf:.2f}")

                        detections.append({
                            "bbox": (x1, y1, x2, y2),
                            "id": track_id,
                            "class_name": class_name,
                            "tracked": track_id in tracked_ids
                        })

            # --------------------------------------------------------------
            # Visualization and Sending
            # --------------------------------------------------------------
            annotated_frame = annotate_frame(annotated_frame, detections, mask)

            if SHOW_LOCAL:
                cv2.imshow("SmartLiveStock Stream", annotated_frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    print("Transmissão interrompida localmente.")
                    break

            try:
                await send_frame(websocket, annotated_frame, flag_new_detections, shared_state["camera"])
                flag_new_detections = False
            except WebSocketDisconnect:
                print("Cliente desconectado.")
                break

    finally:
        capture.release()
        cv2.destroyAllWindows()
        print("Transmissão encerrada.")


# ==============================================================
# WebSocket Endpoint
# ==============================================================
@app.websocket("/jetson_ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("Cliente conectado à jetson.")
    capture = None
    stop_event = asyncio.Event()
    frame_task = None

    try:
        while True:
            try:
                message = json.loads(await websocket.receive_text())
            except WebSocketDisconnect:
                print("Cliente fechou a conexão.")
                break

            msg_type = message.get("type")

            if msg_type == "video":
                msg_params = message.get("params", {})
                shared_state.update({
                    "camera": msg_params.get("camera"),
                    "detect": msg_params.get("detect"),
                    "area": msg_params.get("area", [])
                })

                # Reinicia a captura se já estiver em execução
                if frame_task and not frame_task.done():
                    stop_event.set()
                    await frame_task
                    stop_event.clear()

                if capture:
                    capture.release()

                cam_source = shared_state["camera"]
                try:
                    cam_index = int(cam_source)
                    capture = cv2.VideoCapture(cam_index)
                    print(f"A usar câmara: {cam_index}")
                except (ValueError, TypeError):
                    capture = cv2.VideoCapture(cam_source)
                    print(f"A reproduzir vídeo: {shared_state["camera"]}")

                if not capture.isOpened():
                    await websocket.send_text(json.dumps({"error": f"Não foi possível abrir {shared_state["camera"]}"}))
                    continue

                await websocket.send_text(json.dumps({
                    "type": msg_type,
                    "camera": shared_state["camera"],
                    "area": shared_state["area"],
                }))

                frame_task = asyncio.create_task(
                    stream_frames(websocket, capture, stop_event, shared_state)
                )

            elif msg_type == "teste":
                await websocket.send_text(json.dumps({"status": "Jetson esta a responder"}))

            elif msg_type == "stop":
                stop_event.set()
                await websocket.send_text(json.dumps({"status": "stopped"}))

    except Exception as e:
        print("Erro na conexão:", e)
    finally:
        if frame_task and not frame_task.done():
            stop_event.set()
            await frame_task
        if capture:
            capture.release()
        cv2.destroyAllWindows()
        print("Conexão encerrada.")