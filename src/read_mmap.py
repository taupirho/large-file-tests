import mmap
from pathlib import Path
from struct import Struct
from time import perf_counter

path = Path(__file__).resolve().parent / "sales.bin"
record = Struct("<QQ16x")
size = path.stat().st_size
if size == 0 or size % (10_000 * record.size):
    raise ValueError("Expected complete batches from create_data.rs")
expected = (size // (10_000 * record.size)) * 49_995_000
start = perf_counter()
with path.open("rb") as file:
    with mmap.mmap(file.fileno(), 0, access=mmap.ACCESS_READ) as mapped:
        total = sum(amount for _, amount in record.iter_unpack(mapped))
elapsed = perf_counter() - start
assert total == expected, "Incorrect sales total"
print(f"Memory map: {elapsed:.3f} seconds")
print(f"Throughput: {size / 2**20 / elapsed:.1f} MiB/s")
print(f"Total pence: {total:,}")