import mysql.connector

def obtener_conexion():
    try:
        conexion = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",   # En XAMPP normalmente está vacío
            database="reconocimiento_facial",
            port=3306
        )
        return conexion
    except mysql.connector.Error as e:
        print("Error de conexión:", e)
        return None