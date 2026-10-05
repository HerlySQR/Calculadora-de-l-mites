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


# FUNCIÓN PARA MOSTRAR NÚMEROS, ELIMINANDO CEROS INNECESARIOS
def quitar_ceros(valor):
    if not np.isfinite(valor):
        return str(valor)
    return f"{valor:.12f}".rstrip("0").rstrip(".")

# APÉNDICE

if seccion == "Apéndice":
    st.header("Apéndice")
    st.write("Aquí encontrarás definiciones y resultados auxiliares.")

# LÍMITES

elif seccion == "Límite":
    st.header("Límites")
    st.write("Introduce una función y el valor al que se aproxima x.")

    # INGRESAR FUNCIÓN

    funcion_texto = st.text_input(
        "Función f(x)",
        value="sin(x)/x",
        key="funcion_limite"
    )

    # ELEGIR HACIA DÓNDE SE APROXIMA x

    tipo_a = st.selectbox("x se aproxima a", ["Número", "+∞", "-∞"], key = "tipo_punto_limite")

    # SI a ES UN NÚMERO

    if tipo_a == "Número":
        a = st.number_input("Valor de a", value = 0.0, step = 0.1, format = "%.6f", key = "punto_limite")
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
                st.error(
                    "La función solamente puede utilizar "
                    "la variable x."
                )

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

                    st.info(
                        "La función presenta un comportamiento oscilatorio "
                        "cuando x tiende a infinito."
                    )
                    st.latex(r"\text{Valores de acumulación: }" + sp.latex(limite))

                elif limite.is_finite is True:
                    st.success("La función se aproxima a un valor finito.")

                else:
                    st.warning(
                        "No se pudo determinar simbólicamente el "
                        "comportamiento del límite."
                    )

                # FUNCIÓN NUMÉRICA

                f = sp.lambdify(x, funcion, modules = ["numpy"])

                # TABLA DE APROXIMACIÓN

                st.subheader("Aproximación paso a paso")

                st.write(
                    "Observamos qué ocurre con f(x) "
                    "cuando |x| crece cada vez más."
                )


                # Valores: 10, 100, 1000, 10000, ...

                valores_aproximacion = [10.0 ** n for n in range(1, 7)]

                datos = []

                for valor in valores_aproximacion:
                    if a == sp.oo:
                        x_valor = valor
                    else:
                        x_valor = -valor

                    try:
                        with np.errstate(
                            divide="ignore",
                            invalid="ignore",
                            over="ignore"
                        ):
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

                # ELEGIR INTERVALO

                if a == sp.oo:
                    xmin = 1
                    xmax = 1000
                else:
                    xmin = -1000
                    xmax = -1

                valores_x = np.linspace(xmin, xmax, 3000)

                # EVALUAR FUNCIÓN

                with np.errstate(
                    divide = "ignore",
                    invalid = "ignore",
                    over = "ignore"
                ):
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
                    st.info(
                        "La función continúa oscilando "
                        "cuando x tiende a infinito."
                    )

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

                with st.spinner(
                    "Analizando el comportamiento "
                    "de la función..."
                ):

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

                    es_indefinido = (
                        valor_a.has(sp.zoo)
                        or
                        valor_a.has(sp.oo)
                        or
                        valor_a.has(-sp.oo)
                        or
                        valor_a.has(sp.nan)
                    )

                    coincide = False

                    if not es_indefinido:
                        try:
                            coincide = (sp.simplify(valor_a - limite_finito) == 0)
                        except Exception:
                            coincide = False

                    if not coincide:
                        st.warning(
                            "Se detectó una "
                            "discontinuidad removible."
                        )

                        st.write(
                            "El límite existe y es finito, "
                            "pero la función no coincide "
                            "con el límite en x = a."
                        )

                        st.latex(r"\lim_{x\to " + sp.latex(a) + r"} f(x) = " + sp.latex(limite_finito))

                        tipo_grafica = "removible"

                    # FUNCIÓN CONTINUA

                    else:
                        st.success(
                            "La función es continua "
                            "en el punto analizado."
                        )

                        st.latex(r"\lim_{x\to " + sp.latex(a) + r"} f(x) = " + sp.latex(limite_finito))

                        tipo_grafica = "continua"

                # CASO 3: LÍMITES LATERALES DIFERENTES

                else:
                    st.warning(
                        "Los límites laterales son "
                        "diferentes. Por lo tanto, "
                        "el límite bilateral no existe."
                    )

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

                    with np.errstate(
                        divide = "ignore",
                        invalid = "ignore",
                        over = "ignore"
                    ):

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
                    st.error(
                        "No se encontraron valores "
                        "que puedan representarse."
                    )
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

                st.write(
                    "Observamos qué ocurre con f(x) "
                    "cuando x se acerca cada vez más a a."
                )

                distancias = [10.0 ** (-n) for n in range(1, 13)]

                datos_izquierda = []
                datos_derecha = []

                for distancia in distancias:
                    x_izq = (float(a) - distancia)
                    x_der = (float(a) + distancia)

                    try:
                        y_izq = float(f(x_izq))
                    except Exception:
                        y_izq = np.nan

                    try:
                        y_der = float(f(x_der))
                    except Exception:
                        y_der = np.nan

                    datos_izquierda.append({
                        "Distancia": quitar_ceros(distancia),
                        "x": quitar_ceros(x_izq),
                        "f(x)": (quitar_ceros(y_izq) if np.isfinite(y_izq) else "No definido")
                    })

                    datos_derecha.append({
                        "Distancia": quitar_ceros(distancia),
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
            st.error(
                "No se pudo analizar la función. "
                "Revisa que esté escrita correctamente."
            )

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