# investigate_api.py (Versión final usando solo Requests)

import requests # Usaremos la librería estándar para peticiones web.
import json
from datetime import datetime, timedelta
import pandas as pd
import sys

# --- INSTRUCCIONES DE INSTALACIÓN (si es necesario) ---
# Si ves un error "ModuleNotFoundError", ejecuta estos comandos en tu terminal:
# python -m pip install requests pandas
# ---------------------------------------------------------

# ===================================================================
# PASO 0: CHEQUEO DEL ENTORNO
# ===================================================================
print("--- PASO 0: CHEQUEO DEL ENTORNO ---")
print(f"El script está siendo ejecutado por el intérprete de Python en:")
print(f"-> {sys.executable}\n")
# -------------------------------------------------------------------

# --- CONFIGURACIÓN ---
player_name_to_find = "Tarik Skubal"
player_team_name_to_find = "Detroit Tigers" 
BASE_API_URL = "https://statsapi.mlb.com/api/v1"

# --- BASE DE DATOS DE PARK FACTORS ---
# Fuente: ESPN Park Factors 2023. Un valor > 1.000 favorece a los bateadores, < 1.000 a los lanzadores.
PARK_FACTORS = {
    "Angel Stadium": 1.019, "Coors Field": 1.359, "Comerica Park": 0.932,
    "Fenway Park": 1.103, "Great American Ball Park": 1.251, "Guaranteed Rate Field": 1.118,
    "Kauffman Stadium": 1.082, "Minute Maid Park": 0.951, "Nationals Park": 1.033,
    "Oracle Park": 0.849, "Oriole Park at Camden Yards": 0.999, "PNC Park": 0.953,
    "Petco Park": 0.879, "Progressive Field": 0.951, "Rogers Centre": 1.052,
    "T-Mobile Park": 0.842, "Target Field": 1.001, "Tropicana Field": 0.918,
    "Truist Park": 1.042, "Wrigley Field": 1.049, "Yankee Stadium": 1.087,
    "American Family Field": 0.998, "Busch Stadium": 0.916, "Chase Field": 1.036,
    "Citi Field": 0.871, "Citizens Bank Park": 1.059, "Dodger Stadium": 0.937,
    "loanDepot park": 0.887, "Globe Life Field": 0.887, "Oakland Coliseum": 0.855
}


print(f"--- INICIANDO RADIOGRAFÍA DE LA API PARA: {player_name_to_find} ({player_team_name_to_find}) ---")
print("Usando el método de búsqueda por roster de equipo para máxima fiabilidad.\n")

player_id = None
player_full_name = ""
position = "N/A"
team_id = None
team_venue_name = None
season = 2024

# ===================================================================
# PASO 1: Buscar al jugador a través del Roster de su equipo
# ===================================================================
print("1. Buscando ID del jugador vía roster de equipo...")
try:
    print(f"   - Buscando el ID para el equipo '{player_team_name_to_find}'...")
    teams_response = requests.get(f"{BASE_API_URL}/teams?sportId=1")
    teams_response.raise_for_status()
    teams_data = teams_response.json().get('teams', [])
    
    team_id_found = None
    for team in teams_data:
        if team.get('name', '').lower() == player_team_name_to_find.lower():
            team_id_found = team['id']
            team_venue_name = team.get('venue', {}).get('name')
            break
            
    if not team_id_found:
        raise ValueError(f"No se pudo encontrar un equipo con el nombre '{player_team_name_to_find}'.")
    
    team_id = team_id_found
    print(f"   - Equipo encontrado con ID: {team_id} (Estadio: {team_venue_name})")

    print(f"   - Obteniendo roster del equipo y buscando a '{player_name_to_find}'...")
    roster_url = f"{BASE_API_URL}/teams/{team_id}/roster?rosterType=40Man"
    roster_response = requests.get(roster_url)
    roster_response.raise_for_status()
    roster_list = roster_response.json().get('roster', [])

    found_player_person = None
    for item in roster_list:
        person = item.get('person', {})
        if player_name_to_find.lower() in person.get('fullName', '').lower():
            found_player_person = person
            break
            
    if found_player_person:
        player_id = found_player_person['id']
        player_full_name = found_player_person['fullName']
        print(f"   - ¡Éxito! Se encontró a '{player_full_name}' con el ID de MLB: {player_id}\n")
    else:
        raise ValueError(f"No se pudo encontrar a '{player_name_to_find}' en el roster de '{player_team_name_to_find}'.")

