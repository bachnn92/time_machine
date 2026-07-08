import json
import tempfile
import unittest
from pathlib import Path

from src.module.data_persistence import (
    clear_marked_cell,
    load_marked_dates,
    load_marked_dates_into,
    save_marked_dates,
    set_marked_cell_level,
    summarize_commit_schedule,
)


class DataPersistenceCoordinateTests(unittest.TestCase):
    def test_load_marked_dates_uses_matrix_grid_order(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "data.json"
            path.write_text(
                '[{"cordinate": "[1, 2]", "date": "2026-01-04T00:00:00", "level": 4}]',
                encoding="utf-8",
            )

            marked = load_marked_dates(str(path))

            self.assertEqual(marked[(1, 0)], 4)

    def test_save_marked_dates_writes_matrix_grid_coordinates(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "data.json"

            save_marked_dates({(1, 0): 4}, 2026, str(path))
            data = json.loads(path.read_text(encoding="utf-8"))

            self.assertEqual(data[0]["cordinate"], "[1, 2]")

    def test_summarize_commit_schedule_counts_entries_and_total_commits(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "data.json"
            path.write_text(
                '[{"cordinate": "[1, 2]", "date": "2026-01-04T00:00:00", "level": 3}, {"cordinate": "[2, 3]", "date": "2026-01-05T00:00:00", "level": 2}]',
                encoding="utf-8",
            )

            self.assertEqual(summarize_commit_schedule(str(path)), (2, 5))

    def test_set_marked_cell_level_persists_immediately(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "data.json"
            marked = {}

            set_marked_cell_level(marked, (1, 0), 3, 2026, str(path))

            saved_data = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(saved_data[0]["level"], 3)
            self.assertEqual(marked[(1, 0)], 3)

    def test_clear_marked_cell_persists_immediately(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "data.json"
            marked = {(1, 0): 3}

            clear_marked_cell(marked, (1, 0), 2026, str(path))

            self.assertEqual(json.loads(path.read_text(encoding="utf-8")), [])
            self.assertNotIn((1, 0), marked)

    def test_load_marked_dates_into_persists_to_target_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            source_path = Path(tmpdir) / "template.json"
            target_path = Path(tmpdir) / "data.json"
            source_path.write_text(
                '[{"cordinate": "[1, 2]", "date": "2026-01-04T00:00:00", "level": 4}]',
                encoding="utf-8",
            )

            marked = {}
            load_marked_dates_into(marked, str(source_path), 2026, str(target_path))

            self.assertEqual(marked[(1, 0)], 4)
            self.assertEqual(json.loads(target_path.read_text(encoding="utf-8"))[0]["cordinate"], "[1, 2]")


if __name__ == "__main__":
    unittest.main()
