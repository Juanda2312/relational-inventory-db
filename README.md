# Sistema de Gestión de Proveedores y Productos

Proyecto final de **Bases de Datos I** — Programa de Ingeniería de Sistemas y Computación, Universidad del Quindío (2026-II).

**Integrantes:** Juan David Tapiero, Santiago Torres, Jose Manuel Bedoya

> **Versión demo.** Este repositorio es un fork del proyecto original, adaptado para que cualquiera lo pruebe sin instalar nada. El proyecto académico con **Microsoft SQL Server** está en [ShanT237/relational-inventory-db](https://github.com/ShanT237/relational-inventory-db).

## Prueba la demo (sin instalar nada)

[**Descargar ProveedoresDemo.exe**](https://github.com/Juanda2312/relational-inventory-db/releases/latest) (Windows x64, un solo archivo)

No necesitas Docker, SQL Server, ODBC ni Python. Descárgalo y ábrelo con doble clic.

| Usuario | Contraseña | Rol | Qué puede hacer |
|---------|------------|-----|-----------------|
| `admin` | `admin1234` | Administrador | Todo, incluida la gestión de usuarios y la bitácora |
| `tradicional` | `demo1234` | Tradicional | Entidades, transacciones, consultas y reportes |
| `esporadico` | `demo1234` | Esporádico | Solo consultas |

**Windows puede mostrar «Windows protegió tu PC».** El archivo no está firmado digitalmente. Pulsa *Más información* → *Ejecutar de todas formas*.

**Dónde se guardan los datos.** En `%LOCALAPPDATA%\ProveedoresDemo` (la base `demo.db` y la carpeta `reportes`), nunca junto al `.exe`. La base se crea sola la primera vez, con datos de ejemplo. Para volver a empezar, cierra la app y borra esa carpeta. Se puede cambiar la ubicación con la variable de entorno `DATOS_DEMO_DIR`.

## 1. Descripción

Las empresas comerciales necesitan saber a qué proveedores pueden hacer pedidos de sus productos. Este sistema guarda esa información y permite consultarla.

La aplicación registra:

- **Proveedores**, que pueden estar en cualquier ciudad de Colombia.
- **Productos**, con sus datos y la categoría a la que pertenecen.
- **Qué productos puede enviar cada proveedor**, con el precio y los días de entrega. Un proveedor puede proveer varios productos y un producto puede adquirirse con varios proveedores.
- **Usuarios**, con inicio de sesión y permisos según su tipo.
- **Bitácora**, con la fecha y hora de entrada y salida de cada usuario.

## 2. Alcance

Es una **aplicación de escritorio**. El enunciado prohíbe usar frameworks, así que solo se usan la biblioteca estándar de Python y librerías puntuales para generar PDF.

## 3. Tecnologías

| Componente | Tecnología | Uso |
|------------|------------|-----|
| Lenguaje | Python 3 | Lógica de la aplicación |
| Interfaz gráfica | Tkinter (incluido en Python) | Ventanas y formularios |
| Base de datos (demo) | SQLite (`sqlite3`, incluido en Python) | Almacenamiento de datos, se crea sola |
| Base de datos (original) | Microsoft SQL Server | Versión académica, en el repositorio original |
| Reportes | `reportlab` y `pymupdf` | Generar los PDF y mostrar la vista previa |
| Seguridad | `hashlib` (PBKDF2) | Cifrar las contraseñas |
| Empaquetado | PyInstaller | Solo para compilar el `.exe` |

Tkinter, `reportlab` y `pymupdf` son librerías, no frameworks.

La capa de datos es la única que cambia respecto al original: `repositorios/conexion.py` es un adaptador sobre `sqlite3` con la misma forma de uso que `pyodbc` (parámetros posicionales con `?` y filas con acceso por atributo). Vistas, controladores y servicios son los mismos.

## 4. Usuarios y permisos

| Tipo de usuario | Cantidad | Qué puede hacer |
|-----------------|----------|-----------------|
| **Administrador** | Solo 1 | Todo lo del Tradicional, más crear y modificar usuarios y ver la bitácora |
| **Tradicional** | Varios | CRUD de los datos (crear, consultar, modificar, eliminar), consultas y reportes |
| **Esporádico** | Varios | Solo consultas |

Solo el Administrador puede crear usuarios nuevos. Las contraseñas se guardan cifradas. La base impide un segundo Administrador con un índice único parcial.

> **Decisión sobre los reportes:** por ahora el Esporádico **no** genera reportes (el enunciado le deja solo consultas). Si el equipo decide permitírselo, hay que cambiar `requiere_modificar` por `requiere_sesion` en `ReporteServicio.construir` y mostrar la sección Reportes a ese rol en `menu_principal_vista.py`.

## 5. Módulos

| Módulo | Función | Acceso |
|--------|---------|--------|
| **Ingreso** | Inicio de sesión. Valida usuario y contraseña, y abre el registro en la bitácora | Todos |
| **Entidades** | CRUD de ciudades, categorías, proveedores y productos | Administrador, Tradicional |
| **Transacciones** | Asignar a cada proveedor los productos que suministra, con precio y días de entrega | Administrador, Tradicional |
| **Consultas** | Las cinco consultas mínimas del enunciado | Todos |
| **Reportes** | Los cinco reportes en PDF con filtros | Administrador, Tradicional |
| **Auditoría** | Gestión de usuarios y bitácora de entrada y salida | Solo Administrador |

Al iniciar sesión se crea un registro en `bitacora` con la fecha y hora de entrada. Al cerrar sesión se completa la fecha y hora de salida.

## 6. Modelo de datos

La base de datos tiene 9 tablas: `ciudad`, `categoria`, `tipo_documento`, `rol`, `proveedor`, `producto`, `proveedor_producto`, `usuario` y `bitacora`.

- Diagrama entidad-relación: `docs/diagrama-er.drawio`
- Diccionario de datos: [`diccionario-de-datos.md`](diccionario-de-datos.md)
- Documento final (explicación, diagramas y diccionario): [`docs/documento-final.md`](docs/documento-final.md)
- Scripts SQL de **SQL Server** del proyecto original: [`sql/`](sql/). Se conservan como documentación del diseño.
- Esquema y datos de la **demo** (SQLite): `src/demo/esquema.py` y `src/demo/datos.py`.

La relación muchos a muchos entre proveedor y producto se resuelve con la tabla `proveedor_producto`.

## 7. Consultas mínimas

### Consultas con JOIN (3 tablas o más)

1. **Proveedores con su ciudad y los productos que suministran** (`proveedor`, `ciudad`, `proveedor_producto`, `producto`).
2. **Productos con su categoría y los proveedores que los ofrecen, con precio y días de entrega** (`producto`, `categoria`, `proveedor_producto`, `proveedor`).
3. **Bitácora de ingresos con el usuario y su rol** (`bitacora`, `usuario`, `rol`).

```sql
-- Consulta 1
SELECT p.nombre AS proveedor, c.nombre AS ciudad, c.departamento,
       pr.nombre AS producto, pp.precio_unitario
FROM proveedor p
JOIN ciudad c ON c.id_ciudad = p.id_ciudad
JOIN proveedor_producto pp ON pp.id_proveedor = p.id_proveedor
JOIN producto pr ON pr.id_producto = pp.id_producto;
```

### Consultas con subconsultas (2 tablas)

4. **Proveedores que ofrecen productos con precio mayor al promedio** (`proveedor`, `proveedor_producto`).
5. **Productos que no tienen ningún proveedor asignado** (`producto`, `proveedor_producto`).

```sql
-- Consulta 4
SELECT p.nit, p.nombre
FROM proveedor p
WHERE p.id_proveedor IN (
    SELECT pp.id_proveedor
    FROM proveedor_producto pp
    WHERE pp.precio_unitario > (SELECT AVG(precio_unitario) FROM proveedor_producto)
);

-- Consulta 5
SELECT pr.codigo, pr.nombre
FROM producto pr
WHERE NOT EXISTS (
    SELECT 1 FROM proveedor_producto pp WHERE pp.id_producto = pr.id_producto
);
```

## 8. Reportes

Todos se generan en PDF y el usuario elige los filtros en listas desplegables. El PDF se muestra como vista previa dentro de la ventana y el botón **Descargar** lo guarda donde el usuario elija. Lleva encabezado, título, filtros aplicados, tabla, fecha, hora, usuario y número de página.

**Productos y proveedores (3 reportes)**

| Reporte | Filtro del usuario |
|---------|--------------------|
| Productos que suministra un proveedor | Proveedor |
| Proveedores por ciudad con sus productos | Ciudad o departamento |
| Proveedores de un producto con precios | Producto |

**Productos y categorías (2 reportes)**

| Reporte | Filtro del usuario |
|---------|--------------------|
| Productos de una categoría | Categoría |
| Cantidad de productos por categoría | Estado (todos, activos o inactivos) |

## 9. Arquitectura

La aplicación se divide en tres capas:

- **Presentación:** ventanas de Tkinter (`vistas/`) y controladores (`controladores/`). No contiene consultas SQL.
- **Lógica:** reglas del negocio (`servicios/`), como validar permisos y el Administrador único, y la generación de PDF.
- **Datos:** acceso a la base (`repositorios/`). Todas las consultas usan parámetros (`?`) para evitar inyección SQL.

```text
relational-inventory-db/
├── src/
│   ├── main.py             # prepara la base, arma las piezas y arranca la aplicación
│   ├── configuracion/      # rutas de la carpeta de datos del usuario
│   ├── demo/               # esquema SQLite y datos de ejemplo (primera ejecución)
│   ├── dominio/            # entidades y errores del negocio
│   ├── repositorios/       # conexión SQLite y consultas SQL
│   ├── servicios/          # reglas del negocio, permisos y generador de PDF
│   ├── controladores/      # conectan las vistas con los servicios
│   └── vistas/             # ventanas de Tkinter
├── tests/                  # pruebas automáticas (unittest)
├── sql/                    # scripts de SQL Server del proyecto original
├── docs/                   # diagrama-er.drawio y documento-final.md
├── diccionario-de-datos.md
├── requirements.txt        # dependencias de ejecución
├── requirements-build.txt  # dependencias para compilar el .exe
└── README.md
```

## 10. Entregables

- [x] Diagrama entidad-relación
- [x] Diccionario de datos
- [x] Diagrama relacional de tablas normalizado
- [x] Explicación general de la aplicación (este documento y `docs/documento-final.md`)
- [x] Aplicación funcionando: ingreso, entidades, transacciones, consultas, reportes y auditoría

## Ejecutar desde el código fuente

Requiere Python 3 con Tkinter (viene incluido en el instalador oficial de Windows).

```powershell
git clone https://github.com/Juanda2312/relational-inventory-db
cd relational-inventory-db
pip install -r requirements.txt
python src/main.py
```

La primera vez se crea la base de la demo en la carpeta de datos del usuario. Entra con cualquiera de las credenciales de la tabla de arriba.

### Pruebas automáticas

```powershell
python -m unittest discover -s tests -t . -v
```

### Compilar el `.exe`

```powershell
pip install -r requirements-build.txt
pyinstaller --noconfirm --onefile --windowed --name ProveedoresDemo --paths src src/main.py
```

El resultado queda en `dist\ProveedoresDemo.exe`. Si la vista previa de los reportes dice «Falta la librería PyMuPDF», añade `--collect-all pymupdf` al comando. Si Windows Defender marca el archivo, compila con `--onedir` y publica un `.zip` de la carpeta `dist\ProveedoresDemo`.

### Notas

- `DATOS_DEMO_DIR` cambia la carpeta donde se guardan la base y los reportes (útil para pruebas).
- Para volver a los datos de ejemplo, borra la carpeta de datos con la app cerrada.
- Esta versión no usa Docker ni SQL Server. Para ejecutar el proyecto con SQL Server, ve al [repositorio original](https://github.com/ShanT237/relational-inventory-db).