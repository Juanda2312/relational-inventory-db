import os
import shutil
import tempfile
import unittest
from datetime import date, datetime
from decimal import Decimal

from demo.base import asegurar_base
from dominio.entidades.proveedor_producto import ProveedorProducto
from repositorios.bitacora_repositorio import BitacoraRepositorio
from repositorios.conexion import obtener_conexion
from repositorios.consulta_repositorio import ConsultaRepositorio
from repositorios.proveedor_producto_repositorio import ProveedorProductoRepositorio
from repositorios.reporte_repositorio import ReporteRepositorio
from repositorios.usuario_repositorio import UsuarioRepositorio
from servicios.autenticacion_servicio import AutenticacionServicio
from servicios.seguridad_servicio import SeguridadServicio


def _fetchall(sql, *parametros):
    con = obtener_conexion()
    try:
        return con.cursor().execute(sql, *parametros).fetchall()
    finally:
        con.close()


class RepositoriosDemoTest(unittest.TestCase):

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
        asegurar_base()

    def test_login_y_cierre_de_sesion_con_las_credenciales_demo(self):
        servicio = AutenticacionServicio(
            UsuarioRepositorio(), BitacoraRepositorio(), SeguridadServicio())
        sesion = servicio.iniciar_sesion("admin", "admin1234")
        self.assertEqual(sesion.rol, "Administrador")
        self.assertIsInstance(sesion.id_bitacora, int)
        servicio.cerrar_sesion(sesion)
        fila = BitacoraRepositorio().listar()[0]
        self.assertIsInstance(fila["entrada"], datetime)
        self.assertIsNotNone(fila["salida"])

    def test_bitacora_hasta_incluye_todo_el_dia(self):
        id_admin = _fetchall(
            "SELECT id_usuario FROM usuario WHERE nombre_usuario = 'admin'")[0][0]
        con = obtener_conexion()
        try:
            con.cursor().execute(
                "INSERT INTO bitacora (id_usuario, fecha_hora_entrada) VALUES (?, ?)",
                id_admin, datetime(2026, 11, 5, 23, 59, 0))
            con.commit()
        finally:
            con.close()
        repo = BitacoraRepositorio()
        self.assertEqual(len(repo.listar(None, date(2026, 11, 5), date(2026, 11, 5))), 1)
        self.assertEqual(len(repo.listar(None, date(2026, 11, 6), None)), 0)
        self.assertEqual(len(repo.listar(None, None, date(2026, 11, 4))), 0)

    def test_la_base_sigue_impidiendo_un_segundo_administrador(self):
        datos = {"nombre_usuario": "otro_admin", "nombre": "Otro", "apellido": "Admin",
                 "contrasena_hash": "x", "numero_documento": "99999999", "id_rol": 1,
                 "id_tipo_documento": 1, "estado": True, "creado_por": None}
        with self.assertRaisesRegex(ValueError, "Ya existe un Administrador"):
            UsuarioRepositorio().insertar_usuario(datos)

    def test_oferta_con_decimal_exacto_y_consulta_sobre_el_promedio(self):
        id_proveedor, nit = _fetchall(
            "SELECT p.id_proveedor, p.nit FROM proveedor p WHERE NOT EXISTS "
            "(SELECT 1 FROM proveedor_producto pp WHERE pp.id_proveedor = p.id_proveedor)"
        )[0]
        repo = ProveedorProductoRepositorio()
        repo.insertar(ProveedorProducto(id_proveedor, 1, Decimal("999999.99"), 1, True))
        oferta = next(o for o in repo.listar()
                      if o.id_proveedor == id_proveedor and o.id_producto == 1)
        self.assertIsInstance(oferta.precio_unitario, Decimal)
        self.assertEqual(oferta.precio_unitario, Decimal("999999.99"))
        _, filas = ConsultaRepositorio().ejecutar("proveedores_precio_sobre_promedio")
        self.assertIn(nit, [f[0] for f in filas])

    def test_las_cinco_consultas_y_los_reportes_ejecutan(self):
        for clave in ConsultaRepositorio._CONSULTAS:
            with self.subTest(clave):
                columnas, filas = ConsultaRepositorio().ejecutar(clave)
                self.assertTrue(columnas)
                if clave == "productos_sin_proveedor":
                    self.assertEqual(len(filas), 1)

        r = ReporteRepositorio()
        self.assertIsNotNone(r.obtener_proveedor(1))
        self.assertIsNotNone(r.obtener_producto(1))
        self.assertIsNotNone(r.obtener_categoria(1))
        self.assertIsNotNone(r.obtener_ciudad(1))
        self.assertTrue(r.productos_de_proveedor(1))
        self.assertTrue(r.proveedores_de_producto(1))
        self.assertTrue(r.productos_de_categoria(1))
        por_ciudad = r.proveedores_por_ubicacion(id_ciudad=1)
        por_depto = r.proveedores_por_ubicacion(departamento="Quindío")
        self.assertEqual(len(por_ciudad), len(por_depto))
        self.assertTrue(any(f[4] is None for f in por_ciudad))   # proveedor sin productos
        self.assertEqual(sum(c for _, c in r.cantidad_por_categoria()), 10)
        self.assertEqual(sum(c for _, c in r.cantidad_por_categoria(True)), 9)
        self.assertEqual(sum(c for _, c in r.cantidad_por_categoria(False)), 1)


if __name__ == "__main__":
    unittest.main()