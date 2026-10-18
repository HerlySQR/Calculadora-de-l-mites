import numpy as np
import sympy as sp

def quitar_ceros(valor):
    if not np.isfinite(valor):
        return str(valor)
    return f"{valor:.12f}".rstrip("0").rstrip(".")

def encontrar_intervalo_infinito(f, limite, direccion, tolerancia = 0.1, minimo = 2, maximo = 1e8):
    x_actual = float(minimo)

    # Número de puntos consecutivos que deben estar suficientemente cerca del límite
    puntos_convergencia = 2

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
