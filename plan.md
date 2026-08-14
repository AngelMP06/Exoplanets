1) El orden de aparición de las gráficas será el siguiente
    - discovery
    - distance
    - size
    - system
    - habitability

Quiero que a las gráficas que tienen categorías creadas por mi haciendolas en un rango, muestren dicho rango abajo.

Titulo (Exoplanetas)

descripción: Los exoplanetas son planetas que pertenecen a otro sistema solar, orbitan una estrella que no es nuestro sol, hasta el momento se han confirmado {Número de exoplanetas (usar la api de position para hacer counts)} exoplanetas, lo cual es un número pequeño comparado con las aproximadamente 100 mil estrellas en nuestra galaxia, lo que da a suponer que aún hay una exorbitante cantidad de exoplanetas esperando ser descubiertos.

## Descubrimiento

Tendremos 2 columnas, en la de la izquierda estarán 3 categorías controladas por dropdown, y la derecha solo tendrá la categoría por_metodo, cada una tendrá el texto por encima de ella.

(por_año, tendencia_Acumulada, por_discovery_era): Los primeros 2 exoplanetas fueron descubiertos en 1992, dichos planetas orbitaban un púlsar llamado Lich. Este fue el inicio de la búsqueda de más exoplanetas en nuestra galaxia.

Vemos que entre los años 2014 y 2016 se hicieron el descubrimiento de varios exoplanetas, sin embargo, no es que esos exoplanetas se hayan detectado en esos años, se detectaron en años anteriores, pero tuvieron que esperar hasta esos años para, mediante estudios científicos, confirmar su existencia.

Fue gracias al telescopio Kepler de la NASA, que publicó enormes lotes de datos espaciales acumulados e introdujo métodos avanzados de verificación estadística que confirmaron miles de candidatos a planetas a la vez, por eso tiene la mayor cantidad de

por_método: Indiscutiblemente, el mejor método para detectar exoplanetas es el transitorio, el cual consiste en observar el valor de la luminosidad de una estrella para ver si es que disminuye debido a que un planeta se ha puesto entre dicha estrella y el telescopio que la observa.

El segundo método que descubrió más exoplanetas es el de la velocidad radial, este detecta el "bamboleo" periódico de una estrella debido a que está siendo afectada por la gravedad de un planeta que la orbita, ya que ambos orbitan un centro de gravedad común.

El tercer método es de microlente gravitacional, este consiste en detectar cuando la gravedad de un planeta que pasa frente a una estrella y curva su luz, esto añade un pico de luz de extra brillo que permite medir su masa y posición. Este método es utilizado para detectar planetas lejasnos que otros métodos no pueden detectar. 


## Distancia

También tendremos 2 columnas, en la izquierda estarán los 2 rankings de mart_distance en tablas, ambos tendrán el mismo texto, mientras que a la derecha estará la distribución de distancias usando matplotlib, las distancias serán obtenidas de mart_position:

(mas_distante, menos_distante): Lo planetas más distantes encontrados están a 8500 pc = 27722 años luz de distancia, este es por ahora el límite de hacia donde podemos ver. Y los más cercanos se encuentran a 1.3 pc = 4.2 años luz, ambas se encuentran orbitando la estrella proxima centauri, la estrella más cercana a nuestro sol.

distribución_distancia: Esta gráfica es muy importante, por que nos indica que la mayoría de exoplanetas descubiertos se encuentran cerca a nosotros, debido a que son los más fáciles de comprobar, esto nos indicaría que aún hay muchos planetas por descubrir los cuales se encuentran en estrellas más distantes. ¿Cuanto nos estaremos perdiendo?

## Size

CAsi igual que distancia, 2 columnas, en la izquierda estarán los 2 rankings de mart_size en tablas, con el mismo texto, a la derecha la distribución de sizes, esta vez usando plotly, pues la data ya está en la api, dejalo como esta hecho. En distribución, no contar los planetas que tienen categiría desconocido.

(mas grande, mas pequeña): El planeta más grande encontrado es un planeta joviano de más de 87 veces el radio de la tierra, es tán grande que solo su radio ya es mayor que la distancia entre la tierra y la luna, y es casi 8 veces el tamaño de Jupiter. El más pequeño encontrado es uno tipo mercurio tiene casi el 31 % del radio terrestre, es más pequeño que mercurio que tiene le 38 %.

(distribución): Vemos que los exoplanetas más grandes son los que más se descubren, siendo que la mayoría de planetas descubiertos caen en la categoría de sub-neptunianos o jovianos. Esto puede provocar un sesgo, se podría pensar que la mayoría de planetas que existen son de esos tipos, pero simplemente esta distribución puede deberse a que los planetas más grandes son mucho más fáciles de encontrar que los pequeños.

## Habitability

Casi igual a los antereiores, a la izquierda el ranking de planetas habitables como tabla y a la derecha las 2 distribuciones con dropdown (por habitability y por temp habitability), no se cuentan los "Desconocido".

(ranking): El máximo número de planetas en la zona habitable de un sistema es de 3 planetas, es mayor a nuestro sistema solar que tiene 2 planetas en la zona habitable (tierra y marte), esto puede dar indiciso de que es posible la vida en esos sistemas algo que siempre se ha creído probable.

(distribución): Vemos que la mayoría de planetas encontrados se encuentran cerca de su estrella anfitriona siendo por lo tanto muy calientes, esto se muestra en ambas gráficas de distribución, otra vez, al ser planetas cercanos a sus estrellas, son detectados gracias a que nuestros métodos siempre toma en cuenta el contraste entre esos planetas y sus estrellas. Lo que indica que incluso puede haber más planetas en sus zonas habitables que solamente 3 por sistema a lo más.

## System

Aquí solo irá la distribución_num_planetas, los tops no irán:

(distribución_num_planetas): Vemos que la mayoría de sistemas tienen 1 exoplaneta descubierto y con un máximo de 8 planetas por sistema, al igual que nuestro sistema solar que también tiene 8 planetas.

## Conclusión

Todas las gráficas nos mostraron algo contundente, nuestros métodos para detectar planetas no son suficientes, los planetas más fáciles de encontrar son aquellos grandes, poco distantes y cercanos a sus respectivas estrellas, siendo los llamados júpiters calientes los más comunes. Todo esto generaría un gran sesgo si no se hiciese un análisis más profundo ¿Cuanto nos estaremos perdiendo? Posiblemente haya más planetas e incluso asteroides o lunas que no detectamos, posiblemente cada uno de esos sitemas tienen una gran variedad de cuerpos, al igual que nuestro sistema solar, pero indetectables con la tecnología actual. Nos dimos cuenta que recién estamos en pañales cuando hablamos de detección de exoplanetas, aún falta muchísimo más por mejorar. Ojalá en un futuro se logre desarrollar más estas técnicas o encontrar nuevas formas de buscar cuerpos más allá de nuestro sistema solar.