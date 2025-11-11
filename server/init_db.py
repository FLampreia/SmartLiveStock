import sqlite3
from auth import get_password_hash
import os
from dotenv import load_dotenv

# Carregar variáveis do .env
load_dotenv("server/.env")
DB_PATH = "smartlivestock.db"

# Conectar/criar a base de dados
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Criar tabela users (se não existir)
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL
)
""")

# Criar um utilizador de teste
username = "admin"
password = "admin123"
hashed_password = get_password_hash(password)

# print(hashed_password)

# Verificar se o utilizador já existe
cursor.execute("SELECT * FROM users WHERE username=?", (username,))
if not cursor.fetchone():
    cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed_password))
    print(f"Utilizador '{username}' criado com sucesso.")
else:
    print(f"Utilizador '{username}' já existe.")

# Guardar alterações e fechar conexão
conn.commit()
conn.close()
