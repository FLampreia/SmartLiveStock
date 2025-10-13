import sqlite3

# Conectar à base de dados
connection = sqlite3.connect("/home/lampreia/Projects/SmartLiveStock/web/server/smartlivestock.db")
cursor = connection.cursor()

cursor.execute('''
CREATE TABLE IF NOT EXISTS ovelhas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    idade INTEGER
)
''')
# Inserir dados de teste
ovelhas_teste = [
    ("Dolly", 3),
    ("Mimosa", 2),
    ("Flocos", 4)
]

cursor.executemany('''
INSERT INTO ovelhas (nome, idade) VALUES (?, ?)
''', ovelhas_teste)

connection.commit()
cursor.close()
connection.close()