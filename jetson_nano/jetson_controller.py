from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import cv2
import json
import asyncio
import numpy as np
from ultralytics import YOLO

SHOW_LOCAL = True

FRAME_WIDTH = 640
FRAME_HEIGHT = 480
CLASS_TYPE = "sheep"
CONF_THRESHOLD = 0.80
MODEL_PATH = "jetson_nano/models/yolo11n.pt"

app = FastAPI()
model = YOLO(MODEL_PATH)
model.to('cuda')

sheep_count = 0
tracked_ids = set()


# ==============================================================
# Função de streaming com deteção e área
# ==============================================================
async def stream_frames(websocket: WebSocket, capture: cv2.VideoCapture, stop_event: asyncio.Event,
                        area_points=None, msg_detect=None):
    global sheep_count, tracked_ids

    sheep_count = 0
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
            mask = np.ones((FRAME_HEIGHT, FRAME_WIDTH), dtype=np.uint8) * 255 #TODO multiplica por 255 para colocar inicialmente todo o frame como mask
            annotated_frame = frame.copy()

            # Se há área definida, desenhar
            if area_points:
                # print("Área recebida:", area_points)

                mask = np.zeros((FRAME_HEIGHT, FRAME_WIDTH), dtype=np.uint8)
                pts = np.array(area_points, np.int32)
                hull = cv2.convexHull(pts)

                # desenhar contorno visível
                cv2.polylines(annotated_frame, [hull], isClosed=True, color=(255, 255, 0), thickness=2)

                # preencher área dentro do polígono
                cv2.fillPoly(mask, [hull], 255)



            # Executar deteção e tracking
            if msg_detect:
                result = model.track(frame, persist=True, verbose=False)

                if result[0] is not None and result[0].boxes.id is not None:
                    boxes = result[0].boxes
                    xyxy = boxes.xyxy.cpu().tolist()
                    ids = boxes.id.cpu().tolist()
                    class_ids = boxes.cls.int().cpu().tolist()
                    confs = boxes.conf.cpu().tolist()

                    for box, track_id, class_id, conf in zip(xyxy, ids, class_ids, confs):
                        class_name = model.names[class_id]

                        # tem de ser ovelha
                        if class_name != CLASS_TYPE:
                            continue

                        x1, y1, x2, y2 = map(int, box)
                        obj_x = int((x1 + x2) / 2)  # centro X do bounding box
                        obj_y = int((y1 + y2) / 2)  # centro Y do bounding box

                        # ✅ verifica se o ponto central está dentro da área (ou toda a janela)
                        inside_area = mask[obj_y, obj_x] > 0  # > 0 porque a máscara tem 255 em zonas válidas

                        if conf >= CONF_THRESHOLD and inside_area and track_id not in tracked_ids:
                            tracked_ids.add(track_id)
                            sheep_count += 1
                            print(f"[{sheep_count}] Nova ovelha ID {track_id} | Confiança: {conf:.2f}")

                        # ✅ desenha o retângulo e ID
                        color = (0, 255, 0) if track_id in tracked_ids else (255, 0, 0)
                        cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), color, 2)
                        cv2.putText(annotated_frame, f"{class_name} #{track_id}",
                                    (x1, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)

            if SHOW_LOCAL:
                # Mostrar frame localmente
                cv2.imshow("SmartLiveStock Stream", annotated_frame)

                if cv2.waitKey(1) & 0xFF == ord('q'):
                    stop_event.set()
                    print("Transmissão interrompida localmente com 'q'.")
                    break

            # Enviar frame via WebSocket
            _, buffer = cv2.imencode(".jpg", annotated_frame)
            try:
                await websocket.send_bytes(buffer.tobytes())
            except WebSocketDisconnect:
                print("Cliente desconectou-se — encerrando stream.")
                stop_event.set()
                break

            # await asyncio.sleep(0.01)  # ~20 FPS

    finally:
        capture.release()
        cv2.destroyAllWindows()
        print("Transmissão encerrada e janela fechada.")


# ==============================================================
# Endpoint WebSocket — duas tarefas independentes
# ==============================================================
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("Servidor conectado ao WebSocket.")

    capture = None
    stop_event = asyncio.Event()
    frame_task = None

    try:
        print(f"Dispositivo do modelo: {next(model.model.parameters()).device}")

        while True:
            try:
                data = await websocket.receive_text()
            except WebSocketDisconnect:
                print("Cliente fechou o WebSocket.")
                stop_event.set()
                break

            message = json.loads(data)
            msg_type = message.get("type")

            if msg_type == "video":
                msg_params = message.get("params", {})
                msg_camera = msg_params.get("camera")
                msg_detect = msg_params.get("detect")
                area_points = msg_params.get("area", [])

                if frame_task and not frame_task.done():
                    stop_event.set()
                    await frame_task
                    stop_event.clear()

                if capture:
                    capture.release()

                try:
                    cam_index = int(msg_camera)
                    capture = cv2.VideoCapture(cam_index)
                    print(f"A usar câmara: {cam_index}")
                except (ValueError, TypeError):
                    capture = cv2.VideoCapture(msg_camera)
                    print(f"A reproduzir vídeo: {msg_camera}")

                if not capture.isOpened():
                    await websocket.send_text(json.dumps({"error": f"Não foi possível abrir {msg_camera}"}))
                    continue

                await websocket.send_text(json.dumps({
                    "type": msg_type,
                    "camera": msg_camera,
                    "area": area_points
                }))

                frame_task = asyncio.create_task(
                    stream_frames(websocket, capture, stop_event, area_points, msg_detect)
                )

            elif msg_type == "stop":
                stop_event.set()
                await websocket.send_text(json.dumps({"status": "stopped"}))

    except Exception as e:
        print("Erro na conexão:", e)
        stop_event.set()
        if frame_task:
            await frame_task
        if capture:
            capture.release()
        cv2.destroyAllWindows()
        print("Conexão WebSocket encerrada.")
