import contextlib
import csv
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from create_csv import create_file, make_batch
from benchmark_common import run_benchmark
from read_stream import process as stream
from read_mmap import process as mapped


class CsvTests(unittest.TestCase):
    def test_small_generated_file_all_methods(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "sales.csv"
            with contextlib.redirect_stdout(io.StringIO()):
                expected = create_file(path, 1_000_000)
                self.assertEqual(path.stat().st_size, 1_000_000)
                for process in (stream, mapped):
                    with self.subTest(method=process.__module__):
                        self.assertEqual(
                            process(path),
                            (expected["rows"], expected["total_pence"]),
                        )
            with self.assertRaises(FileExistsError):
                create_file(path, 1_000_000)

    def test_batch_contents(self):
        rows = list(csv.reader(io.StringIO(make_batch().decode("utf-8"),
                                           newline="")))
        self.assertEqual(len(rows), 10_000)
        self.assertEqual(sum(int(row[1]) for row in rows), 49_995_000)
        self.assertTrue(any("\n" in row[2] for row in rows))
        self.assertTrue(any("," in row[2] for row in rows))
        self.assertTrue(any('"' in row[2] for row in rows))
        self.assertTrue(any("Caf\u00e9" == row[2] for row in rows))
        self.assertGreater(len({len(row[0]) + len(row[1]) + len(row[2])
                                for row in rows}), 1)

    def test_wrong_total_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "sales.csv"
            with contextlib.redirect_stdout(io.StringIO()):
                metadata = create_file(path, 1_000_000)
            metadata["total_pence"] += 1
            path.with_suffix(".meta.json").write_text(
                json.dumps(metadata), encoding="utf-8")
            for process in (stream, mapped):
                with self.subTest(method=process.__module__), patch(
                    "sys.argv", ["test", "--path", str(path)]
                ):
                    with self.assertRaises(ValueError):
                        run_benchmark("test", process)

    def test_truncation_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "sales.csv"
            with contextlib.redirect_stdout(io.StringIO()):
                create_file(path, 1_000_000)
            with path.open("r+b") as file:
                file.truncate(999_999)
            with patch("sys.argv", ["test", "--path", str(path)]):
                with self.assertRaises(ValueError):
                    run_benchmark("test", stream)


if __name__ == "__main__":
    unittest.main()
