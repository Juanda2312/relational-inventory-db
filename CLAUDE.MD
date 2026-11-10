# Demo SQLite + .exe Implementation Plan
 
> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.
 
**Goal:** Que cualquiera descargue un `.exe` desde un Release de GitHub, lo abra y use la app de proveedores sin instalar Docker, SQL Server ni ODBC.
 
**Architecture:** En el **fork** (el repo original queda intacto porque necesita SQL Server por temas académicos) se reemplaza solo la capa de conexión: un adaptador sobre `sqlite3` con la misma forma de uso que `pyodbc` (`execute(sql, *params)`, filas con acceso por atributo). Vistas, controladores y servicios no se tocan, salvo detalles puntuales (mensaje en el login, carpeta de reportes). La base se crea sola en la primera ejecución, con datos de ejemplo, y se empaqueta con PyInstaller.
 
**Tech Stack:** Python 3 (`sqlite3`, `tkinter`), `reportlab`, `pymupdf`, PyInstaller (solo para compilar), `unittest`, `gh` (GitHub CLI, opcional).
 
**Spec:** conversación del 2026-11-10 (opción 2 «versión demo ejecutable»); no hay documento de diseño aparte, los requisitos están en *Global Constraints*.
 
## Global Constraints
 
- Se trabaja **solo en el fork**. No se modifica el repo original (`ShanT237/relational-inventory-db`).
- Solo biblioteca estándar de Python + `reportlab` + `pymupdf` en tiempo de ejecución (el enunciado académico prohíbe frameworks). PyInstaller solo se usa para compilar.
- Todo el SQL sigue parametrizado con `?` (sin concatenar valores).
- Los nombres de tablas y columnas son los del `diccionario-de-datos.md` (los 9 repositorios no cambian de consultas salvo lo indicado).
- Credenciales demo exactas: `admin` / `admin1234` (Administrador), `tradicional` / `demo1234` (Tradicional), `esporadico` / `demo1234` (Esporadico, sin tilde, como en `02_datos_iniciales.sql`).
- Los datos de la demo viven en la carpeta de datos del usuario, **nunca junto al `.exe`**: `%LOCALAPPDATA%\ProveedoresDemo` en Windows (`~/.proveedores_demo` en otros sistemas), sobrescribible con la variable de entorno `DATOS_DEMO_DIR`.
- Ejecutable: `ProveedoresDemo.exe`, un solo archivo, Windows x64, publicado como asset de un Release (no se sube al repo).
- Seguir mostrando en el README la autoría de los tres integrantes y el enlace al repo original.
## Review Focus
 
1. `demo.db` ya existe pero está vacío (0 bytes, p. ej. una ejecución interrumpida): se debe inicializar, no fallar con «no such table».
2. Abrir la app dos veces seguidas no duplica datos ni pisa los cambios que hizo el visitante.
3. Ruta de datos con espacios y tilde (usuario de Windows tipo `José Pérez`): la base se crea y se abre igual.
4. Filtro `hasta` de la bitácora incluye todo ese día (una entrada a las 23:59 del día `hasta` aparece).
5. Precios con 2 decimales (`2500.50`) vuelven como `Decimal` exacto y la consulta «precio sobre el promedio» sigue funcionando.
---
 
### Task 1: Capa de conexión SQLite
 
**Files:**
- Create: `src/configuracion/rutas.py`
- Create: `src/repositorios/conexion.py`
- Test: `tests/test_conexion.py`
**Interfaces:**
- Consumes: nada.
- Produces:
  - `rutas.carpeta_datos() -> Path` (lee `DATOS_DEMO_DIR` en cada llamada; **no** crea la carpeta) y `rutas.ruta_bd() -> Path` (`carpeta_datos() / "demo.db"`).
  - `conexion.obtener_conexion() -> Conexion`. `Conexion` tiene `cursor() -> Cursor`, `executescript(sql: str) -> None`, `commit()`, `rollback()`, `close()`.
  - `Cursor` tiene `execute(sql: str, *parametros) -> Cursor` (parámetros posicionales sueltos, como `pyodbc`), `fetchone()`, `fetchall()`, `description`, `rowcount`, `lastrowid`.
  - Las filas son `namedtuple`: acceso por atributo (`fila.nombre`), por índice (`fila[0]`) y `tuple(fila)`.
  - `obtener_conexion()` crea la carpeta de datos si no existe y activa `PRAGMA foreign_keys = ON`.
