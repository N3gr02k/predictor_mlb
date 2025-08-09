# src/asset_loader.py (VERSIÓN FINAL COMPLETA)
import joblib
import pandas as pd
import os

def load_all_assets():
    print("--- [Asset Loader] Iniciando la carga de activos... ---")
    try:
        # La variable BASE_DIR apunta a la carpeta 'src'
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))

        # 1. Cargamos nuestro mejor modelo guardado (el XGBoost optimizado).
        model_path = os.path.join(BASE_DIR, 'assets', 'mlb_model_final_tuned.joblib')
        model = joblib.load(model_path)
        print(f"Modelo cargado desde: {model_path}")

        # 2. Cargamos el historial completo para los cálculos en vivo.
        data_path = os.path.join(BASE_DIR, '..', 'data', 'historical_games_rich.csv')
        historical_data = pd.read_csv(data_path, parse_dates=['game_date'])
        print(f"Datos históricos cargados desde: {data_path}")

        print("--- [Asset Loader] Todos los activos cargados exitosamente. ---")

        # Devolvemos un diccionario con los activos esenciales
        return {
            "model": model,
            "historical_data": historical_data
        }
        
    except FileNotFoundError as e:
        print(f"--- [Asset Loader] ERROR CRÍTICO: No se pudo encontrar un archivo de activo: {e}")
        print("Asegúrate de haber ejecutado 'build_dataset_v2.py' y '05_hyperparameter_tuning.ipynb'.")
        return None