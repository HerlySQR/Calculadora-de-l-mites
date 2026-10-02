
import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

st.set_page_config(
    page_title="Simulador de calor",
    page_icon="🌡️",
    layout="wide"
)

st.title("Simulador de la ecuación de calor")
st.write(
    "Observa cómo evoluciona la temperatura "
    "en una barra cuyos extremos están a temperatura cero."
)

st.latex(r"\frac{\partial u}{\partial t}"
         r"=\alpha\frac{\partial^2u}{\partial x^2}")

st.sidebar.header("Parámetros")

alpha = st.sidebar.slider(
    "Difusividad térmica α",
    min_value=0.01,
    max_value=1.0,
    value=0.1,
    step=0.01
)

tiempo = st.sidebar.slider(
    "Tiempo de simulación",
    min_value=0.0,
    max_value=1.0,
    value=0.2,
    step=0.01
)

# Solución analítica para u(x,0) = sin(pi*x)
x = np.linspace(0, 1, 400)
u = np.exp(-alpha * np.pi**2 * tiempo) * np.sin(np.pi * x)

fig, ax = plt.subplots()
ax.plot(x, u, label=f"t = {tiempo:.2f}")
ax.set_xlabel("Posición x")
ax.set_ylabel("Temperatura u(x,t)")
ax.set_title("Distribución de temperatura")
ax.grid(True)
ax.legend()

st.pyplot(fig)
plt.close(fig)

st.metric("Difusividad térmica", f"{alpha:.2f}")
st.metric("Temperatura máxima", f"{np.max(u):.4f}")

st.caption(
    "Modelo: solución analítica de la ecuación de calor "
    "con extremos a temperatura cero."
)