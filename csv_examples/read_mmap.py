import mmap
import struct

from benchmark_common import add_rows, run_benchmark


def process(path):
    if struct.calcsize("P") < 8:
        raise RuntimeError("Use 64-bit Python for the large mapping")
    with path.open("rb") as file:
        with mmap.mmap(file.fileno(), 0, access=mmap.ACCESS_READ) as data:
            lines = (line.decode("utf-8")
                     for line in iter(data.readline, b""))
            return add_rows(lines)


if __name__ == "__main__":
    run_benchmark("mmap", process)
