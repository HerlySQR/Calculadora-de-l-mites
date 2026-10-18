import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import sympy as sp

import pandas as pd

import utilidad as ut

def detectar_singularidades_numericas(funcion, x, a, b, numero_puntos = 200, umbral = 1e12, refinamientos = 40, tolerancia = 1e-10):
    """
    Detecta numéricamente posibles singularidades de una función en un intervalo finito [a,b].

    Busca:
    - valores no finitos
    - valores muy grandes
    - cambios bruscos
    - cambios de signo asociados a crecimiento muy grande

    Después refina los intervalos sospechosos.
    """

    # COMPROBAR QUE EL INTERVALO SEA FINITO

    if not (a.is_finite is True and b.is_finite is True):
        return []

    a_num = float(sp.N(a))
    b_num = float(sp.N(b))

    if a_num >= b_num:
        return []

    # CONVERTIR LA FUNCIÓN A NUMÉRICA
    funcion_numerica = sp.lambdify(x, funcion, "numpy")

    # EVALUAR UNA FUNCIÓN EN UN PUNTO

    def evaluar(x_valor):
        try:
            with np.errstate(divide = "ignore", invalid = "ignore", over = "ignore"):
                y = funcion_numerica(x_valor)

            y = float(y)

            if np.isfinite(y):
                return y

            return np.nan

        except Exception:
            return np.nan

    # PRIMERA MALLA
    valores_x = np.linspace(a_num, b_num, numero_puntos)

    valores_y = np.array([evaluar(x_valor) for x_valor in valores_x], dtype=float)

    # INTERVALOS SOSPECHOSOS
    intervalos = []

    for i in range(len(valores_x) - 1):
        x1 = valores_x[i]
        x2 = valores_x[i + 1]

        y1 = valores_y[i]
        y2 = valores_y[i + 1]

        # CASO 1: ALGÚN PUNTO NO ES FINITO

        if not (np.isfinite(y1) and np.isfinite(y2)):
            intervalos.append((x1, x2))
            continue

        # CASO 2: VALORES MUY GRANDES

        if (abs(y1) > umbral or abs(y2) > umbral):
            intervalos.append((x1, x2))
            continue

        # CASO 3: CAMBIO DE SIGNO + CRECIMIENTO GRANDE
        # Esto es especialmente útil para tan(x)
        if y1 * y2 < 0:
            diferencia = abs(y2 - y1)

            escala = max(1, abs(y1), abs(y2))

            if (diferencia / escala > 0.9 or abs(y1) > umbral / 10 or abs(y2) > umbral / 10):
                intervalos.append((x1, x2))

        # CASO 4: CAMBIO MUY GRANDE ENTRE LOS DOS PUNTOS
        diferencia = abs(y2 - y1)

        if diferencia > umbral:
            intervalos.append((x1, x2))

    # COMPROBAR TAMBIÉN LOS EXTREMOS
    if not np.isfinite(valores_y[0]):
        intervalos.append((a_num, valores_x[1]))

    if not np.isfinite(valores_y[-1]):
        intervalos.append((valores_x[-2], b_num))

    # REFINAR INTERVALOS SOSPECHOSOS
    candidatos = []

    for izquierda, derecha in intervalos:
        for _ in range(refinamientos):
            medio = (izquierda + derecha) / 2
            y_izquierda = evaluar(izquierda)
            y_derecha = evaluar(derecha)
            y_medio = evaluar(medio)

            # SI EL PUNTO MEDIO NO ES FINITO
            if not np.isfinite(y_medio):
                derecha = medio
                continue

            # SI HAY UN VALOR MUY GRANDE

            if abs(y_medio) > umbral:
                # Determinamos en qué mitad está el comportamiento problemático.
                if (np.isfinite(y_izquierda) and abs(y_izquierda) < abs(y_medio)):
                    izquierda = medio
                else:
                    derecha = medio
                continue

            # CAMBIO DE SIGNO

            if (np.isfinite(y_izquierda) and y_izquierda * y_medio < 0):
                derecha = medio
                continue

            if (np.isfinite(y_derecha) and y_medio * y_derecha < 0):
                izquierda = medio
                continue

            # SI NO HAY UNA SEÑAL CLARA, CONSERVAMOS LA MITAD CON MAYOR VARIACIÓN
            if (np.isfinite(y_izquierda) and np.isfinite(y_derecha)):
                diferencia_izquierda = abs(y_medio - y_izquierda)
                diferencia_derecha = abs(y_derecha - y_medio)

                if (diferencia_izquierda > diferencia_derecha):
                    derecha = medio
                else:
                    izquierda = medio
            else:
                derecha = medio

            # DETENER CUANDO EL INTERVALO ES MUY PEQUEÑO
            if (abs(derecha - izquierda) < tolerancia):
                break

        # CANDIDATO FINAL
        candidato = (izquierda + derecha) / 2
        candidatos.append(candidato)

    # ORDENAR CANDIDATOS
    if not candidatos:
        return []

    candidatos.sort()

    # UNIR CANDIDATOS QUE REPRESENTAN LA MISMA SINGULARIDAD
    distancia_minima = (b_num - a_num) / numero_puntos * 2

    singularidades = []

    grupo = [candidatos[0]]

    for candidato in candidatos[1:]:
        if (candidato - grupo[-1] < distancia_minima):
            grupo.append(candidato)
        else:
            singularidades.append(np.mean(grupo))
            grupo = [candidato]

    singularidades.append(np.mean(grupo))

    # ELIMINAR DUPLICADOS MUY CERCANOS
    resultado = []

    for s in singularidades:
        if not resultado:
            resultado.append(s)
        elif abs(s - resultado[-1]) > tolerancia * 10:
            resultado.append(s)

    return resultado

