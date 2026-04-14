import sqlite3
import hashlib
import os
import threading

DB_PATH = "database/cache.sqlite"
_db_lock = threading.Lock()

def _get_connection():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.execute('''
        CREATE TABLE IF NOT EXISTS translations (
            hash_id TEXT,
            epub_filename TEXT,
            translated_text TEXT,
            PRIMARY KEY(hash_id, epub_filename)
        )
    ''')
    conn.commit()
    return conn

_conn = _get_connection()

def _get_hash(text: str) -> str:
    return hashlib.md5(text.encode('utf-8')).hexdigest()

def get_cached_translation(original_text: str, epub_filename: str) -> str:
    with _db_lock:
        cursor = _conn.cursor()
        cursor.execute('SELECT translated_text FROM translations WHERE hash_id = ? AND epub_filename = ?', (_get_hash(original_text), epub_filename))
        row = cursor.fetchone()
        return row[0] if row else None

def save_translation(original_text: str, translated_text: str, epub_filename: str):
    with _db_lock:
        try:
            cursor = _conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO translations (hash_id, epub_filename, translated_text)
                VALUES (?, ?, ?)
            ''', (_get_hash(original_text), epub_filename, translated_text))
            _conn.commit()
        except Exception as e:
            print(f"\n[WARNING] Failed to save to cache DB: {e}")

def clear_cache_for_epub(epub_filename: str):
    """Deletes cached translations for a specific EPUB file upon success."""
    with _db_lock:
        try:
            cursor = _conn.cursor()
            cursor.execute('DELETE FROM translations WHERE epub_filename = ?', (epub_filename,))
            _conn.commit()
        except Exception as e:
            print(f"\n[WARNING] Failed to clear cache for {epub_filename}: {e}")
