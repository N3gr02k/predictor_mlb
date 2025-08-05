# src/pitcher_analysis.py (Versión Optimizada)
import mlbstatsapi
import pandas as pd

mlb = mlbstatsapi.Mlb()

def get_pitcher_recent_stats(pitcher_id, year, limit=5):
    """
    Calcula el ERA, WHIP y K/9 de un lanzador en sus últimas 'limit' salidas.
    Ahora es más rápido porque no busca el nombre del jugador.
    """
    try:
        # 1. Obtener el game log del pitcher para la temporada especificada
        stats_response = mlb.get_player_stats(
            person_id=pitcher_id, 
            stats=['gameLog'], 
            groups=['pitching'],
            season=year
        )

        # 2. Navegar la estructura de datos que ya conocemos
        if 'pitching' not in stats_response or not hasattr(stats_response['pitching'], 'gamelog') or not stats_response['pitching'].gamelog.splits:
            return None

        # 3. Extraer, procesar y calcular las estadísticas
        stats_list = [split.stat for split in stats_response['pitching'].gamelog.splits]
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
        
        return { 'recent_era': era, 'recent_whip': whip, 'recent_k_per_9': k_per_9 }

    except Exception as e:
        print(f"--- [Pitcher Analysis] Ocurrió un error para pitcher ID {pitcher_id}: {e} ---")
        return None