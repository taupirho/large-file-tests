import pandas as pd

from benchmark_common import run_benchmark


def process(path):
    count = total = 0
    with pd.read_csv(
        path,
        engine="c",
        usecols=["amount_pence"],
        dtype={"amount_pence": "int64"},
        chunksize=100_000,
    ) as chunks:
        for chunk in chunks:
            count += len(chunk)
            total += int(chunk["amount_pence"].sum())
    return count, total


if __name__ == "__main__":
    run_benchmark("pandas", process)
