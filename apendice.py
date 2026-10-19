
import streamlit as st

def ejecutar_apendice():
    st.header("Apéndice")

    st.write(
        "En esta sección encontrarás definiciones, "
        "propiedades, teoremas y ejemplos de los temas "
        "estudiados en la calculadora."
    )

    # PESTAÑAS PRINCIPALES: ÍNDICE DE TEMAS
    pestanas = st.tabs([
        "Índice",
        "Límites",
        "Derivadas",
        "Integrales",
        "Series"
    ])

    # PESTAÑA ÍNDICE
    with pestanas[0]:
        st.subheader("Índice de contenidos")

        st.markdown("""
        ### 1. Límites
        - Definición
        - Límites laterales
        - Límites infinitos
        - Límites al infinito
        - Propiedades de los límites
        - Límites notables
        - Indeterminaciones

        ### 2. Derivadas
        - Definición de derivada
        - Interpretación geométrica
        - Reglas de derivación
        - Derivadas laterales
        - Relación entre continuidad y derivabilidad

        ### 3. Integrales
        - Sumas de Riemann
        - Integral definida
        - Teorema fundamental del cálculo
        - Integrales impropias

        ### 4. Series
        - Sucesiones y sumas parciales
        - Series convergentes y divergentes
        - Series geométricas
        - Criterios de convergencia
        """)

    # PESTAÑA LÍMITES
    with pestanas[1]:
        st.subheader("Límites")

        with st.expander("1. Definición intuitiva del límite"):
            st.write(
                "El límite describe el valor al que se aproxima una función cuando su variable se acerca "
                "a un punto determinado."
            )

            st.latex(r"\lim_{x\to a} f(x)=L")

            st.write(
                r"La definición formal de que el límite de $f(x)$ es $L$ cuando $x$ tiende a $a$ "
                r"si para cada epsilon positivo existe un delta positivo tal que:"
            )

            st.latex(
                r"\forall \varepsilon>0,\ \exists \delta>0:"
                r"\quad 0<|x-a|<\delta"
                r"\Rightarrow |f(x)-L|<\varepsilon"
            )

            st.write(
                r"Esto quiere decir, que si $x$ está suficientemente cerca a $a$, entonces $f(x)$ "
                r"estará cerca o será igual a $L$. Por ejemplo:"
            )

            st.latex(r"\lim_{x\to 2} x^2=4")

            st.write(
                r"O sea, hay que demostrar que:"
            )

            st.latex(
                r"\forall \varepsilon>0,\ \exists \delta>0:"
                r"\quad 0<|x-2|<\delta"
                r"\Rightarrow |x^2-4|<\varepsilon"
            )

            st.write(
                r"Para esto, vamos a imponer que:"
            )

            st.latex(
                r"|x-2|<1"
            )

            st.write(
                r"Por desigualdad triangular:"
            )

            st.latex(
                r"|x+2|=|x-2+4|\leq|x-2|+4<1+4=5"
            )

            st.write(
                r"Tenemos que:"
            )

            st.latex(
                r"|x^2-4|=|x+2||x-2|<5|x-2|"
            )

            st.write(
                r"O sea, necesitamos que $5|x-2|<\varepsilon$, entonces $|x-2|<\frac{\varepsilon}{5}$, "
                r"por lo que nuestro $\delta$ lo podemos definir como:"
            )

            st.latex(
                r"\delta=\min\{1,\varepsilon/5\}>0"
            )

            st.write(
                r"Por lo que si $|x-2|<\delta$, entonces $|x-2|<1$ y por la desigualdad triangular "
                r"anterior $|x+2|<5$, multiplicando ambos:"
            )

            st.latex(
                r"|x^2-4|=|x+2||x-2|<5|x-2|<5\frac{\varepsilon}{5}=\varepsilon"
            )

            st.write(
                r"Y como $\varepsilon$ era arbitrario: "
            )

            st.latex(
                r"\forall \varepsilon>0,\ \exists \delta>0:"
                r"\quad 0<|x-2|<\delta"
                r"\Rightarrow |x^2-4|<\varepsilon"
            )

            st.write(
                r"Por lo que queda demostrado el límite."
            )

        with st.expander("2. Límites laterales"):
            st.write(
                "El límite por la izquierda estudia valores "
                "con x menor que a; el límite por la derecha "
                "estudia valores con x mayor que a."
            )

            st.latex(
                r"\lim_{x\to a^-}f(x),\qquad "
                r"\lim_{x\to a^+}f(x)"
            )

        with st.expander("4. Límites al infinito"):
            st.write(
                "Estudian el comportamiento de una función "
                "cuando x crece o decrece sin límite."
            )

            st.latex(
                r"\lim_{x\to+\infty}f(x),\qquad "
                r"\lim_{x\to-\infty}f(x)"
            )

    # PESTAÑA DERIVADAS
    with pestanas[2]:
        st.subheader("Derivadas")

    # PESTAÑA INTEGRALES
    with pestanas[3]:
        st.subheader("Integrales")

    # PESTAÑA SERIES
    with pestanas[4]:
        st.subheader("Series")
