import os
import shutil
import tempfile
import unittest
from datetime import datetime
from decimal import Decimal
from pathlib import Path

from configuracion.rutas import ruta_bd
from repositorios.conexion import obtener_conexion


class ConexionTest(unittest.TestCase):

    def setUp(self):
        # Carpeta con espacio y ñ, como un usuario de Windows tipo «José Pérez»
        self.dir = tempfile.mkdtemp(prefix="demo ñ ")
        anterior = os.environ.get("DATOS_DEMO_DIR")
        os.environ["DATOS_DEMO_DIR"] = self.dir

        def restaurar():
            if anterior is None:
                os.environ.pop("DATOS_DEMO_DIR", None)
            else:
                os.environ["DATOS_DEMO_DIR"] = anterior
            shutil.rmtree(self.dir, ignore_errors=True)

        self.addCleanup(restaurar)

    def test_ruta_con_espacios_y_tilde(self):
        con = obtener_conexion()
        con.close()
        self.assertEqual(ruta_bd().parent, Path(self.dir))
        self.assertTrue(ruta_bd().exists())

    def test_parametros_posicionales_estilo_pyodbc_y_filas_con_atributos(self):
        con = obtener_conexion()
        try:
            cur = con.cursor()
            cur.execute("CREATE TABLE t (a INTEGER, b TEXT)")
            cur.execute("INSERT INTO t (a, b) VALUES (?, ?)", 1, "x")
            fila = cur.execute("SELECT a, b FROM t WHERE a = ?", 1).fetchone()
            self.assertEqual((fila.a, fila[1], tuple(fila)), (1, "x", (1, "x")))
        finally:
            con.close()

    def test_columnas_repetidas_o_calculadas_no_rompen(self):
        con = obtener_conexion()
        try:
            cur = con.cursor()
            cur.execute("CREATE TABLE t (a INTEGER)")
            fila = cur.execute(
                "SELECT 1 AS nombre, 2 AS nombre, COUNT(*) FROM t").fetchone()
            self.assertEqual((fila[0], fila[1]), (1, 2))
            self.assertEqual(cur.description[0][0], "nombre")
        finally:
            con.close()

    def test_decimal_y_datetime_ida_y_vuelta(self):
        con = obtener_conexion()
        try:
            cur = con.cursor()
            cur.execute("CREATE TABLE t2 (p DECIMAL(12,2), f DATETIME2(0))")
            cur.execute("INSERT INTO t2 (p, f) VALUES (?, ?)",
                        Decimal("2500.50"), datetime(2026, 11, 10, 9, 5, 7, 123456))
            fila = cur.execute("SELECT p, f FROM t2").fetchone()
            self.assertIsInstance(fila.p, Decimal)
            self.assertEqual(fila.p, Decimal("2500.50"))
            self.assertEqual(fila.f, datetime(2026, 11, 10, 9, 5, 7))
        finally:
            con.close()

    def test_claves_foraneas_activas(self):
        con = obtener_conexion()
        try:
            cur = con.cursor()
            self.assertEqual(cur.execute("PRAGMA foreign_keys").fetchone()[0], 1)
        finally:
            con.close()


if __name__ == "__main__":
    unittest.main()