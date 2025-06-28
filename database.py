import sqlite3
import json
import os

DB_NAME = "claims.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    # Create users table
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                 id INTEGER PRIMARY KEY AUTOINCREMENT,
                 username TEXT UNIQUE NOT NULL,
                 password TEXT NOT NULL,
                 created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    
    # Create claims table
    c.execute('''CREATE TABLE IF NOT EXISTS claims (
                 id INTEGER PRIMARY KEY AUTOINCREMENT,
                 user_id INTEGER NOT NULL,
                 claim_type TEXT NOT NULL,
                 input_text TEXT NOT NULL,
                 output_json TEXT NOT NULL,
                 created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                 FOREIGN KEY(user_id) REFERENCES users(id))''')
    
    conn.commit()
    conn.close()

def log_claim(user_id, claim_type, input_text, output_json):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''INSERT INTO claims (user_id, claim_type, input_text, output_json)
                 VALUES (?, ?, ?, ?)''', 
              (user_id, claim_type, input_text, json.dumps(output_json)))
    conn.commit()
    conn.close()

def get_claim_history(user_id, limit=10):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''SELECT id, claim_type, input_text, output_json, created_at 
                 FROM claims 
                 WHERE user_id = ? 
                 ORDER BY created_at DESC 
                 LIMIT ?''', (user_id, limit))
    claims = c.fetchall()
    conn.close()
    
    # Parse JSON output
    result = []
    for claim in claims:
        claim_id, claim_type, input_text, output_json, created_at = claim
        result.append({
            "id": claim_id,
            "claim_type": claim_type,
            "input_text": input_text[:100] + "..." if len(input_text) > 100 else input_text,
            "output": json.loads(output_json),
            "created_at": created_at
        })
    return result

def add_user(username, password):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    try:
        c.execute('''INSERT INTO users (username, password)
                     VALUES (?, ?)''', 
                  (username, password))
        conn.commit()
        return c.lastrowid  # Return new user ID
    except sqlite3.IntegrityError:
        return None  # Username already exists
    finally:
        conn.close()

def get_user(username):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''SELECT id, password FROM users WHERE username = ?''', (username,))
    user = c.fetchone()
    conn.close()
    return user

# Initialize database on import
init_db()