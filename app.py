import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import sympy as sp

from matplotlib.ticker import FuncFormatter

import threading
import queue

# CONFIGURACIÓN

st.set_page_config(
    page_title = "Calculadora matemática",
    page_icon = "📘",
    layout = "wide"
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

# FUNCIÓN PARA MOSTRAR NÚMEROS, ELIMINANDO CEROS INNECESARIOS
def quitar_ceros(valor):
    if not np.isfinite(valor):
        return str(valor)
    return f"{valor:.12f}".rstrip("0").rstrip(".")

def encontrar_intervalo_infinito(f, limite, direccion, tolerancia = 0.01, minimo = 2, maximo = 1e8):
    x_actual = float(minimo)

    # Número de puntos consecutivos que deben estar suficientemente cerca del límite
    puntos_convergencia = 3

    consecutivos = 0
    ultimo_x = x_actual

    for _ in range(30):
        # Elegir x según la dirección
        if direccion == 1:
            x_valor = x_actual
        else:
            x_valor = -x_actual

        # Evaluar la función
        try:
            with np.errstate(divide = "ignore", invalid = "ignore", over = "ignore"):
                y_valor = float(f(x_valor))
        except Exception:
            x_actual *= 2
            continue

        # Comprobar que sea finito
        if not np.isfinite(y_valor):
            x_actual *= 2
            continue

        # Límite finito

        if limite.is_finite is True:
            try:
                limite_num = float(sp.N(limite))
                error = abs(y_valor - limite_num)

                if error < tolerancia:
                    consecutivos += 1
                else:
                    consecutivos = 0

                if consecutivos >= puntos_convergencia:
                    ultimo_x = x_actual
                    break

            except Exception:
                pass

        # Límite infinito
        else:
            ultimo_x = x_actual
            break

        ultimo_x = x_actual

        # Aumentamos gradualmente
        x_actual *= 2

        # Límite máximo
        if x_actual >= maximo:
            x_actual = maximo
            ultimo_x = maximo
            break

    # INTERVALO DE VISUALIZACIÓN
    factor_visualizacion = 2.0
    extremo = ultimo_x * factor_visualizacion

    if direccion == 1:
        xmin = 1
        xmax = extremo
    else:
        xmin = -extremo
        xmax = -1

    return xmin, xmax, ultimo_x

def generar_puntos_tabla_infinito(f, limite, ultimo_x, direccion):
    limite_num = float(sp.N(limite))

    # Generamos muchos candidatos entre 2 y ultimo_x geomspace permite explorar varias escalas de x.
    candidatos = np.geomspace(2, ultimo_x, 100)

    datos = []

    for x_abs in candidatos:
        x_valor = (x_abs if direccion == 1 else -x_abs)

        try:
            with np.errstate(divide = "ignore", invalid = "ignore", over = "ignore"):
                y = float(f(x_valor))
        except Exception:
            continue

        if not np.isfinite(y):
            continue

        error = abs(y - limite_num)

        datos.append((x_abs, error))

    if len(datos) == 0:
        return []

    # Analizamos cómo disminuye el error
    puntos = []

    # Siempre mostramos el primer punto
    puntos.append(datos[0][0])

    ultimo_error = datos[0][1]

    for x_actual, error_actual in datos[1:]:
        if ultimo_error == 0:
            break

        # Qué fracción del error anterior queda
        proporcion = error_actual / ultimo_error

        # Si el error disminuyó bastante, mostramos este punto.
        if proporcion < 0.5:
            puntos.append(x_actual)
            ultimo_error = error_actual

    # Nos aseguramos de mostrar el último punto
    if puntos[-1] != ultimo_x:
        puntos.append(ultimo_x)

    return puntos

def generar_puntos_tabla_finito(f, limite, a, direccion, minimo = 1e-1, maximo = 1e-12):
    limite_num = float(sp.N(limite))

    # Distancias candidatas desde a
    candidatos = np.geomspace(minimo, maximo, 100)

    datos = []

    for distancia in candidatos:
        if direccion == "izquierda":
            x_valor = a - distancia
        else:
            x_valor = a + distancia

        try:
            with np.errstate(divide = "ignore", invalid = "ignore", over = "ignore"):
                y = float(f(x_valor))

        except Exception:
            continue

        if not np.isfinite(y):
            continue

        error = abs(y - limite_num)
        datos.append((distancia, error))

    if len(datos) == 0:
        return []

    puntos = []

    # Primer punto
    puntos.append(datos[0][0])

    ultimo_error = datos[0][1]

    for distancia, error_actual in datos[1:]:
        if ultimo_error == 0:
            break

        proporcion = error_actual / ultimo_error

        # Añadimos un punto cuando el error se reduce al menos a la mitad.
        if proporcion < 0.5:
            puntos.append(distancia)
            ultimo_error = error_actual

    return puntos

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

    # ELEGIR HACIA DÓNDE SE APROXIMA x
    tipo_a = st.selectbox("x se aproxima a", ["Número", "+∞", "-∞"], key = "tipo_punto_limite")

    # SI a ES UN NÚMERO
    if tipo_a == "Número":
        a_texto = st.text_input("Valor de a", value = "0")
        a_t = sp.sympify(a_texto)

        if not a_t.is_real:
            st.error("El punto a debe ser real.")
            st.stop()

        a = float(sp.N(a_t))
    elif tipo_a == "+∞":
        a = sp.oo
    else:
        a = -sp.oo

    # BOTÓN ANALIZAR
    if st.button("Analizar límite", type = "primary", key = "analizar_limite"):
        try:
            # CONVERTIR TEXTO A EXPRESIÓN DE SYMPY
            funcion = sp.sympify(funcion_texto)

            # VERIFICAR QUE SOLO APAREZCA x
            if funcion.free_symbols - {x}:
                st.error("La función solamente puede utilizar la variable x.")
                st.stop()

            # MOSTRAR FUNCIÓN
            st.latex(r"f(x) = " + sp.latex(funcion))

            # CASO 1: x → +∞ O x → -∞
            if a == sp.oo or a == -sp.oo:
                # CALCULAR LÍMITE
                with st.spinner("Calculando el límite..."):
                    limite = sp.limit(funcion, x, a)

                # MOSTRAR RESULTADO
                st.subheader("Límite en infinito")
                st.latex(r"\lim_{x\to " + sp.latex(a) + r"} f(x) = " + sp.latex(limite))

                # INTERPRETACIÓN

                if limite == sp.oo:
                    st.success("La función crece sin límite.")
                elif limite == -sp.oo:
                    st.success("La función decrece sin límite.")
                elif isinstance(limite, sp.AccumBounds):
                    st.warning("El límite no existe.")

                    st.info("La función presenta un comportamiento oscilatorio cuando x tiende a infinito.")
                    st.latex(r"\text{Valores de acumulación: }" + sp.latex(limite))

                elif limite.is_finite is True:
                    st.success("La función se aproxima a un valor finito.")
                else:
                    st.warning("No se pudo determinar simbólicamente el comportamiento del límite.")

                # FUNCIÓN NUMÉRICA
                f = sp.lambdify(x, funcion, modules = ["numpy"])

                # ELEGIR INTERVALO
                xmin, xmax, ultimo_x = encontrar_intervalo_infinito(f, limite, 1 if a == sp.oo else -1)
                valores_x = np.linspace(xmin, xmax, 3000)

                # TABLA DE APROXIMACIÓN
                st.subheader("Aproximación paso a paso")
                st.write("Observamos qué ocurre con f(x) cuando |x| crece cada vez más.")

                # Valores dependen de la velocidad de convergencia hacia el límite.
                valores_aproximacion = generar_puntos_tabla_infinito(f, limite, ultimo_x, 1 if a == sp.oo else -1)

                datos = []

                for valor in valores_aproximacion:
                    if a == sp.oo:
                        x_valor = valor
                    else:
                        x_valor = -valor

                    try:
                        with np.errstate(divide = "ignore", invalid = "ignore", over = "ignore"):
                            y_valor = float(f(x_valor))
                    except Exception:
                        y_valor = np.nan

                    datos.append({
                        "x": quitar_ceros(x_valor),
                        "f(x)": (quitar_ceros(y_valor) if np.isfinite(y_valor) else "No definido")
                    })

                st.dataframe(datos, use_container_width = True, hide_index = True)

                # GRÁFICA
                st.subheader("Gráfica")

                # EVALUAR FUNCIÓN

                with np.errstate(divide = "ignore", invalid = "ignore", over = "ignore"):
                    valores_y = np.asarray(f(valores_x), dtype = float)

                if valores_y.ndim == 0:
                    valores_y = np.full_like(valores_x, valores_y.item())

                valores_y = np.broadcast_to(valores_y, valores_x.shape).astype(float, copy = True)

                valores_y[~np.isfinite(valores_y)] = np.nan

                # ELIMINAR VALORES EXTREMADAMENTE GRANDES PARA QUE LA GRÁFICA SEA LEGIBLE

                valores_y[np.abs(valores_y) > 1e6] = np.nan

                # DETECTAR OSCILACIÓN

                es_oscilatoria = isinstance(limite, sp.AccumBounds)

                if not es_oscilatoria:
                    valores_finitos = valores_y[np.isfinite(valores_y)]

                    if valores_finitos.size >= 50:
                        ultimos = valores_finitos[-500:]
                        diferencias = np.diff(ultimos)
                        escala = max(np.max(np.abs(ultimos)), 1.0)
                        tolerancia = 1e-8 * escala
                        diferencias[np.abs(diferencias) < tolerancia] = 0
                        signos = np.sign(diferencias)
                        signos = signos[signos != 0]

                        if signos.size >= 5:
                            cambios = np.sum(signos[1:] != signos[:-1])

                            amplitud = (np.max(ultimos) - np.min(ultimos))

                            if (cambios >= 4 and amplitud > tolerancia):
                                es_oscilatoria = True

                if es_oscilatoria:
                    st.info("La función continúa oscilando cuando x tiende a infinito.")

                # CREAR GRÁFICA
                fig, ax = plt.subplots(figsize = (10, 5))
                ax.plot(valores_x, valores_y, label="f(x)")

                # LÍNEA DEL LÍMITE
                if limite not in (sp.oo, -sp.oo):
                    try:
                        limite_num = float(sp.N(limite))

                        ax.axhline(
                            limite_num,
                            color = "green",
                            linestyle = ":",
                            linewidth = 1,
                            label = (f"Límite = " f"{quitar_ceros(limite_num)}")
                        )
                    except Exception:
                        pass

                # EJE X
                ax.axhline(0, color = "black", linewidth = 0.7)

                # CONFIGURACIÓN
                ax.set_xlim(xmin, xmax)
                ax.set_xlabel("x")
                ax.set_ylabel("f(x)")
                ax.set_title("Comportamiento de f(x) " f"cuando x → {sp.latex(a)}")
                ax.grid(True, alpha = 0.3)
                ax.legend()

                st.pyplot(fig)
                plt.close(fig)

            # CASO 2: x → a, CON a FINITO
            else:
                # CALCULAR LÍMITES LATERALES
                with st.spinner("Analizando el comportamiento de la función..."):
                    limite_izquierdo = sp.limit(funcion, x, a, dir = "-")
                    limite_derecho = sp.limit(funcion, x, a, dir = "+")
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
                es_infinito_izq = (limite_izquierdo in (sp.oo, -sp.oo))
                es_infinito_der = (limite_derecho in (sp.oo, -sp.oo))

                # CASO 1: ASÍNTOTA VERTICAL
                if (es_infinito_izq or es_infinito_der):
                    st.error(f"Se detectó una asíntota " f"vertical en x = {a}")
                    tipo_grafica = "asintota"

                # CASO 2: LÍMITES LATERALES IGUALES
                elif sp.simplify(limite_izquierdo - limite_derecho) == 0:
                    limite_finito = limite
                    try:
                        valor_a = funcion.subs(x, a)
                    except Exception:
                        valor_a = sp.nan

                    # COMPROBAR DISCONTINUIDAD REMOVIBLE
                    es_indefinido = (valor_a.has(sp.zoo) or valor_a.has(sp.oo) or valor_a.has(-sp.oo) or valor_a.has(sp.nan))

                    coincide = False

                    if not es_indefinido:
                        try:
                            coincide = (sp.simplify(valor_a - limite_finito) == 0)
                        except Exception:
                            coincide = False

                    if not coincide:
                        st.warning("Se detectó una discontinuidad removible.")
                        st.write("El límite existe y es finito, pero la función no coincide con el límite en x = a.")

                        st.latex(r"\lim_{x\to " + sp.latex(a) + r"} f(x) = " + sp.latex(limite_finito))

                        tipo_grafica = "removible"

                    # FUNCIÓN CONTINUA
                    else:
                        st.success("La función es continua en el punto analizado.")
                        st.latex(r"\lim_{x\to " + sp.latex(a) + r"} f(x) = " + sp.latex(limite_finito))
                        tipo_grafica = "continua"

                # CASO 3: LÍMITES LATERALES DIFERENTES
                else:
                    st.warning("Los límites laterales son diferentes. Por lo tanto, el límite bilateral no existe.")
                    st.latex(r"\lim_{x\to " + sp.latex(a) + r"} f(x)" r"\quad\text{no existe}")
                    tipo_grafica = "diferentes"

                # FUNCIÓN NUMÉRICA
                f = sp.lambdify(x, funcion, modules = ["numpy"])

                # ELEGIR AUTOMÁTICAMENTE EL INTERVALO
                escala = max(1.0, abs(float(a)))
                radio = 0.5 * escala
                xmin = (float(a) - radio)
                xmax = (float(a) + radio)
                izquierda = np.linspace(xmin, float(a) - radio * 1e-5, 2500)
                derecha = np.linspace(float(a) + radio * 1e-5, xmax, 2500)

                # EVALUAR FUNCIÓN
                def evaluar(valores_x):

                    with np.errstate(divide = "ignore", invalid = "ignore", over = "ignore"):
                        valores_y = np.asarray(f(valores_x), dtype = float)

                    if valores_y.ndim == 0:
                        valores_y = np.full_like(valores_x, valores_y.item())

                    valores_y = np.broadcast_to(valores_y, valores_x.shape).astype(float, copy = True)
                    valores_y[~np.isfinite(valores_y)] = np.nan

                    return valores_y

                y_izquierda = evaluar(izquierda)
                y_derecha = evaluar(derecha)

                # OBTENER VALORES PARA LA ESCALA
                valores = np.concatenate([
                    np.abs(y_izquierda[np.isfinite(y_izquierda)]),
                    np.abs(y_derecha[np.isfinite(y_derecha)])
                ])

                if valores.size == 0:
                    st.error("No se encontraron valores que puedan representarse.")
                    st.stop()

                # ESCALA PARA ASÍNTOTA
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
                        amplitud_vertical = (np.percentile(distancia, 95))
                    else:
                        amplitud_vertical = 1.0

                    amplitud_vertical = max(amplitud_vertical, 0.5)
                    ymin = (limite_num - amplitud_vertical)
                    ymax = (limite_num + amplitud_vertical)

                # CREAR GRÁFICA
                fig, ax = plt.subplots(figsize=(10, 5))

                if tipo_grafica == "asintota":
                    ax.plot(izquierda, y_izquierda, label = "x < a")
                    ax.plot(derecha, y_derecha, label = "x > a")
                    ax.set_ylim(-amplitud, amplitud)

                else:
                    ax.plot(izquierda, y_izquierda, color = "blue")
                    ax.plot(derecha, y_derecha, color = "blue")
                    ax.set_ylim(ymin, ymax)

                # LÍNEA x = a
                ax.axvline(float(a), color="red", linestyle="--", linewidth=1, label=f"x = {a:g}")

                # LÍNEA HORIZONTAL DEL LÍMITE
                if (tipo_grafica == "continua" or tipo_grafica == "removible"):
                    try:
                        limite_num = float(sp.N(limite))
                        ax.axhline(limite_num, color="green", linestyle=":", linewidth=1,
                            label = ("Límite = " f"{limite_num:g}")
                        )
                    except Exception:
                        pass

                # EJE X
                ax.axhline(0, color="black", linewidth = 0.7)

                # CONFIGURACIÓN
                ax.set_xlim(xmin, xmax)
                ax.set_xlabel("x")
                ax.set_ylabel("f(x)")
                ax.set_title("Comportamiento de f(x) " f"cuando x → {a:g}")
                ax.grid(True, alpha=0.3)
                ax.legend()
                st.pyplot(fig)
                plt.close(fig)

                # APROXIMACIÓN PASO A PASO
                st.subheader("Aproximación paso a paso")
                st.write("Observamos qué ocurre con f(x) cuando x se acerca cada vez más a a.")

                puntos_izquierda = generar_puntos_tabla_finito(f, limite_izquierdo, float(a), "izquierda")
                puntos_derecha = generar_puntos_tabla_finito(f, limite_derecho, float(a), "derecha")

                valores_izquierda = [float(a) - d for d in puntos_izquierda]
                valores_derecha = [float(a) + d for d in puntos_derecha]

                datos_izquierda = []
                datos_derecha = []

                for x_izq in valores_izquierda:
                    try:
                        y_izq = float(f(x_izq))
                    except Exception:
                        y_izq = np.nan

                    datos_izquierda.append({
                        "x": quitar_ceros(x_izq),
                        "f(x)": (quitar_ceros(y_izq) if np.isfinite(y_izq) else "No definido")
                    })

                for x_der in valores_derecha:
                    try:
                        y_der = float(f(x_der))
                    except Exception:
                        y_der = np.nan

                    datos_derecha.append({
                        "x": quitar_ceros(x_der),
                        "f(x)": (quitar_ceros(y_der) if np.isfinite(y_der) else "No definido")
                    })

                col1, col2 = st.columns(2)

                with col1:
                    st.write("**Aproximación por la izquierda**")

                    st.dataframe(
                        datos_izquierda,
                        use_container_width = True,
                        hide_index = True
                    )

                with col2:
                    st.write("**Aproximación por la derecha**")

                    st.dataframe(
                        datos_derecha,
                        use_container_width = True,
                        hide_index = True
                    )

        except Exception as error:
            st.error("No se pudo analizar la función. Revisa que esté escrita correctamente.")

# DERIVADA

elif seccion == "Derivada":
    st.header("Derivada")
    st.write("Calcula si la derivada de una función existe en un punto, determina su valor y muestra la recta tangente.")

    # ENTRADAS
    funcion_texto = st.text_input("Función f(x)", value = "x**2")
    a_texto = st.text_input("Punto x = a", value = "1")

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
                                error_izquierda = abs(cociente_izquierda - derivada_num)

                                datos_izquierda.append({
                                    "h": h_izquierda,
                                    "x": x_izquierda,
                                    "cociente": cociente_izquierda,
                                    "error": error_izquierda
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
                                error_derecha = abs(cociente_derecha - derivada_num)

                                datos_derecha.append({
                                    "h": h_derecha,
                                    "x": x_derecha,
                                    "cociente": cociente_derecha,
                                    "error": error_derecha
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
                    st.markdown("### Aproximación por la izquierda")

                    tabla_izquierda = []

                    for punto in puntos_izquierda:
                        tabla_izquierda.append({
                            "h": punto["h"],
                            "x = a + h": punto["x"],
                            "Cociente incremental": punto["cociente"],
                            "Error": punto["error"]
                        })

                    st.dataframe(tabla_izquierda, use_container_width = True, hide_index = True)

                # TABLA DERECHA
                if puntos_derecha:
                    st.markdown("### Aproximación por la derecha")

                    tabla_derecha = []

                    for punto in puntos_derecha:
                        tabla_derecha.append({
                            "h": punto["h"],
                            "x = a + h": punto["x"],
                            "Cociente incremental": punto["cociente"],
                            "Error": punto["error"]
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

elif seccion == "Integral":
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
                (_, b_graf, _) = encontrar_intervalo_infinito(funcion_numerica, b_limite, 1)
            elif b_num is not None:
                # (-∞, b]
                b_graf = b_num
                (a_graf, _, _) = encontrar_intervalo_infinito(funcion_numerica, a_limite, -1)
            else:
                # (-∞, +∞)
                (a_graf, _, _) = encontrar_intervalo_infinito(funcion_numerica, a_limite, -1)
                (_, b_graf, _) = encontrar_intervalo_infinito(funcion_numerica, b_limite, 1)

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

            # MOSTRAR RESULTADO

            st.subheader("Resultado de la integral")

            st.latex(r"\int_{" + sp.latex(a) + r"}^{" + sp.latex(b) + r"} " + sp.latex(funcion) + r"\,dx = " + sp.latex(integral))

            if isinstance(integral, sp.Integral):
                st.warning("SymPy dejó una integral sin evaluar. Todavía no se puede concluir su convergencia.")
            elif integral in (sp.oo, -sp.oo, sp.zoo, sp.nan):
                st.error("La integral no tiene un valor finito según el resultado simbólico.")
            elif integral.is_finite is True:
                st.success("Se obtuvo un resultado finito. Si existen singularidades interiores, todavía debe verificarse la convergencia de cada tramo.")
            else:
                st.warning("No se pudo confirmar automáticamente la convergencia.")

            # GRAFICAR EL INTEGRANDO

            st.subheader("Gráfica de la función y área")

            numero_puntos = 4000

            valores_x = np.linspace(a_graf, b_graf, numero_puntos)

            with np.errstate(divide = "ignore", invalid = "ignore", over = "ignore"):
                valores_y = np.asarray(funcion_numerica(valores_x), dtype=float)

            if valores_y.ndim == 0:
                valores_y = np.full_like(valores_x, valores_y.item())

            valores_y = np.broadcast_to(valores_y, valores_x.shape).astype(float, copy=True)

            valores_y[~np.isfinite(valores_y)] = np.nan

            # Separar la gráfica en las singularidades detectadas.
            singularidades_grafica = sorted(s for s in singularidades if a_graf < s < b_graf)

            paso = (b_graf - a_graf) / (numero_puntos - 1)
            margen = 3 * paso

            for s in singularidades_grafica:
                valores_y[np.abs(valores_x - s) < margen] = np.nan

            valores_finitos = valores_y[np.isfinite(valores_y)]

            if len(valores_finitos) == 0:
                st.warning("No hay valores finitos suficientes para representar la función.")
            else:

                if singularidades:
                    # Aplicar percentiles únicamente si se detectaron singularidades
                    if len(valores_finitos) > 0:
                        minimo_y, maximo_y = np.percentile(valores_finitos, [2, 98])

                        # Evitar un intervalo vertical de amplitud cero
                        if minimo_y == maximo_y:
                            margen = max(1.0, abs(minimo_y) * 0.1)
                            minimo_y -= margen
                            maximo_y += margen
                else:
                    minimo_y, maximo_y = min(valores_finitos), max(valores_finitos)
                    minimo_y -= 10 ** int(np.log10(abs(minimo_y) + 1))
                    maximo_y += 10 ** int(np.log10(abs(maximo_y) + 1))

                fig, ax = plt.subplots(figsize = (11, 6))
                ax.set_ylim(minimo_y, maximo_y)

                ax.plot(valores_x, valores_y, label = r"$f(x)$", linewidth=1.8)

                ax.axhline(0, color = "black", linewidth = 0.8)

                # Sombrear por tramos, sin cruzar singularidades.
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
                        ax.fill_between(valores_x[mascara], valores_y[mascara], 0, alpha = 0.2)

                # Marcar las singularidades detectadas.
                for i, s in enumerate(singularidades_grafica):
                    ax.axvline(s, color="red", linestyle="--", linewidth=1.3, label = ("Posible singularidad" if i == 0 else None))

                # Indicar visualmente los extremos infinitos.
                if a == -sp.oo:
                    ax.annotate("−∞", xy=(0.01, 0.03), xycoords="axes fraction")

                if b == sp.oo:
                    ax.annotate("+∞", xy=(0.99, 0.03), xycoords="axes fraction", ha="right")

                ax.set_xlim(a_graf, b_graf)
                ax.set_ylim(minimo_y, maximo_y)

                ax.set_xlabel("x")
                ax.set_ylabel("f(x)")
                ax.set_title("Función y área en la ventana de visualización")
                ax.grid(True, alpha=0.3)
                ax.legend()

                st.pyplot(fig)
                plt.close(fig)

                if a == -sp.oo or b == sp.oo:
                    st.caption(f"La gráfica muestra solamente " f"[{a_graf:.6g}, {b_graf:.6g}]. La ventana es finita aunque la integral tenga una o ambas cotas infinitas.")

        except Exception as error:
            st.error("No se pudo analizar la función. Revisa que esté escrita correctamente.")
            print(f"Error: {error}")

elif seccion == "Suma infinita":
    st.header("Sumas infinitas")
    st.write("Aquí podrás hallar y aproximar el valor de series.")