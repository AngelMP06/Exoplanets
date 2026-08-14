import streamlit as st
import os
import requests
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import matplotlib.pyplot as plt

from dotenv import load_dotenv
load_dotenv()

st.set_page_config(layout="wide", page_title="Exoplanetas", page_icon="🪐")

API_BASE_URL = os.getenv("URL")


@st.cache_data(ttl=600)
def fetch(endpoint, params=None):
    r = requests.get(f"{API_BASE_URL}{endpoint}", params=params)
    r.raise_for_status()
    return r.json()


# ============================================
# Órdenes, colores y rangos
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

# Rampa secuencial de un solo hue (azul, claro→oscuro) para codificar distancia
# en el mapa 3D: mismo criterio de color que el resto de la página.
RAMPA_SECUENCIAL = ["#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"]
# El Sol se marca aparte, con el color categórico 2 (naranja) para distinguirlo
# de la rampa secuencial que usan las estrellas.
COLOR_SOL = "#eb6834"
# Plano de la eclíptica: amarillo tenue (categórico 4), como referencia visual.
COLOR_ECLIPTICA = "#eda100"
# Oblicuidad de la eclíptica respecto al ecuador celeste (época J2000).
OBLICUIDAD_ECLIPTICA = np.radians(23.4393)
# Plano de la Vía Láctea: gris tenue (el mismo gris de ejes/etiquetas del
# resto de la página), como referencia de orientación, no a escala real.
COLOR_VIA_LACTEA = "#c3c2b7"
# Polo galáctico norte en coordenadas ecuatoriales J2000 (define la
# orientación del plano de la Vía Láctea).
RA_POLO_GALACTICO = np.radians(192.859508)
DEC_POLO_GALACTICO = np.radians(27.128336)


def hay_datos(df, mensaje="Sin datos para esta selección."):
    if df.empty:
        st.info(mensaje)
        return False
    return True


def grafico_distribucion(df, orden=None, etiquetas=None, altura=380):
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


def coordenadas_cartesianas(df):
    """RA/Dec/distancia (coordenadas esféricas centradas en el Sol) a x/y/z en pc."""
    ra = np.radians(df["ra_deg"])
    dec = np.radians(df["dec_deg"])
    d = df["distance_pc"]
    return df.assign(
        x=d * np.cos(dec) * np.cos(ra),
        y=d * np.cos(dec) * np.sin(ra),
        z=d * np.sin(dec),
    )


def grafico_mapa_3d(df, altura=550):
    d = coordenadas_cartesianas(df)
    fig = px.scatter_3d(
        d,
        x="x", y="y", z="z",
        color="distance_pc",
        color_continuous_scale=RAMPA_SECUENCIAL,
        hover_name="planet_name",
        hover_data={"star_name": True, "distance_pc": ":.1f", "x": False, "y": False, "z": False},
        labels={"distance_pc": "Distancia [pc]"},
    )
    fig.update_traces(marker=dict(size=2.5, opacity=0.75))

    alcance = max(d["x"].abs().max(), d["y"].abs().max(), d["z"].abs().max())

    # Plano de la eclíptica: mismo plano x-y equinoccial girado por la
    # oblicuidad respecto al ecuador celeste (z = y * tan(oblicuidad)).
    xs = np.array([-alcance, alcance])
    xx, yy = np.meshgrid(xs, xs)
    zz = yy * np.tan(OBLICUIDAD_ECLIPTICA)
    fig.add_trace(go.Surface(
        x=xx, y=yy, z=zz,
        colorscale=[[0, COLOR_ECLIPTICA], [1, COLOR_ECLIPTICA]],
        showscale=False,
        opacity=0.15,
        hoverinfo="skip",
        showlegend=False,
    ))

    # Plano de la Vía Láctea: perpendicular a la dirección del polo galáctico
    # norte. No hay un eje compartido con el sistema ecuatorial como en la
    # eclíptica, así que se arma una base ortonormal (u, v) del plano a partir
    # de su normal y se genera la malla en esa base.
    normal_galactico = np.array([
        np.cos(DEC_POLO_GALACTICO) * np.cos(RA_POLO_GALACTICO),
        np.cos(DEC_POLO_GALACTICO) * np.sin(RA_POLO_GALACTICO),
        np.sin(DEC_POLO_GALACTICO),
    ])
    ayuda = np.array([0.0, 0.0, 1.0]) if abs(normal_galactico[2]) < 0.9 else np.array([1.0, 0.0, 0.0])
    u = np.cross(ayuda, normal_galactico)
    u /= np.linalg.norm(u)
    v = np.cross(normal_galactico, u)

    ss, tt = np.meshgrid(xs, xs)
    fig.add_trace(go.Surface(
        x=ss * u[0] + tt * v[0],
        y=ss * u[1] + tt * v[1],
        z=ss * u[2] + tt * v[2],
        colorscale=[[0, COLOR_VIA_LACTEA], [1, COLOR_VIA_LACTEA]],
        showscale=False,
        opacity=0.15,
        hoverinfo="skip",
        showlegend=False,
    ))

    fig.add_trace(go.Scatter3d(
        x=[0], y=[0], z=[0],
        mode="markers+text",
        marker=dict(size=6, color=COLOR_SOL, symbol="diamond"),
        text=["Sol"],
        textposition="top center",
        name="Sol (nosotros)",
        hoverinfo="name",
    ))
    fig.update_layout(
        height=altura,
        margin=dict(l=0, r=0, t=10, b=0),
        scene=dict(xaxis_title="X [pc]", yaxis_title="Y [pc]", zaxis_title="Z [pc]"),
        legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01),
    )
    return fig


