import streamlit as st
import os
import requests
import pandas as pd
import plotly.express as px
import matplotlib.pyplot as plt

from dotenv import load_dotenv
load_dotenv()

st.set_page_config(layout="wide")

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

ORDEN_HABITABILIDAD = ["Zona habitable", "Muy cerca", "Muy lejos", "Desconocido"]

ORDEN_TEMP_HABITABILIDAD = [
    "hP - hypopsychroplanet", "P - psychroplanet", "M - mesoplanet",
    "T - thermoplanet", "hT - hyperthermoplanet", "Desconocido",
]

# Un solo azul: con una sola serie el color no codifica nada, así que no hay
# leyenda que leer.
COLOR_SERIE = "#2a78d6"

# Rangos de las categorías que clasifican por un valor numérico (ver schema.md).
# Se muestran debajo de su gráfico correspondiente para que quede claro qué
# significa cada categoría.
RANGO_TAMANOS = (
    "Mercury-like: < 0.5 · Mini-Earth: 0.5–0.8 · Earth-like: 0.8–1.2 · "
    "Super-Earth: 1.2–1.75 · Transition: 1.75–2.1 · Sub-Neptune: 2.1–4 · "
    "Neptune-like: 4–8 · Jovian-like: > 8 (radios terrestres)"
)
RANGO_TEMP_HABITABILIDAD = (
    "hP - hypopsychroplanet: < −50 °C · P - psychroplanet: −50 a 0 °C · "
    "M - mesoplanet: 0 a 50 °C · T - thermoplanet: 50 a 100 °C · "
    "hT - hyperthermoplanet: ≥ 100 °C"
)
RANGO_DISCOVERY_ERA = "Pre-Kepler: antes de 2009 · Era Kepler: 2009–2017 · Era TESS: desde 2018"


def hay_datos(df, mensaje="Sin datos para esta selección."):
    if df.empty:
        st.info(mensaje)
        return False
    return True


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
# Título y descripción
# ============================================

st.title("Exoplanetas")

df_position = pd.DataFrame(fetch("/position"))
num_exoplanetas = len(df_position)

st.markdown(
    f"Los exoplanetas son planetas que pertenecen a otro sistema solar, orbitan "
    f"una estrella que no es nuestro sol, hasta el momento se han confirmado "
    f"**{num_exoplanetas}** exoplanetas, lo cual es un número pequeño comparado "
    f"con las aproximadamente 100 mil estrellas en nuestra galaxia, lo que da a "
    f"suponer que aún hay una exorbitante cantidad de exoplanetas esperando ser "
    f"descubiertos."
)

# ============================================
# Descubrimiento
# ============================================

st.header("Exoplanetas por descubrimiento")

col_tiempo, col_metodo = st.columns(2)

