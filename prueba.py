import sympy as sp

x = sp.symbols("x")

f = 1/(x - 2)

izquierda = sp.limit(f, x, 2, dir="-")
derecha = sp.limit(f, x, 2, dir="+")

print(izquierda)
print(derecha)