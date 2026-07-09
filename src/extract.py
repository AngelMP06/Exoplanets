import logging

import requests

from tenacity import retry, stop_after_attempt, wait_fixed

import pandas as pd

logger = logging.getLogger(__name__)

URL = "https://exoplanetarchive.ipac.caltech.edu/TAP/sync"

columns = [
    "pl_name",          #Planet Name
    "hostname",         #Host Name
    "sy_snum",          #Number of Stars
    "sy_pnum",          #Number of Planets
    "sy_mnum",          #Number of Moons
    "discoverymethod",  #Discovery Method
    "disc_year",        #Discovery Year
    "disc_locale",      #Discovery Locale
    "disc_facility",    #Discovery Facility
    "disc_telescope",   #Discovery Telescope
    "disc_instrument",  #Discovery Instrument
    "pl_orbper",        #Orbital Period [days]
    "pl_orbsmax",       #Orbit Semi-Major Axis [au]
    "pl_orbeccen",      #Orbit Eccentricity
    "pl_rade",          #Planet Radius [Earth Radius]
    "pl_eqt",           #Equilibrium Temperature [K]
    "st_teff",          #Stellar Effective Temperature [K]
    "st_rad",           #Stellar Radius [Solar Radius]
    "st_mass",          #Stellar Mass [Solar mass]
    "st_lum",           #Stellar Luminosity [log10(Solar)]
    "sy_dist",          #Distance [pc]
    "ra",               #RA [decimal degrees]
    "dec",              #Dec [decimal degrees]
]

query = f"""
SELECT {",".join(columns)} FROM pscomppars
"""

PARAMS = {
    "query": query,
    "format": "json",
}


@retry(stop=stop_after_attempt(3), wait=wait_fixed(5))
def get_data(url=URL, params=PARAMS):
    """Capa raw: consulta la API TAP de NASA y devuelve los datos crudos (JSON).
    Reintenta hasta 3 veces (esperando 5 s) si la petición falla."""
    logger.info("Consultando API TAP de NASA: %s", url)
    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()  # lanza error si el HTTP status es 4xx o 5xx
    except requests.RequestException:
        logger.exception("Fallo al consultar la API TAP")
        raise
    data = response.json()
    logger.info("Petición correcta: %d filas recibidas", len(data))
    df = pd.DataFrame(data)
    return df


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
    df = get_data()
    print(df.isnull().sum())
    logger.info("Filas recibidas: %d", len(df))
    logger.info("Primera fila: %s", df.iloc[0])