"""Rutas de la carpeta de datos de la demo. Nunca se guarda nada junto al .exe."""
import os
import sys
from pathlib import Path


def carpeta_datos() -> Path:
    """Carpeta donde viven la base y los reportes. No la crea.

    Se puede cambiar con la variable de entorno DATOS_DEMO_DIR (se lee en cada llamada)."""
    forzada = os.environ.get("DATOS_DEMO_DIR")
    if forzada:
        return Path(forzada)
    if sys.platform == "win32":
        base = os.environ.get("LOCALAPPDATA") or str(Path.home() / "AppData" / "Local")
        return Path(base) / "ProveedoresDemo"
    return Path.home() / ".proveedores_demo"


def ruta_bd() -> Path:
    return carpeta_datos() / "demo.db"