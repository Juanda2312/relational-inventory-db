import os
import shutil
import sqlite3
import tempfile
import unittest

from configuracion.rutas import ruta_bd
from demo.base import asegurar_base
from demo.datos import CREDENCIALES_DEMO
from repositorios.conexion import obtener_conexion
from servicios.seguridad_servicio import SeguridadServicio

ESPERADO = {"rol": 3, "tipo_documento": 3, "usuario": 3, "ciudad": 5, "categoria": 4,
            "proveedor": 6, "producto": 10, "proveedor_producto": 14, "bitacora": 0}


def _escalar(sql, *parametros):
    con = obtener_conexion()
    try:
        return con.cursor().execute(sql, *parametros).fetchone()[0]
    finally:
        con.close()


def _conteos():
    return {t: _escalar(f"SELECT COUNT(*) FROM {t}") for t in ESPERADO}


class BaseDemoTest(unittest.TestCase):

    def setUp(self):
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

    def test_crea_esquema_y_datos(self):
        asegurar_base()
        self.assertEqual(_conteos(), ESPERADO)

    def test_administrador_es_rol_1_y_la_base_impide_un_segundo(self):
        asegurar_base()
        self.assertEqual(
            _escalar("SELECT id_rol FROM rol WHERE nombre = 'Administrador'"), 1)
        con = obtener_conexion()
        try:
            cur = con.cursor()
            with self.assertRaises(sqlite3.IntegrityError):
                cur.execute(
                    "INSERT INTO usuario (nombre_usuario, nombre, apellido, "
                    "contrasena_hash, numero_documento, id_rol, id_tipo_documento) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?)",
                    "otro_admin", "Otro", "Admin", "x", "99999999", 1, 1)
        finally:
            con.close()

    def test_casos_para_consultas_y_reportes(self):
        asegurar_base()
        self.assertEqual(_escalar(
            "SELECT COUNT(*) FROM producto pr WHERE NOT EXISTS "
            "(SELECT 1 FROM proveedor_producto pp WHERE pp.id_producto = pr.id_producto)"), 1)
        self.assertEqual(_escalar(
            "SELECT COUNT(*) FROM proveedor p WHERE NOT EXISTS "
            "(SELECT 1 FROM proveedor_producto pp WHERE pp.id_proveedor = p.id_proveedor)"), 1)
        self.assertGreaterEqual(_escalar("SELECT COUNT(*) FROM producto WHERE estado = 0"), 1)
        self.assertGreaterEqual(
            _escalar("SELECT COUNT(*) FROM proveedor_producto WHERE estado = 0"), 1)
        self.assertEqual(_escalar(
            "SELECT COUNT(*) FROM ciudad WHERE nombre = 'Armenia' "
            "AND departamento = 'Quindío'"), 1)

    def test_es_idempotente_y_no_pisa_cambios(self):
        asegurar_base()
        con = obtener_conexion()
        try:
            con.cursor().execute(
                "UPDATE categoria SET nombre = 'Cambiada' WHERE id_categoria = 1")
            con.commit()
        finally:
            con.close()
        asegurar_base()
        self.assertEqual(_conteos(), ESPERADO)
        self.assertEqual(
            _escalar("SELECT nombre FROM categoria WHERE id_categoria = 1"), "Cambiada")

    def test_archivo_vacio_se_inicializa(self):
        ruta_bd().parent.mkdir(parents=True, exist_ok=True)
        ruta_bd().write_bytes(b"")
        asegurar_base()
        self.assertEqual(_escalar("SELECT COUNT(*) FROM rol"), 3)

    def test_credenciales_demo_verifican_contra_el_hash_guardado(self):
        asegurar_base()
        con = obtener_conexion()
        try:
            filas = con.cursor().execute(
                "SELECT u.nombre_usuario, u.contrasena_hash, r.nombre AS rol "
                "FROM usuario u JOIN rol r ON r.id_rol = u.id_rol").fetchall()
        finally:
            con.close()
        roles = {f.nombre_usuario: f.rol for f in filas}
        self.assertEqual(roles, {"admin": "Administrador", "tradicional": "Tradicional",
                                 "esporadico": "Esporadico"})
        seguridad = SeguridadServicio()
        for fila in filas:
            self.assertTrue(seguridad.verificar(
                CREDENCIALES_DEMO[fila.nombre_usuario], fila.contrasena_hash))
    def test_texto_no_distingue_mayusculas(self):
        asegurar_base()
        self.assertEqual(
            _escalar("SELECT COUNT(*) FROM usuario WHERE nombre_usuario = 'ADMIN'"), 1)
        self.assertEqual(
            _escalar("SELECT COUNT(*) FROM categoria WHERE nombre = 'lácteos'"), 1)
        con = obtener_conexion()
        try:
            with self.assertRaises(sqlite3.IntegrityError):
                con.cursor().execute(
                    "INSERT INTO categoria (nombre, descripcion) VALUES (?, ?)",
                    "LÁCTEOS", "duplicada")
        finally:
            con.close()

if __name__ == "__main__":
    unittest.main()