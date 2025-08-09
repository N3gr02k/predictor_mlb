# build_dataset.py (VERSIÓN FINAL, AHORA SÍ, CORREGIDA)
import pandas as pd
from datetime import date, timedelta
import time

# Asegúrate de que los módulos de src se puedan importar
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Importa las funciones que ya tienes
from src.api_client import get_games_for_date

def daterange(start_date, end_date):
    """Generador para iterar sobre un rango de fechas."""
    for n in range(int((end_date - start_date).days) + 1):
        yield start_date + timedelta(n)

def build_historical_dataset():
    """
    Construye el archivo CSV histórico que necesitamos para entrenar y evaluar el modelo.
    """
    # Define el rango de fechas para las temporadas que quieres incluir
    # Por ejemplo, la temporada regular de la MLB 2023
    start_date = date(2023, 3, 30)
    end_date = date(2023, 10, 1)
    
    # <<< ESTA ES LA LÍNEA CORREGIDA Y DEFINITIVA >>>
    # La variable se inicializa como una lista vacía con [].
    all_game_data = []

    print(f"Iniciando la recolección de datos desde {start_date} hasta {end_date}...")

    for single_date in daterange(start_date, end_date):
        date_str = single_date.strftime("%Y-%m-%d")
        print(f"Procesando fecha: {date_str}")
        
        games_on_date = get_games_for_date(date_str)
        
        if not games_on_date:
            continue

        for game in games_on_date:
            # 1. Asegurarse de que el partido haya terminado
            game_status = game.get('status', {}).get('abstractGameState', '')
            if game_status!= 'Final':
                continue

            # 2. Extraer las características (Features)
            home_team_data = game.get('teams', {}).get('home', {})
            away_team_data = game.get('teams', {}).get('away', {})
            
            features = {
                'h_team_wins_season': home_team_data.get('leagueRecord', {}).get('wins', 0),
                'h_team_losses_season': home_team_data.get('leagueRecord', {}).get('losses', 0),
                'v_team_wins_season': away_team_data.get('leagueRecord', {}).get('wins', 0),
                'v_team_losses_season': away_team_data.get('leagueRecord', {}).get('losses', 0),
            }

            # 3. Determinar el resultado (Target)
            is_home_winner = home_team_data.get('isWinner', False)
            features['target'] = 1 if is_home_winner else 0
            
            all_game_data.append(features)
        
        # La API de la MLB tiene límites de peticiones, es bueno ser cortés
        time.sleep(1) 

    print("Recolección de datos completada. Creando DataFrame...")
    
    # 4. Crear el DataFrame y guardarlo como CSV
    if all_game_data:
        historical_df = pd.DataFrame(all_game_data)
        
        # Crear la carpeta 'data' si no existe
        if not os.path.exists('data'):
            os.makedirs('data')
            
        output_path = 'data/historical_game_data_with_features.csv'
        historical_df.to_csv(output_path, index=False)
        
        print(f"¡Éxito! El dataset ha sido guardado en: {output_path}")
        print(f"Total de partidos procesados: {len(historical_df)}")
    else:
        print("No se encontraron datos de partidos finalizados en el rango de fechas.")

if __name__ == '__main__':
    build_historical_dataset()