- [ ] **Step 1: Escribir las pruebas que fallan**
En `tests/test_conexion.py` (`setUp`: carpeta temporal cuyo nombre lleva espacio y `ñ`, p. ej. `tempfile.mkdtemp(prefix="demo ñ ")`, asignada a `os.environ["DATOS_DEMO_DIR"]`, con limpieza que la borra y restaura la variable):
 
```python
def test_ruta_con_espacios_y_tilde(self):
    con = obtener_conexion(); con.close()
    self.assertEqual(ruta_bd().parent, Path(self.dir))
    self.assertTrue(ruta_bd().exists())
 
def test_parametros_posicionales_estilo_pyodbc_y_filas_con_atributos(self):
    # tabla t(a INTEGER, b TEXT); INSERT con cur.execute(sql, 1, "x")
    fila = cur.execute("SELECT a, b FROM t WHERE a = ?", 1).fetchone()
    self.assertEqual((fila.a, fila[1], tuple(fila)), (1, "x", (1, "x")))
 
def test_columnas_repetidas_o_calculadas_no_rompen(self):
    fila = cur.execute("SELECT 1 AS nombre, 2 AS nombre, COUNT(*) FROM t").fetchone()
    self.assertEqual((fila[0], fila[1]), (1, 2))
    self.assertEqual(cur.description[0][0], "nombre")
 
def test_decimal_y_datetime_ida_y_vuelta(self):
    # tabla t2(p DECIMAL(12,2), f DATETIME2(0)); se inserta Decimal("2500.50") y
    # datetime(2026, 11, 10, 9, 5, 7, 123456)
    self.assertIsInstance(fila.p, Decimal)
    self.assertEqual(fila.p, Decimal("2500.50"))
    self.assertEqual(fila.f, datetime(2026, 11, 10, 9, 5, 7))
 
def test_claves_foraneas_activas(self):
    self.assertEqual(cur.execute("PRAGMA foreign_keys").fetchone()[0], 1)
```
 
- [ ] **Step 2: Ver que fallan**
Run: `python -m unittest tests.test_conexion -v`
Expected: `ModuleNotFoundError: No module named 'repositorios.conexion'`
 
- [ ] **Step 3: Implementar `rutas.py` y `conexion.py` con las firmas de *Interfaces***
Decisiones que no se deducen de las pruebas:
- `sqlite3.connect(..., detect_types=sqlite3.PARSE_DECLTYPES)`; registrar adaptador `Decimal -> str` y convertidor `"DECIMAL" -> Decimal`; adaptadores `datetime`/`date` que escriben `YYYY-MM-DD HH:MM:SS` (sin microsegundos) y convertidor `"DATETIME2" -> datetime.fromisoformat`. (No depender de los adaptadores por defecto, están deprecados desde Python 3.12.)
- `Cursor.execute` hace `self._c.execute(sql, parametros)`: `sqlite3` exige una secuencia, `pyodbc` acepta sueltos.
- `row_factory` crea `namedtuple(..., rename=True)`: sin `rename=True` falla con `COUNT(*)` y con columnas repetidas (`nombre`, `nombre`).
- [ ] **Step 4: Ver que pasan**
Run: `python -m unittest tests.test_conexion -v`
Expected: 5 tests `ok`.
 
- [ ] **Step 5: Commit**
```powershell
git add src/configuracion/rutas.py src/repositorios/conexion.py tests/test_conexion.py
git commit -m "feat: capa de conexión SQLite con la misma interfaz de uso que pyodbc"
```
 
---
 
### Task 2: Esquema SQLite y datos demo
 
