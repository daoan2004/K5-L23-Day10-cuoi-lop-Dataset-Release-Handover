#!/usr/bin/env python3
"""Validator của nhóm cho lô bàn giao Day 10.

  python validator/validate.py <delivery> --out errors.json [--candidates candidates.json]

- Chỉ đọc thư mục <delivery> được truyền vào; chỉ thư viện chuẩn; không dùng mạng.
- errors.json  : CHỈ lỗi luật (máy chứng minh được). Lỗi gán nhãn phải qua review bằng mắt,
                 rồi gộp bằng scripts/merge_review.py.
- candidates.json : ứng viên lỗi gán nhãn (đối chiếu detection <-> panoptic) để cả nhóm mở ảnh xem.

Ngưỡng đối chiếu chỉnh bằng tham số dòng lệnh (--drift-cov, --drift-iou, --missing-frac, ...)
và phải được đo trên lô sạch (runs/clean) trước khi dùng.
"""
from __future__ import annotations

import argparse
import bisect
import csv
import hashlib
import json
import math
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import pngutil  # noqa: E402  (đọc PNG bằng thư viện chuẩn, được phép theo RULES)

NUM_CLASSES = 80


# ----------------------------------------------------------------------------- tiện ích
def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:  # tính trên BYTES, không phải text
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def iou(a, b) -> float:
    """a, b = (x0, y0, x1, y1) toạ độ pixel liên tục."""
    ix = max(0.0, min(a[2], b[2]) - max(a[0], b[0]))
    iy = max(0.0, min(a[3], b[3]) - max(a[1], b[1]))
    inter = ix * iy
    ua = (a[2] - a[0]) * (a[3] - a[1]) + (b[2] - b[0]) * (b[3] - b[1]) - inter
    return inter / ua if ua > 0 else 0.0


def union_box(a, b):
    return (min(a[0], b[0]), min(a[1], b[1]), max(a[2], b[2]), max(a[3], b[3]))


# ----------------------------------------------------------------------------- nạp lô
class Delivery:
    def __init__(self, root: Path):
        self.root = root
        self.manifest = read_json(root / "manifest.json")["items"]
        self.meta = {m["image"]: m for m in read_json(root / "metadata.json")["items"]}
        with (root / "jobs.csv").open(encoding="utf-8", newline="") as f:
            self.jobs = {r["job_id"].strip(): r for r in csv.DictReader(f)}
        self.class_names = {}
        for line in (root / "classes.txt").read_text(encoding="utf-8").splitlines():
            if line.strip():
                idx, name = line.strip().split(" ", 1)
                self.class_names[int(idx)] = name.strip()
        pan = read_json(root / "panoptic.json")
        self.categories = {c["id"]: c for c in pan["categories"]}
        self.cat_name_to_id = {c["name"]: c["id"] for c in pan["categories"]}
        self.things = {c["id"] for c in pan["categories"] if c.get("isthing")}
        img_by_id = {im["id"]: im for im in pan["images"]}
        self.pan = {}  # tên ảnh -> (image info, annotation)
        for ann in pan["annotations"]:
            name = Path(ann["file_name"]).stem
            self.pan[name] = (img_by_id.get(ann["image_id"], {}), ann)
        self.names = sorted(self.manifest)

    def label_rows(self, name: str):
        rel = self.manifest[name].get("label", f"labels/{name}.txt")
        p = self.root / rel
        if not p.is_file():
            return []
        rows = []
        for line in p.read_text(encoding="utf-8").splitlines():
            parts = line.split()
            if len(parts) == 5:
                rows.append(parts)
        return rows


