# src/run_daily_predictions.py

from datetime import datetime
import sys
import os

# --- Configuración del Path de Python ---
# Esto es necesario para que el script pueda encontrar y importar 'app.py' correctamente.
# Añade la carpeta raíz del proyecto ('predictor_mlb') al path.
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

# Ahora podemos importar desde 'src'
# CAMBIO CLAVE: Importar el nombre de función correcto
from src.app import get_predictions_for_date, app

def pre_populate_cache_for_today():
    """
    Ejecuta el proceso de predicción para la fecha actual y guarda los resultados en la caché.
    Esta función está diseñada para ser ejecutada por una tarea programada.
    """
    today_str = datetime.now().strftime('%Y-%m-%d')
    print(f"--- Iniciando pre-población de la caché para: {today_str} ---")
    
    # Usamos 'app_context' para que la función de caché tenga acceso a la configuración de la app Flask.
    with app.app_context():
        # --- CAMBIO CLAVE: Asegurarse de que el directorio de la caché exista ---
        cache_dir = app.config.get('CACHE_DIR')
        if cache_dir and not os.path.exists(cache_dir):
            os.makedirs(cache_dir)
            print(f"--- Directorio de caché creado en: {cache_dir} ---")
        # --------------------------------------------------------------------

        # CAMBIO CLAVE: Llamar a la función con el nombre correcto
        get_predictions_for_date(today_str)
    
    print("--- Proceso de pre-población de la caché completado. ---")

# ===================================================================
# BLOQUE PRINCIPAL DE EJECUCIÓN
# ===================================================================
if __name__ == "__main__":
    pre_populate_cache_for_today()
