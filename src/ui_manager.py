# src/ui_manager.py

from datetime import datetime, timezone

def prepare_game_data_for_ui(game, unlocked_game_ids):
    """
    Toma los datos crudos de un partido de la API y los transforma
    en un formato listo para ser usado por la plantilla HTML (index.html).
    """
    home_team = game.get('teams', {}).get('home', {})
    away_team = game.get('teams', {}).get('away', {})
    
    game_status = game.get('status', {}).get('abstractGameState', 'Preview')
    is_final = game_status == 'Final'
    is_in_progress = game_status == 'Live'
    
    # --- CAMBIO CLAVE: Lógica para extraer el marcador ---
    linescore = game.get('linescore', {})
    home_runs = linescore.get('teams', {}).get('home', {}).get('runs', '-')
    away_runs = linescore.get('teams', {}).get('away', {}).get('runs', '-')
    home_hits = linescore.get('teams', {}).get('home', {}).get('hits', '-')
    away_hits = linescore.get('teams', {}).get('away', {}).get('hits', '-')
    home_errors = linescore.get('teams', {}).get('home', {}).get('errors', '-')
    away_errors = linescore.get('teams', {}).get('away', {}).get('errors', '-')
    
    # Para juegos que no han comenzado, nos aseguramos de que aparezcan guiones
    if not is_final and not is_in_progress:
        home_runs, away_runs, home_hits, away_hits, home_errors, away_errors = '-', '-', '-', '-', '-', '-'
    # --- FIN DEL CAMBIO ---

    game_data = {
        'game_id': game.get('gamePk'),
        'game': game,
        'is_final': is_final,
        'is_in_progress': is_in_progress,
        'is_pre_game': not is_final and not is_in_progress,
        
        'display_time_or_inning': linescore.get('currentInningOrdinal', game.get('game_time', '')) if is_in_progress else game.get('game_time', ''),
        
        'home_team_logo': f"https://www.mlbstatic.com/team-logos/{home_team.get('team', {}).get('id')}.svg",
        'away_team_logo': f"https://www.mlbstatic.com/team-logos/{away_team.get('team', {}).get('id')}.svg",
        
        'home_record_wins': home_team.get('leagueRecord', {}).get('wins', 0),
        'home_record_losses': home_team.get('leagueRecord', {}).get('losses', 0),
        'away_record_wins': away_team.get('leagueRecord', {}).get('wins', 0),
        'away_record_losses': away_team.get('leagueRecord', {}).get('losses', 0),
        
        # Añadimos los datos del marcador
        'home_runs': home_runs,
        'away_runs': away_runs,
        'home_hits': home_hits,
        'away_hits': away_hits,
        'home_errors': home_errors,
        'away_errors': away_errors,
        
        'pitchers': {
            'home': game.get('teams', {}).get('home', {}).get('probablePitcher'),
            'away': game.get('teams', {}).get('away', {}).get('probablePitcher')
        },
        
        'is_selected_by_user': game.get('gamePk') in unlocked_game_ids
    }
    
    return game_data
