from database.consultas import guardar_usuario as guardar_usuario_db

def guardar_usuario(nombre, embedding, account_number=None):
    """
    Guarda un usuario con su embedding facial en la base de datos.
    
    Args:
        nombre: Nombre del usuario
        embedding: Embedding facial (numpy array)
        account_number: Número de cuenta opcional (se genera automáticamente si no se proporciona)
    
    Returns:
        Dict con 'user_id' y 'account_number' si éxito, False si error
    """
    resultado = guardar_usuario_db(nombre, embedding, account_number)
    if resultado and isinstance(resultado, dict):
        print(f"Usuario '{nombre}' guardado correctamente con número de cuenta: {resultado['account_number']}.")
        return resultado
    else:
        print(f"Error guardando usuario '{nombre}'.")
        return False
        return False
