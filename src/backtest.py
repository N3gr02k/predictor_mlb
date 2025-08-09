# src/backtest.py

import data_enrichment as de
from datetime import datetime, timedelta
import pandas as pd
import requests 
import joblib
import os
import time
from config import TEAM_NAME_MAP

def load_model(model_path):
    """
    Carga el modelo de predicción desde el archivo .pkl.
    """
    if not os.path.exists(model_path):
        print(f"\n[ERROR] No se encontró el archivo del modelo en '{model_path}'.")
        print("Por favor, ejecuta primero 'src/train_model.py' para crearlo.")
        return None
    print(f"--- Cargando modelo desde: {model_path} ---")
    return joblib.load(model_path)

def get_games_for_date(date):
    """
    Obtiene la lista de partidos programados para una fecha específica.
    """
    print(f"\n--- Obteniendo partidos para la fecha: {date.strftime('%Y-%m-%d')} ---")
    schedule_url = f"{de.BASE_API_URL}/schedule"
    schedule_params = {'sportId': 1, 'date': date.strftime('%Y-%m-%d')}
    try:
        response = requests.get(schedule_url, params=schedule_params)
        response.raise_for_status()
        schedule_data = response.json().get('dates', [])
        if not schedule_data:
            return []
        return [game for game in schedule_data[0].get('games', []) if game['status']['abstractGameState'] == 'Final']
    except requests.exceptions.RequestException as e:
        print(f"Error al obtener el calendario: {e}")
        return []

def get_starting_pitchers(game):
    """
    Obtiene los lanzadores abridores de un juego desde el boxscore.
    """
    try:
        game_pk = game['gamePk']
        boxscore_url = f"{de.BASE_API_URL}/game/{game_pk}/boxscore"
        boxscore_response = requests.get(boxscore_url)
        boxscore_data = boxscore_response.json()
        
        home_starter_id = boxscore_data['teams']['home']['pitchers'][0]
        away_starter_id = boxscore_data['teams']['away']['pitchers'][0]
        
        return {
            'home_pitcher_id': home_starter_id,
            'away_pitcher_id': away_starter_id,
        }
    except (KeyError, IndexError, requests.exceptions.RequestException) as e:
        print(f"No se pudo obtener el abridor del boxscore para el juego {game['gamePk']}: {e}")
        return {}

def run_backtest(model, feature_order, start_date, end_date):
    """
    Ejecuta el backtesting del modelo en un rango de fechas.
    """
    all_results = []
    current_date = start_date
    
    while current_date <= end_date:
        games_on_date = get_games_for_date(current_date)
        
        for game in games_on_date:
            home_team = game['teams']['home']['team']
            away_team = game['teams']['away']['team']
            
            pitchers = get_starting_pitchers(game)
            if not pitchers:
                continue

            try:
                game_date = datetime.strptime(game['gameDate'], '%Y-%m-%dT%H:%M:%SZ')
                game_season = game_date.year

                # Recopilar características
                home_pitcher_stats = de.get_recent_pitcher_stats(pitchers['home_pitcher_id'], game_season, game_date - timedelta(days=30), game_date)
                home_momentum = de.get_team_momentum(home_team['id'], game_season, game_date - timedelta(days=14), game_date)
                
                team_details_response = requests.get(f"{de.BASE_API_URL}/teams/{home_team['id']}")
                venue_name = team_details_response.json()['teams'][0]['venue']['name']
                home_park = de.get_park_factor(venue_name)

                away_pitcher_stats = de.get_recent_pitcher_stats(pitchers['away_pitcher_id'], game_season, game_date - timedelta(days=30), game_date)
                away_momentum = de.get_team_momentum(away_team['id'], game_season, game_date - timedelta(days=14), game_date)

                features = {
                    'home_recent_era': home_pitcher_stats.get('recent_era'),
                    'home_recent_whip': home_pitcher_stats.get('recent_whip'),
                    'home_team_ops': float(home_momentum.get('team_ops', 0) if home_momentum.get('team_ops') else 0),
                    'home_bullpen_era': home_momentum.get('bullpen_era'),
                    'home_park_factor': home_park.get('park_factor'),
                    'away_recent_era': away_pitcher_stats.get('recent_era'),
                    'away_recent_whip': away_pitcher_stats.get('recent_whip'),
                    'away_team_ops': float(away_momentum.get('team_ops', 0) if away_momentum.get('team_ops') else 0),
                    'away_bullpen_era': away_momentum.get('bullpen_era'),
                }

                # Preparar datos para la predicción
                prediction_df = pd.DataFrame([features])[feature_order]
                prediction_df.fillna(0, inplace=True) # Rellenar nulos

                # Hacer predicción
                prediction = model.predict(prediction_df)[0]
                
                # Almacenar resultado
                result = {
                    'date': game_date.strftime('%Y-%m-%d'),
                    'home_team': home_team['name'],
                    'away_team': away_team['name'],
                    'prediction': 'home' if prediction == 1 else 'away',
                    'actual_winner': 'home' if game['teams']['home']['isWinner'] else 'away'
                }
                result['correct_prediction'] = 1 if result['prediction'] == result['actual_winner'] else 0
                all_results.append(result)
                
                print(f"  - Predicción para {away_team['name']} @ {home_team['name']}: {'Correcta' if result['correct_prediction'] else 'Incorrecta'}")

            except Exception as e:
                print(f"  - [ERROR] Saltando partido {game['gamePk']}: {e}")
            
            time.sleep(1) # Pausa para no sobrecargar la API

        current_date += timedelta(days=1)
        
    return pd.DataFrame(all_results)

# ===================================================================
# BLOQUE PRINCIPAL DE EJECUCIÓN
# ===================================================================
if __name__ == "__main__":
    MODEL_PATH = 'src/ml_model/mlb_predictor_model.pkl'
    ml_model = load_model(MODEL_PATH)

    if ml_model:
        FEATURE_ORDER = [
            'home_recent_era', 'home_recent_whip', 'home_team_ops', 'home_bullpen_era', 
            'home_park_factor', 'away_recent_era', 'away_recent_whip', 'away_team_ops', 
            'away_bullpen_era'
        ]

        # Definimos el rango de fechas para el backtesting
        backtest_start_date = datetime(2024, 6, 1)
        backtest_end_date = datetime(2024, 6, 30)
        
        print("\n" + "="*50)
        print("INICIANDO BACKTESTING")
        print(f"Periodo: {backtest_start_date.strftime('%Y-%m-%d')} a {backtest_end_date.strftime('%Y-%m-%d')}")
        print("="*50)

        results_df = run_backtest(ml_model, FEATURE_ORDER, backtest_start_date, backtest_end_date)
        
        if not results_df.empty:
            accuracy = results_df['correct_prediction'].mean()
            
            print("\n" + "="*50)
            print("RESULTADOS DEL BACKTESTING")
            print("="*50)
            print(f"Total de partidos predichos: {len(results_df)}")
            print(f"Total de aciertos: {results_df['correct_prediction'].sum()}")
            print(f"PRECISIÓN TOTAL: {accuracy:.2%}")
            
            output_filename = 'backtest_results.csv'
            results_df.to_csv(output_filename, index=False)
            print(f"\nResultados detallados guardados en '{output_filename}'")
        else:
            print("\nNo se pudieron generar resultados para el periodo de backtesting.")
