"""Giam sat he thong - Giai doan 1.

Thu thap cac chi so su dung he thong (CPU, RAM, o dia, mang) de sau nay
AI hoc thoi diem nao may ranh de backup.
"""

import csv
from datetime import datetime 
import os
import time
import psutil


COT_CSV = ["thoi_gian", "cpu", "ram", "dia", "mang_gui", "mang_nhan"]


def thu_thap_metrics():
    """Lay mot mau chi so he thong tai thoi diem hien tai."""
    cpu = psutil.cpu_percent(interval=0.5)
    ram = psutil.virtual_memory().percent
    o_dia_goc = os.path.abspath(os.sep)
    dia = psutil.disk_usage(o_dia_goc).percent
    mang = psutil.net_io_counters()
    return {
        "thoi_gian": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "cpu": round(cpu, 1),
        "ram": round(ram, 1),
        "dia": round(dia, 1),
        "mang_gui": int(mang.bytes_sent),
        "mang_nhan": int(mang.bytes_recv),
    }


def danh_gia_tai(metrics):
    """Danh gia may dang ranh, binh thuong hay ban dua tren CPU va RAM."""
    cpu = metrics["cpu"]
    ram = metrics["ram"]
    if cpu < 20 and ram < 70:
        return "ranh"
    if cpu < 60 and ram < 85:
        return "binh_thuong"
    return "ban"


def ghi_metrics_csv(duong_dan, metrics):
    """Ghi them mot dong metrics vao file CSV (tu tao tieu de neu file moi)."""
    da_co = os.path.exists(duong_dan) and os.path.getsize(duong_dan) > 0
    with open(duong_dan, "a", encoding="utf-8", newline="") as f:
        viet = csv.DictWriter(f, fieldnames=COT_CSV)
        if not da_co:
            viet.writeheader()
        viet.writerow({cot: metrics[cot] for cot in COT_CSV})


def doc_metrics_csv(duong_dan):
    """Doc toan bo file CSV metrics thanh danh sach dict."""
    with open(duong_dan, "r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))

if __name__ == "__main__":
    print("Đang tiến hành giám sát hệ thống (ghi nhận vào metrics.csv)...")
    print("Nhấn Ctrl + C để dừng lại khi đã thu thập đủ dữ liệu.")
    try:
        while True:
            # Lấy thông số máy hiện tại trước, sau đó mới ghi vào file
            thong_so = thu_thap_metrics()
            ghi_metrics_csv("metrics.csv", thong_so)
            time.sleep(5)  # Cứ mỗi 5 giây thu thập 1 lần
    except KeyboardInterrupt:
        print("\nĐã dừng giám sát. File metrics.csv đã được lưu thành công!")  
        