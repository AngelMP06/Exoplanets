with biggest_planet as (
    
select planet_name, planet_radius_earth, star_name,
ROW_NUMBER() OVER (PARTITION BY star_name ORDER BY planet_radius_earth desc) as rn
from {{ ref('mart_planets') }}
)

(select planet_name, planet_radius_earth, star_name, 'mas grande' as categoria
from {{ ref('mart_planets') }} order by planet_radius_earth desc limit 10)

UNION ALL

(select planet_name, planet_radius_earth, star_name, 'mas pequeña' as categoria
from {{ ref('mart_planets') }} order by planet_radius_earth asc limit 10)

union all   

(select planet_name, planet_radius_earth, star_name, 'mas grande por sistema' as categoria
from biggest_planet where rn = 1 order by planet_radius_earth desc limit 10)