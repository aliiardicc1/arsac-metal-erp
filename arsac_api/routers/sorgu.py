"""
Arsac Metal ERP — Generic SQL Sorgu Router
==========================================
Client'tan gelen SQL sorgularını çalıştırır.
SQLite → PostgreSQL syntax dönüşümü burada.
"""
import re
from fastapi import APIRouter, Depends, HTTPException
from core.database import get_db
from core.auth import token_dogrula
from models.schemas import SorguIstek

router = APIRouter(tags=["Sorgu"])


def sqlite_to_pg(sql: str) -> str:
    """SQLite sorgusunu PostgreSQL'e çevirir."""
    sql = sql.replace("?", "%s")
    sql = sql.replace("date('now')", "CURRENT_DATE")
    sql = sql.replace("date(%s, '-7 days')", "(CURRENT_DATE - INTERVAL '7 days')")
    sql = sql.replace("INSERT OR IGNORE INTO", "INSERT INTO")
    sql = sql.replace("INSERT OR REPLACE INTO", "INSERT INTO")
    sql = re.sub(r"HAVING\s+(\w+)\s+<", r"HAVING SUM(\1) <", sql)
    return sql


@router.post("/sorgu")
def sorgu_calistir(
    istek: SorguIstek,
    kullanici: str = Depends(token_dogrula),
    db=Depends(get_db)
):
    conn, cursor = db
    sql = sqlite_to_pg(istek.sql)
    params = istek.params or []

    try:
        cursor.execute(sql, params)
        try:
            rows = cursor.fetchall()
            result_rows = [dict(r) for r in rows]
        except Exception:
            result_rows = []
        conn.commit()
        return {
            "rows":      result_rows,
            "rowcount":  cursor.rowcount,
            "lastrowid": None
        }
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))
