
import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
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

if seccion == "Apéndice":
    st.header("Apéndice")
    st.write("Aquí encontrarás definiciones y resultados auxiliares.")

else:
    st.header(seccion)

    st.write(
        "Escribe una función matemática utilizando x "
        "como variable independiente."
    )

    funcion_texto = st.text_input(
        "Función f(x)",
        value="sin(x)/x",
        key="funcion_" + seccion
    )

    col1, col2 = st.columns(2)

    with col1:
        xmin = st.number_input(
            "Extremo izquierdo",
            value=-10.0,
            key="xmin_" + seccion
        )

    with col2:
        xmax = st.number_input(
            "Extremo derecho",
            value=10.0,
            key="xmax_" + seccion
        )

    if st.button("Graficar función", type="primary"):
        try:
            # Interpretar la expresión matemática
            funcion = sp.sympify(funcion_texto)

            # Comprobar que solo se use la variable x
            if funcion.free_symbols - {x}:
                st.error("Utiliza únicamente x como variable.")
            elif xmin >= xmax:
                st.error("El extremo izquierdo debe ser menor que el derecho.")
            else:
                f = sp.lambdify(x, funcion, modules=["numpy"])

                valores_x = np.linspace(xmin, xmax, 2000)

                with np.errstate(
                    divide="ignore",
                    invalid="ignore",
                    over="ignore"
                ):
                    valores_y = np.asarray(
                        f(valores_x), dtype=float
                    )

                if valores_y.ndim == 0:
                    valores_y = np.full_like(
                        valores_x, valores_y.item()
                    )

                valores_y = np.broadcast_to(
                    valores_y, valores_x.shape
                ).astype(float, copy=True)

                # Evitar valores no finitos y picos enormes
                valores_y[~np.isfinite(valores_y)] = np.nan
                valores_y[np.abs(valores_y) > 1e6] = np.nan

                if not np.any(np.isfinite(valores_y)):
                    st.warning(
                        "No se encontraron valores finitos "
                        "en el intervalo elegido."
                    )
                else:
                    fig, ax = plt.subplots(figsize=(10, 5))

                    ax.plot(valores_x, valores_y, label=f"f(x) = {funcion}")
                    ax.axhline(0, color="black", linewidth=0.7)
                    ax.axvline(0, color="black", linewidth=0.7)

                    ax.set_xlabel("x")
                    ax.set_ylabel("f(x)")
                    ax.set_title(f"Gráfica de la función — {seccion}")
                    ax.grid(True, alpha=0.3)
                    ax.legend()

                    st.pyplot(fig)
                    plt.close(fig)

                    st.latex(
                        r"f(x)=" + sp.latex(funcion)
                    )

        except Exception:
            st.error(
                "No se pudo interpretar la función. "
                "Revisa que esté escrita correctamente."
            )