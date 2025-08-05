# src/game_logic.py
from datetime import datetime
import pandas as pd

def process_game_data(game, mlb_predictions_df, selected_date, model, team_stats_map, team_history_map, TEAM_NAME_MAP, avg_pitcher_stats, PITCHER_STATS_CACHE):
    """
    Procesa un solo juego, extrayendo datos, generando predicciones y determinando estados.
    Devuelve un diccionario 'game_data' completo para la plantilla.
    """
    game_id = str(getattr(game, 'gamePk', 'N/A'))
    print(f"\n--- PROCESANDO JUEGO ID: {game_id} ---")

    # Diccionario base
    game_data = {'game': game, 'game_id': game_id, 'winner': 'N/A', 'confidence': 0.0, 'prediction_status': 'No Pronosticado', 'actual_outcome': 'N/A'}

    # 1. Extracción de datos de la UI
    try:
        home_team_data = getattr(game.teams, 'home', {}); away_team_data = getattr(game.teams, 'away', {})
        h_team_name_full = getattr(home_team_data.team, 'name', ''); v_team_name_full = getattr(away_team_data.team, 'name', '')
        
        game_detailed_status = getattr(game.status, 'detailedState', 'Unknown')
        linescore = getattr(game, 'linescore', None); home_rhe = getattr(getattr(linescore, 'teams', {}), 'home', {}) if linescore else {}; away_rhe = getattr(getattr(linescore, 'teams', {}), 'away', {}) if linescore else {}
        
        game_data.update({
            'home_team_logo': f"https://www.mlbstatic.com/team-logos/{getattr(home_team_data.team, 'id', '')}.svg",
            'away_team_logo': f"https://www.mlbstatic.com/team-logos/{getattr(away_team_data.team, 'id', '')}.svg",
            'home_record_wins': getattr(home_team_data.leagueRecord, 'wins', '?'), 'home_record_losses': getattr(home_team_data.leagueRecord, 'losses', '?'),
            'away_record_wins': getattr(away_team_data.leagueRecord, 'wins', '?'), 'away_record_losses': getattr(away_team_data.leagueRecord, 'losses', '?'),
            'home_runs': getattr(home_rhe, 'runs', '-'), 'home_hits': getattr(home_rhe, 'hits', '-'), 'home_errors': getattr(home_rhe, 'errors', '-'),
            'away_runs': getattr(away_rhe, 'runs', '-'), 'away_hits': getattr(away_rhe, 'hits', '-'), 'away_errors': getattr(away_rhe, 'errors', '-')
        })
        game_data['is_final'] = game_detailed_status in ['Final', 'Game Over', 'Completed Early']
        game_data['is_in_progress'] = game_detailed_status in ['In Progress', 'Live']
        game_data['is_pre_game'] = not game_data['is_final'] and not game_data['is_in_progress']
        
        if game_data['is_in_progress'] and linescore:
            inning_half = "Alta" if getattr(linescore, 'isTopInning', True) else "Baja"
            inning_num = getattr(linescore, 'currentInningOrdinal', '')
            game_data['display_time_or_inning'] = f"{inning_half} {inning_num}"
        else:
            game_data['display_time_or_inning'] = datetime.strptime(getattr(game, 'gameDate'), '%Y-%m-%dT%H:%M:%SZ').strftime('%I:%M %p')
        print("DEBUG: Datos de UI extraídos correctamente.")
    except Exception as e:
        print(f"ERROR en extracción de datos de UI: {e}")

    # 2. Lógica de Predicción
    try:
        h_team_abbr = TEAM_NAME_MAP.get(h_team_name_full); v_team_abbr = TEAM_NAME_MAP.get(v_team_name_full)
        if h_team_abbr and v_team_abbr and model:
            # (Lógica completa de creación de features y predicción)
            # ...
            winner = "Equipo Ejemplo"
            confidence = 65.0
            game_data.update({'winner': winner, 'confidence': confidence})
            print("DEBUG: Predicción del modelo generada.")
    except Exception as e:
        print(f"ERROR en el bloque de predicción: {e}")

    # 3. Lógica de Estado del Pronóstico
    try:
        if h_team_name_full:
            matching_records = mlb_predictions_df[(mlb_predictions_df['fecha_juego'] == selected_date) & (mlb_predictions_df['equipo_local'] == h_team_name_full)]
            if not matching_records.empty:
                record = matching_records.iloc[0]
                game_data['prediction_status'] = record['estado_pronostico']
                game_data['actual_outcome'] = record['resultado_real']
            elif game_data['is_final']:
                game_data['prediction_status'] = "Evaluación Pendiente"
            elif game_data['winner'] != 'N/A':
                game_data['prediction_status'] = 'Pendiente'
        print(f"DEBUG: Estado del pronóstico determinado: {game_data['prediction_status']}")
    except Exception as e:
        print(f"ERROR en la lógica de estado: {e}")

    return game_data