**Files:**
- Create: `src/demo/__init__.py` (vacío), `src/demo/esquema.py`, `src/demo/datos.py`, `src/demo/base.py`
- Test: `tests/test_base_demo.py`
**Interfaces:**
- Consumes: `obtener_conexion()`, `ruta_bd()` (Task 1); `SeguridadServicio().cifrar(contrasena) -> str` (existente).
- Produces:
  - `esquema.ESQUEMA: str`: script SQLite con las 9 tablas del diccionario de datos (`INTEGER PRIMARY KEY AUTOINCREMENT`, `TEXT`; mantener los tipos declarados `DECIMAL(12,2)` y `DATETIME2(0)` para que actúen los convertidores) y el índice único parcial `UX_usuario_un_administrador ON usuario(id_rol) WHERE id_rol = 1`.
  - `datos.CREDENCIALES_DEMO: dict[str, str]` (los tres usuarios de *Global Constraints*) y `datos.cargar_datos_demo(con: Conexion) -> None`. Inserta roles en este orden (Administrador=1, Tradicional=2, Esporadico=3), los 3 tipos de documento de `02_datos_iniciales.sql` y los usuarios demo con hash real (`creado_por` = id del admin para los otros dos).
  - `base.asegurar_base() -> None`: crea la carpeta de datos; si la tabla `rol` no existe (archivo nuevo **o vacío**), ejecuta `ESQUEMA` y `cargar_datos_demo`. Si ya existe, no hace nada.
- Cantidades que fija el seed: 5 ciudades, 4 categorías, 6 proveedores, 10 productos, 14 ofertas (`proveedor_producto`), 3 usuarios, 0 bitácoras. Casos para consultas y reportes: exactamente **1** producto sin ofertas, exactamente **1** proveedor sin ofertas, al menos **1** producto inactivo y al menos **1** oferta inactiva. Ciudades de Colombia reales (incluye Armenia, Quindío).
- [ ] **Step 1: Escribir las pruebas que fallan**
`tests/test_base_demo.py` (mismo `setUp` con `DATOS_DEMO_DIR` temporal; las consultas se hacen con `obtener_conexion()`):
 
```python
def test_crea_esquema_y_datos(self):
    asegurar_base()
    esperado = {"rol": 3, "tipo_documento": 3, "usuario": 3, "ciudad": 5, "categoria": 4,
                "proveedor": 6, "producto": 10, "proveedor_producto": 14, "bitacora": 0}
    # SELECT COUNT(*) de cada tabla == esperado
 
def test_administrador_es_rol_1_y_la_base_impide_un_segundo(self):
    # SELECT id_rol FROM rol WHERE nombre='Administrador' -> 1
    # INSERT directo de otro usuario con id_rol=1 -> assertRaises(sqlite3.IntegrityError)
 
def test_casos_para_consultas_y_reportes(self):
    # productos sin oferta == 1; proveedores sin oferta == 1;
    # producto.estado=0 >= 1; proveedor_producto.estado=0 >= 1
 
def test_es_idempotente_y_no_pisa_cambios(self):
    asegurar_base()
    # UPDATE categoria SET nombre='Cambiada' WHERE id_categoria=1
    asegurar_base()
    # conteos iguales a los de arriba y nombre sigue 'Cambiada'
 
def test_archivo_vacio_se_inicializa(self):
    ruta_bd().parent.mkdir(parents=True, exist_ok=True); ruta_bd().write_bytes(b"")
    asegurar_base()   # luego COUNT(*) de rol == 3
 
def test_credenciales_demo_verifican_contra_el_hash_guardado(self):
    # para cada usuario de CREDENCIALES_DEMO: SeguridadServicio().verificar(clave, hash) es True
    # y su rol (JOIN rol) es Administrador / Tradicional / Esporadico respectivamente
```
 
- [ ] **Step 2: Ver que fallan**
Run: `python -m unittest tests.test_base_demo -v`
Expected: `ModuleNotFoundError: No module named 'demo'`
 
- [ ] **Step 3: Implementar `esquema.py`, `datos.py` y `base.py` con las firmas de *Interfaces***
El esquema y el seed van como constantes/funciones de Python (no como `.sql` sueltos) para que PyInstaller los incluya sin `--add-data`.
 
- [ ] **Step 4: Ver que pasan**
Run: `python -m unittest tests.test_base_demo -v`
Expected: 6 tests `ok`.
 
- [ ] **Step 5: Commit**
```powershell
git add src/demo tests/test_base_demo.py
git commit -m "feat: esquema SQLite y datos de ejemplo que se crean en la primera ejecución"
```
 
---
 
### Task 3: Repositorios sobre SQLite
 
