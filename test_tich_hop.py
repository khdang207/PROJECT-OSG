"""Kiem tra tich hop toan he thong sau khi sua loi (chay: python test_tich_hop.py).

Khong can TensorFlow, khong mo cua so giao dien. Moi muc in ĐẠT hoac dung
ngay o muc loi voi thong bao ro rang.
"""

import csv
import json
import os
import subprocess
import sys
import tempfile
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backup import backup, khoi_phuc, trang_thai
from du_lieu import khoi_tao_db, luu_metrics, doc_metrics, nhap_tu_csv
from giao_dien import kiem_tra_duong_dan
from huan_luyen import huan_luyen
from lap_lich import BoLapLich
from mo_hinh_rl import TacNhanQ
from moi_truong import MoiTruongBackup


def _metrics_mau(gio, cpu, ram=50):
    return {"thoi_gian": f"2026-11-07 {gio:02d}:00:00", "cpu": cpu, "ram": ram,
            "dia": 50, "mang_gui": 0, "mang_nhan": 0}


def _ghi_lich_su(duong_dan, thoi_gian, quyet_dinh="backup", ket_qua=None):
    with open(duong_dan, "w", encoding="utf-8") as f:
        json.dump([{"thoi_gian": thoi_gian, "quyet_dinh": quyet_dinh,
                    "ly_do": "test", "ket_qua": ket_qua or {"cach": "rsync"}}], f)


