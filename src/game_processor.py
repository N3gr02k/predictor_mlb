# src/game_processor.py
from .ui_manager import prepare_game_data_for_ui
from .prediction_module import make_prediction
from .status_manager import get_prediction_status
from .config import TEAM_NAME_MAP

def process_game(game, unlocked_game_ids, mlb_predictions_df, selected_date, user_role, assets):
    try:
        model = assets["model"]
        team_stats_map = assets["team_stats_map"]
        team_history_map = assets["team_history_map"]
        avg_pitcher_stats = assets["avg_pitcher_stats"]

        # 1. Módulo de UI prepara los datos visuales
        game_data = prepare_game_data_for_ui(game, unlocked_game_ids)
        
        # 2. Módulo de Predicción genera el pronóstico
        home_team_data = game.get('teams', {}).get('home', {})
        away_team_data = game.get('teams', {}).get('away', {})
        h_team_name = home_team_data.get('team', {}).get('name', '')
        v_team_name = away_team_data.get('team', {}).get('name', '')
        
        prediction_result = make_prediction(h_team_name, v_team_name, model, team_stats_map, team_history_map, avg_pitcher_stats, home_team_data, away_team_data, TEAM_NAME_MAP)
        if prediction_result:
            game_data.update(prediction_result)

        # 3. Módulo de Estado determina el estado del pronóstico
        status, outcome = get_prediction_status(game_data, game_data.get('winner', 'N/A'))
        game_data['prediction_status'] = status
        game_data['actual_outcome'] = outcome
        
        # 4. Lógica de visualización final
        if user_role in ['Master', 'Administrator'] or game_data.get('is_final') or game_data.get('game_id') in unlocked_game_ids:
            game_data['show_prediction'] = True
        
        return game_data

    except Exception as e:
        print(f"ERROR CRÍTICO procesando el juego {game.get('gamePk', 'N/A')}: {e}")
        return {'game': game, 'error': True, 'game_id': game.get('gamePk', 'N/A')}