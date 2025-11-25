import sqlite3
import os

DB_PATH = "smartlivestock.db"

# Delete database if exists
if os.path.exists(DB_PATH):
    os.remove(DB_PATH)
    print("Base de dados recriada com sucesso.")
else:
    print("A base de dados não existia.")

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

cursor.execute("""
CREATE TABLE IF NOT EXISTS cameras (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    location TEXT NOT NULL,
    resolution INTEGER NOT NULL,
    fps INTEGER NOT NULL,
    model TEXT NOT NULL,
    ip_address TEXT UNIQUE NOT NULL,
    installation_date TIMESTAMP NOT NULL,
    last_maintenance_date TIMESTAMP NOT NULL,
    orientation TEXT,
    notes TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS counts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    id_camera INTEGER NOT NULL,
    id_user INTEGER NOT NULL,
    id_area INTEGER NOT NULL,
    count_number INTEGER NOT NULL,
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP NOT NULL CHECK (end_time > start_time),
    duration INTEGER NOT NULL,
    
    FOREIGN KEY (id_camera) REFERENCES cameras (id),
    FOREIGN KEY (id_user) REFERENCES users (id),
    FOREIGN KEY (id_area) REFERENCES areas (id)
)
""")

cursor.execute("""
CREATE TRIGGER IF NOT EXISTS trg_counts_set_duration
BEFORE INSERT ON counts
FOR EACH ROW
BEGIN
    SELECT
        NEW.duration = CAST(
            (julianday(NEW.end_time) - julianday(NEW.start_time)) * 86400
            AS INTEGER
        );
END;
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS vertices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    x_pos REAL NOT NULL,
    y_pos REAL NOT NULL,
    
    UNIQUE (x_pos, y_pos)
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS areas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS areaVertices (
    id_area INTEGER NOT NULL,
    id_vertices INTEGER NOT NULL,
    order_index INTEGER NOT NULL CHECK (order_index > 0),
    
    PRIMARY KEY (id_area, id_vertices),
    FOREIGN KEY (id_area) REFERENCES areas (id),
    FOREIGN KEY (id_vertices) REFERENCES vertices (id),
    
    UNIQUE (id_area, order_index)
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS frames (
    frame_number INTEGER NOT NULL,
    id_count INTEGER NOT NULL,
    num_counts_frame INTEGER NOT NULL,
    captured_time TIMESTAMP NOT NULL,
    image BLOB NOT NULL,
    
    PRIMARY KEY (frame_number, id_count),
    FOREIGN KEY (id_count) REFERENCES counts (id)    
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS reportInfo (
    id INTEGER PRIMARY KEY AUTOINCREMENT, 
    creation_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    interval_start TEXT NOT NULL,
    interval_end TEXT NOT NULL,
    
    UNIQUE (interval_start, interval_end)
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS reportInfoCount (
    id_counts INTEGER NOT NULL, 
    id_reports INTEGER NOT NULL, 
    
    PRIMARY KEY (id_counts, id_reports),
    FOREIGN KEY (id_counts) REFERENCES counts (id),
    FOREIGN KEY (id_reports) REFERENCES reportInfo (id)
)
""")

# Save and Close connection
conn.commit()
conn.close()
