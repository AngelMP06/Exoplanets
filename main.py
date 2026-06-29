import sys
from pathlib import Path

# permite importar los módulos de src/ (extract, normalize, transform)
sys.path.insert(0, str(Path(__file__).parent / "src"))

from normalize import normalize
from transform import transform
from load import load_to_s3


def main():
    # pipeline: raw (extract) -> staging (normalize) -> marts (transform)
    df = transform(normalize())
    print(df)

    # guardar local y subir a S3
    load_to_s3(df, "planets.parquet")
    print("Pipeline completado.")


if __name__ == "__main__":
    main()
