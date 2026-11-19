#!/usr/bin/env python3
"""Vẽ ứng viên lên ảnh để cả nhóm review bằng mắt (Pha 2). Dùng Pillow (chỉ cho công cụ xem ảnh).

  python tools/review_viewer.py runs/r3007/delivery runs/r3007/candidates.json --out runs/r3007/review

Sinh ra:
  <out>/NN_<ảnh>.png       ảnh gốc | ảnh đã vẽ (phóng to vùng quanh vật)
  <out>/index.html         mở bằng trình duyệt để xem lần lượt
  <out>/review_todo.csv    khung review_log: điền verdict (confirmed/rejected) + note (thấy gì), chọn đúng type

Màu: ĐỎ = box detection của ứng viên, CAM = box thứ hai (instance_merge),
     XANH LÁ = viền segment panoptic của ứng viên (tô mờ), XÁM = các box detection khác.
"""
from __future__ import annotations

import argparse
import csv
import html
import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import pngutil  # noqa: E402


def load_names(delivery: Path) -> dict:
    out = {}
    for line in (delivery / "classes.txt").read_text(encoding="utf-8").splitlines():
        if line.strip():
            i, n = line.strip().split(" ", 1)
            out[int(i)] = n
    return out


def seg_mask(delivery: Path, name: str, seg_id: int) -> Image.Image | None:
    p = delivery / "masks" / f"{name}.png"
    if not p.is_file() or seg_id is None:
        return None
    w, h, px = pngutil.read_rgb(p)
    out = bytearray(w * h)
    for i in range(w * h):
        if pngutil.segment_id(px, i * 3) == seg_id:
            out[i] = 255
    return Image.frombytes("L", (w, h), bytes(out))


def draw_one(delivery: Path, c: dict, names: dict, zoom_to: int) -> Image.Image:
    name = c["image"]
    img_p = delivery / "images" / f"{name}.jpg"
    m = seg_mask(delivery, name, c.get("seg_id"))
    try:
        base = Image.open(img_p).convert("RGB")
    except Exception:  # thiếu hoặc hỏng ảnh: vẽ trên nền đen cỡ mask
        print(f"  cảnh báo: không mở được {img_p}", file=sys.stderr)
        base = Image.new("RGB", m.size if m is not None else (640, 480), "black")
    W, H = base.size
    ov = base.copy()
    if m is not None and m.size == base.size:
        green = Image.new("RGB", base.size, (0, 220, 0))
        ov = Image.composite(Image.blend(ov, green, 0.45), ov, m)
        edge = m.filter(__import__("PIL.ImageFilter", fromlist=["FIND_EDGES"]).FIND_EDGES)
        ov.paste((0, 255, 0), mask=edge)
    d = ImageDraw.Draw(ov)
    lab = delivery / "labels" / f"{name}.txt"
    if lab.is_file():
        for ln in lab.read_text(encoding="utf-8").splitlines():
            p = ln.split()
            if len(p) != 5:
                continue
            k, x, y, w, h = int(float(p[0])), *map(float, p[1:])
            d.rectangle([(x - w / 2) * W, (y - h / 2) * H, (x + w / 2) * W, (y + h / 2) * H], outline=(160, 160, 160), width=1)
            d.text(((x - w / 2) * W + 2, (y - h / 2) * H + 1), names.get(k, str(k)), fill=(200, 200, 200))
    if "other_box" in c:
        d.rectangle(c["other_box"], outline=(255, 140, 0), width=3)
    if "box" in c:
        d.rectangle(c["box"], outline=(255, 0, 0), width=3)
    if "seg_bbox" in c:
        d.rectangle(c["seg_bbox"], outline=(0, 255, 0), width=1)
    # cắt vùng quanh ứng viên rồi phóng to (ảnh nhỏ ~240x320 khó nhìn)
    boxes = [c[k] for k in ("box", "other_box", "seg_bbox") if k in c]
    x0 = min(b[0] for b in boxes); y0 = min(b[1] for b in boxes)
    x1 = max(b[2] for b in boxes); y1 = max(b[3] for b in boxes)
    pad = 0.35 * max(x1 - x0, y1 - y0, 40)
    crop = (max(0, int(x0 - pad)), max(0, int(y0 - pad)), min(W, int(x1 + pad)), min(H, int(y1 + pad)))
    raw, drawn = base.crop(crop), ov.crop(crop)
    s = zoom_to / max(raw.size)
    size = (max(1, int(raw.width * s)), max(1, int(raw.height * s)))
    raw, drawn = raw.resize(size, Image.LANCZOS), drawn.resize(size, Image.LANCZOS)
    sheet = Image.new("RGB", (size[0] * 2 + 10, size[1]), "white")
    sheet.paste(raw, (0, 0)); sheet.paste(drawn, (size[0] + 10, 0))
    return sheet


def describe(c: dict) -> str:
    t = c["type"]
    if t == "class_swap|category_swap":
        return f"detection ghi <b>{c['det_class']}</b>, panoptic ghi <b>{c['pan_class']}</b>. {c['hint']}"
    if t == "bbox_drift":
        return f"box {c['cls']}: chỉ {c['pixel_cov']:.0%} pixel segment nằm trong box (IoU {c['iou']})"
    if t == "missing_box":
        return f"segment {c['cls']} {c['area_px']} px không có box cùng lớp (phủ tốt nhất {c['best_same_class_cov']})"
    if t == "instance_merge":
        return f"một segment {c['cls']} trải ra 2 box (đỏ + cam), phủ {c['pixel_cov']}"
    return t


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("delivery")
    ap.add_argument("candidates")
    ap.add_argument("--out", required=True)
    ap.add_argument("--zoom", type=int, default=520, help="cạnh dài của vùng cắt sau khi phóng to (px)")
    args = ap.parse_args()
    delivery, out = Path(args.delivery), Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    names = load_names(delivery)
    cands = json.loads(Path(args.candidates).read_text(encoding="utf-8"))["candidates"]
    rows, cards = [], []
    for i, c in enumerate(cands, 1):
        fn = f"{i:02d}_{c['image']}.png"
        draw_one(delivery, c, names, args.zoom).save(out / fn)
        suggested = "" if "|" in c["type"] else c["type"]
        rows.append({"image": c["image"], "type": suggested, "verdict": "", "note": ""})
        cards.append(f"<div class=c><h3>{i}. {c['image']} — {html.escape(c['type'])} (score {c['score']})</h3>"
                     f"<p>{describe(c)}</p><img src='{fn}'></div>")
    with (out / "review_todo.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["image", "type", "verdict", "note"])
        w.writeheader(); w.writerows(rows)
    (out / "index.html").write_text(
        "<meta charset=utf-8><style>body{font-family:sans-serif;max-width:1150px;margin:auto}"
        ".c{border-bottom:1px solid #ccc;padding:12px 0}img{max-width:100%}</style>"
        "<h1>Hàng đợi review</h1><p>Trái: ảnh gốc. Phải: ĐỎ box ứng viên, CAM box thứ hai, XANH segment panoptic, XÁM box khác.</p>"
        + "".join(cards), encoding="utf-8")
    print(f"{len(cands)} ứng viên -> {out}/index.html ; điền {out}/review_todo.csv rồi lưu thành review_log.csv")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
