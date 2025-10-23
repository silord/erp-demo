import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), 'sync_results.db')


def _get_conn():
    conn = sqlite3.connect(DB_PATH)
    return conn


def init_db():
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute('''
    CREATE TABLE IF NOT EXISTS sync_results (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        bill_key TEXT,
        erp_key TEXT,
        sync_state INTEGER,
        sync_msg TEXT,
        error_code INTEGER,
        created_at TEXT
    )
    ''')
    conn.commit()
    conn.close()


def save_result(bill_key, erp_key, sync_state, sync_msg, error_code):
    init_db()
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute('''
    INSERT INTO sync_results (bill_key, erp_key, sync_state, sync_msg, error_code, created_at)
    VALUES (?, ?, ?, ?, ?, ?)
    ''', (bill_key, erp_key, int(sync_state), sync_msg, int(error_code), datetime.utcnow().isoformat()))
    conn.commit()
    conn.close()


def list_results(limit=100):
    init_db()
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute('SELECT id, bill_key, erp_key, sync_state, sync_msg, error_code, created_at FROM sync_results ORDER BY id DESC LIMIT ?', (limit,))
    rows = cur.fetchall()
    conn.close()
    return rows
