# src/data_acquisition/player_id_manager.py

import pybaseball as pyb
import pandas as pd
import os

# Definimos la ruta de salida para mantener el código limpio
OUTPUT_DIR = "data/raw"
PLAYER_INDEX_FILE = os.path.join(OUTPUT_DIR, "player_id_master_index.csv")

def update_player_index():
    """
    Descarga el registro completo de jugadores del Chadwick Bureau
    y lo guarda como un archivo CSV. Este es nuestro "mapa" para traducir
    IDs entre diferentes fuentes de datos (MLB, FanGraphs, etc.).
    """
    print("Iniciando la descarga del registro de jugadores de Chadwick...")
    print("Esto puede tardar unos minutos, pero solo se hace una vez.")

    # Habilitar el caché de pybaseball para futuras consultas
    pyb.cache.enable()

    # Descargar la tabla de correspondencia de IDs
    try:
        player_lookup_table = pyb.chadwick_register()

        # Asegurarse de que el directorio de salida exista
        os.makedirs(OUTPUT_DIR, exist_ok=True)

        # Guardar el índice en la carpeta data/raw
        player_lookup_table.to_csv(PLAYER_INDEX_FILE, index=False)

        print(f"¡Éxito! Índice maestro de jugadores guardado en: {PLAYER_INDEX_FILE}")
        print(f"La tabla contiene {len(player_lookup_table)} registros de jugadores.")

    except Exception as e:
        print(f"Ocurrió un error al descargar o guardar el índice: {e}")

if __name__ == "__main__":
    # Esto permite que ejecutemos este script directamente desde la terminal
    # para actualizar nuestro índice cuando sea necesario.
    update_player_index()