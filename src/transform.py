import logging

import numpy as np

from src.extract import get_data

logger = logging.getLogger(__name__)

# raw -> staging: mismos renombres que stg_planets.sql
COLUMN_NAMES = {
    "pl_name": "planet_name",
    "hostname": "star_name",
    "sy_snum": "num_stars",
    "sy_pnum": "num_planets",
    "sy_mnum": "num_moons",
    "discoverymethod": "discovery_method",
    "disc_year": "discovery_year",
    "disc_locale": "discovery_locale",
    "disc_facility": "discovery_facility",
    "disc_telescope": "discovery_telescope",
    "disc_instrument": "discovery_instrument",
    "pl_orbper": "orbital_period_days",
    "pl_orbsmax": "semi_major_axis_au",
    "pl_orbeccen": "eccentricity",
    "pl_rade": "planet_radius_earth",
    "pl_eqt": "equilibrium_temp_k",
    "st_teff": "star_temp_k",
    "st_rad": "star_radius_solar",
    "st_mass": "star_mass_solar",
    "st_lum": "star_luminosity_log",
    "sy_dist": "distance_pc",
    "ra": "ra_deg",
    "dec": "dec_deg",
}

UNKNOWN = "Desconocido"


def stage(df):
    """Capa staging: renombra columnas y castea tipos (stg_planets)."""
    staged = df.rename(columns=COLUMN_NAMES)[list(COLUMN_NAMES.values())]

    # Int64 (nullable) porque disc_year puede venir nulo
    staged["discovery_year"] = staged["discovery_year"].astype("Int64")

    logger.info("Staging: %d filas, %d columnas", len(staged), staged.shape[1])
    return staged


def mart(df):
    """Capa mart: columnas calculadas y clasificaciones (mart_planets)."""
    out = df.copy()

    # Zona habitable: la luminosidad viene en log10, se pasa a lineal primero
    luminosity = 10 ** out["star_luminosity_log"]
    out["hz_inner"] = 0.75 * np.sqrt(luminosity)
    out["hz_outer"] = 1.77 * np.sqrt(luminosity)
    out["eff_distance"] = out["semi_major_axis_au"] * (
        1 + out["eccentricity"] ** 2 / 2
    )

    # Con nulos las comparaciones dan False y cae al default (UNKNOWN),
    # igual que el else del case en SQL.
    out["habitability"] = np.select(
        [
            out["eff_distance"] < out["hz_inner"],
            out["eff_distance"] > out["hz_outer"],
            out["eff_distance"].between(out["hz_inner"], out["hz_outer"]),
        ],
        ["Muy cerca", "Muy lejos", "Zona habitable"],
        default=UNKNOWN,
    )

    temp_c = out["equilibrium_temp_k"] - 273.15
    out["temp_habitability"] = np.select(
        [
            temp_c < -50,
            temp_c < 0,
            temp_c < 50,
            temp_c < 100,
            temp_c >= 100,
        ],
        [
            "hP - hypopsychroplanet",
            "P - psychroplanet",
            "M - mesoplanet",
            "T - thermoplanet",
            "hT - hyperthermoplanet",
        ],
        default=UNKNOWN,
    )

    radius = out["planet_radius_earth"]
    out["planet_type"] = np.select(
        [
            radius < 0.5,
            radius < 0.8,
            radius < 1.2,
            radius < 1.75,
            radius < 2.1,
            radius < 4,
            radius < 8,
            radius >= 8,
        ],
        [
            "Mercury-like",
            "Mini-Earth",
            "Earth-like",
            "Super-Earth",
            "Transition",
            "Sub-Neptune",
            "Neptune-like",
            "Jovian-like",
        ],
        default=UNKNOWN,
    )

    star_temp = out["star_temp_k"]
    out["spectral_type"] = np.select(
        [
            star_temp >= 30000,
            star_temp >= 10000,
            star_temp >= 7500,
            star_temp >= 6000,
            star_temp >= 5200,
            star_temp >= 3700,
            star_temp < 3700,
        ],
        ["O", "B", "A", "F", "G", "K", "M"],
        default=UNKNOWN,
    )

    # a float: los nulos de Int64 son pd.NA y np.select solo acepta booleanos
    year = out["discovery_year"].to_numpy(dtype="float64", na_value=np.nan)
    out["discovery_era"] = np.select(
        [
            year < 2009,
            year <= 2017,
            year >= 2018,
        ],
        ["Pre-Kepler", "Era Kepler", "Era TESS"],
        default=UNKNOWN,
    )

    logger.info("Mart: %d filas, %d columnas", len(out), out.shape[1])
    return out


def transform():
    """Pipeline completo: raw (get_data) -> stg_planets -> mart_planets."""
    return mart(stage(get_data()))


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
    df = transform()
    print(df.head())
    print(df["habitability"].value_counts())
    print(df["planet_type"].value_counts())
