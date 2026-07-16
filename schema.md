# Esquema de datos — Exoplanets

Documentación del pipeline de datos por capas: **raw → staging → marts**.

- **raw**: datos crudos de la fuente, sin transformar.
- **staging**: limpieza y normalización (nombres, tipos, nulos).
- **marts**: tablas finales con columnas calculadas y clasificaciones.

---

## Raw

### raw.planets

Datos crudos de la API TAP de NASA Exoplanet Archive, tabla `pscomppars`
(Planetary Systems Composite Parameters). Una fila por planeta confirmado.
No se transforma nada: es la respuesta de `get_data()` (extract.py) volcada tal cual
a un parquet en S3, que dbt lee como source.

- **Fuente:** https://exoplanetarchive.ipac.caltech.edu/TAP/sync
- **Tabla origen:** `pscomppars`
- **Source dbt:** `raw.planets` → `s3://exoplanetas-pipeline-datos/raw/planets.parquet`
- **Grano:** un planeta por fila
- **Docs columnas:** https://exoplanetarchive.ipac.caltech.edu/docs/API_PS_columns.html

| columna          | tipo   | descripción                              |
|------------------|--------|------------------------------------------|
| pl_name          | string | Nombre del planeta                       |
| hostname         | string | Nombre de la estrella anfitriona         |
| sy_snum          | int    | Número de estrellas en el sistema        |
| sy_pnum          | int    | Número de planetas en el sistema         |
| sy_mnum          | int    | Número de lunas en el sistema            |
| discoverymethod  | string | Método de descubrimiento                 |
| disc_year        | float  | Año de descubrimiento                    |
| disc_locale      | string | Lugar de descubrimiento (espacio/tierra) |
| disc_facility    | string | Instalación que lo descubrió             |
| disc_telescope   | string | Telescopio usado                         |
| disc_instrument  | string | Instrumento usado                        |
| pl_orbper        | float  | Periodo orbital [días]                   |
| pl_orbsmax       | float  | Semieje mayor de la órbita [AU]          |
| pl_orbeccen      | float  | Excentricidad orbital                    |
| pl_rade          | float  | Radio del planeta [radios terrestres]    |
| pl_eqt           | float  | Temperatura de equilibrio [K]            |
| st_teff          | float  | Temperatura efectiva estelar [K]         |
| st_rad           | float  | Radio estelar [radios solares]           |
| st_mass          | float  | Masa estelar [masas solares]             |
| st_lum           | float  | Luminosidad estelar [log10(solar)]       |
| sy_dist          | float  | Distancia al sistema [pc]                |
| ra               | float  | Ascensión recta [grados decimales]       |
| dec              | float  | Declinación [grados decimales]           |

---

## Staging

### stg_planets

Limpieza de `raw_ps`: columnas renombradas a nombres intuitivos y tipos
casteados. Es un "uno a uno" con raw (misma granularidad, un planeta por fila).

- **Origen:** `raw_ps`
- **Grano:** un planeta por fila

| columna               | tipo   | origen          | descripción                                |
|-----------------------|--------|-----------------|--------------------------------------------|
| planet_name           | string | pl_name         | Nombre del planeta                         |
| star_name             | string | hostname        | Nombre de la estrella anfitriona           |
| num_stars             | int    | sy_snum         | Número de estrellas en el sistema          |
| num_planets           | int    | sy_pnum         | Número de planetas en el sistema           |
| num_moons             | int    | sy_mnum         | Número de lunas en el sistema              |
| discovery_method      | string | discoverymethod | Método de descubrimiento                   |
| discovery_year        | int    | disc_year       | Año de descubrimiento (casteado a int)     |
| discovery_locale      | string | disc_locale     | Lugar de descubrimiento (espacio/tierra)   |
| discovery_facility    | string | disc_facility   | Instalación que lo descubrió               |
| discovery_telescope   | string | disc_telescope  | Telescopio usado                           |
| discovery_instrument  | string | disc_instrument | Instrumento usado                          |
| orbital_period_days   | float  | pl_orbper       | Periodo orbital [días]                     |
| semi_major_axis_au    | float  | pl_orbsmax      | Semieje mayor de la órbita [AU]            |
| eccentricity          | float  | pl_orbeccen     | Excentricidad orbital                      |
| planet_radius_earth   | float  | pl_rade         | Radio del planeta [radios terrestres]      |
| equilibrium_temp_k    | float  | pl_eqt          | Temperatura de equilibrio [K]              |
| star_temp_k           | float  | st_teff         | Temperatura efectiva estelar [K]           |
| star_radius_solar     | float  | st_rad          | Radio estelar [radios solares]             |
| star_mass_solar       | float  | st_mass         | Masa estelar [masas solares]               |
| star_luminosity_log   | float  | st_lum          | Luminosidad estelar [log10(solar)]         |
| distance_pc           | float  | sy_dist         | Distancia al sistema [pc]                  |
| ra_deg                | float  | ra              | Ascensión recta [grados decimales]         |
| dec_deg               | float  | dec             | Declinación [grados decimales]             |

