# AI-Enabled Automated Backup System — Bản hoàn chỉnh

Hệ thống backup tự động dùng học tăng cường để chọn thời điểm backup ít
làm phiền nhất. Bản này là bản cuối: đã sửa toàn bộ 6 lỗi trong nhận xét
chấm bài ngày 08/11/2026, đã huấn luyện thật cả 2 tác nhân AI
(Q-learning + DQN TensorFlow), đã kiểm chứng end-to-end trên Linux.
Mọi mục đều đã chạy kiểm chứng bằng `test_tich_hop.py` — xem cuối file.

## Đã sửa gì (đối chiếu từng lỗi đã chấm)

1. **Thiếu `mo_hinh_rl.py`, `moi_truong.py` — đã bổ sung.**
   Đây là 2 file phần RL (của Khánh Đăng) trong bản base đã giao ngày 07/11
   mà nhóm quên nộp kèm. Thêm cả `huan_luyen.py`. Model đã huấn luyện thật:
   `mo_hinh/q_model.json` (Q-learning, 500 tập, phần thưởng trung bình
   100 tập cuối = 3,3) và `mo_hinh/dqn_model.keras` (DQN, 500 tập, phần
   thưởng trung bình 100 tập cuối = 3,4), kèm 2 file lịch sử
   `mo_hinh/lich_su_huan_luyen.csv` và `mo_hinh/lich_su_dqn.csv` để vẽ
   biểu đồ reward.
   Chạy lại huấn luyện bằng: `python main.py huan-luyen --so-tap 500`
   (Q-learning) hoặc `python main.py huan-luyen --so-tap 500 --dqn` (DQN).
2. **Không có test / requirements / README — đã thêm.**
   `test_tich_hop.py` (8 mục, xem dưới), `requirements.txt` (`psutil`),
   `requirements-tf.txt` (chỉ cần nếu dùng DQN), README này.
3. **Hai CLI trùng nhau — đã gộp về 1 điểm vào duy nhất `main.py`.**
   `chay.py` và `chay_backup.py` đã bỏ khỏi bản nộp (chức năng của chúng
   đều có trong `main.py`). Không còn 2 mặc định giám sát khác nhau.
4. **Đường dẫn model không thống nhất — đã thống nhất.**
   Q-learning: `mo_hinh/q_model.json`; DQN: `mo_hinh/dqn_model.keras`.
   Bộ lập lịch tự nhận dạng loại model theo đuôi file (`.keras`/`.h5`
   → DQN TensorFlow, `.json` → bảng Q), nên dùng model nào cũng chỉ cần
   đổi `--model`. Không còn chuỗi `.pkl` nào trong code.
5. **Giao diện tự mâu thuẫn ở mặc định — đã sửa.** Mặc định đích đổi từ
   `backup` (nằm trong nguồn `.`) thành `../backup` (nằm ngoài nguồn) nên
   bấm "Backup ngay" với mặc định không còn bị hộp thoại lỗi. Khi demo vẫn
   nên chọn thư mục thật bằng nút "Chọn...".
   Thêm **quy tắc backup bắt buộc sau 24 giờ** (`lap_lich.py`): nếu hơn
   24 giờ chưa có backup thành công thì backup ngay bất kể máy bận hay rảnh,
   nên hệ thống không bao giờ để trống một ngày.
6. **Lỗi nhỏ — đã sửa.**
   - `nhap_tu_csv` (`du_lieu.py`): chỉ mở 1 kết nối, ghi trong 1 transaction;
     CSV lỗi giữa chừng thì rollback, không để lại import dở.
   - `backup` (`backup.py`): manifest hỏng thì trả `{}` thay vì crash;
     rsync thêm `--delete` và bản Python tự xóa file đích đã xóa ở nguồn,
     nên thống kê và thực tế không còn lệch nhau.
   - Help ghi sai định dạng model và emoji trong `chay.py`: hết hiệu lực
     vì file này đã bỏ, `main.py` không còn 2 lỗi đó.
   - `huan_luyen.py`: Q và DQN dùng file lịch sử riêng
     (`lich_su_huan_luyen.csv` / `lich_su_dqn.csv`) — trước đây chạy `--dqn`
     sẽ ghi đè lịch sử của Q-learning.
   - `mo_hinh_rl.py`: mã hóa trạng thái DQN thành mảng numpy 2 chiều thay
     vì list Python — Keras 3 (TensorFlow 2.16+) không nhận list ở
     `predict`/`fit`, bản cũ sẽ lỗi `Unrecognized data type` khi chạy DQN.
     `requirements-tf.txt` ghim `tensorflow-cpu==2.16.2` (bản CPU, đã kiểm
     chứng chạy được trên Linux + Python 3.12).

## So sánh 4 cách lập lịch (200 ngày mô phỏng, `so_sanh.py`)

| Cách | Phần thưởng TB | Ngày có backup | Backup lúc rảnh | Chờ TB |
|---|---|---|---|---|
| AI (Q-learning) | 3,49 | 99,5% | 29,6% | 1,8 giờ |
| AI (DQN) | 3,58 | 99,5% | 33,7% | 2,0 giờ |
| Quy tắc (CPU < 20%) | 2,24 | 84,5% | 100% | 5,7 giờ |
| Ngẫu nhiên | -1,21 | 96,0% | 22,4% | 2,0 giờ |

