# src/cache_manager.py
import json
import os
from datetime import datetime

CACHE_FILE = 'pitcher_stats_cache.json'
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CACHE_PATH = os.path.join(BASE_DIR, CACHE_FILE) # Guarda en la carpeta 'src'

def load_pitcher_cache():
    today_str = datetime.now().strftime('%Y-%m-%d')
    if not os.path.exists(CACHE_PATH):
        return {}
    try:
        with open(CACHE_PATH, 'r') as f:
            cache_data = json.load(f)
        if cache_data.get('date') == today_str:
            print("--- [Cache Manager] Caché de lanzadores cargado para hoy. ---")
            return cache_data.get('stats', {})
        else:
            print("--- [Cache Manager] El caché es antiguo. Se creará uno nuevo. ---")
            return {}
    except (json.JSONDecodeError, IOError):
        return {}

def save_pitcher_cache(pitcher_stats):
    today_str = datetime.now().strftime('%Y-%m-%d')
    cache_data = {'date': today_str, 'stats': pitcher_stats}
    try:
        with open(CACHE_PATH, 'w') as f:
            json.dump(cache_data, f, indent=4)
        print(f"--- [Cache Manager] Caché de lanzadores guardado. Contiene {len(pitcher_stats)} pitchers. ---")
    except IOError as e:
        print(f"--- [Cache Manager] ERROR al guardar el caché: {e} ---")