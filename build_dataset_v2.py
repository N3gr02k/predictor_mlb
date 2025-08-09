# build_dataset_v2.py
import pandas as pd
from datetime import date, timedelta
import time

# Asegúrate de que los módulos de src se puedan importar
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from src.api_client import get_games_for_date

def daterange(start_date, end_date):
    for n in range(int((end_date - start_date).days) + 1):
        yield start_date + timedelta(n)

def build_rich_historical_dataset():
    """
    Construye un dataset histórico enriquecido, incluyendo fechas y nombres de equipos.
    """
    start_date = date(2023, 3, 30)
    end_date = date(2023, 10, 1)
    
    all_game_data = []

    print(f"Iniciando la recolección de datos ENRIQUECIDOS desde {start_date} hasta {end_date}...")

    for single_date in daterange(start_date, end_date):
        date_str = single_date.strftime("%Y-%m-%d")
        print(f"Procesando fecha: {date_str}")
        
        games_on_date = get_games_for_date(date_str)
        
        if not games_on_date:
            continue

        for game in games_on_date:
            game_status = game.get('status', {}).get('abstractGameState', '')
            if game_status!= 'Final':
                continue

            home_team_data = game.get('teams', {}).get('home', {})
            away_team_data = game.get('teams', {}).get('away', {})
            
            features = {
                # --- NUEVAS CARACTERÍSTICAS CLAVE ---
                'game_date': game.get('gameDate'),
                'h_team_name': home_team_data.get('team', {}).get('name', 'N/A'),
                'v_team_name': away_team_data.get('team', {}).get('name', 'N/A'),
                
                # Características originales
                'h_team_wins_season': home_team_data.get('leagueRecord', {}).get('wins', 0),
                'h_team_losses_season': home_team_data.get('leagueRecord', {}).get('losses', 0),
                'v_team_wins_season': away_team_data.get('leagueRecord', {}).get('wins', 0),
                'v_team_losses_season': away_team_data.get('leagueRecord', {}).get('losses', 0),
            }

            is_home_winner = home_team_data.get('isWinner', False)
            features['target'] = 1 if is_home_winner else 0
            
            all_game_data.append(features)
        
        time.sleep(1) 

    print("Recolección de datos completada.")
    
    if all_game_data:
        historical_df = pd.DataFrame(all_game_data)
        
        # Convertir la fecha a un formato de fecha real
        historical_df['game_date'] = pd.to_datetime(historical_df['game_date'])
        
        output_path = 'data/historical_games_rich.csv' # Nuevo nombre de archivo
        historical_df.to_csv(output_path, index=False)
        
        print(f"¡Éxito! El dataset enriquecido ha sido guardado en: {output_path}")
    else:
        print("No se encontraron datos de partidos finalizados.")

if __name__ == '__main__':
    build_rich_historical_dataset()