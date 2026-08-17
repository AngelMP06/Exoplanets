import streamlit as st
import os
import base64
from contextlib import contextmanager
import requests
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from dotenv import load_dotenv
load_dotenv()

st.set_page_config(layout="wide", page_title="Exoplanetas", page_icon="🪐")

# Ancho máximo de 600px para tablas y un tope de 700px para la "columna de
# lectura" (subtítulo + texto + gráfica/tabla de cada subsección) — no anchos
# fijos, topes: en pantallas angostas se achican solas junto con su
# contenedor.
st.markdown(
    """
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link
        href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=Source+Serif+4:opsz,wght@8..60,400;8..60,600&display=swap"
        rel="stylesheet"
    >
    <style>
    /* Tipografías centralizadas acá: todo título (h1/h2/h3, TOC) usa
       --font-titulos y todo cuerpo de texto usa --font-cuerpo, en vez de
       repetir el nombre de la fuente en cada selector — para cambiar la
       tipografía de toda la página alcanza con tocar estas dos líneas.
       Las fuentes reales se cargan arriba con <link> (en vez de @import,
       que bloquea el render mientras se descarga); el fallback de sistema
       solo entra si la carga falla. */
    :root {
        --font-titulos: 'Space Grotesk', sans-serif;
        --font-cuerpo: 'Source Serif 4', Georgia, serif;
    }
    div[data-testid="stTable"] {
        max-width: 600px;
        margin: 0 auto 1rem auto;
    }
    div[data-testid="stTable"] th {
        text-align: center !important;
    }
    div[data-testid="stTable"] td {
        text-align: center !important;
    }
    /* Columna de lectura compartida por subtítulo, texto y gráfica/tabla de
       una subsección: mismo margen izquierdo y mismo ancho máximo (700px)
       para los tres, así una gráfica de 600px queda centrada en relación al
       texto de arriba, no en relación a toda la página. */
    div[class*="st-key-columna-lectura-"] {
        max-width: 900px;
    }
    div[class*="st-key-tarjeta-"] {
        max-width: 600px;
        margin: 0.5rem auto 1.5rem auto;
        padding: 1.25rem;
        border-radius: 12px;
        background-color: #eaf1fb;
        box-sizing: border-box;
    }
    /* Texto narrativo del artículo: una serif en vez del sans por defecto,
       con más interlineado, para que se sienta más "artículo". El <p> que
       envuelve st.markdown trae su propia regla de Streamlit con
       font-family explícito, que gana por sobre lo heredado del div —
       por eso el !important también hace falta acá, apuntando al <p>
       directamente y no solo al div contenedor. */
    div[class*="st-key-parrafo-"] {
        font-size: 1.05rem;
        line-height: 1.7;
    }
    div[class*="st-key-parrafo-"] p {
        font-family: var(--font-cuerpo) !important;
    }
    /* !important porque Streamlit ya trae su propia regla para h1-h6
       (con una clase de scope, más específica que un simple "h2, h3"). */
    h2, h3 {
        font-family: var(--font-titulos) !important;
    }
    h2 {
        padding: 10px 0;
    }
    /* Separación extra entre el banner y el primer título de sección. */
    h2:first-of-type {
        padding-top: 3rem;
    }
    /* El padding horizontal por defecto de Streamlit en el contenedor
       principal es justo lo que desalineaba el banner de ancho completo
       (ver más abajo) — se pone en 0 acá; toda la sangría del artículo la
       dan las propias columnas de lectura, no este padding. */
    .block-container {
        padding-left: 5rem !important;
        padding-right: 5rem !important;
    }
    /* Tabla de contenidos con scroll normal mientras estamos sobre el
       banner, y "enganchada" (position: sticky) desde que arranca el
       contenido: los intentos anteriores con sticky fallaban porque el div
       flotaba fuera de cualquier columna, sin un contenedor hermano de la
       misma altura para recorrer mientras se scrollea. Ahora vive en
       col_toc, que Streamlit estira (height:100%) a la misma altura que
       col_contenido (ver más abajo) — pero ese estirado se corta un nivel
       más abajo: el div interno que envuelve este markdown puntual
       (stElementContainer) vuelve a tener altura automática, así que
       sticky no tenía dónde "recorrer". Se vuelve a estirar toda esa
       cadena de divs internos de Streamlit hasta el padre directo del
       TOC, para que sticky tenga los ~7900px de la columna para
       engancharse en top:5rem y despegarse solo al subir por encima. */
    div[data-testid="stElementContainer"]:has(.toc-fija) {
        height: 100%;
    }
    div[data-testid="stElementContainer"]:has(.toc-fija) > div[data-testid="stMarkdown"] {
        height: 100%;
    }
    div[data-testid="stElementContainer"]:has(.toc-fija) > div[data-testid="stMarkdown"] > div {
        height: 100%;
    }
    div[data-testid="stElementContainer"]:has(.toc-fija) [data-testid="stMarkdownContainer"] {
        height: 100%;
    }
    .toc-fija {
        position: sticky;
        top: 5rem;
        width: 100%;
        max-width: 276px;
        box-sizing: border-box;
        background-color: #eaf1fb;
        border-radius: 12px;
        padding: 1.5rem 1.75rem;
        box-shadow: 0 2px 10px rgba(11, 11, 11, 0.12);
        z-index: 999;
    }
    .toc-fija .toc-titulo {
        font-family: var(--font-titulos);
        font-weight: 700;
        margin-bottom: 0.9rem;
        font-size: 1.4rem;
        color: #0b0b0b;
    }
    .toc-fija a {
        display: block;
        padding: 0.5rem 0;
        color: #184f95;
        text-decoration: none;
        font-size: 1.15rem;
    }
    .toc-fija a:hover {
        text-decoration: underline;
    }
    @media (max-width: 900px) {
        .toc-fija { display: none; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

API_BASE_URL = os.getenv("API_BASE_URL")
if not API_BASE_URL:
    st.error(
        "Falta configurar la variable de entorno API_BASE_URL con la URL "
        "de la API."
    )
    st.stop()


@st.cache_data(ttl=600)
def fetch(endpoint, params=None):
    # La API en Render puede tardar ~20s en despertar si estuvo inactiva —
    # timeout generoso en vez de dejar que la request cuelgue indefinido, y
    # un error legible en vez del traceback crudo de requests/Streamlit.
    try:
        r = requests.get(f"{API_BASE_URL}{endpoint}", params=params, timeout=30)
        r.raise_for_status()
        return r.json()
    except requests.exceptions.RequestException:
        st.error(
            "No se pudo conectar con la API — puede tardar ~20s en "
            "despertar si estuvo inactiva. Recargá la página en un momento."
        )
        st.stop()


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

ORDEN_HABITABILIDAD = ["Muy cerca", "Zona habitable", "Muy lejos", "Desconocido"]

ORDEN_TEMP_HABITABILIDAD = [
    "hP - hypopsychroplanet", "P - psychroplanet", "M - mesoplanet",
    "T - thermoplanet", "hT - hyperthermoplanet", "Desconocido",
]

ORDEN_DISCOVERY_ERA = ["Pre-Kepler", "Era Kepler", "Era TESS"]

# Value → etiqueta de cada selectbox: la key es el valor real que espera la
# API (categoria del mart), el value es lo que ve el usuario — para poder
# mostrar un texto lindo sin tocar el parámetro que se manda al backend.
OPCIONES_DESCUBRIMIENTO = {
    "por_año": "Por año",
    "tendencia_acumulada": "Tendencia acumulada",
    "por_discovery_era": "Por era de telescopio",
}
OPCIONES_HABITABILIDAD = {
    "por_habitability": "Habitabilidad según posición",
    "por_temp_habitability": "Habitabilidad por temperatura",
}

# Un solo azul: con una sola serie el color no codifica nada, así que no hay
# leyenda que leer.
COLOR_SERIE = "#2a78d6"

# Los gráficos de Plotly no heredan el CSS de la página (corren en su propio
# layout), así que la tipografía y la tinta de texto se repiten acá como
# constantes en vez de duplicar el string en cada función de gráfico.
FUENTE_GRAFICOS = "'Space Grotesk', sans-serif"
COLOR_TEXTO_GRAFICO = "#3b3b3b"
COLOR_GRID_GRAFICO = "rgba(11, 11, 11, 0.08)"

# Constantes astronómicas para los párrafos de "los extremos" (Distancia y
# Tamaño): el número puntual siempre sale del DataFrame recién fetcheado,
# nunca hardcodeado — pero convertirlo a años luz o compararlo con Júpiter/
# Mercurio necesita estas referencias fijas.
PC_A_ANIOS_LUZ = 3.26156
RADIO_JUPITER_TIERRA = 11.2
RADIO_MERCURIO_TIERRA = 0.383
PLANETAS_SISTEMA_SOLAR = 8
# Bajo el mismo criterio de zona habitable que usa mart_planets (0.75-1.77 UA
# equivalente, ver mart_planets.sql), la Tierra y Marte caen dentro — no es
# un redondeo optimista nuestro, es consistente con cómo se clasifica acá el
# resto de los planetas.
PLANETAS_HABITABLES_SISTEMA_SOLAR = 2

# Rangos de las categorías que clasifican por un valor numérico (ver schema.md).
# Listas de (categoría, rango) en vez de un string largo con "·": se muestran
# como leyenda vertical a la derecha del gráfico correspondiente (ver
# leyenda_rangos), no como una línea de texto debajo.
RANGO_TAMANOS = [
    ("Mercury-like", "< 0.5"),
    ("Mini-Earth", "0.5–0.8"),
    ("Earth-like", "0.8–1.2"),
    ("Super-Earth", "1.2–1.75"),
    ("Transition", "1.75–2.1"),
    ("Sub-Neptune", "2.1–4"),
    ("Neptune-like", "4–8"),
    ("Jovian-like", "> 8"),
]
RANGO_TEMP_HABITABILIDAD = [
    ("hP - hypopsychroplanet", "< −50 °C"),
    ("P - psychroplanet", "−50 a 0 °C"),
    ("M - mesoplanet", "0 a 50 °C"),
    ("T - thermoplanet", "50 a 100 °C"),
    ("hT - hyperthermoplanet", "≥ 100 °C"),
]
RANGO_DISCOVERY_ERA = [
    ("Pre-Kepler", "antes de 2009"),
    ("Era Kepler", "2009–2017"),
    ("Era TESS", "desde 2018"),
]

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


@st.cache_resource
def cargar_banner_b64():
    """PNG generado localmente (matplotlib, ver scratchpad/generate_banner.py)
    para evitar cualquier duda de derechos de autor sobre imágenes de terceros."""
    ruta = os.path.join(os.path.dirname(__file__), "assets", "banner_exoplanetas_v2.png")
    with open(ruta, "rb") as f:
        return base64.b64encode(f.read()).decode()


def hay_datos(df, mensaje="Sin datos para esta selección."):
    if df.empty:
        st.info(mensaje)
        return False
    return True


def comparacion_con_referencia(valor, referencia):
    """Frase "más/menos/igual que <referencia>" para comparar un número que
    viene del dataset (puede cambiar con nuevos descubrimientos) contra una
    referencia fija — para que la afirmación siga siendo cierta aunque el
    valor del dataset cambie, en vez de quedar hardcodeada para un solo caso."""
    if valor > referencia:
        return "más que"
    if valor < referencia:
        return "menos que"
    return "igual que"


_contador_columna = 0


# Sangría compartida por el subtítulo, el texto y las gráficas de una
# subsección: los tres arrancan en el mismo margen izquierdo, distinto (más
# adentro) del margen del título de sección (h2).
INDENTACION_SUBSECCION = [1, 24]


@contextmanager
def _columna_lectura():
    """Columna compartida por subtítulo/texto/gráfica de una subsección:
    misma sangría y mismo ancho máximo de lectura (700px, vía CSS en
    st-key-columna-lectura-N), para que todo quede alineado entre sí."""
    global _contador_columna
    _contador_columna += 1
    _, col = st.columns(INDENTACION_SUBSECCION)
    with col:
        with st.container(key=f"columna-lectura-{_contador_columna}"):
            yield


def subseccion(titulo):
    """Subtítulo de una subsección, con sangría respecto al título de la
    sección (h2)."""
    with _columna_lectura():
        st.subheader(titulo)


def parrafo(texto):
    """Texto narrativo, a la misma sangría y ancho que su subtítulo."""
    with _columna_lectura():
        with st.container(key=f"parrafo-{_contador_columna}"):
            st.markdown(texto)


@contextmanager
def tarjeta_grafico(key):
    """Gráfica (y su selectbox, si tiene) en una tarjeta con fondo propio,
    centrada dentro de la misma columna de lectura que el texto — por eso
    queda alineada con el texto, no con el ancho total de la página."""
    with _columna_lectura():
        with st.container(key=f"tarjeta-{key}"):
            yield


def tabla_estilizada(df):
    """Estilo compartido por las tablas de ranking: encabezado azulado,
    filas intercaladas y texto centrado. Usa pandas Styler + st.table (HTML
    real) en vez de st.dataframe, porque st.dataframe se dibuja en canvas y
    no admite estas propiedades CSS."""
    df = df.reset_index(drop=True)
    colores_fila = ["#ffffff" if i % 2 == 0 else "#f2f6fc" for i in df.index]
    return (
        df.style
        .hide(axis="index")
        .set_table_styles([
            {"selector": "th", "props": [
                ("background-color", "#cfe3fb"),
                ("color", "#0b0b0b"),
                ("text-align", "center"),
                ("font-weight", "600"),
                ("padding", "0.4rem 0.6rem"),
            ]},
            {"selector": "td", "props": [
                ("text-align", "center"),
                ("padding", "0.35rem 0.6rem"),
            ]},
        ])
        .apply(lambda _: [f"background-color: {c}" for c in colores_fila], axis=0)
    )


def leyenda_rangos(items, nota=None):
    """Leyenda vertical (categoría → rango) para mostrar al costado de un
    gráfico de barras, en vez de una línea de texto larga debajo — se lee
    mejor como leyenda cuando tiene su propia columna angosta a la derecha."""
    filas = "".join(
        f'<div style="margin-bottom:0.35rem;"><b>{cat}</b>: {rango}</div>'
        for cat, rango in items
    )
    nota_html = (
        f'<div style="margin-top:0.4rem;font-style:italic;">{nota}</div>' if nota else ""
    )
    st.markdown(
        f'<div style="font-size:0.8rem;color:#5a5a5a;line-height:1.4;">'
        f'{filas}{nota_html}</div>',
        unsafe_allow_html=True,
    )


def aplicar_estilo_grafico(fig, altura=400, grilla_y=True):
    """Estilo compartido por todos los gráficos de Plotly: misma tipografía
    que el resto de la página, fondo transparente (para que se vea el celeste
    de la tarjeta en vez de un rectángulo blanco aparte), grilla tenue —
    presente solo como referencia, nunca protagonista — y un tooltip prolijo
    al pasar el mouse."""
    fig.update_layout(
        height=altura,
        margin=dict(l=0, r=0, t=10, b=0),
        font=dict(family=FUENTE_GRAFICOS, color=COLOR_TEXTO_GRAFICO, size=13),
        hoverlabel=dict(
            font=dict(family=FUENTE_GRAFICOS, size=13),
            bgcolor="#ffffff",
            bordercolor=COLOR_SERIE,
        ),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
    )
    fig.update_xaxes(showgrid=False, zeroline=False, linecolor=COLOR_GRID_GRAFICO)
    fig.update_yaxes(showgrid=grilla_y, gridcolor=COLOR_GRID_GRAFICO, zeroline=False)
    return fig


def grafico_distribucion(df, orden=None, etiquetas=None, altura=400):
    """Barra vertical para el patrón clasificacion / conteo."""
    fig = px.bar(
        df,
        x="clasificacion",
        y="conteo",
        labels=etiquetas or {"clasificacion": "", "conteo": "Nº de planetas"},
        category_orders={"clasificacion": orden} if orden else None,
    )
    fig.update_traces(
        marker=dict(color=COLOR_SERIE, cornerradius=4),
        hovertemplate="%{x}<br><b>%{y:,}</b><extra></extra>",
    )
    return aplicar_estilo_grafico(fig, altura=altura)


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
        font=dict(family=FUENTE_GRAFICOS, color=COLOR_TEXTO_GRAFICO, size=13),
        hoverlabel=dict(font=dict(family=FUENTE_GRAFICOS, size=13)),
        scene=dict(xaxis_title="X [pc]", yaxis_title="Y [pc]", zaxis_title="Z [pc]"),
        legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01),
    )
    return fig


def grafico_histograma_distancia(df, altura=400):
    """Histograma de distancias. En Plotly (antes era una imagen estática de
    matplotlib) para que comparta estilo, tipografía y hover con el resto de
    gráficos de la página en vez de verse como un elemento aparte."""
    fig = px.histogram(df, x="distance_pc", nbins=30, labels={"distance_pc": "Distancia [pc]"})
    fig.update_traces(
        marker=dict(color=COLOR_SERIE, cornerradius=2),
        hovertemplate="%{x} pc<br><b>%{y:,} planetas</b><extra></extra>",
    )
    fig.update_yaxes(title="Nº de planetas")
    return aplicar_estilo_grafico(fig, altura=altura)


# ============================================
# Encabezado
# ============================================

df_position = pd.DataFrame(fetch("/position"))

# mart_position solo trae los planetas con ra/dec/distancia completos (para
# el mapa 3D y el histograma), así que len(df_position) subcuenta el total
# real. "por_metodo" agrupa sobre mart_planets entero, sin ese filtro —
# discovery_method nunca es nulo — así que sumar su "conteo" da el total
# real de exoplanetas confirmados.
data_metodo_total = fetch("/discovery_distribution", params={"categoria": "por_metodo"})
num_exoplanetas = sum(fila["conteo"] for fila in data_metodo_total)

st.markdown(
    f"""
    <style>
    .block-container {{ padding-top: 0rem !important; }}
    .banner-exoplanetas {{
        position: relative;
        left: 50%;
        right: 50%;
        margin-left: -50vw;
        margin-right: -50vw;
        width: 100vw;
        min-height: 100vh;
        box-sizing: border-box;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        text-align: center;
        padding: 2rem;
        color: #ffffff;
        background-image:
            linear-gradient(180deg, rgba(6,6,13,0.35) 0%, rgba(6,6,13,0.8) 100%),
            url("data:image/png;base64,{cargar_banner_b64()}");
        background-size: cover;
        background-position: center;
    }}
    .banner-exoplanetas h1 {{
        font-family: var(--font-titulos);
        font-size: 3.5rem;
        margin: 0 0 1rem 0;
    }}
    .banner-exoplanetas p {{
        max-width: 640px;
        font-size: 1.15rem;
        opacity: 0.92;
    }}
    .banner-exoplanetas .banner-metrica {{
        margin-top: 1.5rem;
        font-size: 1.5rem;
        font-weight: 600;
    }}
    </style>
    <div class="banner-exoplanetas">
        <h1>Exoplanetas</h1>
        <p>
            Planetas que giran alrededor de otra estrella que no es el Sol.
            Todavía conocemos pocos, comparado con las ~100 mil millones de
            estrellas que tiene la galaxia — seguramente queden muchísimos
            más por descubrir.
        </p>
        <div class="banner-metrica">🪐 {num_exoplanetas:,} exoplanetas confirmados</div>
    </div>
    """,
    unsafe_allow_html=True,
)

col_contenido, col_toc = st.columns([4, 1], gap="large")

with col_toc:
    st.markdown(
        """
        <div class="toc-fija">
            <div class="toc-titulo">Contenido</div>
            <a href="#descubrimiento">1. Descubrimiento</a>
            <a href="#distancia">2. Distancia</a>
            <a href="#tamano">3. Tamaño</a>
            <a href="#sistema">4. Sistema</a>
            <a href="#habitabilidad">5. Habitabilidad</a>
            <a href="#mapa-estelar">6. Mapa estelar</a>
            <a href="#conclusion">7. Conclusión</a>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col_contenido:

    # ============================================
    # Descubrimiento
    # ============================================

    st.header("1. Descubrimiento", anchor="descubrimiento")

    subseccion("Cuándo se descubrieron")

    parrafo(
        "Los dos primeros exoplanetas se descubrieron en 1992. Orbitaban "
        "un púlsar (una estrella muerta que gira rapidísimo) al que "
        "después le pusieron el nombre de Lich. Ahí arrancó todo.\n\n"
        "Si mirás el gráfico, vas a ver un salto enorme entre 2014 y "
        "2016. Pero ese salto no significa que se hayan encontrado más "
        "planetas justo esos años, significa que se confirmaron. "
        "Muchos ya se habían detectado antes; solo hacía falta más "
        "tiempo y más estudios para confirmar que eran reales.\n\n"
        "Ese salto es obra del telescopio Kepler, de la NASA. Kepler "
        "juntó tantísimos datos que los científicos desarrollaron "
        "nuevas formas de confirmar miles de candidatos a la vez, en "
        "vez de uno por uno. Por eso Kepler tiene, de lejos, la mayor "
        "cantidad de descubrimientos."
    )

    with tarjeta_grafico("descubrimiento-tiempo"):
        categoria_descubrimiento = st.selectbox(
            "Distribución por descubrimiento",
            list(OPCIONES_DESCUBRIMIENTO.keys()),
            format_func=lambda k: OPCIONES_DESCUBRIMIENTO[k],
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
                fig_descubrimiento.update_traces(
                    line_color=COLOR_SERIE,
                    line_width=2,
                    marker=dict(size=6, color=COLOR_SERIE),
                    hovertemplate="Año %{x}<br><b>%{y:,} acumulado</b><extra></extra>",
                )
                aplicar_estilo_grafico(fig_descubrimiento, altura=400)
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
                    orden=ORDEN_DISCOVERY_ERA,
                    etiquetas={"clasificacion": "Era", "conteo": "Nº de planetas"},
                )

            if categoria_descubrimiento == "por_discovery_era":
                col_grafico, col_leyenda = st.columns([2, 1])
                with col_grafico:
                    st.plotly_chart(fig_descubrimiento, use_container_width=True)
                with col_leyenda:
                    leyenda_rangos(RANGO_DISCOVERY_ERA)
            else:
                st.plotly_chart(fig_descubrimiento, use_container_width=True)

    subseccion("Cómo se descubrieron")

    parrafo(
        "El método que más exoplanetas encontró es el de tránsito: "
        "miras una estrella y esperas a que su brillo baje un poco. "
        "Si baja de forma regular, es porque algo (un planeta) está "
        "pasando justo por delante, tapando una parte de esa luz.\n\n"
        "El segundo método es la velocidad radial. Un planeta no solo "
        "gira alrededor de su estrella: la estrella también se mueve un "
        "poco por la gravedad del planeta, como un bamboleo. Ese vaivén "
        "se puede medir, y así se puede encontrar un nuevo planeta.\n\n"
        "El tercero es el microlente gravitacional, el más raro de "
        "explicar: cuando una estrella con un planeta pasa justo por "
        "delante de otra mucho más lejana, su gravedad funciona como "
        "una lupa y curva la luz de esa estrella de fondo, generando "
        "un pico de brillo. Si hay un planeta, deja una pequeña marca "
        "extra en ese pico, que sirve para calcular su masa y a qué "
        "distancia orbita. Es el método que mejor funciona para "
        "encontrar planetas muy lejanos, donde los demás no llegan."
    )

    with tarjeta_grafico("descubrimiento-metodo"):
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

    st.header("2. Distancia", anchor="distancia")

    data_mas_distante = fetch("/distance", params={"categoria": "mas_distante"})
    df_mas_distante = pd.DataFrame(data_mas_distante)
    data_menos_distante = fetch("/distance", params={"categoria": "menos_distante"})
    df_menos_distante = pd.DataFrame(data_menos_distante)

    subseccion("El más lejano y el más cercano")

    fila_mas_lejano = df_mas_distante.loc[df_mas_distante["distance_pc"].idxmax()]
    fila_mas_cercano = df_menos_distante.loc[df_menos_distante["distance_pc"].idxmin()]
    parrafo(
        f"El planeta confirmado más lejano está a "
        f"{fila_mas_lejano['distance_pc']:,.0f} pc de nosotros "
        f"(unos {fila_mas_lejano['distance_pc'] * PC_A_ANIOS_LUZ:,.0f} años "
        f"luz) — hasta ahí llega, por ahora, lo que podemos detectar. El "
        f"más cercano está a solo {fila_mas_cercano['distance_pc']:.1f} pc "
        f"({fila_mas_cercano['distance_pc'] * PC_A_ANIOS_LUZ:.1f} años "
        f"luz), orbitando la estrella {fila_mas_cercano['star_name']}."
    )

    with tarjeta_grafico("distancia-extremos"):
        opcion_distancia = st.selectbox(
            "Ranking a mostrar",
            ["Más distantes", "Más cercanos"],
            key="ranking_distancia",
        )
        df_ranking_distancia = (
            df_mas_distante if opcion_distancia == "Más distantes" else df_menos_distante
        )
        if hay_datos(df_ranking_distancia):
            st.table(tabla_estilizada(df_ranking_distancia.drop(columns=["categoria"])))

    subseccion("Qué tan lejos están, en general")

    parrafo(
        "La mayoría de los exoplanetas que conocemos están relativamente "
        "cerca de nosotros. No es casualidad: cuanto más cerca está un "
        "planeta, más fácil es detectarlo. Seguramente hay muchísimos "
        "más dando vueltas alrededor de estrellas lejanas, todavía "
        "esperando a que los encontremos."
    )

    with tarjeta_grafico("distancia-histograma"):
        if hay_datos(df_position):
            st.plotly_chart(grafico_histograma_distancia(df_position), use_container_width=True)

    # ============================================
    # Tamaño
    # ============================================

    st.header("3. Tamaño", anchor="tamano")

    data_mas_grande = fetch("/size", params={"categoria": "mas grande"})
    df_mas_grande = pd.DataFrame(data_mas_grande)
    data_mas_pequena = fetch("/size", params={"categoria": "mas pequeña"})
    df_mas_pequena = pd.DataFrame(data_mas_pequena)

    subseccion("El más grande y el más chico")

    radio_max = df_mas_grande["planet_radius_earth"].max()
    radio_min = df_mas_pequena["planet_radius_earth"].min()
    parrafo(
        f"El planeta más grande que encontramos mide casi "
        f"{radio_max / RADIO_JUPITER_TIERRA:.0f} veces el tamaño de "
        f"Júpiter, unos {radio_max:.0f} radios terrestres. En el otro "
        f"extremo, el más chico ni siquiera llega al tamaño de Mercurio: "
        f"mide apenas el {radio_min / RADIO_MERCURIO_TIERRA:.0%} de su "
        f"radio."
    )

    with tarjeta_grafico("tamano-extremos"):
        opcion_tamano = st.selectbox(
            "Ranking a mostrar",
            ["Más grandes", "Más pequeños"],
            key="ranking_tamano",
        )
        df_ranking_tamano = (
            df_mas_grande if opcion_tamano == "Más grandes" else df_mas_pequena
        )
        if hay_datos(df_ranking_tamano):
            st.table(tabla_estilizada(df_ranking_tamano.drop(columns=["categoria"])))

    subseccion("Qué tipos de planeta hay")

    parrafo(
        "Los planetas grandes, del tamaño de Neptuno o Júpiter para "
        "arriba, son los que más aparecen en la lista. Otra vez el "
        "mismo motivo: son más fáciles de detectar por su tamaño, no " \
        "necesariamente más comunes en el universo."
    )

    with tarjeta_grafico("tamano-distribucion"):
        data_dist_tamano = fetch("/size_distribution", params={"categoria": "por_tipo_planeta"})
        df_dist_tamano = pd.DataFrame(data_dist_tamano)

        if hay_datos(df_dist_tamano):
            df_dist_tamano = df_dist_tamano[df_dist_tamano["clasificacion"] != "Desconocido"]
            orden_tamano = [c for c in ORDEN_TAMANOS if c != "Desconocido"]
            col_grafico, col_leyenda = st.columns([2, 1])
            with col_grafico:
                st.plotly_chart(
                    grafico_distribucion(df_dist_tamano, orden=orden_tamano),
                    use_container_width=True,
                )
            with col_leyenda:
                leyenda_rangos(RANGO_TAMANOS, nota="Radios terrestres")

    # ============================================
    # Sistema
    # ============================================

    st.header("4. Sistema", anchor="sistema")

    data_dist_sistema = fetch(
        "/system_distribution", params={"categoria": "distribucion_num_planetas"}
    )
    df_dist_sistema = pd.DataFrame(data_dist_sistema)

    max_planetas_sistema = int(df_dist_sistema["clasificacion"].max())
    comparacion_sistema = comparacion_con_referencia(max_planetas_sistema, PLANETAS_SISTEMA_SOLAR)
    parrafo(
        f"La mayoría de los sistemas que conocemos tiene un solo "
        f"exoplaneta confirmado. El sistema con más planetas que "
        f"encontramos tiene {max_planetas_sistema}, {comparacion_sistema} "
        f"al igual que el nuestro."
    )

    with tarjeta_grafico("sistema"):
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

    st.header("5. Habitabilidad", anchor="habitabilidad")

    data_habitabilidad = fetch("/habitability")
    df_habitabilidad = pd.DataFrame(data_habitabilidad)

    subseccion("Los sistemas con más planetas habitables")

    max_habitables = int(df_habitabilidad["planetas_habitables"].max())
    comparacion_hab = comparacion_con_referencia(max_habitables, PLANETAS_HABITABLES_SISTEMA_SOLAR)
    parrafo(
        f"El sistema con más planetas en zona habitable tiene "
        f"{max_habitables} planetas habitables, más que nuestro sistema solar"
        f", que tiene {PLANETAS_HABITABLES_SISTEMA_SOLAR} (la Tierra y Marte)."
    )

    with tarjeta_grafico("habitabilidad-ranking"):
        if hay_datos(df_habitabilidad):
            st.table(tabla_estilizada(df_habitabilidad))

    subseccion("Qué tan habitables son, en general")

    parrafo(
        "La mayoría de los planetas que detectamos están cerca a su "
        "estrella, y por lo tanto son bastante calientes. De nuevo el "
        "mismo patrón: los que están cerca son los más fáciles de "
        "encontrar, así que son los que más aparecen."
    )

    with tarjeta_grafico("habitabilidad-distribucion"):
        categoria_dist_hab = st.selectbox(
            "Distribución por habitabilidad",
            list(OPCIONES_HABITABILIDAD.keys()),
            format_func=lambda k: OPCIONES_HABITABILIDAD[k],
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

            if categoria_dist_hab == "por_temp_habitability":
                col_grafico, col_leyenda = st.columns([2, 1])
                with col_grafico:
                    st.plotly_chart(
                        grafico_distribucion(df_dist_hab, orden=orden_hab),
                        use_container_width=True,
                    )
                with col_leyenda:
                    leyenda_rangos(RANGO_TEMP_HABITABILIDAD)
            else:
                st.plotly_chart(
                    grafico_distribucion(df_dist_hab, orden=orden_hab),
                    use_container_width=True,
                )

    # ============================================
    # Mapa estelar
    # ============================================

    st.header("6. Mapa estelar", anchor="mapa-estelar")

    st.caption(
        "Acá están ubicadas todas las estrellas con planetas confirmados, "
        "calculadas a partir de su posición en el cielo y su distancia. El "
        "Sol está justo en el centro. El plano de color amarillo suave es"
        "el plano de la eclíptica (por donde se mueve la Tierra alrededor del Sol) y el "
        "plano gris marca hacia dónde se extiende la Vía Láctea, los dos son "
        "solo de referencia, no están a escala real. Pueds arrastrar para "
        "rotar y usar la rueda del mouse para hacer zoom."
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

    st.header("7. Conclusión", anchor="conclusion")

    parrafo(
        "Todos los gráficos de esta página cuentan, en el fondo, la misma "
        "historia: nuestros métodos para detectar planetas todavía no "
        "alcanzan. Lo que más encontramos son planetas grandes, cercanos "
        "a su estrella y calientes —los famosos \"júpiters calientes\"— "
        "no porque sean los más comunes, sino porque son los más fáciles "
        "de ver.\n\n"
        "Eso deja una pregunta abierta: ¿cuánto nos estamos perdiendo? "
        "Probablemente haya muchos más planetas, lunas y asteroides ahí "
        "afuera que todavía no podemos detectar. Nuestro propio sistema "
        "solar tiene una variedad enorme de cuerpos —lunas, asteroides, "
        "cometas— y si lo miráramos desde otra estrella, con la "
        "tecnología actual, probablemente ni la mitad de eso sería "
        "detectable.\n\n"
        "Estamos recién empezando. Todavía falta mucho camino en la "
        "búsqueda de exoplanetas, y ojalá en el futuro aparezcan mejores "
        "técnicas — o formas completamente nuevas de buscar — para "
        "encontrar todo lo que todavía se nos escapa."
    )
