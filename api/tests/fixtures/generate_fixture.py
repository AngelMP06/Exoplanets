import duckdb
import os

os.makedirs("tests/fixtures", exist_ok=True)

fixture = duckdb.connect("tests/fixtures/test_exoplanets.duckdb")
fixture.execute("ATTACH 'exoplanets.duckdb' AS real (READ_ONLY)")

marts_sin_categoria = ["mart_habitability",
                        "mart_habitability_by_spectral_type",
                        "mart_position"]

marts_con_categoria = ["mart_size",
                        "mart_distance",
                        "mart_system",
                        "mart_discovery_distribution",
                        "mart_habitability_distribution",
                        "mart_size_distribution",
                        "mart_system_distribution"]


def copiar_sin_categorias(fixture, mart, n=15):
    fixture.execute(f"CREATE OR REPLACE TABLE {mart} AS SELECT * FROM real.{mart} LIMIT {n}")


def copiar_con_categorias(fixture, mart, columna="categoria", n=15):
    categorias = fixture.execute(f"SELECT DISTINCT {columna} FROM real.{mart}").fetchall()
    primera = True
    for (cat,) in categorias:
        query = f"SELECT * FROM real.{mart} WHERE {columna} = ? LIMIT {n}"
        if primera:
            fixture.execute(f"CREATE OR REPLACE TABLE {mart} AS {query}", [cat])
            primera = False
        else:
            fixture.execute(f"INSERT INTO {mart} {query}", [cat])


for mart in marts_sin_categoria:
    copiar_sin_categorias(fixture, mart, n=15)

for mart in marts_con_categoria:
    copiar_con_categorias(fixture, mart, columna="categoria", n=15)

fixture.execute("DETACH real")
fixture.close()