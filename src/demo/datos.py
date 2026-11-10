"""Datos de ejemplo de la demo."""
from decimal import Decimal

from servicios.seguridad_servicio import SeguridadServicio

CREDENCIALES_DEMO = {
    "admin": "admin1234",
    "tradicional": "demo1234",
    "esporadico": "demo1234",
}

_ROLES = [  # el orden fija los ids: Administrador=1, Tradicional=2, Esporadico=3
    ("Administrador", "Único usuario con todos los permisos: crea usuarios y consulta la bitácora"),
    ("Tradicional", "Registra, consulta, modifica y elimina datos, y genera reportes"),
    ("Esporadico", "Solo realiza consultas"),
]

_TIPOS_DOCUMENTO = [
    ("Cedula de ciudadania", "Documento de identidad de los ciudadanos colombianos mayores de edad"),
    ("Cedula de extranjeria", "Documento de identidad de los extranjeros residentes en Colombia"),
    ("Pasaporte", "Documento de identidad para viajes internacionales"),
]

_CIUDADES = [
    ("Armenia", "Quindío"),
    ("Bogotá", "Cundinamarca"),
    ("Medellín", "Antioquia"),
    ("Cali", "Valle del Cauca"),
    ("Pereira", "Risaralda"),
]

_CATEGORIAS = [
    ("Lácteos", "Leche, quesos, yogures y derivados lácteos", 1),
    ("Granos", "Arroz, frijol, lentejas y otros granos secos", 1),
    ("Bebidas", "Jugos, aguas, café y otras bebidas", 1),
    ("Aseo", "Productos de limpieza para el hogar y la empresa", 1),
]

# nit, nombre, direccion, telefono, correo, id_ciudad (el proveedor 6 no tiene ofertas)
_PROVEEDORES = [
    ("900123456-7", "Lácteos del Quindío S.A.S.", "Calle 15 # 12-30", "3101234567",
     "ventas@lacteosquindio.com", 1),
    ("900234567-8", "Distribuidora Andina Ltda", "Carrera 7 # 45-20", "3112345678",
     "pedidos@andina.com", 2),
    ("900345678-9", "Granos y Cereales del Valle", "Avenida 3N # 20-15", "3123456789",
     "contacto@granosvalle.com", 4),
    ("900456789-0", "Bebidas Antioquia S.A.", "Calle 50 # 30-10", "3134567890",
     "ventas@bebidasantioquia.com", 3),
    ("900567890-1", "Aseo Total Pereira", "Carrera 8 # 18-25", "3145678901",
     "info@aseototal.com", 5),
    ("900678901-2", "Agroinsumos El Café S.A.S.", "Carrera 14 # 9-40", "3156789012",
     "agro@elcafe.com", 1),
]

# codigo, nombre, descripcion, unidad, estado, id_categoria
# (el producto 10 no tiene ofertas; el 9 está inactivo)
_PRODUCTOS = [
    ("LAC-001", "Leche entera", "Leche entera pasteurizada", "litro", 1, 1),
    ("LAC-002", "Queso campesino", "Queso fresco campesino", "kg", 1, 1),
    ("LAC-003", "Yogur natural", "Yogur natural sin azúcar", "litro", 1, 1),
    ("GRA-001", "Arroz blanco", "Arroz blanco de grano largo", "kg", 1, 2),
    ("GRA-002", "Frijol cargamanto", "Frijol cargamanto seleccionado", "kg", 1, 2),
    ("BEB-001", "Jugo de naranja", "Jugo de naranja natural", "litro", 1, 3),
    ("BEB-002", "Agua mineral", "Agua mineral sin gas", "litro", 1, 3),
    ("ASE-001", "Detergente en polvo", "Detergente en polvo multiusos", "kg", 1, 4),
    ("ASE-002", "Jabón de barra", "Jabón de barra para ropa", "unidad", 0, 4),
    ("BEB-003", "Café molido", "Café molido tostado medio", "kg", 1, 3),
]

# id_proveedor, id_producto, precio, dias_entrega, estado  (14 ofertas, 2 con decimales)
_OFERTAS = [
    (1, 1, "2800.00", 1, 1), (1, 2, "18500.00", 2, 1), (1, 3, "4200.50", 1, 1),
    (2, 1, "2950.00", 3, 1), (2, 4, "3800.00", 4, 1), (2, 8, "12900.00", 5, 1),
    (3, 4, "3600.00", 2, 1), (3, 5, "7200.00", 3, 1), (3, 2, "19000.00", 6, 0),
    (4, 6, "5400.00", 2, 1), (4, 7, "2500.50", 1, 1), (4, 1, "3100.00", 2, 1),
    (5, 8, "12500.00", 3, 1), (5, 9, "1800.00", 2, 0),
]


def cargar_datos_demo(con):
    """Inserta los datos de ejemplo. No hace commit: lo hace quien llama."""
    cur = con.cursor()
    for fila in _ROLES:
        cur.execute("INSERT INTO rol (nombre, descripcion) VALUES (?, ?)", *fila)
    for fila in _TIPOS_DOCUMENTO:
        cur.execute("INSERT INTO tipo_documento (nombre, descripcion) VALUES (?, ?)", *fila)
    for fila in _CIUDADES:
        cur.execute("INSERT INTO ciudad (nombre, departamento) VALUES (?, ?)", *fila)
    for fila in _CATEGORIAS:
        cur.execute(
            "INSERT INTO categoria (nombre, descripcion, estado) VALUES (?, ?, ?)", *fila)
    for fila in _PROVEEDORES:
        cur.execute(
            "INSERT INTO proveedor (nit, nombre, direccion, telefono, correo, id_ciudad) "
            "VALUES (?, ?, ?, ?, ?, ?)", *fila)
    for fila in _PRODUCTOS:
        cur.execute(
            "INSERT INTO producto (codigo, nombre, descripcion, unidad_medida, estado, "
            "id_categoria) VALUES (?, ?, ?, ?, ?, ?)", *fila)
    for id_prov, id_prod, precio, dias, estado in _OFERTAS:
        cur.execute(
            "INSERT INTO proveedor_producto (id_proveedor, id_producto, precio_unitario, "
            "dias_entrega, estado) VALUES (?, ?, ?, ?, ?)",
            id_prov, id_prod, Decimal(precio), dias, estado)

    seguridad = SeguridadServicio()
    usuarios = [  # nombre_usuario, nombre, apellido, documento, id_rol
        ("admin", "Admin", "Demo", "1000000001", 1),
        ("tradicional", "Tradicional", "Demo", "1000000002", 2),
        ("esporadico", "Esporadico", "Demo", "1000000003", 3),
    ]
    id_admin = None
    for nombre_usuario, nombre, apellido, documento, id_rol in usuarios:
        cur.execute(
            "INSERT INTO usuario (nombre_usuario, nombre, apellido, contrasena_hash, "
            "numero_documento, id_rol, id_tipo_documento, estado, creado_por) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?)",
            nombre_usuario, nombre, apellido,
            seguridad.cifrar(CREDENCIALES_DEMO[nombre_usuario]),
            documento, id_rol, 1, id_admin)
        if id_admin is None:
            id_admin = cur.lastrowid