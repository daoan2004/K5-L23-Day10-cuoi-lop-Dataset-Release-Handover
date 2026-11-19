#!/usr/bin/env python3
"""Dựng lô v2 (Pha 4) từ delivery v1 + errors.json đã chốt. KHÔNG sửa delivery/.

  python tools/build_handover.py --run runs/r3007
  python tools/build_handover.py --run runs/r3007 --broken-hash 000000001234   # ảnh wrong_hash mở ra thấy hỏng

Quy tắc (GUIDE Pha 4):
- Sửa ngay trong v2: wrong_hash (ảnh còn nguyên -> ghi hash mới; ảnh hỏng -> rework, dùng --broken-hash),
  guideline_mismatch (lấy guideline theo job), scene_leak (đưa cả cảnh về split đa số).
- Lỗi nhãn detection / thiếu file -> rework_queue.csv, bỏ khỏi v2.
- Lỗi chỉ ở panoptic -> ảnh ở lại v2, ghi vào Ghi chú README để báo team panoptic.
Ảnh và nhãn được chép NGUYÊN BYTE (không sửa tay nhãn). Sau khi chạy: đọc lại README.txt,
viết lại phần Ghi chú bằng lời của nhóm, rồi chạy pack_release.py và check_handover.py.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
from collections import Counter, defaultdict
from pathlib import Path

DET_REWORK = {"missing_image", "invalid_class", "bbox_out_of_bounds", "duplicate_box", "class_swap", "bbox_drift", "missing_box"}
PANOPTIC_ONLY = {"invalid_category_id", "thing_overlap", "category_swap", "instance_merge"}
ACTION = {
    "missing_image": "gửi lại file ảnh rồi kiểm lại nhãn",
    "invalid_class": "gán lại lớp hợp lệ (0-79)",
    "bbox_out_of_bounds": "vẽ lại box trong khung ảnh",
    "duplicate_box": "xoá box lặp",
    "class_swap": "sửa lớp của box theo vật thật",
    "bbox_drift": "vẽ lại box khớp vật",
    "missing_box": "thêm box cho vật bị thiếu",
    "wrong_hash": "ảnh hỏng: gửi lại ảnh gốc",
}
THRESHOLD = 0.02


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", required=True)
    ap.add_argument("--broken-hash", nargs="*", default=[], help="ảnh wrong_hash mở ra thấy HỎNG -> đưa vào rework")
    ap.add_argument("--force", action="store_true", help="ghi đè thư mục v2 đã có")
    args = ap.parse_args()
    run = Path(args.run)
    d = run / "delivery"
    rid = json.loads((d / "release.json").read_text(encoding="utf-8"))["release_id"]
    man = json.loads((d / "manifest.json").read_text(encoding="utf-8"))["items"]
    meta = {m["image"]: m for m in json.loads((d / "metadata.json").read_text(encoding="utf-8"))["items"]}
    with (d / "jobs.csv").open(encoding="utf-8", newline="") as f:
        jobs = {r["job_id"]: r for r in csv.DictReader(f)}
    names = {}
    for line in (d / "classes.txt").read_text(encoding="utf-8").splitlines():
        if line.strip():
            i, n = line.strip().split(" ", 1)
            names[int(i)] = n
    errors = json.loads((run / "errors.json").read_text(encoding="utf-8"))["errors"]

    by_img = {e["target"]: e["type"] for e in errors if e["target"] in man}
    leak_scenes = {e["target"] for e in errors if e["type"] == "scene_leak"}
    rework = {img: t for img, t in by_img.items() if t in DET_REWORK}
    for img in args.broken_hash:
        if by_img.get(img) != "wrong_hash":
            raise SystemExit(f"{img} không có lỗi wrong_hash trong errors.json")
        rework[img] = "wrong_hash"

    v2 = run / "handover" / f"{rid}_v2"
    if v2.exists():
        if not args.force:
            raise SystemExit(f"{v2} đã có; thêm --force để dựng lại")
        shutil.rmtree(v2)
    (v2 / "images").mkdir(parents=True)
    (v2 / "labels").mkdir()

    # split sau khi sửa: cảnh rò -> split đa số của cảnh
    scene_imgs = defaultdict(list)
    for img, m in meta.items():
        scene_imgs[m["scene_id"]].append(img)
    fixed_split, leak_notes = {}, []
    for sc in sorted(leak_scenes):
        cnt = Counter(meta[i]["split"] for i in scene_imgs[sc])
        major = cnt.most_common(1)[0][0]
        moved = [i for i in scene_imgs[sc] if meta[i]["split"] != major]
        for i in scene_imgs[sc]:
            fixed_split[i] = major
        leak_notes.append(f"{sc}: đưa {', '.join(moved)} về {major} (cả cảnh một split)")

    keep = []
    for img in sorted(man):
        if img in rework or not (d / man[img]["image"]).is_file():
            continue
        shutil.copyfile(d / man[img]["image"], v2 / "images" / f"{img}.jpg")
        shutil.copyfile(d / man[img]["label"], v2 / "labels" / f"{img}.txt")
        keep.append(img)

    with (v2 / "rework_queue.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["image", "type", "annotator", "reviewer", "action"])
        for img in sorted(rework):
            job = jobs[meta[img]["job_id"]]
            w.writerow([img, rework[img], job["annotator"], job["reviewer"], ACTION.get(rework[img], "gán lại")])

    with (v2 / "manifest.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["file", "sha256"])
        for sub in ("images", "labels"):
            for p in sorted((v2 / sub).iterdir()):
                w.writerow([f"{sub}/{p.name}", sha(p)])

    counts = Counter()
    for img in keep:
        for ln in (v2 / "labels" / f"{img}.txt").read_text(encoding="utf-8").splitlines():
            if ln.strip():
                counts[names[int(float(ln.split()[0]))]] += 1
    with (v2 / "label_summary.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["class", "count"])
        for k in sorted(names):
            if counts[names[k]]:
                w.writerow([names[k], counts[names[k]]])
        w.writerow(["TOTAL", sum(counts.values())])

    with (v2 / "truyvet.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["image", "scene_id", "split", "job_id", "annotator", "reviewer", "guideline"])
        for img in keep:
            m, job = meta[img], jobs[meta[img]["job_id"]]
            w.writerow([img, m["scene_id"], fixed_split.get(img, m["split"]), m["job_id"],
                        job["annotator"], job["reviewer"], job["guideline"]])

    # README
    n_err = len({e["target"] for e in errors})
    rate = n_err / len(man)
    v1 = "Hold" if rate > THRESHOLD else "Release"
    pct = f"{rate * 100:.1f}%".replace(".", ",")
    gl = defaultdict(list)
    for j in sorted(jobs):
        gl[jobs[j]["guideline"]].append(j)
    gl_txt = ", ".join(f"{v} ({js[0]}-{js[-1]})" if len(js) > 1 else f"{v} ({js[0]})" for v, js in sorted(gl.items()))
    hash_fixed = sorted(i for i, t in by_img.items() if t == "wrong_hash" and i not in rework)
    gm = sorted(i for i, t in by_img.items() if t == "guideline_mismatch")
    pan = sorted(f"{i} ({t})" for i, t in by_img.items() if t in PANOPTIC_ONLY)
    rw = sorted(f"{i} ({rework[i]}) -> {jobs[meta[i]['job_id']]['annotator']}/{jobs[meta[i]['job_id']]['reviewer']}" for i in rework)
    note = "; ".join(filter(None, [
        f"Split: {'; '.join(leak_notes)}" if leak_notes else "",
        f"Hash: {', '.join(hash_fixed)} đã mở ảnh kiểm, ảnh còn nguyên, chỉ manifest v1 ghi sai, manifest v2 ghi hash mới" if hash_fixed else "",
        f"Guideline: {', '.join(gm)} ghi sai phiên bản ở metadata, v2 lấy theo job trong jobs.csv" if gm else "",
        f"Rework ({len(rw)} ảnh, giao đúng người gán/kiểm của job): {'; '.join(rw)}" if rw else "",
        f"Lỗi chỉ ở panoptic, ảnh ở lại v2 vì nhãn detection đúng, báo team panoptic: {', '.join(pan)}" if pan else "",
    ]))
    readme = (
        f"Release: {rid}_v2\n"
        f"Parent: {rid}\n"
        f"Số ảnh: {len(keep)}\n"
        f"Số nhãn: {sum(counts.values())}\n"
        f"Guideline: {gl_txt}\n"
        f"QC v1: {n_err}/{len(man)} = {pct}\n"
        f"Kết luận v1: {v1} — {n_err}/{len(man)} ảnh/cảnh lỗi = {pct} "
        f"{'> 2% nên không Release' if v1 == 'Hold' else '<= 2%'}\n"
        f"Kết luận v2: Release — đã tách {len(rework)} ảnh lỗi nhãn detection sang rework_queue, "
        f"sửa split/hash/guideline trong v2; ảnh lỗi panoptic ở lại (nhãn detection đúng)\n"
        f"Ghi chú: {note}\n"
    )
    (v2 / "README.txt").write_text(readme, encoding="utf-8")
    print(f"v2: {len(keep)} ảnh, {sum(counts.values())} nhãn, rework {len(rework)} -> {v2}")
    print(f"QC v1 {n_err}/{len(man)} = {rate:.1%} => {v1}. ĐỌC LẠI README.txt và viết Ghi chú bằng lời của nhóm.")
    print(f"Tiếp: python scripts/pack_release.py {v2}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
