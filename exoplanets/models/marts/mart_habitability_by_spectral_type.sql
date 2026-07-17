select 
    spectral_type, 
    habitability, 
    count(*) as conteo
from {{ ref('mart_planets') }}
group by spectral_type, habitability