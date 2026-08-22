# Marts de presentación — Exoplanets

Documentación de los marts que consume la página. Todos derivan de `mart_planets`,
la tabla base documentada en [schema.md](schema.md) (capa `raw → staging → marts`).

`mart_planets` es "una fila por planeta" y sirve para análisis. Los marts de este
archivo son distintos: ya vienen agregados o recortados para alimentar un gráfico
o un ranking concreto, sin cálculo adicional del lado de la página.

- **Materialización:** view (default de dbt, no hay `materialized` en `dbt_project.yml`).
- **Origen de todos:** `mart_planets`.

---

## Patrones comunes

Casi todos los marts siguen uno de dos patrones. Conviene entenderlos una vez y
no repetirlos por modelo:

**Patrón ranking** — varios top-10 apilados con `UNION ALL` en una sola tabla.
La columna `categoria` dice de qué ranking viene cada fila; la página filtra por
ella. Grano: una fila por planeta (o estrella) dentro de cada ranking.

**Patrón distribución** — varios `GROUP BY` apilados con `UNION ALL`, con forma
fija `clasificacion` / `conteo` / `categoria`. `clasificacion` es el valor
agrupado, `conteo` cuántas filas caen ahí, y `categoria` de qué agrupación viene.
Grano: una fila por valor distinto dentro de cada agrupación.

