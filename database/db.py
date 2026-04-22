import sqlite3
import json
from datetime import date, timedelta
from config import DATABASE_PATH


def get_conn():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_conn()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS daily_reports (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            tanggal     TEXT NOT NULL,
            hari        TEXT NOT NULL,
            nama_pic    TEXT NOT NULL,
            divisi      TEXT NOT NULL,
            lokasi      TEXT NOT NULL,
            shift       TEXT NOT NULL,
            cuaca       TEXT NOT NULL,
            kondisi_lapangan TEXT NOT NULL,
            ringkasan   TEXT NOT NULL,
            detail_kegiatan  TEXT NOT NULL,
            kendala     TEXT NOT NULL,
            koordinasi  TEXT NOT NULL,
            rencana_besok    TEXT NOT NULL,
            catatan_tambahan TEXT NOT NULL,
            created_at  TEXT DEFAULT (datetime('now'))
        )
    """)
    conn.commit()
    conn.close()


def save_report(data: dict) -> int:
    conn = get_conn()
    cur = conn.execute("""
        INSERT INTO daily_reports
            (tanggal, hari, nama_pic, divisi, lokasi, shift, cuaca,
             kondisi_lapangan, ringkasan, detail_kegiatan, kendala,
             koordinasi, rencana_besok, catatan_tambahan)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, (
        data["tanggal"],
        data["hari"],
        data["nama_pic"],
        data["divisi"],
        data["lokasi"],
        data["shift"],
        data["cuaca"],
        data["kondisi_lapangan"],
        json.dumps(data["ringkasan"], ensure_ascii=False),
        json.dumps(data["detail_kegiatan"], ensure_ascii=False),
        json.dumps(data["kendala"], ensure_ascii=False),
        json.dumps(data["koordinasi"], ensure_ascii=False),
        json.dumps(data["rencana_besok"], ensure_ascii=False),
        data["catatan_tambahan"],
    ))
    conn.commit()
    report_id = cur.lastrowid
    conn.close()
    return report_id


def get_reports_by_week(start_date: date, end_date: date) -> list[dict]:
    conn = get_conn()
    rows = conn.execute("""
        SELECT * FROM daily_reports
        WHERE tanggal BETWEEN ? AND ?
        ORDER BY tanggal ASC
    """, (start_date.isoformat(), end_date.isoformat())).fetchall()
    conn.close()

    reports = []
    for row in rows:
        r = dict(row)
        for field in ("ringkasan", "detail_kegiatan", "kendala", "koordinasi", "rencana_besok"):
            r[field] = json.loads(r[field])
        reports.append(r)
    return reports


def get_current_week_reports() -> list[dict]:
    today = date.today()
    monday = today - timedelta(days=today.weekday())
    saturday = monday + timedelta(days=5)
    return get_reports_by_week(monday, saturday)
