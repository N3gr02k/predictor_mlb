# src/asset_loader.py
import joblib
import pandas as pd
import os

def load_all_assets():
    print("--- [Asset Loader] Iniciando la carga de activos... ---")
    try:
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        
        model = joblib.load(os.path.join(BASE_DIR, 'ml_model', 'mlb_ultimate_model.pkl'))
        team_stats_map = joblib.load(os.path.join(BASE_DIR, 'ml_model', 'team_stats_map.pkl'))
        team_history_map = joblib.load(os.path.join(BASE_DIR, 'ml_model', 'team_history_map.pkl'))
        
        df_pitchers = pd.read_csv(os.path.join(BASE_DIR, 'data', 'pitching_stats_lahman.csv'))
        df_pitchers['IP'] = df_pitchers['ipouts'] / 3
        df_pitchers['WHIP'] = (df_pitchers['h'] + df_pitchers['bb']) / df_pitchers['IP'].replace(0, pd.NA)
        df_pitchers['K_per_9'] = (df_pitchers['so'] * 9) / df_pitchers['IP'].replace(0, pd.NA)
        
        avg_pitcher_stats = {
            'era': df_pitchers[df_pitchers['gs'] > 10]['era'].mean(),
            'whip': df_pitchers[df_pitchers['gs'] > 10]['WHIP'].mean(),
            'k_per_9': df_pitchers[df_pitchers['gs'] > 10]['K_per_9'].mean()
        }
        
        print("--- [Asset Loader] Todos los activos cargados exitosamente. ---")
        
        return {
            "model": model,
            "team_stats_map": team_stats_map,
            "team_history_map": team_history_map,
            "avg_pitcher_stats": avg_pitcher_stats
        }

    except Exception as e:
        print(f"--- [Asset Loader] ERROR CRÍTICO al cargar archivos: {e} ---")
        return { "model": None, "team_stats_map": {}, "team_history_map": {}, "avg_pitcher_stats": {} }