import duckdb

from benchmark_common import run_benchmark


def process(path):
    with duckdb.connect() as connection:
        return connection.execute("""
            SELECT count(*), sum(amount_pence)
            FROM read_csv(
                ?, header=true, auto_detect=false,
                delim=',', quote='"', escape='"',
                columns={
                    'sale_id': 'BIGINT',
                    'amount_pence': 'BIGINT',
                    'note': 'VARCHAR'
                }
            )
        """, [str(path)]).fetchone()


if __name__ == "__main__":
    run_benchmark("duckdb", process)
