import streamlit as st
import os
import requests
import pandas as pd
import plotly.express as px

from dotenv import load_dotenv
load_dotenv()

st.set_page_config(layout="wide")

st.title("Toda la información de exoplanetas en un solo lugar")

API_BASE_URL = os.getenv("URL")


@st.cache_data(ttl=600)
def fetch(endpoint, params=None):
    r = requests.get(f"{API_BASE_URL}{endpoint}", params=params)
    r.raise_for_status()
    return r.json()


# ============================================
# Órdenes y colores
# ============================================

# El orden de las categorías sale de schema.md, no del orden en que la API
# devuelve las filas (los marts no llevan ORDER BY y la API tampoco).
ORDEN_TAMANOS = [
    "Mercury-like", "Mini-Earth", "Earth-like", "Super-Earth",
    "Transition", "Sub-Neptune", "Neptune-like", "Jovian-like",
    "Desconocido",
]

ORDEN_ESPECTRAL = ["O", "B", "A", "F", "G", "K", "M", "Desconocido"]

ORDEN_HABITABILIDAD = ["Zona habitable", "Muy cerca", "Muy lejos", "Desconocido"]

ORDEN_TEMP_HABITABILIDAD = [
    "hP - hypopsychroplanet", "P - psychroplanet", "M - mesoplanet",
    "T - thermoplanet", "hT - hyperthermoplanet", "Desconocido",
]

# Un solo azul cuando hay una sola serie: el color no codifica nada, así que no
# hay leyenda que leer. Cuando la habitabilidad sí es una serie, el color se fija
# por valor (no por posición) para que un filtro no repinte las barras.
COLOR_SERIE = "#2a78d6"
COLORES_HABITABILIDAD = {
    "Zona habitable": "#1baf7a",
    "Muy cerca": "#eb6834",
    "Muy lejos": "#2a78d6",
    "Desconocido": "#898781",
}


def hay_datos(df, mensaje="Sin datos para esta selección."):
    if df.empty:
        st.info(mensaje)
        return False
    return True


def grafico_ranking(df, columna_valor, columna_etiqueta, ascendente=False, etiquetas=None):
    """Barra horizontal para un top-10. El mart no garantiza el orden de salida,
    así que se ordena aquí; el eje se invierte para dejar al primero arriba."""
    d = df.sort_values(columna_valor, ascending=ascendente)
    fig = px.bar(
        d,
        x=columna_valor,
        y=columna_etiqueta,
        orientation="h",
        labels=etiquetas or {},
        category_orders={columna_etiqueta: list(d[columna_etiqueta])},
    )
    fig.update_traces(marker_color=COLOR_SERIE)
    fig.update_yaxes(autorange="reversed", title=None)
    fig.update_layout(height=420, margin=dict(l=0, r=0, t=10, b=0))
    return fig


def grafico_distribucion(df, orden=None, etiquetas=None, altura=420):
    """Barra vertical para el patrón clasificacion / conteo."""
    fig = px.bar(
        df,
        x="clasificacion",
        y="conteo",
        labels=etiquetas or {"clasificacion": "", "conteo": "Nº de planetas"},
        category_orders={"clasificacion": orden} if orden else None,
    )
    fig.update_traces(marker_color=COLOR_SERIE)
    fig.update_layout(height=altura, margin=dict(l=0, r=0, t=10, b=0))
    return fig


# ============================================
# Clasificación de exoplanetas por tamaño
# ============================================

st.header("Exoplanetas por tamaño")

categoria_tamano = st.selectbox(
    "Ranking por tamaño",
    ["mas grande", "mas pequeña", "mas grande por sistema"],
    key="rank_tamano",
)

data_ranking = fetch("/size", params={"categoria": categoria_tamano})
df_ranking = pd.DataFrame(data_ranking)

col_tabla_tamano, col_grafico_tamano = st.columns(2)

with col_tabla_tamano:
    st.write("Ranking de exoplanetas por tamaño")
    if hay_datos(df_ranking):
        st.dataframe(df_ranking.drop(columns=["categoria"]), use_container_width=True)

with col_grafico_tamano:
    st.write("Radio de cada planeta del ranking, en radios terrestres")
    if hay_datos(df_ranking):
        st.plotly_chart(
            grafico_ranking(
                df_ranking,
                "planet_radius_earth",
                "planet_name",
                ascendente=(categoria_tamano == "mas pequeña"),
                etiquetas={"planet_radius_earth": "Radio [radios terrestres]"},
            ),
            use_container_width=True,
        )

