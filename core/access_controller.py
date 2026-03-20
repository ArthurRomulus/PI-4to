from core.face_engine import FaceEngine
from core.database_manager import DatabaseManager
from core.hardware.motor_controller import MotorController


class AccessController:

    def __init__(self):
        self.face_engine = FaceEngine()
        self.db = DatabaseManager()

        # Inicializar motor solo si estamos en Raspberry
        try:
            self.motor = MotorController()
        except Exception:
            self.motor = None  # Permite pruebas en PC sin GPIO

    # ==========================================
    # PROCESO DE VERIFICACIÓN
    # ==========================================

    def process_access(self, frame):
        """
        Recibe un frame de cámara.
        Retorna diccionario con resultado.
        """

        recognized, id_user, name = self.face_engine.recognize_face(frame)

        if recognized:
            # Registrar acceso autorizado
            self.db.insert_access(id_user, "AUTHORIZED")

            # Activar motor si existe
            if self.motor:
                self.motor.open_door()

            return {
                "status": "AUTHORIZED",
                "id_user": id_user,
                "name": name
            }

        else:
            # Registrar intento fallido
            self.db.insert_access(None, "DENIED")

            return {
                "status": "DENIED",
                "id_user": None,
                "name": None
            }

    def verify_face(self, frame):
        """
        Verifica si el rostro en el frame coincide con algún usuario.
        Retorna dict con info del usuario o None.
        """
        recognized, id_user, name = self.face_engine.recognize_face(frame)

        if recognized:
            user_data = self.db.get_user_by_id(id_user)
            if user_data:
                id_user, name, user_type, encoding = user_data
                # Registrar acceso autorizado
                self.db.insert_access(id_user, "AUTHORIZED")
                
                # Activar motor si existe
                if self.motor:
                    self.motor.open_door()
                
                return {
                    "id": id_user,
                    "name": name,
                    "type": user_type
                }
        
        # Registrar intento fallido
        self.db.insert_access(None, "DENIED")
        return None

    # ==========================================
    # REGISTRO DE NUEVO USUARIO
    # ==========================================

    def register_user(self, name, user_type, encoding):
        """
        Guarda nuevo usuario en base de datos
        """
        self.db.insert_user(name, user_type, encoding)

    # ==========================================
    # VERIFICACIÓN ADMIN
    # ==========================================

    def verify_admin(self, username, pin):
        return self.db.verify_admin(username, pin)

    # ==========================================
    # LIMPIEZA DE HARDWARE
    # ==========================================

    def cleanup(self):
        if self.motor:
            self.motor.cleanup()