# ----------------------------------------------------------------------------- mask
class MaskStats:
    """Quét mask một lần: số pixel thật, bbox thật và các 'run' theo hàng cho từng segment."""

    def __init__(self, path: Path):
        self.width, self.height, pixels = pngutil.read_rgb(path)
        W = self.width
        self.count = defaultdict(int)
        self.bbox = {}
        # runs[sid] = {y: [(x_start, x_end_exclusive), ...]}
        self.runs = defaultdict(dict)
        for y in range(self.height):
            row = pixels[y * W * 3:(y + 1) * W * 3]
            prev, start = None, 0
            x = 0
            for r, g, b in zip(row[0::3], row[1::3], row[2::3]):
                sid = r + (g << 8) + (b << 16)
                if sid != prev:
                    if prev:
                        self._add_run(prev, y, start, x)
                    prev, start = sid, x
                x += 1
            if prev:
                self._add_run(prev, y, start, x)
        self.row_keys = {sid: sorted(rows) for sid, rows in self.runs.items()}

    def _add_run(self, sid, y, x0, x1):
        self.count[sid] += x1 - x0
        self.runs[sid].setdefault(y, []).append((x0, x1))
        bb = self.bbox.get(sid)
        if bb is None:
            self.bbox[sid] = [x0, y, x1, y + 1]
        else:
            bb[0] = min(bb[0], x0); bb[1] = min(bb[1], y)
            bb[2] = max(bb[2], x1); bb[3] = max(bb[3], y + 1)

    def inside(self, sid: int, box, margin: float = 1.0) -> int:
        """Số pixel của segment sid nằm trong box (x0, y0, x1, y1), nới margin pixel."""
        rows = self.runs.get(sid)
        if not rows:
            return 0
        x0, y0, x1, y1 = box[0] - margin, box[1] - margin, box[2] + margin, box[3] + margin
        # pixel (x, y) thuộc box nếu tâm (x+0.5, y+0.5) nằm trong box
        px_lo, px_hi = math.ceil(x0 - 0.5), math.floor(x1 - 0.5) + 1   # [px_lo, px_hi)
        py_lo, py_hi = math.ceil(y0 - 0.5), math.floor(y1 - 0.5) + 1
        keys = self.row_keys[sid]
        total = 0
        for k in keys[bisect.bisect_left(keys, py_lo):bisect.bisect_left(keys, py_hi)]:
            for a, b in rows[k]:
                lo_x, hi_x = max(a, px_lo), min(b, px_hi)
                if hi_x > lo_x:
                    total += hi_x - lo_x
        return total


# ----------------------------------------------------------------------------- luật
def check_rules(d: Delivery, masks: dict, errors: list):
    seen_err = set()

    def add(kind, target):
        if (kind, target) not in seen_err:
            seen_err.add((kind, target))
            errors.append({"type": kind, "target": target})

    # --- file: missing_image, wrong_hash
    for name in d.names:
        item = d.manifest[name]
        img = d.root / item.get("image", f"images/{name}.jpg")
        if not img.is_file():
            add("missing_image", name)
            continue
        if sha256_file(img) != item.get("image_sha256", "").lower():
            add("wrong_hash", name)

    # --- nhãn detection
    for name in d.names:
        info, _ = d.pan.get(name, ({}, None))
        W = info.get("width") or (masks[name].width if name in masks else None)
        H = info.get("height") or (masks[name].height if name in masks else None)
        rows = d.label_rows(name)
        parsed = []
        for r in rows:
            try:
                cls = int(r[0])
                x, y, w, h = map(float, r[1:5])
            except ValueError:
                add("invalid_class", name)
                continue
            if not (0 <= cls < NUM_CLASSES):
                add("invalid_class", name)
                continue
            eps = 0.002  # ~1 pixel: chỉ làm tròn số, không phải tràn mép thật
            if x - w / 2 < -eps or y - h / 2 < -eps or x + w / 2 > 1 + eps or y + h / 2 > 1 + eps:
                add("bbox_out_of_bounds", name)
            parsed.append((cls, x, y, w, h))
        # duplicate_box: cùng lớp, CÙNG kích thước, tâm lệch <= 3 pixel
        if W and H:
            for i in range(len(parsed)):
                for j in range(i + 1, len(parsed)):
                    a, b = parsed[i], parsed[j]
                    if a[0] != b[0]:
                        continue
                    same_size = abs(a[3] - b[3]) * W < 0.5 and abs(a[4] - b[4]) * H < 0.5
                    dx, dy = abs(a[1] - b[1]) * W, abs(a[2] - b[2]) * H
                    if same_size and dx <= 3.0 and dy <= 3.0:
                        add("duplicate_box", name)

    # --- metadata: guideline_mismatch (so với JOB), scene_leak (target = scene)
    scene_splits = defaultdict(set)
    for name, m in d.meta.items():
        scene_splits[m["scene_id"]].add(m["split"])
        job = d.jobs.get(m.get("job_id", ""))
        if job and m.get("guideline_version", "").strip() != job["guideline"].strip():
            add("guideline_mismatch", name)
    for scene, splits in sorted(scene_splits.items()):
        if len(splits) > 1:
            add("scene_leak", scene)

    # --- panoptic: invalid_category_id, thing_overlap
    for name in d.names:
        if name not in d.pan:
            continue
        _, ann = d.pan[name]
        ms = masks.get(name)
        for s in ann.get("segments_info", []):
            if s["category_id"] not in d.categories:
                add("invalid_category_id", name)
                continue
            if ms is not None and s.get("area", 0) > ms.count.get(s["id"], 0):
                # area khai nhiều hơn số pixel thật: segment đã bị vật khác đè
                add("thing_overlap", name)


