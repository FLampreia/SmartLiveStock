from fastapi import FastAPI, WebSocket
import cv2
import json
import asyncio
import numpy as np
from ultralytics import YOLO

width = 640
height = 480
class_type = "sheep"
conf_threshold = 0.88
app = FastAPI()



async def stream_frames(websocket: WebSocket, capture: cv2.VideoCapture, area_points: list, model, stop_event: asyncio.Event):
    """Envia frames continuamente com a área desenhada enquanto o stop_event não estiver ativo."""
    print("Início da transmissão de frames.")
    while not stop_event.is_set():
        success, frame = capture.read()

        # Reinicia o vídeo se terminou (para loop)
        if not success:
            capture.set(cv2.CAP_PROP_POS_FRAMES, 0)
            await asyncio.sleep(0.1)
            continue

        # Desenha a área, se existir
        if area_points:
            pts = np.array(area_points, np.int32)
            pts = pts.reshape((-1, 1, 2))
            cv2.polylines(frame, [pts], isClosed=True, color=(0, 255, 0), thickness=2)

        # Codifica e envia o frame
        _, buffer = cv2.imencode(".jpg", frame)
        await websocket.send_bytes(buffer.tobytes())

        await asyncio.sleep(0.05)  # 20 FPS aprox.

    print("Transmissão de frames terminada.")


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("Cliente conectado ao WebSocket.")
    capture = None
    stop_event = asyncio.Event()
    frame_task = None

    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            msg_type = message.get("type")

            # Inicia streaming de vídeo
            if msg_type == "video":
                await websocket.send_text(json.dumps({"status": "video"}))

                params = message.get("params", {})
                cam_value = params.get("camera")
                area = params.get("area", [])
                model = params.get("model")

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
                    "area": area
                }))

                # Inicia tarefa de streaming
                if frame_task is None or frame_task.done():
                    stop_event.clear()
                    frame_task = asyncio.create_task(stream_frames(websocket, capture, area, model, stop_event))

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
