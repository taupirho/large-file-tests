import argparse
import csv
import json
from pathlib import Path
from threading import Event, Thread
from time import perf_counter

import psutil


class MemorySampler:
    """Sample this process's resident memory, not its virtual mapping size."""

    def __init__(self, interval=0.05):
        self.interval = interval
        self.process = psutil.Process()
        self.stop = Event()
        self.error = None

    def __enter__(self):
        self.baseline = self.process.memory_info().rss
        self.peak = self.baseline
        self.thread = Thread(target=self._sample, daemon=True)
        self.thread.start()
        return self

    def _sample(self):
        try:
            while not self.stop.wait(self.interval):
                self.peak = max(self.peak, self.process.memory_info().rss)
        except psutil.Error as error:
            self.error = error

    def __exit__(self, exc_type, exc_value, traceback):
        self.stop.set()
        self.thread.join()
        if exc_type is None:
            if self.error is not None:
                raise RuntimeError("RAM sampling failed") from self.error
            self.peak = max(self.peak, self.process.memory_info().rss)


def add_rows(lines):
    csv.field_size_limit(1_000_000)
    reader = csv.reader(lines, strict=True)
    if next(reader, None) != ["sale_id", "amount_pence", "note"]:
        raise ValueError("Unexpected header")
    count = total = 0
    for sale_id, amount, note in reader:
        count += 1
        total += int(amount)
    return count, total


def run_benchmark(method, process):
    parser = argparse.ArgumentParser(description=f"CSV benchmark: {method}")
    parser.add_argument(
        "--path", type=Path,
        default=Path(__file__).with_name("sales.csv"),
    )
    args = parser.parse_args()
    path = args.path
    expected = json.loads(
        path.with_suffix(".meta.json").read_text(encoding="utf-8")
    )
    size = path.stat().st_size
    if size != expected["bytes"]:
        raise ValueError("Unexpected file size")

    with MemorySampler() as memory:
        start = perf_counter()
        count, total = process(path)
        elapsed = perf_counter() - start

    if (count, total) != (expected["rows"], expected["total_pence"]):
        raise ValueError("Incorrect row count or total")

    print(f"{method}: {elapsed:.3f} seconds")
    print(f"Throughput: {size / 1_000_000_000 / elapsed:.3f} GB/s")
    print(f"RAM before processing: {memory.baseline / 1_000_000_000:.3f} GB")
    print(f"Sampled peak RAM: {memory.peak / 1_000_000_000:.3f} GB")
    print(f"Peak increase over baseline: "
          f"{(memory.peak - memory.baseline) / 1_000_000_000:.3f} GB")
    print(f"Rows: {count:,}")
    print(f"Total pence: {total:,}")
