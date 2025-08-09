# src/session_manager.py

from flask import session
from datetime import datetime

def handle_user_session(prediction_limits):
    """
    Gestiona la sesión del usuario para controlar los límites de predicción diarios.
    """
    today_str = datetime.now().strftime('%Y-%m-%d')
    
    # Si es un nuevo día, reiniciamos el contador de predicciones del usuario.
    if session.get('date') != today_str:
        session['date'] = today_str
        session['unlocked_games'] = [] # Lista de IDs de juegos vistos
    
    # Asegurarnos de que la lista exista en la sesión
    if 'unlocked_games' not in session:
        session['unlocked_games'] = []

    user_role = session.get('user_role', 'Junior') # Por defecto, el rol es Junior
    limit = prediction_limits.get(user_role, 2)
    
    unlocked_count = len(session['unlocked_games'])
    has_reached_limit = unlocked_count >= limit
    
    print(f"--- [Session] Rol: {user_role}, Límite: {limit}, Vistos: {unlocked_count}, Límite alcanzado: {has_reached_limit} ---")
    
    return session['unlocked_games'], has_reached_limit

def update_unlocked_games(selected_games):
    """
    Añade los nuevos juegos seleccionados por el usuario a su sesión.
    """
    if 'unlocked_games' not in session:
        session['unlocked_games'] = []
    
    # Usamos un set para evitar duplicados y luego lo convertimos de nuevo a lista
    unlocked_set = set(session['unlocked_games'])
    for game_id in selected_games:
        unlocked_set.add(int(game_id))
    
    session['unlocked_games'] = list(unlocked_set)
    session.modified = True # Importante para que Flask guarde los cambios en la sesión
