import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import sympy as sp

from matplotlib.ticker import FuncFormatter

def ejecutar_derivadas():
    st.header("Derivada")
    st.write("Calcula si la derivada de una función existe en un punto, determina su valor y muestra la recta tangente.")

    # ENTRADAS
    funcion_texto = st.text_input("Función f(x)", value = "x**2")
    a_texto = st.text_input("Punto x = a (Para hallar f'(a))", value = "1")

    if st.button("Analizar derivada", type = "primary", key = "analizar_derivada"):
        try:
            # INTERPRETACIÓN DE LA FUNCIÓN
            x = sp.symbols("x")

            funcion = sp.sympify(funcion_texto)

            a = sp.sympify(a_texto)

            if not a.is_real:
                st.error("El punto a debe ser real.")
                st.stop()

            a_num = float(sp.N(a))

            # VALOR f(a)
            try:
                valor_a = sp.simplify(funcion.subs(x, a))
            except Exception:
                valor_a = sp.nan

            if valor_a.is_finite is not True:
                st.error("La función no está definida de forma finita en x = a.")
                st.stop()

            # DEFINICIÓN DE LA DERIVADA
            h = sp.symbols("h", real = True)

            cociente = sp.simplify((funcion.subs(x, a + h) - valor_a) / h)

            # LÍMITES LATERALES DEL COCIENTE
            try:
                derivada_izquierda = sp.limit(cociente, h, 0, dir = "-")
            except Exception:
                derivada_izquierda = sp.nan

            try:
                derivada_derecha = sp.limit(cociente, h, 0, dir = "+")
            except Exception:
                derivada_derecha = sp.nan

            # COMPROBAR SI COINCIDEN
            coinciden = False

            try:
                if (derivada_izquierda.is_finite is True and derivada_derecha.is_finite is True):
                    coinciden = bool(sp.simplify(derivada_izquierda - derivada_derecha) == 0)
                elif derivada_izquierda == derivada_derecha:
                    coinciden = True
            except Exception:
                coinciden = False

            # CLASIFICACIÓN
            izquierda_infinita = (derivada_izquierda == sp.oo or derivada_izquierda == -sp.oo)
            derecha_infinita = (derivada_derecha == sp.oo or derivada_derecha == -sp.oo)

            derivada_finita = (coinciden and derivada_izquierda.is_finite is True and derivada_derecha.is_finite is True)
            derivada_infinita = (coinciden and (izquierda_infinita or derecha_infinita))

            # RESULTADO
            st.subheader("Resultado")

            if derivada_finita:
                derivada = derivada_izquierda
                st.success("La derivada existe y es finita.")

                st.latex(r"\boxed{f'(" + sp.latex(a) + r")=" + sp.latex(derivada) + r"}")

            elif derivada_infinita:
                st.warning("La derivada es infinita.")

                if derivada_izquierda == sp.oo:
                    signo = "+\\infty"
                elif derivada_izquierda == -sp.oo:
                    signo = "-\\infty"
                else:
                    signo = "\\infty"

                st.latex(r"\boxed{f'(" + sp.latex(a) + r")=" + signo + r"}")
                st.info("La gráfica presenta una tangente vertical en este punto.")

            elif (izquierda_infinita or derecha_infinita):
                st.warning("La derivada no existe como número real finito porque los comportamientos laterales no coinciden.")

            else:
                st.warning("La derivada no existe en este punto.")

            # LÍMITES LATERALES
            st.subheader("Límites de la definición de la derivada")

            col1, col2 = st.columns(2)

            with col1:
                st.latex(r"\lim_{h\to0^-}" r"\frac{f(a+h)-f(a)}{h}" r"=" + sp.latex(derivada_izquierda))

            with col2:
                st.latex(r"\lim_{h\to0^+}" r"\frac{f(a+h)-f(a)}{h}" r"="+ sp.latex(derivada_derecha))

            # TABLA ADAPTATIVA

            if derivada_finita:
                st.subheader("Aproximación de la derivada")

                derivada_num = float(sp.N(derivada))

                valor_a_num = float(sp.N(valor_a))

                # Convertimos la expresión simbólica en una función numérica de NumPy
                funcion_numerica = sp.lambdify(x, funcion, "numpy")

                def generar_puntos_derivada(derivada_num):
                    # Valores candidatos para |h|
                    candidatos = np.geomspace(1e-1, 1e-12, 200)

                    datos_izquierda = []
                    datos_derecha = []

                    for h_abs in candidatos:
                        # IZQUIERDA: h < 0
                        h_izquierda = -h_abs

                        x_izquierda = (a_num + h_izquierda)

                        try:
                            with np.errstate(divide = "ignore", invalid = "ignore", over = "ignore"):
                                cociente_izquierda = (float(funcion_numerica(x_izquierda)) - valor_a_num) / h_izquierda

                            if np.isfinite(cociente_izquierda):
                                datos_izquierda.append({
                                    "h": h_izquierda,
                                    "x": x_izquierda,
                                    "cociente": cociente_izquierda
                                })

                        except (ValueError, TypeError, OverflowError):
                            pass

                        # DERECHA: h > 0
                        h_derecha = h_abs

                        x_derecha = (a_num + h_derecha)

                        try:
                            with np.errstate(divide = "ignore", invalid = "ignore", over = "ignore"):
                                cociente_derecha = (float(funcion_numerica(x_derecha)) - valor_a_num) / h_derecha

                            if np.isfinite(cociente_derecha):
                                datos_derecha.append({
                                    "h": h_derecha,
                                    "x": x_derecha,
                                    "cociente": cociente_derecha
                                })

                        except (ValueError, TypeError, OverflowError):
                            pass

                    # SELECCIÓN DE PUNTOS
                    def seleccionar_puntos(datos, max_puntos = 10):
                        if len(datos) == 0:
                            return []

                        if len(datos) <= max_puntos:
                            return datos

                        indices = np.linspace(0, len(datos) - 1, max_puntos).astype(int)

                        return [datos[i] for i in indices]

                    return (seleccionar_puntos(datos_izquierda), seleccionar_puntos(datos_derecha))

                puntos_izquierda, puntos_derecha = (generar_puntos_derivada(derivada_num))

                # TABLA IZQUIERDA
                if puntos_izquierda:
                    st.markdown("Aproximación por la izquierda")

                    tabla_izquierda = []

                    for punto in puntos_izquierda:
                        tabla_izquierda.append({
                            "h": punto["h"],
                            "x = a + h": punto["x"],
                            "Cociente incremental": punto["cociente"]
                        })

                    st.dataframe(tabla_izquierda, use_container_width = True, hide_index = True)

                # TABLA DERECHA
                if puntos_derecha:
                    st.markdown("Aproximación por la derecha")

                    tabla_derecha = []

                    for punto in puntos_derecha:
                        tabla_derecha.append({
                            "h": punto["h"],
                            "x = a + h": punto["x"],
                            "Cociente incremental": punto["cociente"]
                        })

                    st.dataframe(tabla_derecha, use_container_width = True, hide_index = True)

                if not puntos_izquierda and not puntos_derecha:
                    st.info("No se pudieron obtener valores numéricos para construir la tabla.")

            # GRÁFICA
            st.subheader("Gráfica")

            # Determinar amplitud
            distancia_grafica = 0.5

            if derivada_finita:
                todos_h = []

                for dato in puntos_izquierda:
                    todos_h.append(abs(dato["h"]))

                for dato in puntos_derecha:
                    todos_h.append(abs(dato["h"]))

                if len(todos_h) > 0:
                    distancia_minima = min(todos_h)
                    distancia_grafica = max(0.1, distancia_minima * 20)

            # Coordenada local
            valores_u = np.linspace(-distancia_grafica, distancia_grafica, 1000)
            valores_x = (a_num + valores_u)

            # Evaluar función
            try:
                valores_y = np.asarray(sp.lambdify(x, funcion, "numpy")(valores_x), dtype = float)

                if valores_y.ndim == 0:
                    valores_y = np.full_like(valores_x, valores_y.item())

                valores_y = np.broadcast_to(valores_y, valores_x.shape).astype(float, copy = True)

                valores_y[~np.isfinite(valores_y)] = np.nan

                # Crear gráfica
                fig, ax = plt.subplots()

                ax.plot(valores_u, valores_y, label = "f(x)")

                # Punto donde se calcula la derivada
                ax.scatter([0], [float(sp.N(valor_a))], zorder = 5, label=f"({a_num:g}, {float(sp.N(valor_a)):g})")

                # Recta tangente
                if derivada_finita:
                    pendiente = derivada_num
                    valor_funcion_num = float(sp.N(valor_a) )

                    valores_tangente = (valor_funcion_num + pendiente * valores_u)

                    ax.plot(valores_u, valores_tangente, linestyle="--", label = "Recta tangente")

                # Tangente vertical
                elif derivada_infinita:
                    ax.axvline(0, linestyle = "--",  label = "Tangente vertical")

                # Escala
                ax.set_xlim(-distancia_grafica, distancia_grafica)

                # Etiquetas del eje x
                def formatear_eje_x(valor_u, posicion):
                    valor_x = (a_num + valor_u)
                    return f"{valor_x:.6g}"

                ax.xaxis.set_major_formatter(FuncFormatter(formatear_eje_x))

                ax.set_xlabel("x")
                ax.set_ylabel("f(x)")

                ax.grid(True)
                ax.legend()

                st.pyplot(fig)

            except Exception:
                st.warning("No se pudo generar la gráfica para esta función.")

        except Exception as error:
            st.error("No se pudo analizar la función. Verifica que la expresión y el punto sean válidos.")