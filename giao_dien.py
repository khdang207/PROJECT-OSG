import argparse
import json
import os
import queue
import threading
import tkinter as tk
from datetime import datetime
from tkinter import filedialog, messagebox, ttk

from backup import backup, trang_thai
from giam_sat import thu_thap_metrics, danh_gia_tai
from lap_lich import BoLapLich

NEN = "#0f172a"
KHUNG = "#1e293b"
CHU = "#e2e8f0"
MO = "#94a3b8"
XANH = "#38bdf8"
LUC = "#22c55e"
VANG = "#fbbf24"
DO = "#fb7185"


def dinh_dang_dung_luong(so_byte):
    """Đổi bytes sang B/KB/MB/GB, dùng cho thống kê backup."""
    try:
        so = max(float(so_byte), 0)
    except (ValueError, TypeError):
        return "0 B"
    for don_vi in ("B", "KB", "MB", "GB", "TB"):
        if so < 1024 or don_vi == "TB":
            return f"{so:.0f} {don_vi}" if don_vi == "B" else f"{so:.1f} {don_vi}"
        so /= 1024


def kiem_tra_duong_dan(nguon, dich):
    """Ngăn nguồn không hợp lệ và đích nằm trong nguồn (backup lặp)."""
    if not nguon or not dich:
        raise ValueError("Vui lòng chọn đủ thư mục nguồn và đích.")
    nguon = os.path.realpath(os.path.abspath(os.path.expanduser(nguon)))
    dich = os.path.realpath(os.path.abspath(os.path.expanduser(dich)))
    if not os.path.isdir(nguon):
        raise ValueError(f"Thư mục nguồn không tồn tại: {nguon}")
    if os.path.commonpath([nguon, dich]) == nguon:
        raise ValueError("Thư mục đích không được nằm trong thư mục nguồn.")
    if os.path.commonpath([nguon, dich]) == dich:
        raise ValueError("Thư mục nguồn không được nằm trong thư mục đích.")
    return nguon, dich


