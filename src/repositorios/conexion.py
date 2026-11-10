"""Conexión a SQLite con la misma forma de uso que pyodbc:
cur.execute(sql, p1, p2), filas con acceso por atributo, por índice y tuple(fila)."""
import sqlite3
from collections import namedtuple
from datetime import date, datetime
from decimal import Decimal

from configuracion.rutas import carpeta_datos, ruta_bd

_CENTAVOS = Decimal("0.01")

# Adaptadores y convertidores propios (los por defecto están deprecados desde Python 3.12).
sqlite3.register_adapter(Decimal, str)
sqlite3.register_adapter(datetime, lambda d: d.strftime("%Y-%m-%d %H:%M:%S"))
sqlite3.register_adapter(date, lambda d: d.isoformat())
sqlite3.register_converter(
    "DECIMAL", lambda b: Decimal(b.decode("utf-8")).quantize(_CENTAVOS))
sqlite3.register_converter(
    "DATETIME2", lambda b: datetime.fromisoformat(b.decode("utf-8")))

_CLASES_FILA = {}


def _fabrica_filas(cursor, fila):
    """Fila como namedtuple. rename=True evita el error con COUNT(*) o columnas repetidas."""
    nombres = tuple(d[0] for d in cursor.description)
    clase = _CLASES_FILA.get(nombres)
    if clase is None:
        clase = namedtuple("Fila", nombres, rename=True)
        _CLASES_FILA[nombres] = clase
    return clase(*fila)


class Cursor:

    def __init__(self, cursor):
        self._c = cursor

    def execute(self, sql, *parametros):
        # sqlite3 exige una secuencia; pyodbc acepta parámetros sueltos.
        self._c.execute(sql, parametros)
        return self

    def fetchone(self):
        return self._c.fetchone()

    def fetchall(self):
        return self._c.fetchall()

    @property
    def description(self):
        return self._c.description

    @property
    def rowcount(self):
        return self._c.rowcount

    @property
    def lastrowid(self):
        return self._c.lastrowid


class Conexion:

    def __init__(self, conexion):
        self._con = conexion

    def cursor(self):
        return Cursor(self._con.cursor())

    def executescript(self, sql):
        self._con.executescript(sql)

    def commit(self):
        self._con.commit()

    def rollback(self):
        self._con.rollback()

    def close(self):
        self._con.close()


def obtener_conexion() -> Conexion:
    """Abre una conexión nueva; crea la carpeta de datos si no existe."""
    carpeta_datos().mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(str(ruta_bd()), detect_types=sqlite3.PARSE_DECLTYPES)
    con.row_factory = _fabrica_filas
    con.create_collation("NOCASE_UNICODE", _comparar_sin_mayusculas)
    con.execute("PRAGMA foreign_keys = ON")
    return Conexion(con)

def _comparar_sin_mayusculas(a, b):
    a, b = a.casefold(), b.casefold()
    return (a > b) - (a < b)