def main():
    tmp = tempfile.mkdtemp()
    goc = os.path.dirname(os.path.abspath(__file__))

    # 1. Du lieu: luu/doc + nhap CSV 1 ket noi, loi giua chung thi rollback
    db = os.path.join(tmp, "metrics.db")
    khoi_tao_db(db)
    luu_metrics(db, _metrics_mau(2, 10))
    assert len(doc_metrics(db)) == 1
    csv_ok = os.path.join(tmp, "metrics.csv")
    with open(csv_ok, "w", encoding="utf-8", newline="") as f:
        viet = csv.writer(f)
        viet.writerow(["thoi_gian", "cpu", "ram", "dia", "mang_gui", "mang_nhan"])
        for gio, cpu in ((3, 8), (4, 12), (10, 65)):
            viet.writerow([f"2026-11-07 {gio:02d}:00:00", cpu, 50, 40, 0, 0])
    assert nhap_tu_csv(db, csv_ok) == 3 and len(doc_metrics(db)) == 4
    csv_loi = os.path.join(tmp, "loi.csv")
    with open(csv_loi, "w", encoding="utf-8", newline="") as f:
        viet = csv.writer(f)
        viet.writerow(["thoi_gian", "cpu", "ram", "dia", "mang_gui", "mang_nhan"])
        viet.writerow(["2026-11-07 05:00:00", 9, 50, 40, 0, 0])
        viet.writerow(["2026-11-07 06:00:00", "hong", 50, 40, 0, 0])
    try:
        nhap_tu_csv(db, csv_loi)
        raise AssertionError("CSV loi phai bao loi")
    except ValueError:
        pass
    assert len(doc_metrics(db)) == 4, "CSV loi giua chung khong duoc ghi dong nao"
    print("1. du_lieu (luu/doc/nhap CSV + rollback): ĐẠT")

    # 2. Moi truong: thuong/phat dung nhu thiet ke
    env = MoiTruongBackup(seed=0)
    env.gio = 2
    env.cpu_theo_gio = {2: 8}
    _tt, thuong, ket = env.buoc(1)
    assert thuong == 10 and ket is True
    env.gio = 9
    env.cpu_theo_gio = {9: 70}
    _tt, thuong, ket = env.buoc(1)
    assert thuong == -10 and ket is True
    print("2. moi_truong (thuong luc ranh, phat luc ban): ĐẠT")

    # 3. Tac nhan Q: hoc xong biet backup luc ranh, cho luc ban; luu/tai JSON
    tac_nhan = TacNhanQ()
    huan_luyen(tac_nhan, MoiTruongBackup(seed=0), 800)
    assert tac_nhan.chon_hanh_dong((2, 0, 0), huan_luyen=False) == 1
    assert tac_nhan.chon_hanh_dong((9, 2, 0), huan_luyen=False) == 0
    file_model = os.path.join(tmp, "q_model.json")
    tac_nhan.luu(file_model)
    assert TacNhanQ.tai(file_model).chon_hanh_dong((2, 0, 0), huan_luyen=False) == 1
    print("3. mo_hinh_rl (hoc + luu/tai q_model.json): ĐẠT")

    # 4. Lap lich: quy tac, AI, trang thai la -> du phong, quy tac 24h
    nguon = os.path.join(tmp, "nguon")
    dich = os.path.join(tmp, "dich")
    os.makedirs(nguon)
    with open(os.path.join(nguon, "a.txt"), "w", encoding="utf-8") as f:
        f.write("du lieu")
    file_ls = os.path.join(tmp, "lich_su.json")
    _ghi_lich_su(file_ls, (datetime.now() - timedelta(hours=1)).strftime(
        "%Y-%m-%d %H:%M:%S"))  # backup cach day 1 gio -> chua bat buoc
    bo_ranh = BoLapLich(nguon, dich, file_lich_su=file_ls,
                        ham_lay_metrics=lambda: _metrics_mau(2, 10))
    ban = bo_ranh.chay_mot_lan()
    assert ban["quyet_dinh"] == "backup", ban
    assert os.path.exists(os.path.join(dich, "a.txt"))
    bo_ban = BoLapLich(nguon, dich, file_lich_su=file_ls,
                       ham_lay_metrics=lambda: _metrics_mau(9, 80, 90))
    ban = bo_ban.chay_mot_lan()
    assert ban["quyet_dinh"] == "cho", ban
    bo_ai = BoLapLich(nguon, dich, duong_dan_model=file_model,
                      file_lich_su=file_ls,
                      ham_lay_metrics=lambda: _metrics_mau(2, 10))
    ban = bo_ai.chay_mot_lan()
    assert ban["quyet_dinh"] == "backup" and "AI" in ban["ly_do"], ban
    tac_nhan_moi = TacNhanQ()
    file_model_moi = os.path.join(tmp, "q_moi.json")
    tac_nhan_moi.luu(file_model_moi)
    bo_moi = BoLapLich(nguon, dich, duong_dan_model=file_model_moi,
                       file_lich_su=file_ls,
                       ham_lay_metrics=lambda: _metrics_mau(2, 10))
    ban = bo_moi.chay_mot_lan()
    assert ban["quyet_dinh"] == "backup" and "Trạng thái lạ" in ban["ly_do"], ban
    # Quy tac 24h: backup gan nhat da 25h truoc, may ban van phai backup
    _ghi_lich_su(file_ls, (datetime.now() - timedelta(hours=25)).strftime(
        "%Y-%m-%d %H:%M:%S"))
    bo_han = BoLapLich(nguon, dich, file_lich_su=file_ls,
                       ham_lay_metrics=lambda: _metrics_mau(9, 80, 90))
    ban = bo_han.chay_mot_lan()
    assert ban["quyet_dinh"] == "backup" and "24 giờ" in ban["ly_do"], ban
    print("4. lap_lich (quy tac + AI + du phong + bat buoc 24h): ĐẠT")

    # 5. Backup: rsync mirror (--delete), khoi phuc, manifest hong khong crash
    with open(os.path.join(nguon, "b.txt"), "w", encoding="utf-8") as f:
        f.write("b")
    backup(nguon, dich)
    assert os.path.exists(os.path.join(dich, "b.txt"))
    os.remove(os.path.join(nguon, "b.txt"))
    backup(nguon, dich)
    assert not os.path.exists(os.path.join(dich, "b.txt")), "file da xoa phai bien mat o dich"
    with open(os.path.join(dich, "manifest.json"), "w", encoding="utf-8") as f:
        f.write("{hong")
    assert trang_thai(dich) == {"so_file": 0, "tong_dung_luong": 0}
    backup(nguon, dich)  # manifest hong khong duoc lam crash backup
    assert os.path.exists(os.path.join(dich, "a.txt"))
    dich_kp = os.path.join(tmp, "khoi_phuc")
    assert khoi_phuc(dich, dich_kp)["so_file_da_khoi_phuc"] == 1
    print("5. backup (mirror + khoi phuc + manifest hong): ĐẠT")

    # 6. Giao dien: mac dinh moi (../backup) qua kiem tra, mac dinh cu thi loi
    goc_test = os.path.join(tmp, "du_an")
    os.makedirs(goc_test)
    os.chdir(goc_test)
    assert kiem_tra_duong_dan(".", "../backup")[1].endswith("backup")
    try:
        kiem_tra_duong_dan(".", "backup")
        raise AssertionError("dich trong nguon phai bi chan")
    except ValueError:
        pass
    print("6. giao_dien (kiem tra duong dan, mac dinh moi het mau thuan): ĐẠT")

    # 7. main.py: 1 diem vao duy nhat, chay duoc cac lenh chinh
    def chay_cli(*doi_so):
        ket = subprocess.run([sys.executable, os.path.join(goc, "main.py"), *doi_so],
                             capture_output=True, text=True, cwd=goc)
        assert ket.returncode == 0, (doi_so, ket.stdout, ket.stderr)
        return ket.stdout
    nguon2 = os.path.join(tmp, "nguon2")
    dich2 = os.path.join(tmp, "dich2")
    os.makedirs(nguon2)
    with open(os.path.join(nguon2, "x.txt"), "w", encoding="utf-8") as f:
        f.write("x")
    chay_cli("backup", nguon2, dich2)
    assert os.path.exists(os.path.join(dich2, "x.txt"))
    chay_cli("trang-thai", dich2)
    chay_cli("lap-lich", "--nguon", nguon2, "--dich", dich2,
             "--model", file_model)
    chay_cli("khoi-phuc", dich2, os.path.join(tmp, "kp2"))
    assert os.path.exists(os.path.join(tmp, "kp2", "x.txt"))
    print("7. main.py (backup/trang-thai/lap-lich/khoi-phuc): ĐẠT")

    # 8. DQN TensorFlow: huan luyen ngan, luu/tai .keras, lap lich dung duoc.
    #    Bo qua neu may chua cai TensorFlow (test chinh van dat 7/7).
    tong_muc = 7
    try:
        from mo_hinh_rl import TacNhanDQN
        tac_nhan_dqn = TacNhanDQN()
        lich_su_dqn = huan_luyen(tac_nhan_dqn, MoiTruongBackup(seed=0), 50)
        assert len(lich_su_dqn) == 50
        file_dqn = os.path.join(tmp, "dqn_model.keras")
        tac_nhan_dqn.luu(file_dqn)
        assert os.path.exists(file_dqn)
        tai_lai = TacNhanDQN.tai(file_dqn)
        assert tai_lai.chon_hanh_dong((2, 0, 0), huan_luyen=False) in (0, 1)
        bo_dqn = BoLapLich(nguon, dich, duong_dan_model=file_dqn,
                           file_lich_su=file_ls,
                           ham_lay_metrics=lambda: _metrics_mau(2, 10))
        assert isinstance(bo_dqn.tac_nhan, TacNhanDQN), "lap lich phai tai DQN"
        ban = bo_dqn.chay_mot_lan()
        assert "AI" in ban["ly_do"], ban
        print("8. DQN (huan luyen + luu/tai .keras + lap lich): ĐẠT")
        tong_muc = 8
    except (ImportError, RuntimeError):
        # TacNhanDQN.__init__ bao RuntimeError khi thieu TensorFlow.
        print("8. DQN: BỎ QUA (chưa có TensorFlow)")

    print(f"TÍCH HỢP: HOÀN THÀNH — {tong_muc}/{tong_muc} mục ĐẠT")


if __name__ == "__main__":
    main()