**Files:**
- Modify: los 9 de `src/repositorios/` que importan la conexión: `bitacora_repositorio.py`, `categoria_repositorio.py`, `ciudad_repositorio.py`, `consulta_repositorio.py`, `producto_repositorio.py`, `proveedor_producto_repositorio.py`, `proveedor_repositorio.py`, `reporte_repositorio.py`, `usuario_repositorio.py`
- Test: `tests/test_repositorios_demo.py`
**Interfaces:**
- Consumes: `obtener_conexion()` (Task 1), `asegurar_base()`, `CREDENCIALES_DEMO` (Task 2).
- Produces: los repositorios con las **mismas firmas y retornos de siempre** (`BitacoraRepositorio.listar/registrar_entrada/registrar_salida`, `UsuarioRepositorio.*`, `ConsultaRepositorio.ejecutar`, `ReporteRepositorio.*`, etc.).
- [ ] **Step 1: Escribir las pruebas que fallan**
`tests/test_repositorios_demo.py` (`setUp`: `DATOS_DEMO_DIR` temporal + `asegurar_base()`):
 
```python
def test_login_y_cierre_de_sesion_con_las_credenciales_demo(self):
    servicio = AutenticacionServicio(UsuarioRepositorio(), BitacoraRepositorio(), SeguridadServicio())
    sesion = servicio.iniciar_sesion("admin", "admin1234")
    self.assertEqual(sesion.rol, "Administrador")
    self.assertIsInstance(sesion.id_bitacora, int)
    servicio.cerrar_sesion(sesion)
    fila = BitacoraRepositorio().listar()[0]
    self.assertIsInstance(fila["entrada"], datetime)
    self.assertIsNotNone(fila["salida"])
 
def test_bitacora_hasta_incluye_todo_el_dia(self):
    # INSERT directo de una entrada del admin el 2026-11-05 23:59:00
    self.assertEqual(len(repo.listar(None, date(2026, 11, 5), date(2026, 11, 5))), 1)
    self.assertEqual(len(repo.listar(None, date(2026, 11, 6), None)), 0)
    self.assertEqual(len(repo.listar(None, None, date(2026, 11, 4))), 0)
 
def test_la_base_sigue_impidiendo_un_segundo_administrador(self):
    # insertar_usuario con id_rol=1 -> assertRaisesRegex(ValueError, "Ya existe un Administrador")
 
def test_oferta_con_decimal_exacto_y_consulta_sobre_el_promedio(self):
    # al proveedor sin ofertas (buscarlo por SQL) se le inserta una oferta Decimal("999999.99")
    self.assertEqual(listar()[...].precio_unitario, Decimal("999999.99"))
    _, filas = ConsultaRepositorio().ejecutar("proveedores_precio_sobre_promedio")
    self.assertIn(nit_de_ese_proveedor, [f[0] for f in filas])
 
def test_las_cinco_consultas_y_los_reportes_ejecutan(self):
    # las 5 claves de ConsultaRepositorio._CONSULTAS: columnas no vacías;
    # "productos_sin_proveedor" devuelve exactamente 1 fila
    # cada método de ReporteRepositorio con ids existentes devuelve lista sin error;
    # cantidad_por_categoria() suma 10 productos en total
```
 
- [ ] **Step 2: Ver que fallan**
Run: `python -m unittest tests.test_repositorios_demo -v`
Expected: FAIL (`ModuleNotFoundError: No module named 'pyodbc'` o `repositorios.conexion_sqlserver`).
 
- [ ] **Step 3: Cambiar el import en los 9 repositorios**
Reemplazo global en `src/repositorios/` (VS Code: Ctrl+Shift+H): `repositorios.conexion_sqlserver` → `repositorios.conexion`. Debe tocar 9 archivos.
 
