# run.py
import sys
import os

# Soluciona los problemas de importación de forma definitiva
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from src.app import app

if __name__ == '__main__':
    app.run(debug=True)