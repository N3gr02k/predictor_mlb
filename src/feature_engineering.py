# src/feature_engineering.py (VERSIÓN FINAL COMPLETA)
import pandas as pd

def add_pythagorean_expectation(df):
    """
    Calcula la Expectativa Pitagórica para cada equipo y añade la diferencia
    como una nueva característica al DataFrame.
    """
    print("--- Aplicando Ingeniería de Características: Expectativa Pitagórica ---")
    
    # Usamos una aproximación de carreras basada en victorias y derrotas.
    # En un futuro, obtener las carreras reales mejoraría aún más esta métrica.
    df['h_team_rs'] = df['h_team_wins_season'] * 4.5
    df['h_team_ra'] = df['h_team_losses_season'] * 4.5
    df['v_team_rs'] = df['v_team_wins_season'] * 4.5
    df['v_team_ra'] = df['v_team_losses_season'] * 4.5

    exponent = 1.83
    df['h_pyth_exp'] = df['h_team_rs']**exponent / (df['h_team_rs']**exponent + df['h_team_ra']**exponent)
    df['v_pyth_exp'] = df['v_team_rs']**exponent / (df['v_team_rs']**exponent + df['v_team_ra']**exponent)
    df['pythag_diff'] = df['h_pyth_exp'] - df['v_pyth_exp']
    
    print("¡Característica 'pythag_diff' creada con éxito!")
    return df

class EloRatingSystem:
    """
    Un sistema de calificación Elo para rastrear la fortaleza dinámica de los equipos.
    """
    def __init__(self, k_factor=20, base_rating=1500):
        self.ratings = {}
        self.k_factor = k_factor
        self.base_rating = base_rating

    def get_rating(self, team_name):
        return self.ratings.get(team_name, self.base_rating)

    def update_ratings(self, winner_name, loser_name):
        rating_winner = self.get_rating(winner_name)
        rating_loser = self.get_rating(loser_name)
        expected_winner = 1 / (1 + 10**((rating_loser - rating_winner) / 400))
        self.ratings[winner_name] = rating_winner + self.k_factor * (1 - expected_winner)
        self.ratings[loser_name] = rating_loser + self.k_factor * (0 - (1 - expected_winner))

def add_elo_ratings(df, elo_system):
    """Añade la diferencia de Elo como una nueva característica."""
    print("--- Aplicando Ingeniería de Características: Calificaciones Elo ---")
    df['h_elo'] = df['h_team_name'].apply(elo_system.get_rating)
    df['v_elo'] = df['v_team_name'].apply(elo_system.get_rating)
    df['elo_diff'] = df['h_elo'] - df['v_elo']
    print("¡Característica 'elo_diff' creada con éxito!")
    return df

def add_rolling_win_percentage(df):
    """
    Calcula el porcentaje de victorias en una ventana móvil de 10 partidos
    para capturar la forma reciente del equipo.
    """
    print("--- Aplicando Ingeniería de Características: Forma Reciente (Medias Móviles) ---")
    
    df_sorted = df.sort_values(by='game_date').reset_index()
    
    df_sorted['h_win'] = (df_sorted['target'] == 1).astype(int)
    df_sorted['v_win'] = (df_sorted['target'] == 0).astype(int)
    
    h_roll = df_sorted.groupby('h_team_name')['h_win'].transform(lambda x: x.rolling(10, min_periods=1).mean().shift(1))
    v_roll = df_sorted.groupby('v_team_name')['v_win'].transform(lambda x: x.rolling(10, min_periods=1).mean().shift(1))
    
    df_sorted['h_win_pct_roll_10'] = h_roll
    df_sorted['v_win_pct_roll_10'] = v_roll
    
    df_sorted['win_pct_roll_diff'] = df_sorted['h_win_pct_roll_10'] - df_sorted['v_win_pct_roll_10']
    
    df_sorted = df_sorted.drop(columns=['h_win', 'v_win', 'h_win_pct_roll_10', 'v_win_pct_roll_10'])
    df_sorted = df_sorted.fillna(0)
    
    # Devolvemos el dataframe original con la nueva columna, manteniendo el orden original
    df['win_pct_roll_diff'] = df_sorted['win_pct_roll_diff']

    print("¡Característica 'win_pct_roll_diff' creada con éxito!")
    return df