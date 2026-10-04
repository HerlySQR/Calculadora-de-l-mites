import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import sympy as sp

# CONFIGURACIÓN

st.set_page_config(
    page_title="Calculadora matemática",
    page_icon="📘",
    layout="wide"
)


# Variable simbólica
x = sp.symbols("x")

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


# APÉNDICE

if seccion == "Apéndice":
    st.header("Apéndice")
    st.write("Aquí encontrarás definiciones y resultados auxiliares.")


# LÍMITES

elif seccion == "Límite":
    st.header("Límites")
    st.write("Introduce una función y el valor al que se aproxima x.")

    # INGRESAR FUNCIÓN

    funcion_texto = st.text_input("Función f(x)", value = "sin(x)/x", key = "funcion_limite")

    # PUNTO AL QUE SE ACERCA x

    a = st.number_input("x se aproxima a", value = 0.0, step = 0.1, format = "%.6f", key = "punto_limite")


    # BOTÓN ANALIZAR

    if st.button("Analizar límite", type = "primary", key = "analizar_limite"):

        try:
            # Convertir el texto a una expresión de SymPy
            funcion = sp.sympify(funcion_texto)

            # Verificar que solamente aparezca x
            if funcion.free_symbols - {x}:
                st.error("La función solamente puede utilizar la variable x.")
                st.stop()


            # Mostrar la función
            st.latex(r"f(x) = " + sp.latex(funcion))

            # CALCULAR LOS LÍMITES

            with st.spinner("Analizando el comportamiento de la función..."):
                limite_izquierdo = sp.limit(funcion, x, a, dir = "-")
                limite_derecho = sp.limit(funcion, x, a, dir="+")
                limite = sp.limit(funcion, x, a)

            # MOSTRAR LÍMITES LATERALES

            col1, col2 = st.columns(2)

            with col1:
                st.subheader("Límite por la izquierda")
                st.latex(r"\lim_{x\to " + sp.latex(a) + r"^-} f(x)" r" = " + sp.latex(limite_izquierdo))

            with col2:
                st.subheader("Límite por la derecha")

                st.latex(r"\lim_{x\to " + sp.latex(a) + r"^+} f(x)" r" = " + sp.latex(limite_derecho))


            # DETECCIÓN DEL TIPO DE COMPORTAMIENTO

            # ¿El límite izquierdo es infinito?
            es_infinito_izq = limite_izquierdo in (sp.oo, -sp.oo)

            # ¿El límite derecho es infinito?
            es_infinito_der = limite_derecho in (sp.oo, -sp.oo)

            # CASO 1: ASÍNTOTA VERTICAL

            if es_infinito_izq or es_infinito_der:
                st.error(f"Se detectó una asíntota vertical en x = {a}")

                if es_infinito_izq:
                    st.write(f"Por la izquierda: " f"{sp.latex(limite_izquierdo)}")

                if es_infinito_der:
                    st.write(f"Por la derecha: " f"{sp.latex(limite_derecho)}")

                tipo_grafica = "asintota"


            # CASO 2: LÍMITES LATERALES IGUALES

            elif sp.simplify(limite_izquierdo - limite_derecho) == 0:
                limite_finito = limite

                # Intentamos calcular f(a)
                try:
                    valor_a = funcion.subs(x, a)
                except Exception:
                    valor_a = sp.nan

                # DISCONTINUIDAD REMOVIBLE

                if (
                    valor_a is sp.nan
                    or valor_a.has(sp.zoo)
                    or valor_a.has(sp.oo)
                    or valor_a.has(-sp.oo)
                    or valor_a != limite_finito
                ):
                    st.warning("Se detectó una discontinuidad removible.")

                    st.write(
                        "El límite existe y es finito, "
                        "pero la función no coincide con el "
                        "límite en x = a."
                    )

                    st.latex(r"\lim_{x\to " + sp.latex(a) + r"} f(x) = " + sp.latex(limite_finito))

                    tipo_grafica = "removible"

                # FUNCIÓN CONTINUA

                else:
                    st.success("La función es continua en el punto analizado.")

                    st.latex(r"\lim_{x\to " + sp.latex(a) + r"} f(x) = " + sp.latex(limite_finito))

                    tipo_grafica = "continua"


            # CASO 3: LÍMITES LATERALES DIFERENTES

            else:
                st.warning(
                    "Los límites laterales son diferentes. "
                    "Por lo tanto, el límite bilateral no existe."
                )

                st.latex(r"\lim_{x\to " + sp.latex(a) + r"} f(x)" r"\quad\text{no existe}")

                tipo_grafica = "diferentes"

            # CONVERTIR FUNCIÓN SIMBÓLICA EN FUNCIÓN NUMÉRICA

            f = sp.lambdify(x, funcion, modules = ["numpy"])

            # ELEGIR AUTOMÁTICAMENTE EL INTERVALO

            escala = max(1.0, abs(float(a)))

            radio = 0.5 * escala

            xmin = float(a) - radio
            xmax = float(a) + radio

            # PARTE IZQUIERDA

            izquierda = np.linspace(xmin, float(a) - radio * 1e-5, 2500)

            # PARTE DERECHA

            derecha = np.linspace(float(a) + radio * 1e-5, xmax, 2500)

            # FUNCIÓN PARA EVALUAR NUMÉRICAMENTE

            def evaluar(valores_x):
                with np.errstate(
                    divide="ignore",
                    invalid="ignore",
                    over="ignore"
                ):

                    valores_y = np.asarray(f(valores_x), dtype = float)


                # Si la función devuelve un escalar
                if valores_y.ndim == 0:
                    valores_y = np.full_like(valores_x, valores_y.item())

                # Asegurar mismo tamaño
                valores_y = np.broadcast_to(valores_y, valores_x.shape).astype(float, copy = True)

                # Convertir valores inválidos en NaN
                valores_y[~np.isfinite(valores_y)] = np.nan

                return valores_y

            # Evaluar ambos lados
            y_izquierda = evaluar(izquierda)
            y_derecha = evaluar(derecha)

            # OBTENER VALORES PARA LA ESCALA VERTICAL

            valores = np.concatenate([
                np.abs(y_izquierda[np.isfinite(y_izquierda)]),
                np.abs(y_derecha[np.isfinite(y_derecha)])
            ])

            if valores.size == 0:
                st.error(
                    "No se encontraron valores que puedan "
                    "representarse en la gráfica."
                )

                st.stop()

            # ELEGIR AMPLITUD PARA ASÍNTOTA

            if tipo_grafica == "asintota":
                amplitud = np.percentile(valores, 90)
                amplitud *= 1.15

            # ESCALA PARA LÍMITES FINITOS

            else:
                try:
                    limite_num = float(sp.N(limite))
                except Exception:
                    limite_num = 0.0

                distancia = np.abs(valores - limite_num)

                distancia = distancia[np.isfinite(distancia)]

                if distancia.size > 0:
                    amplitud_vertical = np.percentile(distancia, 95)
                else:
                    amplitud_vertical = 1.0

                amplitud_vertical = max(amplitud_vertical, 0.5)

                ymin = (limite_num - amplitud_vertical)

                ymax = (limite_num + amplitud_vertical)

            # CREAR GRÁFICA

            fig, ax = plt.subplots(figsize = (10, 5))

            # GRÁFICA DE ASÍNTOTA

            if tipo_grafica == "asintota":
                ax.plot(izquierda, y_izquierda, label = "x < a")
                ax.plot(derecha, y_derecha, label = "x > a")
                ax.set_ylim(-amplitud, amplitud)

            # GRÁFICA NORMAL

            else:
                ax.plot(izquierda, y_izquierda, color = "blue")
                ax.plot(derecha, y_derecha, color="blue")
                ax.set_ylim(ymin, ymax)

            # LÍNEA x = a

            ax.axvline(float(a), color = "red", linestyle = "--", linewidth = 1, label = f"x = {a:g}")

            # LÍNEA HORIZONTAL DEL LÍMITE

            if (tipo_grafica == "continua" or tipo_grafica == "removible"):
                
                try:
                    limite_num = float(sp.N(limite))
                    ax.axhline(limite_num, color = "green", linestyle = ":", linewidth = 1, label = f"Límite = {limite_num:g}")
                except Exception:
                    pass

            # EJE X

            ax.axhline(0, color = "black", linewidth = 0.7)

            # CONFIGURACIÓN DE LA GRÁFICA

            ax.set_xlim(xmin, xmax)

            ax.set_xlabel("x")

            ax.set_ylabel("f(x)")

            ax.set_title(f"Comportamiento de f(x) cuando x → {a:g}")

            ax.grid(True, alpha = 0.3)

            ax.legend()


            # Mostrar gráfica en Streamlit
            st.pyplot(fig)

            # Liberar memoria de Matplotlib
            plt.close(fig)
        except Exception as e:
            pass

# OTRAS SECCIONES

elif seccion == "Derivada":
    st.header("Derivadas")
    st.write("Aquí encontrarás teoría y ejemplos de derivadas.")

elif seccion == "Integral":
    st.header("Integrales")
    st.write("Aquí encontrarás teoría y ejemplos de integrales.")

elif seccion == "Suma infinita":
    st.header("Sumas infinitas")
    st.write("Aquí encontrarás teoría y ejemplos de series.")