import os
import struct
from time import perf_counter

FILE_PATH = "sales.bin"
RECORD_SIZE = 32
BLOCK_SIZE = 10_000 * RECORD_SIZE
CHUNK_SIZE = 100 * BLOCK_SIZE  # 32 MB

file_size = os.path.getsize(FILE_PATH)

assert file_size == 40_000_000_000, (
    f"Expected a 40 GB file, found {file_size:,} bytes"
)

# Independently calculate the expected sum for one block.
expected_block_total = sum(
    (row * 37) % 10_000
    for row in range(10_000)
)
assert expected_block_total == 49_995_000

expected_total = expected_block_total * (file_size // BLOCK_SIZE)
expected_records = file_size // RECORD_SIZE

actual_total = 0
actual_records = 0
start = perf_counter()

# < = little-endian; QQ = two unsigned 64-bit integers;
# 16x = skip the 16 padding bytes.
record = struct.Struct("<QQ16x")

with open(FILE_PATH, "rb") as file:
    while chunk := file.read(CHUNK_SIZE):
        if len(chunk) % RECORD_SIZE:
            raise ValueError("File contains an incomplete record")

        for sale_id, amount in record.iter_unpack(chunk):
            actual_total += amount
            actual_records += 1

elapsed = perf_counter() - start

print(f"Total per block: {expected_block_total:,} pence")
print(f"Records read:   {actual_records:,}")
print(f"Expected total: {expected_total:,} pence")
print(f"Actual total:   {actual_total:,} pence")
print(f"Time taken:     {elapsed:.2f} seconds")

assert actual_records == expected_records, "Record count mismatch"
assert actual_total == expected_total, "Amount total mismatch"

print("PASS: record count and total match.")