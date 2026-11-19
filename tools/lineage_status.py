"""Đọc trạng thái QC/lineage và in lệnh cần chạy sau khi nhóm chốt bài."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", required=True, type=Path)
    args = parser.parse_args()
    run = args.run.resolve()
    try:
        delivery = run / "delivery"
        release_id = json.loads((delivery / "release.json").read_text(encoding="utf-8"))["release_id"]
        manifest = json.loads((delivery / "manifest.json").read_text(encoding="utf-8"))["items"]
        log = run.parent / "lineage.jsonl"
        events = [json.loads(line) for line in log.read_text(encoding="utf-8").splitlines() if line.strip()] if log.exists() else []
        print(f"Release v1 = {release_id}")
        print(f"Số ảnh = {len(manifest)}")
        print(f"Lineage = {log}")
        trains = [event["run_id"] for event in events if event.get("event") == "train" and event.get("release_id") == release_id]
        print(f"Training run liên quan = {', '.join(trains) or 'chưa ghi nhận'}")
        decisions = [event.get("decision") for event in events if event.get("event") == "decision" and event.get("release_id") == release_id]
        print(f"Các quyết định đã ghi = {', '.join(decisions) or 'chưa có'}")
        errors_path = run / "errors.json"
        if errors_path.is_file():
            errors = json.loads(errors_path.read_text(encoding="utf-8"))["errors"]
            pairs = {(error["type"], error["target"]) for error in errors}
            if len(pairs) != len(errors):
                raise ValueError("errors.json có cặp type/target trùng, cần nhóm chốt lại.")
            rate = len(errors) / len(manifest)
            decision = "HOLD" if rate > 0.02 else "RELEASE"
            print(f"QC theo errors.json hiện tại = {len(errors)}/{len(manifest)} = {rate:.2%}")
            print("Sau khi nhóm xác nhận errors.json đã đầy đủ, ghi quyết định bằng lệnh")
            print(f'python scripts/lineage.py --root "{run.parent}" record --event decision --release-id {release_id} --decision {decision}')
        else:
            print("ĐANG CHỜ errors.json đã chốt để tính QC và ghi quyết định v1.")
        print("Kiểm tra ảnh hưởng của quyết định đã ghi bằng lệnh")
        print(f'python scripts/lineage.py --root "{run.parent}" impact --release-id {release_id}')
        v2 = run / "handover" / f"{release_id}_v2"
        if not v2.is_dir():
            print("ĐANG CHỜ thư mục handover v2 từ người phụ trách bàn giao.")
        print("Sau khi v2 hoàn thiện và đã đóng gói, ghi quan hệ cha–con bằng lệnh")
        print(f'python scripts/lineage.py --root "{run.parent}" record --event release --release-id {release_id}_v2 --parent {release_id}')
    except (OSError, ValueError, KeyError, ZeroDivisionError) as error:
        parser.exit(1, f"Không đọc được trạng thái lineage: {error}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
