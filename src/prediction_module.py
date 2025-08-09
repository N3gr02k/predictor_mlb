# src/prediction_module.py

import requests
from datetime import datetime, timedelta
import pandas as pd
from unidecode import unidecode
from .config import TEAM_NAME_MAP

# --- CONSTANTES Y CONFIGURACIÓN ---
BASE_API_URL = "https://statsapi.mlb.com/api/v1"

PARK_FACTORS = {
    "Angel Stadium": 1.019, "Coors Field": 1.359, "Comerica Park": 0.932,
    "Fenway Park": 1.103, "Great American Ball Park": 1.251, "Guaranteed Rate Field": 1.118,
    "Kauffman Stadium": 1.082, "Minute Maid Park": 0.951, "Nationals Park": 1.033,
    "Oracle Park": 0.849, "Oriole Park at Camden Yards": 0.999, "PNC Park": 0.953,
    "Petco Park": 0.879, "Progressive Field": 0.951, "Rogers Centre": 1.052,
    "T-Mobile Park": 0.842, "Target Field": 1.001, "Tropicana Field": 0.918,
    "Truist Park": 1.042, "Wrigley Field": 1.049, "Yankee Stadium": 1.087,
    "American Family Field": 0.998, "Busch Stadium": 0.916, "Chase Field": 1.036,
    "Citi Field": 0.871, "Citizens Bank Park": 1.059, "Dodger Stadium": 0.937,
    "loanDepot park": 0.887, "Globe Life Field": 0.887, "Oakland Coliseum": 0.855,
    "Daikin Park": 0.951
}

def get_recent_pitcher_stats(player_id, season, game_date):
    """Calcula el ERA y WHIP de un lanzador en los 30 días previos al juego."""
    start_date = game_date - timedelta(days=30)
    gamelog_url = f"{BASE_API_URL}/people/{player_id}/stats"
    gamelog_params = {'stats': 'gameLog', 'group': 'pitching', 'season': season}
    response = requests.get(gamelog_url, params=gamelog_params)
    response.raise_for_status()
    game_logs = response.json().get('stats', [{}])[0].get('splits', [])
    
    if not game_logs: return {'recent_era': None, 'recent_whip': None}

    game_logs_df = pd.DataFrame([log['stat'] for log in game_logs])
    game_logs_df['game_date_dt'] = pd.to_datetime([log['date'] for log in game_logs])
    
    recent_games = game_logs_df[(game_logs_df['game_date_dt'] >= start_date) & (game_logs_df['game_date_dt'] < game_date)]
    if recent_games.empty: return {'recent_era': None, 'recent_whip': None}

    total_ip = pd.to_numeric(recent_games['inningsPitched'], errors='coerce').sum()
    total_er = pd.to_numeric(recent_games['earnedRuns'], errors='coerce').sum()
    total_hits = pd.to_numeric(recent_games['hits'], errors='coerce').sum()
    total_walks = pd.to_numeric(recent_games['baseOnBalls'], errors='coerce').sum()
    
    if total_ip > 0:
        return {
            'recent_era': round((total_er * 9) / total_ip, 2),
            'recent_whip': round((total_walks + total_hits) / total_ip, 2)
        }
    return {'recent_era': None, 'recent_whip': None}

