import sqlite3

# Connect (creates the DB file if it doesn't exist)
conn = sqlite3.connect('chat_memory.db')
cursor = conn.cursor()

# Create a chat_memory table
cursor.execute('''
CREATE TABLE IF NOT EXISTS chat_memory (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_input TEXT,
    ai_response TEXT
)
''')

conn.commit()
conn.close()

print("SQLite chat_memory.db created with chat_memory table!")
