from fastapi import FastAPI, WebSocket
from fastapi.responses import HTMLResponse
import sqlite3
import base64
import cv2 as cv2
app = FastAPI()

DB_PATH = "server/smartlivestock.db"


@app.get("/")
def root():
    return {"Hello": "World SmartLiveStock!"}


@app.get("/ovelhas/")
def listar_ovelhas():
    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()

    cursor.execute("SELECT * FROM ovelhas")
    ovelhas = cursor.fetchall()  # retorna lista de tuplos [(id, nome, idade), ...]

    cursor.close()
    connection.close()

    # Transformar para JSON
    resultado = [{"id": o[0], "nome": o[1], "idade": o[2]} for o in ovelhas]
    return resultado