def get_team_momentum(team_id, season, game_date):
    """Calcula el momentum de un equipo en los 14 días previos al juego."""
    end_date = game_date - timedelta(days=1)
    start_date = end_date - timedelta(days=14)
    start_str, end_str = start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')
    
    momentum_params = {'season': season, 'startDate': start_str, 'endDate': end_str}
    
    offensive_params = {**momentum_params, 'stats': 'byDateRange', 'group': 'hitting'}
    offensive_response = requests.get(f"{BASE_API_URL}/teams/{team_id}/stats", params=offensive_params)
    offensive_stats = offensive_response.json().get('stats', [{}])[0].get('splits', [{}])[0].get('stat', {})
    
    pitching_params = {**momentum_params, 'stats': 'byDateRange', 'group': 'pitching'}
    pitching_response = requests.get(f"{BASE_API_URL}/teams/{team_id}/stats", params=pitching_params)
    pitching_stats = pitching_response.json().get('stats', [{}])[0].get('splits', [{}])[0].get('stat', {})

    schedule_url = f"{BASE_API_URL}/schedule"
    schedule_params = {'sportId': 1, 'teamId': team_id, 'startDate': start_str, 'endDate': end_str}
    schedule_response = requests.get(schedule_url, params=schedule_params)
    games = schedule_response.json().get('dates', [])
    
    total_bullpen_ip_outs, total_bullpen_er, total_bullpen_hits, total_bullpen_walks = 0, 0, 0, 0
    for date_info in games:
        for game in date_info.get('games', []):
            boxscore_response = requests.get(f"{BASE_API_URL}/game/{game['gamePk']}/boxscore")
            boxscore_data = boxscore_response.json()
            team_side = 'home' if boxscore_data['teams']['home']['team']['id'] == team_id else 'away'
            pitchers = boxscore_data['teams'][team_side].get('pitchers', [])
            for pitcher_id in pitchers[1:]:
                p_stats = boxscore_data['teams'][team_side]['players'].get(f'ID{pitcher_id}', {}).get('stats', {}).get('pitching', {})
                if p_stats:
                    ip_str = p_stats.get('inningsPitched', "0.0")
                    parts = ip_str.split('.')
                    total_bullpen_ip_outs += (int(parts[0]) * 3) + (int(parts[1]) if len(parts) > 1 else 0)
                    total_bullpen_er += p_stats.get('earnedRuns', 0)
                    total_bullpen_hits += p_stats.get('hits', 0)
                    total_bullpen_walks += p_stats.get('baseOnBalls', 0)

    bullpen_era, bullpen_whip = None, None
    if total_bullpen_ip_outs > 0:
        total_bullpen_ip = total_bullpen_ip_outs / 3.0
        bullpen_era = round((total_bullpen_er * 9) / total_bullpen_ip, 2)
        bullpen_whip = round((total_bullpen_walks + total_bullpen_hits) / total_bullpen_ip, 2)

    return {
        'runs_scored': offensive_stats.get('runs'),
        'team_ops': offensive_stats.get('ops'),
        'runs_allowed': pitching_stats.get('runs'),
        'bullpen_era': bullpen_era,
        'bullpen_whip': bullpen_whip
    }

def make_prediction(game_data, model, feature_order):
    """
    Orquesta la recolección de datos y hace una predicción para un solo juego.
    """
    try:
        home_team = game_data['teams']['home']['team']
        away_team = game_data['teams']['away']['team']
        game_date = datetime.strptime(game_data['gameDate'], '%Y-%m-%dT%H:%M:%SZ')
        game_season = game_date.year

        home_pitcher = game_data['teams']['home'].get('probablePitcher')
        away_pitcher = game_data['teams']['away'].get('probablePitcher')

        if not home_pitcher or not away_pitcher:
            return {'winner': 'N/A', 'confidence': 0, 'error': 'Lanzadores no anunciados'}

        # Recopilar características
        home_pitcher_stats = get_recent_pitcher_stats(home_pitcher['id'], game_season, game_date)
        home_momentum = get_team_momentum(home_team['id'], game_season, game_date)
        home_park_factor = PARK_FACTORS.get(game_data.get('venue', {}).get('name'))

        away_pitcher_stats = get_recent_pitcher_stats(away_pitcher['id'], game_season, game_date)
        away_momentum = get_team_momentum(away_team['id'], game_season, game_date)

        features = {
            'home_recent_era': home_pitcher_stats.get('recent_era'),
            'home_recent_whip': home_pitcher_stats.get('recent_whip'),
            'home_team_ops': float(home_momentum.get('team_ops', 0) if home_momentum.get('team_ops') else 0),
            'home_bullpen_era': home_momentum.get('bullpen_era'),
            'home_park_factor': home_park_factor,
            'away_recent_era': away_pitcher_stats.get('recent_era'),
            'away_recent_whip': away_pitcher_stats.get('recent_whip'),
            'away_team_ops': float(away_momentum.get('team_ops', 0) if away_momentum.get('team_ops') else 0),
            'away_bullpen_era': away_momentum.get('bullpen_era'),
        }

        # Preparar datos y predecir
        prediction_df = pd.DataFrame([features])[feature_order]
        
        # CORRECCIÓN: Convertimos explícitamente a tipos numéricos antes de rellenar.
        # Esto elimina el FutureWarning y es una práctica más robusta.
        for col in prediction_df.columns:
            prediction_df[col] = pd.to_numeric(prediction_df[col], errors='coerce')
        
        prediction_df = prediction_df.fillna(0)

        prediction = model.predict(prediction_df)
        prediction_proba = model.predict_proba(prediction_df)

        winner_index = prediction[0]
        winner_name = home_team['name'] if winner_index == 1 else away_team['name']
        confidence = prediction_proba[0][winner_index]

        return {'winner': TEAM_NAME_MAP.get(winner_name, winner_name), 'confidence': confidence}

    except Exception as e:
        print(f"[ERROR en make_prediction para juego {game_data.get('gamePk')}]: {e}")
        return {'winner': 'Error', 'confidence': 0, 'error': str(e)}
