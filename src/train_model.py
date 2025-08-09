# src/train_model.py

import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
from xgboost import XGBClassifier
import joblib # Para guardar el modelo
import os # Necesario para construir la ruta del archivo

# --- INSTRUCCIONES DE INSTALACIÓN (si es necesario) ---
# Si ves un error "ModuleNotFoundError", ejecuta estos comandos en tu terminal:
# python -m pip install scikit-learn xgboost joblib
# ---------------------------------------------------------

def train_and_evaluate_model(dataset_path):
    """
    Carga el dataset, entrena un modelo XGBoost y evalúa su precisión.
    """
    print(f"--- Cargando dataset desde: {dataset_path} ---")
    try:
        df = pd.read_csv(dataset_path)
    except FileNotFoundError:
        print(f"\n[ERROR] No se encontró el archivo del dataset en '{dataset_path}'.")
        print("Por favor, ejecuta primero 'src/build_dataset.py' para crearlo.")
        return

    print("Dataset cargado exitosamente.")
    
    # --- 1. PREPROCESAMIENTO DE DATOS ---
    print("\n--- 1. Preparando los datos para el entrenamiento ---")
    
    # Seleccionamos las características que usará el modelo
    features = [
        'home_recent_era', 'home_recent_whip', 'home_team_ops', 'home_bullpen_era', 
        'home_park_factor', 'away_recent_era', 'away_recent_whip', 'away_team_ops', 
        'away_bullpen_era'
    ]
    
    target = 'home_team_winner'
    
    # Nos aseguramos de que solo usamos las columnas necesarias
    df_model = df[features + [target]].copy()
    
    # Manejo de valores nulos: una estrategia simple es rellenar con la media de la columna.
    # Esto es crucial si, por ejemplo, un lanzador no tenía estadísticas recientes.
    for col in features:
        if df_model[col].isnull().any():
            mean_value = df_model[col].mean()
            # CAMBIO: Se actualiza la forma de rellenar los nulos para evitar el FutureWarning.
            df_model[col] = df_model[col].fillna(mean_value)
            print(f"Valores nulos en '{col}' rellenados con la media ({mean_value:.2f}).")

    # Separamos las características (X) de la variable objetivo (y)
    X = df_model[features]
    y = df_model[target]
    
    # --- 2. DIVISIÓN DE DATOS ---
    print("\n--- 2. Dividiendo los datos en conjuntos de entrenamiento y prueba ---")
    # Usamos 80% de los datos para entrenar y 20% para probar la precisión.
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    print(f"Tamaño del conjunto de entrenamiento: {len(X_train)} partidos.")
    print(f"Tamaño del conjunto de prueba: {len(X_test)} partidos.")
    
    # --- 3. ENTRENAMIENTO DEL MODELO ---
    print("\n--- 3. Entrenando el modelo XGBoost ---")
    # XGBoost es un algoritmo potente, ideal para datos tabulares como los nuestros.
    model = XGBClassifier(use_label_encoder=False, eval_metric='logloss', random_state=42)
    model.fit(X_train, y_train)
    print("Modelo entrenado exitosamente.")
    
    # --- 4. EVALUACIÓN DEL MODELO ---
    print("\n--- 4. Evaluando la precisión del modelo ---")
    # Hacemos predicciones en el conjunto de prueba, que el modelo nunca ha visto.
    y_pred = model.predict(X_test)
    
    # Comparamos las predicciones con los resultados reales.
    accuracy = accuracy_score(y_test, y_pred)
    print(f"\n========================================")
    print(f" PRECISIÓN DEL MODELO: {accuracy:.2%}")
    print(f"========================================")
    
    # --- 5. GUARDAR EL MODELO ---
    # CAMBIO CLAVE: Guardar el modelo en la carpeta correcta 'src/ml_model'
    model_dir = 'src/ml_model'
    if not os.path.exists(model_dir):
        os.makedirs(model_dir) # Crea la carpeta si no existe
        
    model_filename = os.path.join(model_dir, 'mlb_predictor_model.pkl')
    print(f"\n--- 5. Guardando el modelo entrenado en '{model_filename}' ---")
    joblib.dump(model, model_filename)
    print("Modelo guardado exitosamente.")
    
    return model, features

# ===================================================================
# BLOQUE PRINCIPAL DE EJECUCIÓN
# ===================================================================
if __name__ == "__main__":
    # Asegúrate de que el nombre del archivo coincida con el que generó build_dataset.py
    dataset_filename = 'mlb_dataset_2024_05.csv'
    train_and_evaluate_model(dataset_filename)
