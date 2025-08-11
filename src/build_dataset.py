# src/build_dataset.py

import sys
import os
from datetime import datetime
import pandas as pd
import requests
import time
import calendar

# --- Configuración del Path de Python ---
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

# Ahora podemos importar desde 'src'
from src.prediction_module import get_recent_pitcher_stats, get_team_momentum, PARK_FACTORS
from src.api_client import get_games_for_date
from src.feature_engineering import get_pitcher_splits # <--- NUEVA IMPORTACIÓN

def get_lineup_composition(boxscore_data, team_side):
    """
    Analiza la alineación de un equipo y cuenta los bateadores zurdos, diestros y ambidiestros.
    """
    batters = boxscore_data['teams'][team_side].get('batters', [])
    lefties, righties, switch = 0, 0, 0
    
    for batter_id in batters:
        player_info = boxscore_data['teams'][team_side]['players'].get(f'ID{batter_id}', {})
        bat_side = player_info.get('person', {}).get('batSide', {}).get('code')
        if bat_side == 'L':
            lefties += 1
        elif bat_side == 'R':
            righties += 1
        elif bat_side == 'S':
            switch += 1
            
    return {'lefties': lefties, 'righties': righties, 'switch': switch}

def process_game_data(game):
    """
    Procesa un solo juego para extraer todas las características, incluyendo las nuevas.
    """
    try:
        game_date = datetime.strptime(game['gameDate'], '%Y-%m-%dT%H:%M:%SZ')
        game_season = game_date.year

        game_pk = game['gamePk']
        boxscore_url = f"https://statsapi.mlb.com/api/v1/game/{game_pk}/boxscore"
        boxscore_response = requests.get(boxscore_url, timeout=15)
        boxscore_data = boxscore_response.json()
        
        home_team = game['teams']['home']['team']
        away_team = game['teams']['away']['team']
        
        if not boxscore_data['teams']['home'].get('pitchers') or not boxscore_data['teams']['away'].get('pitchers'):
            return None

        home_starter_id = boxscore_data['teams']['home']['pitchers'][0]
        away_starter_id = boxscore_data['teams']['away']['pitchers'][0]
        home_pitcher_name = boxscore_data['teams']['home']['players'][f'ID{home_starter_id}']['person']['fullName']
        away_pitcher_name = boxscore_data['teams']['away']['players'][f'ID{away_starter_id}']['person']['fullName']

        print(f"Procesando: {away_team['name']} @ {home_team['name']}...")

        # --- RECOPILACIÓN DE CARACTERÍSTICAS ---
        home_pitcher_stats = get_recent_pitcher_stats(home_starter_id, game_season, game_date)
        home_momentum = get_team_momentum(home_team['id'], game_season, game_date)
        venue_name = game.get('venue', {}).get('name')
        home_park_factor = PARK_FACTORS.get(venue_name)

        away_pitcher_stats = get_recent_pitcher_stats(away_starter_id, game_season, game_date)
        away_momentum = get_team_momentum(away_team['id'], game_season, game_date)
        
        # --- NUEVAS CARACTERÍSTICAS DE INGENIERÍA ---
        home_pitcher_splits = get_pitcher_splits(home_starter_id, game_season)
        away_pitcher_splits = get_pitcher_splits(away_starter_id, game_season)
        
        home_lineup = get_lineup_composition(boxscore_data, 'home')
        away_lineup = get_lineup_composition(boxscore_data, 'away')
        # -----------------------------------------

        features = {
            'game_date': game_date.strftime('%Y-%m-%d'),
            'home_team': home_team['name'], 'away_team': away_team['name'],
            'home_pitcher': home_pitcher_name, 'away_pitcher': away_pitcher_name,
            
            # Características existentes
            'home_recent_era': home_pitcher_stats.get('recent_era'),
            'home_recent_whip': home_pitcher_stats.get('recent_whip'),
            'home_team_ops': float(home_momentum.get('team_ops', 0) if home_momentum.get('team_ops') else 0),
            'home_bullpen_era': home_momentum.get('bullpen_era'),
            'home_park_factor': home_park_factor,
            'away_recent_era': away_pitcher_stats.get('recent_era'),
            'away_recent_whip': away_pitcher_stats.get('recent_whip'),
            'away_team_ops': float(away_momentum.get('team_ops', 0) if away_momentum.get('team_ops') else 0),
            'away_bullpen_era': away_momentum.get('bullpen_era'),
            
            # Nuevas características de enfrentamientos
            'home_pitcher_ops_vs_L': home_pitcher_splits.get('vs_left_ops'),
            'home_pitcher_ops_vs_R': home_pitcher_splits.get('vs_right_ops'),
            'away_team_lefty_batters': away_lineup.get('lefties'),
            'away_team_righty_batters': away_lineup.get('righties'),
            
            'away_pitcher_ops_vs_L': away_pitcher_splits.get('vs_left_ops'),
            'away_pitcher_ops_vs_R': away_pitcher_splits.get('vs_right_ops'),
            'home_team_lefty_batters': home_lineup.get('lefties'),
            'home_team_righty_batters': home_lineup.get('righties'),

            'home_team_winner': 1 if game['teams']['home']['isWinner'] else 0
        }
        
        return features

    except Exception as e:
        print(f"\n[ERROR] No se pudo procesar el partido {game.get('gamePk', 'N/A')}: {e}")
        return None

# ===================================================================
# BLOQUE PRINCIPAL DE EJECUCIÓN
# ===================================================================
if __name__ == "__main__":
    YEAR = 2023
    START_MONTH = 4
    END_MONTH = 9
    
    all_game_features = []
    
    for month in range(START_MONTH, END_MONTH + 1):
        _, num_days = calendar.monthrange(YEAR, month)
        for day in range(1, num_days + 1):
            current_date = datetime(YEAR, month, day)
            games_on_date = get_games_for_date(current_date.strftime('%Y-%m-%d'))
            for game in games_on_date:
                game_data = process_game_data(game)
                if game_data:
                    all_game_features.append(game_data)
                time.sleep(1.5) 
    
    if all_game_features:
        dataset = pd.DataFrame(all_game_features)
        output_filename = f"mlb_dataset_{YEAR}_season_v2.csv"
        output_path = os.path.join(project_root, output_filename)
        dataset.to_csv(output_path, index=False)
        
        print("\n" + "="*50)
        print("PROCESO COMPLETADO")
        print(f"Se ha creado el dataset '{output_path}' con {len(dataset)} partidos.")
        print("="*50)
        print("Primeras 5 filas del nuevo dataset:")
        print(dataset.head())
    else:
        print("\nNo se pudieron recopilar datos para el rango de fechas especificado.")
