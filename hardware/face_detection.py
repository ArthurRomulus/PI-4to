import cv2
import numpy as np


class FaceDetector:
    """Detector de rostros con validación de posicionamiento y distancia."""

    def __init__(self):
        """Inicializa el detector con Haar Cascade para cara y ojos."""
        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        )
        # Cascade de ojos — disponible en cualquier instalación de OpenCV
        self.eye_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_eye.xml'
        )
        
    def detect_and_validate(self, frame):
        """
        Detecta rostros y valida posicionamiento en óvalo y distancia.
        
        Args:
            frame: Frame de OpenCV (BGR)
            
        Returns:
            dict con resultados de detección y validación
        """
        frame_h, frame_w = frame.shape[:2]
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Detectar rostros — parámetros relajados para tolerar pelo y oclusión parcial
        faces = self.face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.05,
            minNeighbors=5,
            minSize=(80, 80)
        )
        
        # Parámetros del óvalo
        oval_center = (frame_w // 2, frame_h // 2)
        oval_axes = (frame_w // 4, frame_h // 3)
        
        result = {
            'faces': faces,
            'oval_center': oval_center,
            'oval_axes': oval_axes,
            'face_inside_oval': False,
            'face_distance_ok': False,
            'distance_status': 'Distance unknown',
            'alignment_status': 'No face detected',
            'oval_color': (0, 0, 255),  # Rojo por defecto
            'face_center': None,
            'face_rect': None,
            # Crop anclado en ojos (invariante al pelo)
            'face_crop_hint': None
        }
        
        if len(faces) > 0:
            # Tomar el rostro más grande
            x, y, w, h = max(faces, key=lambda rect: rect[2] * rect[3])
            face_center = (x + w // 2, y + h // 2)
            result['face_rect'] = (x, y, w, h)
            result['face_center'] = face_center

            # ── Crop anclado en ojos (invariante al pelo) ──────────────────────
            result['face_crop_hint'] = self._eye_anchored_crop(
                gray, frame_h, frame_w, x, y, w, h
            )

            # Validar posicionamiento dentro del óvalo (margen +15% para tolerar pelo)
            dx = (face_center[0] - oval_center[0]) / float(oval_axes[0])
            dy = (face_center[1] - oval_center[1]) / float(oval_axes[1])
            if dx * dx + dy * dy <= 1.15:
                result['face_inside_oval'] = True

            # Validar distancia — rango ampliado para evitar falsos rechazos por pelo
            face_ratio = float(h) / frame_h
            min_ratio = 0.30
            max_ratio = 0.80

            if face_ratio < min_ratio:
                result['distance_status'] = 'Acerquese a la camara'
            elif face_ratio > max_ratio:
                result['distance_status'] = 'Alejese un poco'
            else:
                result['distance_status'] = 'Distance OK'
                result['face_distance_ok'] = True

            # Determinar estado general y color del óvalo
            if result['face_inside_oval'] and result['face_distance_ok']:
                result['oval_color'] = (0, 255, 0)  # Verde - OK
                result['alignment_status'] = 'Face aligned and distance OK'
            elif result['face_inside_oval']:
                result['oval_color'] = (0, 255, 255)  # Amarillo - distancia
                result['alignment_status'] = result['distance_status']
            else:
                result['oval_color'] = (0, 0, 255)  # Rojo - Alinear
                result['alignment_status'] = 'Align face inside oval'
        else:
            result['alignment_status'] = 'Align face inside oval'
        
        return result

    def _eye_anchored_crop(self, gray, frame_h, frame_w, x, y, w, h):
        """
        Calcula un crop de la cara anclado en la posición de los ojos,
        ignorando el pelo (que queda fuera del recorte).

        Retorna (cx, cy, cw, ch) o None si no se detectan ojos.
        """
        # Buscar ojos solo en la mitad superior del bbox de la cara
        roi_top = y
        roi_bot = y + int(h * 0.65)   # ojos nunca están más abajo del 65%
        roi_h   = roi_bot - roi_top
        face_roi = gray[roi_top:roi_bot, x:x + w]

        eyes = self.eye_cascade.detectMultiScale(
            face_roi,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(20, 20)
        )

        if len(eyes) >= 2:
            # Centros de ojo en coordenadas absolutas del frame
            centers = [
                (x + ex + ew // 2, roi_top + ey + eh // 2)
                for ex, ey, ew, eh in eyes
            ]
            centers.sort(key=lambda c: c[0])   # izquierda → derecha
            left_eye  = centers[0]
            right_eye = centers[-1]

            cx_eyes   = (left_eye[0] + right_eye[0]) // 2
            cy_eyes   = (left_eye[1] + right_eye[1]) // 2
            eye_dist  = max(abs(right_eye[0] - left_eye[0]), 30)  # mínimo 30 px

            # Crop: arriba = 0.4 × eye_dist sobre los ojos (frente, sin pelo)
            #        abajo  = 1.8 × eye_dist bajo los ojos (nariz + boca + barbilla)
            #        lados  = ±1.0 × eye_dist
            pad_x  = int(eye_dist * 1.0)
            top    = max(0, cy_eyes - int(eye_dist * 0.4))
            bottom = min(frame_h, cy_eyes + int(eye_dist * 1.8))
            left   = max(0, cx_eyes - pad_x)
            right  = min(frame_w, cx_eyes + pad_x)

            cw = right - left
            ch = bottom - top
            if cw > 20 and ch > 20:
                return (left, top, cw, ch)

        # Fallback: recortar el 20% superior del bbox (donde suele estar el pelo)
        trim = int(h * 0.20)
        new_y = min(y + trim, y + h - 1)
        new_h = h - trim
        if new_h > 20:
            return (x, new_y, w, new_h)
        return (x, y, w, h)  # último recurso: bbox original
    
    def draw_face_detection(self, frame, detection_result):
        """
        Dibuja los elementos visuales de detección en el frame.
        
        Args:
            frame: Frame de OpenCV para dibujar
            detection_result: Resultado de detect_and_validate()
            
        Returns:
            Frame modificado con visualizaciones
        """
        frame_h, frame_w = frame.shape[:2]
        oval_center = detection_result['oval_center']
        oval_axes = detection_result['oval_axes']
        oval_color = detection_result['oval_color']
        
        # Dibujar óvalo de referencia
        cv2.ellipse(frame, oval_center, oval_axes, 0, 0, 360, oval_color, 2)
        
        # Dibujar rostro detectado si existe
        if detection_result['face_rect']:
            x, y, w, h = detection_result['face_rect']
            cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)
            if detection_result['face_center']:
                cv2.circle(frame, detection_result['face_center'], 4, (255, 0, 0), -1)
        
        # Dibujar textos de estado
        status_color = detection_result['oval_color']
        cv2.putText(
            frame,
            detection_result['alignment_status'],
            (10, frame_h - 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            status_color,
            2
        )
        
        return frame