- [ ] **Step 4: Adaptar lo que es propio de SQL Server**
- `BitacoraRepositorio.registrar_entrada`: `INSERT INTO bitacora (id_usuario, fecha_hora_entrada) VALUES (?, ?)` con `datetime.now()` y devolver `cur.lastrowid` (sin `SYSDATETIME()` ni `OUTPUT INSERTED`).
- `BitacoraRepositorio.registrar_salida`: parámetro `datetime.now()` en vez de `SYSDATETIME()`.
- `BitacoraRepositorio.listar`: `desde` → `datetime.combine(desde, time.min)` con `>=`; `hasta` → `datetime.combine(hasta + timedelta(days=1), time.min)` con `<` (sin `DATEADD`).
- `UsuarioRepositorio._bloquear_roles`: quitar `WITH (TABLOCKX, HOLDLOCK)` (el `SELECT nombre FROM rol WHERE id_rol = ?` se queda).
- [ ] **Step 5: Ver que pasan**
Run: `python -m unittest tests.test_repositorios_demo -v`
Expected: 5 tests `ok`.
 
- [ ] **Step 6: Commit**
```powershell
git add src/repositorios tests/test_repositorios_demo.py
git commit -m "feat: repositorios funcionan sobre SQLite (bitácora, usuarios y consultas)"
```
 
---
 
### Task 4: Arranque de la demo y limpieza del fork
 
**Files:**
- Modify: `src/main.py`, `src/vistas/login_vista.py`, `requirements.txt`, `.gitignore`
- Create: `requirements-build.txt`
- Delete: `src/repositorios/conexion_sqlserver.py`, `src/configuracion/configuracion.py`, `src/configuracion/configuracion_local.ejemplo.py`, `src/crear_admin.py`, `restaurar-bd.ps1`, `docker-compose.yml`, `.env.example`, `db/`
- Conservar: `sql/`, `diccionario-de-datos.md`, `docs/` (documentación del diseño original).
**Interfaces:**
- Consumes: `asegurar_base()`, `CREDENCIALES_DEMO`.
- Produces: la app arranca con `python src/main.py` sin SQL Server.
- [ ] **Step 1: `main.py` llama `asegurar_base()` antes del login**
Si lanza una excepción, mostrar `messagebox.showerror("Gestión de Proveedores", ...)` con el mensaje y salir (con `--windowed` el `.exe` no tiene consola; sin el cuadro el visitante vería que «no pasa nada»). Para el cuadro hace falta una raíz `tk.Tk()` oculta (`withdraw()`).
 
- [ ] **Step 2: Pista de credenciales en el login**
En `login_vista.py`, bajo «Ingresa tus credenciales para continuar.», una etiqueta `Suave.Tarjeta.TLabel` con tres líneas generadas desde `CREDENCIALES_DEMO`, p. ej. `Demo · admin / admin1234 (Administrador)`. Sin cambiar el ancho de la ventana.
 
- [ ] **Step 3: Dependencias y limpieza**
- `requirements.txt`: dejar `reportlab>=4.0` y `pymupdf>=1.24` (quitar `pyodbc`).
- `requirements-build.txt`: `-r requirements.txt` y `pyinstaller>=6.0`.
- `.gitignore`: añadir `build/`, `dist/`, `*.spec`.
- Borrar los archivos de la lista **Delete**.
- [ ] **Step 4: Verificar**
Run: `python -m unittest discover -s tests -t . -v`
Expected: todas `ok` (incluye `test_generador_pdf` y `test_reporte_servicio`, que ya existían).
 
Run: `python -c "import sys; sys.path.insert(0,'src'); import main"`
Expected: sin salida ni errores.
 
Prueba manual con base limpia:
```powershell
$env:DATOS_DEMO_DIR = "$env:TEMP\demo-smoke"; python src/main.py
```
Expected: abre el login con la pista de credenciales; `admin` ve Entidades, Transacciones, Consultas, Reportes y Auditoría; `esporadico` solo ve Consultas; `tradicional` no ve Auditoría; crear una ciudad y cerrar sesión funciona; Auditoría → Bitácora muestra las sesiones.
 
- [ ] **Step 5: Commit**
```powershell
git add -A
git commit -m "feat: la app arranca en modo demo sin SQL Server; se retiran Docker y pyodbc"
```
 
---
 
### Task 5: Empaquetado y Release
 
**Files:**
- Modify: `src/servicios/generador_pdf.py` (constante `CARPETA_REPORTES`), `src/vistas/reportes_vista.py` (constante `CARPETA_REPORTES`)
**Interfaces:**
- Consumes: `carpeta_datos()` (Task 1).
- Produces: `dist/ProveedoresDemo.exe` y un Release `v1.0-demo` con ese archivo.
- [ ] **Step 1: Mover la carpeta de reportes**
En ambos archivos, `CARPETA_REPORTES = carpeta_datos() / "reportes"`. Motivo: dentro del `.exe` de un solo archivo, `Path(__file__).parents[2]` apunta a una carpeta temporal que se borra al cerrar, y el «Guardar como…» se abriría ahí.
 