# ============================================
# Encabezado
# ============================================

st.title("Exoplanetas")

df_position = pd.DataFrame(fetch("/position"))
num_exoplanetas = len(df_position)

col_desc, col_metrica = st.columns([3, 1])

with col_desc:
    st.caption(
        "Planetas que orbitan una estrella distinta al Sol. Todavía son pocos "
        "los confirmados frente a las ~100 mil estrellas de la galaxia — "
        "probablemente queden muchísimos más por descubrir."
    )

with col_metrica:
    st.metric("Exoplanetas confirmados", f"{num_exoplanetas:,}")

tab_descubrimiento, tab_distancia, tab_tamano, tab_sistema, tab_habitabilidad, tab_mapa, tab_conclusion = st.tabs(
    [
        "📡 Descubrimiento", "📏 Distancia", "🪐 Tamaño", "☀️ Sistema",
        "🌍 Habitabilidad", "🗺️ Mapa estelar", "📝 Conclusión",
    ]
)

# ============================================
# Descubrimiento
# ============================================

with tab_descubrimiento:
    col_tiempo, col_metodo = st.columns(2)

    with col_tiempo:
        st.caption(
            "Los primeros exoplanetas se descubrieron en 1992. El salto entre "
            "2014 y 2016 no es un pico real de detecciones: son planetas "
            "hallados antes y confirmados después, gracias al telescopio "
            "Kepler de la NASA."
        )
        with st.expander("Más contexto"):
            st.markdown(
                "Los primeros 2 exoplanetas fueron descubiertos en 1992, dichos "
                "planetas orbitaban un púlsar llamado Lich. Este fue el inicio "
                "de la búsqueda de más exoplanetas en nuestra galaxia.\n\n"
                "Vemos que entre los años 2014 y 2016 se hicieron el "
                "descubrimiento de varios exoplanetas, sin embargo, no es que "
                "esos exoplanetas se hayan detectado en esos años, se "
                "detectaron en años anteriores, pero tuvieron que esperar "
                "hasta esos años para, mediante estudios científicos, "
                "confirmar su existencia.\n\n"
                "Fue gracias al telescopio Kepler de la NASA, que publicó "
                "enormes lotes de datos espaciales acumulados e introdujo "
                "métodos avanzados de verificación estadística que "
                "confirmaron miles de candidatos a planetas a la vez, por eso "
                "tiene la mayor cantidad de descubrimientos."
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
                fig_descubrimiento.update_layout(height=380, margin=dict(l=0, r=0, t=10, b=0))
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
        st.caption(
            "El método de tránsito (observar cuándo cae el brillo de una "
            "estrella) es el que más exoplanetas ha detectado, seguido de la "
            "velocidad radial y el microlente gravitacional."
        )
        with st.expander("Más contexto"):
            st.markdown(
                "Indiscutiblemente, el mejor método para detectar exoplanetas "
                "es el transitorio, el cual consiste en observar el valor de "
                "la luminosidad de una estrella para ver si es que disminuye "
                "debido a que un planeta se ha puesto entre dicha estrella y "
                "el telescopio que la observa.\n\n"
                "El segundo método que descubrió más exoplanetas es el de la "
                "velocidad radial, este detecta el \"bamboleo\" periódico de "
                "una estrella debido a que está siendo afectada por la "
                "gravedad de un planeta que la orbita, ya que ambos orbitan "
                "un centro de gravedad común.\n\n"
                "El tercer método es de microlente gravitacional, este "
                "consiste en detectar cuando la gravedad de un planeta que "
                "pasa frente a una estrella y curva su luz, esto añade un "
                "pico de luz de extra brillo que permite medir su masa y "
                "posición. Este método es utilizado para detectar planetas "
                "lejanos que otros métodos no pueden detectar."
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

with tab_distancia:
    col_ranking_distancia, col_dist_distancia = st.columns(2)

    with col_ranking_distancia:
        st.caption(
            "El planeta más distante confirmado está a 8500 pc (27 722 años "
            "luz) — el límite actual de lo que podemos ver. El más cercano "
            "está a 1.3 pc (4.2 años luz), orbitando Próxima Centauri."
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
        st.caption(
            "La mayoría de los exoplanetas descubiertos están cerca de "
            "nosotros porque son los más fáciles de confirmar — es probable "
            "que haya muchos más esperando en estrellas más lejanas."
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

with tab_tamano:
    col_ranking_tamano, col_dist_tamano = st.columns(2)

    with col_ranking_tamano:
        st.caption(
            "El planeta más grande hallado es casi 8 veces el tamaño de "
            "Júpiter (87 radios terrestres). El más pequeño es más chico que "
            "Mercurio, con solo el 31 % de su radio."
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
        st.caption(
            "Los planetas grandes (sub-neptunos y jovianos) son los que más "
            "se descubren — probablemente porque son los más fáciles de "
            "detectar, no porque sean los más comunes."
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

with tab_sistema:
    st.caption(
        "La mayoría de los sistemas tiene 1 solo exoplaneta confirmado; el "
        "máximo encontrado es 8, igual que en nuestro propio sistema solar."
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

with tab_habitabilidad:
    col_ranking_hab, col_dist_hab = st.columns(2)

    with col_ranking_hab:
        st.caption(
            "El sistema con más planetas en zona habitable tiene 3 — más que "
            "el nuestro, que tiene 2 (Tierra y Marte)."
        )

        data_habitabilidad = fetch("/habitability")
        df_habitabilidad = pd.DataFrame(data_habitabilidad)

        if hay_datos(df_habitabilidad):
            st.dataframe(df_habitabilidad, use_container_width=True)

    with col_dist_hab:
        st.caption(
            "La mayoría de los planetas detectados están muy cerca de su "
            "estrella (y muy calientes) — otra vez, sesgo de detección: son "
            "los más fáciles de encontrar."
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
# Mapa estelar
# ============================================

with tab_mapa:
    st.caption(
        "Posición de cada estrella con planetas confirmados, calculada a "
        "partir de su ascensión recta, declinación y distancia. El Sol está "
        "en el centro (0, 0, 0); el plano amarillo tenue es la eclíptica "
        "(por donde orbita la Tierra) y el plano gris tenue es la "
        "orientación del disco de la Vía Láctea — ambos solo como "
        "referencia, no a escala real. Arrastra para rotar, rueda del mouse "
        "para hacer zoom."
    )

    @st.dialog("Mapa estelar 3D", width="large")
    def mostrar_mapa_fullscreen():
        st.plotly_chart(grafico_mapa_3d(df_position, altura=800), use_container_width=True)

    col_espacio_mapa, col_boton_mapa = st.columns([5, 1])
    with col_boton_mapa:
        if st.button("⛶ Pantalla completa", use_container_width=True, key="btn_mapa_fullscreen"):
            mostrar_mapa_fullscreen()

    if hay_datos(df_position):
        st.plotly_chart(grafico_mapa_3d(df_position), use_container_width=True)

# ============================================
# Conclusión
# ============================================

with tab_conclusion:
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
