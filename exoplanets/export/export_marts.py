import duckdb
import os
from pathlib import Path

DUCKDB_PATH = os.getenv("DUCKDB_PATH", "exoplanets.duckdb")
OUTPUT_DIR = Path("export/output")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

MARTS = [
    "mart_size",
    "mart_distance",
    "mart_system",
    "mart_position",
    "mart_habitability",
    "mart_size_distribution",
    "mart_system_distribution",
    "mart_habitability_distribution",
    "mart_discovery_distribution",
    "mart_habitability_by_spectral_type",
]

con = duckdb.connect(DUCKDB_PATH, read_only=True)

for mart in MARTS:
    df = con.execute(f"SELECT * FROM {mart}").df()
    output_path = OUTPUT_DIR / f"{mart}.json"
    df.to_json(output_path, orient="records", indent=2)
    print(f"Exportado {mart}: {len(df)} filas")

con.close()