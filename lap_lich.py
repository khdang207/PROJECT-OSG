import json
import os
from datetime import datetime

from backup import backup
from giam_sat import thu_thap_metrics, danh_gia_tai
from mo_hinh_rl import TacNhanQ, TacNhanDQN
from moi_truong import _xep_loai_cpu, _xep_loai_ram

def _trang_thai_tu_metrics(metrics):
    """Chuyển đổi dữ liệu thô (CPU, RAM, Thời gian) từ metrics thành trạng thái (State) 
    để mô hình Học tăng cường (Q-learning) có thể đọc và hiểu được.
    """
    gio = int(metrics["thoi_gian"][11:13])  # Lấy ra giờ trong ngày (0-23)
    return (gio, _xep_loai_cpu(metrics["cpu"]), _xep_loai_ram(metrics["ram"]))

class BoLapLich:
    def __init__(self, nguon, dich, duong_dan_model=None,
                 file_lich_su="du_lieu/lich_su_backup.json",
                 ham_lay_metrics=None):
        """Khởi tạo bộ lập lịch hệ thống backup."""
        self.nguon = nguon
        self.dich = dich
        self.file_lich_su = file_lich_su
        self.gioi_han_gio_chua_backup = 24  # Bao dam toi thieu 1 backup/ngay
        self.ham_lay_metrics = ham_lay_metrics or thu_thap_metrics
        self.tac_nhan = None
        if duong_dan_model and os.path.exists(duong_dan_model):
            try:
                # Tu nhan dang loai model theo duoi file: .keras/.h5 -> DQN
                # (TensorFlow), .json -> bang Q (Q-learning).
                if duong_dan_model.endswith((".keras", ".h5")):
                    self.tac_nhan = TacNhanDQN.tai(duong_dan_model)
                else:
                    self.tac_nhan = TacNhanQ.tai(duong_dan_model)
                print(f"[Bộ lập lịch] Đã tải thành công mô hình AI từ: {duong_dan_model}")
            except Exception as e:
                print(f"[Bộ lập lịch] Cảnh báo: Không thể tải mô hình AI ({e}). Sẽ dùng quy tắc ngưỡng.")
        else:
            print("[Bộ lập lịch] Không tìm thấy mô hình AI. Hệ thống chạy bằng quy tắc ngưỡng an toàn.")

    def _lan_backup_cuoi_cung(self):
        """Tra ve thoi diem backup thanh cong gan nhat trong lich su, None neu chua co."""
        if not os.path.exists(self.file_lich_su):
            return None
        try:
            with open(self.file_lich_su, "r", encoding="utf-8") as f:
                lich_su = json.load(f)
        except (OSError, ValueError):
            return None
        if not isinstance(lich_su, list):
            return None
        for ban in reversed(lich_su):
            if ban.get("quyet_dinh") != "backup":
                continue
            ket_qua = ban.get("ket_qua") or {}
            if isinstance(ket_qua, dict) and ket_qua.get("trang_thai") == "that_bai":
                continue
            try:
                return datetime.strptime(ban["thoi_gian"], "%Y-%m-%d %H:%M:%S")
            except (KeyError, ValueError, TypeError):
                continue
        return None

    def _qua_han_backup(self):
        """True neu chua tung backup, hoac da hon 24 gio ke tu backup gan nhat."""
        lan_cuoi = self._lan_backup_cuoi_cung()
        if lan_cuoi is None:
            return True
        gio_troi = (datetime.now() - lan_cuoi).total_seconds() / 3600
        return gio_troi > self.gioi_han_gio_chua_backup

    def quyet_dinh_backup(self, metrics):
        """Quyết định xem có nên backup hay tiếp tục chờ dựa trên AI hoặc Quy tắc dự phòng."""
        if self._qua_han_backup():
            return True, ("Bắt buộc: quá 24 giờ chưa backup "
                          "(bảo đảm tối thiểu 1 lần/ngày, bất kể máy bận hay rảnh)")
        if self.tac_nhan is not None:
            trang_thai = _trang_thai_tu_metrics(metrics)
            if hasattr(self.tac_nhan, "da_gap") and not self.tac_nhan.da_gap(trang_thai):
                muc = danh_gia_tai(metrics)
                return muc == "ranh", f"Quy tắc dự phòng (Trạng thái lạ với AI): Máy đang {muc}"
            hanh_dong = self.tac_nhan.chon_hanh_dong(trang_thai, huan_luyen=False)
            nen_backup = (hanh_dong == 1)
            ten_hanh_dong = 'backup' if nen_backup else 'chờ'
            return nen_backup, f"AI quyết định: {ten_hanh_dong} (tại trạng thái {trang_thai})"
        muc = danh_gia_tai(metrics)
        return muc == "ranh", f"Quy tắc ngưỡng: Máy đang {muc}"

    def _ghi_lich_su(self, ban_ghi):
        """Ghi lại lịch sử chạy backup vào file JSON để module giao diện (Vinh) đọc lên hiển thị."""
        thu_muc = os.path.dirname(self.file_lich_su)
        if thu_muc:
            os.makedirs(thu_muc, exist_ok=True)
            
        lich_su = []
        if os.path.exists(self.file_lich_su):
            try:
                with open(self.file_lich_su, "r", encoding="utf-8") as f:
                    lich_su = json.load(f)
            except json.JSONDecodeError:
                lich_su = []
                
        lich_su.append(ban_ghi)
        
        with open(self.file_lich_su, "w", encoding="utf-8") as f:
            json.dump(lich_su, f, ensure_ascii=False, indent=2)

    def chay_mot_lan(self):
        """Thực hiện một vòng kiểm tra duy nhất: Lấy metrics -> Ra quyết định -> Backup (nếu cần) -> Ghi log."""
        metrics = self.ham_lay_metrics()
        nen_backup, ly_do = self.quyet_dinh_backup(metrics)
        ket_qua = None
        if nen_backup:
            try:
                ket_qua = backup(self.nguon, self.dich)
            except Exception as e:
                ket_qua = {"trang_thai": "that_bai", "loi": str(e)}
                print(f"[Lỗi Backup]: {e}")
        ban_ghi = {
            "thoi_gian": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "cpu": metrics["cpu"], 
            "ram": metrics["ram"],
            "quyet_dinh": "backup" if nen_backup else "cho",
            "ly_do": ly_do, 
            "ket_qua": ket_qua,
        }
        self._ghi_lich_su(ban_ghi)
        trang_thai_in = "backup" if nen_backup else "tiếp tục chờ"
        print(f"[{ban_ghi['thoi_gian']}] {ly_do} -> Quyết định: {trang_thai_in}" + (f" | Chi tiết: {ket_qua}" if ket_qua else ""))
        
        return ban_ghi

    def chay_lien_tuc(self, khoang_giay=3600):
        """Chạy vòng lặp vô hạn, kiểm tra hệ thống định kỳ sau mỗi khoảng thời gian (mặc định 1 giờ = 3600 giây)."""
        import time
        print(f"=== BỘ LẬP LỊCH ĐÃ BẮT ĐẦU CHẠY LIÊN TỤC (Khoảng cách kiểm tra: {khoang_giay} giây) ===")
        print("Nhấn Ctrl + C để dừng chương trình an toàn.\n")
        try:
            while True:
                self.chay_mot_lan()
                time.sleep(khoang_giay)
        except KeyboardInterrupt:
            print("\n=== Đã dừng bộ lập lịch theo yêu cầu người dùng ===")

if __name__ == "__main__":
    thu_muc_nguon_test = "./thu_muc_nguon_mau"
    thu_muc_dich_test = "./thu_muc_dich_backup"
    duong_dan_model_test = "mo_hinh/q_model.json"
    
    os.makedirs(thu_muc_nguon_test, exist_ok=True)
    os.makedirs(thu_muc_dich_test, exist_ok=True)

    lap_lich = BoLapLich(
        nguon=thu_muc_nguon_test, 
        dich=thu_muc_dich_test, 
        duong_dan_model=duong_dan_model_test
    )

    print("\n--- BẮT ĐẦU KIỂM TRA CHẠY THỬ 1 LẦN ---")
    lap_lich.chay_mot_lan()