---

## Marts

### mart_planets

Tabla final lista para análisis. Hereda todas las columnas de `stg_planets` y
añade las columnas calculadas y clasificaciones definidas en `mart_planets.sql`.
Es la tabla base que consumen el resto de marts.

Todos los rangos de las clasificaciones son semiabiertos: el límite inferior
entra en la categoría y el superior no (`[inicio, fin)`).

- **Origen:** `stg_planets`
- **Grano:** un planeta por fila

Columnas añadidas (además de las de `stg_planets`):

| columna           | tipo   | descripción                              |
|-------------------|--------|------------------------------------------|
| hz_inner          | float  | Límite interior de la zona habitable [AU]|
| hz_outer          | float  | Límite exterior de la zona habitable [AU]|
| eff_distance      | float  | Distancia efectiva promedio [AU]         |
| habitability      | string | Posición vs. zona habitable              |
| temp_habitability | string | Clase térmica T-PHC                      |
| planet_type       | string | Familia por radio (exoplanet.eu)         |
| spectral_type     | string | Tipo espectral Morgan-Keenan             |
| discovery_era     | string | Era de descubrimiento                    |

**Cómo se calculan las columnas numéricas**

- **hz_inner / hz_outer** — límites de la zona habitable de la estrella [AU].
  Se obtienen a partir de la luminosidad estelar. Como `star_luminosity_log`
  está en log10, primero se pasa a lineal (`L = 10 ** star_luminosity_log`) y
  luego se escala por la raíz de la luminosidad:
  - `hz_inner = 0.75 * sqrt(L)`
  - `hz_outer = 1.77 * sqrt(L)`
  - Referencia: https://exoplanetarchive.ipac.caltech.edu/docs/poet_calculations.html

- **eff_distance** — distancia orbital promedio efectiva [AU], ajustando el
  semieje mayor por la excentricidad de la órbita:
  - `eff_distance = semi_major_axis_au * (1 + eccentricity**2 / 2)`
  - Referencia: https://physics.stackexchange.com/questions/713816

**Valores de las clasificaciones**

- **habitability** — `eff_distance` vs. la zona habitable:
  - `Zona habitable`: entre `hz_inner` y `hz_outer`
  - `Muy cerca`: más cerca que `hz_inner`
  - `Muy lejos`: más lejos que `hz_outer`
  - `Desconocido`: falta `eff_distance`, `hz_inner` o `hz_outer`

- **temp_habitability** — T-PHC (PHL @ UPR Arecibo), sobre `equilibrium_temp_k` convertida a °C (`K - 273.15`):
  - `hP - hypopsychroplanet`: < −50 °C
  - `P - psychroplanet`: −50 a 0 °C
  - `M - mesoplanet`: 0 a 50 °C
  - `T - thermoplanet`: 50 a 100 °C
  - `hT - hyperthermoplanet`: ≥ 100 °C
  - `Desconocido`: sin temperatura
  - Referencia: https://phl.upr.edu/library/labnotes/a-thermal-planetary-habitability-classification-for-exoplanets

- **planet_type** — familia por radio (exoplanet.eu), en radios terrestres:
  - `Mercury-like`: < 0.5 · `Mini-Earth`: 0.5–0.8 · `Earth-like`: 0.8–1.2 · `Super-Earth`: 1.2–1.75
  - `Transition`: 1.75–2.1 · `Sub-Neptune`: 2.1–4 · `Neptune-like`: 4–8 · `Jovian-like`: > 8
  - `Desconocido`: sin radio
  - Referencia: https://scholar.exoplanet.eu/spip.php?article291&lang=en

- **spectral_type** — clasificación Morgan-Keenan por `star_temp_k`:
  - `O`: >= 30000 · `B`: 10000–30000 · `A`: 7500–10000 · `F`: 6000–7500
  - `G`: 5200–6000 · `K`: 3700–5200 · `M`: < 3700 · `Desconocido`: sin temperatura

- **discovery_era** — por `discovery_year`:
  - `Pre-Kepler`: < 2009 · `Era Kepler`: 2009–2017 · `Era TESS`: ≥ 2018 · `Desconocido`: sin año
