select 
    planet_type as clasificacion,
    count(*) as conteo,
    'por_tipo_planeta' as categoria
from mart_planets
group by planet_type