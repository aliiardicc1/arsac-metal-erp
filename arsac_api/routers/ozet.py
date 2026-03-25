"""
Arsac Metal ERP — Dashboard Özet Router
"""
from fastapi import APIRouter, Depends
from core.database import get_db
from core.auth import token_dogrula

router = APIRouter(tags=["Özet"])


@router.get("/ozet")
def ozet_getir(db=Depends(get_db), _=Depends(token_dogrula)):
    conn, cursor = db

    def _say(sql, params=()):
        try:
            cursor.execute(sql, params)
            r = cursor.fetchone()
            return list(r.values())[0] if r else 0
        except:
            return 0

    def _toplam(sql, params=()):
        try:
            cursor.execute(sql, params)
            r = cursor.fetchone()
            v = list(r.values())[0] if r else 0
            return float(v or 0)
        except:
            return 0.0

    # Stok
    depoda_sac  = _say("SELECT COUNT(*) FROM stok WHERE durum=1")
    yolda_sac   = _say("SELECT COUNT(*) FROM stok WHERE durum=0")
    toplam_kg   = _toplam("SELECT SUM(kg) FROM stok WHERE durum=1")

    # Talepler
    bekleyen_talep = _say("SELECT COUNT(*) FROM talepler WHERE durum=0")

    # Siparişler
    aktif_siparis  = _say("SELECT COUNT(*) FROM siparisler WHERE durum NOT IN ('Teslim Edildi','İptal')")
    bugun_termin   = _say("""
        SELECT COUNT(*) FROM siparisler
        WHERE durum NOT IN ('Teslim Edildi','İptal')
        AND termin = TO_CHAR(CURRENT_DATE, 'DD.MM.YYYY')
    """)

    # Üretim
    aktif_is     = _say("SELECT COUNT(*) FROM isler WHERE durum NOT IN ('Tamamlandı','İptal')")
    bekleyen_uretim = _say("SELECT COUNT(*) FROM parcalar WHERE durum='Beklemede'")

    # Finans
    toplam_borc  = _toplam("SELECT SUM(toplam_tutar) FROM satinalma_kayitlari WHERE odendi=0 OR odendi IS NULL")
    vadesi_gecmis = _say("""
        SELECT COUNT(*) FROM satinalma_kayitlari
        WHERE (odendi=0 OR odendi IS NULL)
        AND vade_tarihi IS NOT NULL
        AND vade_tarihi != ''
        AND TO_DATE(vade_tarihi, 'DD.MM.YYYY') < CURRENT_DATE
    """)

    # Kritik stok
    try:
        cursor.execute("""
            SELECT COUNT(*) FROM (
                SELECT malzeme, SUM(kg) as topkg
                FROM stok GROUP BY malzeme
                HAVING SUM(kg) < 500
            ) t
        """)
        r = cursor.fetchone()
        kritik_stok = list(r.values())[0] if r else 0
    except:
        kritik_stok = 0

    # Son 5 sipariş
    try:
        cursor.execute("""
            SELECT sip_no, musteri, durum, genel_toplam, tarih
            FROM siparisler ORDER BY id DESC LIMIT 5
        """)
        son_siparisler = [dict(r) for r in cursor.fetchall()]
    except:
        son_siparisler = []

    return {
        "stok": {
            "depoda_sac":  depoda_sac,
            "yolda_sac":   yolda_sac,
            "toplam_kg":   round(toplam_kg, 1),
            "kritik_stok": kritik_stok,
        },
        "talepler": {
            "bekleyen": bekleyen_talep,
        },
        "siparisler": {
            "aktif":       aktif_siparis,
            "bugun_termin": bugun_termin,
        },
        "uretim": {
            "aktif_is":        aktif_is,
            "bekleyen_uretim": bekleyen_uretim,
        },
        "finans": {
            "toplam_borc":   round(toplam_borc, 2),
            "vadesi_gecmis": vadesi_gecmis,
        },
        "son_siparisler": son_siparisler,
    }
