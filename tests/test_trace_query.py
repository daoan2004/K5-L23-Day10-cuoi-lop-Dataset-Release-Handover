"""Kiểm tra truy vết bằng dữ liệu tổng hợp, không dùng đáp án của lab."""

import json
import tempfile
import unittest
from pathlib import Path

from tools.trace_query import trace


class TraceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.delivery = Path(self.temp.name)
        for folder in ("incoming", "guideline", "labels"):
            (self.delivery / folder).mkdir()
        self.write("incoming/ticket.md", "Bỏ sót `cup` ở scene_one.")
        self.write("guideline/changelog.md", "## v1.3\n- Lớp `cup`: vẫn gán box (v1.2 cho phép bỏ qua).\n")
        self.write("classes.txt", "0 person\n1 cup\n")
        self.write("jobs.csv", "job_id,annotator,reviewer,guideline\nJ1,A1,Q1,v1.2\nJ2,A2,Q2,v1.3\n")
        items = [
            {"image": "a", "scene_id": "scene_one", "job_id": "J1", "guideline_version": "v1.3"},
            {"image": "b", "scene_id": "scene_other", "job_id": "J1", "guideline_version": "v1.2"},
            {"image": "c", "scene_id": "scene_one", "job_id": "J2", "guideline_version": "v1.2"},
            {"image": "d", "scene_id": "scene_one", "job_id": "J1", "guideline_version": "v1.2"},
        ]
        self.write("metadata.json", json.dumps({"items": items}))
        self.write("manifest.json", json.dumps({"items": {item["image"]: {"label": f"labels/{item['image']}.txt"} for item in items}}))
        for image in "abc":
            self.write(f"labels/{image}.txt", "1 0.5 0.5 0.2 0.2\n1 0.6 0.6 0.1 0.1\n")
        self.write("labels/d.txt", "0 0.5 0.5 0.2 0.2\n")

    def write(self, path, value):
        (self.delivery / path).write_text(value, encoding="utf-8")

    def test_tiers_use_job_guideline_and_detection_class(self):
        self.assertEqual(trace(self.delivery), {"tier_a": ["a"], "tier_b": ["b"], "notify": ["A1", "Q1"]})

    def test_missing_label_fails_instead_of_omitting_image(self):
        (self.delivery / "labels/b.txt").unlink()
        with self.assertRaises(FileNotFoundError):
            trace(self.delivery)

    def test_explicit_scenes_override_ticket(self):
        result = trace(self.delivery, reported_scenes=["scene_other"])
        self.assertEqual(result["tier_a"], ["b"])
        self.assertEqual(result["tier_b"], ["a"])

    def test_unrecognised_changelog_requires_explicit_version(self):
        self.write("guideline/changelog.md", "Lớp `cup` đổi quy tắc.\n")
        with self.assertRaises(ValueError):
            trace(self.delivery)
        self.assertEqual(trace(self.delivery, old_guideline="v1.2")["tier_a"], ["a"])

    def test_manifest_path_cannot_leave_delivery(self):
        manifest = json.loads((self.delivery / "manifest.json").read_text())
        manifest["items"]["a"]["label"] = "../outside.txt"
        self.write("manifest.json", json.dumps(manifest))
        with self.assertRaises(ValueError):
            trace(self.delivery)


if __name__ == "__main__":
    unittest.main()
