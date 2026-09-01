# Migración a PostgreSQL - factra_db

El sistema de Punto de Venta ya corre sobre PostgreSQL (`factra_db`).
El archivo `database.db` (SQLite) queda solo como respaldo/origen de los
datos ya migrados; la aplicación no vuelve a leerlo.

## Datos de conexión

| Parámetro   | Valor                     |
|-------------|---------------------------|
| Host        | localhost                 |
| Puerto      | 5432                      |
| Base datos  | `factra_db`               |
| Usuario     | `pos_app`                 |
| Contraseña  | Variable de entorno `POS_DB_PASSWORD` |

> Configura la contraseña mediante variables de entorno o un gestor de
> secretos. No la guardes en el repositorio.

```
postgresql://pos_app:<POS_DB_PASSWORD>@localhost:5432/factra_db
```

## Instalación limpia

La base debe crearse con `pos_app` como propietario y el esquema debe
ejecutarse con ese mismo usuario. No ejecutes `esquema.sql` únicamente como
`postgres`, porque la migración de la aplicación necesita poder agregar
columnas e índices en actualizaciones posteriores.

```text
createdb -O pos_app factra_db
psql -U pos_app -d factra_db -f postgresql/esquema.sql
```

Si el esquema fue instalado por un administrador distinto, transfiere la
propiedad de las tablas y secuencias a `pos_app` antes de ejecutar la
migración, o concede explícitamente esos permisos mediante el procedimiento
de administración de PostgreSQL.

## Cómo quedó conectado el código

El sistema seguía escrito 100% contra la API de `sqlite3` (más de 100
`cur.execute(...)` con placeholders `?` repartidos en ~60 archivos).
En vez de reescribir cada consulta, se creó **`db_conexion.py`** en la
raíz del proyecto: una capa de compatibilidad que expone la misma API
(`connect()`, `.cursor()`, `.execute()`, `sqlite3.Error`, el uso como
`with sqlite3.connect(...) as conn:`) pero habla con PostgreSQL por
detrás (traduce `?` → `%s` y usa psycopg2).

Cada archivo que antes tenía:

```python
import sqlite3
```

ahora tiene:

```python
import db_conexion as sqlite3
```

El resto del código (todas las consultas, los `self.db_name = "database.db"`
que quedaron como valor inerte, el manejo de `sqlite3.Error`, etc.) no
tuvo que tocarse.

## Contenido de esta carpeta

- `esquema.sql` — Script DDL completo (35 tablas, índices y
  validaciones) ya aplicado a `factra_db`.

## Bugs reales que aparecieron al migrar (y se corrigieron)

Migrar obligó a validar cada consulta contra el esquema real, y eso
sacó a la luz features que en SQLite **nunca habían funcionado** (la
excepción quedaba silenciada y la pantalla mostraba datos de mentira):

- **Categorías**: la consulta pedía `c.descripcion`, columna que nunca
  existió → se agregó la columna.
- **Proveedores**: la pantalla espera `nit, telefono, contacto, email,
  ciudad`; la tabla tenía `identificacion, celular, correo` → se
  rediseñó la tabla con los nombres reales y se remapearon los 6
  proveedores existentes al migrar los datos.
- **Promociones**: la pantalla es un motor de reglas de descuento
  (%, valor fijo, vigencia) pero la tabla estaba diseñada para
  combos/paquetes (`precio_venta`, `costo_total` + detalle) — un
  choque de dos features distintas bajo el mismo nombre. Se rediseñó
  la tabla para la que realmente se usa; los 2 registros viejos (con
  el otro formato) no se migraron por no ser compatibles.
- **Impuestos y Utilidad**: guardaba el margen de utilidad en
  `configuracion_utilidad` (tabla pensada para configurar el margen
  *por producto*, con `id_producto` obligatorio) usando una columna
  que tampoco existía (`porcentaje`) — nunca pudo guardar nada. Se creó
  `configuracion_general` (una sola fila) y ahora la pantalla persiste
  los 5 campos reales (nombre/porcentaje de impuesto, los 2 checkboxes,
  y el margen).
