(select 
    star_name, 
    num_planets as valor, 
    'top_planetas_por_sistema' as categoria
from (select distinct star_name, num_planets from mart_planets)
order by valor desc
limit 10)

UNION ALL

(select 
    star_name, 
    num_moons as valor, 
    'top_lunas_por_sistema' as categoria
from (select distinct star_name, num_moons from mart_planets)
order by valor desc
limit 10)