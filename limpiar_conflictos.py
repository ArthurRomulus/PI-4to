#!/usr/bin/env python
"""Script para limpiar conflictos de merge en consultas.py."""

import re

# Leer el archivo con conflictos
with open('database/consultas.py', 'r', encoding='utf-8') as f:
    contenido = f.read()

# Patrón para encontrar conflictos (multilínea)
patron = r'<<<<<<< HEAD\n(.*?)\n=======\n(.*?)\n>>>>>>> [^\n]+\n'

# Función de reemplazo - mantener HEAD (versión con login integrado)
def limpiar_conflicto(match):
    return match.group(1) + '\n'

# Limpiar todos los conflictos
contenido_limpio = re.sub(patron, limpiar_conflicto, contenido, flags=re.DOTALL)

# Escribir el archivo limpio
with open('database/consultas.py', 'w', encoding='utf-8') as f:
    f.write(contenido_limpio)

print("✓ Conflictos resueltos exitosamente")
print("La versión HEAD (con login integrado) fue conservada")
