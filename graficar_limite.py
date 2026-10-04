import streamlit as st
import sympy as sp
import numpy as np
import matplotlib.pyplot as plt

def graficar_limite(funcion, a, x):
    f = sp.lambdify(x, funcion, modules=["numpy"])

    escala = max(5.0, abs(a))
    radio = 0.5 * escala

    # Muestreo más fino cerca de a
    distancias = np.geomspace(radio, radio * 1e-8, 1500)

    # Separar ambos lados para no cruzar una asíntota
    x_izq = a - distancias
    x_der = (a + distancias)[::-1]

    def evaluar(valores_x):
        with np.errstate(
            divide="ignore",
            invalid="ignore",
            over="ignore"
        ):
            valores_y = np.asarray(f(valores_x), dtype=float)

        if valores_y.ndim == 0:
            valores_y = np.full_like(valores_x, valores_y.item())

        valores_y = np.broadcast_to(valores_y, valores_x.shape).astype(float, copy=True)

        valores_y[~np.isfinite(valores_y)] = np.nan
        return valores_y

    y_izq = evaluar(x_izq)
    y_der = evaluar(x_der)

    # Calcular una amplitud vertical automática y robusta
    valores_finitos = np.concatenate([
        np.abs(y_izq[np.isfinite(y_izq)]),
        np.abs(y_der[np.isfinite(y_der)])
    ])

    if valores_finitos.size == 0:
        st.error("No se encontraron valores finitos para graficar.")
        return

    amplitud = np.percentile(valores_finitos, 80)

    # Evitar una escala nula o demasiado pequeña
    amplitud = max(amplitud * 1.15, 1e-6)

    fig, ax = plt.subplots(figsize=(10, 5))

    # Graficar cada lado por separado
    ax.plot(x_izq, y_izq, label="x < a")
    ax.plot(x_der, y_der, label="x > a")

    ax.axvline(
        a, color="red", linestyle="--",
        label=f"x → {a:g}"
    )
    ax.axhline(0, color="black", linewidth=0.7)

    # Amplitud vertical calculada automáticamente
    ax.set_ylim(-amplitud, amplitud)
    ax.set_xlim(a - radio, a + radio)

    ax.set_xlabel("x")
    ax.set_ylabel("f(x)")
    ax.set_title("Gráfica para estudiar el límite")
    ax.grid(True, alpha=0.3)
    ax.legend()

    st.pyplot(fig)
    plt.close(fig)

    st.caption(
        f"Escala vertical automática: "
        f"de {-amplitud:.4g} a {amplitud:.4g}"
    )
