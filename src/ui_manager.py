# src/ui_manager.py
from datetime import datetime

def prepare_game_data_for_ui(game, unlocked_game_ids):
    game_id = str(game.get('gamePk', 'N/A'))
    
    game_data = {
        'game': game, 
        'game_id': game_id,
        'is_selected_by_user': game_id in unlocked_game_ids,
        'pitchers': {}
    }

    home_team_data = game.get('teams', {}).get('home', {})
    away_team_data = game.get('teams', {}).get('away', {})
    game_detailed_status = game.get('status', {}).get('detailedState', 'Unknown')
    linescore = game.get('linescore', {})
    home_rhe = linescore.get('teams', {}).get('home', {})
    away_rhe = linescore.get('teams', {}).get('away', {})

    game_data.update({
        'home_team_logo': f"https://www.mlbstatic.com/team-logos/{home_team_data.get('team', {}).get('id', '')}.svg",
        'away_team_logo': f"https://www.mlbstatic.com/team-logos/{away_team_data.get('team', {}).get('id', '')}.svg",
        'home_record_wins': home_team_data.get('leagueRecord', {}).get('wins', '?'),
        'home_record_losses': home_team_data.get('leagueRecord', {}).get('losses', '?'),
        'away_record_wins': away_team_data.get('leagueRecord', {}).get('wins', '?'),
        'away_record_losses': away_team_data.get('leagueRecord', {}).get('losses', '?'),
        'home_runs': home_rhe.get('runs'),
        'home_hits': home_rhe.get('hits'),
        'home_errors': home_rhe.get('errors'),
        'away_runs': away_rhe.get('runs'),
        'away_hits': away_rhe.get('hits'),
        'away_errors': away_rhe.get('errors')
    })
    
    game_data['is_final'] = game_detailed_status in ['Final', 'Game Over', 'Completed Early']
    game_data['is_in_progress'] = game_detailed_status in ['In Progress', 'Live']
    game_data['is_pre_game'] = not game_data['is_final'] and not game_data['is_in_progress']

    if game_data['is_in_progress'] and linescore:
        inning_half = "Alta" if linescore.get('isTopInning', True) else "Baja"
        inning_num = linescore.get('currentInningOrdinal', '')
        game_data['display_time_or_inning'] = f"{inning_half} {inning_num}"
    else:
        game_data['display_time_or_inning'] = game.get('game_time', 'TBD')

    for side in ['home', 'away']:
        team_data = game.get('teams', {}).get(side, {})
        if 'probablePitcher' in team_data:
            pitcher = team_data.get('probablePitcher', {})
            game_data['pitchers'][side] = {'fullName': pitcher.get('fullName', 'N/A')}

    return game_data