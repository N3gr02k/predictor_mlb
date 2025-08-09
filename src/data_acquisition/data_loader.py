# src/data_acquisition/data_loader.py

import mlbstatsapi
import pybaseball as pyb
import pandas as pd
import datetime
import os
import time

# Definimos la ruta a nuestro índice maestro.
PLAYER_INDEX_FILE = "data/raw/player_id_master_index.csv"

def load_player_index():
    """Carga el índice maestro de jugadores desde el archivo CSV."""
    if not os.path.exists(PLAYER_INDEX_FILE):
        raise FileNotFoundError(f"El archivo de índice de jugadores no se encontró en {PLAYER_INDEX_FILE}. "
                              "Por favor, ejecuta 'player_id_manager.py' primero.")
    return pd.read_csv(PLAYER_INDEX_FILE)

def get_player_analysis_data(player_name: str):
    """
    Implementa nuestro flujo de trabajo híbrido: Descubrimiento -> Traducción -> Enriquecimiento.
    """
    print(f"--- Iniciando análisis para: {player_name} ---")
    
    # --- PASO 1: DESCUBRIMIENTO (usando python-mlb-statsapi) ---
    print("[1/4] Descubriendo IDs básicos con mlbstatsapi...")
    mlb = mlbstatsapi.Mlb()
    try:
        player_ids = mlb.get_people_id(player_name)
        if not player_ids:
            print(f"Error: No se encontró al jugador '{player_name}' con mlbstatsapi.")
            return None
        
        # CORRECCIÓN #1 (TU DESCUBRIMIENTO): Extraemos el NÚMERO de la lista.
        player_id_mlbam = player_ids

        player_obj = mlb.get_person(player_id_mlbam)
        
        team_id = None
        
        # PLAN A: Intentar obtener el equipo desde el perfil del jugador.
        if hasattr(player_obj, 'currentteam') and player_obj.currentteam:
            team_id = player_obj.currentteam.id
            print(f"  -> Plan A exitoso: Equipo obtenido del perfil del jugador.")

        # PLAN B: Si el Plan A falla, obtener el equipo desde las estadísticas de la temporada.
        if not team_id:
            print("  -> 'currentteam' no disponible. Ejecutando Plan B: Obtener equipo desde estadísticas.")
            today = datetime.date.today()
            stats_params = {'season': today.year}
            stats = mlb.get_player_stats(player_id_mlbam, stats=['season'], groups=['hitting'], **stats_params)
            
            # ####################################################################
            # ### CORRECCIÓN FINAL: Mapeamos el objeto y extraemos el PRIMER elemento de la lista 'splits'. ###
            # ####################################################################
            if stats and 'hitting' in stats and 'season' in stats['hitting'] and stats['hitting']['season'].splits:
                # Extraemos el primer objeto de la lista de splits y luego accedemos a su propiedad.team.id
                team_id = stats['hitting']['season'].splits.team.id
                print(f"  -> Plan B exitoso: Equipo obtenido de las estadísticas de la temporada.")

        if not team_id:
            print(f"Error: No se pudo determinar el equipo actual para el jugador con ID {player_id_mlbam} por ningún método.")
            return None
        
        today = datetime.date.today()
        start_date = today - datetime.timedelta(days=30)
        schedule = mlb.get_schedule(start_date=start_date.strftime('%Y-%m-%d'), end_date=today.strftime('%Y-%m-%d'), team_id=team_id)
        
        if not schedule or not hasattr(schedule, 'games') or not schedule.games:
            print(f"No se encontraron juegos finalizados recientemente para el equipo de {player_name}.")
            return None

        completed_games = [game for game in schedule.games if game.status.abstract_game_state == 'Final']
        if not completed_games:
            print(f"No se encontraron juegos finalizados recientemente para el equipo de {player_name}.")
            return None
            
        completed_games.sort(key=lambda g: g.game_date, reverse=True)
        last_game_pk = completed_games.game_pk
        
        print(f"  -> ID de MLBAM: {player_id_mlbam}, Último juego PK: {last_game_pk}")

    except Exception as e:
        print(f"Error durante la fase de descubrimiento: {e}")
        return None

    # --- PASO 2: TRADUCIÓN DE IDS (usando nuestro índice maestro) ---
    print("[2/4] Traduciendo IDs con nuestro índice maestro...")
    player_index = load_player_index()
    player_row = player_index[player_index['key_mlbam'] == player_id_mlbam]
    if player_row.empty or pd.isna(player_row['key_fangraphs'].iloc):
        print(f"Error: No se pudo encontrar un ID de FanGraphs para MLBAM ID {player_id_mlbam}.")
        return None
    player_fangraphs_id = int(player_row['key_fangraphs'].iloc)
    print(f"  -> ID de FanGraphs: {player_fangraphs_id}")

    # --- PASO 3: ENRIQUECIMIENTO (usando pybaseball) ---
    try:
        pyb.cache.enable()
        print("[3/4] Obteniendo datos de Statcast del último juego...")
        last_game_statcast = pyb.statcast_batter_at_bat(last_game_pk, player_id_mlbam)
        time.sleep(2) 
        print("[4/4] Obteniendo estadísticas de temporada de FanGraphs...")
        season_stats_fg = pyb.batting_stats(today.year)
        player_season_stats = season_stats_fg == player_fangraphs_id
        print("--- Análisis completado con éxito ---")
        
        return {
            "player_info": {"name": player_name, "mlbam_id": player_id_mlbam, "fangraphs_id": player_fangraphs_id, "last_game_pk": last_game_pk},
            "last_game_statcast": last_game_statcast,
            "season_fangraphs_stats": player_season_stats
        }

    except Exception as e:
        print(f"Error durante la fase de enriquecimiento con pybaseball: {e}")
        return None