except Exception as e:
    print(f"\n[ERROR] Ocurrió un error en el PASO 1: {e}")
    exit()

# ===================================================================
# PASO 2: Obtener información de la persona
# ===================================================================
print(f"2. Obteniendo datos de la persona para el ID {player_id}...")
try:
    person_url = f"{BASE_API_URL}/people/{player_id}"
    response = requests.get(person_url)
    response.raise_for_status()
    person_data = response.json().get('people', [])
    if person_data:
        position = person_data[0].get('primaryPosition', {}).get('abbreviation', 'N/A')
        print(f"   - ¡Éxito! Se obtuvieron los datos de '{person_data[0].get('fullName', 'N/A')}' (Posición: {position}).")
    else:
        print("   - Error: La API no devolvió datos para esta persona.\n")
except Exception as e:
    print(f"   - Error en el PASO 2: {e}\n")

# ===================================================================
# PASO 3: Obtener estadísticas de la temporada
# ===================================================================
group = "hitting" if position != "P" else "pitching"
print(f"\n3. Obteniendo estadísticas de '{group}' de la temporada para el ID {player_id}...")
try:
    stats_url = f"{BASE_API_URL}/people/{player_id}/stats"
    stats_params = {'stats': 'season', 'group': group}
    response = requests.get(stats_url, params=stats_params)
    response.raise_for_status()
    stats_data = response.json().get('stats', [])
    if stats_data:
        print("   - ¡Éxito! Se obtuvieron las estadísticas de la temporada.")
    else:
        print("   - Error: La API no devolvió estadísticas para esta persona.")
except Exception as e:
    print(f"   - Error en el PASO 3: {e}")

# ===================================================================
# PASO 4: ENRIQUECER DATOS USANDO EL ENDPOINT 'GAMELOG' DE LA API DE MLB
# ===================================================================
if position == 'P':
    print(f"\n4. Obteniendo rendimiento reciente para '{player_full_name}' usando la API de MLB...")
    try:
        # Construimos la URL para obtener los registros de juego (gameLog) del lanzador
        gamelog_url = f"{BASE_API_URL}/people/{player_id}/stats"
        gamelog_params = {'stats': 'gameLog', 'group': 'pitching', 'season': season}
        
        print(f"   - Consultando registros de juego de la temporada {season}...")
        response = requests.get(gamelog_url, params=gamelog_params)
        response.raise_for_status()
        
        # La API devuelve una lista de "splits", donde cada split es un juego.
        game_logs = response.json().get('stats', [{}])[0].get('splits', [])
        
        if not game_logs:
            print("   - Información: No se encontraron registros de juego para este jugador en la temporada especificada.")
        else:
            # Convertimos la lista de juegos a un DataFrame de pandas
            game_logs_df = pd.DataFrame(game_logs)
            
            # La fecha viene en el formato 'YYYY-MM-DD', la convertimos para poder filtrar
            game_logs_df['game_date_dt'] = pd.to_datetime(game_logs_df['date'])

            # Definimos el rango de fechas para el análisis
            start_date = datetime(season, 5, 1)
            end_date = datetime(season, 5, 31)
            print(f"   - Filtrando localmente por el rango de fechas: {start_date.strftime('%Y-%m-%d')} a {end_date.strftime('%Y-%m-%d')}...")

            # Filtramos por fecha
            recent_games = game_logs_df[
                (game_logs_df['game_date_dt'] >= start_date) & 
                (game_logs_df['game_date_dt'] <= end_date)
            ]

            if recent_games.empty:
                print(f"   - Información: El lanzador no tuvo actividad entre {start_date.strftime('%Y-%m-%d')} y {end_date.strftime('%Y-%m-%d')}.")
            else:
                # Los datos de la API ya vienen como números, pero los convertimos por seguridad
                total_ip = pd.to_numeric(recent_games['stat'].apply(lambda x: x.get('inningsPitched', 0)), errors='coerce').sum()
                total_er = pd.to_numeric(recent_games['stat'].apply(lambda x: x.get('earnedRuns', 0)), errors='coerce').sum()
                total_hits = pd.to_numeric(recent_games['stat'].apply(lambda x: x.get('hits', 0)), errors='coerce').sum()
                total_walks = pd.to_numeric(recent_games['stat'].apply(lambda x: x.get('baseOnBalls', 0)), errors='coerce').sum()
                
                if total_ip > 0:
                    recent_era = (total_er * 9) / total_ip
                    recent_whip = (total_walks + total_hits) / total_ip
                    print("\n   --- RENDIMIENTO RECIENTE DEL LANZADOR (RANGO FIJO) ---")
                    print(f"   - Total Innings Lanzados: {total_ip:.1f}")
                    print(f"   - ERA Reciente: {recent_era:.2f}")
                    print(f"   - WHIP Reciente: {recent_whip:.2f}")
                    print("   ----------------------------------------------------")
                else:
                    print("   - Información: No hay suficientes datos para calcular ERA/WHIP recientes.")

    except Exception as e:
        print(f"\n[ERROR] Ocurrió un error durante el enriquecimiento con la API de MLB: {e}")

