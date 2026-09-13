import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.csv as pacsv

from benchmark_common import run_benchmark


def process(path):
    count = total = 0
    with pacsv.open_csv(
        path,
        read_options=pacsv.ReadOptions(block_size=1_000_000),
        parse_options=pacsv.ParseOptions(newlines_in_values=True),
        convert_options=pacsv.ConvertOptions(
            include_columns=["amount_pence"],
            column_types={"amount_pence": pa.int64()},
        ),
    ) as batches:
        for batch in batches:
            count += batch.num_rows
            total += pc.sum(batch.column(0)).as_py()
    return count, total


if __name__ == "__main__":
    run_benchmark("arrow", process)
