import sqlite3
import hashlib
import os
import threading

_db_lock = threading.Lock()
_conns = {}

def _get_db_path(epub_filename: str) -> str:
    return f"database/cache_{epub_filename}.sqlite"

def _get_connection(epub_filename: str):
    with _db_lock:
        if epub_filename in _conns:
            return _conns[epub_filename]
        db_path = _get_db_path(epub_filename)
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        conn = sqlite3.connect(db_path, check_same_thread=False)
        conn.execute('''
            CREATE TABLE IF NOT EXISTS translations (
                hash_id TEXT,
                translated_text TEXT,
                PRIMARY KEY(hash_id)
            )
        ''')
        conn.commit()
        _conns[epub_filename] = conn
        return conn

def _get_hash(text: str) -> str:
    return hashlib.md5(text.encode('utf-8')).hexdigest()

def get_cached_translation(original_text: str, epub_filename: str) -> str:
    conn = _get_connection(epub_filename)
    with _db_lock:
        cursor = conn.cursor()
        cursor.execute('SELECT translated_text FROM translations WHERE hash_id = ?', (_get_hash(original_text),))
        row = cursor.fetchone()
        return row[0] if row else None

def save_translation(original_text: str, translated_text: str, epub_filename: str):
    conn = _get_connection(epub_filename)
    with _db_lock:
        try:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO translations (hash_id, translated_text)
                VALUES (?, ?)
            ''', (_get_hash(original_text), translated_text))
            conn.commit()
        except Exception as e:
            print(f"\n[WARNING] Failed to save to cache DB for {epub_filename}: {e}")

def clear_cache_for_epub(epub_filename: str):
    """Deletes the cached database file for a specific EPUB file upon completion."""
    with _db_lock:
        if epub_filename in _conns:
            _conns[epub_filename].close()
            del _conns[epub_filename]
        
        db_path = _get_db_path(epub_filename)
        if os.path.exists(db_path):
            try:
                os.remove(db_path)
            except Exception as e:
                print(f"\n[WARNING] Failed to delete cache file for {epub_filename}: {e}")
