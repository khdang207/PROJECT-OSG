"""Moi truong hoc tang cuong cho viec chon gio backup - Giai doan 3 (Khanh Dang).

Mot ngay duoc chia thanh 24 khung gio. Moi buoc, tac nhan chon:
  0 = cho (chua backup), 1 = backup ngay.
Phan thuong: backup luc may ranh duoc thuong, backup luc may ban bi phat,
cho lau bi tru diem, het ngay ma chua backup bi phat nang.
"""

import random

# Mau su dung may gia lap theo gio (CPU trung binh): ban ngay ban, dem ranh.
MAU_CPU_MAC_DINH = [10, 8, 6, 5, 6, 10, 20, 35, 60, 70, 75, 65,
                    55, 70, 75, 70, 60, 45, 40, 50, 65, 45, 25, 15]


def _xep_loai_cpu(cpu):
    if cpu < 20:
        return 0
    if cpu < 60:
        return 1
    return 2


def _xep_loai_ram(ram):
    if ram < 70:
        return 0
    if ram < 85:
        return 1
    return 2


def tao_mau_cpu_tu_du_lieu(phan_tich):
    """Xay mau CPU 24 gio tu ket qua phan_tich_gio_ranh (du_lieu.py).
    Gio nao chua co du lieu thi mac dinh CPU 40%."""
    mau = [40] * 24
    for gio, cpu_tb, _ram_tb, _so_mau in phan_tich:
        mau[gio] = int(cpu_tb)
    return mau


class MoiTruongBackup:
    def __init__(self, mau_cpu=None, seed=0):
        self.mau_cpu = list(mau_cpu) if mau_cpu else list(MAU_CPU_MAC_DINH)
        self.rng = random.Random(seed)
        self.gio = 0
        self.cpu_theo_gio = {}
        self.da_backup = False

    def _lay_cpu(self, gio):
        # CPU that o mot gio: phan lon theo mau thoi quen, nhung doi luc
        # lech khoi mau (nguoi dung hom nay dung it hon moi ngay) de tac
        # nhan hoc duoc luat theo CPU that chu khong chi nho gio.
        if gio not in self.cpu_theo_gio:
            if self.rng.random() < 0.25:
                cpu = self.rng.randint(0, 100)
            else:
                cpu = self.mau_cpu[gio] + self.rng.randint(-15, 15)
            self.cpu_theo_gio[gio] = max(0, min(100, cpu))
        return self.cpu_theo_gio[gio]

    def reset(self):
        # Moi tap bat dau o mot gio ngau nhien trong ngay, tac nhan phai
        # hoc cach cho den gio ranh moi backup thay vi backup ngay.
        self.gio = self.rng.randint(0, 23)
        self.cpu_theo_gio = {}
        self.da_backup = False
        return self._trang_thai_hien_tai()

    def _trang_thai_hien_tai(self):
        cpu = self._lay_cpu(self.gio)
        ram = 55 + (self.gio % 5) * 5
        return (self.gio, _xep_loai_cpu(cpu), _xep_loai_ram(ram))

    def buoc(self, hanh_dong):
        """Thuc hien mot hanh dong, tra ve (trang thai moi, phan thuong, ket thuc)."""
        cpu = self._lay_cpu(self.gio)
        if hanh_dong == 1:
            self.da_backup = True
            if cpu < 20:
                phan_thuong = 10
            elif cpu < 60:
                phan_thuong = 2
            else:
                phan_thuong = -10
            return self._trang_thai_hien_tai(), phan_thuong, True
        phan_thuong = -1
        self.gio += 1
        if self.gio >= 24:
            return (23, 2, 2), -10, True
        return self._trang_thai_hien_tai(), phan_thuong, False
