from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from pydantic import BaseModel

origins = os.getenv("SERVER_ORIGINS", "").split(",")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Command(BaseModel):
    action: str
    params: dict | None = None

@app.post("/command")
async def receive_command(cmd: Command):
    if cmd.action == "start":
        # Aqui chamarias o teu detector
        print("Iniciar contagem com parâmetros:", cmd.params)
        return {"status": "started"}
    elif cmd.action == "stop":
        print("Parar contagem")
        return {"status": "stopped"}
    elif cmd.action == "set_params":
        print("Atualizar parâmetros:", cmd.params)
        return {"status": "params_updated"}
    else:
        return {"error": "Ação desconhecida"}