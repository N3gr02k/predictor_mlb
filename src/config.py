# src/config.py
TEAM_NAME_MAP = {
    "Arizona Diamondbacks": "ARI", "Atlanta Braves": "ATL", "Baltimore Orioles": "BAL",
    "Boston Red Sox": "BOS", "Chicago Cubs": "CHN", "Chicago White Sox": "CHA",
    "Cincinnati Reds": "CIN", "Cleveland Guardians": "CLE", "Colorado Rockies": "COL",
    "Detroit Tigers": "DET", "Houston Astros": "HOU", "Kansas City Royals": "KCA",
    "Los Angeles Angels": "ANA", "Los Angeles Dodgers": "LAN", "Miami Marlins": "MIA",
    "Milwaukee Brewers": "MIL", "Minnesota Twins": "MIN", "New York Mets": "NYN",
    "New York Yankees": "NYA", "Oakland Athletics": "OAK", "Athletics": "OAK",
    "Philadelphia Phillies": "PHI", "Pittsburgh Pirates": "PIT", "San Diego Padres": "SDN",
    "San Francisco Giants": "SFN", "Seattle Mariners": "SEA", "St. Louis Cardinals": "SLN",
    "Tampa Bay Rays": "TBA", "Texas Rangers": "TEX", "Toronto Blue Jays": "TOR",
    "Washington Nationals": "WAS"
}

PREDICTION_LIMITS = {
    'Master': float('inf'),
    'Senior': 5,
    'Junior': 2,
    'Administrator': float('inf')
}