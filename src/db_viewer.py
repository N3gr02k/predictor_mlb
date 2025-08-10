# src/db_viewer.py

import pandas as pd
import sqlite3
import os

# Construimos la ruta a la base de datos
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'mlb_predictions.db')

def view_database_contents():
    """
    Se conecta a la base de datos SQLite y muestra el contenido de la tabla de predicciones.
    """
    if not os.path.exists(DB_PATH):
        print(f"ERROR: No se encontró el archivo de la base de datos en '{DB_PATH}'")
        print("Asegúrate de haber ejecutado la aplicación Flask al menos una vez para que se cree.")
        return

    try:
        # Nos conectamos a la base de datos
        conn = sqlite3.connect(DB_PATH)
        
        # Usamos pandas para leer la tabla 'prediction' y convertirla en un DataFrame
        print("--- Leyendo la tabla 'prediction' de la base de datos... ---")
        df = pd.read_sql_query("SELECT * FROM prediction", conn)
        
        # Cerramos la conexión
        conn.close()
        
        if df.empty:
            print("\nLa base de datos está vacía. Aún no se han guardado predicciones.")
        else:
            print(f"\nSe encontraron {len(df)} predicciones en la base de datos.")
            print("Mostrando las últimas 10 entradas:")
            # Mostramos las últimas 10 predicciones guardadas, ordenadas por fecha
            print(df.sort_values(by='prediction_date', ascending=False).head(10).to_string())

    except Exception as e:
        print(f"Ocurrió un error al leer la base de datos: {e}")

# ===================================================================
# BLOQUE PRINCIPAL DE EJECUCIÓN
# ===================================================================
if __name__ == "__main__":
    view_database_contents()