# ----------------------------------------------------------------------------- đối chiếu
def cross_check(d: Delivery, masks: dict, args) -> list:
    cands = []
    for name in d.names:
        if name not in masks or name not in d.pan:
            continue
        ms = masks[name]
        W, H = ms.width, ms.height
        _, ann = d.pan[name]
        segs = []
        for s in ann.get("segments_info", []):
            cid = s["category_id"]
            if cid not in d.things or s.get("iscrowd") or ms.count.get(s["id"], 0) == 0:
                continue
            bb = ms.bbox[s["id"]]
            segs.append({"id": s["id"], "cls": d.categories[cid]["name"], "area": ms.count[s["id"]],
                         "bbox": tuple(bb)})
        boxes = []
        for r in d.label_rows(name):
            try:
                cls = int(r[0]); x, y, w, h = map(float, r[1:5])
            except ValueError:
                continue
            if not (0 <= cls < NUM_CLASSES):
                continue
            boxes.append({"cls": d.class_names.get(cls, str(cls)),
                          "box": ((x - w / 2) * W, (y - h / 2) * H, (x + w / 2) * W, (y + h / 2) * H)})

        # ma trận cặp: IoU bbox và độ phủ pixel (phần segment nằm trong box)
        pair = {}
        for bi, b in enumerate(boxes):
            for si, s in enumerate(segs):
                ov = iou(b["box"], s["bbox"])
                if ov <= 0:
                    continue
                cov = ms.inside(s["id"], b["box"]) / s["area"]
                pair[bi, si] = (ov, cov)

        def emit(kind, score, **info):
            cands.append({"image": name, "type": kind, "score": round(score, 3), **info})

        def rnd(b):
            return [round(v, 1) for v in b]

        used_b, used_s = set(), set()

        # 1) instance_merge: pixel của MỘT segment chia ra >= 2 box cùng lớp, không box nào phủ trọn nó.
        #    (Cặp người/xe chồng nhau tự nhiên: segment của mỗi vật vẫn nằm gọn trong box của chính nó.)
        for si, s in enumerate(segs):
            covs = sorted(((pair[bi, si][1], bi) for bi, b in enumerate(boxes)
                           if (bi, si) in pair and b["cls"] == s["cls"] and pair[bi, si][1] >= args.merge_part),
                          reverse=True)
            if len(covs) >= 2 and covs[0][0] < args.merge_single and covs[0][0] + covs[1][0] >= args.merge_total:
                b1, b2 = covs[0][1], covs[1][1]
                used_s.add(si); used_b.update((b1, b2))
                emit("instance_merge", covs[0][0] + covs[1][0], cls=s["cls"], seg_id=s["id"], seg_bbox=list(s["bbox"]),
                     box=rnd(boxes[b1]["box"]), other_box=rnd(boxes[b2]["box"]),
                     pixel_cov=[round(covs[0][0], 3), round(covs[1][0], 3)])

        # 2) ghép một-một CÙNG lớp, tham lam theo IoU bbox
        match_b, match_s = {}, {}
        same = sorted(((v[0], bi, si) for (bi, si), v in pair.items()
                       if bi not in used_b and si not in used_s
                       and boxes[bi]["cls"] == segs[si]["cls"] and v[0] >= args.match_iou), reverse=True)
        for ov, bi, si in same:
            if bi not in match_b and si not in match_s:
                match_b[bi], match_s[si] = si, bi
        used_b.update(match_b); used_s.update(match_s)

        # 3) bbox_drift: cặp đã ghép nhưng một phần pixel của segment rơi ra ngoài box.
        #    Không dùng IoU bbox: vật bị che làm IoU giảm nhưng pixel vẫn nằm trọn trong box.
        for bi, si in match_b.items():
            ov, cov = pair[bi, si]
            if cov < args.drift_cov:
                emit("bbox_drift", 1 - cov, cls=boxes[bi]["cls"], seg_id=segs[si]["id"], box=rnd(boxes[bi]["box"]),
                     seg_bbox=list(segs[si]["bbox"]), iou=round(ov, 3), pixel_cov=round(cov, 3))

        # 4) box chưa ghép trùng vị trí segment KHÁC lớp chưa ghép -> class_swap hoặc category_swap
        for bi, b in enumerate(boxes):
            if bi in used_b:
                continue
            best = max(((pair[bi, si][0], si) for si in range(len(segs))
                        if (bi, si) in pair and si not in used_s and segs[si]["cls"] != b["cls"]),
                       default=(0, None))
            if best[1] is not None and best[0] >= args.swap_iou:
                si = best[1]
                used_s.add(si); used_b.add(bi)
                emit("class_swap|category_swap", best[0], det_class=b["cls"], pan_class=segs[si]["cls"], seg_id=segs[si]["id"],
                     box=rnd(b["box"]), seg_bbox=list(segs[si]["bbox"]), iou=round(best[0], 3),
                     hint="mở ảnh: vật thật là det_class -> category_swap; là pan_class -> class_swap")

        # 5) missing_box: segment lớn chưa ghép, không box cùng lớp nào phủ đáng kể
        for si, s in enumerate(segs):
            if si in used_s or s["area"] < args.missing_frac * W * H:
                continue
            covered = max((pair[bi, si][1] for bi, b in enumerate(boxes)
                           if (bi, si) in pair and b["cls"] == s["cls"]), default=0.0)
            if covered < args.missing_cov:
                emit("missing_box", s["area"] / (W * H) * 10, cls=s["cls"], seg_id=s["id"], seg_bbox=list(s["bbox"]),
                     area_px=s["area"], best_same_class_cov=round(covered, 3))

    cands.sort(key=lambda c: -c["score"])
    return cands


