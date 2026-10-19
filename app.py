import streamlit as st
import sympy as sp

# CONFIGURACIÓN

st.set_page_config(
    page_title = "Calculadora matemática",
    page_icon = "📘",
    layout = "wide"
)

# CONTROL DEL MENÚ
if "seccion" not in st.session_state:
    st.session_state.seccion = "Límite"

st.title("Calculadora matemática")

st.write("Explora funciones, límites, derivadas, integrales y series.")

# Opciones del menú
opciones = [
    "Límite",
    "Derivada",
    "Integral",
    "Suma infinita",
    "Apéndice"
]

# Crear cinco columnas
columnas = st.columns(5)

# Crear los botones
for columna, opcion in zip(columnas, opciones):
    with columna:
        if st.button(opcion, key = opcion, use_container_width = True):
            st.session_state.seccion = opcion

st.divider()

# Obtener la sección seleccionada
seccion = st.session_state.seccion

# FUNCIÓN PARA MOSTRAR NÚMEROS, ELIMINANDO CEROS INNECESARIOS

# APÉNDICE

if seccion == "Apéndice":
    from apendice import ejecutar_apendice
    ejecutar_apendice()

elif seccion == "Límite":
    from limite import ejecutar_limites
    ejecutar_limites()

elif seccion == "Derivada":
    from derivada import ejecutar_derivadas
    ejecutar_derivadas()

elif seccion == "Integral":
    from integral import ejecutar_integrales
    ejecutar_integrales()

elif seccion == "Suma infinita":
    from suma_infinita import ejecutar_sumas_infinitas
    ejecutar_sumas_infinitas()