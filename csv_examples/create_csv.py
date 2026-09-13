import argparse
import csv
import io
import json
import os
from decimal import Decimal
from pathlib import Path
from time import perf_counter

HEADER = b"sale_id,amount_pence,note\n"
BATCH_ROWS = 10_000
BATCH_TOTAL = 49_995_000


def make_batch():
    text = io.StringIO(newline="")
    writer = csv.writer(text, lineterminator="\n")
    notes = ["Online", "Shop, London", 'Customer said "thanks"',
             "Delivery\nleave by door", "Caf\u00e9"]
    for row in range(BATCH_ROWS):
        writer.writerow([row, (row * 37) % 10_000,
                         notes[row % len(notes)]])
    return text.getvalue().encode("utf-8")


def create_file(path, target):
    batch = make_batch()
    footer_prefix = b"0,0,"
    footer_minimum = len(footer_prefix) + 1
    if target < len(HEADER) + len(batch) + footer_minimum:
        raise ValueError("Choose a size large enough for one complete batch")

    batches = (target - len(HEADER) - footer_minimum) // len(batch)
    padding = target - len(HEADER) - batches * len(batch) - footer_minimum
    metadata_path = path.with_suffix(".meta.json")
    if path.exists() or metadata_path.exists():
        raise FileExistsError("Data or metadata already exists; choose another path")

    started = perf_counter()
    with path.open("xb") as file:
        file.write(HEADER)
        next_report = 1_000_000_000
        for index in range(batches):
            file.write(batch)
            written = len(HEADER) + (index + 1) * len(batch)
            if written >= next_report:
                print(f"Written {written / 1_000_000_000:.2f} GB", flush=True)
                next_report += 1_000_000_000
        file.write(footer_prefix + b"x" * padding + b"\n")
        file.flush()
        os.fsync(file.fileno())

    if path.stat().st_size != target:
        raise RuntimeError("Unexpected output size")
    metadata = {
        "bytes": target,
        "rows": batches * BATCH_ROWS + 1,
        "total_pence": batches * BATCH_TOTAL,
    }
    with metadata_path.open("x", encoding="utf-8") as file:
        json.dump(metadata, file, indent=2)
    print(f"Created {target / 1_000_000_000:.3f} GB in "
          f"{perf_counter() - started:.2f} seconds")
    print(json.dumps(metadata, indent=2))
    return metadata


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("gb", type=Decimal)
    parser.add_argument("--path", type=Path,
                        default=Path(__file__).with_name("sales.csv"))
    args = parser.parse_args()
    byte_count = args.gb * 1_000_000_000
    if not byte_count.is_finite() or byte_count <= 0:
        parser.error("Size must be a positive finite number of GB")
    if byte_count != byte_count.to_integral_value():
        parser.error("Size must represent a whole number of bytes")
    create_file(args.path, int(byte_count))
