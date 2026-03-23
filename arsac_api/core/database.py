"""
Arsac Metal ERP — Veritabanı Bağlantı Yöneticisi
=================================================
Tek yerden bağlantı yönetimi.
"""
import os
import psycopg2
import psycopg2.extras

DB_CONFIG = {
    "host":     os.environ.get("DB_HOST", "localhost"),
    "port":     os.environ.get("DB_PORT", "5432"),
    "dbname":   os.environ.get("DB_NAME", "arsac_db"),
    "user":     os.environ.get("DB_USER", "arsac_user"),
    "password": os.environ.get("DB_PASS", "arsac2024"),
}

def get_db():
    """FastAPI Depends ile kullanılır. Her istek için bağlantı açar/kapatır."""
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    try:
        yield conn, cursor
    finally:
        conn.close()
