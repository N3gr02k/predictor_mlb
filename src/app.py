# src/app.py

from flask import Flask, render_template, request, jsonify, session
from flask_caching import Cache
from datetime import datetime
import joblib
import os
import time

# --- Importaciones de nuestros módulos ---
from .api_client import get_games_for_date
from .prediction_module import make_prediction
from .ui_manager import prepare_game_data_for_ui
from .config import TEAM_NAME_MAP, PREDICTION_LIMITS
from .status_manager import get_prediction_status
from . import database_manager as db_manager
from . import session_manager

# --- Configuración de la App y la Caché ---
app = Flask(__name__, template_folder='templates', static_folder='static')
app.secret_key = os.environ.get('SECRET_KEY', 'super_secreto_local_para_desarrollo') # Usa una variable de entorno en producción
app.config['CACHE_TYPE'] = 'FileSystemCache'
app.config['CACHE_DIR'] = os.path.join(os.path.dirname(__file__), 'cache')
cache = Cache(app)

# --- Inicialización de la Base de Datos ---
db_manager.init_app(app)

# --- Carga de Activos ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, 'ml_model', 'mlb_predictor_model.pkl')
model = joblib.load(MODEL_PATH) if os.path.exists(MODEL_PATH) else None
if model:
    print(f"--- [App] Modelo cargado exitosamente desde: {MODEL_PATH} ---")
else:
    print(f"--- [App] ERROR CRÍTICO: No se encontró el archivo del modelo en '{MODEL_PATH}'. ---")

FEATURE_ORDER = [
    'home_recent_era', 'home_recent_whip', 'home_team_ops', 'home_bullpen_era', 
    'home_park_factor', 'away_recent_era', 'away_recent_whip', 'away_team_ops', 
    'away_bullpen_era'
]

def calculate_daily_live_metrics(games_list):
    evaluated_predictions = sum(1 for g in games_list if g.get('prediction_status') in ['Winner', 'Loser'])
    winners = sum(1 for g in games_list if g.get('prediction_status') == 'Winner')
    accuracy = (winners / evaluated_predictions * 100) if evaluated_predictions > 0 else 0
    return accuracy, winners, evaluated_predictions

@cache.memoize(timeout=3600) # Aumentamos el timeout a 1 hora
def get_predictions_for_date(date_str):
    """
    Esta es la función de trabajo pesado. Solo debe ser llamada por el script de fondo.
    """
    print(f"--- [WORKER] Calculando nuevas predicciones para {date_str} ---")
    partidos = get_games_for_date(date_str)
    games_for_display = []
    if partidos:
        for i, game in enumerate(partidos):
            print(f"  -> Procesando partido {i+1}/{len(partidos)}...")
            try:
                game_data = prepare_game_data_for_ui(game, [])
                prediction_result = make_prediction(game, model, FEATURE_ORDER)
                if prediction_result: game_data.update(prediction_result)
                
                db_manager.save_prediction({
                    'game_id': game.get('gamePk'), 'prediction_date': date_str,
                    'home_team': game.get('teams', {}).get('home', {}).get('team', {}).get('name', 'N/A'),
                    'away_team': game.get('teams', {}).get('away', {}).get('team', {}).get('name', 'N/A'),
                    'prediction': prediction_result
                })
                
                status, outcome = get_prediction_status(game_data, game_data.get('winner', 'N/A'))
                game_data.update({'prediction_status': status, 'actual_outcome': outcome})
                
                if game_data.get('is_final'): db_manager.update_game_result(game_data)
                
                games_for_display.append(game_data)
            except Exception as e:
                print(f"ERROR CRÍTICO procesando el juego {game.get('gamePk', 'N/A')}: {e}")
    return games_for_display

@app.route('/', methods=['GET', 'POST'])
def home():
    start_time = time.time()
    if not model:
        return "Error: El modelo de predicción no se ha cargado. Revisa los logs del servidor.", 500

    user_role = request.form.get('user_role', session.get('user_role', 'Junior'))
    session['user_role'] = user_role

    if request.method == 'POST':
        selected_games = request.form.getlist('selected_games')
        session_manager.update_unlocked_games(selected_games)

    unlocked_game_ids, user_has_reached_limit = session_manager.handle_user_session(PREDICTION_LIMITS)
    
    selected_date = request.form.get('game_date', datetime.now().strftime('%Y-%m-%d'))
    
    # CAMBIO CLAVE: Ya no calculamos. Solo intentamos leer la caché.
    cache_key = f"memoize_get_predictions_for_date_{selected_date}"
    games_for_display = cache.get(cache_key)
    
    if games_for_display is None:
        # Si la caché está vacía, mostramos una lista vacía y un mensaje.
        games_for_display = []
        print(f"--- [App] La caché para {selected_date} está vacía. El worker de fondo debe ejecutarse. ---")

    # Personalizamos la visualización para el usuario actual
    final_games_for_display = []
    for game_data in games_for_display:
        game_id = game_data.get('game_id')
        if user_role in ['Master', 'Administrator'] or game_data.get('is_final') or game_id in unlocked_game_ids:
            game_data['show_prediction'] = True
        else:
            game_data['show_prediction'] = False
        
        game_data['is_selected_by_user'] = game_id in unlocked_game_ids
        final_games_for_display.append(game_data)

    daily_accuracy, daily_winners, daily_evaluated_predictions = calculate_daily_live_metrics(final_games_for_display or [])
    overall_accuracy_global, total_winners_global, total_evaluated_predictions_global = db_manager.calculate_historical_accuracy()

    end_time = time.time()
    print(f"--- [App] Tiempo total de carga de la página: {end_time - start_time:.4f} segundos ---")

    return render_template('index.html', 
                           games=final_games_for_display, 
                           selected_date=selected_date,
                           user_role=user_role, 
                           prediction_limits=PREDICTION_LIMITS,
                           user_has_reached_limit=user_has_reached_limit,
                           daily_accuracy=daily_accuracy, 
                           daily_winners=daily_winners, 
                           daily_evaluated_predictions=daily_evaluated_predictions,
                           overall_accuracy_global=overall_accuracy_global,
                           total_winners_global=total_winners_global, 
                           total_evaluated_predictions_global=total_evaluated_predictions_global)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    app.run(debug=False, host='0.0.0.0', port=port)
