from benchmark_common import add_rows, run_benchmark


def process(path):
    with path.open(encoding="utf-8", newline="") as file:
        return add_rows(file)


if __name__ == "__main__":
    run_benchmark("csv", process)