st.write("Cuántos planetas hay de cada familia por radio")

data_dist_tamano = fetch("/size_distribution", params={"categoria": "por_tipo_planeta"})
df_dist_tamano = pd.DataFrame(data_dist_tamano)

if hay_datos(df_dist_tamano):
    st.plotly_chart(
        grafico_distribucion(df_dist_tamano, orden=ORDEN_TAMANOS),
        use_container_width=True,
    )

# ============================================
# Clasificación de exoplanetas por distancia
# ============================================

st.header("Exoplanetas por distancia")

categoria_distancia = st.selectbox(
    "Ranking por distancia",
    ["mas_distante", "menos_distante"],
    key="rank_distancia",
)

data_distancia = fetch("/distance", params={"categoria": categoria_distancia})
df_distancia = pd.DataFrame(data_distancia)

col_tabla_distancia, col_grafico_distancia = st.columns(2)

with col_tabla_distancia:
    st.write("Ranking de exoplanetas por distancia")
    if hay_datos(df_distancia):
        st.dataframe(df_distancia.drop(columns=["categoria"]), use_container_width=True)

with col_grafico_distancia:
    st.write("Distancia del sistema, en parsecs")
    if hay_datos(df_distancia):
        st.plotly_chart(
            grafico_ranking(
                df_distancia,
                "distance_pc",
                "planet_name",
                ascendente=(categoria_distancia == "menos_distante"),
                etiquetas={"distance_pc": "Distancia [pc]"},
            ),
            use_container_width=True,
        )

# ============================================
# Clasificación de exoplanetas por sistema
# ============================================

st.header("Exoplanetas por sistema")

categoria_sistema = st.selectbox(
    "Ranking por sistema",
    ["top_planetas_por_sistema", "top_lunas_por_sistema"],
    key="rank_sistema",
)

data_sistema = fetch("/system", params={"categoria": categoria_sistema})
df_sistema = pd.DataFrame(data_sistema)

# `valor` es num_planets o num_moons según la categoría; el mart no lo renombra.
etiqueta_sistema = (
    "Nº de planetas" if categoria_sistema == "top_planetas_por_sistema" else "Nº de lunas"
)

col_tabla_sistema, col_grafico_sistema = st.columns(2)

with col_tabla_sistema:
    st.write("Ranking de sistemas más poblados")
    if hay_datos(df_sistema):
        st.dataframe(df_sistema.drop(columns=["categoria"]), use_container_width=True)

with col_grafico_sistema:
    st.write(etiqueta_sistema + " de cada sistema del ranking")
    if hay_datos(df_sistema):
        st.plotly_chart(
            grafico_ranking(
                df_sistema,
                "valor",
                "star_name",
                etiquetas={"valor": etiqueta_sistema},
            ),
            use_container_width=True,
        )

categoria_dist_sistema = st.selectbox(
    "Distribución por sistema",
    ["distribucion_num_planetas", "distribucion_num_lunas"],
    key="dist_sistema",
)

st.write("Cuántos sistemas hay con cada número de planetas o de lunas")

data_dist_sistema = fetch("/system_distribution", params={"categoria": categoria_dist_sistema})
df_dist_sistema = pd.DataFrame(data_dist_sistema)

if hay_datos(df_dist_sistema):
    # Aquí `clasificacion` es un entero: se ordena numéricamente y después se
    # pasa a texto, para que el eje sea categórico y no deje huecos entre valores.
    df_dist_sistema = df_dist_sistema.sort_values("clasificacion")
    df_dist_sistema["clasificacion"] = df_dist_sistema["clasificacion"].astype(str)
    st.plotly_chart(
        grafico_distribucion(
            df_dist_sistema,
            orden=list(df_dist_sistema["clasificacion"]),
            etiquetas={
                "clasificacion": (
                    "Nº de planetas"
                    if categoria_dist_sistema == "distribucion_num_planetas"
                    else "Nº de lunas"
                ),
                "conteo": "Nº de sistemas",
            },
        ),
        use_container_width=True,
    )

# ============================================
# Clasificación de exoplanetas por descubrimiento
# ============================================

st.header("Exoplanetas por descubrimiento")

categoria_descubrimiento = st.selectbox(
    "Distribución por descubrimiento",
    ["por_metodo", "por_año", "tendencia_acumulada", "por_discovery_era"],
    key="dist_descubrimiento",
)

data_descubrimiento = fetch(
    "/discovery_distribution", params={"categoria": categoria_descubrimiento}
)
df_descubrimiento = pd.DataFrame(data_descubrimiento)

