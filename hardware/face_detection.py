import cv2
import numpy as np


class FaceDetector:
    """Detector de rostros con validación de posicionamiento y distancia."""
    
    def __init__(self):
        """Inicializa el detector con Haar Cascade."""
        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
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
        
        # Detectar rostros con parámetros estrictos
        faces = self.face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.05,
            minNeighbors=8,
            minSize=(150, 150)
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
            'face_rect': None
        }
        
        if len(faces) > 0:
            # Tomar el rostro más grande
            x, y, w, h = max(faces, key=lambda rect: rect[2] * rect[3])
            face_center = (x + w // 2, y + h // 2)
            result['face_rect'] = (x, y, w, h)
            result['face_center'] = face_center
            
            # Validar posicionamiento dentro del óvalo
            dx = (face_center[0] - oval_center[0]) / float(oval_axes[0])
            dy = (face_center[1] - oval_center[1]) / float(oval_axes[1])
            if dx * dx + dy * dy <= 1.0:
                result['face_inside_oval'] = True
            
            # Validar distancia
            face_ratio = float(h) / frame_h
            min_ratio = 0.40
            max_ratio = 0.70
            
            if face_ratio < min_ratio:
                result['distance_status'] = 'Too far: move closer'
            elif face_ratio > max_ratio:
                result['distance_status'] = 'Too close: move back'
            else:
                result['distance_status'] = 'Distance OK'
                result['face_distance_ok'] = True
            
            # Determinar estado general y color del óvalo
            if result['face_inside_oval'] and result['face_distance_ok']:
                result['oval_color'] = (0, 255, 0)  # Verde - OK
                result['alignment_status'] = 'Face aligned and distance OK'
            elif result['face_inside_oval']:
                result['oval_color'] = (0, 255, 255)  # Amarillo - Posición OK pero distancia no
                result['alignment_status'] = result['distance_status']
            else:
                result['oval_color'] = (0, 0, 255)  # Rojo - Alinear
                result['alignment_status'] = 'Align face inside oval'
        else:
            result['alignment_status'] = 'Align face inside oval'
        
        return result
    
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
