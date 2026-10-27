"""Configuración global de pruebas para SismoReporta AQP."""
import sys
from pathlib import Path

# Agregar 'src' al path de búsqueda de módulos de Python
SRC_DIR = Path(__file__).resolve().parent.parent / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))
