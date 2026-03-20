import sqlite3
from config import DATABASE_PATH

def inspect_admins():
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT * FROM admins")
        rows = cursor.fetchall()

        if rows:
            print("Contenido de la tabla 'admins':")
            for row in rows:
                print(row)
        else:
            print("La tabla 'admins' está vacía.")

    except Exception as e:
        print(f"Error al consultar la tabla 'admins': {e}")

    finally:
        conn.close()

if __name__ == "__main__":
    inspect_admins()