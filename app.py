import streamlit as st
import sympy as sp

st.set_page_config(
    page_title="Calculadora matemática",
    page_icon="📘",
    layout="wide"
)

x = sp.symbols("x")

# Inicializar la sección
if "seccion" not in st.session_state:
    st.session_state.seccion = "Límite"

st.title("Calculadora matemática")
st.write("Explora funciones, límites, derivadas, integrales y series.")

# Menú principal
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
        if st.button(opcion, key=opcion, use_container_width=True):
            st.session_state.seccion = opcion


st.divider()

seccion = st.session_state.seccion

from graficar_limite import graficar_limite

if seccion == "Apéndice":
    st.header("Apéndice")
    st.write("Aquí encontrarás definiciones y resultados auxiliares.")


else:
    st.header(seccion)

    funcion_texto = st.text_input(
        "Función f(x)",
        value="sin(x)/x" if seccion == "Límite" else "x**2",
        key="funcion_" + seccion
    )

    if seccion == "Límite":
        a = st.number_input(
            "Valor al que tiende x (a)",
            value=0.0,
            step=0.1,
            format="%.6f"
        )

        if st.button("Graficar límite", type="primary"):
            try:
                funcion = sp.sympify(funcion_texto)

                if funcion.free_symbols - {x}:
                    st.error("Utiliza únicamente x como variable.")
                else:
                    st.latex(
                        r"\lim_{x\to " +
                        sp.latex(a) +
                        r"} " + sp.latex(funcion)
                    )

                    graficar_limite(funcion, a, x)

            except Exception:
                st.error("No se pudo interpretar la función.")

    else:
        st.info("Introduce una función para graficarla.")