class BangDieuKhien:
    def __init__(self, root, nguon, dich,
                 file_lich_su="du_lieu/lich_su_backup.json"):
        self.root = root
        self.nguon = nguon
        self.dich = dich
        self.file_lich_su = file_lich_su
        self.hang_doi = queue.Queue()
        self.dang_chay = False
        self.tu_dong = False
        self.dang_do_metrics = False
        self.da_dong = False
        self.sau_lap_lich = None
        self.sau_metrics = None
        self.sau_hang_doi = None
        self.nguon_var = tk.StringVar(value=nguon)
        self.dich_var = tk.StringVar(value=dich)
        self.chu_ky_var = tk.StringVar(value="60")
        self.trang_thai_var = tk.StringVar(value="Sẵn sàng")
        self.che_do_var = tk.StringVar(value="Đang kiểm tra mô hình...")
        self.cpu_var = tk.StringVar(value="-- %")
        self.ram_var = tk.StringVar(value="-- %")
        self.dia_var = tk.StringVar(value="-- %")
        self.tai_var = tk.StringVar(value="Chưa có dữ liệu")
        self.ban_sao_var = tk.StringVar(value="Chưa có dữ liệu")
        self.quyet_dinh_var = tk.StringVar(value="Chưa có quyết định")

        self.root.title("AI Backup | Bảng điều khiển")
        self.root.geometry("1000x720")
        self.root.minsize(800, 610)
        self.root.configure(bg=NEN)
        self.root.protocol("WM_DELETE_WINDOW", self.dong_cua_so)
        self._tao_giao_dien()
        self._kiem_tra_che_do()
        self.lam_moi()
        self.sau_hang_doi = self.root.after(120, self._xu_ly_hang_doi)
        self._lap_lai_metrics()

    def _nhan(self, cha, text, size=10, mau=CHU, bold=False, **kw):
        return tk.Label(cha, text=text, bg=kw.pop("bg", KHUNG), fg=mau,
                        font=("Segoe UI", size, "bold" if bold else "normal"),
                        **kw)

    def _tao_giao_dien(self):
        tieu_de = tk.Frame(self.root, bg=NEN)
        tieu_de.pack(fill="x", padx=22, pady=(18, 9))
        self._nhan(tieu_de, "AI BACKUP DASHBOARD", 21, CHU, True, bg=NEN).pack(anchor="w")
        self._nhan(tieu_de, "Giám sát • AI/Quy tắc • Sao lưu tự động", 10, MO,
                   bg=NEN).pack(anchor="w", pady=(4, 0))

        duong_dan = tk.LabelFrame(self.root, text="  THƯ MỤC SAO LƯU  ", bg=KHUNG,
                                  fg=XANH, font=("Segoe UI", 10, "bold"),
                                  bd=0, padx=12, pady=10)
        duong_dan.pack(fill="x", padx=20, pady=8)
        duong_dan.columnconfigure(1, weight=1)
        for i, (nhan, bien) in enumerate((("Nguồn", self.nguon_var), ("Đích", self.dich_var))):
            self._nhan(duong_dan, nhan).grid(row=i, column=0, sticky="w", padx=6, pady=5)
            tk.Entry(duong_dan, textvariable=bien, bg=NEN, fg=CHU,
                     insertbackground=CHU, relief="flat", font=("Segoe UI", 10)
                     ).grid(row=i, column=1, sticky="ew", ipady=6, padx=8)
            tk.Button(duong_dan, text="Chọn...", bg="#334155", fg="white",
                      relief="flat", cursor="hand2",
                      command=lambda b=bien: self._chon_thu_muc(b)
                      ).grid(row=i, column=2, padx=4)

        luoi = tk.Frame(self.root, bg=NEN)
        luoi.pack(fill="x", padx=20, pady=8)
        for i in range(3):
            luoi.columnconfigure(i, weight=1)
        self.thanh = {}
        for i, (ten, bien, key) in enumerate((("CPU", self.cpu_var, "cpu"),
                                             ("RAM", self.ram_var, "ram"),
                                             ("Ổ ĐĨA", self.dia_var, "dia"))):
            card = tk.Frame(luoi, bg=KHUNG, padx=14, pady=12)
            card.grid(row=0, column=i, sticky="nsew", padx=(0 if i == 0 else 5,
                                                             0 if i == 2 else 5))
            self._nhan(card, ten, 10, MO, True).pack(anchor="w")
            tk.Label(card, textvariable=bien, font=("Segoe UI", 24, "bold"),
                     bg=KHUNG, fg=XANH).pack(anchor="w", pady=5)
            thanh = ttk.Progressbar(card, orient="horizontal", length=130, mode="determinate",
                                    maximum=100)
            thanh.pack(fill="x")
            self.thanh[key] = thanh

        thong_tin = tk.Frame(self.root, bg=KHUNG, padx=16, pady=12)
        thong_tin.pack(fill="x", padx=20, pady=8)
        for ten, bien in (("Mức tải", self.tai_var),
                          ("Chế độ quyết định", self.che_do_var),
                          ("Bản sao hiện tại", self.ban_sao_var),
                          ("Quyết định cuối", self.quyet_dinh_var)):
            hang = tk.Frame(thong_tin, bg=KHUNG)
            hang.pack(fill="x", pady=3)
            self._nhan(hang, ten + ":", 10, MO, True).pack(side="left")
            tk.Label(hang, textvariable=bien, font=("Segoe UI", 10),
                     bg=KHUNG, fg=CHU, anchor="w", wraplength=730,
                     justify="left").pack(side="left", padx=10)

        dk = tk.Frame(self.root, bg=NEN)
        dk.pack(fill="x", padx=20, pady=8)
        self.nut_backup = self._nut(dk, "Backup ngay", self.backup_ngay, LUC)
        self.nut_ai = self._nut(dk, "AI kiểm tra 1 lần", self.kiem_tra_ai, "#2563eb")
        self.nut_tu_dong = self._nut(dk, "Bật tự động", self.bat_tat_tu_dong, "#7c3aed")
        self._nhan(dk, "Chu kỳ (phút):", 10, MO, bg=NEN).pack(side="left", padx=(10, 4))
        tk.Spinbox(dk, textvariable=self.chu_ky_var, from_=1, to=1440, width=5,
                   bg=KHUNG, fg=CHU, insertbackground=CHU,
                   buttonbackground="#334155").pack(side="left")
        self._nut(dk, "Làm mới", self.lam_moi, "#475569")

        lich_su = tk.LabelFrame(self.root, text="  LỊCH SỬ QUYẾT ĐỊNH  ", bg=KHUNG,
                                fg=XANH, font=("Segoe UI", 10, "bold"),
                                bd=0, padx=10, pady=8)
        lich_su.pack(fill="both", expand=True, padx=20, pady=(6, 8))
        cot = ("thoi_gian", "quyet_dinh", "cpu", "ram", "ly_do")
        self.bang = ttk.Treeview(lich_su, columns=cot, show="headings", height=7)
        for key, nhan, rong in (("thoi_gian", "Thời gian", 160),
                               ("quyet_dinh", "Quyết định", 100),
                               ("cpu", "CPU", 65), ("ram", "RAM", 65),
                               ("ly_do", "Lý do / trạng thái AI", 420)):
            self.bang.heading(key, text=nhan)
            self.bang.column(key, width=rong, anchor="w", stretch=(key == "ly_do"))
        keo = ttk.Scrollbar(lich_su, orient="vertical", command=self.bang.yview)
        self.bang.configure(yscrollcommand=keo.set)
        self.bang.pack(side="left", fill="both", expand=True)
        keo.pack(side="right", fill="y")

        cuoi = tk.Frame(self.root, bg=NEN)
        cuoi.pack(fill="x", padx=22, pady=(0, 12))
        tk.Label(cuoi, textvariable=self.trang_thai_var, bg=NEN, fg=VANG,
                 font=("Segoe UI", 10)).pack(side="left")
        self._nhan(cuoi, "Giai đoạn 4 • Tkinter • Vinh", 9, MO,
                   bg=NEN).pack(side="right")

    def _nut(self, cha, chu, ham, mau):
        nut = tk.Button(cha, text=chu, command=ham, bg=mau, fg="white",
                        activebackground=mau, activeforeground="white", relief="flat",
                        padx=11, pady=8, font=("Segoe UI", 9, "bold"),
                        cursor="hand2")
        nut.pack(side="left", padx=(0, 6))
        return nut

    def _chon_thu_muc(self, bien):
        thu_muc = filedialog.askdirectory(parent=self.root, title="Chọn thư mục")
        if thu_muc:
            bien.set(thu_muc)
            self.lam_moi()

    def _kiem_tra_che_do(self):
        self.che_do_var.set("Q-learning (nếu có mo_hinh/q_model.json), "
                             "ngược lại dùng quy tắc dự phòng")
        if os.path.isfile("mo_hinh/q_model.json"):
            self.che_do_var.set("Q-learning có model • dự phòng quy tắc khi trạng thái lạ")
        else:
            self.che_do_var.set("Quy tắc dự phòng • chưa có model Q-learning")

    def _chay_nen(self, ten, ham):
        """Không gọi Tkinter từ thread; chuyển kết quả qua queue."""
        if self.dang_chay:
            self.trang_thai_var.set("Đang có tác vụ khác, vui lòng đợi hoàn tất.")
            return False
        self.dang_chay = True
        self.nut_backup.config(state="disabled")
        self.nut_ai.config(state="disabled")
        self.trang_thai_var.set("Đang thực hiện: " + ten)

        def worker():
            try:
                self.hang_doi.put(("tac_vu_ok", ten, ham()))
            except Exception as exc:
                self.hang_doi.put(("tac_vu_loi", ten, str(exc)))
        threading.Thread(target=worker, daemon=True).start()
        return True

    def _xu_ly_hang_doi(self):
        if self.da_dong:
            return
        try:
            while True:
                kieu, ten, ket_qua = self.hang_doi.get_nowait()
                if kieu == "metrics_ok":
                    self.dang_do_metrics = False
                    self._hien_metrics(ket_qua)
                elif kieu == "metrics_loi":
                    self.dang_do_metrics = False
                    self.trang_thai_var.set("Không thể lấy metrics: " + ket_qua)
                else:
                    self.dang_chay = False
                    self.nut_backup.config(state="normal")
                    self.nut_ai.config(state="normal")
                    if kieu == "tac_vu_loi":
                        self.trang_thai_var.set("Lỗi " + ten + ": " + ket_qua)
                        messagebox.showerror("Tác vụ thất bại", ket_qua, parent=self.root)
                    else:
                        self.trang_thai_var.set(ten + " hoàn tất lúc " +
                                                 datetime.now().strftime("%H:%M:%S"))
                        if isinstance(ket_qua, dict) and "quyet_dinh" in ket_qua:
                            self.quyet_dinh_var.set(
                                f"{ket_qua['quyet_dinh'].upper()} • {ket_qua['ly_do']}")
                        self.lam_moi()
        except queue.Empty:
            pass
        self.sau_hang_doi = self.root.after(120, self._xu_ly_hang_doi)

    def _hien_metrics(self, metrics):
        for key, bien in (("cpu", self.cpu_var), ("ram", self.ram_var),
                          ("dia", self.dia_var)):
            try:
                gia_tri = float(metrics[key])
            except (KeyError, ValueError, TypeError):
                continue
            bien.set(f"{gia_tri:.1f}%")
            self.thanh[key]["value"] = max(0, min(100, gia_tri))
        muc = danh_gia_tai(metrics)
        self.tai_var.set({"ranh": "Rảnh • phù hợp để backup",
                          "binh_thuong": "Bình thường", "ban": "Bận • nên hạn chế backup"}
                         .get(muc, muc))

    def _lap_lai_metrics(self):
        if self.da_dong:
            return
        if not self.dang_do_metrics:
            self.dang_do_metrics = True
            def worker():
                try:
                    self.hang_doi.put(("metrics_ok", "", thu_thap_metrics()))
                except Exception as exc:
                    self.hang_doi.put(("metrics_loi", "", str(exc)))
            threading.Thread(target=worker, daemon=True).start()
        self.sau_metrics = self.root.after(3000, self._lap_lai_metrics)

    def _duong_dan(self):
        nguon, dich = kiem_tra_duong_dan(self.nguon_var.get(), self.dich_var.get())
        self.nguon, self.dich = nguon, dich
        return nguon, dich

    def lam_moi(self):
        """Làm mới trạng thái backup và bảng lịch sử (không block đo CPU)."""
        try:
            tt = trang_thai(self.dich_var.get())
            self.ban_sao_var.set(f"{tt['so_file']} file • "
                                  f"{dinh_dang_dung_luong(tt['tong_dung_luong'])}")
        except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
            self.ban_sao_var.set("Chưa đọc được dữ liệu backup: " + str(exc))
        self._kiem_tra_che_do()
        for hang in self.bang.get_children():
            self.bang.delete(hang)
        if not os.path.isfile(self.file_lich_su):
            return
        try:
            with open(self.file_lich_su, "r", encoding="utf-8") as f:
                du_lieu = json.load(f)
            if not isinstance(du_lieu, list):
                raise ValueError("Lịch sử phải là danh sách JSON")
            for ban in reversed(du_lieu[-100:]):
                self.bang.insert("", "end", values=(
                    ban.get("thoi_gian", ""), ban.get("quyet_dinh", ""),
                    str(ban.get("cpu", "")) + "%" if "cpu" in ban else "--",
                    str(ban.get("ram", "")) + "%" if "ram" in ban else "--",
                    ban.get("ly_do", "")))
        except (OSError, ValueError, json.JSONDecodeError, TypeError) as exc:
            self.trang_thai_var.set("Lỗi đọc lịch sử: " + str(exc))

    def backup_ngay(self):
        try:
            nguon, dich = self._duong_dan()
        except (ValueError, OSError) as exc:
            messagebox.showerror("Thư mục không hợp lệ", str(exc), parent=self.root)
            return
        self._chay_nen("Backup thủ công", lambda: backup(nguon, dich))

    def kiem_tra_ai(self):
        try:
            nguon, dich = self._duong_dan()
        except (ValueError, OSError) as exc:
            messagebox.showerror("Thư mục không hợp lệ", str(exc), parent=self.root)
            return
        def thuc_hien():
            bo_lap = BoLapLich(nguon, dich,
                               duong_dan_model="mo_hinh/q_model.json",
                               file_lich_su=self.file_lich_su)
            return bo_lap.chay_mot_lan()
        self._chay_nen("AI kiểm tra & quyết định", thuc_hien)

    def bat_tat_tu_dong(self):
        if self.tu_dong:
            self.tu_dong = False
            if self.sau_lap_lich is not None:
                self.root.after_cancel(self.sau_lap_lich)
                self.sau_lap_lich = None
            self.nut_tu_dong.config(text="Bật tự động")
            self.trang_thai_var.set("Đã tắt lịch tự động (tác vụ đang chạy vẫn hoàn tất).")
            return
        try:
            phut = int(self.chu_ky_var.get())
            if not 1 <= phut <= 1440:
                raise ValueError
            self._duong_dan()
        except (ValueError, OSError):
            messagebox.showerror("Sai thiết lập", "Chọn thư mục hợp lệ và chu kỳ 1–1440 phút.",
                                 parent=self.root)
            return
        self.tu_dong = True
        self.nut_tu_dong.config(text="Tắt tự động")
        self.trang_thai_var.set(f"Đã bật tự động: kiểm tra mỗi {phut} phút.")
        self._chu_ky_ai(phut)

    def _chu_ky_ai(self, phut):
        if not self.tu_dong or self.da_dong:
            return
        if not self.dang_chay:
            self.kiem_tra_ai()
        self.sau_lap_lich = self.root.after(phut * 60 * 1000,
                                           lambda: self._chu_ky_ai(phut))

    def dong_cua_so(self):
        if self.dang_chay:
            messagebox.showwarning("Đang chạy backup",
                                   "Vui lòng đợi tác vụ kết thúc trước khi đóng.",
                                   parent=self.root)
            return
        self.da_dong = True
        for job in (self.sau_lap_lich, self.sau_metrics, self.sau_hang_doi):
            if job is not None:
                self.root.after_cancel(job)
        self.root.destroy()


def main():
    parser = argparse.ArgumentParser(description="Giao diện AI Backup")
    parser.add_argument("--nguon", default=".")
    # Dich mac dinh phai nam NGOAI nguon, neu khong kiem_tra_duong_dan se
    # chan ngay (loi cu: dich "backup" nam trong nguon ".").
    parser.add_argument("--dich", default="../backup")
    args = parser.parse_args()
    root = tk.Tk()
    BangDieuKhien(root, args.nguon, args.dich)
    root.mainloop()


if __name__ == "__main__":
    main()