Run: `python -m unittest discover -s tests -t . -v`
Expected: todas `ok`.
 
- [ ] **Step 2: Compilar**
```powershell
pip install -r requirements-build.txt
pyinstaller --noconfirm --onefile --windowed --name ProveedoresDemo --paths src src/main.py
```
Expected: se crea `dist\ProveedoresDemo.exe`.
 
- [ ] **Step 3: Probar el `.exe` como un visitante nuevo**
```powershell
Remove-Item "$env:LOCALAPPDATA\ProveedoresDemo" -Recurse -ErrorAction SilentlyContinue
```
Copiar el `.exe` a una carpeta con espacios (p. ej. `C:\Prueba demo\`) y abrirlo con doble clic. Expected: login → `admin` / `admin1234` → Reportes → «Productos de un proveedor» → elegir proveedor → **Generar PDF** muestra la vista previa → **Descargar** guarda y abre el PDF → cerrar y volver a abrir conserva los datos.
 
Si la vista previa dice «Falta la librería PyMuPDF», recompilar añadiendo `--collect-all pymupdf`. Si Windows Defender marca el archivo, compilar con `--onedir` y publicar un `.zip` de la carpeta `dist\ProveedoresDemo`.
 
- [ ] **Step 4: Publicar el Release (el `.exe` va como asset, no en el repo)**
```powershell
gh release create v1.0-demo dist\ProveedoresDemo.exe --title "Demo v1.0 (sin instalación)" --notes "Descarga y abre ProveedoresDemo.exe. Usuario demo: admin / admin1234."
```
Sin `gh`: GitHub → Releases → Draft a new release → arrastrar el `.exe`. Expected: la página del Release muestra `ProveedoresDemo.exe`; al descargarlo desde ahí y abrirlo en una carpeta nueva funciona igual que en el Step 3.
 
- [ ] **Step 5: Commit**
```powershell
git add src/servicios/generador_pdf.py src/vistas/reportes_vista.py .gitignore
git commit -m "chore: reportes en la carpeta de datos del usuario y build del .exe"
git push
```
 
---
 
### Task 6: README de la demo y enlace desde el portafolio
 
**Files:**
- Modify: `README.md` (del fork); en el repo `Juanda2312/portafolio`, el archivo donde está la tarjeta del proyecto.
**Interfaces:**
- Consumes: el Release `v1.0-demo` (Task 5).
- Produces: un enlace de descarga visible desde el portafolio.
- [ ] **Step 1: Sección al inicio del README del fork**
Debe incluir: botón/enlace a `https://github.com/Juanda2312/relational-inventory-db/releases/latest` (ajusta si renombraste el fork); credenciales demo de los 3 roles; aviso de que Windows puede mostrar «Windows protegió tu PC» (archivo sin firmar): *Más información → Ejecutar de todas formas*; dónde se guardan los datos y cómo reiniciarlos (borrar `%LOCALAPPDATA%\ProveedoresDemo`); una línea que diga que esta es la versión demo con SQLite y que el proyecto original con SQL Server está en `ShanT237/relational-inventory-db`. Se mantienen la línea de **Integrantes** y las secciones de diseño existentes.
 
- [ ] **Step 2: Enlazar desde el portafolio**
En el repo del portafolio: `Select-String -Path . -Pattern "Proveedores" -Recurse` para encontrar la tarjeta del proyecto y añadir un botón «Descargar demo (.exe)» hacia el Release (y el video si haces la opción 1).
 
- [ ] **Step 3: Verificar**
Abrir la página del portafolio publicada. Expected: el botón lleva al Release y baja el `.exe`.
 
- [ ] **Step 4: Commit (uno por repo)**
```powershell
# en el fork
git add README.md
git commit -m "docs: README de la versión demo con enlace de descarga"
git push
 
# en el repo del portafolio
git add -A
git commit -m "feat: enlace de descarga de la demo de proveedores"
git push
```