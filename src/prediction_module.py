# src/prediction_module.py
import pandas as pd

def make_prediction(h_team_name, v_team_name, model, team_stats_map, team_history_map, avg_pitcher_stats, home_team_data, away_team_data, TEAM_NAME_MAP):
    try:
        h_team_abbr = TEAM_NAME_MAP.get(h_team_name)
        v_team_abbr = TEAM_NAME_MAP.get(v_team_name)
        if not (h_team_abbr and v_team_abbr and model): return None
            
        features = {}
        for abbr, side in [(h_team_abbr, 'h'), (v_team_abbr, 'v')]:
            stats = team_stats_map.get(abbr, {}); history = team_history_map.get(abbr, [])
            if not stats or stats.get('games_played', 0) == 0: return None
            games_played = stats.get('games_played', 1); at_bats = stats.get('at_bats', 1); ip = stats.get('outs_recorded', 1) / 3
            plate_appearances = at_bats + stats.get('walks', 0) + stats.get('hit_by_pitch', 0) + stats.get('sacrifice_flies', 0); times_on_base = stats.get('hits', 0) + stats.get('walks', 0) + stats.get('hit_by_pitch', 0)
            features[f'{side}_ops'] = (times_on_base / plate_appearances) + (stats.get('total_bases', 0) / at_bats) if plate_appearances > 0 and at_bats > 0 else 0.720
            features[f'{side}_whip'] = (stats.get('walks_allowed', 0) + stats.get('hits_allowed', 0)) / ip if ip > 0 else 1.32
            features[f'{side}_k_per_9'] = 9 * stats.get('strikeouts_made', 0) / ip if ip > 0 else 8.5; features[f'{side}_streak_pct'] = sum(history) / len(history) if history else 0.5
            features[f'{side}_avg'] = stats.get('hits', 0) / at_bats if at_bats > 0 else 0.250; features[f'{side}_hr_per_g'] = stats.get('homeruns', 0) / games_played
            features[f'{side}_rbi_per_g'] = stats.get('rbi', 0) / games_played; features[f'{side}_sb_per_g'] = stats.get('stolen_bases', 0) / games_played
            features[f'{side}_gidp_per_g'] = stats.get('gidp', 0) / games_played; features[f'{side}_lob_per_g'] = stats.get('lob', 0) / games_played
            features[f'{side}_xbh_per_g'] = (stats.get('doubles', 0) + stats.get('triples', 0) + stats.get('homeruns', 0)) / games_played
            features[f'{side}_sb_eff'] = stats.get('stolen_bases', 0) / (stats.get('stolen_bases', 0) + stats.get('cs', 0)) if (stats.get('stolen_bases', 0) + stats.get('cs', 0)) > 0 else 0.75
            features[f'{side}_errors_per_g'] = stats.get('errors', 0) / games_played; features[f'{side}_dp_per_g'] = stats.get('dp_made', 0) / games_played
            features[f'{side}_saves_per_g'] = stats.get('saves', 0) / games_played

        for side, team_obj in [('h', home_team_data), ('v', away_team_data)]:
            features[f'{side}_pitcher_era'] = avg_pitcher_stats['era']
            features[f'{side}_pitcher_whip'] = avg_pitcher_stats['whip']
            features[f'{side}_pitcher_k_per_9'] = avg_pitcher_stats['k_per_9']
        
        feature_names = sorted(features.keys())
        feature_df = pd.DataFrame([features], columns=feature_names)
        probabilities = model.predict_proba(feature_df)[0]
        winner = h_team_name if probabilities[1] > probabilities[0] else v_team_name
        confidence = max(probabilities) * 100
        print(f"--- [Prediction Module] Predicción generada: {winner} con {confidence:.2f}% de confianza ---")
        return {'winner': winner, 'confidence': confidence}
    except Exception as e:
        print(f"--- [Prediction Module] ERROR al generar la predicción: {e} ---")
        return None