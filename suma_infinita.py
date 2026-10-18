import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import sympy as sp
import scipy.special

import pandas as pd

def ejecutar_sumas_infinitas():
    st.header("Sumas infinitas")
    st.write("Estudia el comportamiento de una serie mediante sus sumas parciales y observa si parecen converger.")

    # ENTRADAS
    termino_texto = st.text_input("Término general a_n", value = "1/n**2", key = "termino_serie")

    col1, col2 = st.columns(2)

    with col1:
        indice_inicial = st.number_input("Primer índice n₀", value = 1, step = 1, key = "indice_inicial_serie")

    with col2:
        N_max = st.number_input("Último índice N", min_value = 2, value = 100, step = 1, key = "N_max_serie")

    if st.button("Analizar serie", type = "primary", key = "analizar_serie"):
        try:
            # VARIABLE SIMBÓLICA
            n = sp.Symbol("n", integer=True)

            # INTERPRETAR EL TÉRMINO GENERAL
            termino = sp.sympify(
                termino_texto,
                locals = {"n": n, "pi": sp.pi, "e": sp.E}
            )

            n0 = int(indice_inicial)
            N = int(N_max)

            if N < n0:
                st.error("El último índice N debe ser mayor o igual que el primer índice n₀.")
                st.stop()

            # COMPROBAR EL DOMINIO EN TODOS LOS ÍNDICES
            indices = np.arange(n0, N + 1)

            funcion_numerica = sp.lambdify(n, termino, modules = [
                {"factorial": lambda x: scipy.special.factorial(x, exact = False)},
                "numpy"
            ])

            try:
                with np.errstate(divide = "ignore", invalid = "ignore", over = "ignore"):
                    terminos = np.asarray(funcion_numerica(indices))

                    terminos = np.broadcast_to(terminos, indices.shape).astype(float)

                # Identificar índices con valores no finitos
                indices_invalidos = indices[~np.isfinite(terminos)]

                if len(indices_invalidos) > 0:
                    lista_indices = ", ".join(str(int(i)) for i in indices_invalidos[:10])

                    mensaje = (
                        "El término general no está definido "
                        "o produce un valor no finito en "
                        f"los siguientes índices: {lista_indices}."
                    )

                    if len(indices_invalidos) > 10:
                        mensaje += (f" Y otros {len(indices_invalidos) - 10} índices.")

                    st.error(mensaje)
                    st.stop()

            except Exception as error:
                st.error("No se pudo evaluar el término general en todos los índices seleccionados.")
                print(f"Error: {error}")
                st.stop()

            # Solo continuar si todos los términos son finitos
            # A partir de aquí puedes calcular la suma simbólica
            # y las sumas parciales.


            # 1. INTENTAR CALCULAR LA SUMA INFINITA
            resultado = None
            error_simbolico = None

            try:
                resultado = sp.summation(termino, (n, n0, sp.oo))
            except Exception as error:
                error_simbolico = str(error)

            # 2. CALCULAR LOS TÉRMINOS NUMÉRICOS

            with np.errstate(divide = "ignore", invalid = "ignore", over = "ignore"):
                terminos = np.asarray(funcion_numerica(indices))
                terminos = np.broadcast_to(terminos, indices.shape).astype(float)

            # SUMAS PARCIALES
            sumas_parciales = []
            suma_actual = 0.0

            for termino_actual in terminos:
                if not np.isfinite(termino_actual):
                    suma_actual = np.nan
                elif np.isfinite(suma_actual):
                    suma_actual += termino_actual

                sumas_parciales.append(suma_actual)

            sumas_parciales = np.asarray(sumas_parciales)

            # GUARDAR RESULTADOS
            st.session_state["datos_serie"] = {
                "termino_texto": termino_texto,
                "termino": termino,
                "n0": n0,
                "N": N,
                "indices": indices,
                "terminos": terminos,
                "sumas": sumas_parciales,
                "resultado": resultado,
                "error_simbolico": error_simbolico
            }

        except Exception as error:
            st.error(
                "No se pudo interpretar el término general. "
                "Revisa la expresión introducida."
            )
            print(f"Error: {error}")

    # MOSTRAR RESULTADOS FUERA DEL BOTÓN
    datos = st.session_state.get("datos_serie")

    if datos is not None:

        # COMPROBAR SI LAS ENTRADAS SIGUEN SIENDO LAS MISMAS
        if (
            datos["termino_texto"] != termino_texto
            or datos["n0"] != int(indice_inicial)
            or datos["N"] != int(N_max)
        ):
            st.info(
                "Pulsa «Analizar serie» para actualizar "
                "los resultados."
            )
            st.stop()

        termino = datos["termino"]
        indices = datos["indices"]
        terminos = datos["terminos"]
        sumas_parciales = datos["sumas"]
        resultado = datos["resultado"]

        # MOSTRAR LA SERIE
        st.subheader("Serie estudiada")

        st.latex(
            r"\sum_{n=" + str(datos["n0"]) +
            r"}^{\infty} \left(" +
            sp.latex(termino) + r"\right)"
        )

        # RESULTADO SIMBÓLICO
        st.subheader("Resultado de la suma infinita")

        if resultado is None:
            st.warning("SymPy no pudo calcular la suma simbólicamente. Esto no significa que la serie diverja.")

        elif resultado.has(sp.Sum):
            st.warning("SymPy dejó una suma sin evaluar. No se ha obtenido un resultado explícito.")

        elif resultado in (sp.nan, sp.zoo, sp.oo, -sp.oo):
            st.warning("El resultado simbólico no es un número real finito. Hay que estudiar la divergencia de la serie.")

        elif resultado.is_finite is True:
            st.success("Se obtuvo un resultado finito.")

            st.latex(
                r"\sum_{n=" + str(datos["n0"]) +
                r" }^{\infty} a_n = " +
                sp.latex(resultado)
            )

            resultado_decimal = sp.N(resultado, 15)

            st.write("**Aproximación decimal:**", str(resultado_decimal))

        else:
            st.info("El resultado simbólico no permite confirmar por sí solo la convergencia de la serie.")

            st.latex(
                r"\text{Resultado de SymPy: }" +
                sp.latex(resultado)
            )

        # TABLA DE SUMAS PARCIALES
        st.subheader("Tabla de sumas parciales")

        tabla = pd.DataFrame({
            "N": indices,
            "Término a_N": terminos,
            "Suma parcial S_N": sumas_parciales
        })

        st.dataframe(
            tabla,
            hide_index=True,
            use_container_width=True
        )

        # GRÁFICAS
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Término general")

            fig1, ax1 = plt.subplots(figsize=(6, 4))

            ax1.plot(
                indices,
                terminos,
                marker = "o",
                markersize = 3
            )

            ax1.axhline(0, color = "black", linewidth = 0.8)
            ax1.set_xlabel("n")
            ax1.set_ylabel("aₙ")
            ax1.set_title("Términos de la serie")
            ax1.grid(True, alpha=0.3)

            st.pyplot(fig1)
            plt.close(fig1)

        with col2:
            st.subheader("Sumas parciales")

            fig2, ax2 = plt.subplots(figsize=(6, 4))

            ax2.plot(
                indices,
                sumas_parciales,
                marker = "o",
                markersize = 3
            )

            ax2.set_xlabel("N")
            ax2.set_ylabel("S_N")
            ax2.set_title("Comportamiento de las sumas parciales")
            ax2.grid(True, alpha=0.3)

            st.pyplot(fig2)
            plt.close(fig2)

        # OBSERVACIÓN NUMÉRICA
        valores_finitos = sumas_parciales[
            np.isfinite(sumas_parciales)
        ]

        if len(valores_finitos) >= 5:
            st.subheader("Observación numérica")

            diferencias = np.abs(np.diff(valores_finitos))

            if (len(diferencias) >= 4 and np.all(diferencias[-4:] < 1e-4)):
                st.write(
                    "Las últimas sumas parciales varían poco. "
                    "Esto sugiere estabilización numérica, pero "
                    "no demuestra la convergencia de la serie."
                )
            else:
                st.write(
                    "Las sumas parciales todavía presentan "
                    "variaciones apreciables o no muestran una "
                    "estabilización clara."
                )