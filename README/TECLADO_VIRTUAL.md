# Teclado Virtual Estilo Celular

## Descripción

Se ha mejorado el teclado virtual con un diseño moderno estilo celular/móvil que se activa automáticamente cuando el usuario toca (hace focus) en cualquier campo `QLineEdit` de la aplicación.

## Características

✅ **Diseño estilo móvil**: Teclado moderno con colores fluidos y bordes redondeados
✅ **Activación automática**: Se muestra al hacer focus en un campo de texto
✅ **Teclas especiales**: Shift (⇧), Espacio, Borrar (⌫), Aceptar (✓)
✅ **Integración global**: Funciona en toda la aplicación
✅ **Posicionamiento inteligente**: Se posiciona en la parte inferior de la pantalla
✅ **Cierre automático**: Se oculta al perder el focus

## Estructura

### Archivos principales:

```
ui/
├── keyboard_manager.py      # Teclado virtual mejorado (VirtualKeyboard)
├── keyboard_helper.py       # Helpers para integración (NUEVO)
└── ...

main.py                       # Punto de entrada con inicialización del teclado
```

## Cómo funciona

### 1. Inicialización Global (main.py)

El teclado se inicializa automáticamente en la aplicación:

```python
from ui.keyboard_manager import VirtualKeyboardInstaller
from ui.keyboard_helper import KeyboardManager

app = QApplication(sys.argv)
keyboard_installer = VirtualKeyboardInstaller(app)
app.installEventFilter(keyboard_installer)

# Registrar en el gestor centralizado
KeyboardManager().set_installer(keyboard_installer)
```

### 2. Uso en componentes (Automático)

El teclado se muestra automáticamente cuando cualquier `QLineEdit` recibe focus:

```python
from PyQt5.QtWidgets import QLineEdit

# El teclado se mostrará automáticamente
input_field = QLineEdit()
parent_widget.addWidget(input_field)
```

### 3. Uso en componentes personalizados (IconInput)

Para componentes personalizados como `IconInput`:

```python
# El teclado funciona automáticamente con self.input
self.input = QLineEdit()
self.input.setFocusPolicy(Qt.StrongFocus)  # Asegurar que puede recibir focus
```

## Páginas que usan el teclado

Las siguientes páginas ya tienen integración automática:

- ✅ `ui/admin/login_window.py` - Login
- ✅ `ui/admin/admin_dialog.py` - Diálogo de admin
- ✅ `ui/admin/change_password_window.py` - Cambio de contraseña
- ✅ `ui/admin/create_admin_window.py` - Crear admin
- ✅ `ui/admin/forgot_password_window.py` - Recuperar contraseña
- ✅ `ui/admin/registerpage.py` - Registro
- ✅ `ui/admin/users_page.py` - Gestión de usuarios
- ✅ `ui/admin/privacy_notice.py` - Aviso de privacidad
- ✅ `ui/admin/access_page.py` - Página de acceso

## Ejemplos de uso

### Ejemplo 1: Componente simple

```python
from PyQt5.QtWidgets import QLineEdit
from PyQt5.QtCore import Qt

# El teclado se mostrará automáticamente
input_field = QLineEdit()
input_field.setFocusPolicy(Qt.StrongFocus)
input_field.setPlaceholderText("Ingrese texto...")
```

### Ejemplo 2: Componente personalizado

```python
from PyQt5.QtWidgets import QFrame, QVBoxLayout, QLineEdit, QPushButton
from PyQt5.QtCore import Qt
from ui.keyboard_helper import enable_keyboard_for_widget

class CustomInputFrame(QFrame):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        
        self.input = QLineEdit()
        self.input.setFocusPolicy(Qt.StrongFocus)
        layout.addWidget(self.input)
        
        # Habilitar teclado para todos los QLineEdit del widget
        enable_keyboard_for_widget(self)
```

### Ejemplo 3: Con gestor centralizado

