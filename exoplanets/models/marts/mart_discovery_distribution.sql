(select 
    discovery_method as clasificacion,
    count(*) as conteo,
    'por_metodo' as categoria
from {{ ref('mart_planets') }}
group by discovery_method
order by conteo desc)

UNION ALL

(select 
    cast(discovery_year as varchar) as clasificacion,
    count(*) as conteo,
    'por_año' as categoria
from {{ ref('mart_planets') }}
where discovery_year is not null
group by discovery_year
order by conteo desc)

UNION ALL

(select
    cast(discovery_year as varchar) as clasificacion,
    sum(count(*)) over (order by discovery_year) as conteo,
    'tendencia_acumulada' as categoria
from {{ ref('mart_planets') }}
where discovery_year is not null
group by discovery_year)

UNION ALL

(select
    discovery_era as clasificacion,
    count(*) as conteo,
    'por_discovery_era' as categoria
from {{ ref('mart_planets') }}
group by discovery_era)