with col_tiempo:
    st.markdown(
        "Los primeros 2 exoplanetas fueron descubiertos en 1992, dichos planetas "
        "orbitaban un púlsar llamado Lich. Este fue el inicio de la búsqueda de "
        "más exoplanetas en nuestra galaxia.\n\n"
        "Vemos que entre los años 2014 y 2016 se hicieron el descubrimiento de "
        "varios exoplanetas, sin embargo, no es que esos exoplanetas se hayan "
        "detectado en esos años, se detectaron en años anteriores, pero "
        "tuvieron que esperar hasta esos años para, mediante estudios "
        "científicos, confirmar su existencia.\n\n"
        "Fue gracias al telescopio Kepler de la NASA, que publicó enormes "
        "lotes de datos espaciales acumulados e introdujo métodos avanzados de "
        "verificación estadística que confirmaron miles de candidatos a "
        "planetas a la vez, por eso tiene la mayor cantidad de descubrimientos."
    )

    categoria_descubrimiento = st.selectbox(
        "Distribución por descubrimiento",
        ["por_año", "tendencia_acumulada", "por_discovery_era"],
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
        elif categoria_descubrimiento == "por_año":
            df_descubrimiento = df_descubrimiento.sort_values("clasificacion")
            fig_descubrimiento = grafico_distribucion(
                df_descubrimiento,
                orden=list(df_descubrimiento["clasificacion"]),
                etiquetas={"clasificacion": "Año", "conteo": "Nº de planetas"},
            )
        else:  # por_discovery_era
            fig_descubrimiento = grafico_distribucion(
                df_descubrimiento,
                orden=list(df_descubrimiento["clasificacion"]),
                etiquetas={"clasificacion": "Era", "conteo": "Nº de planetas"},
            )

        st.plotly_chart(fig_descubrimiento, use_container_width=True)

        if categoria_descubrimiento == "por_discovery_era":
            st.caption(RANGO_DISCOVERY_ERA)

with col_metodo:
    st.markdown(
        "Indiscutiblemente, el mejor método para detectar exoplanetas es el "
        "transitorio, el cual consiste en observar el valor de la luminosidad "
        "de una estrella para ver si es que disminuye debido a que un planeta "
        "se ha puesto entre dicha estrella y el telescopio que la observa.\n\n"
        "El segundo método que descubrió más exoplanetas es el de la velocidad "
        "radial, este detecta el \"bamboleo\" periódico de una estrella debido "
        "a que está siendo afectada por la gravedad de un planeta que la "
        "orbita, ya que ambos orbitan un centro de gravedad común.\n\n"
        "El tercer método es de microlente gravitacional, este consiste en "
        "detectar cuando la gravedad de un planeta que pasa frente a una "
        "estrella y curva su luz, esto añade un pico de luz de extra brillo "
        "que permite medir su masa y posición. Este método es utilizado para "
        "detectar planetas lejanos que otros métodos no pueden detectar."
    )

    data_metodo = fetch("/discovery_distribution", params={"categoria": "por_metodo"})
    df_metodo = pd.DataFrame(data_metodo)

    if hay_datos(df_metodo):
        df_metodo = df_metodo.drop(columns=["categoria"]).sort_values(
            "conteo", ascending=False
        )
        fig_metodo = grafico_distribucion(
            df_metodo,
            orden=list(df_metodo["clasificacion"]),
            etiquetas={"clasificacion": "Método", "conteo": "Nº de planetas"},
        )
        st.plotly_chart(fig_metodo, use_container_width=True)

# ============================================
# Distancia
# ============================================

st.header("Exoplanetas por distancia")

col_ranking_distancia, col_dist_distancia = st.columns(2)

with col_ranking_distancia:
    st.markdown(
        "Los planetas más distantes encontrados están a 8500 pc = 27722 años "
        "luz de distancia, este es por ahora el límite de hacia donde podemos "
        "ver. Y los más cercanos se encuentran a 1.3 pc = 4.2 años luz, ambas "
        "se encuentran orbitando la estrella próxima centauri, la estrella "
        "más cercana a nuestro sol."
    )

    data_mas_distante = fetch("/distance", params={"categoria": "mas_distante"})
    df_mas_distante = pd.DataFrame(data_mas_distante)
    data_menos_distante = fetch("/distance", params={"categoria": "menos_distante"})
    df_menos_distante = pd.DataFrame(data_menos_distante)

    col_mas_distante, col_menos_distante = st.columns(2)

    with col_mas_distante:
        st.caption("Más distantes")
        if hay_datos(df_mas_distante):
            st.dataframe(
                df_mas_distante.drop(columns=["categoria"]), use_container_width=True
            )

    with col_menos_distante:
        st.caption("Más cercanos")
        if hay_datos(df_menos_distante):
            st.dataframe(
                df_menos_distante.drop(columns=["categoria"]), use_container_width=True
            )

with col_dist_distancia:
    st.markdown(
        "Esta gráfica es muy importante, por que nos indica que la mayoría de "
        "exoplanetas descubiertos se encuentran cerca a nosotros, debido a que "
        "son los más fáciles de comprobar, esto nos indicaría que aún hay "
        "muchos planetas por descubrir los cuales se encuentran en estrellas "
        "más distantes. ¿Cuánto nos estaremos perdiendo?"
    )

    if hay_datos(df_position):
        fig_distancia, ax_distancia = plt.subplots()
        ax_distancia.hist(df_position["distance_pc"], bins=30, color=COLOR_SERIE)
        ax_distancia.set_xlabel("Distancia [pc]")
        ax_distancia.set_ylabel("Nº de planetas")
        st.pyplot(fig_distancia)

# ============================================
# Tamaño
# ============================================

st.header("Exoplanetas por tamaño")

col_ranking_tamano, col_dist_tamano = st.columns(2)

with col_ranking_tamano:
    st.markdown(
        "El planeta más grande encontrado es un planeta joviano de más de 87 "
        "veces el radio de la tierra, es tan grande que solo su radio ya es "
        "mayor que la distancia entre la tierra y la luna, y es casi 8 veces "
        "el tamaño de Júpiter. El más pequeño encontrado es uno tipo mercurio "
        "tiene casi el 31 % del radio terrestre, es más pequeño que mercurio "
        "que tiene el 38 %."
    )

    data_mas_grande = fetch("/size", params={"categoria": "mas grande"})
    df_mas_grande = pd.DataFrame(data_mas_grande)
    data_mas_pequena = fetch("/size", params={"categoria": "mas pequeña"})
    df_mas_pequena = pd.DataFrame(data_mas_pequena)

    col_mas_grande, col_mas_pequena = st.columns(2)

    with col_mas_grande:
        st.caption("Más grandes")
        if hay_datos(df_mas_grande):
            st.dataframe(
                df_mas_grande.drop(columns=["categoria"]), use_container_width=True
            )

    with col_mas_pequena:
        st.caption("Más pequeños")
        if hay_datos(df_mas_pequena):
            st.dataframe(
                df_mas_pequena.drop(columns=["categoria"]), use_container_width=True
            )

with col_dist_tamano:
    st.markdown(
        "Vemos que los exoplanetas más grandes son los que más se descubren, "
        "siendo que la mayoría de planetas descubiertos caen en la categoría "
        "de sub-neptunianos o jovianos. Esto puede provocar un sesgo, se "
        "podría pensar que la mayoría de planetas que existen son de esos "
        "tipos, pero simplemente esta distribución puede deberse a que los "
        "planetas más grandes son mucho más fáciles de encontrar que los "
        "pequeños."
    )

    data_dist_tamano = fetch("/size_distribution", params={"categoria": "por_tipo_planeta"})
    df_dist_tamano = pd.DataFrame(data_dist_tamano)

    if hay_datos(df_dist_tamano):
        df_dist_tamano = df_dist_tamano[df_dist_tamano["clasificacion"] != "Desconocido"]
        orden_tamano = [c for c in ORDEN_TAMANOS if c != "Desconocido"]
        st.plotly_chart(
            grafico_distribucion(df_dist_tamano, orden=orden_tamano),
            use_container_width=True,
        )
        st.caption(RANGO_TAMANOS)

# ============================================
# Sistema
# ============================================

st.header("Exoplanetas por sistema")

st.markdown(
    "Vemos que la mayoría de sistemas tienen 1 exoplaneta descubierto y con "
    "un máximo de 8 planetas por sistema, al igual que nuestro sistema solar "
    "que también tiene 8 planetas."
)

data_dist_sistema = fetch(
    "/system_distribution", params={"categoria": "distribucion_num_planetas"}
)
df_dist_sistema = pd.DataFrame(data_dist_sistema)

if hay_datos(df_dist_sistema):
    # `clasificacion` es un entero: se ordena numéricamente y después se pasa a
    # texto, para que el eje sea categórico y no deje huecos entre valores.
    df_dist_sistema = df_dist_sistema.sort_values("clasificacion")
    df_dist_sistema["clasificacion"] = df_dist_sistema["clasificacion"].astype(str)
    st.plotly_chart(
        grafico_distribucion(
            df_dist_sistema,
            orden=list(df_dist_sistema["clasificacion"]),
            etiquetas={"clasificacion": "Nº de planetas", "conteo": "Nº de sistemas"},
        ),
        use_container_width=True,
    )

# ============================================
# Habitabilidad
# ============================================

st.header("Exoplanetas por habitabilidad")

col_ranking_hab, col_dist_hab = st.columns(2)

with col_ranking_hab:
    st.markdown(
        "El máximo número de planetas en la zona habitable de un sistema es "
        "de 3 planetas, es mayor a nuestro sistema solar que tiene 2 planetas "
        "en la zona habitable (tierra y marte), esto puede dar indicios de "
        "que es posible la vida en esos sistemas algo que siempre se ha "
        "creído probable."
    )

    data_habitabilidad = fetch("/habitability")
    df_habitabilidad = pd.DataFrame(data_habitabilidad)

    if hay_datos(df_habitabilidad):
        st.dataframe(df_habitabilidad, use_container_width=True)

with col_dist_hab:
    st.markdown(
        "Vemos que la mayoría de planetas encontrados se encuentran cerca de "
        "su estrella anfitriona siendo por lo tanto muy calientes, esto se "
        "muestra en ambas gráficas de distribución, otra vez, al ser planetas "
        "cercanos a sus estrellas, son detectados gracias a que nuestros "
        "métodos siempre toma en cuenta el contraste entre esos planetas y "
        "sus estrellas. Lo que indica que incluso puede haber más planetas en "
        "sus zonas habitables que solamente 3 por sistema a lo más."
    )

    categoria_dist_hab = st.selectbox(
        "Distribución por habitabilidad",
        ["por_habitability", "por_temp_habitability"],
        key="dist_habitabilidad",
    )

    data_dist_hab = fetch(
        "/habitability_distribution", params={"categoria": categoria_dist_hab}
    )
    df_dist_hab = pd.DataFrame(data_dist_hab)

    if hay_datos(df_dist_hab):
        df_dist_hab = df_dist_hab[df_dist_hab["clasificacion"] != "Desconocido"]
        if categoria_dist_hab == "por_habitability":
            orden_hab = [c for c in ORDEN_HABITABILIDAD if c != "Desconocido"]
        else:
            orden_hab = [c for c in ORDEN_TEMP_HABITABILIDAD if c != "Desconocido"]

        st.plotly_chart(
            grafico_distribucion(df_dist_hab, orden=orden_hab),
            use_container_width=True,
        )

        if categoria_dist_hab == "por_temp_habitability":
            st.caption(RANGO_TEMP_HABITABILIDAD)

# ============================================
# Conclusión
# ============================================

st.header("Conclusión")

st.markdown(
    "Todas las gráficas nos mostraron algo contundente, nuestros métodos "
    "para detectar planetas no son suficientes, los planetas más fáciles de "
    "encontrar son aquellos grandes, poco distantes y cercanos a sus "
    "respectivas estrellas, siendo los llamados júpiters calientes los más "
    "comunes. Todo esto generaría un gran sesgo si no se hiciese un análisis "
    "más profundo ¿Cuánto nos estaremos perdiendo? Posiblemente haya más "
    "planetas e incluso asteroides o lunas que no detectamos, posiblemente "
    "cada uno de esos sistemas tienen una gran variedad de cuerpos, al igual "
    "que nuestro sistema solar, pero indetectables con la tecnología actual. "
    "Nos dimos cuenta que recién estamos en pañales cuando hablamos de "
    "detección de exoplanetas, aún falta muchísimo más por mejorar. Ojalá en "
    "un futuro se logre desarrollar más estas técnicas o encontrar nuevas "
    "formas de buscar cuerpos más allá de nuestro sistema solar."
)