La excepción es `mart_position` (ver [Proyección](#proyección)): ni agrega ni
rankea, es una fila por planeta sin tocar.

---

## Rankings

### mart_size

Los planetas más grandes y más pequeños por radio, en radios terrestres.

- **Grano:** un planeta por fila, dentro de cada `categoria`
- **Filas:** hasta 30 (10 por categoría)

| columna             | tipo   | descripción                       |
|---------------------|--------|-----------------------------------|
| planet_name         | string | Nombre del planeta                |
| planet_radius_earth | float  | Radio [radios terrestres]         |
| star_name           | string | Estrella anfitriona               |
| categoria           | string | Qué ranking produjo la fila       |

Valores de `categoria`:

- `mas grande`: top 10 por radio descendente, sobre todos los planetas.
- `mas pequeña`: top 10 por radio ascendente, sobre todos los planetas.
- `mas grande por sistema`: se toma el planeta más grande de cada estrella
  (`ROW_NUMBER()` particionado por `star_name`) y de esos se muestran los 10
  mayores. Sirve para que un solo sistema con muchos gigantes no acapare el
  ranking `mas grande`.

### mart_distance

Los sistemas más lejanos y más cercanos a nosotros.

- **Grano:** un planeta por fila, dentro de cada `categoria`
- **Filas:** hasta 20 (10 por categoría)
- Se descartan los planetas sin `distance_pc`.

| columna     | tipo   | descripción                 |
|-------------|--------|-----------------------------|
| planet_name | string | Nombre del planeta          |
| distance_pc | float  | Distancia al sistema [pc]   |
| star_name   | string | Estrella anfitriona         |
| categoria   | string | Qué ranking produjo la fila |

Valores de `categoria`: `mas_distante` (top 10 descendente) · `menos_distante`
(top 10 ascendente).

### mart_system

Los sistemas más poblados, por número de planetas y por número de lunas.

- **Grano:** una estrella por fila, dentro de cada `categoria`
- **Filas:** hasta 20 (10 por categoría)
- `num_planets` y `num_moons` son atributos del sistema, no del planeta, así que
  se hace `select distinct star_name, ...` antes de ordenar. Sin ese `distinct`
  una estrella con N planetas aparecería N veces.

| columna   | tipo   | descripción                                   |
|-----------|--------|-----------------------------------------------|
| star_name | string | Estrella anfitriona                           |
| valor     | int    | Nº de planetas o de lunas, según `categoria`  |
| categoria | string | Qué ranking produjo la fila                   |

Valores de `categoria`: `top_planetas_por_sistema` (`valor` = `num_planets`) ·
`top_lunas_por_sistema` (`valor` = `num_moons`).

### mart_habitability

Las estrellas con más planetas dentro de su zona habitable.

- **Grano:** una estrella por fila
- **Filas:** hasta 10
- Solo cuenta planetas con `habitability = 'Zona habitable'`; las estrellas con
  cero no aparecen.

| columna             | tipo   | descripción                                |
|---------------------|--------|--------------------------------------------|
| star_name           | string | Estrella anfitriona                        |
| planetas_habitables | int    | Nº de planetas suyos en la zona habitable  |

---

## Distribuciones

### mart_size_distribution

Cuántos planetas hay de cada familia por radio.

- **Grano:** un `planet_type` por fila
- **Filas:** hasta 9 (los 8 tipos + `Desconocido`)

| columna       | tipo   | descripción                          |
|---------------|--------|--------------------------------------|
| clasificacion | string | Valor de `planet_type`               |
| conteo        | int    | Nº de planetas de ese tipo           |
| categoria     | string | Siempre `por_tipo_planeta`           |

`categoria` es constante aquí; existe solo para que la forma coincida con el
resto de distribuciones. Los valores posibles de `clasificacion` son los de
`planet_type` en [schema.md](schema.md).

### mart_system_distribution

Cuántos sistemas hay con N planetas, y cuántos con N lunas.

- **Grano:** un valor de N por fila, dentro de cada `categoria`
- Igual que `mart_system`, deduplica con `select distinct star_name, ...` para
  contar sistemas y no planetas.

| columna       | tipo   | descripción                                |
|---------------|--------|--------------------------------------------|
| clasificacion | int    | El N: nº de planetas o de lunas            |
| conteo        | int    | Nº de sistemas con ese N                   |
| categoria     | string | Qué agrupación produjo la fila             |

Valores de `categoria`: `distribucion_num_planetas` · `distribucion_num_lunas`.

Ojo: aquí `clasificacion` es un entero, no un string como en las otras
distribuciones.

### mart_habitability_distribution

Cuántos planetas hay en cada clase de habitabilidad, por las dos clasificaciones
que existen.

- **Grano:** una clase por fila, dentro de cada `categoria`

| columna       | tipo   | descripción                     |
|---------------|--------|---------------------------------|
| clasificacion | string | Valor de la clase               |
| conteo        | int    | Nº de planetas en esa clase     |
| categoria     | string | Qué agrupación produjo la fila  |

Valores de `categoria`:

- `por_habitability`: `clasificacion` toma los valores de `habitability`
  (posición vs. zona habitable).
- `por_temp_habitability`: `clasificacion` toma los valores de
  `temp_habitability` (clase térmica T-PHC).

Ambas listas de valores están en [schema.md](schema.md).

### mart_discovery_distribution

Cómo y cuándo se han descubierto los planetas. Es la distribución más cargada:
apila cuatro agrupaciones distintas.

- **Grano:** un valor por fila, dentro de cada `categoria`

| columna       | tipo   | descripción                            |
|---------------|--------|----------------------------------------|
| clasificacion | string | Valor agrupado (método, año o era)     |
| conteo        | int    | Nº de planetas, o acumulado            |
| categoria     | string | Qué agrupación produjo la fila         |

Valores de `categoria`:

- `por_metodo`: `clasificacion` = `discovery_method`. Cuántos planetas ha
  encontrado cada técnica.
- `por_año`: `clasificacion` = `discovery_year`. Descubrimientos por año.
  Excluye planetas sin año.
- `tendencia_acumulada`: `clasificacion` = `discovery_year`, pero `conteo` es el
  **total acumulado** hasta ese año (`sum(count(*)) over (order by
  discovery_year)`), no el conteo de ese año. Es la curva de crecimiento
  histórico. Excluye planetas sin año.
- `por_discovery_era`: `clasificacion` = `discovery_era` (Pre-Kepler / Era
  Kepler / Era TESS / Desconocido).

`discovery_year` va casteado a `varchar` en las dos categorías por año: el
`UNION ALL` obliga a que la columna tenga un solo tipo, y `discovery_method` y
`discovery_era` ya son texto. Al leerlo desde la página, el año viene como
string.

### mart_habitability_by_spectral_type

Cruce de tipo espectral de la estrella contra habitabilidad del planeta. Pensado
para un heatmap o barras agrupadas.

- **Grano:** una combinación (`spectral_type`, `habitability`) por fila
- **Filas:** hasta 32 (8 tipos espectrales × 4 clases de habitabilidad), solo
  las combinaciones que existen

| columna       | tipo   | descripción                          |
|---------------|--------|--------------------------------------|
| spectral_type | string | Tipo espectral Morgan-Keenan         |
| habitability  | string | Posición vs. zona habitable          |
| conteo        | int    | Nº de planetas en esa combinación    |

No es el patrón `clasificacion`/`categoria`: al cruzar dos dimensiones, cada una
se queda con su nombre real.

---

## Proyección

### mart_position

Posición de cada planeta, para el mapa 3D y el histograma de distancia. A
diferencia de los rankings y las distribuciones, no agrega ni recorta: es
`mart_planets` proyectado a solo las columnas que necesita un gráfico de
posición, fila por planeta.

- **Grano:** un planeta por fila
- **Filas:** todas las que tengan las cinco columnas completas — no hay
  `categoria` ni tope de 10, a diferencia de los patrones de arriba.
- Se descartan los planetas con `ra_deg`, `dec_deg`, `distance_pc`,
  `planet_name` o `star_name` nulos — alcanza con que falte uno solo de los
  cinco para que la fila entera caiga. En la práctica el único filtro que
  pesa es `distance_pc`: `ra_deg`/`dec_deg`/`planet_name`/`star_name` casi
  no tienen nulos, así que la brecha entre `mart_position` y el total real
  de `mart_planets` es chica (del orden de las pocas decenas de filas), pero
  no cero.

| columna     | tipo   | descripción                          |
|-------------|--------|---------------------------------------|
| ra_deg      | float  | Ascensión recta [grados decimales]    |
| dec_deg     | float  | Declinación [grados decimales]        |
| distance_pc | float  | Distancia al sistema [pc]             |
| planet_name | string | Nombre del planeta                    |
| star_name   | string | Estrella anfitriona                   |

Ojo: como filtra por `distance_pc` (y por ra/dec) igual que `mart_distance`,
`count(*)` sobre este mart **no** es el total de exoplanetas confirmados —
es un subconjunto. Para el total real conviene sumar `conteo` sobre
`mart_discovery_distribution` con `categoria = 'por_metodo'`, que agrupa
sobre `mart_planets` entero sin filtrar por posición.

---

## Tests

Los tests viven en `exoplanets/models/marts/schema.yml`. La pauta es:

- `not_null` en las claves y en los conteos.
- `accepted_values` en cada `categoria`, que actúa de contrato con la página: si
  alguien añade un `UNION ALL` con una categoría nueva y no la declara, el test
  falla.

Dos huecos actuales:

- `mart_size_distribution` no está en `schema.yml`, así que su `categoria`
  (`por_tipo_planeta`) no tiene test de `accepted_values`.
- `mart_size` tiene `not_null` en `planet_radius_earth` pero, a diferencia de
  `mart_distance`, no filtra los nulos en el SQL. El test pasa porque el motor
  ordena los nulos al final; es una dependencia implícita del orden de nulos.
