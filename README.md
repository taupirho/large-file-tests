# Six ways to process a CSV larger than RAM in Python

Compare six methods for counting records and summing sales amounts in a 40 GB CSV. Each benchmark runs separately and reports elapsed time, throughput, and sampled process RAM.

## Setup

Use 64-bit Python 3.14 or later and uv:

```powershell
git clone https://github.com/taupirho/large-file-tests.git
cd large-file-tests
uv sync
```

Run the commands below from the repository root. The scripts find their default data file beside themselves.

## Create the CSV

Start with a small trial:

```powershell
uv run python csv_examples/create_csv.py 0.001 --path csv_examples/trial.csv
uv run python csv_examples/read_stream.py --path csv_examples/trial.csv
```

Create the full input when you have at least 40 GB of free disk space, plus room for the environment:

```powershell
uv run python csv_examples/create_csv.py 40
```

This writes exactly 40,000,000,000 bytes to `csv_examples/sales.csv`, plus expected counts in `sales.meta.json`. Existing data and metadata aren't overwritten. An interrupted generation can leave a partial CSV; move or remove that file yourself before retrying.

Generated data and metadata are ignored by Git. All reported GB values use decimal units: 1 GB = 1,000,000,000 bytes.

## What the file contains

The UTF-8 CSV has three columns:

- `sale_id`: a row identifier, repeated from zero to 9,999 in each batch.
- `amount_pence`: integer amounts from zero to 9,999.
- `note`: variable-length text, including quoted commas, quotation marks, accented characters, and embedded line breaks.

A batch of 10,000 records repeats throughout the file. A final zero-value row pads the file to its requested size. Identifiers aren't globally unique.

For the generated 40 GB CSV, all six methods should return:

```text
Rows: 1,551,710,001
Total pence: 7,757,774,145,000
```

## Run the six benchmarks

| Script | Method |
|---|---|
| `csv_examples/read_stream.py` | Standard-library CSV parsing with a Python row loop. |
| `csv_examples/read_mmap.py` | Read-only memory mapping with the same CSV parser. |
| `csv_examples/read_pandas.py` | DataFrame chunks of up to 100,000 rows. |
| `csv_examples/read_pyarrow.py` | Incremental Arrow record batches and column sums. |
| `csv_examples/read_polars.py` | A lazy aggregation executed with the streaming engine. |
| `csv_examples/read_duckdb.py` | A SQL aggregation directly over the CSV. |

```powershell
uv run python csv_examples/read_stream.py
uv run python csv_examples/read_mmap.py
uv run python csv_examples/read_pandas.py
uv run python csv_examples/read_pyarrow.py
uv run python csv_examples/read_polars.py
uv run python csv_examples/read_duckdb.py
```

Every script accepts `--path` for another generated CSV. Keep its matching `.meta.json` beside it. For example:

```powershell
uv run python csv_examples/read_polars.py --path csv_examples/trial.csv
```

Don't modify or truncate the CSV during a benchmark. The mmap adapter is designed for the generator's UTF-8 encoding and LF line endings.

## Reading the statistics

The shared `benchmark_common.py` helper validates file size, row count, and amount total. It prints:

- Elapsed seconds and throughput in GB/s.
- Process RAM before processing.
- Sampled peak process RAM.
- Peak increase over the baseline.

RAM means resident process memory, not the RAM available across your computer. Sampling targets a 50-millisecond interval and can miss short peaks. It includes resident library and mapped-file pages, but not the whole operating-system file cache. Three-decimal-place rounding can display a small increase as 0.000 GB.

Imports and metadata loading are outside the timer. Reader setup, parsing, aggregation, and resource cleanup are inside it. Sampling adds some overhead.

Repeat runs in different orders and compare median times. Earlier reads and file generation can warm the operating-system cache. These are processing benchmarks, not isolated disk-speed measurements. The analytical libraries can avoid retaining unused columns; the standard-library parser creates each row's fields.

The examples retain only a small result. Collecting every row, concatenating all chunks, or performing a different query can have very different memory requirements.

## Tests

```powershell
uv run python -m unittest discover -s csv_examples -v
```

Tests use temporary small CSVs, exercise all six command-line scripts, verify totals and RAM output, and check error handling. They don't generate or scan the 40 GB file.

The previous binary-file benchmarks remain available in Git history.
