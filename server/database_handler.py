import sqlite3
from dotenv import load_dotenv
from .auth import verify_password
import os

#=================================
# Configuração
#=================================
load_dotenv("server/.env")
DB_PATH = os.getenv("DB_PATH", "server/smartlivestock.db")


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


def get_user_roles(current_user: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
    SELECT r.name
    FROM roles r
    JOIN userRoles ur ON ur.id_role = r.id
    JOIN users u ON ur.id_user = u.id
    WHERE u.username = ?
    """, (current_user,))

    roles = [row[0] for row in cursor.fetchall()]
    conn.close()
    return roles
