# src/api_client.py
import requests
from datetime import datetime

BASE_URL = "https://statsapi.mlb.com/api/v1"

def get_games_for_date(date_str):
    hydrate = "linescore,team,leagueRecord,probablePitcher,game(content(summary)),gameData"
    url = f"{BASE_URL}/schedule?sportId=1&date={date_str}&hydrate={hydrate}"
    
    print(f"--- [API Client] Llamando a la URL: {url} ---")
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if 'dates' in data and data['dates']:
            games_list = data['dates'][0].get('games', [])
            for game in games_list:
                game_date_str = game.get('gameDate', '1970-01-01T00:00:00Z')
                game['game_time'] = datetime.strptime(game_date_str, '%Y-%m-%dT%H:%M:%SZ').strftime('%I:%M %p')
            print(f"--- [API Client] ¡Éxito! Se encontraron {len(games_list)} partidos.")
            return games_list
        else:
            return []
    except requests.exceptions.RequestException as e:
        print(f"--- [API Client] ERROR al obtener datos de la MLB: {e} ---")
        return []