"""
Arsac Metal ERP — PostgreSQL Bağlantı Katmanı
==============================================
• psycopg2 ThreadedConnectionPool (min:2 max:20)
• RealDictCursor — satırlar dict olarak döner
• .env veya ortam değişkeninden bağlantı bilgisi
• get_db() FastAPI Depends ile kullanılır
"""
import os
import psycopg2
from psycopg2 import pool as pg_pool
from psycopg2.extras import RealDictCursor

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://arsac_user:arsac_pass@localhost:5432/arsac_db"
)

_pool: pg_pool.ThreadedConnectionPool | None = None


def get_pool() -> pg_pool.ThreadedConnectionPool:
    global _pool
    if _pool is None or _pool.closed:
        _pool = pg_pool.ThreadedConnectionPool(
            minconn=2,
            maxconn=20,
            dsn=DATABASE_URL
        )
    return _pool


def get_db():
    """FastAPI Depends ile kullanılır. (conn, cursor) döner."""
    p = get_pool()
    conn = p.getconn()
    conn.autocommit = False
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    try:
        yield conn, cursor
    finally:
        cursor.close()
        try:
            p.putconn(conn)
        except Exception:
            pass


def db_saglik() -> dict:
    """Sağlık kontrolü için ping."""
    try:
        p = get_pool()
        conn = p.getconn()
        cur = conn.cursor()
        cur.execute("SELECT 1")
        cur.close()
        p.putconn(conn)
        return {"durum": "ok", "veritabani": "PostgreSQL"}
    except Exception as e:
        return {"durum": "hata", "detay": str(e)}
