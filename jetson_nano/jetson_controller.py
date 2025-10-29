from fastapi import FastAPI, WebSocket
import cv2
import json
import asyncio
import numpy as np
from ultralytics import YOLO

# from jetson_nano.stream_analyser import sheep_count, tracked_ids

FRAME_WIDTH = 640
FRAME_HEIGHT = 480
CLASS_TYPE = "sheep"
CONF_THRESHOLD  = 0.88
MODEL_PATH = "jetson_nano/models/yolo11n.pt"
app = FastAPI()

model = YOLO(MODEL_PATH)
model.to('cuda')
sheep_count = 0
tracked_ids = set()

# ==============================================================
# Função de streaming com deteção e área
# ==============================================================

async def stream_frames(websocket: WebSocket, capture: cv2.VideoCapture, stop_event: asyncio.Event, area_points=None):
    global sheep_count, tracked_ids

    sheep_count = 0
    tracked_ids.clear()

    while not stop_event.is_set():
        success, frame = capture.read()

        # Reiniciar vídeo se terminar (loop)
        if not success:
            capture.set(cv2.CAP_PROP_POS_FRAMES, 0)
            await asyncio.sleep(0.1)
            continue

        frame = cv2.resize(frame, (FRAME_WIDTH, FRAME_HEIGHT))

        # Se há área definida, desenhar
        if area_points:
            pts = [tuple(p) for p in area_points]
            cv2.polylines(frame, [cv2.convexHull(np.array(pts, np.int32))], True, (255, 255, 0), 2)

        # Executar deteção e tracking
        result = model.track(frame, persist=True, verbose=False)

        annotated_frame = frame.copy()

        if result[0] is not None and result[0].boxes.id is not None:
            boxes = result[0].boxes
            xyxy = boxes.xyxy.cpu().tolist()
            ids = boxes.id.cpu().tolist()
            class_ids = boxes.cls.int().cpu().tolist()
            confs = boxes.conf.cpu().tolist()

            for box, track_id, class_id, conf in zip(xyxy, ids, class_ids, confs):
                class_name = model.names[class_id]
                if class_name != CLASS_TYPE:
                    continue

                x1, y1, x2, y2 = map(int, box)

                if conf >= CONF_THRESHOLD and track_id not in tracked_ids:
                    tracked_ids.add(track_id)
                    sheep_count += 1
                    print(f"[{sheep_count}] Nova ovelha ID {track_id} | Confiança: {conf:.2f}")

                color = (0, 255, 0) if track_id in tracked_ids else (255, 0, 0)
                cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), color, 2)
                cv2.putText(annotated_frame, f"{class_name} #{track_id}", (x1, y1 - 5),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)

        # Enviar frame via WebSocket
        _, buffer = cv2.imencode(".jpg", annotated_frame)
        await websocket.send_bytes(buffer.tobytes())
        await asyncio.sleep(0.01)  # ~20 FPS

    print("Transmissão de frames terminada.")



@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("Servidor conectado ao WebSocket.")
    capture = None
    stop_event = asyncio.Event()
    frame_task = None
    area_points = []

    try:
        print(f"Dispositivo do modelo: {next(model.model.parameters()).device}")

        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            msg_type = message.get("type")

            # Inicia streaming de vídeo
            if msg_type == "video":

                params = message.get("params", {})
                cam_value = params.get("camera")
                area_points = params.get("area", [])

                # Fecha capturas anteriores
                if capture:
                    capture.release()

                # Cria nova captura (câmara ou vídeo)
                try:
                    cam_index = int(cam_value)
                    capture = cv2.VideoCapture(cam_index)
                    print(f"A usar câmara: {cam_index}")
                except (ValueError, TypeError):
                    capture = cv2.VideoCapture(cam_value)
                    print(f"A reproduzir vídeo: {cam_value}")

                if not capture.isOpened():
                    await websocket.send_text(json.dumps({"error": f"Não foi possível abrir {cam_value}"}))
                    continue

                await websocket.send_text(json.dumps({
                    "status": "camera_set",
                    "camera": cam_value,
                    "area": area_points
                }))

                # Inicia tarefa de streaming
                if frame_task is None or frame_task.done():
                    stop_event.clear()
                    frame_task = asyncio.create_task(
                        stream_frames(websocket, capture, stop_event, area_points)
                    )

            # Parar streaming
            elif msg_type == "stop":
                stop_event.set()
                await websocket.send_text(json.dumps({"status": "stopped"}))

            # Comando genérico
            elif msg_type == "command":
                await websocket.send_text(json.dumps({"status": "command"}))

            else:
                await websocket.send_text(json.dumps({"error": f"Tipo não reconhecido: {msg_type}"}))

    except Exception as e:
        print("Conexão encerrada:", e)
        if capture:
            capture.release()
        stop_event.set()
