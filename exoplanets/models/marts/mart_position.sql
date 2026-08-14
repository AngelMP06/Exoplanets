select 
    ra_deg,
    dec_deg,
    distance_pc,
    planet_name,
    star_name
from {{ ref('mart_planets') }} 
where ra_deg is not null
  and dec_deg is not null
  and distance_pc is not null
  and planet_name is not null
  and star_name is not null