================================================
PROYECTO: predictor_mlb - Documentación de Módulos
================================================
Versión: 3.0 (Arquitectura Modular Estable)
Fecha: 05 de Agosto, 2025

Este documento describe la función de cada uno de los 13 archivos y módulos clave que componen la aplicación, siguiendo el principio de diseño de "director de orquesta", donde 'app.py' coordina el trabajo de los demás componentes.

-------------------------------------------------
### Archivos Principales (Raíz del Proyecto)
-------------------------------------------------

1. **run.py**: 
   - **Función:** Es el **punto de entrada único y oficial** para ejecutar la aplicación.
   - **Responsabilidad:** Su única misión es importar la aplicación Flask desde 'src.app' y ponerla en marcha. Soluciona todos los problemas de importación de Python.

2. **requirements.txt**:
   - **Función:** El **manifiesto de dependencias** del proyecto.
   - **Responsabilidad:** Lista todas las librerías exactas y sus versiones que nuestro proyecto necesita para funcionar. Permite recrear el entorno virtual en cualquier máquina con un solo comando (`pip install -r requirements.txt`).

-------------------------------------------------
### Módulos en la Carpeta `src/`
-------------------------------------------------

3. **app.py (El Director de Orquesta)**:
   - **Función:** Es el núcleo de la aplicación web, ahora significativamente simplificado.
   - **Responsabilidad:** Gestiona las rutas (URL), recibe las peticiones del usuario y coordina a todos los demás módulos para obtener los datos, procesar los juegos y enviar el resultado final a la plantilla 'index.html'.

4. **api_client.py**:
   - **Función:** Nuestra **librería personalizada** para comunicarnos con la API de la MLB.
   - **Responsabilidad:** Se encarga de construir la URL de la API, realizar la llamada usando la librería `requests`, y devolver los datos de los juegos en un formato de diccionario de Python limpio y predecible.

5. **asset_loader.py**:
   - **Función:** El **cargador de activos** de Machine Learning.
   - **Responsabilidad:** Carga todos los archivos pesados que la aplicación necesita al arrancar: el modelo entrenado (.pkl), los mapas de estadísticas y rachas, y los datos históricos de los lanzadores.

6. **config.py**:
   - **Función:** El **archivo de configuración** del proyecto.
   - **Responsabilidad:** Contiene todas las variables y constantes que no cambian, como `TEAM_NAME_MAP` y `PREDICTION_LIMITS`.

7. **game_processor.py**:
   - **Función:** El **jefe de producción** para un solo partido.
   - **Responsabilidad:** Orquesta el procesamiento completo de un único juego. Llama a los módulos de UI, predicción y estado en el orden correcto y devuelve un diccionario `game_data` final y listo para ser mostrado.

8. **metrics_calculator.py**:
   - **Función:** El **calculador de métricas en vivo**.
   - **Responsabilidad:** Toma los juegos ya procesados del día y recalcula la precisión diaria en tiempo real, basándose en los estados "Winner" o "Loser" determinados por el 'status_manager'.

9. **prediction_manager.py**:
   - **Función:** El **archivista** o administrador del historial de pronósticos.
   - **Responsabilidad:** Gestiona el archivo `mlb_predictions.csv`. Se encarga de leer el historial de predicciones, añadir nuevos pronósticos y calcular la precisión basándose en los resultados guardados.

10. **prediction_module.py**:
    - **Función:** El **cerebro de predicción** de la aplicación.
    - **Responsabilidad:** Recibe los datos de un partido, construye el vector de características y lo pasa al modelo de Machine Learning para obtener una predicción (ganador y confianza).

11. **session_manager.py**:
    - **Función:** El **gestor de sesión** del usuario.
    - **Responsabilidad:** Maneja la lógica de la sesión de Flask, rastreando qué predicciones ha desbloqueado un usuario y si ha alcanzado su límite diario.

12. **status_manager.py**:
    - **Función:** El **evaluador de estado** del pronóstico.
    - **Responsabilidad:** Su única misión es determinar si un pronóstico es "Winner", "Loser", "Pendiente" o "Evaluación Pendiente", comparando en tiempo real la predicción del modelo con el resultado del juego.

13. **ui_manager.py**:
    - **Función:** El **preparador de datos visuales**.
    - **Responsabilidad:** Transforma el diccionario de datos crudo de un juego en un formato enriquecido que la plantilla 'index.html' puede mostrar fácilmente (logos, récords, marcadores, etc.).