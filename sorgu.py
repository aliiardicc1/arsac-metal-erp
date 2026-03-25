"""
Arsac Metal ERP — Güvenli Sorgu Router
"""
import re
from fastapi import APIRouter, Depends, HTTPException
from core.database import get_db
from core.auth import token_dogrula
from models.schemas import SorguIstek

router = APIRouter(tags=["Sorgu"])

ENGELLI = [r'\bDROP\b', r'\bTRUNCATE\b', r'\bALTER\b', r'\bCREATE\b', r'\bGRANT\b']

def sqlite_to_pg(sql):
    sql = sql.replace("?", "%s")
    sql = sql.replace("date('now')", "CURRENT_DATE")
    sql = sql.replace("date(%s, '-7 days')", "(CURRENT_DATE - INTERVAL '7 days')")
    sql = sql.replace("INSERT OR IGNORE INTO", "INSERT INTO")
    sql = sql.replace("INSERT OR REPLACE INTO", "INSERT INTO")
    sql = re.sub(r"HAVING\s+(\w+)\s+<", r"HAVING SUM(\1) <", sql)
    return sql

@router.post("/sorgu")
def sorgu_calistir(istek: SorguIstek, kullanici: str = Depends(token_dogrula), db=Depends(get_db)):
    for pattern in ENGELLI:
        if re.search(pattern, istek.sql.upper()):
            raise HTTPException(status_code=403, detail="Guvenlik: Bu komut kullanilamaz")
    conn, cursor = db
    sql = sqlite_to_pg(istek.sql)

    # INSERT sorgularına RETURNING id ekle — lastrowid almak için
    sql_upper = sql.strip().upper()
    is_insert = sql_upper.startswith("INSERT")
    if is_insert and "RETURNING" not in sql_upper:
        sql = sql.rstrip().rstrip(";") + " RETURNING id"

    try:
        cursor.execute(sql, istek.params or [])
        lastrowid = None
        rows = []
        try:
            raw = cursor.fetchall()
            if raw:
                rows = [dict(r) for r in raw]
                # INSERT RETURNING id — ilk satırdan id'yi al, rows'u temizle
                if is_insert and rows and "id" in rows[0]:
                    lastrowid = rows[0]["id"]
                    rows = []
        except:
            pass
        conn.commit()
        return {"rows": rows, "rowcount": cursor.rowcount, "lastrowid": lastrowid}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))