# ----------------------------------------------------------------------------- main
def main() -> int:
    ap = argparse.ArgumentParser(description="Validator Day 10: lỗi luật + ứng viên đối chiếu")
    ap.add_argument("delivery")
    ap.add_argument("--out", required=True, help="errors.json (chỉ lỗi luật)")
    ap.add_argument("--candidates", help="candidates.json (ứng viên lỗi gán nhãn để review)")
    ap.add_argument("--match-iou", type=float, default=0.3, help="IoU tối thiểu để ghép box với segment cùng lớp")
    ap.add_argument("--drift-cov", type=float, default=0.95, help="dưới mức này: pixel segment rơi ra ngoài box")
    ap.add_argument("--swap-iou", type=float, default=0.7, help="IoU tối thiểu để coi box/segment khác lớp là cùng vật")
    ap.add_argument("--merge-part", type=float, default=0.15, help="mỗi box phải chứa >= tỉ lệ này pixel của segment")
    ap.add_argument("--merge-single", type=float, default=0.85, help="không box nào chứa >= tỉ lệ này (nếu có: segment là của box đó)")
    ap.add_argument("--merge-total", type=float, default=0.85, help="hai box cộng lại phải chứa >= tỉ lệ này")
    ap.add_argument("--missing-frac", type=float, default=0.004, help="segment phải chiếm >= tỉ lệ này của ảnh")
    ap.add_argument("--missing-cov", type=float, default=0.7)
    args = ap.parse_args()

    root = Path(args.delivery)
    d = Delivery(root)

    masks = {}
    for i, name in enumerate(d.names, 1):
        rel = d.manifest[name].get("mask", f"masks/{name}.png")
        p = root / rel
        if p.is_file():
            masks[name] = MaskStats(p)
        if i % 50 == 0:
            print(f"  đã đọc {i}/{len(d.names)} mask", file=sys.stderr)

    errors = []
    check_rules(d, masks, errors)
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps({"errors": errors}, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    by_type = defaultdict(int)
    for e in errors:
        by_type[e["type"]] += 1
    print(f"{len(errors)} lỗi luật -> {args.out}  {dict(by_type)}")

    if args.candidates:
        rule_imgs = {e["target"] for e in errors}
        cands = [c for c in cross_check(d, masks, args) if c["image"] not in rule_imgs]  # mỗi ảnh tối đa 1 lỗi
        # mỗi ảnh chỉ giữ ứng viên điểm cao nhất (lỗi gài: tối đa một lỗi/ảnh)
        best = {}
        for c in cands:
            best.setdefault(c["image"], c)
        cands = sorted(best.values(), key=lambda c: -c["score"])
        Path(args.candidates).write_text(json.dumps({"candidates": cands}, indent=1, ensure_ascii=False) + "\n",
                                         encoding="utf-8")
        kinds = defaultdict(int)
        for c in cands:
            kinds[c["type"]] += 1
        print(f"{len(cands)} ứng viên -> {args.candidates}  {dict(kinds)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
