# src/session_manager.py
from flask import session, request
from datetime import datetime

def handle_user_session(prediction_limits):
    selected_date = request.form.get('game_date', datetime.now().strftime('%Y-%m-%d'))
    user_role = request.form.get('user_role', 'Junior')

    if 'revealed_predictions' not in session:
        session['revealed_predictions'] = []

    current_revealed_entry = next((item for item in session['revealed_predictions'] if item['date'] == selected_date and item['role'] == user_role), None)

    if current_revealed_entry is None:
        current_revealed_entry = {'date': selected_date, 'role': user_role, 'game_ids': []}
        session['revealed_predictions'].append(current_revealed_entry)
        session.modified = True

    if request.method == 'POST':
        selected_game_ids_from_post = request.form.getlist('selected_games')
        if selected_game_ids_from_post:
            limit = prediction_limits.get(user_role, 0)
            if 'game_ids' not in current_revealed_entry:
                current_revealed_entry['game_ids'] = []
            newly_revealed_ids = []
            for game_id_to_add in selected_game_ids_from_post:
                if game_id_to_add not in current_revealed_entry['game_ids'] and len(current_revealed_entry['game_ids']) + len(newly_revealed_ids) < limit:
                    newly_revealed_ids.append(game_id_to_add)
            current_revealed_entry['game_ids'].extend(newly_revealed_ids)
            session.modified = True

    unlocked_game_ids = current_revealed_entry.get('game_ids', [])
    user_has_reached_limit = len(unlocked_game_ids) >= prediction_limits.get(user_role, 0) and user_role not in ['Master', 'Administrator']

    return unlocked_game_ids, user_has_reached_limit