import os
import struct
import sys
from time import perf_counter


def main():
    if len(sys.argv) != 2:
        raise ValueError(
            "Usage: python create_data.py <whole GB>, "
            "for example: python create_data.py 80"
        )

    gb = int(sys.argv[1])

    if gb < 1:
        raise ValueError("Size must be at least 1 GB")

    total_bytes = gb * 1_000_000_000

    if total_bytes > (1 << 64) - 1:
        raise ValueError("Requested size is too large")

    # 10,000 records, each with two little-endian u64s
    # and 16 zero-filled padding bytes.
    block = bytearray(10_000 * 32)

    for row in range(10_000):
        offset = row * 32
        amount = (row * 37) % 10_000
        struct.pack_into("<QQ", block, offset, row, amount)

    print(
        f"Creating sales.bin: {gb} GB ({total_bytes} bytes)",
        flush=True,
    )

    # "xb" creates a new binary file and fails if it already exists.
    with open("sales.bin", "xb") as file:
        start = perf_counter()

        # A whole decimal GB contains exactly 3,125 complete blocks.
        blocks = total_bytes // len(block)

        for index in range(blocks):
            file.write(block)

            if (index + 1) % 3_125 == 0:
                print(
                    f"Written {(index + 1) // 3_125} GB",
                    flush=True,
                )

        # Flush Python's buffer, then sync the file to disk.
        file.flush()
        os.fsync(file.fileno())

        print(f"Finished in {perf_counter() - start:.2f} seconds")


if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError) as error:
        print(f"Error: {error}", file=sys.stderr)
        sys.exit(1)