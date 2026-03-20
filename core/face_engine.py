import face_recognition
import numpy as np
from config import FACE_TOLERANCE
from core.database_manager import DatabaseManager


class FaceEngine:

    def __init__(self):
        self.db = DatabaseManager()

    # ===================================
    # GENERAR ENCODING DESDE FRAME
    # ===================================

    def get_face_encoding(self, frame):
        """
        Recibe un frame BGR (OpenCV)
        Retorna encoding facial o None
        """

        rgb_frame = frame[:, :, ::-1]  # BGR → RGB
        face_locations = face_recognition.face_locations(rgb_frame)

        if not face_locations:
            return None

        encodings = face_recognition.face_encodings(rgb_frame, face_locations)

        if len(encodings) > 0:
            return encodings[0]

        return None

    def encode_face(self, frame):
        """
        Alias para get_face_encoding para compatibilidad.
        Recibe un frame BGR o RGB.
        Retorna encoding facial o None.
        """
        # Si el frame viene en RGB (shape[-1] == 3), usamos directo
        if len(frame.shape) == 3 and frame.shape[2] == 3:
            face_locations = face_recognition.face_locations(frame)
        else:
            rgb_frame = frame[:, :, ::-1]  # BGR → RGB
            face_locations = face_recognition.face_locations(rgb_frame)

        if not face_locations:
            return None

        if len(frame.shape) == 3 and frame.shape[2] == 3:
            encodings = face_recognition.face_encodings(frame, face_locations)
        else:
            rgb_frame = frame[:, :, ::-1]
            encodings = face_recognition.face_encodings(rgb_frame, face_locations)

        if len(encodings) > 0:
            return encodings[0]

        return None

    # ===================================
    # COMPARAR CON BASE DE DATOS
    # ===================================

    def recognize_face(self, frame):
        """
        Retorna:
        (True, id_user, name) si coincide
        (False, None, None) si no coincide
        """

        encoding = self.get_face_encoding(frame)

        if encoding is None:
            return (False, None, None)

        users = self.db.get_all_users()

        for id_user, name, user_type, stored_encoding in users:

            distance = np.linalg.norm(stored_encoding - encoding)

            if distance < FACE_TOLERANCE:
                return (True, id_user, name)

        return (False, None, None)

    # ===================================
    # PROMEDIO DE MÚLTIPLES ENCODINGS
    # ===================================

    def average_encodings(self, encoding_list):
        """
        Recibe lista de encodings
        Retorna promedio para registro más robusto
        """
        return np.mean(encoding_list, axis=0)