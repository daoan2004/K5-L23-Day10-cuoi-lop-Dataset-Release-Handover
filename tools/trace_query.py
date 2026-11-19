#!/usr/bin/env python3
"""Truy vết ticket của team AI (Pha 5).

  python tools/trace_query.py runs/r3007/delivery --out runs/r3007/trace.json
  python tools/trace_query.py delivery --out submission/de_an/trace.json --class car --scenes scene_123 scene_456

Mặc định đọc lớp bị đổi quy tắc và các cảnh được báo từ incoming/ticket.md (lớp: đoạn `...` đầu tiên,
cảnh: mọi chuỗi scene_xxx). Đọc kỹ ticket/changelog: nếu tự động đọc sai thì truyền --class/--scenes.

Tiêu chí (theo GUIDE Pha 5):
  điều kiện chung: job theo guideline CŨ (ghi ở jobs.csv, KHÔNG dùng guideline ghi ở từng ảnh)
                   và ảnh có >= 1 box detection (labels/) thuộc lớp bị đổi quy tắc
  tier_a = ảnh thoả điều kiện, nằm trong các cảnh ticket nêu
  tier_b = ảnh thoả điều kiện, ở cảnh khác (chưa ai báo)
  notify = annotator + reviewer của các job chứa ảnh tier_a và tier_b
"""
from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("delivery")
    ap.add_argument("--out", required=True)
    ap.add_argument("--class", dest="cls", help="tên lớp bị đổi quy tắc (mặc định đọc từ ticket)")
    ap.add_argument("--scenes", nargs="*", help="các scene team AI nêu (mặc định đọc từ ticket)")
    ap.add_argument("--old", help="phiên bản guideline cũ (mặc định: phiên bản thấp nhất trong jobs.csv)")
    args = ap.parse_args()
    d = Path(args.delivery)

    ticket = (d / "incoming" / "ticket.md").read_text(encoding="utf-8")
    cls = args.cls or re.search(r"`([^`]+)`", ticket).group(1)
    scenes = set(args.scenes or re.findall(r"scene_\w+", ticket))

    with (d / "jobs.csv").open(encoding="utf-8", newline="") as f:
        jobs = {r["job_id"]: r for r in csv.DictReader(f)}
    versions = sorted({j["guideline"] for j in jobs.values()}, key=lambda v: [int(x) for x in re.findall(r"\d+", v)])
    old = args.old or versions[0]
    old_jobs = {j for j, r in jobs.items() if r["guideline"] == old}

    names = {}
    for line in (d / "classes.txt").read_text(encoding="utf-8").splitlines():
        if line.strip():
            i, n = line.strip().split(" ", 1)
            names[i] = n
    meta = {m["image"]: m for m in json.loads((d / "metadata.json").read_text(encoding="utf-8"))["items"]}

    tier_a, tier_b, hit_jobs = [], [], set()
    for img, m in sorted(meta.items()):
        if m["job_id"] not in old_jobs:
            continue
        lab = d / "labels" / f"{img}.txt"
        if not lab.is_file():
            continue
        classes = {names.get(ln.split()[0]) for ln in lab.read_text(encoding="utf-8").splitlines() if ln.split()}
        if cls not in classes:
            continue
        (tier_a if m["scene_id"] in scenes else tier_b).append(img)
        hit_jobs.add(m["job_id"])
    notify = sorted({jobs[j]["annotator"] for j in hit_jobs} | {jobs[j]["reviewer"] for j in hit_jobs})

    out = {"tier_a": tier_a, "tier_b": tier_b, "notify": notify}
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8")
    print(f"lớp '{cls}', guideline cũ {old} (jobs {sorted(old_jobs)}), cảnh báo {sorted(scenes)}")
    print(f"tier_a {len(tier_a)} ảnh, tier_b {len(tier_b)} ảnh, notify {notify} -> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
