import pandas as pd

from extract import get_data

# Renombrado raw -> staging (ver schema.md, capa Staging)
COLUMN_RENAME = {
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


def normalize():
    """Capa staging: toma los datos crudos de la API y devuelve un df limpio
    con nombres intuitivos y tipos casteados (ver schema.md -> stg_planets)."""
    data = get_data()
    df = pd.DataFrame(data)

    # nombres intuitivos
    df = df.rename(columns=COLUMN_RENAME)

    # año de descubrimiento como entero (Int64 admite nulos)
    df["discovery_year"] = df["discovery_year"].astype("Int64")

    return df


if __name__ == "__main__":
    print(normalize().info())
