"""Crea la base de la demo en la primera ejecución."""
from configuracion.rutas import carpeta_datos, ruta_bd
from demo.datos import cargar_datos_demo
from demo.esquema import ESQUEMA
from repositorios.conexion import obtener_conexion


def asegurar_base():
    """Si la base no existe (o es un archivo vacío), la crea con datos de ejemplo.
    Si ya tiene tablas, no toca nada."""
    carpeta_datos().mkdir(parents=True, exist_ok=True)
    con = obtener_conexion()
    try:
        cur = con.cursor()
        existe = cur.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'rol'"
        ).fetchone()
        if existe is not None:
            return
        try:
            con.executescript(ESQUEMA)
            cargar_datos_demo(con)
            con.commit()
        except Exception:
            # Una base a medias (con tablas pero sin datos) no se re-inicializaría
            # sola: se descarta para que el próximo arranque empiece limpio.
            con.rollback()
            con.close()
            ruta_bd().unlink(missing_ok=True)
            raise
    finally:
        con.close()