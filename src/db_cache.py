import sqlite3
import hashlib
import os
from src.config import DB_PATH

def _get_connection():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.execute('''
        CREATE TABLE IF NOT EXISTS translations (
            hash_id TEXT PRIMARY KEY,
            translated_text TEXT
        )
    ''')
    conn.commit()
    return conn

_conn = _get_connection()

def _get_hash(text: str) -> str:
    return hashlib.md5(text.encode('utf-8')).hexdigest()

def get_cached_translation(original_text: str) -> str:
    cursor = _conn.cursor()
    cursor.execute('SELECT translated_text FROM translations WHERE hash_id = ?', (_get_hash(original_text),))
    row = cursor.fetchone()
    return row[0] if row else None

def save_translation(original_text: str, translated_text: str):
    cursor = _conn.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO translations (hash_id, translated_text)
        VALUES (?, ?)
    ''', (_get_hash(original_text), translated_text))
    _conn.commit()
