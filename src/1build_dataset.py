# src/build_dataset.py

import data_enrichment as de
from datetime import datetime, timedelta
import pandas as pd
import requests
import time
import calendar

def get_games_for_date(date):
    """
    Obtiene la lista de partidos finalizados para una fecha específica.
    """
    print(f"\n--- Obteniendo partidos para la fecha: {date.strftime('%Y-%m-%d')} ---")
    schedule_url = f"{de.BASE_API_URL}/schedule"
    schedule_params = {'sportId': 1, 'date': date.strftime('%Y-%m-%d')}
    try:
        response = requests.get(schedule_url, params=schedule_params, timeout=15)
        response.raise_for_status()
        schedule_data = response.json().get('dates', [])
        if not schedule_data:
            return []
        # Filtramos para asegurarnos de que solo procesamos juegos que realmente terminaron
        return [game for game in schedule_data[0].get('games', []) if game['status']['abstractGameState'] == 'Final']
    except requests.exceptions.RequestException as e:
        print(f"Error al obtener el calendario: {e}")
        return []

def process_game_data(game):
    """
    Procesa un solo juego para extraer todas las características y el resultado final.
    """
    try:
        game_date = datetime.strptime(game['gameDate'], '%Y-%m-%dT%H:%M:%SZ')
        game_season = game_date.year

        # Obtenemos los abridores del boxscore, que es la fuente más fiable para juegos pasados
        game_pk = game['gamePk']
        boxscore_url = f"{de.BASE_API_URL}/game/{game_pk}/boxscore"
        boxscore_response = requests.get(boxscore_url, timeout=15)
        boxscore_data = boxscore_response.json()
        
        home_team = game['teams']['home']['team']
        away_team = game['teams']['away']['team']
        
        home_starter_id = boxscore_data['teams']['home']['pitchers'][0]
        away_starter_id = boxscore_data['teams']['away']['pitchers'][0]
        home_pitcher_name = boxscore_data['teams']['home']['players'][f'ID{home_starter_id}']['person']['fullName']
        away_pitcher_name = boxscore_data['teams']['away']['players'][f'ID{away_starter_id}']['person']['fullName']

        print(f"Procesando: {away_team['name']} @ {home_team['name']}...")

        # Recopilamos todas las características usando nuestro motor de enriquecimiento
        home_pitcher_stats = de.get_recent_pitcher_stats(home_starter_id, game_season, game_date)
        home_momentum = de.get_team_momentum(home_team['id'], game_season, game_date)
        
        team_details_response = requests.get(f"{de.BASE_API_URL}/teams/{home_team['id']}")
        venue_name = team_details_response.json()['teams'][0]['venue']['name']
        home_park = de.get_park_factor(venue_name)

        away_pitcher_stats = de.get_recent_pitcher_stats(away_starter_id, game_season, game_date)
        away_momentum = de.get_team_momentum(away_team['id'], game_season, game_date)

        # Construimos el diccionario de características
        features = {
            'game_date': game_date.strftime('%Y-%m-%d'),
            'home_team': home_team['name'],
            'away_team': away_team['name'],
            'home_pitcher': home_pitcher_name,
            'away_pitcher': away_pitcher_name,
            'home_recent_era': home_pitcher_stats.get('recent_era'),
            'home_recent_whip': home_pitcher_stats.get('recent_whip'),
            'home_team_ops': float(home_momentum.get('team_ops', 0) if home_momentum.get('team_ops') else 0),
            'home_bullpen_era': home_momentum.get('bullpen_era'),
            'home_park_factor': home_park.get('park_factor'),
            'away_recent_era': away_pitcher_stats.get('recent_era'),
            'away_recent_whip': away_pitcher_stats.get('recent_whip'),
            'away_team_ops': float(away_momentum.get('team_ops', 0) if away_momentum.get('team_ops') else 0),
            'away_bullpen_era': away_momentum.get('bullpen_era'),
            # La variable objetivo: 1 si gana el local, 0 si gana el visitante
            'home_team_winner': 1 if game['teams']['home']['isWinner'] else 0
        }
        
        return features

    except Exception as e:
        print(f"\n[ERROR] No se pudo procesar el partido {game['gamePk']}: {e}")
        return None

# ===================================================================
# BLOQUE PRINCIPAL DE EJECUCIÓN
# ===================================================================
if __name__ == "__main__":
    # Definimos el año y los meses para construir nuestro dataset
    # La temporada regular de la MLB va de abril (4) a septiembre (9)
    YEAR = 2023
    START_MONTH = 4
    END_MONTH = 9
    
    all_game_features = []
    
    for month in range(START_MONTH, END_MONTH + 1):
        # Obtenemos el número de días del mes
        _, num_days = calendar.monthrange(YEAR, month)
        
        for day in range(1, num_days + 1):
            current_date = datetime(YEAR, month, day)
            games_on_date = get_games_for_date(current_date)
            
            for game in games_on_date:
                game_data = process_game_data(game)
                if game_data:
                    all_game_features.append(game_data)
                # Pausa para no sobrecargar la API
                time.sleep(1.5) 
    
    if all_game_features:
        # Convertimos la lista de diccionarios a un DataFrame de Pandas
        dataset = pd.DataFrame(all_game_features)
        
        # Guardamos el dataset en un archivo CSV
        output_filename = f"mlb_dataset_{YEAR}_season.csv"
        dataset.to_csv(output_filename, index=False)
        
        print("\n" + "="*50)
        print("PROCESO COMPLETADO")
        print(f"Se ha creado el dataset '{output_filename}' con {len(dataset)} partidos.")
        print("="*50)
        print("Primeras 5 filas del dataset:")
        print(dataset.head())
    else:
        print("\nNo se pudieron recopilar datos para el rango de fechas especificado.")