Đọc đúng số liệu: 2 cách AI thắng về phần thưởng và gần như không bỏ sót
ngày nào; DQN nhỉnh hơn Q-learning một chút (3,58 so với 3,49) và backup
lúc rảnh nhiều hơn (33,7% so với 29,6%). Cả 2 đều hay backup cả lúc máy
vừa (CPU 20–60%, thưởng +2) thay vì chờ lúc rảnh hẳn (+10) — vì chờ mỗi
giờ bị trừ 1 điểm. Quy tắc thì 100% backup lúc rảnh nhưng bỏ sót 15,5%
số ngày (không có giờ nào đủ rảnh) — đúng lỗ hổng mà quy tắc bắt buộc
24 giờ ở trên vá lại. Chạy lại: `python so_sanh.py`.

## Cách chạy

```bash
./setup.sh                     # tạo venv + cài requirements.txt (Linux)
source venv/bin/activate
python test_tich_hop.py          # kiểm tra tích hợp, phải ra 8/8 ĐẠT
python main.py huan-luyen --so-tap 500
python main.py lap-lich --nguon <thu-muc> --dich <thu-muc-backup>
python main.py lap-lich --nguon <thu-muc> --dich <thu-muc-backup> --lien-tuc
python main.py bang-dieu-khien --nguon <thu-muc> --dich <thu-muc-backup>
python main.py backup <nguon> <dich>
python main.py khoi-phuc <thu-muc-backup> <thu-muc-dich>
python main.py trang-thai <thu-muc-backup>
```

Muốn dùng DQN TensorFlow thay cho Q-learning:
`pip install -r requirements-tf.txt` rồi
`python main.py huan-luyen --so-tap 500 --dqn`, sau đó chạy lập lịch với
`--model mo_hinh/dqn_model.keras`. Không cần cài TensorFlow nếu chỉ dùng
Q-learning (mặc định).

## Kiểm chứng đã chạy (08/11/2026, máy Linux)

`python test_tich_hop.py` → **8/8 ĐẠT**:
1. du_lieu (lưu/đọc/nhập CSV + rollback khi CSV lỗi),
2. moi_truong (thưởng lúc rảnh, phạt lúc bận),
3. mo_hinh_rl (học + lưu/tải `q_model.json`, backup lúc rảnh / chờ lúc bận),
4. lap_lich (quy tắc + AI + dự phòng khi trạng thái lạ + bắt buộc 24h),
5. backup (mirror `--delete` + khôi phục + manifest hỏng không crash),
6. giao_dien (kiểm tra đường dẫn, mặc định mới hết mâu thuẫn),
7. main.py (backup / trạng thái / lập lịch / khôi phục),
8. DQN (huấn luyện + lưu/tải `.keras` + bộ lập lịch tải đúng DQN và ra
   quyết định bằng AI).

Huấn luyện DQN thật (500 tập, TensorFlow 2.16.2 CPU): phần thưởng trung
bình 100 tập — 1,1 → 2,1 → 2,2 → 3,5 → 3,4 (tăng dần, đã học được).
Quyết định kiểm tra: 2h rảnh → backup, 9h bận → chờ.

Giao diện đã mở cửa sổ thật trên màn hình ảo (xvfb): tiêu đề
"AI Backup | Bảng điều khiển", bấm backup thủ công chạy xong, file xuất
hiện đúng ở thư mục đích. Chưa chạy thử trên Windows thật.

Chạy end-to-end thật: `thu-thap` (3 mẫu vào SQLite) → `lap-lich`
(Q-learning gặp trạng thái lạ → dự phòng quy tắc → chờ; DQN → AI quyết
định backup, rsync copy 2 file) → `trang-thai` (2 file) → `khoi-phuc`
(2 file về đúng).

## Còn lại (chưa làm trong bản này)

- Chạy thử giao diện thật trên Windows (máy Linux chỉ mở được cửa sổ
  Tkinter qua màn hình ảo, chưa chạy trên Windows thật).
- Hạn nộp và yêu cầu nộp của môn vẫn chưa rõ — điền vào báo cáo khi có.

## Cây thư mục

```
├── setup.sh                # Tạo venv + cài requirements.txt (Linux)
├── main.py                 # Điểm vào duy nhất (gộp chay.py + chay_backup.py)
├── giam_sat.py             # Giai đoạn 1 — Anh Minh
├── du_lieu.py              # Giai đoạn 2 — Anh Minh
├── backup.py               # Động cơ backup — Kiệt
├── lap_lich.py             # Lập lịch AI/quy tắc — Tân (+ quy tắc 24h)
├── mo_hinh_rl.py           # Tác nhân Q-learning / DQN — Khánh Đăng
├── moi_truong.py           # Môi trường RL — Khánh Đăng
├── huan_luyen.py           # Huấn luyện — Khánh Đăng
├── giao_dien.py            # Bảng điều khiển Tkinter — Vinh
├── test_tich_hop.py        # Test tích hợp 8 mục
├── so_sanh.py / so_sanh.csv
├── mo_hinh/q_model.json    # Model Q-learning đã huấn luyện (500 tập)
├── mo_hinh/dqn_model.keras # Model DQN đã huấn luyện (500 tập)
├── mo_hinh/lich_su_huan_luyen.csv  # Lịch sử reward Q-learning
├── mo_hinh/lich_su_dqn.csv         # Lịch sử reward DQN
├── requirements.txt / requirements-tf.txt
└── README.md
```