if hay_datos(df_descubrimiento):
    df_descubrimiento = df_descubrimiento.drop(columns=["categoria"])

    if categoria_descubrimiento == "tendencia_acumulada":
        # `conteo` ya viene acumulado desde el mart: es una curva, no barras.
        st.write("Total acumulado de exoplanetas descubiertos hasta cada año")
        df_descubrimiento = df_descubrimiento.sort_values("clasificacion")
        fig_descubrimiento = px.line(
            df_descubrimiento,
            x="clasificacion",
            y="conteo",
            markers=True,
            labels={"clasificacion": "Año", "conteo": "Total acumulado"},
        )
        fig_descubrimiento.update_traces(line_color=COLOR_SERIE, line_width=2)
        fig_descubrimiento.update_layout(height=420, margin=dict(l=0, r=0, t=10, b=0))
    else:
        if categoria_descubrimiento == "por_metodo":
            # Sin orden natural: se ordena por magnitud.
            st.write("Cuántos exoplanetas ha encontrado cada técnica")
            df_descubrimiento = df_descubrimiento.sort_values("conteo", ascending=False)
            etiqueta_x = "Método"
        elif categoria_descubrimiento == "por_año":
            st.write("Exoplanetas descubiertos cada año")
            df_descubrimiento = df_descubrimiento.sort_values("clasificacion")
            etiqueta_x = "Año"
        else:
            st.write("Exoplanetas descubiertos en cada era")
            etiqueta_x = "Era"

        fig_descubrimiento = grafico_distribucion(
            df_descubrimiento,
            orden=list(df_descubrimiento["clasificacion"]),
            etiquetas={"clasificacion": etiqueta_x, "conteo": "Nº de planetas"},
        )

    st.plotly_chart(fig_descubrimiento, use_container_width=True)

# ============================================
# Clasificación de exoplanetas por habitabilidad
# ============================================

st.header("Exoplanetas por habitabilidad")

data_habitabilidad = fetch("/habitability")
df_habitabilidad = pd.DataFrame(data_habitabilidad)

col_tabla_hab, col_grafico_hab = st.columns(2)

with col_tabla_hab:
    st.write("Ranking de estrellas por número de planetas habitables")
    if hay_datos(df_habitabilidad):
        st.dataframe(df_habitabilidad, use_container_width=True)

with col_grafico_hab:
    st.write("Planetas en zona habitable por estrella")
    if hay_datos(df_habitabilidad):
        st.plotly_chart(
            grafico_ranking(
                df_habitabilidad,
                "planetas_habitables",
                "star_name",
                etiquetas={"planetas_habitables": "Planetas en zona habitable"},
            ),
            use_container_width=True,
        )

col_dist_hab, col_espectral = st.columns(2)

with col_dist_hab:
    categoria_dist_hab = st.selectbox(
        "Distribución por habitabilidad",
        ["por_habitability", "por_temp_habitability"],
        key="dist_habitabilidad",
    )

    st.write("Cuántos planetas hay en cada clase de habitabilidad")

    data_dist_hab = fetch(
        "/habitability_distribution", params={"categoria": categoria_dist_hab}
    )
    df_dist_hab = pd.DataFrame(data_dist_hab)

    if hay_datos(df_dist_hab):
        orden_hab = (
            ORDEN_HABITABILIDAD
            if categoria_dist_hab == "por_habitability"
            else ORDEN_TEMP_HABITABILIDAD
        )
        st.plotly_chart(
            grafico_distribucion(df_dist_hab, orden=orden_hab, altura=500),
            use_container_width=True,
        )

with col_espectral:
    st.write("Habitabilidad de los planetas según el tipo espectral de su estrella")

    data_espectral = fetch("/habitability_by_spectral_type")
    df_espectral = pd.DataFrame(data_espectral)

    if hay_datos(df_espectral):
        fig_espectral = px.bar(
            df_espectral,
            x="spectral_type",
            y="conteo",
            color="habitability",
            barmode="group",
            labels={
                "spectral_type": "Tipo espectral",
                "conteo": "Nº de planetas",
                "habitability": "Habitabilidad",
            },
            category_orders={
                "spectral_type": ORDEN_ESPECTRAL,
                "habitability": ORDEN_HABITABILIDAD,
            },
            color_discrete_map=COLORES_HABITABILIDAD,
        )
        fig_espectral.update_layout(height=500, margin=dict(l=0, r=0, t=10, b=0))
        st.plotly_chart(fig_espectral, use_container_width=True)
