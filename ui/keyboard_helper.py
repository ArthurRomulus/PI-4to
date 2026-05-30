"""
Helper para facilitar el uso del teclado virtual en componentes personalizados.
Este módulo proporciona funcionalidades adicionales para mejorar la experiencia
del teclado virtual en formularios y dialogs.
"""

from PyQt5.QtWidgets import QLineEdit, QWidget
from PyQt5.QtCore import Qt


class KeyboardEnabledComponent:
    """
    Mixin class que proporciona acceso automático a QLineEdit para el teclado virtual.
    
    Uso:
        class MiComponente(QFrame, KeyboardEnabledComponent):
            def __init__(self):
                super().__init__()
                self.setup_keyboard_inputs([self.input1, self.input2])
    """
    
    def setup_keyboard_inputs(self, inputs_list):
        """
        Configura una lista de QLineEdit para que muestren el teclado virtual automáticamente.
        
        Args:
            inputs_list: Lista de QLineEdit widgets a configurar
        """
        for line_edit in inputs_list:
            if isinstance(line_edit, QLineEdit):
                # El teclado se mostrará automáticamente al hacer focus
                line_edit.setFocusPolicy(Qt.StrongFocus)


def get_all_line_edits(widget):
    """
    Obtiene todos los QLineEdit dentro de un widget.
    
    Args:
        widget: El widget padre
        
    Returns:
        Lista de todos los QLineEdit encontrados
    """
    return widget.findChildren(QLineEdit)


def enable_keyboard_for_widget(widget):
    """
    Habilita automáticamente el teclado virtual para todos los QLineEdit en un widget.
    
    Args:
        widget: El widget contenedor
    """
    line_edits = get_all_line_edits(widget)
    for line_edit in line_edits:
        line_edit.setFocusPolicy(Qt.StrongFocus)


class KeyboardManager:
    """
    Gestor centralizado para manejar múltiples instancias del teclado virtual.
    """
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(KeyboardManager, cls).__new__(cls)
            cls._instance.keyboard_installer = None
        return cls._instance
    
    def set_installer(self, installer):
        """Registra la instancia del VirtualKeyboardInstaller"""
        self.keyboard_installer = installer
    
    def get_keyboard(self):
        """Obtiene la instancia del teclado virtual"""
        if self.keyboard_installer:
            return self.keyboard_installer.keyboard
        return None
    
    def show_keyboard_for(self, line_edit):
        """Muestra el teclado para un QLineEdit específico"""
        keyboard = self.get_keyboard()
        if keyboard:
            installer = self.keyboard_installer
            if installer is not None and hasattr(installer, "show_keyboard_for"):
                installer.show_keyboard_for(line_edit)
            else:
                keyboard.show_with_target(line_edit)
    
    def hide_keyboard(self):
        """Oculta el teclado virtual"""
        installer = self.keyboard_installer
        if installer is not None and hasattr(installer, "hide_keyboard"):
            installer.hide_keyboard()
            return

        keyboard = self.get_keyboard()
        if keyboard:
            keyboard.hide()
