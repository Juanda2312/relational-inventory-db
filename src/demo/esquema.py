ESQUEMA = """
CREATE TABLE ciudad (
    id_ciudad    INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre       TEXT NOT NULL COLLATE NOCASE_UNICODE,
    departamento TEXT NOT NULL COLLATE NOCASE_UNICODE
);

CREATE TABLE categoria (
    id_categoria INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre       TEXT NOT NULL UNIQUE COLLATE NOCASE_UNICODE,
    descripcion  TEXT,
    estado       INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE tipo_documento (
    id_tipo_documento INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre            TEXT NOT NULL UNIQUE COLLATE NOCASE_UNICODE,
    descripcion       TEXT
);

CREATE TABLE rol (
    id_rol      INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre      TEXT NOT NULL UNIQUE COLLATE NOCASE_UNICODE,
    descripcion TEXT
);

CREATE TABLE proveedor (
    id_proveedor INTEGER PRIMARY KEY AUTOINCREMENT,
    nit          TEXT NOT NULL UNIQUE COLLATE NOCASE_UNICODE,
    nombre       TEXT NOT NULL COLLATE NOCASE_UNICODE,
    direccion    TEXT,
    estado       INTEGER NOT NULL DEFAULT 1,
    telefono     TEXT,
    correo       TEXT COLLATE NOCASE_UNICODE,
    id_ciudad    INTEGER NOT NULL REFERENCES ciudad (id_ciudad)
);

CREATE TABLE producto (
    id_producto   INTEGER PRIMARY KEY AUTOINCREMENT,
    codigo        TEXT NOT NULL UNIQUE COLLATE NOCASE_UNICODE,
    nombre        TEXT NOT NULL COLLATE NOCASE_UNICODE,
    descripcion   TEXT,
    unidad_medida TEXT COLLATE NOCASE_UNICODE,
    estado        INTEGER NOT NULL DEFAULT 1,
    id_categoria  INTEGER NOT NULL REFERENCES categoria (id_categoria)
);

CREATE TABLE proveedor_producto (
    id_proveedor    INTEGER NOT NULL REFERENCES proveedor (id_proveedor),
    id_producto     INTEGER NOT NULL REFERENCES producto (id_producto),
    precio_unitario DECIMAL(12,2) NOT NULL,
    dias_entrega    INTEGER NOT NULL DEFAULT 0,
    estado          INTEGER NOT NULL DEFAULT 1,
    PRIMARY KEY (id_proveedor, id_producto)
);

CREATE TABLE usuario (
    id_usuario        INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre_usuario    TEXT NOT NULL UNIQUE COLLATE NOCASE_UNICODE,
    nombre            TEXT NOT NULL COLLATE NOCASE_UNICODE,
    apellido          TEXT NOT NULL COLLATE NOCASE_UNICODE,
    contrasena_hash   TEXT NOT NULL,
    estado            INTEGER NOT NULL DEFAULT 1,
    correo            TEXT COLLATE NOCASE_UNICODE,
    telefono          TEXT,
    numero_documento  TEXT NOT NULL COLLATE NOCASE_UNICODE,
    id_rol            INTEGER NOT NULL REFERENCES rol (id_rol),
    id_tipo_documento INTEGER NOT NULL REFERENCES tipo_documento (id_tipo_documento),
    creado_por        INTEGER REFERENCES usuario (id_usuario)
);

CREATE TABLE bitacora (
    id_bitacora        INTEGER PRIMARY KEY AUTOINCREMENT,
    id_usuario         INTEGER NOT NULL REFERENCES usuario (id_usuario),
    fecha_hora_entrada DATETIME2(0) NOT NULL,
    fecha_hora_salida  DATETIME2(0)
);

-- Un solo Administrador (rol 1): índice único parcial, igual que en SQL Server.
CREATE UNIQUE INDEX UX_usuario_un_administrador ON usuario (id_rol) WHERE id_rol = 1;
"""