- **Importar Productos (CSV)**: insertaba en una columna `foto` que no
  existe (es `image_path`) → toda importación fallaba.
- **Bajas de Productos**, **Pedidos Anulados**: pedían columnas
  (`producto`/`responsable`, `usuario`) distintas a las de la tabla
  original (`nombre`, sin equivalente) → se alinearon las tablas con lo
  que el código realmente usa.
- **Cliente por Defecto**: la pantalla existía pero nunca escribía en
  la tabla `cliente_defecto` (mostraba éxito sin guardar nada, y
  consultaba una columna `numero_id` inexistente). Ahora sí guarda, y
  Ventas precarga automáticamente ese cliente al abrir.
- **`documentos.py`** (generador de facturas) usaba `ORDER BY rowid`,
  específico de SQLite → se cambió a `ORDER BY id` (la tabla `ventas`
  ahora tiene un `id` explícito).

Ninguno de estos bugs lo causó la migración — ya estaban rotos en
SQLite. Migrar fue lo que los hizo imposibles de ignorar, porque
PostgreSQL exige que cada columna referenciada exista de verdad.

## Diferencias de tipos respecto a SQLite (y por qué)

- **Dinero y cantidades decimales**: se usó `DOUBLE PRECISION`, NO
  `NUMERIC`. psycopg2 devuelve `NUMERIC` como `Decimal`, y el código
  mezcla constantemente esos valores con `float` normales de Python
  (`0.0`, resultados de `float(entry.get())`, etc.) — mezclar
  `Decimal` y `float` en una resta o suma lanza `TypeError` en Python.
  `DOUBLE PRECISION` devuelve `float` nativo, igual que hacía `REAL`
  en SQLite: cero cambios de comportamiento.
- **`fecha` / `hora`**: se dejaron como `TEXT` (formato `AAAA-MM-DD` /
  `HH:MM:SS`), NO `DATE`/`TIME`. El código concatena fechas con `||`,
  las compara como cadenas, hace `.split('-')`, `strptime(...)`, etc.
  en decenas de lugares — pasarlas a tipos nativos habría roto todo
  eso silenciosamente (un `datetime.date` no tiene `.split()`).
- **Cédula / teléfono / identificación**: `VARCHAR` en vez de
  `NUMERIC` (no pierden ceros a la izquierda, no permiten aritmética
  accidental).
- **Banderas sí/no** (`mostrar_cliente`, etc.): `BOOLEAN` en vez de
  `INTEGER` 0/1.
- **`CHECK` en columnas de estado**: se agregaron solo donde se
  verificó, revisando el código, que el conjunto de valores es cerrado
  y consistente (`Activo/Inactivo`, `Abierta/Cerrada`,
  `Pendiente/Crédito/Pagada`, medios de pago). **No** se le puso
  `UNIQUE` a `clientes.cedula`: la pantalla de Clientes siembra datos
  de muestra la primera vez que se abre usando `"-"` como marcador
  repetido para varios clientes sin cédula real, así que una
  restricción de unicidad ahí habría roto ese comportamiento.

## Verificación hecha antes de dar la migración por buena

- Las 142 consultas SQL del proyecto se extrajeron automáticamente y se
  ejecutaron (con `SAVEPOINT`/`ROLLBACK`) contra el esquema real:
  **0 errores de columna/tabla/sintaxis** al cierre.
- Las 53 pantallas del sistema se instanciaron contra PostgreSQL: todas
  abren sin excepción.
- Prueba funcional de extremo a extremo con datos reales: login,
  venta en efectivo (con descuento de stock), venta a crédito
  (aparece en Cuentas por Cobrar) y registro de un abono — las tres
  quedaron confirmadas en la base de datos.

## Datos migrados

Se copiaron los datos reales de `database.db`: usuarios, categorías,
sucursales, empresa, clientes, proveedores (remapeados), inventario
(52 productos), servicios, combos, cajas, cuentas bancarias, gastos y
ventas (7 facturas históricas). Las tablas relacionadas con
funcionalidades que estaban rotas o vacías en el origen (promociones,
`configuracion_utilidad`, bajas de productos, pedidos anulados) no
tenían datos que migrar o cambiaron de forma.
