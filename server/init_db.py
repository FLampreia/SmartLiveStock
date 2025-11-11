from auth import get_password_hash
import sqlite3
from dotenv import load_dotenv
import os

#=================================
# Configuração
#=================================
load_dotenv("server/.env")
DB_PATH = "smartlivestock.db"

# Conectar à base de dados
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

#=================================
# Criar utilizadores
#=================================
users = [
    ("admin", get_password_hash("admin123"), "admin@localhost", "Administrator"),
    ("oper1", get_password_hash("operator123"), "operator1@localhost", "Operator One"),
    ("oper2", get_password_hash("operator456"), "operator2@localhost", "Operator Two"),
    ("view1", get_password_hash("viewer123"), "viewer1@localhost", "Viewer One")
]

cursor.executemany(
    "INSERT INTO users (username, password, email, full_name) VALUES (?, ?, ?, ?)",
    users
)
print("Utilizadores criados com sucesso.")

#=================================
# Criar roles
#=================================
roles = [
    ("admin", "Can access everything and configure everything"),
    ("operator", "Can start and stop counts, and request reports"),
    ("viewer", "Can only view information and reports")
]

cursor.executemany(
    "INSERT INTO roles (name, description) VALUES (?, ?)",
    roles
)
print("Roles criadas com sucesso.")

#=================================
# Associar roles aos utilizadores
#=================================
user_roles = [
    (1, 1),  # admin → admin
    (2, 2),  # oper1 → operator
    (3, 2),  # oper2 → operator
    (4, 3)   # view1 → viewer
]

cursor.executemany(
    "INSERT INTO userRoles (id_user, id_role) VALUES (?, ?)",
    user_roles
)
print("Associações entre utilizadores e roles criadas com sucesso.")

# Guardar alterações e fechar conexão
conn.commit()
conn.close()

print("Base de dados populada com sucesso.")
