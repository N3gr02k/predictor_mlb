# src/batter_analysis.py (Versión FINAL Y FUNCIONAL para Bateadores)
import mlbstatsapi
from datetime import datetime

mlb = mlbstatsapi.Mlb()

def get_batter_season_obp(player_name, year):
    """
    Obtiene el Porcentaje de Embasado (OBP) de un bateador para un año específico.
    """
    print(f"--- Buscando OBP para: {player_name}, año {year} ---")
    try:
        # 1. Buscar el ID del jugador
        player_ids = mlb.get_people_id(player_name)
        if not player_ids:
            print(f"No se encontró el ID para: {player_name}")
            return None

        player_id = player_ids[0]
        print(f"ID encontrado para {player_name}: {player_id}")

        # 2. Solicitar las estadísticas de la temporada
        stats_response = mlb.get_player_stats(
            person_id=player_id,
            stats=['season'],
            groups=['hitting'],
            season=year
        )
        
        # 3. Extraer el OBP usando la ruta correcta y la sintaxis de diccionario
        if (stats_response and 'hitting' in stats_response and
            'season' in stats_response['hitting'] and 
            hasattr(stats_response['hitting']['season'], 'splits') and
            stats_response['hitting']['season'].splits):
            
            # Las estadísticas están en el primer (y único) elemento de la lista 'splits'
            season_stats_obj = stats_response['hitting']['season'].splits[0].stat
            
            # Usamos getattr para acceder de forma segura al atributo 'obp' del objeto de estadísticas
            obp = getattr(season_stats_obj, 'obp', 'N/A')
            
            print(f"¡Éxito! OBP encontrado.")
            return obp
        else:
            print("No se encontraron estadísticas de bateo para esta temporada.")
            return None

    except Exception as e:
        print(f"Ocurrió un error al extraer las estadísticas: {e}")
        return None

# --- Bloque de prueba ---
if __name__ == '__main__':
    test_player = "Aaron Judge"
    test_year = 2023
    
    on_base_percentage = get_batter_season_obp(test_player, test_year)
    
    if on_base_percentage:
        print("\n--- RESULTADO ---")
        print(f"El OBP de {test_player} en {test_year} fue: {on_base_percentage}")