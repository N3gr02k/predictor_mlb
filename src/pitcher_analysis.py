# src/pitcher_analysis.py (Versión Optimizada con Caché)
import mlbstatsapi
import pandas as pd
from datetime import datetime
from .cache_manager import load_pitcher_cache, save_pitcher_cache # <-- ¡NUEVA IMPORTACIÓN!

mlb = mlbstatsapi.Mlb()

# --- CARGA INICIAL DEL CACHÉ ---
# Cargamos el caché una sola vez cuando el módulo se importa por primera vez
PITCHER_STATS_CACHE = load_pitcher_cache()

def get_pitcher_recent_stats(pitcher_id, year, limit=5):
    """
    Calcula el ERA, WHIP y K/9 de un lanzador.
    Primero busca en el caché y, si no lo encuentra, llama a la API y guarda el resultado.
    """
    # Convertimos el ID a string para usarlo como clave en el JSON del caché
    pitcher_id_str = str(pitcher_id)

    # 1. Revisa si el resultado ya está en nuestro caché
    if pitcher_id_str in PITCHER_STATS_CACHE:
        print(f"--- [Pitcher Analysis] Stats para Pitcher ID {pitcher_id_str} encontradas en CACHÉ. ---")
        return PITCHER_STATS_CACHE[pitcher_id_str]

    # 2. Si no está en el caché, procede a buscarlo en la API
    print(f"\n--- [Pitcher Analysis] Buscando stats en API para Pitcher ID: {pitcher_id}, Año: {year} ---")
    try:
        stats_response = mlb.get_player_stats(
            person_id=pitcher_id, 
            stats=['gameLog'], 
            groups=['pitching'],
            season=year
        )

        if 'pitching' not in stats_response or not hasattr(stats_response['pitching'], 'gamelog') or not stats_response['pitching'].gamelog.splits:
            return None

        stats_list = [vars(split.stat) for split in stats_response['pitching'].gamelog.splits]
        gamelog_df = pd.DataFrame(stats_list)
        
        cols_to_numeric = ['inningspitched', 'baseonballs', 'hits', 'earnedruns', 'strikeouts']
        for col in cols_to_numeric:
            gamelog_df[col] = pd.to_numeric(gamelog_df[col], errors='coerce')

        gamelog_df.dropna(subset=cols_to_numeric, inplace=True)
        recent_games = gamelog_df[gamelog_df['inningspitched'].astype(float) > 0].tail(limit)

        if recent_games.empty:
            return None

        total_ip = recent_games['inningspitched'].astype(float).sum()
        if total_ip == 0: return None
        
        total_walks = recent_games['baseonballs'].astype(int).sum()
        total_hits = recent_games['hits'].astype(int).sum()
        total_er = recent_games['earnedruns'].astype(int).sum()
        total_so = recent_games['strikeouts'].astype(int).sum()

        era = (total_er * 9) / total_ip
        whip = (total_walks + total_hits) / total_ip
        k_per_9 = (total_so * 9) / total_ip
        
        recent_stats = { 'recent_era': era, 'recent_whip': whip, 'recent_k_per_9': k_per_9 }
        
        # 3. Guarda el nuevo resultado en el caché y en el archivo
        PITCHER_STATS_CACHE[pitcher_id_str] = recent_stats
        save_pitcher_cache(PITCHER_STATS_CACHE)
        
        print("--- [Pitcher Analysis] ¡Estadísticas calculadas y guardadas en caché! ---")
        return recent_stats

    except Exception as e:
        print(f"--- [Pitcher Analysis] Ocurrió un error: {e} ---")
        return None