# ===================================================================
# PASO 5: OBTENER RENDIMIENTO RECIENTE DEL EQUIPO (TEAM MOMENTUM)
# ===================================================================
if team_id:
    print(f"\n5. Obteniendo rendimiento reciente para '{player_team_name_to_find}'...")
    try:
        # Definimos el rango de fechas (últimos 14 días)
        # Usamos fechas fijas para consistencia en las pruebas
        end_date_momentum = datetime(season, 5, 31)
        start_date_momentum = end_date_momentum - timedelta(days=14)
        
        start_str = start_date_momentum.strftime('%Y-%m-%d')
        end_str = end_date_momentum.strftime('%Y-%m-%d')
        
        print(f"   - Consultando estadísticas del equipo entre {start_str} y {end_str}...")

        # Parámetros base para la consulta
        momentum_params = {
            'season': season,
            'startDate': start_str,
            'endDate': end_str
        }

        # --- OFENSIVA ---
        offensive_params = {**momentum_params, 'stats': 'byDateRange', 'group': 'hitting'}
        offensive_url = f"{BASE_API_URL}/teams/{team_id}/stats"
        offensive_response = requests.get(offensive_url, params=offensive_params)
        offensive_response.raise_for_status()
        offensive_stats = offensive_response.json().get('stats', [{}])[0].get('splits', [{}])[0].get('stat', {})
        
        runs_scored = offensive_stats.get('runs', 'N/A')
        team_ops = offensive_stats.get('ops', 'N/A')

        # --- DEFENSIVA (PITCHEO TOTAL) ---
        pitching_params = {**momentum_params, 'stats': 'byDateRange', 'group': 'pitching'}
        pitching_url = f"{BASE_API_URL}/teams/{team_id}/stats"
        pitching_response = requests.get(pitching_url, params=pitching_params)
        pitching_response.raise_for_status()
        pitching_stats = pitching_response.json().get('stats', [{}])[0].get('splits', [{}])[0].get('stat', {})
        
        runs_allowed = pitching_stats.get('runs', 'N/A')

        # --- BULLPEN (NUEVA LÓGICA ROBUSTA) ---
        print("   - Calculando rendimiento del bullpen a partir de registros de juego...")
        schedule_url = f"{BASE_API_URL}/schedule"
        schedule_params = {'sportId': 1, 'teamId': team_id, 'startDate': start_str, 'endDate': end_str}
        schedule_response = requests.get(schedule_url, params=schedule_params)
        schedule_response.raise_for_status()
        
        games = schedule_response.json().get('dates', [])
        
        total_bullpen_ip_outs = 0
        total_bullpen_er = 0
        total_bullpen_hits = 0
        total_bullpen_walks = 0

        for date_info in games:
            for game in date_info.get('games', []):
                game_pk = game['gamePk']
                boxscore_url = f"{BASE_API_URL}/game/{game_pk}/boxscore"
                boxscore_response = requests.get(boxscore_url)
                boxscore_data = boxscore_response.json()

                team_side = 'home' if boxscore_data['teams']['home']['team']['id'] == team_id else 'away'
                pitchers = boxscore_data['teams'][team_side].get('pitchers', [])
                
                # Iteramos sobre los relevistas (todos menos el primero)
                for pitcher_id in pitchers[1:]:
                    player_box_stats = boxscore_data['teams'][team_side]['players'].get(f'ID{pitcher_id}', {})
                    pitcher_stats = player_box_stats.get('stats', {}).get('pitching', {})
                    
                    if pitcher_stats:
                        ip_str = pitcher_stats.get('inningsPitched', "0.0")
                        parts = ip_str.split('.')
                        full_innings = int(parts[0])
                        partial_outs = int(parts[1]) if len(parts) > 1 else 0
                        total_bullpen_ip_outs += (full_innings * 3) + partial_outs
                        
                        total_bullpen_er += pitcher_stats.get('earnedRuns', 0)
                        total_bullpen_hits += pitcher_stats.get('hits', 0)
                        total_bullpen_walks += pitcher_stats.get('baseOnBalls', 0)

        if total_bullpen_ip_outs > 0:
            total_bullpen_ip = total_bullpen_ip_outs / 3.0
            bullpen_era = f"{(total_bullpen_er * 9) / total_bullpen_ip:.2f}"
            bullpen_whip = f"{(total_bullpen_walks + total_bullpen_hits) / total_bullpen_ip:.2f}"
        else:
            bullpen_era = '0.00'
            bullpen_whip = '0.00'

        print("\n   --- MOMENTUM DEL EQUIPO (ÚLTIMOS 14 DÍAS) ---")
        print(f"   - Carreras Anotadas: {runs_scored}")
        print(f"   - OPS del Equipo: {team_ops}")
        print(f"   - Carreras Permitidas: {runs_allowed}")
        print(f"   - ERA del Bullpen: {bullpen_era}")
        print(f"   - WHIP del Bullpen: {bullpen_whip}")
        print("   ---------------------------------------------")

    except Exception as e:
        print(f"\n[ERROR] Ocurrió un error durante la obtención del momentum del equipo: {e}")

# ===================================================================
# PASO 6: OBTENER CONTEXTO DEL PARTIDO (PARK FACTORS)
# ===================================================================
if team_venue_name:
    print(f"\n6. Obteniendo contexto del partido para '{team_venue_name}'...")
    try:
        park_factor = PARK_FACTORS.get(team_venue_name, "No disponible")
        
        if isinstance(park_factor, float):
            interpretation = "Favorece a los bateadores" if park_factor > 1.0 else "Favorece a los lanzadores"
            print("\n   --- FACTORES DEL ESTADIO (PARK FACTORS) ---")
            print(f"   - Factor de Carreras: {park_factor}")
            print(f"   - Interpretación: {interpretation}")
            print("   -------------------------------------------")
        else:
            print(f"   - No se encontraron datos de Park Factor para '{team_venue_name}'.")

    except Exception as e:
        print(f"\n[ERROR] Ocurrió un error durante la obtención de los Park Factors: {e}")


print("\n--- RADIOGRAFÍA COMPLETA ---")
