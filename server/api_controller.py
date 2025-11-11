from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
import sqlite3
import os
from dotenv import load_dotenv
from .auth import verify_password, create_access_token, decode_access_token

load_dotenv("server/.env")


# Configuração CORS
origins = os.getenv("FRONTEND_ORIGINS", "").split(",")
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_PATH = os.getenv("DB_PATH", "server/smartlivestock.db")

# Configuração OAuth2
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

@app.get("/")
def root():
    return {"Hello": "World SmartLiveStock!"}

# Função para autenticar utilizador na base de dados
def authenticate_user(username: str, password: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT username, password FROM users WHERE username=?", (username,))
    user = cursor.fetchone()
    conn.close()
    if not user:
        return False
    db_username, db_password = user
    if not verify_password(password, db_password):
        return False
    return {"username": db_username}

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

# Exemplo de rota protegida
@app.get("/protected")
def protected_route(current_user: str = Depends(get_current_user)):
    return {"message": f"Hello {current_user}, you have access!"}
