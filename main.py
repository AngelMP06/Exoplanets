import logging
import sys

from src.extract import get_data
from src.load import load_to_s3

from pathlib import Path


# permite importar los módulos de src/ (extract, normalize, transform)
sys.path.insert(0, str(Path(__file__).parent / "src"))



logger = logging.getLogger(__name__)


def main():
    # raw (extract)
    df = get_data()

    # guardar local y subir a S3
    load_to_s3(df, "planets.parquet")
    logger.info("Pipeline completado.")

if __name__ == "__main__":
    # configuración única de logging para todo el pipeline
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
    main()
