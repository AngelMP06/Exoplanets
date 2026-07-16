(select planet_name, distance_pc, star_name, 'mas_distante' as categoria
from mart_planets
where distance_pc is not null
order by distance_pc desc
limit 10)

UNION ALL

(select planet_name, distance_pc, star_name, 'menos_distante' as categoria
from mart_planets
where distance_pc is not null
order by distance_pc asc
limit 10)