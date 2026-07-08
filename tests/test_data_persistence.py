import json
import tempfile
import unittest
from pathlib import Path

from src.module.data_persistence import load_marked_dates, save_marked_dates


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


if __name__ == "__main__":
    unittest.main()
