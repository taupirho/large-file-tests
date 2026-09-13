import polars as pl

from benchmark_common import run_benchmark


def process(path):
    result = (
        pl.scan_csv(
            path,
            schema={
                "sale_id": pl.Int64,
                "amount_pence": pl.Int64,
                "note": pl.String,
            },
        )
        .select(
            pl.len().alias("rows"),
            pl.col("amount_pence").sum().alias("total"),
        )
        .collect(engine="streaming")
    )
    return result.row(0)


if __name__ == "__main__":
    run_benchmark("polars", process)
