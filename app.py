
import streamlit as st

st.set_page_config(
    page_title="Calculadora de límites",
    page_icon="📘",
    layout="wide"
)

# Inicializar la sección seleccionada
if "seccion" not in st.session_state:
    st.session_state.seccion = "Límite"

# Título principal
st.title("Calculadora matemática")
st.write("Selecciona el tema que deseas consultar.")

# Menú de botones
opciones = [
    "Límite",
    "Derivada",
    "Integral",
    "Suma infinita",
    "Apéndice"
]

columnas = st.columns(5)

for columna, opcion in zip(columnas, opciones):
    with columna:
        if st.button(
            opcion,
            key=opcion,
            use_container_width=True
        ):
            st.session_state.seccion = opcion

st.divider()

# Mostrar el contenido de la sección seleccionada
seccion = st.session_state.seccion

if seccion == "Límite":
    st.header("Límites")
    st.write("Aquí encontrarás teoría y ejemplos de límites.")

elif seccion == "Derivada":
    st.header("Derivadas")
    st.write("Aquí encontrarás teoría y ejemplos de derivadas.")

elif seccion == "Integral":
    st.header("Integrales")
    st.write("Aquí encontrarás teoría y ejemplos de integrales.")

elif seccion == "Suma infinita":
    st.header("Sumas infinitas")
    st.write("Aquí encontrarás teoría y ejemplos de series.")

elif seccion == "Apéndice":
    st.header("Apéndice")
    st.write("Aquí encontrarás definiciones y resultados auxiliares.")