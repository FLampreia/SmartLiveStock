from auth import get_password_hash
import sqlite3

#=================================
# Configuração
#=================================

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
    ("view1", get_password_hash("viewer123"), "viewer1@localhost", "Viewer One"),
    ("view2", get_password_hash("viewer456"), "viewer2@localhost", "Viewer Two")
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
    ("Admin", "Full access: manage users, configure cameras, adjust AI, access all reports and logs."),
    ("Operator", "Controls cameras, starts/stops sheep counting, accesses counting reports, but cannot change system configuration."),
    ("Viewer", "Only views counting data and statistics, without making any changes."),
    ("DataExporter", "Can export reports or statistics.")
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
    (4, 3),  # view1 → viewer
    (5, 3),  # view2 → viewer
    (1, 4),  # admin → dataExporter
    (4, 4)   # view1 → dataExporter
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
