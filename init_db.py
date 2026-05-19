import sqlite3
import os

def init_db():
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'database.db')
    schema_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'sql', 'schema.sql')
    conn = sqlite3.connect(db_path)
    with open(schema_path, 'r') as f:
        conn.executescript(f.read())
    conn.commit()
    conn.close()
    print("Database initialized successfully.")

if __name__ == '__main__':
    init_db()
