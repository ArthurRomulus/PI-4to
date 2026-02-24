import cv2

def capturar_frame():
    cam = cv2.VideoCapture(0)

    if not cam.isOpened():
        print("Error: No se pudo abrir la cámara.")
        return None

    print("Presiona ESPACIO para capturar rostro...")

    while True:
        ret, frame = cam.read()
        if not ret:
            print("Error al leer la cámara.")
            break

        cv2.imshow("Captura de Rostro", frame)

        tecla = cv2.waitKey(1)

        # ESPACIO para capturar
        if tecla == 32:
            break

        # ESC para cancelar
        if tecla == 27:
            frame = None
            break

    cam.release()
    cv2.destroyAllWindows()

    return frame