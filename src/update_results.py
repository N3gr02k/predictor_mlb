# src/update_results.py (Corregido para manejar objetos)
import pandas as pd
from datetime import datetime, timedelta
from data_source import get_games_for_date
from src.prediction1anager import PREDICTIONS_FILE

def update_daily_results():
    """
    Actualiza los resultados de las predicciones del día anterior que están pendientes.
    """
    print("--- Iniciando script de actualización de resultados ---")
    
    # 1. Cargar el archivo de predicciones
    try:
        predictions_df = pd.read_csv(PREDICTIONS_FILE)
        print(f"Archivo '{PREDICTIONS_FILE}' cargado exitosamente.")
    except (FileNotFoundError, pd.errors.EmptyDataError):
        print(f"No se encontró o está vacío el archivo '{PREDICTIONS_FILE}'. No hay nada que actualizar.")
        return

    # 2. Determinar la fecha de ayer
    yesterday = datetime.now() - timedelta(days=1)
    date_to_check = yesterday.strftime('%Y-%m-%d')
    print(f"Verificando resultados para la fecha: {date_to_check}")

    # 3. Filtrar las predicciones pendientes de ayer
    pending_games = predictions_df[
        (predictions_df['fecha_juego'] == date_to_check) &
        (predictions_df['estado_pronostico'] == 'Pendiente')
    ]

    if pending_games.empty:
        print("No hay predicciones pendientes para la fecha especificada.")
        print("--- Script finalizado ---")
        return

    # 4. Obtener los resultados reales de la API
    actual_games = get_games_for_date(date_to_check)
    if not actual_games:
        print("No se pudieron obtener los resultados de los juegos desde la API.")
        print("--- Script finalizado ---")
        return
        
    # Crear un mapa de resultados para búsqueda rápida
    results_map = {
        # CORRECCIÓN: Se accede a los datos como atributos de un objeto
        (game.teams.home.team.name, game.teams.away.team.name): game
        for game in actual_games
    }

    # 5. Comparar y actualizar
    for index, prediction in pending_games.iterrows():
        home_team = prediction['equipo_local']
        away_team = prediction['equipo_visitante']
        predicted_winner = prediction['pronostico_ganador']
        
        game_result = results_map.get((home_team, away_team))
        
        # CORRECCIÓN: Se accede a los datos como atributos de un objeto
        if game_result and getattr(game_result.status, 'detailedState', '') == 'Final':
            home_score = getattr(game_result.teams.home, 'score', 0)
            away_score = getattr(game_result.teams.away, 'score', 0)
            
            actual_winner = home_team if home_score > away_score else away_team
            
            # Actualizamos el DataFrame
            predictions_df.loc[index, 'resultado_real'] = actual_winner
            if predicted_winner == actual_winner:
                predictions_df.loc[index, 'estado_pronostico'] = 'Winner'
                print(f"¡Acierto! {predicted_winner} ganaron. Estado actualizado a 'Winner'.")
            else:
                predictions_df.loc[index, 'estado_pronostico'] = 'Loser'
                print(f"Fallo. {predicted_winner} perdieron. Estado actualizado a 'Loser'.")
        else:
            print(f"No se encontró resultado final para {away_team} vs {home_team}.")

    # 6. Guardar el archivo actualizado
    predictions_df.to_csv(PREDICTIONS_FILE, index=False)
    print(f"Archivo '{PREDICTIONS_FILE}' actualizado y guardado.")
    print("--- Script finalizado ---")

if __name__ == '__main__':
    update_daily_results()