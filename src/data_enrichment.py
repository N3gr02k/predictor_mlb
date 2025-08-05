# src/data_enrichment.py (Versión 2.1 - Corregido el nombre de la librería)
import mlbstatsapi
from datetime import datetime

# Creamos una instancia de la API
mlb = mlbstatsapi.Mlb()

def get_pitcher_current_season_stats(pitcher_full_name):
    """
    Obtiene las estadísticas de un lanzador para la temporada actual usando la API oficial.
    """
    print(f"\n--- BUSCANDO STATS PARA: {pitcher_full_name} ---")
    try:
        # 1. Buscar el ID del jugador
        player_ids = mlb.get_people_id(pitcher_full_name)
        
        if not player_ids:
            print(f"No se encontró el ID para el jugador: {pitcher_full_name}")
            return None
        
        mlbam_id = player_ids[0]
        
        # 2. Obtener las estadísticas de pitcheo de la temporada actual
        current_year = datetime.now().year
        stats = mlb.get_player_stats(mlbam_id, stats=['season'], groups=['pitching'])
        
        # 3. Extraer y devolver las estadísticas de la temporada
        if 'pitching' in stats and 'season' in stats['pitching'] and stats['pitching']['season']:
            pitcher_data = stats['pitching']['season']['stats']
            print("¡Estadísticas encontradas!")
            return pitcher_data
        else:
            print(f"No se encontraron estadísticas de pitcheo para {pitcher_full_name} en {current_year}.")
            return None

    except Exception as e:
        print(f"Ocurrió un error al buscar estadísticas: {e}")
        return None

# --- Bloque de prueba ---
if __name__ == '__main__':
    test_pitcher = "Gerrit Cole" 
    stats_dict = get_pitcher_current_season_stats(test_pitcher)
    
    if stats_dict:
        print("\n--- RESULTADO ---")
        print(f"ERA: {stats_dict.get('era', 'N/A')}")
        print(f"WHIP: {stats_dict.get('whip', 'N/A')}")
        print(f"Ponches: {stats_dict.get('strikeouts', 'N/A')}")
        print(f"Récord: {stats_dict.get('wins', 'N/A')}W - {stats_dict.get('losses', 'N/A')}L")