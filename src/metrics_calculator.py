# src/metrics_calculator.py
import pandas as pd
from .prediction_manager import calculate_accuracy

def calculate_daily_live_metrics(games_for_display, selected_date):
    temp_predictions = []
    for g in games_for_display:
        if g.get('prediction_status') in ['Winner', 'Loser']:
             temp_predictions.append({
                 'fecha_juego': selected_date,
                 'estado_pronostico': g['prediction_status']
             })
    
    if temp_predictions:
        daily_df_live = pd.DataFrame(temp_predictions)
        return calculate_accuracy(daily_df_live)
    else:
        return 0.0, 0, 0