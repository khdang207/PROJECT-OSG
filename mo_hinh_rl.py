"""Tac nhan hoc tang cuong - Giai doan 3 (Khanh Dang).

Co 2 tac nhan cung giao dien:
  - TacNhanQ: bang Q (Q-learning), chay ngay khong can TensorFlow.
  - TacNhanDQN: mang neuron bang TensorFlow (can cai tensorflow).
"""

import json
import os
import random

TOC_DO_HOC = 0.1
HE_SO_GIAM = 0.95


class TacNhanQ:
    def __init__(self, epsilon=0.1, seed=0):
        self.bang_q = {}
        self.epsilon = epsilon
        self.rng = random.Random(seed)

    def _lay_q(self, trang_thai):
        khoa = str(trang_thai)
        if khoa not in self.bang_q:
            self.bang_q[khoa] = [0.0, 0.0]
        return self.bang_q[khoa]

    def da_gap(self, trang_thai):
        """True neu tac nhan da gap trang thai nay khi huan luyen."""
        return str(trang_thai) in self.bang_q

    def chon_hanh_dong(self, trang_thai, huan_luyen=True):
        q = self._lay_q(trang_thai)
        if huan_luyen and self.rng.random() < self.epsilon:
            return self.rng.randint(0, 1)
        return 1 if q[1] > q[0] else 0

    def hoc(self, trang_thai, hanh_dong, phan_thuong, trang_thai_moi, ket_thuc):
        q = self._lay_q(trang_thai)
        muc_tieu = phan_thuong
        if not ket_thuc:
            q_moi = self._lay_q(trang_thai_moi)
            muc_tieu += HE_SO_GIAM * max(q_moi)
        q[hanh_dong] += TOC_DO_HOC * (muc_tieu - q[hanh_dong])

    def luu(self, duong_dan):
        thu_muc = os.path.dirname(duong_dan)
        if thu_muc:
            os.makedirs(thu_muc, exist_ok=True)
        with open(duong_dan, "w", encoding="utf-8") as f:
            json.dump(self.bang_q, f, ensure_ascii=False, indent=2)

    @classmethod
    def tai(cls, duong_dan, epsilon=0.0):
        tac_nhan = cls(epsilon=epsilon)
        with open(duong_dan, "r", encoding="utf-8") as f:
            tac_nhan.bang_q = json.load(f)
        return tac_nhan


class TacNhanDQN:
    """Tac nhan DQN bang TensorFlow. Can cai: pip install -r requirements-tf.txt"""

    def __init__(self, epsilon=0.1, seed=0):
        try:
            import tensorflow as tf
        except ImportError:
            raise RuntimeError(
                "Chua co TensorFlow. Cai bang: pip install -r requirements-tf.txt")
        self.tf = tf
        self.epsilon = epsilon
        self.rng = random.Random(seed)
        self.mo_hinh = self._xay_mo_hinh()

    def _xay_mo_hinh(self):
        mo_hinh = self.tf.keras.Sequential([
            self.tf.keras.layers.Input(shape=(3,)),
            self.tf.keras.layers.Dense(32, activation="relu"),
            self.tf.keras.layers.Dense(32, activation="relu"),
            self.tf.keras.layers.Dense(2),
        ])
        mo_hinh.compile(optimizer="adam", loss="mse")
        return mo_hinh

    def _ma_hoa(self, trang_thai):
        # Keras 3 (TensorFlow 2.16+) khong nhan list Python thuan o
        # predict/fit nen ma hoa thanh mang numpy 2 chieu (1 mau, 3 dac trung).
        import numpy as np
        gio, cpu_loai, ram_loai = trang_thai
        return np.array([[gio / 23.0, cpu_loai / 2.0, ram_loai / 2.0]],
                        dtype=np.float32)

    def chon_hanh_dong(self, trang_thai, huan_luyen=True):
        import numpy as np
        q = self.mo_hinh.predict(self._ma_hoa(trang_thai), verbose=0)[0]
        if huan_luyen and self.rng.random() < self.epsilon:
            return self.rng.randint(0, 1)
        return int(np.argmax(q))

    def hoc(self, trang_thai, hanh_dong, phan_thuong, trang_thai_moi, ket_thuc):
        import numpy as np
        q = self.mo_hinh.predict(self._ma_hoa(trang_thai), verbose=0)[0]
        muc_tieu = phan_thuong
        if not ket_thuc:
            q_moi = self.mo_hinh.predict(self._ma_hoa(trang_thai_moi),
                                         verbose=0)[0]
            muc_tieu += HE_SO_GIAM * float(np.max(q_moi))
        q[hanh_dong] = muc_tieu
        self.mo_hinh.fit(self._ma_hoa(trang_thai),
                         np.array([q], dtype=np.float32), verbose=0)

    def luu(self, duong_dan):
        self.mo_hinh.save(duong_dan)

    @classmethod
    def tai(cls, duong_dan, epsilon=0.0):
        tac_nhan = cls.__new__(cls)
        import tensorflow as tf
        tac_nhan.tf = tf
        tac_nhan.epsilon = epsilon
        tac_nhan.rng = random.Random(0)
        tac_nhan.mo_hinh = tf.keras.models.load_model(duong_dan)
        return tac_nhan
