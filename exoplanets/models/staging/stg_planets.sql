with source as (
    select * from {{ source('raw', 'planets') }}
),

renamed as (
    select
        pl_name as planet_name,
        hostname as star_name,
        sy_snum as num_stars,
        sy_pnum as num_planets,
        sy_mnum as num_moons,
        discoverymethod as discovery_method,
        CAST(disc_year as INTEGER) as discovery_year,
        disc_locale as discovery_locale,
        disc_facility as discovery_facility,
        disc_telescope as discovery_telescope,
        disc_instrument as discovery_instrument,
        pl_orbper as orbital_period_days,
        pl_orbsmax as semi_major_axis_au,
        pl_orbeccen as eccentricity,
        pl_rade as planet_radius_earth,
        pl_eqt as equilibrium_temp_k,
        st_teff as star_temp_k,
        st_rad as star_radius_solar,
        st_mass as star_mass_solar,
        st_lum as star_luminosity_log,
        sy_dist as distance_pc,
        ra as ra_deg,
        dec as dec_deg
    from source 
)

select * from renamed