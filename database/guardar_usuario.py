import pickle
from database.consultas import guardar_usuario as guardar_usuario_db

def guardar_usuario(nombre, embedding, account_number=None):
    """
    Guarda un usuario con su embedding facial en la base de datos.
    
    Args:
        nombre: Nombre del usuario
        embedding: Embedding facial (numpy array)
        account_number: Número de cuenta opcional
    
    Returns:
        ID del usuario creado o False si hubo error
    """
    resultado = guardar_usuario_db(nombre, embedding, account_number)
    if resultado:
        print(f"Usuario '{nombre}' guardado correctamente.")
        return resultado
    else:
        print(f"Error guardando usuario '{nombre}'.")
        return False
