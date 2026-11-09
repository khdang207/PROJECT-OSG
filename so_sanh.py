"""So sanh cac cach lap lich: AI (Q-learning) / AI (DQN) / quy tac / ngau nhien.

Chay: python so_sanh.py
Ket qua in ra bang va luu vao so_sanh.csv de dua vao bao cao.
Moi cach chay 200 ngay mo phong (moi truong seed 123, tac nhan hoc seed 0).
Hang DQN chi xuat hien khi da co mo_hinh/dqn_model.keras (da huan luyen DQN).
"""

import csv
import os
import random

from huan_luyen import huan_luyen
from mo_hinh_rl import TacNhanQ
from moi_truong import MoiTruongBackup

SO_NGAY = 200


def _chay_ngay(moi_truong, ham_chon):
    trang_thai = moi_truong.reset()
    tong_thuong = 0
    so_buoc = 0
    while True:
        hanh_dong = ham_chon(trang_thai)
        trang_thai_moi, phan_thuong, ket_thuc = moi_truong.buoc(hanh_dong)
        tong_thuong += phan_thuong
        so_buoc += 1
        if hanh_dong == 1:
            cpu_loai = trang_thai[1]
            return tong_thuong, True, cpu_loai == 0, so_buoc
        trang_thai = trang_thai_moi
        if ket_thuc:
            return tong_thuong, False, False, so_buoc


def _danh_gia(ten, ham_chon):
    thuong, co_backup, backup_ranh, buoc = [], 0, 0, []
    for _ in range(SO_NGAY):
        env = MoiTruongBackup(seed=123)
        # Moi ngay dung seed rieng theo thu tu chay de 3 cach gap cung 200 ngay
        env.rng = random.Random(1000 + len(thuong))
        t, co, ranh, b = _chay_ngay(env, ham_chon)
        thuong.append(t)
        buoc.append(b)
        co_backup += int(co)
        backup_ranh += int(ranh)
    return {
        "cach": ten,
        "phan_thuong_tb": round(sum(thuong) / len(thuong), 2),
        "ngay_co_backup_pct": round(100 * co_backup / SO_NGAY, 1),
        "backup_luc_ranh_pct": round(100 * backup_ranh / max(co_backup, 1), 1),
        "cho_tb_gio": round(sum(buoc) / len(buoc), 1),
    }


def main():
    tac_nhan = TacNhanQ()
    huan_luyen(tac_nhan, MoiTruongBackup(seed=0), 500)

    def chon_ai(trang_thai):
        if tac_nhan.da_gap(trang_thai):
            return tac_nhan.chon_hanh_dong(trang_thai, huan_luyen=False)
        return 1 if trang_thai[1] == 0 else 0  # Trang thai la -> quy tac du phong

    def chon_quy_tac(trang_thai):
        return 1 if trang_thai[1] == 0 else 0  # CPU < 20% thi backup

    rng = random.Random(7)

    def chon_ngau_nhien(_trang_thai):
        return rng.randint(0, 1)

    ket_qua = [
        _danh_gia("AI (Q-learning)", chon_ai),
        _danh_gia("Quy tac (CPU < 20%)", chon_quy_tac),
        _danh_gia("Ngau nhien", chon_ngau_nhien),
    ]
    # Them hang DQN neu co model DQN da huan luyen (mo_hinh/dqn_model.keras).
    duong_dan_dqn = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                 "mo_hinh", "dqn_model.keras")
    if os.path.exists(duong_dan_dqn):
        try:
            from mo_hinh_rl import TacNhanDQN
            tac_nhan_dqn = TacNhanDQN.tai(duong_dan_dqn)

            def chon_dqn(trang_thai):
                return tac_nhan_dqn.chon_hanh_dong(trang_thai, huan_luyen=False)

            ket_qua.insert(1, _danh_gia("AI (DQN)", chon_dqn))
        except Exception as e:
            print(f"Khong danh gia duoc DQN: {e}")
    print(f"So sanh {len(ket_qua)} cach lap lich ({SO_NGAY} ngay mo phong):")
    for k in ket_qua:
        print(f"  {k['cach']:<22} thuong TB {k['phan_thuong_tb']:>6} | "
              f"ngay co backup {k['ngay_co_backup_pct']:>5}% | "
              f"backup luc ranh {k['backup_luc_ranh_pct']:>5}% | "
              f"cho TB {k['cho_tb_gio']} gio")
    duong_dan = os.path.join(os.path.dirname(os.path.abspath(__file__)), "so_sanh.csv")
    with open(duong_dan, "w", encoding="utf-8", newline="") as f:
        viet = csv.DictWriter(f, fieldnames=list(ket_qua[0].keys()))
        viet.writeheader()
        viet.writerows(ket_qua)
    print(f"Da luu {duong_dan}.")


if __name__ == "__main__":
    main()
