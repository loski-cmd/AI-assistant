import sqlite3

# Connect to your existing database
conn = sqlite3.connect('chat_memory.db')
cursor = conn.cursor()

# Create user_profile table
cursor.execute('''
CREATE TABLE IF NOT EXISTS user_profile (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    mood TEXT,
    trading_goal TEXT
)
''')

conn.commit()
conn.close()

print("✅ User profile table created successfully!")
