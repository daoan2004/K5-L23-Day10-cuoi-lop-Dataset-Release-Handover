"""Doi chieu detection <-> panoptic, sinh ung vien loi gan nhan.

Ung vien: class_swap|category_swap, bbox_drift, missing_box, instance_merge.
Logic nam trong validate.cross_check (dung chung 1 cho validate.py --candidates va file nay),
file nay chi la cua ngo goi duoc de import/chay rieng.
Chi dung thu vien chuan. Chi doc thu muc delivery, khong doc _private/.

  python validator/crosscheck.py <delivery> --out candidates.json [--missing-cov 0.7 ...]
"""
import json
import sys
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parent))
import validate  # noqa: E402

DEFAULTS = dict(match_iou=0.3, drift_cov=0.95, swap_iou=0.7, merge_part=0.15,
                merge_single=0.85, merge_total=0.85, missing_frac=0.004, missing_cov=0.7)


def find_candidates(delivery, **thr):
    """Tra ve list ung vien (moi anh toi da 1 ung vien diem cao nhat)."""
    args = SimpleNamespace(**{**DEFAULTS, **thr})
    d = validate.Delivery(Path(delivery))
    masks = {}
    for name in d.names:
        p = d.root / d.manifest[name].get("mask", f"masks/{name}.png")
        if p.is_file():
            masks[name] = validate.MaskStats(p)
    best = {}
    for c in validate.cross_check(d, masks, args):
        best.setdefault(c["image"], c)
    return sorted(best.values(), key=lambda c: -c["score"])


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("delivery")
    ap.add_argument("--out", required=True)
    for k, v in DEFAULTS.items():
        ap.add_argument("--" + k.replace("_", "-"), type=float, default=v)
    a = vars(ap.parse_args())
    out = a.pop("out"); delivery = a.pop("delivery")
    cands = find_candidates(delivery, **a)
    Path(out).write_text(json.dumps({"candidates": cands}, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"{len(cands)} ung vien -> {out}")
