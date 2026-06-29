import logging

import numpy as np
import pandas as pd

from normalize import normalize


logger = logging.getLogger(__name__)

# https://scholar.exoplanet.eu/spip.php?article291&lang=en

def classify_planet(radius):
    # clasificación por radio (en radios terrestres) según exoplanet.eu
    if pd.isna(radius):
        return "Desconocido"
    elif radius <= 0.5:
        return "Mercury-like"
    elif radius <= 0.8:
        return "Mini-Earth"
    elif radius <= 1.2:
        return "Earth-like"
    elif radius <= 1.75:
        return "Super-Earth"
    elif radius <= 2.1:
        return "Transition"
    elif radius <= 4:
        return "Sub-Neptune"
    elif radius <= 8:
        return "Neptune-like"
    else:
        return "Jovian-like"

# Morgan Keenan classification

def spectral_type(teff):
    if pd.isna(teff):
        return "Desconocido"
    elif teff > 30000:
        return "O"
    elif teff > 10000:
        return "B"
    elif teff > 7500:
        return "A"
    elif teff > 6000:
        return "F"
    elif teff > 5200:
        return "G"
    elif teff > 3700:
        return "K"
    else:
        return "M"


def transform(df):
    """Capa marts: recibe el df normalizado (staging) y añade las columnas
    calculadas y clasificaciones (ver schema.md -> mart_habitability)."""

    logger.info("Iniciando transformación de %d filas", len(df))

    # star_luminosity_log está en log10(luminosidad solar); lo pasamos a lineal
    luminosity = 10 ** df["star_luminosity_log"]

    # https://exoplanetarchive.ipac.caltech.edu/docs/poet_calculations.html
    # Zona habitable de la estrella (en au)
    df["hz_inner"] = 0.75 * np.sqrt(luminosity)   # límite interior
    df["hz_outer"] = 1.77 * np.sqrt(luminosity)   # límite exterior

    # https://physics.stackexchange.com/questions/713816
    # Distancia promedio efectiva del planeta considerando excentricidad (en au)
    df["eff_distance"] = df["semi_major_axis_au"] * (1 + df["eccentricity"] ** 2 / 2)

    # Clasificación según la posición del planeta respecto a la zona habitable
    conditions = [
        df["eff_distance"] < df["hz_inner"],   # más cerca que el límite interior
        df["eff_distance"] > df["hz_outer"],   # más lejos que el límite exterior
    ]
    choices = ["Más caliente", "Más frío"]
    df["habitability"] = np.select(conditions, choices, default="Zona habitable")

    # si falta algún dato, no se puede clasificar
    df.loc[df[["eff_distance", "hz_inner", "hz_outer"]].isna().any(axis=1), "habitability"] = "Desconocido"

    # https://phl.upr.edu/library/labnotes/a-thermal-planetary-habitability-classification-for-exoplanets
    # Clasificación térmica de habitabilidad (T-PHC, PHL @ UPR Arecibo)
    # equilibrium_temp_k está en Kelvin; lo pasamos a °C para usar los límites del esquema
    temp_celsius = df["equilibrium_temp_k"] - 273.15
    temp_conditions = [
        temp_celsius < -50,                        # Clase hP
        temp_celsius < 0,                          # Clase P  (-50 a 0)
        temp_celsius < 50,                         # Clase M  (0 a 50)
        temp_celsius < 100,                        # Clase T  (50 a 100)
    ]
    temp_choices = [
        "hP - hypopsychroplanet",
        "P - psychroplanet",
        "M - mesoplanet",
        "T - thermoplanet",
    ]
    df["temp_habitability"] = np.select(temp_conditions, temp_choices, default="hT - hyperthermoplanet")

    # si no hay temperatura, no se puede clasificar
    df.loc[df["equilibrium_temp_k"].isna(), "temp_habitability"] = "Desconocido"

    df["planet_type"] = df["planet_radius_earth"].apply(classify_planet)

    df["spectral_type"] = df["star_temp_k"].apply(spectral_type)

    # Era de descubrimiento según el año
    # discovery_year es Int64 (nullable); pasamos las condiciones a bool de numpy
    era_conditions = [
        (df["discovery_year"] < 2009).to_numpy(dtype=bool, na_value=False),  # antes de Kepler
        (df["discovery_year"] < 2018).to_numpy(dtype=bool, na_value=False),  # 2009 a 2017 -> era Kepler
    ]
    era_choices = ["Pre-Kepler", "Era Kepler"]
    df["discovery_era"] = np.select(era_conditions, era_choices, default="Era TESS")

    # si no hay año, no se puede clasificar
    df.loc[df["discovery_year"].isna(), "discovery_era"] = "Desconocido"

    logger.info("Transformación completada: %d filas, %d columnas", *df.shape)
    return df


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
    df = transform(normalize())
    df.info()
