(select 
    num_planets as clasificacion, 
    count(*) as conteo, 
    'distribucion_num_planetas' as categoria
from (select distinct star_name, num_planets from mart_planets)
group by num_planets)

UNION ALL

(select 
    num_moons as clasificacion, 
    count(*) as conteo, 
    'distribucion_num_lunas' as categoria
from (select distinct star_name, num_moons from mart_planets)
group by num_moons)