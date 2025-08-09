# src/database_manager.py

from flask_sqlalchemy import SQLAlchemy
from flask import Flask
import os

db = SQLAlchemy()

class Prediction(db.Model):
    """
    Define la tabla 'predictions' en nuestra base de datos.
    """
    id = db.Column(db.Integer, primary_key=True)
    game_id = db.Column(db.Integer, unique=True, nullable=False)
    prediction_date = db.Column(db.String(10), nullable=False)
    home_team = db.Column(db.String(100), nullable=False)
    away_team = db.Column(db.String(100), nullable=False)
    predicted_winner = db.Column(db.String(100), nullable=False)
    confidence = db.Column(db.Float, nullable=False)
    actual_winner = db.Column(db.String(100), nullable=True) # Se llena cuando el juego termina
    is_correct = db.Column(db.Boolean, nullable=True) # Se calcula cuando el juego termina

def init_app(app):
    """
    Inicializa la base de datos con la aplicación Flask.
    """
    db_path = os.path.join(os.path.dirname(__file__), 'mlb_predictions.db')
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    
    with app.app_context():
        print("--- [DB Manager] Creando todas las tablas de la base de datos si no existen... ---")
        db.create_all()

def save_prediction(game_data):
    """
    Guarda o actualiza una predicción en la base de datos.
    """
    with db.session.begin():
        # Buscamos si ya existe una predicción para este juego
        existing_prediction = Prediction.query.filter_by(game_id=game_data['game_id']).first()
        
        if not existing_prediction:
            print(f"--- [DB Manager] Guardando nueva predicción para el juego {game_data['game_id']} ---")
            new_prediction = Prediction(
                game_id=game_data['game_id'],
                prediction_date=game_data['prediction_date'],
                home_team=game_data['home_team'],
                away_team=game_data['away_team'],
                predicted_winner=game_data['prediction']['winner'],
                confidence=game_data['prediction']['confidence']
            )
            db.session.add(new_prediction)
        else:
            # En el futuro, podríamos actualizar la predicción si cambia el lanzador, por ejemplo.
            pass

def update_game_result(game_data):
    """
    Actualiza una predicción con el resultado final del juego.
    """
    with db.session.begin():
        prediction_to_update = Prediction.query.filter_by(game_id=game_data['game_id']).first()
        
        if prediction_to_update and prediction_to_update.actual_winner is None:
            home_team_name = game_data.get('game', {}).get('teams', {}).get('home', {}).get('team', {}).get('name', 'N/A')
            away_team_name = game_data.get('game', {}).get('teams', {}).get('away', {}).get('team', {}).get('name', 'N/A')
            
            home_score = game_data.get('home_runs', -1)
            away_score = game_data.get('away_runs', -1)

            if home_score > away_score:
                actual_winner = home_team_name
            else:
                actual_winner = away_team_name
            
            prediction_to_update.actual_winner = actual_winner
            prediction_to_update.is_correct = (prediction_to_update.predicted_winner == actual_winner)
            print(f"--- [DB Manager] Actualizando resultado para el juego {game_data['game_id']}. Ganador: {actual_winner} ---")

def calculate_historical_accuracy():
    """
    Calcula la precisión histórica a partir de todos los resultados guardados en la BD.
    """
    completed_predictions = Prediction.query.filter(Prediction.is_correct.isnot(None)).all()
    
    if not completed_predictions:
        return 0, 0, 0
        
    total_evaluated = len(completed_predictions)
    total_winners = sum(1 for p in completed_predictions if p.is_correct)
    accuracy = (total_winners / total_evaluated * 100) if total_evaluated > 0 else 0
    
    return accuracy, total_winners, total_evaluated
