import mlbstatsapi
import inspect
import os

print("--- INICIANDO DIAGNÓSTICO DE LIBRERÍA ---")

try:
    # Obtener la ruta del archivo que se está importando
    library_path = inspect.getfile(mlbstatsapi)
    print(f"\n[INFO] La instrucción 'import mlbstatsapi' está cargando el archivo desde:\n{library_path}")

    # Comprobar si la ruta está dentro de 'site-packages' (lo correcto) o no
    if "site-packages" in library_path:
        print("\n[OK] Se está importando la librería desde el entorno virtual. ¡Eso es bueno!")
    else:
        print("\n[PROBLEMA DETECTADO] ¡Estás importando un archivo local en lugar de la librería instalada!")
        print("   - SOLUCIÓN: Busca un archivo llamado 'mlbstatsapi.py' en tu proyecto y cámbiale el nombre (por ejemplo, a 'test_api.py').")

    # Intentar obtener la versión de la librería
    try:
        version = mlbstatsapi.__version__
        print(f"\n[INFO] Versión de MLB-StatsAPI instalada: {version}")
    except AttributeError:
        print("\n[PROBLEMA DETECTADO] No se pudo encontrar la versión. Esto confirma que probablemente es un archivo local.")

    # Comprobar si la función existe
    if hasattr(mlbstatsapi, 'lookup_player'):
        print("\n[OK] La función 'lookup_player' FUE encontrada en el módulo importado.")
    else:
        print("\n[PROBLEMA DETECTADO] La función 'lookup_player' NO FUE encontrada.")


except TypeError:
    print("\n[ERROR CRÍTICO] Python no pudo localizar la librería.")
    print("Esto puede pasar si el nombre del archivo es el mismo que el de la librería.")
    print("Por favor, revisa si tienes un archivo llamado 'mlbstatsapi.py' en tu proyecto.")


print("\n--- DIAGNÓSTICO COMPLETO ---")