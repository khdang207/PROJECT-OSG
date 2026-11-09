import json
import os
import shutil
import subprocess

TEN_MANIFEST = "manifest.json"


def tim_rsync():
    return shutil.which("rsync")


def _quet_manifest(nguon):
    manifest = {}
    for goc, _thu_muc, tap_tin in os.walk(nguon):
        for ten in tap_tin:
            duong_dan = os.path.join(goc, ten)
            duong_dan_tuong_doi = os.path.relpath(duong_dan, nguon)
            thong_tin = os.stat(duong_dan)
            manifest[duong_dan_tuong_doi] = {
                "kich_thuoc": thong_tin.st_size,
                "thoi_gian_sua": thong_tin.st_mtime,
            }
    return manifest


def _lay_manifest(thu_muc_dich):
    """Doc manifest; file hong hoac sai dinh dang thi tra ve {} chu khong crash."""
    duong_dan = os.path.join(thu_muc_dich, TEN_MANIFEST)
    if os.path.exists(duong_dan):
        try:
            with open(duong_dan, "r", encoding="utf-8") as f:
                du_lieu = json.load(f)
            return du_lieu if isinstance(du_lieu, dict) else {}
        except (OSError, ValueError):
            return {}
    return {}


def _luu_manifest(thu_muc_dich, manifest):
    with open(os.path.join(thu_muc_dich, TEN_MANIFEST), "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)


def backup_bang_rsync(nguon, dich):
    """Backup bang rsync, tra ve thong ke so file da copy."""
    os.makedirs(dich, exist_ok=True)
    nguon_chuan = nguon if nguon.endswith(os.sep) else nguon + os.sep
    chay = subprocess.run(
        ["rsync", "-a", "--delete", "--itemize-changes",
         nguon_chuan, dich],  # --delete: dich phan anh dung nguon, file da xoa khong con sot
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    if chay.returncode != 0:
        raise RuntimeError(f"rsync loi: {chay.stderr.strip()}")
    so_file = 0
    for dong in chay.stdout.splitlines():
        if dong.startswith(">f"):
            so_file += 1
    _luu_manifest(dich, _quet_manifest(nguon))
    return {"cach": "rsync", "so_file_da_copy": so_file}


def backup_bang_python(nguon, dich):
    os.makedirs(dich, exist_ok=True)
    manifest_cu = _lay_manifest(dich)
    manifest_moi = _quet_manifest(nguon)
    so_file_moi = 0
    so_file_cap_nhat = 0
    for duong_dan_tuong_doi, thong_tin in manifest_moi.items():
        nguon_file = os.path.join(nguon, duong_dan_tuong_doi)
        dich_file = os.path.join(dich, duong_dan_tuong_doi)
        cu = manifest_cu.get(duong_dan_tuong_doi)
        if cu is None:
            so_file_moi += 1
        elif (cu["kich_thuoc"] != thong_tin["kich_thuoc"]
              or cu["thoi_gian_sua"] != thong_tin["thoi_gian_sua"]):
            so_file_cap_nhat += 1
        else:
            continue
        thu_muc_dich_file = os.path.dirname(dich_file)
        if thu_muc_dich_file:
            os.makedirs(thu_muc_dich_file, exist_ok=True)
        shutil.copy2(nguon_file, dich_file)
    # Xoa file dich con sot tu manifest cu (giong --delete cua rsync),
    # tru manifest.json cua chinh thu muc dich.
    for duong_dan_tuong_doi in manifest_cu:
        if duong_dan_tuong_doi in manifest_moi:
            continue
        dich_file = os.path.join(dich, duong_dan_tuong_doi)
        if os.path.isfile(dich_file):
            os.remove(dich_file)
    _luu_manifest(dich, manifest_moi)
    return {"cach": "python", "so_file_moi": so_file_moi,
            "so_file_cap_nhat": so_file_cap_nhat}


def backup(nguon, dich):
    if not os.path.isdir(nguon):
        raise ValueError(f"Thu muc nguon khong ton tai: {nguon}")
    if tim_rsync():
        return backup_bang_rsync(nguon, dich)
    return backup_bang_python(nguon, dich)


def khoi_phuc(dich, nguon):
    if not os.path.isdir(dich):
        raise ValueError(f"Thu muc backup khong ton tai: {dich}")
    os.makedirs(nguon, exist_ok=True)
    manifest = _lay_manifest(dich)
    so_file = 0
    for duong_dan_tuong_doi in manifest:
        nguon_file = os.path.join(dich, duong_dan_tuong_doi)
        dich_file = os.path.join(nguon, duong_dan_tuong_doi)
        if not os.path.exists(nguon_file):
            continue
        thu_muc_dich_file = os.path.dirname(dich_file)
        if thu_muc_dich_file:
            os.makedirs(thu_muc_dich_file, exist_ok=True)
        shutil.copy2(nguon_file, dich_file)
        so_file += 1
    return {"so_file_da_khoi_phuc": so_file}


def trang_thai(dich):
    manifest = _lay_manifest(dich)
    tong_dung_luong = sum(v["kich_thuoc"] for v in manifest.values())
    return {"so_file": len(manifest), "tong_dung_luong": tong_dung_luong}
