(select habitability as clasificacion, count(*) as conteo, 'por_habitability' as categoria
from {{ ref('mart_planets') }}
group by habitability)

UNION ALL

(select temp_habitability as clasificacion, count(*) as conteo, 'por_temp_habitability' as categoria
from {{ ref('mart_planets') }}
group by temp_habitability)