def extremo_en_cerradura(funcion_numerica, extremo, otro_extremo, lado, numero_pruebas = 20):
    """
    Comprueba numéricamente si el extremo parece
    pertenecer a la cerradura del dominio, mirando
    desde el interior del intervalo.

    lado = 1  : acercarse desde la derecha
    lado = -1 : acercarse desde la izquierda
    """

    longitud = abs(otro_extremo - extremo)

    if longitud == 0 or not np.isfinite(longitud):
        return False

    # Distancias cada vez menores al extremo.
    distancias = longitud * np.geomspace(1e-2, 1e-12, numero_pruebas)

    valores_validos = 0

    for distancia in distancias:
        punto = extremo + lado * distancia

        try:
            with np.errstate(divide = "ignore", invalid = "ignore", over = "ignore"):
                valor = funcion_numerica(punto)

            valor = complex(valor)

            # La función debe tener valores reales definidos cerca del extremo.
            if (np.isfinite(valor.real) and np.isfinite(valor.imag) and abs(valor.imag) < 1e-10):
                valores_validos += 1

        except Exception:
            pass

    # Exigir varios valores válidos muy cerca del extremo, no solo en puntos alejados.
    return valores_validos >= 5

def evaluar_funcion(f, x):
    """Evalúa f en un arreglo y devuelve un arreglo del mismo tamaño."""
    x = np.asarray(x, dtype=float)
    with np.errstate(all = "ignore"):
        y = np.asarray(f(x), dtype = float)

    if y.ndim == 0:
        y = np.full(x.shape, float(y))

    return np.broadcast_to(y, x.shape).astype(float)

def suma_riemann_izquierda(f, a, b, n):
    """Suma de Riemann usando los extremos izquierdos."""
    h = (b - a) / n
    x = a + h * np.arange(n)

    y = np.asarray(f(x), dtype = float)
    if not np.all(np.isfinite(y)):
        return np.nan

    return h * np.sum(y)

def suma_riemann_derecha(f, a, b, n):
    """Suma de Riemann usando los extremos derechos."""
    h = (b - a) / n
    x = a + h * np.arange(1, n + 1)

    y = np.asarray(f(x), dtype = float)
    if not np.all(np.isfinite(y)):
        return np.nan

    return h * np.sum(y)

def metodo_trapecio(f, a, b, n):
    """Regla del trapecio compuesta."""
    h = (b - a) / n
    x = np.linspace(a, b, n + 1)

    y = np.asarray(f(x), dtype = float)
    if not np.all(np.isfinite(y)):
        return np.nan

    return h * (0.5 * y[0] + np.sum(y[1:-1]) + 0.5 * y[-1])

