# src/status_manager.py

from .config import TEAM_NAME_MAP

def get_prediction_status(game_data, predicted_winner_abbr):
    """
    Determina el estado de una predicción (Winner, Loser, Pendiente)
    comparando el pronóstico con el resultado real del partido.
    """
    is_final = game_data.get('is_final', False)
    
    if not is_final:
        return 'Pendiente', 'Pendiente'

    home_team_name = game_data.get('game', {}).get('teams', {}).get('home', {}).get('team', {}).get('name', 'N/A')
    away_team_name = game_data.get('game', {}).get('teams', {}).get('away', {}).get('team', {}).get('name', 'N/A')
    
    home_score = game_data.get('home_runs', -1)
    away_score = game_data.get('away_runs', -1)

    if home_score == -1 or away_score == -1:
        return 'Datos incompletos', 'N/A'

    actual_winner_name = home_team_name if home_score > away_score else away_team_name
    actual_winner_abbr = TEAM_NAME_MAP.get(actual_winner_name, actual_winner_name)

    if predicted_winner_abbr == actual_winner_abbr:
        status = 'Winner'
    else:
        status = 'Loser'
        
    return status, actual_winner_abbr
