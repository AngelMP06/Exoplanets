with planets as (
    select * from {{ ref('stg_planets') }}
),

calculated as (
    select
        *,
        0.75 * sqrt(power(10, star_luminosity_log)) as hz_inner,
        1.77 * sqrt(power(10, star_luminosity_log)) as hz_outer,
        semi_major_axis_au * (1 + eccentricity**2 / 2) as eff_distance

    from planets
),

classified as (
    select
        *,
        case
            when eff_distance < hz_inner then 'Muy cerca'
            when eff_distance > hz_outer then 'Muy lejos'
            when eff_distance between hz_inner and hz_outer then 'Zona habitable'
            else 'Desconocido'
        end as habitability,
        case
            when equilibrium_temp_k - 273.15 < -50 then 'hP - hypopsychroplanet'
            when equilibrium_temp_k - 273.15 >= -50 and equilibrium_temp_k - 273.15 < 0 then 'P - psychroplanet'
            when equilibrium_temp_k - 273.15 >= 0 and equilibrium_temp_k - 273.15 < 50 then 'M - mesoplanet'
            when equilibrium_temp_k - 273.15 >= 50 and equilibrium_temp_k - 273.15 < 100 then 'T - thermoplanet'
            when equilibrium_temp_k - 273.15 >= 100 then 'hT - hyperthermoplanet'
            else 'Desconocido'
        end as temp_habitability,
        case
            when planet_radius_earth < 0.5 then 'Mercury-like'
            when planet_radius_earth >= 0.5 and planet_radius_earth < 0.8 then 'Mini-Earth'
            when planet_radius_earth >= 0.8 and planet_radius_earth < 1.2 then 'Earth-like'
            when planet_radius_earth >= 1.2 and planet_radius_earth < 1.75 then 'Super-Earth'
            when planet_radius_earth >= 1.75 and planet_radius_earth < 2.1 then 'Transition'
            when planet_radius_earth >= 2.1 and planet_radius_earth < 4 then 'Sub-Neptune'
            when planet_radius_earth >= 4 and planet_radius_earth < 8 then 'Neptune-like'
            when planet_radius_earth >= 8 then 'Jovian-like'
            else 'Desconocido'
        end as planet_type,
        case
            when star_temp_k >= 30000 then 'O'
            when star_temp_k >= 10000 and star_temp_k < 30000 then 'B'
            when star_temp_k >= 7500 and star_temp_k < 10000 then 'A'
            when star_temp_k >= 6000 and star_temp_k < 7500 then 'F'
            when star_temp_k >= 5200 and star_temp_k < 6000 then 'G'
            when star_temp_k >= 3700 and star_temp_k < 5200 then 'K'
            when star_temp_k < 3700 then 'M'
            else 'Desconocido'
        end as spectral_type,
        case
            when discovery_year < 2009 then 'Pre-Kepler'
            when discovery_year >= 2009 and discovery_year <= 2017 then 'Era Kepler'
            when discovery_year >= 2018 then 'Era TESS'
            else 'Desconocido'
        end as discovery_era
    from calculated
)

select * from classified