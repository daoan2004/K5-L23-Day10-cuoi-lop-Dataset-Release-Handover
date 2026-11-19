"""Truy vết ticket từ delivery, chỉ dùng thư viện chuẩn và dữ liệu được giao."""

from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path


def delivery_file(delivery: Path, relative: str) -> Path:
    path = (delivery / relative).resolve()
    if not path.is_relative_to(delivery):
        raise ValueError(f"Đường dẫn vượt ra ngoài delivery: {relative}")
    return path


def trace(delivery: Path, class_name: str | None = None,
          old_guideline: str | None = None,
          reported_scenes: list[str] | None = None) -> dict:
    delivery = delivery.resolve()
    ticket = (delivery / "incoming/ticket.md").read_text(encoding="utf-8-sig")
    changelog = (delivery / "guideline/changelog.md").read_text(encoding="utf-8-sig")
    classes = {}
    for line in (delivery / "classes.txt").read_text(encoding="utf-8-sig").splitlines():
        if not line.strip():
            continue
        number, name = line.split(maxsplit=1)
        classes[name.strip()] = int(number)

    if class_name is None:
        mentioned = set(re.findall(r"`([^`]+)`", ticket))
        changed = set(re.findall(r"Lớp\s+`([^`]+)`", changelog))
        matches = mentioned & changed & classes.keys()
        if len(matches) != 1:
            raise ValueError("Không xác định duy nhất lớp đổi quy tắc. Chỉ định --class-name sau khi đọc ticket/changelog.")
        class_name = matches.pop()
    if class_name not in classes:
        raise ValueError(f"Lớp không có trong classes.txt: {class_name}")

    if old_guideline is None:
        changes = re.findall(r"Lớp\s+`" + re.escape(class_name) + r"`[^\n]*", changelog)
        versions = set(re.findall(r"\((v\d+(?:\.\d+)+)\s", "\n".join(changes)))
        if len(versions) != 1:
            raise ValueError("Không xác định duy nhất guideline cũ. Chỉ định --old-guideline sau khi đọc changelog.")
        old_guideline = versions.pop()
    scenes = set(reported_scenes) if reported_scenes is not None else set(re.findall(r"\bscene_[A-Za-z0-9]+\b", ticket))
    if not scenes:
        raise ValueError("Ticket không có scene_id để truy vết.")

    with (delivery / "jobs.csv").open(encoding="utf-8-sig", newline="") as handle:
        jobs = {row["job_id"]: row for row in csv.DictReader(handle)}
    if old_guideline not in {job["guideline"] for job in jobs.values()}:
        raise ValueError(f"Không có job dùng guideline {old_guideline}.")
    metadata = json.loads((delivery / "metadata.json").read_text(encoding="utf-8-sig"))["items"]
    manifest = json.loads((delivery / "manifest.json").read_text(encoding="utf-8-sig"))["items"]
    tiers = {"tier_a": set(), "tier_b": set()}
    notify = set()
    for item in metadata:
        job = jobs[item["job_id"]]
        if job["guideline"] != old_guideline:
            continue
        image = item["image"]
        label = delivery_file(delivery, manifest[image]["label"])
        has_class = False
        for number, line in enumerate(label.read_text(encoding="utf-8-sig").splitlines(), 1):
            if not line.strip():
                continue
            fields = line.split()
            if len(fields) != 5:
                raise ValueError(f"Nhãn YOLO sai cấu trúc: {label.name}, dòng {number}")
            has_class |= int(fields[0]) == classes[class_name]
        if has_class:
            tier = "tier_a" if item["scene_id"] in scenes else "tier_b"
            tiers[tier].add(image)
            notify.update((job["annotator"], job["reviewer"]))
    return {**{key: sorted(value) for key, value in tiers.items()}, "notify": sorted(notify)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("delivery", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--class-name", "--class", dest="class_name", help="Lớp trong ticket, dùng khi văn bản không theo mẫu lab")
    parser.add_argument("--old-guideline", "--old", dest="old_guideline", help="Guideline cũ, ví dụ v1.2")
    parser.add_argument("--scenes", nargs="*", help="Các scene được báo, mặc định đọc từ ticket")
    args = parser.parse_args()
    try:
        if args.out.resolve().is_relative_to(args.delivery.resolve()):
            raise ValueError("File kết quả phải nằm ngoài delivery.")
        result = trace(args.delivery, args.class_name, args.old_guideline, args.scenes)
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    except (OSError, ValueError, KeyError) as error:
        parser.exit(1, f"Không tạo được trace.json: {error}\n")
    print(f"Đã ghi {args.out}")
    for key, values in result.items():
        print(f"{key} = {len(values)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
