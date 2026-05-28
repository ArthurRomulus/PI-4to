# ⚡ Quick Reference - Teclado Virtual

## 🎯 En 30 segundos

El teclado virtual aparece automáticamente en cualquier `QLineEdit`. **No necesitas hacer nada especial.**

```python
# ✅ Esto ya funciona con el teclado
input_field = QLineEdit()
window.addWidget(input_field)
```

---

## 🚀 Casos de Uso Rápidos

### Caso 1: Campo simple
```python
self.input = QLineEdit()
self.input.setPlaceholderText("Escribe aquí...")
layout.addWidget(self.input)
# ✅ El teclado aparecerá al hacer focus
```

### Caso 2: Componente personalizado
```python
from ui.keyboard_helper import enable_keyboard_for_widget

class MiFormulario(QFrame):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        
        self.nombre = QLineEdit()
        self.email = QLineEdit()
        self.telefono = QLineEdit()
        
        layout.addWidget(self.nombre)
        layout.addWidget(self.email)
        layout.addWidget(self.telefono)
        
        # ✅ Habilita teclado para todos
        enable_keyboard_for_widget(self)
```

### Caso 3: Control manual
```python
from ui.keyboard_helper import KeyboardManager

kb = KeyboardManager()

# Mostrar
kb.show_keyboard_for(input_field)

# Ocultar
kb.hide_keyboard()

# Obtener instancia
keyboard = kb.get_keyboard()
```

---

## 📍 Ubicación de Archivos

```
Archivo                          Qué es                    Dónde
─────────────────────────────────────────────────────────────────
ui/keyboard_manager.py           Teclado (actualizado)     ✏️
ui/keyboard_helper.py            Helpers (nuevo)           ✨
main.py                          Inicialización (actualizado) ✏️
example_virtual_keyboard.py      Demo (nuevo)              ✨
README/TECLADO_VIRTUAL.md        Documentación             📖
```

---

## 🎨 Colores del Teclado

| Elemento | Color | Código |
|----------|-------|--------|
| Fondo | Gris Oscuro | `#0f172a` |
| Teclas | Gris | `#1e293b` |
| Shift | Azul | `#38bdf8` |
| Espacio | Gris Oscuro | `#334155` |
| Borrar | Rojo | `#ef4444` |
| Aceptar | Verde | `#10b981` |

---

## 🔧 Configuración Rápida

### Cambiar altura del teclado
**Archivo:** `ui/keyboard_manager.py` línea 24
```python
self.setFixedHeight(300)  # Valores típicos: 250, 300, 350
```

### Cambiar tamaño de fuente
**Archivo:** `ui/keyboard_manager.py` línea 155
```python
font.setPointSize(13)  # Valores típicos: 11, 12, 13, 14, 15
```

### Cambiar color de fondo
**Archivo:** `ui/keyboard_manager.py` línea 41
```python
background: rgba(15, 23, 42, 0.98);  # Cambiar RGB
```

---

## 🆘 Troubleshooting 2 minutos

| Problema | Solución |
|----------|----------|
| Teclado no aparece | 1. Asegúrate que es `QLineEdit` 2. Importa `enable_keyboard_for_widget` 3. Reinicia |
| Teclado no escribe | 1. Verifica que el input tiene focus 2. Revisa la consola 3. Reinicia app |
| Teclado se oculta rápido | Aumenta delay: `start(300)` en línea 264 |
| Teclas no responden | Comprueba que el `QLineEdit` no tiene `readOnly` |

---

## 📱 Probar Ahora

```bash
python example_virtual_keyboard.py
```

Se abrirá una ventana con 3 campos. ¡Haz click y prueba!

---

## 📚 Documentos Completos

- 📖 **TECLADO_VIRTUAL.md** - Guía detallada completa
- 📋 **CAMBIOS_TECLADO_VIRTUAL.md** - Cambios técnicos
- 🎨 **VISUALIZACION_TECLADO.md** - Vistas visuales
- ⚡ **QUICK_REFERENCE.md** - Este documento

---

## ✨ Lo Más Importante

```
1️⃣  El teclado es AUTOMÁTICO (aparece solo)
2️⃣  Funciona en TODAS las páginas
3️⃣  NO necesitas modificar código existente
4️⃣  Puedes usar helpers si necesitas control
5️⃣  Ver example_virtual_keyboard.py para ejemplos
```

---

## 🔗 Conexiones Rápidas

```python
# Importar lo que necesitas
from ui.keyboard_manager import VirtualKeyboardInstaller, VirtualKeyboard
from ui.keyboard_helper import KeyboardManager, enable_keyboard_for_widget

# Todo lo demás es automático ✨
```

---

## 🎯 Meta

- ✅ Implementado
- ✅ Testeado
- ✅ Documentado
- ✅ Listo para usar

**Nada más que hacer, ¡ya está todo funcionando!** 🚀
