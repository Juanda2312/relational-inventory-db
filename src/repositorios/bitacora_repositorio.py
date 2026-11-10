"""Repositorio: acceso a la tabla bitacora."""
from datetime import datetime, time, timedelta

from repositorios.conexion import obtener_conexion


class BitacoraRepositorio:

    def listar(self, nombre_usuario=None, desde=None, hasta=None):
        """Lista accesos con usuario y rol, filtrados por usuario y fechas opcionales."""
        condiciones = []
        parametros = []
        if nombre_usuario:
            condiciones.append("u.nombre_usuario = ?")
            parametros.append(nombre_usuario)
        if desde:
            condiciones.append("b.fecha_hora_entrada >= ?")
            parametros.append(datetime.combine(desde, time.min))
        if hasta:
            # «hasta» incluye todo ese día: se compara contra la medianoche siguiente
            condiciones.append("b.fecha_hora_entrada < ?")
            parametros.append(datetime.combine(hasta + timedelta(days=1), time.min))
        where = " WHERE " + " AND ".join(condiciones) if condiciones else ""

        con = obtener_conexion()
        try:
            cur = con.cursor()
            cur.execute(
                """SELECT b.id_bitacora, u.nombre_usuario, u.nombre, u.apellido,
                          r.nombre AS rol, b.fecha_hora_entrada, b.fecha_hora_salida
                   FROM bitacora b
                   JOIN usuario u ON u.id_usuario = b.id_usuario
                   JOIN rol r ON r.id_rol = u.id_rol""" + where +
                " ORDER BY b.fecha_hora_entrada DESC",
                *parametros,
            )
            return [{
                "id_bitacora": fila.id_bitacora,
                "nombre_usuario": fila.nombre_usuario,
                "usuario": f"{fila.nombre} {fila.apellido}",
                "rol": fila.rol,
                "entrada": fila.fecha_hora_entrada,
                "salida": fila.fecha_hora_salida,
            } for fila in cur.fetchall()]
        finally:
            con.close()

    def registrar_entrada(self, id_usuario):
        """Crea el registro con fecha y hora de entrada. Devuelve su id."""
        con = obtener_conexion()
        try:
            cur = con.cursor()
            cur.execute(
                "INSERT INTO bitacora (id_usuario, fecha_hora_entrada) VALUES (?, ?)",
                id_usuario, datetime.now(),
            )
            id_bitacora = cur.lastrowid
            con.commit()
            return id_bitacora
        finally:
            con.close()

    def registrar_salida(self, id_bitacora):
        """Completa la fecha y hora de salida del registro."""
        con = obtener_conexion()
        try:
            cur = con.cursor()
            cur.execute(
                "UPDATE bitacora SET fecha_hora_salida = ? WHERE id_bitacora = ?",
                datetime.now(), id_bitacora,
            )
            con.commit()
        finally:
            con.close()