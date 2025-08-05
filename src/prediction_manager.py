# src/prediction_manager.py
import pandas as pd
import os

PREDICTIONS_FILE = 'mlb_predictions.csv'

def inicializar_dataframe_pronosticos():
    if os.path.exists(PREDICTIONS_FILE):
        try:
            return pd.read_csv(PREDICTIONS_FILE)
        except pd.errors.EmptyDataError:
            return pd.DataFrame(columns=['fecha_juego', 'equipo_local', 'equipo_visitante', 'pronostico_ganador', 'resultado_real', 'estado_pronostico'])
    else:
        df = pd.DataFrame(columns=['fecha_juego', 'equipo_local', 'equipo_visitante', 'pronostico_ganador', 'resultado_real', 'estado_pronostico'])
        df.to_csv(PREDICTIONS_FILE, index=False)
        return df

def agregar_pronostico(df, fecha, local, visitante, pronostico):
    mask = (df['fecha_juego'] == fecha) & (df['equipo_local'] == local) & (df['equipo_visitante'] == visitante)
    if not df[mask].empty:
        return df
    nuevo_pronostico = pd.DataFrame([{'fecha_juego': fecha, 'equipo_local': local, 'equipo_visitante': visitante, 
                                    'pronostico_ganador': pronostico, 'resultado_real': 'Pendiente', 'estado_pronostico': 'Pendiente'}])
    df = pd.concat([df, nuevo_pronostico], ignore_index=True)
    df.to_csv(PREDICTIONS_FILE, index=False)
    return df

def calculate_accuracy(df):
    if not isinstance(df, pd.DataFrame) or df.empty:
        return 0.0, 0, 0
    evaluados = df[df['estado_pronostico'].isin(['Winner', 'Loser'])]
    if len(evaluados) == 0:
        return 0.0, 0, 0
    winners = len(evaluados[evaluados['estado_pronostico'] == 'Winner'])
    total_evaluados = len(evaluados)
    accuracy = (winners / total_evaluados) * 100 if total_evaluados > 0 else 0.0
    return accuracy, winners, total_evaluados