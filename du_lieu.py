"""Luu tru va phan tich du lieu su dung he thong - Giai doan 2 (Anh Minh).

Du lieu metrics duoc luu vao SQLite de mo hinh hoc tang cuong dung sau nay.
"""

import csv
import os
import sqlite3

BANG_METRICS = """
CREATE TABLE IF NOT EXISTS metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    thoi_gian TEXT NOT NULL,
    gio INTEGER NOT NULL,
    cpu REAL NOT NULL,
    ram REAL NOT NULL,
    dia REAL NOT NULL,
    mang_gui INTEGER NOT NULL,
    mang_nhan INTEGER NOT NULL
)
"""


def khoi_tao_db(duong_dan):
    thu_muc = os.path.dirname(duong_dan)
    if thu_muc:
        os.makedirs(thu_muc, exist_ok=True)
    with sqlite3.connect(duong_dan) as ket_noi:
        ket_noi.execute(BANG_METRICS)
        ket_noi.commit()


def luu_metrics(duong_dan, metrics):
    khoi_tao_db(duong_dan)
    gio = int(metrics["thoi_gian"][11:13])
    with sqlite3.connect(duong_dan) as ket_noi:
        ket_noi.execute(
            "INSERT INTO metrics (thoi_gian, gio, cpu, ram, dia, mang_gui, mang_nhan)"
            " VALUES (?, ?, ?, ?, ?, ?, ?)",
            (metrics["thoi_gian"], gio, metrics["cpu"], metrics["ram"],
             metrics["dia"], metrics["mang_gui"], metrics["mang_nhan"]),
        )
        ket_noi.commit()


def doc_metrics(duong_dan, gioi_han=None):
    if not os.path.exists(duong_dan):
        return []
    cau_lenh = ("SELECT thoi_gian, gio, cpu, ram, dia, mang_gui, mang_nhan"
                " FROM metrics ORDER BY id")
    if gioi_han:
        cau_lenh += f" LIMIT {int(gioi_han)}"
    with sqlite3.connect(duong_dan) as ket_noi:
        ket_noi.row_factory = sqlite3.Row
        hang = ket_noi.execute(cau_lenh).fetchall()
    return [dict(h) for h in hang]


def phan_tich_gio_ranh(duong_dan):
    """Tra ve danh sach (gio, cpu trung binh, ram trung binh, so mau),
    sap xep tu gio ranh nhat den gio ban nhat."""
    if not os.path.exists(duong_dan):
        return []
    with sqlite3.connect(duong_dan) as ket_noi:
        hang = ket_noi.execute(
            "SELECT gio, AVG(cpu), AVG(ram), COUNT(*) FROM metrics"
            " GROUP BY gio ORDER BY AVG(cpu) ASC"
        ).fetchall()
    return [(int(g), round(c, 1), round(r, 1), int(n)) for g, c, r, n in hang]


def nhap_tu_csv(duong_dan_db, duong_dan_csv):
    """Nhap file metrics.csv (cua giam_sat.py) vao SQLite, tra ve so dong da nhap.

    Chi mo 1 ket noi, ghi het trong 1 transaction: file CSV loi giua chung
    thi khong co dong nao duoc ghi do (rollback), khong de lai import do.
    """
    khoi_tao_db(duong_dan_db)
    dem = 0
    with open(duong_dan_csv, "r", encoding="utf-8", newline="") as f:
        doc = csv.DictReader(f)
        with sqlite3.connect(duong_dan_db) as ket_noi:
            try:
                for dong in doc:
                    gio = int(dong["thoi_gian"][11:13])
                    ket_noi.execute(
                        "INSERT INTO metrics (thoi_gian, gio, cpu, ram, dia,"
                        " mang_gui, mang_nhan) VALUES (?, ?, ?, ?, ?, ?, ?)",
                        (dong["thoi_gian"], gio, float(dong["cpu"]),
                         float(dong["ram"]), float(dong["dia"]),
                         int(dong["mang_gui"]), int(dong["mang_nhan"])),
                    )
                    dem += 1
                ket_noi.commit()
            except Exception:
                ket_noi.rollback()
                raise
    return dem
