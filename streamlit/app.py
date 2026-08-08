import streamlit as st
import os
import requests

from dotenv import load_dotenv
load_dotenv()

st.title("Toda la información de exoplanetas en un solo lugar")


url = os.getenv("URL")

@st.cache_data
def get_json(url):
    response = requests.get(url + "/habitability", timeout = 10)
    if response.status_code == 200:
        return response.json()
    else:
        st.error(f"Error: {response.status_code}")
        return None

datos_json = get_json(url)

if datos_json:
    st.write("Datos obtenidos correctamente")
    st.write(datos_json)
