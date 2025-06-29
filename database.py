import sqlite3
import json
from datetime import datetime

def init_db():
    conn = sqlite3.connect('claims_ai.db')
    c = conn.cursor()
    
    # Create tables
    c.execute('''CREATE TABLE IF NOT EXISTS claims (
                 id INTEGER PRIMARY KEY AUTOINCREMENT,
                 claim_data TEXT NOT NULL,
                 status TEXT DEFAULT 'new',
                 created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS conversations (
                 id INTEGER PRIMARY KEY AUTOINCREMENT,
                 claim_id INTEGER NOT NULL,
                 role TEXT NOT NULL,
                 content TEXT NOT NULL,
                 timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                 FOREIGN KEY (claim_id) REFERENCES claims(id))''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS documents (
                 id INTEGER PRIMARY KEY AUTOINCREMENT,
                 claim_id INTEGER NOT NULL,
                 filename TEXT NOT NULL,
                 doc_type TEXT NOT NULL,
                 content TEXT,
                 analysis TEXT,
                 FOREIGN KEY (claim_id) REFERENCES claims(id))''')
    
    conn.commit()
    conn.close()

def save_claim(claim_data):
    conn = sqlite3.connect('claims_ai.db')
    c = conn.cursor()
    c.execute("INSERT INTO claims (claim_data) VALUES (?)", 
              (json.dumps(claim_data),))
    claim_id = c.lastrowid
    conn.commit()
    conn.close()
    return claim_id

def update_claim_status(claim_id, status):
    conn = sqlite3.connect('claims_ai.db')
    c = conn.cursor()
    c.execute("UPDATE claims SET status = ? WHERE id = ?", (status, claim_id))
    conn.commit()
    conn.close()

def save_message(claim_id, role, content):
    conn = sqlite3.connect('claims_ai.db')
    c = conn.cursor()
    c.execute("INSERT INTO conversations (claim_id, role, content) VALUES (?, ?, ?)",
              (claim_id, role, content))
    conn.commit()
    conn.close()

def save_document(claim_id, filename, doc_type, content, analysis=None):
    conn = sqlite3.connect('claims_ai.db')
    c = conn.cursor()
    c.execute('''INSERT INTO documents 
                 (claim_id, filename, doc_type, content, analysis) 
                 VALUES (?, ?, ?, ?, ?)''',
              (claim_id, filename, doc_type, content, 
               json.dumps(analysis) if analysis else None))
    conn.commit()
    conn.close()

def get_claim(claim_id):
    conn = sqlite3.connect('claims_ai.db')
    c = conn.cursor()
    c.execute("SELECT claim_data, status, created_at FROM claims WHERE id=?", (claim_id,))
    row = c.fetchone()
    conn.close()
    if row:
        return {
            "id": claim_id,
            "data": json.loads(row[0]),
            "status": row[1],
            "created_at": row[2]
        }
    return None

def get_claim_conversation(claim_id):
    conn = sqlite3.connect('claims_ai.db')
    c = conn.cursor()
    c.execute("SELECT role, content, timestamp FROM conversations WHERE claim_id=? ORDER BY timestamp", (claim_id,))
    rows = c.fetchall()
    conn.close()
    return [{"role": row[0], "content": row[1], "timestamp": row[2]} for row in rows]

def get_claim_documents(claim_id):
    conn = sqlite3.connect('claims_ai.db')
    c = conn.cursor()
    c.execute("SELECT id, filename, doc_type, analysis FROM documents WHERE claim_id=?", (claim_id,))
    rows = c.fetchall()
    conn.close()
    return [{
        "id": row[0],
        "filename": row[1],
        "type": row[2],
        "analysis": json.loads(row[3]) if row[3] else None
    } for row in rows]

def list_claims(limit=10):
    conn = sqlite3.connect('claims_ai.db')
    c = conn.cursor()
    c.execute("SELECT id, status, created_at FROM claims ORDER BY created_at DESC LIMIT ?", (limit,))
    claims = [{"id": row[0], "status": row[1], "created_at": row[2]} for row in c.fetchall()]
    conn.close()
    return claims