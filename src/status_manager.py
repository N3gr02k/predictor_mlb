# src/status_manager.py
def get_prediction_status(game_data, predicted_winner):
    if not game_data.get('is_final', False):
        if predicted_winner != 'N/A':
            return "Pendiente", "Pendiente"
        else:
            return "No Pronosticado", "N/A"

    home_score = game_data.get('home_runs')
    away_score = game_data.get('away_runs')

    if not isinstance(home_score, int) or not isinstance(away_score, int):
        return "Evaluación Pendiente", "N/A"

    home_team_name = game_data.get('game', {}).get('teams', {}).get('home', {}).get('team', {}).get('name', '')
    away_team_name = game_data.get('game', {}).get('teams', {}).get('away', {}).get('team', {}).get('name', '')
    actual_winner = home_team_name if home_score > away_score else away_team_name
    
    if predicted_winner == actual_winner:
        return "Winner", actual_winner
    else:
        return "Loser", actual_winner