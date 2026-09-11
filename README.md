# How to read and process files bigger than RAM in Python

Compare chunked reading and memory mapping with a generated binary sales file. The examples sum every record in the file, then compare `seek` and `mmap` for 50,000 individual lookups.

Chunked reading streams blocks through a small input buffer. Memory mapping lets the operating system load file pages as they're accessed. Both examples keep a running total instead of collecting all the records in memory.

## Setup

You'll need Git, uv, and 64-bit Python 3.14 or later. The commands below work in PowerShell. Allow at least 40 GB of free disk space for the example data, plus space for the project and Python environment.

```powershell
git clone https://github.com/taupirho/large-file-tests.git
cd large-file-tests
uv sync
cd src
```

Run the remaining commands from `src`. The generator writes `sales.bin` into the current directory, while the benchmark scripts look for it beside their source files.

## Create the data

```powershell
uv run python create_data.py 40
```

This creates a 40 GB file. Here, 1 GB means 1,000,000,000 bytes. You can supply another positive whole number, such as `1` for a smaller trial.

The generator refuses to overwrite an existing `sales.bin`. Move or delete an unwanted data file yourself before generating a replacement. Git ignores `sales.bin`, so the data isn't included in this repository.

To check total and currently available RAM in decimal GB:

```powershell
uv run python -c "import psutil; m = psutil.virtual_memory(); print(f'Total physical RAM: {m.total / 1_000_000_000:.2f} GB'); print(f'Available now: {m.available / 1_000_000_000:.2f} GB')"
```

A 40 GB file isn't necessarily larger than your machine's RAM. Choose the file size to suit the comparison you want to make, and distinguish installed RAM from memory available at the time of the test.

## Process the entire file

```powershell
uv run python read_chunks.py
uv run python read_mmap.py
```

`read_chunks.py` reads 262,144 records per block. `read_mmap.py` creates a read-only mapping of the whole file and unpacks records directly from it. Mapping the file doesn't load all of it into physical RAM at once.

Both scripts report elapsed time, throughput, and the total amount in pence. For a 40 GB file, each should print:

```text
Total pence: 6,249,375,000,000
```

The scripts calculate the expected total from the file size and check it with an assertion. Run Python without `-O`, which disables these checks.

The current scripts print throughput in MiB/s. If you want decimal GB/s, replace the throughput print statement in each reader with:

```python
print(f"Throughput: {size / 1_000_000_000 / elapsed:.3f} GB/s")
```

To experiment with smaller chunks, change `32 * 262_144` to `32 * 32_768` in `read_chunks.py`. Keep the file and calculation unchanged when comparing results.

## Retrieve individual records

```powershell
uv run python random_access.py seek
uv run python random_access.py mmap
```

The seek test uses buffered file reads. The mmap test unpacks each record at its byte offset in the mapping.

Both use `Random(42)` to select 50,000 positions, with possible repeats. For a given file size, they use the same positions and should produce the same total. Changing the file size changes the positions, but the lookup count stays at 50,000.

For the 40 GB file, the expected lookup total is:

```text
Total pence: 249,146,201
```

Position generation and expected-total calculation happen before the timer starts. The timed section includes opening and closing the file, performing the lookups, and creating and closing the mapping for the mmap test.

## Read the timings carefully

These tests measure reading and Python record processing together. Similar full-scan timings don't establish that the two access methods have identical overhead.

The operating system caches file data in RAM. Creating the file or running a benchmark can leave data cached for later runs. Reversing the test order doesn't clear that cache. Repeat both tests in alternating order and compare median times, but don't describe those results as uncached disk performance.

The 50,000 lookups touch only part of the file. That data can fit in RAM even when the whole file doesn't. This test therefore doesn't establish random-access performance for a working set larger than RAM. An uncached mmap access still has to fetch data from storage.

Don't modify or truncate `sales.bin` while a benchmark is running. If you adapt the examples, keep intermediate results bounded too. Collecting every decoded record in a list would defeat the memory-saving approach.

## Data format and extra validation

Each record occupies 32 bytes and uses the struct format `<QQ16x`:

- An unsigned 64-bit little-endian row number.
- An unsigned 64-bit little-endian amount in pence.
- 16 padding bytes.

The file repeats a batch of 10,000 records. Row numbers restart at zero in each batch, so they aren't unique across the file. Amounts follow `(row * 37) % 10_000`, covering every integer from zero to 9,999 once per batch. Each batch totals 49,995,000 pence.

A 40 GB file contains 125,000 batches and 1,250,000,000 records. For an additional full scan that checks both the record count and total, run:

```powershell
uv run python sizes.py
```

Unlike the other readers, `sizes.py` specifically expects a 40 GB file.
