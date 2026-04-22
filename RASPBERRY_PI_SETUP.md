# Configuración de Audio para Raspberry Pi 5

Si estás usando Raspberry Pi 5, ten en cuenta:

## 1. Instalación de dependencias de audio

```bash
sudo apt-get install -y pulseaudio alsa-utils
sudo apt-get install -y libqt5multimedia5 libqt5multimedia5-plugins
```

## 2. Configuración de audio en Raspberry Pi

Para garantizar que el audio funcione correctamente:

```bash
# Verificar que ALSA está configurado
alsamixer

# O usar PulseAudio (recomendado)
pulseaudio --start
```

## 3. Permisos de archivo

Asegúrate de que los archivos MP3 tienen permisos de lectura:

```bash
chmod 644 ui/assets/sounds/*.mp3
```

## 4. Prueba rápida del audio

```bash
# Desde Python
python -c "from PyQt5.QtMultimedia import QMediaPlayer; print('Audio OK')"
```

## 5. Notas de compatibilidad

- El volumen se reduce a 85% en Raspberry Pi para evitar "popping" de audio
- QMediaPlayer automáticamente detecta y usa el backend disponible (ALSA/PulseAudio)
- Si no hay audio, revisa `/var/log/syslog` para mensajes de error
- En headless mode (sin display), considera redirigir el audio por red o USB

## 6. Construcción completa en Raspberry Pi

```bash
# 1. Clonar/actualizar repositorio
git clone <repo>
cd PI-4to

# 2. Crear entorno virtual Python 3.10+
python3.10 -m venv .venv310
source .venv310/bin/activate

# 3. Instalar dependencias
pip install -r requirements.txt
pip install 'PyQt5>=5.15.9' 'opencv-python>=4.8.1.78' 'numpy>=1.24.3'

# 4. Ejecutar aplicación
python main.py
```
