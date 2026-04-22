import os
import sys
import platform

from PyQt5.QtCore import QObject, QEvent, QUrl
from PyQt5.QtWidgets import QWidget, QPushButton
from PyQt5.QtMultimedia import QMediaContent, QMediaPlayer

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SOUNDS_DIR = os.path.join(BASE_DIR, "assets", "sounds")

# Detectar plataforma para optimización
_IS_RASPBERRY_PI = os.path.isfile('/etc/os-release') and 'Raspberry' in open('/etc/os-release').read() if os.path.isfile('/etc/os-release') else False
_PLATFORM = platform.system()


class _SoundPlayer(QObject):
    def __init__(self):
        super().__init__()
        self._players = []
        self._audio_available = True
        self._test_audio_backend()

    def _test_audio_backend(self):
        """Verifica si el backend de audio está disponible."""
        try:
            test_player = QMediaPlayer()
            # En Raspberry Pi, a veces QMediaPlayer necesita un pequeño tiempo para inicializarse
            if _IS_RASPBERRY_PI:
                test_player.setVolume(0)
            test_player.deleteLater()
        except Exception as e:
            print(f"[audio] Advertencia: Backend de audio no disponible: {e}")
            self._audio_available = False

    def play(self, filename):
        if not self._audio_available:
            return False

        file_path = os.path.abspath(os.path.join(SOUNDS_DIR, filename))
        if not os.path.exists(file_path):
            print(f"[audio] Archivo no encontrado: {file_path}")
            return False

        try:
            player = QMediaPlayer()
            # Volumen al máximo (100%)
            player.setVolume(100)
            player.setMedia(QMediaContent(QUrl.fromLocalFile(file_path)))
            player.stateChanged.connect(lambda state, current=player: self._cleanup(current, state))
            player.error.connect(lambda error, current=player, filename=filename: self._on_error(current, error, filename))
            self._players.append(player)
            player.play()
            return True
        except Exception as e:
            print(f"[audio] Error reproduciendo {filename}: {e}")
            return False

    def _cleanup(self, player, state):
        if state == QMediaPlayer.StoppedState and player in self._players:
            self._players.remove(player)
            player.deleteLater()

    def _on_error(self, player, error, filename):
        if error != QMediaPlayer.NoError:
            print(f"[audio] Error en QMediaPlayer para {filename}: {player.errorString()}")
        self._cleanup(player, QMediaPlayer.StoppedState)


_sound_player = _SoundPlayer()


def play_sound(filename):
    """Reproduce un archivo de sonido. Retorna True si fue exitoso."""
    try:
        return _sound_player.play(filename)
    except Exception as e:
        print(f"[audio] Excepción inesperada al reproducir {filename}: {e}")
        return False


class _ButtonSoundInstaller(QObject):
    """Instalador global de sonidos para botones mediante event filter.
    
    Compatible con Windows, Linux (incluyendo Raspberry Pi).
    Agrega automáticamente sonido a todos los QPushButton nuevos.
    """
    
    def __init__(self, default_sound="sistema.mp3", parent=None):
        super().__init__(parent)
        self.default_sound = default_sound
        self._hooked_buttons = set()

    def eventFilter(self, obj, event):
        if event.type() in (QEvent.Show, QEvent.Polish, QEvent.ChildAdded) and isinstance(obj, QWidget):
            self._attach_button_sounds(obj)
        return False

    def _attach_button_sounds(self, root_widget):
        """Busca y engancha sonidos a botones no procesados."""
        for button in root_widget.findChildren(QPushButton):
            button_id = id(button)
            if button_id in self._hooked_buttons:
                continue

            sound_file = button.property("sound_file") or self.default_sound
            try:
                button.pressed.connect(lambda sound_name=sound_file: play_sound(sound_name))
                self._hooked_buttons.add(button_id)
            except Exception as e:
                print(f"[audio] Error enganchando sonido al botón: {e}")


def install_global_button_sounds(app, default_sound="sistema.mp3"):
    """Instala filtro global de sonidos en la aplicación.
    
    Args:
        app: Instancia de QApplication
        default_sound: Nombre del archivo MP3 por defecto (ej: 'sistema.mp3')
    
    Uso:
        install_global_button_sounds(app)
    
    Compatible con Windows, Linux y Raspberry Pi.
    """
    installer = _ButtonSoundInstaller(default_sound=default_sound, parent=app)
    app.installEventFilter(installer)
    app._button_sound_installer = installer
    return installer
