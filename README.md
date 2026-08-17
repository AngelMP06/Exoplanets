# 🪐 Exoplanets

Pipeline de datos end-to-end sobre los ~6,300 exoplanetas confirmados del
[NASA Exoplanet Archive](https://exoplanetarchive.ipac.caltech.edu/): extracción,
almacenamiento en la nube, transformación con dbt, exposición vía API y
visualización interactiva.

Proyecto de portfolio construido para practicar ingeniería de datos de end to end, no solo el pipeline, sino también las decisiones de arquitectura,
trade-offs, testing y despliegue que lo rodean.

![Python](https://img.shields.io/badge/Python-3.11-blue)
![dbt](https://img.shields.io/badge/dbt--duckdb-FF694B)
![FastAPI](https://img.shields.io/badge/FastAPI-009688)
![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B)
![AWS S3](https://img.shields.io/badge/AWS-S3-FF9900)

**🔗 API en vivo (Swagger):** https://exoplanets-uiu5.onrender.com/docs

**🔗 Dashboard:** https://exoplanets-l3t6uag3hps7ccehr24cz5.streamlit.app/

> ⚠️ **Sobre el cold start:** tanto la API (Render) como el frontend (Streamlit
> Community Cloud) corren en tier gratuito y se "duermen" tras inactividad
> (~15 min la API, ~12h el frontend). La primera carga puede tardar 30-60
> segundos mientras el contenedor entero de la API vuelve a levantar (la
> descarga del `.duckdb` en sí es rápida, pesa solo 9 MB).

---

## Índice

1. [Descripción general](#1-descripción-general)
2. [Arquitectura](#2-arquitectura)
3. [Stack tecnológico](#3-stack-tecnológico)
4. [Modelo de datos](#4-modelo-de-datos)
5. [Testing y CI/CD](#5-testing-y-cicd)
6. [Despliegue](#6-despliegue)
7. [Cómo correrlo en local](#7-cómo-correrlo-en-local)
8. [Estructura del repositorio](#8-estructura-del-repositorio)
9. [Qué sigue (v2)](#9-qué-sigue-v2)

---

## 1. Descripción general

Los exoplanetas confirmados que conocemos no son una muestra representativa
del universo — son los que nuestra tecnología actual pudo detectar. Ese sesgo
de observación aparece una y otra vez en los datos (concentración en
detecciones cercanas, dominancia del método de tránsito, picos de
confirmación en años puntuales) y es el hilo conductor del análisis que
expone el dashboard.

El proyecto cubre el stack completo:

```
NASA API → extract (Python) → S3 (raw) → dbt/DuckDB (transform) →
S3 (snapshot) → FastAPI → Streamlit
```

Cada capa tiene su propia justificación técnica, son decisiones tomadas una por una a lo largo del proyecto.

## 2. Arquitectura

**Flujo, paso a paso:**

1. **Extracción** — `extract.py` llama a la API TAP de NASA (tabla
   `pscomppars`), con manejo de errores y reintentos ante fallos de red.
2. **Raw a S3** — los datos se guardan primero como Parquet local (se valida
   que todo funcione antes de tocar AWS), luego se suben a S3 con un usuario
   IAM de permisos mínimos (`exoplanetas_pipeline`).
3. **Transformación** — dbt-duckdb lee ese Parquet como source y lo procesa
   en dos capas: `staging` (limpieza, tipado, renombrado) → `marts`
   (columnas calculadas, clasificaciones, agregaciones). Corre tests de
   `not_null`, `unique`, `relationships` y `accepted_values` en cada build.
4. **Snapshot a S3** — `dbt build` deja un `.duckdb` completo y
   materializado, que se sube a S3 como snapshot único.
5. **API** — FastAPI descarga ese `.duckdb` al arrancar (usando `lifespan`)
   y sirve todo desde el archivo local, con un usuario IAM de solo lectura
   (`exoplanetas_api`) y conexiones DuckDB `read_only=True` por request.
6. **Frontend** — Streamlit consume la API vía `requests`, cachea las
   respuestas (`st.cache_data(ttl=600)`) y arma la página con Plotly:
   gráficos de distribución, tablas de ranking filtrables y un mapa 3D de
   posición estelar.
7. **Orquestación** — todo el pipeline de extracción/transformación corre
   diario vía GitHub Actions (`schedule: cron`).

## 3. Stack tecnológico

| Capa | Herramienta | Rol |
|---|---|---|
| Extracción | Python (`requests`) | Llamadas a la API TAP de NASA con retry logic |
| Almacenamiento crudo | AWS S3 + IAM de permisos mínimos | Parquet intermedio entre extracción y transformación |
| Transformación | dbt-duckdb | Capas staging → marts, tests declarativos |
| Warehouse | DuckDB | Motor analítico local, cero infraestructura que mantener |
| Orquestación | GitHub Actions (`cron`) | Scheduling diario, sin dependencias entre tareas que justifiquen algo más pesado |
| API | FastAPI | Snapshot API de solo lectura sobre el `.duckdb` |
| Frontend | Streamlit + Plotly | Reporte interactivo con gráficos, rankings filtrables y mapa 3D |
| CI | GitHub Actions | Tests de dbt y de la API en cada push relevante |
| Deploy API | Render (free tier) | Proceso persistente compatible con `lifespan`|
| Deploy frontend | Streamlit Community Cloud | El umbral de inactividad de Streamlit es más generoso que Render (~12h vs 15min) |

## 4. Modelo de datos

Documentado en detalle en [`schema.md`](schema.md) (capas raw → staging →
marts) y [`marts.md`](marts.md) (marts de presentación que consume la
página). En resumen:

- **`raw.planets`** — un planeta por fila, tal cual responde la API de NASA.
- **`stg_planets`** — mismo grano, columnas renombradas y tipadas.
- **`mart_planets`** — tabla base con clasificaciones calculadas: tipo de
  planeta por radio, posición respecto a la zona habitable, clase térmica
  T-PHC, tipo espectral Morgan-Keenan, era de descubrimiento.
- **Marts de presentación** — derivan todos de `mart_planets`, sin cálculo
  adicional del lado de la página. Siguen tres patrones: **ranking**
  (`mart_size`, `mart_distance`, `mart_system`, `mart_habitability`),
  **distribución** (`mart_size_distribution`, `mart_discovery_distribution`,
  `mart_habitability_distribution`, `mart_system_distribution`) y
  **proyección** (`mart_position`, fila por planeta sin agregar, para el
  mapa 3D y el histograma de distancia).

La API expone 13 endpoints sobre estos marts, con parámetros para filtrar
por `categoria` donde aplica.

## 5. Testing y CI/CD

- **dbt tests**: `not_null` en claves y conteos, `accepted_values` en cada
  columna `categoria` (actúa como contrato — si se agrega un `UNION ALL`
  con una categoría nueva sin declararla, el test falla).
- **API tests**: `pytest` contra un fixture generado con `duckdb ATTACH`
  (copia una muestra representativa del `.duckdb` real, con sampling por
  categoría donde corresponde, sin depender de pandas — no se instaló una
  librería tan grande solo para armar diccionarios de respuesta).
- **Red de seguridad en cada publicación**: antes de subir un `.duckdb`
  transformado a S3, corren los tests. Si algo falla, ese deployment no se
  completa y la API sigue sirviendo el snapshot anterior — la prioridad es
  nunca servir datos corruptos, aunque signifique servir datos algo
  desactualizados. Un fallo notifica por correo.
- **Tres workflows de GitHub Actions**: extracción + transformación diaria
  (`cron`), uno dedicado a rematerializar y republicar el snapshot de forma
  independiente (sin esperar al cron diario — útil al agregar marts
  nuevos), y tests de la API (`test-api.yml`, disparado en push/PR con
  `paths: ['api/**']` más `workflow_dispatch`).

## 6. Despliegue

| Componente | Plataforma | Notas |
|---|---|---|
| API | Render (free tier) | Variables de entorno como secrets en el dashboard; cold start 30-60s |
| Frontend | Streamlit Community Cloud | Secrets vía panel (claves de nivel raíz, expuestas también como env vars) |
| Pipeline | GitHub Actions | Credenciales en GitHub Actions Secrets |

Ambos deploys se redespliegan automáticamente con cada push a la rama
principal.

## 7. Cómo correrlo en local

El proyecto usa tres entornos virtuales aislados (dbt, API, frontend), cada
uno con su propio `.env` — reflejando cómo se despliega cada pieza por
separado.

```powershell
# Pipeline + dbt
python -m venv .venv-dbt
.venv-dbt\Scripts\activate
pip install -r requirements.txt
dbt run
dbt test

# API
cd api
python -m venv .venv-api
.venv-api\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload

# Frontend
cd streamlit
python -m venv .venv-streamlit
.venv-streamlit\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

Cada carpeta (`api/`, `streamlit/`) requiere su propio `.env` con las
credenciales correspondientes — ver `.env.example` en cada una (o el
detalle de variables en `decisions.md`).

## 8. Estructura del repositorio

```
Exoplanets/
├── api/                  # FastAPI: main.py, tests/ (con fixtures propias)
├── streamlit/             # Frontend: app.py, assets/
├── exoplanets/             # Proyecto dbt: models/staging, models/marts
├── notebooks/             # EDA.ipynb
├── src/                  # Módulos del pipeline de extracción
├── data/                 # Parquet local intermedio (no versionado)
├── logs/                 # Logs del pipeline
├── ADR/                  # Architecture Decision Records
├── .github/workflows/     # CI: pipeline + tests de API
├── main.py                # Entry point del pipeline
├── schema.md               # Documentación de capas raw/staging/marts
├── marts.md                # Documentación de marts de presentación
├── plan.md                 # Roadmap del proyecto
├── DEVLOG.md               # Bitácora de desarrollo
└── README.md
```

## 9. Qué sigue (v2)

Ideas capturadas pero **no implementadas** en esta versión — viven en una
rama aparte, no se mezclan con el alcance de v1:

- Segunda fuente de datos relacionada (p. ej. NASA APOD), donde usaría Airflow.
- Migración de DuckDB a Postgres/RDS.
- IAM + S3 particionado por fecha + Secrets Manager.
- Dockerización de la API y el pipeline.
- Migración de la orquestación de `cron` a Airflow.

---

## Autor

**Angel** — [GitHub](https://github.com/angelmp06) — [LinkedIn](https://www.linkedin.com/in/angel-montes-palma/)

Licencia: ver [`LICENSE`](LICENSE).