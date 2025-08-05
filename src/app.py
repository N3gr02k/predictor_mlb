# src/app.py
from flask import Flask, render_template, request
from datetime import datetime
import pandas as pd

from .api_client import get_games_for_date
from .prediction_manager import inicializar_dataframe_pronosticos, calculate_accuracy
from .asset_loader import load_all_assets
from .config import PREDICTION_LIMITS
from .session_manager import handle_user_session
from .metrics_calculator import calculate_daily_live_metrics
from .game_processor import process_game

app = Flask(__name__, template_folder='templates')
app.secret_key = 'super_secreto_y_seguro_mlb_predictor'

assets = load_all_assets()

@app.route('/', methods=['GET', 'POST'])
def home():
    unlocked_game_ids, user_has_reached_limit = handle_user_session(PREDICTION_LIMITS)
    selected_date = request.form.get('game_date', datetime.now().strftime('%Y-%m-%d'))
    user_role = request.form.get('user_role', 'Junior')
    
    partidos = get_games_for_date(selected_date)
    mlb_predictions_df = inicializar_dataframe_pronosticos()
    overall_accuracy, total_winners_global, total_evaluated_predictions_global = calculate_accuracy(mlb_predictions_df)
    
    games_for_display = [
        process_game(game, unlocked_game_ids, mlb_predictions_df, selected_date, user_role, assets) 
        for game in partidos
    ]
    
    daily_accuracy, daily_winners, daily_evaluated_predictions = calculate_daily_live_metrics(games_for_display, selected_date)

    return render_template('index.html', games=games_for_display, selected_date=selected_date, user_role=user_role,
                           prediction_limits=PREDICTION_LIMITS, user_has_reached_limit=user_has_reached_limit,
                           overall_accuracy_global=overall_accuracy, daily_accuracy=daily_accuracy,
                           daily_winners=daily_winners, total_winners_global=total_winners_global,
                           daily_evaluated_predictions=daily_evaluated_predictions, total_evaluated_predictions_global=total_evaluated_predictions_global)