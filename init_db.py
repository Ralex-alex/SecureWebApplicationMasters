import sqlite3

conn = sqlite3.connect("database.db")

conn.execute("""
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT,
    password TEXT,
    role TEXT
)
""")

conn.execute("""
CREATE TABLE notes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT,
    content TEXT,
    user_id INTEGER
)
""")

conn.commit()
conn.close()

print("Database initialized.")
