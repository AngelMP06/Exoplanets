select star_name, count(*) as planetas_habitables
from {{ ref('mart_planets') }}
where habitability = 'Zona habitable'
group by star_name
order by planetas_habitables desc
limit 10