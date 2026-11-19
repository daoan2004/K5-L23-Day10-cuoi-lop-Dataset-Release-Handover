"""Doi chieu detection <-> panoptic, sinh ung vien loi gan nhan.

Ung vien: class_swap, category_swap, bbox_drift, missing_box, instance_merge.
Chi dung thu vien chuan. Chi doc thu muc delivery, khong doc _private/.
"""
import json, os


def load_panoptic(delivery):
    with open(os.path.join(delivery, "panoptic.json"), encoding="utf-8") as f:
        return json.load(f)


def find_candidates(delivery):
    """Tra ve list dict: {"image": ..., "type": ..., "detail": ...}."""
    candidates = []
    # TODO: ghep box detection voi segment panoptic, sinh ung vien
    return candidates