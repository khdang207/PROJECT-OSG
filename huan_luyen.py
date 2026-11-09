"""Huan luyen tac nhan hoc tang cuong - Giai doan 3 (Khanh Dang).

Cach dung:
  python huan_luyen.py --so-tap 500
  python huan_luyen.py --so-tap 500 --dqn
  python huan_luyen.py --so-tap 500 --du-lieu du_lieu/metrics.db
"""

import argparse
import csv
import os

from du_lieu import phan_tich_gio_ranh
from moi_truong import MoiTruongBackup, tao_mau_cpu_tu_du_lieu
from mo_hinh_rl import TacNhanQ, TacNhanDQN


def huan_luyen(tac_nhan, moi_truong, so_tap):
    lich_su = []
    for tap in range(1, so_tap + 1):
        trang_thai = moi_truong.reset()
        tong_thuong = 0
        while True:
            hanh_dong = tac_nhan.chon_hanh_dong(trang_thai, huan_luyen=True)
            trang_thai_moi, phan_thuong, ket_thuc = moi_truong.buoc(hanh_dong)
            tac_nhan.hoc(trang_thai, hanh_dong, phan_thuong, trang_thai_moi, ket_thuc)
            tong_thuong += phan_thuong
            trang_thai = trang_thai_moi
            if ket_thuc:
                break
        lich_su.append(tong_thuong)
        if tap % 100 == 0:
            tb = sum(lich_su[-100:]) / len(lich_su[-100:])
            print(f"Tap {tap}: phan thuong trung binh 100 tap gan nhat = {tb:.1f}")
    return lich_su


def chay_huan_luyen(so_tap=500, dung_dqn=False, duong_dan_db=None,
                   file_model=None, file_lich_su=None):
    # Model Q va DQN dung file model + file lich su RIENG: neu khong tach,
    # chay --dqn se ghi de lich su huan luyen cua Q-learning.
    if dung_dqn:
        file_model = file_model or "mo_hinh/dqn_model.keras"
        file_lich_su = file_lich_su or "mo_hinh/lich_su_dqn.csv"
    else:
        file_model = file_model or "mo_hinh/q_model.json"
        file_lich_su = file_lich_su or "mo_hinh/lich_su_huan_luyen.csv"
    mau_cpu = None
    if duong_dan_db and os.path.exists(duong_dan_db):
        phan_tich = phan_tich_gio_ranh(duong_dan_db)
        mau_cpu = tao_mau_cpu_tu_du_lieu(phan_tich)
        print(f"Dung mau CPU tu du lieu that ({len(phan_tich)} gio co du lieu).")
    moi_truong = MoiTruongBackup(mau_cpu=mau_cpu, seed=0)
    if dung_dqn:
        tac_nhan = TacNhanDQN()
    else:
        tac_nhan = TacNhanQ()
    lich_su = huan_luyen(tac_nhan, moi_truong, so_tap)
    tac_nhan.luu(file_model)
    print(f"Da luu model vao {file_model}.")
    thu_muc = os.path.dirname(file_lich_su)
    if thu_muc:
        os.makedirs(thu_muc, exist_ok=True)
    with open(file_lich_su, "w", encoding="utf-8", newline="") as f:
        viet = csv.writer(f)
        viet.writerow(["tap", "phan_thuong"])
        for i, thuong in enumerate(lich_su, start=1):
            viet.writerow([i, thuong])
    print(f"Da luu lich su huan luyen vao {file_lich_su}.")
    print(f"Phan thuong trung binh 100 tap cuoi: "
          f"{sum(lich_su[-100:]) / len(lich_su[-100:]):.1f}")
    return lich_su


def main():
    trich_dan = argparse.ArgumentParser(description="Huan luyen tac nhan backup AI.")
    trich_dan.add_argument("--so-tap", type=int, default=500, help="So tap huan luyen.")
    trich_dan.add_argument("--dqn", action="store_true", help="Dung DQN TensorFlow.")
    trich_dan.add_argument("--du-lieu", default=None,
                           help="File SQLite metrics.db de lay mau CPU that.")
    doi_so = trich_dan.parse_args()
    chay_huan_luyen(so_tap=doi_so.so_tap, dung_dqn=doi_so.dqn,
                    duong_dan_db=doi_so.du_lieu)


if __name__ == "__main__":
    main()
