import hashlib
from config import ADMIN_PIN


class SecurityManager:
    """Gestor de seguridad del sistema."""

    @staticmethod
    def hash_pin(pin):
        """
        Hashea un PIN usando SHA256.
        """
        return hashlib.sha256(pin.encode()).hexdigest()

    @staticmethod
    def verify_pin(pin, pin_hash):
        """
        Verifica que un PIN coincida con su hash.
        """
        return hashlib.sha256(pin.encode()).hexdigest() == pin_hash

    @staticmethod
    def get_default_admin_pin_hash():
        """
        Retorna el hash del PIN de administrador por defecto.
        """
        return SecurityManager.hash_pin(ADMIN_PIN)