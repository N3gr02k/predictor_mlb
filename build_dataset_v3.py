# build_dataset_v3.py
import pandas as pd
from datetime import date, timedelta
import time
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
from src.api_client import get_games_for_date

def daterange(start_date, end_date):
    for n in range(int((end_date - start_date).days) + 1):
        yield start_date + timedelta(n)

def build_expert_dataset():
    start_date = date(2023, 3, 30)
    end_date = date(2023, 10, 1)
    all_game_data = []
    print(f"Iniciando la recolección de datos de NIVEL EXPERTO desde {start_date} hasta {end_date}...")

    for single_date in daterange(start_date, end_date):
        date_str = single_date.strftime("%Y-%m-%d")
        print(f"Procesando fecha: {date_str}")
        games_on_date = get_games_for_date(date_str)
        if not games_on_date: continue

        for game in games_on_date:
            if game.get('status', {}).get('abstractGameState', '')!= 'Final': continue
            
            home_team_data = game.get('teams', {}).get('home', {})
            away_team_data = game.get('teams', {}).get('away', {})
            
            # Extraer stats de lanzadores (si están disponibles)
            h_pitcher = home_team_data.get('probablePitcher', {})
            v_pitcher = away_team_data.get('probablePitcher', {})
            
            features = {
                'game_date': game.get('gameDate'),
                'h_team_name': home_team_data.get('team', {}).get('name', 'N/A'),
                'v_team_name': away_team_data.get('team', {}).get('name', 'N/A'),
                'h_team_wins_season': home_team_data.get('leagueRecord', {}).get('wins', 0),
                'h_team_losses_season': home_team_data.get('leagueRecord', {}).get('losses', 0),
                'v_team_wins_season': away_team_data.get('leagueRecord', {}).get('wins', 0),
                'v_team_losses_season': away_team_data.get('leagueRecord', {}).get('losses', 0),
                
                # --- NUEVAS CARACTERÍSTICAS DE LANZADOR ---
                'h_pitcher_wins': h_pitcher.get('stats', [{}]).get('stats', {}).get('wins', 0) if h_pitcher.get('stats') else 0,
                'h_pitcher_losses': h_pitcher.get('stats', [{}]).get('stats', {}).get('losses', 0) if h_pitcher.get('stats') else 0,
                'h_pitcher_era': h_pitcher.get('stats', [{}]).get('stats', {}).get('era', '99.00') if h_pitcher.get('stats') else '99.00',
                'v_pitcher_wins': v_pitcher.get('stats', [{}]).get('stats', {}).get('wins', 0) if v_pitcher.get('stats') else 0,
                'v_pitcher_losses': v_pitcher.get('stats', [{}]).get('stats', {}).get('losses', 0) if v_pitcher.get('stats') else 0,
                'v_pitcher_era': v_pitcher.get('stats', [{}]).get('stats', {}).get('era', '99.00') if v_pitcher.get('stats') else '99.00',
            }
            features['target'] = 1 if home_team_data.get('isWinner', False) else 0
            all_game_data.append(features)
        time.sleep(1)

    print("Recolección de datos completada.")
    if all_game_data:
        df = pd.DataFrame(all_game_data)
        df['game_date'] = pd.to_datetime(df['game_date'])
        # Convertir ERA a numérico, manejando posibles errores
        df['h_pitcher_era'] = pd.to_numeric(df['h_pitcher_era'], errors='coerce').fillna(99.0)
        df['v_pitcher_era'] = pd.to_numeric(df['v_pitcher_era'], errors='coerce').fillna(99.0)
        
        output_path = 'data/historical_games_expert.csv'
        df.to_csv(output_path, index=False)
        print(f"¡Éxito! El dataset experto ha sido guardado en: {output_path}")

if __name__ == '__main__':
    build_expert_dataset()