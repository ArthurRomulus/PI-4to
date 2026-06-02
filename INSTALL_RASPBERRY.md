# Instalación en Raspberry Pi

## Paquetes del sistema

```bash
sudo apt update
sudo apt install -y python3-pyqt5 python3-opencv python3-numpy python3-rpi.gpio v4l-utils
```

## Verificación de webcam USB

```bash
ls /dev/video*
v4l2-ctl --list-devices
```

## Paquetes de Python

```bash
python3 -m pip install -r requirements.txt
```

## Prueba rápida

```bash
python3 test_camera.py
```