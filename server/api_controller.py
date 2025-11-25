from fastapi import FastAPI, HTTPException, Depends, status, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
import os
from dotenv import load_dotenv
from .auth import create_access_token, get_current_user
from .database_handler import authenticate_user, get_user_roles
import json
import asyncio
import websockets


load_dotenv("server/.env")

JETSON_WS_URL = os.getenv("JETSON_WS_URL")
# print(JETSON_WS_URL)

# Configuração CORS
ORIGINS = os.getenv("FRONTEND_ORIGINS", "").split(",")
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"Hello": "World SmartLiveStock!"}

# Endpoint de login para gerar token
@app.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Username or password incorrect",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": user["username"]})
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/protected")
def protected_route(current_user: str = Depends(get_current_user)):
    return {"message": f"Hello {current_user}, with roles {get_user_roles(current_user)}, you have access!"}

@app.websocket("/server_ws")
async def ws_endpoint(websocket: WebSocket):
    token_header = websocket.headers.get("Authorization")
    if not token_header or not token_header.startswith("Bearer "):
        await websocket.close(code=4401)
        return

    token = token_header.split(" ")[1]
    try:
        current_user = get_current_user(token)
    except Exception:
        await websocket.close(code=4401)
        return

    await websocket.accept()
    print(f"Cliente conectado ao server: {current_user}")

    jetson_ws = None
    jetson_task = None

    try:
        while True:
            try:
                message = json.loads(await websocket.receive_text())
            except WebSocketDisconnect:
                print("Cliente fechou a conexão.")
                break

            msg_type = message.get("type")

            if msg_type == "video":
                roles = get_user_roles(current_user)

                # enviar status ao browser
                await websocket.send_text(json.dumps({
                    "status": f"a mostrar video ao {current_user} com roles {roles}"

                }))

                print(jetson_ws)

                # enviar comando para a Jetson iniciar video
                if jetson_ws is not None:
                    try:
                        await jetson_ws.send(json.dumps(
                            {
                                "type": "video",
                                "params":
                                    {"detect": "true",
                                     "camera": "tests/data/sheepHerd1.mp4",
                                     "area": [
                                     ]
                                }
                            }))
                    except Exception as e:
                        print("Erro ao enviar comando de vídeo para Jetson:", e)
                        await websocket.send_text(json.dumps({"status": "erro_enviar_comando_jetson"}))


            elif msg_type == "jetson":
                msg_command = message.get("command")

                if msg_command == "connect" and jetson_ws is None:
                    try:
                        jetson_ws = await websockets.connect(JETSON_WS_URL)
                        print("Ligação aberta com a Jetson.")

                        await websocket.send_text(json.dumps({"status": "conectado_a_jetson"}))

                        # inicializar task paralela
                        jetson_task = asyncio.create_task(
                            relay_from_jetson(jetson_ws, websocket)
                        )

                    except Exception as e:
                        print("Erro ao ligar à Jetson:", e)
                        await websocket.send_text(json.dumps({"status": "erro_conectar_jetson"}))

                elif msg_command == "disconnect" and jetson_ws is not None:
                    if jetson_task:
                        jetson_task.cancel()
                    if jetson_ws:
                        await jetson_ws.close()
                        jetson_ws = None
                    await websocket.send_text(json.dumps({"status": "jetson_desconectada"}))

    except Exception as e:
        print("Erro na conexão:", e)

    finally:
        print("Conexão encerrada.")
        if jetson_task:
            jetson_task.cancel()
        if jetson_ws:
            await jetson_ws.close()

async def relay_from_jetson(jetson_ws, browser_ws):
    try:
        while True:
            msg = await jetson_ws.recv()
            await browser_ws.send_text(msg)
    except Exception as e:
        print("Jetson desconectou:", e)
        try:
            await browser_ws.send_text(json.dumps({"status": "jetson_disconnected"}))
        except:
            pass