```python
from PyQt5.QtWidgets import QLineEdit
from ui.keyboard_helper import KeyboardManager

input_field = QLineEdit()

# Mostrar teclado explícitamente si es necesario
keyboard_manager = KeyboardManager()
keyboard_manager.show_keyboard_for(input_field)

# Ocultar teclado si es necesario
keyboard_manager.hide_keyboard()
```

## Funciones Helper

### KeyboardManager (Gestor centralizado)

```python
from ui.keyboard_helper import KeyboardManager

manager = KeyboardManager()

# Mostrar teclado para un input específico
manager.show_keyboard_for(line_edit)

# Ocultar teclado
manager.hide_keyboard()

# Obtener instancia del teclado
keyboard = manager.get_keyboard()
```

### enable_keyboard_for_widget

```python
from ui.keyboard_helper import enable_keyboard_for_widget

# Habilita el teclado para todos los QLineEdit en un widget
enable_keyboard_for_widget(parent_widget)
```

### get_all_line_edits

```python
from ui.keyboard_helper import get_all_line_edits

# Obtiene todos los QLineEdit de un widget
inputs = get_all_line_edits(parent_widget)
for input_field in inputs:
    # Hacer algo con cada input
    input_field.setPlaceholderText("Ingrese...")
```

## Personalización del teclado

### Cambiar colores

En `ui/keyboard_manager.py`, sección `__init__` del `VirtualKeyboard`:

```python
self.setStyleSheet("""
    QWidget#VirtualKeyboard {
        background: rgba(15, 23, 42, 0.98);  # Cambiar color de fondo
        border: 1px solid rgba(148, 163, 184, 0.25);
        border-radius: 20px;
    }
    ...
""")
```

### Cambiar tamaño

```python
# En VirtualKeyboard.__init__
self.setFixedHeight(300)  # Altura del teclado
```

### Cambiar fuente

En el método `_make_key`:

```python
font = QFont()
font.setPointSize(13)  # Cambiar tamaño
font.setBold(True)     # Cambiar negrita
button.setFont(font)
```

## Flujo de interacción

```
Usuario hace click en QLineEdit
        ↓
VirtualKeyboardInstaller detecta FocusIn
        ↓
VirtualKeyboard.show_with_target(QLineEdit)
        ↓
Teclado se posiciona en la parte inferior
        ↓
Usuario presiona teclas
        ↓
Texto se inserta en el QLineEdit
        ↓
Usuario presiona ✓ (Enter)
        ↓
Usuario hace click fuera del input
        ↓
VirtualKeyboardInstaller detecta FocusOut
        ↓
Teclado se oculta automáticamente
```

## Notas técnicas

- El teclado usa `Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint` para mantenerse siempre visible
- Se actualiza automáticamente al hacer cambios en shift
- Soporta seleccionar texto y reemplazarlo
- El backspace funciona en la selección actual

## Troubleshooting

### El teclado no aparece

1. Asegúrate que el widget es un `QLineEdit` o hereda de él
2. Verifica que `setFocusPolicy(Qt.StrongFocus)` está configurado
3. Comprueba que el `VirtualKeyboardInstaller` está inicializado en `main.py`

### El teclado aparece pero no escribe

1. Verifica que el `QLineEdit` tiene focus
2. Comprueba que no hay un `textChanged` signal que interfiera
3. Revisa que el teclado está conectado correctamente en el event filter

### El teclado se oculta demasiado rápido

Ajusta el tiempo del timer en `VirtualKeyboardInstaller`:

```python
self._delay_close_timer.start(150)  # Aumentar este valor
```

## Integración futura

Para agregar el teclado en nuevos widgets:

1. Asegúrate que tus inputs son `QLineEdit`
2. El teclado se mostrará automáticamente (sin necesidad de código adicional)
3. Opcionalmente, usa los helpers de `keyboard_helper.py` para más control

## Licencia

Parte del proyecto PI-4to
