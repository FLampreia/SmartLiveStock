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
MODEL_PATH = "jetson_nano/models/yolo11n.pt"

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
# Função de streaming com deteção e área
# ==============================================================
async def stream_frames(websocket: WebSocket, capture: cv2.VideoCapture, stop_event: asyncio.Event, shared_state):
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

            sh_area_points = shared_state.get("area")
            sh_detect_enabled = shared_state.get("detect")

            # Se há área definida, desenhar
            mask = np.ones((FRAME_HEIGHT, FRAME_WIDTH), dtype=np.uint8) * 255 #TODO multiplica por 255 para colocar inicialmente todo o frame como mask
            if sh_area_points:
                # print("Área recebida:", area_points)
                mask = np.zeros((FRAME_HEIGHT, FRAME_WIDTH), dtype=np.uint8)
                pts = np.array(sh_area_points, np.int32)
                hull = cv2.convexHull(pts)

                # desenhar contorno visível
                cv2.polylines(annotated_frame, [hull], isClosed=True, color=(255, 255, 0), thickness=2)

                # preencher área dentro do polígono
                cv2.fillPoly(mask, [hull], 255)


            # Executar deteção e tracking
            # new_detections = []
            if sh_detect_enabled: #modo detetar ativo
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
                        obj_x, obj_y = (x1 + x2) // 2, (y1 + y2) // 2

                        # ✅ verifica se o ponto central está dentro da área (ou toda a janela)
                        inside_area = mask[obj_y, obj_x] > 0  # > 0 porque a máscara tem 255 em zonas válidas

                        if conf >= CONF_THRESHOLD and inside_area and track_id not in tracked_ids:
                            flag_new_detections = True
                            tracked_ids.add(track_id)
                            sheep_count += 1
                            print(f"[{sheep_count}] Nova ovelha ID {track_id} | Confiança: {conf:.2f}")
                            #
                            # new_detections.append({
                            #     "sheep_id": int(track_id),
                            #     "count_num": sheep_count,
                            #     "confidence": float(conf),
                            #     "b_box": [x1, y1, x2, y2],
                            #     "c_point": [obj_x, obj_y]
                            # })

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
                if flag_new_detections:
                    frame_data = {
                        "type": "frame",
                        "camera_id": shared_state["camera"],
                        "timestamp": datetime.utcnow().isoformat(),
                        "new_detections": flag_new_detections,
                        "image": base64.b64encode(buffer).decode("utf-8")
                    }
                    flag_new_detections = False
                    await websocket.send_text(json.dumps(frame_data))

                await websocket.send_bytes(buffer.tobytes())
            except WebSocketDisconnect:
                print("Cliente desconectou-se — encerrando stream.")
                stop_event.set()
                break

            # await asyncio.sleep(0.01)  # ~20 FPS
            # await asyncio.sleep(1)  # ~20 FPS

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
                shared_state["camera"] = msg_params.get("camera")
                shared_state["detect"] = msg_params.get("detect")
                shared_state["area"] = msg_params.get("area", [])

                if frame_task and not frame_task.done():
                    stop_event.set()
                    await frame_task
                    stop_event.clear()

                if capture:
                    capture.release()

                try:
                    cam_index = int(shared_state["camera"])
                    capture = cv2.VideoCapture(cam_index)
                    print(f"A usar câmara: {cam_index}")
                except (ValueError, TypeError):
                    capture = cv2.VideoCapture(shared_state["camera"])
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