def metodo_simpson(f, a, b, n):
    """Regla de Simpson 1/3 compuesta; n debe ser par."""
    if n % 2 != 0:
        return np.nan

    h = (b - a) / n
    x = np.linspace(a, b, n + 1)

    y = np.asarray(f(x), dtype = float)
    if not np.all(np.isfinite(y)):
        return np.nan

    return (h / 3) * (y[0] + y[-1] + 4 * np.sum(y[1:-1:2]) + 2 * np.sum(y[2:-1:2]))

def ejecutar_integrales():
    st.header("Integrales")
    st.write("Aquí podrás hallar valores y aproximaciones de integrales.")

    # ENTRADAS
    funcion_texto = st.text_input("Función f(x)", value = "1/x")

    # ELEGIR COTAS DE x

    tipo_a = st.selectbox("Límite inferior de x", ["Número", "-∞"], key = "tipo_limite_inferior")

    # SI a ES UN NÚMERO
    if tipo_a == "Número":
        a_texto = st.text_input("Valor del límite inferior", value = "1", key="limite_punto")
        try:
            a = sp.sympify(a_texto)
            if not a.is_real:
                st.error("El punto debe ser real.")
                st.stop()
        except Exception:
            st.error("Introduce un valor válido.")
            st.stop()
    else:
        a = -sp.oo

    tipo_b = st.selectbox("Límite superior de x", ["Número", "+∞"], key = "tipo_limite_superior")

    # SI b ES UN NÚMERO
    if tipo_b == "Número":
        b_texto = st.text_input("Valor del límite superior", value = "exp(1)", key = "limite_superior")
        try:
            b = sp.sympify(b_texto)
            if not b.is_real:
                st.error("El punto debe ser real.")
                st.stop()
        except Exception:
            st.error("Introduce un valor válido.")
            st.stop()
    elif tipo_b == "+∞":
        b = sp.oo

    x = sp.symbols("x")

    # BOTÓN ANALIZAR
    if st.button("Analizar integral", type = "primary", key = "analizar_integral"):

        try:
            # CONVERTIR TEXTO A EXPRESIÓN DE SYMPY
            funcion = sp.sympify(funcion_texto)

            # VERIFICAR QUE SOLO APAREZCA x
            if funcion.free_symbols - {x}:
                st.error("La función solamente puede utilizar la variable x.")
                st.stop()
            
            # VERIFICAR LÍMITES DE INTEGRACIÓN

            if not bool(a < b):
                st.error("El límite inferior debe ser menor que el límite superior.")
                st.stop()

            # La integral ordinaria sobre un intervalo infinito admite estas combinaciones:
            # [número, número], [número, +∞], [-∞, número] y [-∞, +∞].
            
            # DEFINIR EL INTERVALO DE VISUALIZACIÓN
            if a.is_finite is True:
                a_num = float(sp.N(a))
            else:
                a_num = None

            if b.is_finite is True:
                b_num = float(sp.N(b))
            else:
                b_num = None

            # COMPROBAR LOS EXTREMOS FINITOS
            funcion_numerica = sp.lambdify(x, funcion, modules = ["numpy"])
            a_limite = sp.limit(funcion, x, a)
            b_limite = sp.limit(funcion, x, b)

            if a_num is not None and b_num is not None:
                # Ambas cotas son finitas.
                a_graf = a_num
                b_graf = b_num
            elif a_num is not None:
                # [a, +∞)
                a_graf = a_num
                (_, b_graf, _) = ut.encontrar_intervalo_infinito(funcion_numerica, b_limite, 1)
            elif b_num is not None:
                # (-∞, b]
                b_graf = b_num
                (a_graf, _, _) = ut.encontrar_intervalo_infinito(funcion_numerica, a_limite, -1)
            else:
                # (-∞, +∞)
                (a_graf, _, _) = ut.encontrar_intervalo_infinito(funcion_numerica, a_limite, -1)
                (_, b_graf, _) = ut.encontrar_intervalo_infinito(funcion_numerica, b_limite, 1)

            if a_num is not None:
                inferior_valido = extremo_en_cerradura(funcion_numerica, a_num, b_graf, lado = 1)

                if not inferior_valido:
                    st.error("El límite inferior parece no pertenecer a la cerradura del dominio de la función.")
                    st.stop()

            if b_num is not None:
                superior_valido = extremo_en_cerradura(funcion_numerica, b_num, a_graf, lado = -1)

                if not superior_valido:
                    st.error("El límite superior parece no pertenecer a la cerradura del dominio de la función.")
                    st.stop()

            # DETECTAR POSIBLES SINGULARIDADES

            singularidades = detectar_singularidades_numericas(funcion, x, sp.Float(a_graf), sp.Float(b_graf))

            if singularidades:
                texto = ", ".join(f"{s:.6g}" for s in singularidades)
                st.warning("Posibles singularidades dentro de la ventana examinada: " + texto)
            else:
                st.info("No se detectaron posibles singularidades en la ventana examinada.")

            # CALCULAR INTEGRAL

            with st.spinner("Calculando la integral..."):
                try:
                    if a.is_finite is True and b.is_finite is True:
                        integral = sp.integrate(funcion, (x, a, b))
                    elif a.is_finite is True and b == sp.oo:
                        # Integral desde a hasta +∞: límite de la integral desde a hasta T.
                        T = sp.symbols("T", real=True)
                        integral_truncada = sp.integrate(funcion, (x, a, T))
                        integral = sp.limit(integral_truncada, T, sp.oo)

                    elif a == -sp.oo and b.is_finite is True:
                        # Integral desde -∞ hasta b.
                        T = sp.symbols("T", real=True)
                        integral_truncada = sp.integrate(funcion, (x, T, b))
                        integral = sp.limit(integral_truncada, T, -sp.oo)

                    elif a == -sp.oo and b == sp.oo:
                        # Separamos en dos integrales para evitar confundir convergencia con valor principal.
                        izquierda = sp.integrate(funcion, (x, -sp.oo, 0))
                        derecha = sp.integrate(funcion, (x, 0, sp.oo))
                        integral = sp.simplify(izquierda + derecha)

                    else:
                        st.error("Combinación de límites no válida.")
                        st.stop()

                except Exception as error:
                    st.error("No se pudo calcular la integral: " + str(error))
                    st.stop()
            
            # GUARDAR LOS RESULTADOS PARA LAS SIGUIENTES EJECUCIONES
            st.session_state["datos_integral"] = {
                "funcion": funcion,
                "a": a,
                "b": b,
                "a_num": a_num,
                "b_num": b_num,
                "a_graf": a_graf,
                "b_graf": b_graf,
                "singularidades": singularidades,
                "integral": integral,
            }
        except Exception as error:
            st.error("No se pudo analizar la función. Revisa que esté escrita correctamente.")
            print(f"Error: {error}")

    # MOSTRAR RESULTADO, TABLA Y GRÁFICA INTERACTIVA

    datos = st.session_state.get("datos_integral")

    if datos is not None:
        funcion = datos["funcion"]
        a = datos["a"]
        b = datos["b"]
        a_num = datos["a_num"]
        b_num = datos["b_num"]
        a_graf = datos["a_graf"]
        b_graf = datos["b_graf"]
        singularidades = datos["singularidades"]
        integral = datos["integral"]

        funcion_numerica = sp.lambdify(x, funcion, modules = ["numpy"])

        # RESULTADO SIMBÓLICO

        st.subheader("Resultado de la integral")

        st.latex(r"\int_{" + sp.latex(a) + r"}^{" + sp.latex(b) + r"} " + sp.latex(funcion) + r"\,dx = " + sp.latex(integral))

        if isinstance(integral, sp.Integral):
            st.warning("SymPy dejó una integral sin evaluar. No se ha confirmado su convergencia.")
        elif integral in (sp.oo, -sp.oo, sp.zoo, sp.nan):
            st.error("La integral no tiene un valor finito según el resultado simbólico.")
        elif integral.is_finite is True:
            st.success(
                "Se obtuvo un resultado finito simbólico. "
                "Las singularidades interiores requieren un "
                "análisis adicional de convergencia."
            )
        else:
            st.warning("No se pudo confirmar automáticamente la convergencia.")

        # TABLA DE APROXIMACIONES

        metodo_seleccionado = None
        n_seleccionado = None

        if a_num is not None and b_num is not None:
            st.subheader("Aproximaciones numéricas")

            particiones = [2, 4, 8, 16, 32, 64, 128]
            resultados = []

            for n in particiones:
                resultados.append({
                    "Particiones (n)": n,
                    "Riemann izquierda": suma_riemann_izquierda(funcion_numerica, a_num, b_num, n),
                    "Riemann derecha": suma_riemann_derecha(funcion_numerica, a_num, b_num, n),
                    "Trapecio": metodo_trapecio(funcion_numerica, a_num, b_num, n),
                    "Simpson": metodo_simpson(funcion_numerica, a_num, b_num, n),
                })

            tabla = pd.DataFrame(resultados)

            evento = st.dataframe(
                tabla,
                hide_index = True,
                use_container_width = True,
                on_select = "rerun",
                selection_mode = "single-cell",
                key = "tabla_integrales_interactiva",
                column_config = {
                    "Particiones (n)": st.column_config.NumberColumn(format = "%d"),
                    "Riemann izquierda": st.column_config.NumberColumn(format = "%.10g"),
                    "Riemann derecha": st.column_config.NumberColumn(format = "%.10g"),
                    "Trapecio": st.column_config.NumberColumn(format = "%.10g"),
                    "Simpson": st.column_config.NumberColumn(format = "%.10g"),
                },
            )

            celdas = evento.selection.cells

            if celdas:
                fila, nombre_columna = celdas[0]

                # Obtener el valor de la celda seleccionada
                valor = tabla.loc[fila, nombre_columna]

                # Guardar el método y el número de particiones
                if nombre_columna in [
                    "Riemann izquierda",
                    "Riemann derecha",
                    "Trapecio",
                    "Simpson"
                ]:
                    metodo_seleccionado = nombre_columna
                    n_seleccionado = int(tabla.iloc[fila]["Particiones (n)"])
                else:
                    # Se seleccionó la columna de particiones
                    metodo_seleccionado = None
                    n_seleccionado = None
            else:
                metodo_seleccionado = None
                n_seleccionado = None

        else:
            st.info(
                "La tabla de métodos numéricos requiere límites "
                "finitos. La gráfica seguirá mostrando la ventana "
                "finita seleccionada para la integral impropia."
            )

        # -------------------------------------------------
        # C. CONSTRUIR UNA ÚNICA GRÁFICA
        # -------------------------------------------------

        st.subheader("Gráfica de la función y sus aproximaciones")

        numero_puntos = 4000
        valores_x = np.linspace(a_graf, b_graf, numero_puntos)

        with np.errstate(divide = "ignore", invalid = "ignore", over = "ignore"):
            valores_y = np.asarray(funcion_numerica(valores_x), dtype = float)

        if valores_y.ndim == 0:
            valores_y = np.full_like(valores_x, valores_y.item())

        valores_y = np.broadcast_to(valores_y, valores_x.shape).astype(float, copy=True)

        valores_y[~np.isfinite(valores_y)] = np.nan

        singularidades_grafica = sorted(
            s for s in singularidades if a_graf < s < b_graf
        )

        paso_grafica = ((b_graf - a_graf) / (numero_puntos - 1))
        margen_singularidad = 3 * paso_grafica

        for s in singularidades_grafica:
            valores_y[np.abs(valores_x - s) < margen_singularidad] = np.nan

        valores_finitos = valores_y[np.isfinite(valores_y)]

        if len(valores_finitos) == 0:
            st.warning("No hay suficientes valores finitos para graficar.")
        else:
            # Escala vertical: percentiles solamente si hay singularidades.
            if singularidades_grafica:
                minimo_y, maximo_y = np.percentile(valores_finitos, [2, 98])
            else:
                minimo_y = np.min(valores_finitos)
                maximo_y = np.max(valores_finitos)

            if minimo_y == maximo_y:
                margen_y = max(1.0, abs(minimo_y) * 0.1)
            else:
                margen_y = 0.08 * (maximo_y - minimo_y)

            minimo_y -= margen_y
            maximo_y += margen_y

            fig, ax = plt.subplots(figsize=(11, 6))

            ax.plot(valores_x, valores_y, color = "blue", linewidth = 1.8, label = r"$f(x)$")

            ax.axhline(0, color="black", linewidth=0.8)

            # Si no se seleccionó ningún método, mostrar el área original.
            if metodo_seleccionado is None:
                cortes = [a_graf, *singularidades_grafica, b_graf]

                for izquierda, derecha in zip(cortes[:-1], cortes[1:]):
                    mascara = (
                        (valores_x >= izquierda)
                        & (valores_x <= derecha)
                        & np.isfinite(valores_y)
                        & (valores_y >= minimo_y)
                        & (valores_y <= maximo_y)
                    )

                    if np.any(mascara):
                        ax.fill_between(valores_x[mascara], valores_y[mascara], 0, alpha = 0.2,)

            # Marcar singularidades detectadas.
            for i, s in enumerate(singularidades_grafica):
                ax.axvline(
                    s,
                    color = "red",
                    linestyle = "--",
                    linewidth = 1.3,
                    label = ("Posible singularidad" if i == 0 else None),
                )

            # DIBUJAR EL MÉTODO SELECCIONADO

            if metodo_seleccionado is not None:
                n = n_seleccionado
                h = (b_num - a_num) / n

                x_nodos = np.linspace(a_num, b_num, n + 1)

                with np.errstate(all="ignore"):
                    y_nodos = np.asarray(funcion_numerica(x_nodos), dtype = float)

                if not np.all(np.isfinite(y_nodos)):
                    st.warning("Algún nodo coincide con un valor no finito. No se pueden dibujar todas las particiones.")

                else:
                    # Riemann por la izquierda.
                    if metodo_seleccionado == "Riemann izquierda":
                        ax.bar(
                            x_nodos[:-1],
                            y_nodos[:-1],
                            width = h,
                            align = "edge",
                            alpha = 0.35,
                            edgecolor = "blue",
                            label = f"Riemann izquierda (n={n})",
                        )

                    # Riemann por la derecha.
                    elif metodo_seleccionado == "Riemann derecha":
                        ax.bar(
                            x_nodos[:-1],
                            y_nodos[1:],
                            width = h,
                            align = "edge",
                            alpha = 0.35,
                            color = "lightgreen",
                            edgecolor = "green",
                            label = f"Riemann derecha (n={n})",
                        )

                    # Regla del trapecio.
                    elif metodo_seleccionado == "Trapecio":
                        for i in range(n):
                            ax.fill(
                                [x_nodos[i], x_nodos[i], x_nodos[i + 1], x_nodos[i + 1],],
                                [0, y_nodos[i], y_nodos[i + 1], 0,],
                                color = "orange",
                                alpha = 0.3,
                                edgecolor = "darkorange",
                            )

                        ax.plot(
                            x_nodos,
                            y_nodos,
                            "o--",
                            color = "darkorange",
                            markersize = 3,
                            label = f"Trapecios (n={n})",
                        )

                    # Regla de Simpson: parábolas por pares de subintervalos.
                    elif metodo_seleccionado == "Simpson":
                        for i in range(0, n, 2):
                            xp = x_nodos[i:i + 3]
                            yp = y_nodos[i:i + 3]

                            coeficientes = np.polyfit(xp, yp, 2)
                            polinomio = np.poly1d(coeficientes)

                            xc = np.linspace(xp[0], xp[-1], 100)
                            yc = polinomio(xc)

                            ax.fill_between(
                                xc, yc, 0,
                                color = "purple",
                                alpha = 0.2,
                            )

                            ax.plot(
                                xc, yc,
                                color = "purple",
                                linewidth = 2,
                            )

                        ax.plot(
                            [], [],
                            color = "purple",
                            linewidth = 2,
                            label = f"Parábolas de Simpson (n={n})",
                        )

                    # Líneas verticales para identificar los subintervalos.
                    for xn in x_nodos:
                        ax.axvline(
                            xn,
                            color = "gray",
                            alpha = 0.25,
                            linewidth = 0.7,
                        )

                    ax.scatter(
                        x_nodos,
                        y_nodos,
                        color = "red",
                        s = 18,
                        zorder = 5,
                        label = "Nodos",
                    )

                    ax.set_title(f"{metodo_seleccionado} — {n} particiones")
            else:
                ax.set_title("Función y área: selecciona una celda numérica de la tabla")

            ax.set_xlim(a_graf, b_graf)
            ax.set_ylim(minimo_y, maximo_y)
            ax.set_xlabel("x")
            ax.set_ylabel("f(x)")
            ax.grid(True, alpha = 0.3)
            ax.legend()
            fig.tight_layout()

            st.pyplot(fig)
            plt.close(fig)

            if a == -sp.oo or b == sp.oo:
                st.caption(
                    f"La gráfica muestra la ventana finita "
                    f"[{a_graf:.6g}, {b_graf:.6g}] de la integral impropia."
                )