import sys
from pathlib import Path

# permite importar los módulos de src/ (extract, normalize, transform)
sys.path.insert(0, str(Path(__file__).parent / "src"))

from normalize import normalize
from transform import transform


def main():
    # pipeline: raw (extract) -> staging (normalize) -> marts (transform)
    df = transform(normalize())
    print(df)


if __name__ == "__main__":
    main()
