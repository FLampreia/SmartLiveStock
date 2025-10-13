from fastapi import FastAPI
import sqlite3

app = FastAPI()

DB_PATH = "web/smartlivestock.db"


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