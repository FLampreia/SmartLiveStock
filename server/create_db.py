import sqlite3
import os
from dotenv import load_dotenv

# Load .env variables
load_dotenv("server/.env")
DB_PATH = "smartlivestock.db"

# Delete database if exists
if os.path.exists(DB_PATH):
    os.remove(DB_PATH)
    print("Base de dados apagada com sucesso.")
else:
    print("A base de dados não existe.")

# Connect/create database
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Create Users table
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    full_name TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL 
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS roles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    description TEXT NOT NULL
)""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS userRoles (
    id_user INTEGER NOT NULL,
    id_role INTEGER NOT NULL,
    PRIMARY KEY (id_user, id_role),
    FOREIGN KEY (id_user) REFERENCES users (id),
    FOREIGN KEY (id_role) REFERENCES roles (id)
)
""")


# Save and Close connection
conn.commit()
conn.close()
