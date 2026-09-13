import contextlib
import io
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from create_csv import create_file


SCRIPTS = (
    "read_stream.py", "read_mmap.py", "read_pandas.py",
    "read_pyarrow.py", "read_polars.py", "read_duckdb.py",
)
DIRECTORY = Path(__file__).resolve().parent


class SeparateMethodsTests(unittest.TestCase):
    def test_each_cli_and_validation(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "trial.csv"
            with contextlib.redirect_stdout(io.StringIO()):
                expected = create_file(path, 1_000_000)
            for script in SCRIPTS:
                with self.subTest(script=script):
                    result = subprocess.run(
                        [sys.executable, str(DIRECTORY / script),
                         "--path", str(path)],
                        cwd=directory, capture_output=True, text=True,
                        timeout=60,
                    )
                    self.assertEqual(result.returncode, 0, result.stderr)
                    self.assertIn(f"Rows: {expected['rows']:,}", result.stdout)
                    self.assertIn(
                        f"Total pence: {expected['total_pence']:,}", result.stdout
                    )
                    self.assertIn("GB/s", result.stdout)
                    for label in (
                        "RAM before processing", "Sampled peak RAM",
                        "Peak increase over baseline",
                    ):
                        self.assertRegex(
                            result.stdout, rf"{label}: [0-9]+\.[0-9]{{3}} GB"
                        )

            expected["total_pence"] += 1
            path.with_suffix(".meta.json").write_text(
                json.dumps(expected), encoding="utf-8"
            )
            for script in SCRIPTS:
                with self.subTest(wrong_total=script):
                    result = subprocess.run(
                        [sys.executable, str(DIRECTORY / script),
                         "--path", str(path)],
                        cwd=directory, capture_output=True, text=True,
                        timeout=60,
                    )
                    self.assertNotEqual(result.returncode, 0)
                    self.assertIn("Incorrect row count or total", result.stderr)


if __name__ == "__main__":
    unittest.main()
