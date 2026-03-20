from core.database_manager import DatabaseManager

def test_verify_admin():
    db_manager = DatabaseManager()

    # Credenciales de prueba
    username = "administrador"
    password = "12345678"

    # Verificar credenciales
    is_valid = db_manager.verify_admin(username, password)

    if is_valid:
        print(f"Credenciales correctas para el usuario: {username}")
    else:
        print(f"Credenciales incorrectas para el usuario: {username}")

if __name__ == "__main__":
    test_verify_admin()