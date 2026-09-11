import argparse
import mmap
from pathlib import Path
from random import Random
from struct import Struct
from time import perf_counter

parser = argparse.ArgumentParser()
parser.add_argument("method", choices=["seek", "mmap"])
args = parser.parse_args()
path = Path(__file__).resolve().parent / "sales.bin"
record = Struct("<QQ16x")
size = path.stat().st_size
if size == 0 or size % (10_000 * record.size):
    raise ValueError("Expected complete batches from create_data.rs")
rows = size // record.size
rng = Random(42)
positions = [rng.randrange(rows) for _ in range(50_000)]
expected = sum((position * 37) % 10_000 for position in positions)
if args.method == "seek":
    start = perf_counter()
    total = 0
    with path.open("rb") as file:
        for position in positions:
            file.seek(position * record.size)
            _, amount = record.unpack(file.read(record.size))
            total += amount
    elapsed = perf_counter() - start
else:
    start = perf_counter()
    total = 0
    with path.open("rb") as file:
        with mmap.mmap(file.fileno(), 0, access=mmap.ACCESS_READ) as mapped:
            for position in positions:
                _, amount = record.unpack_from(mapped, position * record.size)
                total += amount
    elapsed = perf_counter() - start
assert total == expected, "Incorrect lookup total"
print(f"{args.method}: {elapsed:.3f} seconds for {len(positions):,} lookups")
print(f"Total pence: {total:,}")