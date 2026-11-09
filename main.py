"""Diem vao chinh cua he thong backup AI.

Cach dung:
  python main.py thu-thap --so-lan 10 --file du_lieu/metrics.db
  python main.py huan-luyen --so-tap 500
  python main.py lap-lich --nguon <thu-muc> --dich <thu-muc-backup>
  python main.py lap-lich --nguon <thu-muc> --dich <thu-muc-backup> --lien-tuc
  python main.py bang-dieu-khien --nguon <thu-muc> --dich <thu-muc-backup>
  python main.py backup <nguon> <dich>
  python main.py khoi-phuc <thu-muc-backup> <thu-muc-dich>
  python main.py trang-thai <thu-muc-backup>
"""

import argparse
import time

from backup import backup, khoi_phuc, trang_thai
from du_lieu import luu_metrics
from giam_sat import thu_thap_metrics
from huan_luyen import chay_huan_luyen
from lap_lich import BoLapLich


def lenh_thu_thap(doi_so):
    for i in range(doi_so.so_lan):
        metrics = thu_thap_metrics()
        luu_metrics(doi_so.file, metrics)
        print(f"[{i + 1}/{doi_so.so_lan}] {metrics}")
        if i + 1 < doi_so.so_lan:
            time.sleep(doi_so.khoang_giay)


def lenh_huan_luyen(doi_so):
    chay_huan_luyen(so_tap=doi_so.so_tap, dung_dqn=doi_so.dqn,
                    duong_dan_db=doi_so.du_lieu)


def lenh_lap_lich(doi_so):
    bo_lap = BoLapLich(doi_so.nguon, doi_so.dich,
                       duong_dan_model=doi_so.model)
    if doi_so.lien_tuc:
        bo_lap.chay_lien_tuc(khoang_giay=doi_so.khoang_giay)
    else:
        bo_lap.chay_mot_lan()


def lenh_bang_dieu_khien(doi_so):
    import tkinter as tk
    from giao_dien import BangDieuKhien
    root = tk.Tk()
    BangDieuKhien(root, doi_so.nguon, doi_so.dich)
    root.mainloop()


def main():
    trich_dan = argparse.ArgumentParser(description="He thong backup tu dong co AI.")
    lenh_con = trich_dan.add_subparsers(dest="lenh", required=True)

    p = lenh_con.add_parser("thu-thap", help="Thu thap metrics vao SQLite.")
    p.add_argument("--so-lan", type=int, default=10)
    p.add_argument("--khoang-giay", type=float, default=2)
    p.add_argument("--file", default="du_lieu/metrics.db")
    p.set_defaults(func=lenh_thu_thap)

    p = lenh_con.add_parser("huan-luyen", help="Huan luyen tac nhan RL.")
    p.add_argument("--so-tap", type=int, default=500)
    p.add_argument("--dqn", action="store_true", help="Dung DQN TensorFlow.")
    p.add_argument("--du-lieu", default=None, help="File SQLite metrics.db.")
    p.set_defaults(func=lenh_huan_luyen)

    p = lenh_con.add_parser("lap-lich", help="Kiem tra va backup theo AI/quy tac.")
    p.add_argument("--nguon", required=True)
    p.add_argument("--dich", required=True)
    p.add_argument("--model", default="mo_hinh/q_model.json",
                   help="Duong dan model: mo_hinh/q_model.json (Q-learning) "
                        "hoac mo_hinh/dqn_model.keras (DQN TensorFlow).")
    p.add_argument("--lien-tuc", action="store_true")
    p.add_argument("--khoang-giay", type=float, default=3600)
    p.set_defaults(func=lenh_lap_lich)

    p = lenh_con.add_parser("bang-dieu-khien", help="Mo bang dieu khien.")
    p.add_argument("--nguon", default=".")
    p.add_argument("--dich", default="../backup")  # Phai nam ngoai nguon (xem giao_dien.py)
    p.set_defaults(func=lenh_bang_dieu_khien)

    p = lenh_con.add_parser("backup", help="Backup ngay.")
    p.add_argument("nguon")
    p.add_argument("dich")
    p.set_defaults(func=lambda d: print(f"Backup xong: {backup(d.nguon, d.dich)}"))

    p = lenh_con.add_parser("khoi-phuc", help="Khoi phuc tu ban backup.")
    p.add_argument("nguon")
    p.add_argument("dich")
    p.set_defaults(func=lambda d: print(f"Khoi phuc xong: {khoi_phuc(d.nguon, d.dich)}"))

    p = lenh_con.add_parser("trang-thai", help="Xem thong ke ban backup.")
    p.add_argument("dich")
    p.set_defaults(func=lambda d: print(trang_thai(d.dich)))

    doi_so = trich_dan.parse_args()
    doi_so.func(doi_so)


if __name__ == "__main__":
    main()
