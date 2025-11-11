from fastapi import FastAPI, HTTPException, Depends, status, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
import os
from dotenv import load_dotenv
from .auth import create_access_token, decode_access_token
from .database_handler import authenticate_user, get_user_roles
import json
import asyncio
import websockets


load_dotenv("server/.env")

JETSON_WS_URL = os.getenv("JETSON_WS_URL")

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


# Configuração OAuth2
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

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

# Dependência para validar token e proteger rotas
def get_current_user(token: str = Depends(oauth2_scheme)):
    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return payload["sub"]


@app.get("/protected")
def protected_route(current_user: str = Depends(get_current_user)):
    return {"message": f"Hello {current_user}, with roles {get_user_roles(current_user)}, you have access!"}

@app.post("/conn_jetson")
async def connect_jetson(current_user: str = Depends(get_current_user)):
    """
    Testa se é possível conectar ao WebSocket da Jetson.
    Não envia nenhuma mensagem, apenas verifica se a conexão pode ser aberta.
    """
    try:
        async with websockets.connect(JETSON_WS_URL+"/ws") as websocket:
            # Conexão aberta com sucesso
            return {"status": "connected"}
    except Exception as e:
        return {"status": "error", "detail": str(e)}