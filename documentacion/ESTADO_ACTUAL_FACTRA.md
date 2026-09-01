# Estado actual de Factra Negocio

## Alcance y método

Este documento describe el código encontrado en el proyecto al 1 de septiembre de 2026. Es una auditoría documental: no se modificó código ni se infirió funcionalidad por el nombre de un archivo. La evidencia principal está en los módulos Python, `postgresql/esquema.sql`, `db_conexion.py`, `manager.py`, `factrapi_cliente.py`, `ecf_integracion.py` y los documentos operativos existentes.

No se encontró un repositorio Git en la carpeta inspeccionada. El árbol contiene 267 archivos, entre ellos 75 módulos Python, un esquema PostgreSQL, documentación, imágenes, HTML generados y capturas. No se encontró `database.db`; aunque muchas pantallas conservan el nombre `database.db`, la conexión real depende de las variables `POS_DB_*` y apunta a PostgreSQL.

## Resumen ejecutivo

Factra es actualmente una aplicación de escritorio Tkinter para punto de venta y administración comercial. Permite iniciar sesión, abrir/cerrar caja, crear ventas, consultar y descontar inventario, manejar clientes y proveedores, registrar pedidos/compras, cotizaciones, crédito y abonos, gastos, bancos, reportes y configuración. También contiene soporte operativo para sucursales, puntos de venta, almacenes, inventario por almacén, numeración local, NCF tradicional y facturación electrónica mediante FactrAPI.

La aplicación no está organizada como una arquitectura estricta UI → servicios → repositorios. La mayoría de las ventanas Tkinter ejecutan SQL directamente mediante `db_conexion`, calculan importes y coordinan reglas comerciales. Hay dos capas de integración relativamente separadas: `db_conexion.py` para PostgreSQL y `factrapi_cliente.py`/`ecf_integracion.py` para FactrAPI.

El flujo de venta local sí está implementado en una transacción PostgreSQL: valida caja, reserva el número, guarda las líneas, descuenta existencias globales y del almacén, registra movimientos de inventario y, para pagos no efectivos, registra el movimiento bancario. Para una venta a crédito guarda líneas en `facturas_pendientes` y luego permite abonos. La parte fiscal e-CF ocurre después de confirmar la venta local; si FactrAPI no está disponible, la venta local queda guardada y el comprobante queda pendiente.

La aplicación tiene una base funcional amplia, pero mezcla conceptos antiguos con el modelo multi-almacén/fiscal más reciente. No existe evidencia de una prueba completa de todos los flujos desde la interfaz en este entorno, y varias pantallas capturan excepciones amplias y continúan con listas vacías o mensajes genéricos.

## Arquitectura real encontrada

```text
index.py
  └─ Manager (Tk)
       ├─ migrar_base_datos() al iniciar
       ├─ Login / Registro
       │    └─ db_conexion.connect()
       └─ Container (panel principal)
            ├─ Ventas ── POS, pago, caja, FactrAPI/NCF, documentos
            ├─ Inventarios ── productos, stock, kardex, almacenes
            ├─ Compras/Pedidos ── proveedores, recepción y stock
            ├─ Cotizaciones
            ├─ Clientes / Proveedores
            ├─ Cobros / Caja / Gastos / Bancos
            ├─ Reportes
            └─ Configuración / seguridad

Todas las pantallas Tkinter
          │ SQL directo usando placeholders '?'
          ▼
db_conexion.py (_ConnWrapper/_CursorWrapper)
          │ traduce '?' a '%s'
          ▼
psycopg2 → PostgreSQL factra_db

Ventas en modo ecf_factrapi
          └─ ecf_integracion.py → factrapi_cliente.py → HTTPS FactrAPI
                                      └─ comprobantes_fiscales / secuencias_cache
```

### Inicio y conexión

- `index.py` crea `Manager()` y ejecuta el ciclo Tkinter.
- `Manager.__init__` llama a `migrar_base_datos()` antes de mostrar `Login`.
- `db_conexion.connect(db_name)` ignora el argumento heredado `database.db` y ejecuta `psycopg2.connect` con `POS_DB_HOST`, `POS_DB_PORT`, `POS_DB_NAME`, `POS_DB_USER`, `POS_DB_PASSWORD` y `POS_DB_SSLMODE`.
- Por defecto usa `localhost:5432`, base `factra_db`, usuario `pos_app`, contraseña vacía y `sslmode=prefer` en desarrollo. En `POS_ENV=production` exige contraseña y por defecto `sslmode=require`.
- El wrapper traduce mecánicamente `?` a `%s`, expone `cursor`, `execute`, `fetchone`, `fetchall`, `commit` y `rollback`, y cierra la conexión al salir del `with`.
- `manager.py` agrega tablas/columnas de forma idempotente durante el arranque. La migración incluye numeración atómica, puntos de venta, e-CF, almacenes, inventario por almacén, transferencias, auditoría y columnas de caja/almacén.

## Inventario de módulos y pantallas

### Acceso, sesión y panel

**Archivos:** `index.py`, `manager.py`, `login.py`, `container.py`, `window_utils.py`, `dialogos.py`, `permisos.py`, `roles_permisos.py`, `seguridad.py`.

**Funcionalidad:** login por usuario/contraseña, registro inicial, cierre de sesión, panel principal, datos de empresa, versión 4.4.7 y habilitación de botones por rol. `Container.abrir_modulo` abre las pantallas principales. Los permisos se guardan en `roles_permisos` como `(rol, modulo, permitido)`.

**Estado:** 🟢 funcional en estructura; 🟡 seguridad de autorización parcial. La UI verifica permisos al abrir el módulo y deshabilita botones, pero las funciones internas no forman una capa de autorización uniforme y la aplicación depende de la conexión a la base para iniciar.

**Problemas:** `container.py` conserva un botón `Prueba` que abre `prueba.py`, descrito por el propio código como prototipo visual. Se muestra como acceso visible del panel. El nombre de versión está repetido en varias pantallas y no hay mecanismo para actualizarlo dinámicamente.

### Ventas / Punto de venta

**Archivos:** `ventas.py`, `pago_modal.py`, `cambio_modal.py`, `buscar_producto.py`, `cliente_defecto_modal.py`, `generar_factura_modal.py`, `facturas_pendientes.py`, `ventas_realizadas.py`, `facturas_anuladas.py`, `anular_factura_modal.py`, `factura_detalle.py`, `documentos.py`, `nota_credito_debito.py`, `historial_notas.py`.

**Pantallas:** POS con cliente, búsqueda/código, carrito y totales; modal de pago; cambio; facturas realizadas, pendientes y anuladas; detalle de factura; anulación; notas de crédito/débito; generación/visualización de documentos.

**Funcionalidad real:**

- Busca por ID, código de barras o nombre parcial. En modo almacén filtra por existencias positivas del almacén operativo.
- Agrega artículos y acumula cantidades; valida cantidad positiva y stock al agregar.
- Permite cambiar cantidad y precio por línea. El precio especial cambia solo el importe de la línea, no el precio maestro.
- El carrito calcula subtotal y total con `float`; el impuesto mostrado en el POS queda en `0.00`.
- Permite cliente seleccionado o `Cliente General`.
- `RealizarPagoModal` maneja efectivo, venta a crédito, tarjetas, transferencia y pago mixto según el código del modal. Los medios no efectivos exigen cuenta bancaria.
- Para efectivo se solicita recibido/cambio; el callback recibe monto y cambio. El registro de la venta usa el total, no crea una entidad separada de recibo.
- Al confirmar, la venta se registra dentro de una transacción con caja bloqueada `FOR UPDATE`; reserva `ticket_venta` con `UPDATE ... RETURNING`.
- Una venta normal inserta una fila por línea en `ventas`; una venta a crédito inserta una fila por línea en `facturas_pendientes` con estado `Crédito`.
- Descuenta `inventario_almacen` y `inventario`, registra `SALIDA_VENTA` en `movimientos_inventario` y enlaza la venta a `caja_id` y `almacen_id`.
- Pago electrónico registra un depósito en la cuenta bancaria y la referencia de venta. Pago efectivo se suma al cierre mediante la consulta de ventas/movimientos.
- Si se retoma una factura pendiente, elimina las líneas pendientes con estado `Pendiente` tras confirmar.
- La anulación restaura inventario y registra reversión financiera; si hay e-CF emitido intenta anularlo en FactrAPI. El módulo conserva la venta anulada en `facturas_anuladas`.

**Estado:** 🟢 núcleo local implementado; 🟡 impuestos, descuentos y consistencia de algunas ediciones. La confirmación tiene transacción y controles de stock, pero el POS no calcula ITBIS aunque existe configuración fiscal. La edición de cantidad no vuelve a validar contra stock antes de confirmar; la confirmación sí vuelve a validar en base de datos.

**Flujo actual:**

```text
Producto por nombre/ID/barra
        ↓
Carrito (precio, cantidad, impuesto visual 0)
        ↓
PagoModal (efectivo, crédito, tarjeta, transferencia, mixto)
        ↓
Transacción: factura + líneas / crédito + caja + stock + banco
        ↓
Modo informal, NCF tradicional o emisión/cola e-CF FactrAPI
        ↓
Documento HTML local / consulta de factura
```

**Limitaciones y riesgos:** no hay tabla cabecera de venta: factura, cliente, medio y totales se repiten por línea. No existe campo de descuento/impuesto por línea en `ventas`; el descuento global se reparte proporcionalmente en memoria. El impuesto de la UI es cero. `Venta a Crédito` no está permitido en el `CHECK` de `ventas.medio_pago`, porque se guarda en otra tabla. No se ve una devolución comercial independiente; la anulación y las notas son los mecanismos disponibles.

### Inventario y catálogo

**Archivos:** `inventarios.py`, `producto_modal.py`, `importar_productos.py`, `categorias.py`, `servicios.py`, `combos.py`, `combo_detalle.py`, `promociones.py`, `bajas_productos.py`, `stock_minimo_modal.py`, `stock_minimo_individual.py`, `alerta_stock_bajo.py`, `historial_producto.py`, `kardex_inventario.py`, `transferencia_almacen.py`, `almacenes.py`, `gestor_codigos_barra.py`, `gestor_etiquetas.py`, `catalogo_pdf_modal.py`.

**Funcionalidad:** CRUD/desactivación de productos, categorías, servicios, combos y promociones; importación/exportación CSV; imagen de producto; costos/precios; stock mínimo; alertas; historial de precios; kardex; bajas; código de barras e impresión/guardado de etiquetas; almacenes y transferencias.

**Catálogo de repuestos encontrado:**

| Concepto | Estado | Evidencia / alcance |
|---|---|---|
| SKU/código interno | PARCIAL | Se puede usar el `id` numérico; no hay columna SKU dedicada. |
| Código de barras | EXISTE | `inventario.codigo_barra`, índice único parcial y gestores con EAN-13/UPC-A/Code128. |
| Código OEM/referencia | NO EXISTE | No hay columna, tabla ni flujo identificado. |
| Marca/fabricante | NO EXISTE | No existe entidad o campo de marca/fabricante. |
| Categoría | EXISTE | Campo textual `inventario.categoria` y tabla `categorias`, sin FK entre ambos. |
| Modelo/año/motor/versión | NO EXISTE | No hay estructura de compatibilidad. |
| Costo y precio | EXISTE | `DOUBLE PRECISION` en inventario; un precio y un costo actuales. |
| Múltiples listas de precio | NO EXISTE | No se encontró tabla de listas. |
| ITBIS/impuesto | PARCIAL | Configuración y tipo de impuesto existen; el POS guarda/muestra 0 y no aplica tasa real. |
| Existencia | EXISTE | Stock global y stock por almacén. |
| Existencia mínima | EXISTE | `stock_minimo` y pantallas de alerta. |
| Almacén/ubicación física | PARCIAL | Almacenes existen; no hay pasillo, estante ni ubicación física detallada. |
| Foto | EXISTE | `image_path` y selección/copia de imagen. |
| Unidad | PARCIAL | e-CF usa unidad 43 por defecto; el producto local no tiene unidad. |
| Equivalencias/sustitutos | NO EXISTE | No hay tablas ni flujo. |
| Compatibilidad vehículo | NO EXISTE | No implementado actualmente. |

El stock global y el stock por almacén coexistien. La migración crea un almacén principal y copia el stock global si no existe registro por almacén. Esto reduce el riesgo de perder existencias, pero deja un modelo duplicado que debe mantenerse consistente por la aplicación.

### Compras y proveedores

**Archivos:** `compras.py`, `registrar_pedido_modal.py`, `pedidos_anulados.py`, `proveedores.py`, `reporte_cuentas_pagar.py`, `seleccionar_cuenta_banco.py`.

`proveedores.py` permite registrar, editar, desactivar, buscar y exportar proveedores con nombre, NIT, teléfono, contacto, correo, dirección, ciudad y estado. `compras.py` trabaja principalmente con pedidos: selecciona proveedor/producto, agrega cantidades, registra pedido, guarda borrador, carga borrador y anula pedido. Las líneas se almacenan en `pedidos`; las anulaciones en `pedidos_anulados`.

El modal indica que el stock se actualiza al recibir mercancía. El código relacionado con compras actualiza productos, historial y movimientos de inventario cuando se registra la recepción, pero el modelo no tiene una tabla normalizada de cabecera/detalle de compra, recepción, factura del proveedor o cuenta por pagar. `reporte_cuentas_pagar.py` existe como pantalla/reporte, pero no se encontró una entidad `cuentas_por_pagar` ni un flujo de pago a proveedor equivalente a CxC.

**Estado:** 🟡 pedidos/compras locales parciales; 🔴 CxP formal, órdenes y devoluciones de compra no verificadas como implementadas. Costos existen en `pedidos` y `inventario`, pero no hay historial contable de obligaciones por proveedor.

### Cotizaciones

**Archivos:** `cotizaciones.py`, `cargar_cotizacion.py`, `cotizacion_nota_modal.py`.

Permite armar carrito, asociar cliente, registrar cotización con número atómico `cotizacion`, listar/buscar, añadir observación, cargar una cotización pendiente y anularla. Las líneas están en `cotizaciones` y usan estado `Pendiente`/`Registrada`.

**Estado:** 🟡 funcional como documento comercial. No se encontró conversión directa implementada de cotización a factura: `cargar_cotizacion.py` carga líneas al POS, pero el usuario debe confirmar después una venta. La cotización no descuenta stock ni crea CxC por sí misma.

### Clientes y cuentas por cobrar

`clientes.py`, `cliente_detalle.py` y `cliente_defecto_modal.py` manejan nombre, cédula, celular, dirección, correo, tipo de identificación y estado. No hay campos de límite de crédito, balance almacenado, tipo comercial ni lista de precios. `cliente_defecto` configura el cliente general.

`cuentas_por_cobrar.py` deriva el saldo agrupando `facturas_pendientes` en estado `Crédito` menos `abonos_credito`. Permite configurar un plazo en la pantalla, listar vencidos/por vencer, registrar abono con caja abierta, medio de pago y cuenta bancaria, ver abonos e historial. Los abonos insertan ingreso en caja y, si corresponde, movimiento bancario.

**Estado:** 🟢 CxC básica funcional; 🟡 crédito comercial limitado. El plazo configurado vive en memoria de la pantalla y no en una tabla de configuración. El crédito se identifica por nombre de cliente y número de factura; no hay FK de venta/cliente ni límite de crédito.

### Caja, bancos y gastos

`gestion_caja.py`, `abrir_caja_modal.py`, `caja_detalle.py`, `reporte_caja.py` implementan apertura con fondo y cajero, cierre, monto esperado, monto contado, diferencia, detalle e historial. `cajas` tiene restricción de una caja abierta por cajero (`idx_cajas_cajero_abierta`), pero el punto de venta es opcional. Las ventas y abonos se vinculan a caja cuando pasan por los flujos actuales.

`gestion_banco.py`, `movimientos_bancarios.py`, `registro_financiero.py` permiten cuentas bancarias, saldo y movimientos de ingreso/egreso/depósito/retiro/transferencia. `control_gastos.py` registra gastos, puede destinarlos a caja o banco y usa `gastos`.

**Estado:** 🟢 caja básica y bancos implementados; 🟡 arqueo/historial dependen de datos registrados. No hay sucursal obligatoria en caja, cierre automático, conciliación bancaria ni flujo explícito de devolución en caja.

### Reportes

`reportes.py` abre: ventas totales, ventas por mes/cliente/producto, medios de pago, ganancias, rentabilidad, costo de inventario, compras por producto, gastos por mes, cuentas por cobrar/pagar y caja. Las pantallas consultan PostgreSQL y exportan principalmente CSV; algunas generan PDF con ReportLab.

**Estado:** 🟢 reportes consultados desde datos; 🟡 algunos nombres de pantalla exceden el modelo disponible. Por ejemplo, el reporte de CxP existe aunque no hay tabla CxP formal. No se encontraron números fijos en los reportes principales, pero `prueba.py` sí es una maqueta con resumen interactivo.

### Configuración

`configuracion.py` abre empresa, numeración fiscal, importación de productos, factura, sucursales, categorías, moneda, impuestos, promociones, bajas, cliente por defecto, códigos, bancos, etiquetas, stock mínimo, alertas, combos, almacenes, catálogo PDF, NCF tradicional y FactrAPI.

`empresa` guarda nombre, dirección, teléfono, correo, web, imagen, tipo/número de identificación, NIT y ciudad. `configuracion_general` guarda impuesto, precios con impuesto, desglose, margen, modo fiscal, punto de venta, FactrAPI y almacén operativo. `factura_config`/`info_factura` controlan textos y visibilidad del HTML A4. `moneda` e `impuestos` existen como catálogos, aunque el POS no refleja el impuesto configurado.

## Modelo PostgreSQL

El esquema fuente y la migración usan 41 nombres de tabla efectivos (con una declaración repetida de `puntos_venta` protegida por `IF NOT EXISTS`). Las tablas principales son:

```text
usuarios ── roles_permisos / roles / permisos
empresa ── sucursal ── puntos_venta ── cajas ── movimientos_caja
                         └─ almacenes ── inventario_almacen
inventario ── categorias (relación textual, no FK)
inventario ── stock_minimo, historial_precios, bajas_productos
inventario ── movimientos_inventario, transferencias_almacen
clientes ── ventas / facturas_pendientes / cotizaciones / abonos_credito
proveedores ── pedidos / pedidos_anulados
ventas ── facturas_anuladas / descuentos_ventas / nota_ventas
ventas ── comprobantes_fiscales ── secuencias_cache
configuracion_general ── punto de venta + almacén operativo + FactrAPI
cuentas_bancarias ── movimientos_bancarios
gastos, moneda, impuestos, info_factura, promociones, servicios, combos
```

### Tablas y campos relevantes

- Seguridad: `usuarios`, `roles`, `permisos`, `permisos_rol`, `roles_permisos`, `auditoria_eventos`.
- Organización: `empresa`, `sucursal`, `puntos_venta`, `almacenes`, `configuracion_general`, `moneda`, `impuestos`, `info_factura`.
- Catálogo: `inventario`, `categorias`, `servicios`, `combos`, `combo_detalle`, `promociones`, `stock_minimo`, `historial_precios`, `bajas_productos`.
- Caja/finanzas: `cajas`, `movimientos_caja`, `cuentas_bancarias`, `movimientos_bancarios`, `gastos`, `abonos_credito`.
- Ventas: `ventas`, `facturas_pendientes`, `facturas_anuladas`, `descuentos_ventas`, `nota_ventas`, `cotizaciones`.
- Compras: `pedidos`, `pedidos_anulados`, `pedidos_borradores`.
- Stock/movimientos: `inventario_almacen`, `movimientos_inventario`, `transferencias_almacen`.
- Fiscal: `numeracion_local`, `secuencias_ncf_tradicional`, `documentos_fiscales_locales`, `comprobantes_fiscales`, `secuencias_cache`, `notas_credito_debito_locales`.

Todas las tablas usan `SERIAL` o identidad como clave primaria. Las FK más importantes están en `inventario_almacen`, `combo_detalle`, `abonos_credito.caja_id`, `comprobantes_fiscales.punto_venta_id`, almacenes, movimientos y auditoría. Hay cascada al borrar producto sobre stock por almacén, historial y detalle de combo; el detalle de combo impide borrar producto (`RESTRICT`). Muchas relaciones comerciales son solo por texto/número: `ventas` no tiene FK a cliente, producto, caja, almacén o factura cabecera.

Los importes usan `DOUBLE PRECISION`, no `NUMERIC/DECIMAL`. Fechas y horas operativas se almacenan mayormente como `TEXT`; timestamps se usan en tablas nuevas de migración. Los estados son cadenas con `CHECK` en varias tablas. Existen índices para nombres/categorías/barra de inventario, factura/fecha/cliente de ventas, estados, números documentales, caja, bancos, auditoría y comprobantes.

## Multiempresa, multicaja y multisucursal

### Multiempresa

Existe una sola tabla `empresa` y numerosas consultas hacen `LIMIT 1` o `WHERE id=1` en configuración. No existe `empresa_id` en usuarios, clientes, inventario, ventas, compras, cajas, almacenes ni reportes. Por lo tanto, no hay multiempresa real ni aislamiento entre empresas. El sistema actual es de una empresa por base de datos.

### Multicaja

Existe `cajas` y `puntos_venta`; cada caja identifica cajero, punto de venta opcional y estado. La unicidad parcial impide dos cajas abiertas para el mismo texto de cajero, no para el mismo usuario ID. El número de venta se reserva atómicamente y la caja se bloquea durante la confirmación, por lo que hay cierta protección para cajas/procesos concurrentes.

No hay una pantalla que configure una estructura completa “sucursal → caja 1/2/3” ni un FK obligatorio a punto de venta en cajas/ventas. La selección de caja se hace por `cajero` y la venta actual por la caja abierta de ese cajero.

### Multisucursal

Existe tabla `sucursal`; `puntos_venta` y `almacenes` tienen `sucursal_id`, y el inventario por almacén permite separar stock. También existe transferencia entre almacenes. Sin embargo, la pantalla de producto conserva `inventario.sucursal` como texto, y muchas consultas no filtran sucursal. No hay usuarios por sucursal, reglas de acceso por sucursal, ni una transferencia entre sucursales diferenciada de la transferencia entre almacenes. Es soporte parcial, no aislamiento multisucursal completo.

## Compras, ventas, anulación y notas

El flujo real encontrado es:

```text
Pedido/proveedor → líneas en pedidos → recepción/actualización de producto y stock
                                      └─ movimientos_inventario e historial

Cotización → cotizaciones → cargar al POS → venta confirmada

Venta contado → ventas → stock → caja/banco → documento local o e-CF
Venta crédito → facturas_pendientes → abonos_credito → caja/banco
Anulación → facturas_anuladas + restauración stock + reversión financiera
Nota → notas_credito_debito_locales y, si es e-CF emitido, FactrAPI 33/34
```

No existe una cabecera de venta ni una entidad de factura comercial separada. No se encontró devolución parcial independiente. La nota local registra tipo, factura afectada, motivo, monto y cajero, pero la emisión e-CF construye un ajuste de una sola línea por el monto indicado; no es una devolución detallada de productos.

## Impresión y hardware

`documentos.py` genera HTML local para A4, 50 mm y 80 mm con datos de empresa/factura y abre el archivo mediante `webbrowser`. Hay documentos HTML ya generados en `documentos_emitidos`. La impresión depende del navegador/diálogo de impresión de Windows; no hay driver térmico propio ni envío directo a impresora.

Hay generación de códigos de barras con `python-barcode` y `ImageWriter`, guardado de imágenes y etiquetas. Esto es generación de imagen, no lectura de hardware. No se encontraron integraciones con gaveta de dinero, balanza, puerto COM, USB, TCP/IP, API de impresoras de red ni lector físico. La entrada de código de barras es un campo del POS.

`reportlab` se usa en determinados reportes PDF. No se encontró PDF fiscal firmado ni conexión directa a una impresora fiscal.

## FactrAPI y facturación electrónica

La integración está en `factrapi_cliente.py` y `ecf_integracion.py`. La URL base y API Key se leen de `configuracion_general`; la API Key se descifra con Fernet derivado de `POS_FACTRAPI_ENCRYPTION_KEY`. El documento no reproduce secretos.

Endpoints codificados:

- `POST /api/v1/clientes`
- `GET /api/v1/consulta-rnc/{rnc}`
- `POST /api/v1/comprobantes`
- `POST /api/v1/comprobantes/{id}/enviar`
- `POST /api/v1/comprobantes/{id}/consultar`
- `POST /api/v1/comprobantes/{id}/anular`
- `GET /api/v1/comprobantes/{id}/xml`
- `GET /api/v1/comprobantes/{id}/representacion-impresa`
- `POST /api/v1/puntos-venta`, `GET /api/v1/puntos-venta`
- `GET /api/v1/secuencias`
- `GET /api/v1/catalogos/{nombre}`

Usa `x-api-key`, timeout de 45 segundos, hasta tres reintentos adicionales, backoff con jitter para errores de red/5xx y `Retry-After` para 429. No reintenta automáticamente 409/422. Usa `Idempotency-Key` en creación y acciones repetibles.

El modo `ecf_factrapi` crea clientes remotos si faltan, consulta RNC para clientes NIT, elige E31 para NIT y E32 para otros, arma detalles y envía el comprobante. La venta local ya está confirmada antes de la llamada remota. `comprobantes_fiscales` conserva payload, idempotency key, identificadores, e-NCF, estado y último error. Sin conexión/configuración crea estado `pendiente_conexion`; al abrir POS se ejecutan en segundo plano reintentos de hasta 20 y reconciliación de estados.

Existe caché de secuencias y alertas por agotamiento/vencimiento. El pago mixto se transforma a “Otras formas de pago” (8), porque el propio código reconoce que no registra el desglose real. Las notas 33/34 requieren comprobante e-CF original y cliente sincronizado.

**Estado:** 🟢 integración técnica y cola local implementadas; 🟡 flujo fiscal dependiente de configuración y del contrato externo. No se verificó comunicación real contra FactrAPI durante esta auditoría. La cola es solo para e-CF; la venta comercial no depende de Internet, pero sí depende de PostgreSQL local/remoto.

## Funcionamiento offline y fallos

| Situación | Comportamiento actual |
|---|---|
| Sin Internet | Ventas locales en modo informal/NCF pueden continuar si PostgreSQL está disponible. En e-CF la venta local se guarda y el comprobante queda en `comprobantes_fiscales` pendiente. |
| FactrAPI no responde | `requests` reintenta errores transitorios; después la venta no se revierte y el e-CF queda pendiente o con error según el caso. |
| PostgreSQL no responde | No se puede iniciar/migrar ni vender; las pantallas suelen mostrar error o lista vacía. No existe base local SQLite de contingencia. |
| Cierre durante una venta | La confirmación está dentro de una transacción; si el proceso muere antes del commit PostgreSQL revierte la operación. El carrito en memoria se pierde. |
| Reinicio inesperado | Se conservan datos ya confirmados; se pierde el estado no confirmado. La cola fiscal persistida se puede reintentar al abrir Ventas. |
| Pérdida entre caja y servidor local | Las operaciones nuevas fallan; no hay replicación local, caché de ventas ni sincronización multi-servidor. |

La conclusión objetiva es que existe contingencia offline frente a FactrAPI, no frente a PostgreSQL. El objetivo comercial “seguir vendiendo sin Internet” se cumple parcialmente si PostgreSQL está local y el modo fiscal permite guardar la venta local; no existe operación desconectada del servidor de base de datos.

## Backups y actualizaciones

La configuración ofrece copia y restauración PostgreSQL. `configuracion.py` localiza `pg_dump`/`psql` en PATH o instalaciones estándar de Windows, genera un `.sql` en `backups` y valida que no esté vacío. La restauración solicita un archivo SQL y ejecuta `psql` con confirmación del usuario. No hay backup automático programado, copia en nube/externa, política de frecuencia ni restauración automática. La restauración puede reemplazar datos actuales, según el mensaje de confirmación.

No existe mecanismo de consultar versión remota, descargar una versión, instalarla o reiniciar. **Actualización automática: NO IMPLEMENTADO.**

## Seguridad

### Aspectos implementados

- Contraseñas nuevas usan PBKDF2-SHA256 con 310.000 iteraciones, salt aleatorio y formato `pbkdf2_sha256$...`.
- Existe política mínima de 8 caracteres, letras y números.
- Contraseñas antiguas en texto plano se aceptan para migración y se reemplazan por hash después de login exitoso.
- API Key puede cifrarse con Fernet usando un secreto externo `POS_FACTRAPI_ENCRYPTION_KEY`; producción exige esa variable para e-CF y el preflight detecta claves sin cifrar.
- Las consultas de datos usan parámetros, no interpolación de valores; la migración usa f-strings solo para nombres de tablas/columnas internos.
- Existe auditoría de login, accesos y operaciones sensibles mediante `auditoria_eventos`.
- El preflight valida administrador activo, hashes, permisos, tablas críticas, cajas pendientes, ventas sin caja/almacén y comprobantes huérfanos.

### Problemas clasificados

| Prioridad | Hallazgo |
|---|---|
| P0 | No se encontró un P0 confirmado por lectura estática. La disponibilidad completa depende de PostgreSQL y la seguridad real depende de configuración externa. |
| P1 | No hay aislamiento multiempresa: `empresa_id` no existe en entidades comerciales. Una misma base no puede separar empresas. |
| P1 | Autorización principalmente en UI/dispatcher; no existe una capa de permisos para impedir que todo acceso directo a una clase o función sea invocado por otro camino. |
| P1 | Compatibilidad temporal con contraseñas en texto plano y API Keys sin cifrar existe en desarrollo; si se despliega incorrectamente, expone credenciales. |
| P1 | Credenciales PostgreSQL dependen de variables, pero en desarrollo la contraseña por defecto es vacía. |
| P2 | Auditoría captura excepciones y las ignora (`registrar_evento`), por lo que no garantiza que cada evento sensible quede registrado. |
| P2 | No hay límites de crédito ni validación de identidad única de clientes; la cédula no es única deliberadamente. |
| P2 | Importes con `DOUBLE PRECISION` y fechas como texto pueden producir problemas de exactitud/ordenamiento. |
| P2 | Varias pantallas capturan `Exception` ampliamente, imprimen el error y continúan con datos vacíos. |
| P3 | Duplicación de imports, nombres heredados de SQLite, versión hardcodeada y módulos/prototipos coexistentes aumentan confusión de mantenimiento. |

No se observaron secretos completos en los archivos revisados que deban reproducirse aquí. Los valores sensibles se describen por su existencia y ubicación lógica, no por su contenido.

## Arquitectura del código y deuda técnica

La separación es parcial:

- **UI + SQL:** `ventas.py`, `compras.py`, `cotizaciones.py`, `clientes.py`, `inventarios.py`, `gestion_caja.py`, `cuentas_por_cobrar.py` y la mayoría de modales abren conexiones y ejecutan SQL directamente.
- **Lógica reutilizable:** `db_conexion.py`, `seguridad.py`, `permisos.py`, `registro_financiero.py`, `ncf_tradicional.py`, `factrapi_cliente.py` y `ecf_integracion.py` sí concentran algunas reglas.
- **Presentación/documentos:** `documentos.py` consulta datos y genera HTML en el mismo módulo.
- **Archivos grandes:** `ventas.py` (~56 KB), `manager.py` (~28 KB), `login.py` (~32 KB), `cotizaciones.py` (~25 KB), `producto_modal.py` (~21 KB), `inventarios.py` (~21 KB) y `anular_factura_modal.py` (~21 KB).
- **Duplicación:** importaciones duplicadas de `os`/`db_conexion`; alias `db_conexion as sqlite3`; consultas repetidas para nombres, stock y totales; modelos lineales repetidos en ventas, crédito y anulaciones.
- **Estado global implícito:** usuario actual vive en `Manager`, configuración se lee por filas únicas `id=1`, almacén operativo se lee de configuración y el cajero se pasa como texto.
- **Excepciones:** múltiples pantallas hacen `except Exception`, imprimen y dejan la UI vacía; `registrar_evento` suprime cualquier error de auditoría.
- **Código provisional:** `prueba.py` y el botón `Prueba`; documentos de plan/guía conviven con la implementación y contienen historial de fases, no son código ejecutable.
- **Comentarios/TODO:** no se encontró una concentración de `TODO`/`FIXME` ejecutables; sí hay comentarios de compatibilidad, fases y limitaciones conocidas, especialmente en FactrAPI y el pago mixto.

## Funcionalidades simuladas o no verificables

- `prueba.py` es una maqueta/prototipo visual con resumen y acciones locales; el propio `Container` lo marca como prototipo y no debe confundirse con el POS real.
- El botón de recarga del dashboard vuelve a consultar empresa/usuario y muestra un mensaje; no realiza sincronización ni actualización remota.
- La etiqueta “Exportar Excel” en varias pantallas genera CSV, no un archivo XLSX.
- “Impresión” abre/genera HTML y depende del navegador; no prueba que una impresora física haya impreso.
- El POS muestra impuesto 0.00 aunque existe configuración de impuesto; esto es comportamiento implementado, pero no un cálculo fiscal completo.
- Reportes de CxP y algunas opciones existen como pantallas, aunque no se encontró un libro de cuentas por pagar normalizado.
- No se encontró evidencia de lector de barras, gaveta, balanza o impresora conectados: el código solo procesa entradas y archivos/imágenes.

No se encontró evidencia suficiente para afirmar que las operaciones reales de base sean mock: ventas, stock, caja, abonos, pedidos y FactrAPI tienen SQL y transacciones concretas. Los estados de “éxito” de cada pantalla deben interpretarse junto con la captura de excepciones y no sustituyen una prueba de aceptación.

## Mapa completo actual

```text
FACTRA NEGOCIO
├── Acceso y seguridad
│   ├── Login / Registro
│   ├── Usuarios
│   ├── Roles y permisos
│   └── Auditoría
├── Operación
│   ├── Ventas / POS
│   ├── Facturas realizadas, pendientes y anuladas
│   ├── Cotizaciones
│   ├── Clientes
│   ├── Compras / Pedidos
│   └── Proveedores
├── Inventario
│   ├── Productos
│   ├── Categorías
│   ├── Servicios
│   ├── Combos
│   ├── Promociones
│   ├── Stock mínimo y alertas
│   ├── Kardex / historial / bajas
│   ├── Almacenes y transferencias
│   ├── Códigos de barras y etiquetas
│   └── Catálogo PDF
├── Finanzas
│   ├── Caja y reportes de caja
│   ├── Cobros / CxC / abonos
│   ├── Bancos y movimientos
│   └── Gastos
├── Reportes
│   ├── Ventas
│   ├── Ganancias / rentabilidad
│   ├── Inventario / costos
│   ├── Compras
│   ├── Gastos
│   ├── CxC / CxP
│   └── Medios de pago
├── Fiscal e impresión
│   ├── NCF tradicional
│   ├── FactrAPI / e-CF
│   ├── Notas 33/34
│   ├── HTML A4/50mm/80mm
│   └── PDF de reportes
├── Configuración
│   ├── Empresa, sucursales, puntos de venta
│   ├── Moneda, impuestos, numeración
│   ├── Factura y FactrAPI
│   ├── Backups/restauración manual
│   └── Catálogos operativos
└── Prototipo
    └── Prueba (maqueta visual)
```

## Matriz final de funcionalidades

| Área | Funcionalidad | Estado | Observaciones |
|---|---|---|---|
| Acceso | Login y registro | 🟢 | PostgreSQL; hash PBKDF2 y migración de legacy. |
| Seguridad | Roles/permisos | 🟡 | UI y matriz de permisos; defensa no uniforme dentro de funciones. |
| Ventas | Crear venta contado | 🟢 | Transacción, caja, stock global/almacén y banco. |
| POS | Buscar por nombre/ID/barra | 🟢 | Código de barras es campo/entrada, no lector físico. |
| POS | Modificar cantidad/precio | 🟡 | Existe; edición de cantidad no valida stock hasta confirmar. |
| POS | Impuesto/ITBIS | 🔴 | Configuración existe, cálculo del POS queda en cero. |
| POS | Descuento | 🟡 | Modal/código distribuye descuento proporcionalmente; no hay campo fiscal por línea. |
| POS | Pago efectivo/cambio | 🟢 | Modal y cierre de caja. |
| POS | Tarjeta/transferencia | 🟢 | Requiere cuenta y registra movimiento bancario. |
| POS | Pago mixto | 🟡 | Se guarda como medio mixto; e-CF lo convierte a forma 8 sin desglose. |
| Ventas | Venta a crédito | 🟢 | Líneas en `facturas_pendientes`; no hay límite de crédito. |
| Ventas | Cancelación/anulación | 🟢 | Archiva, restaura stock y revierte finanzas; e-CF se intenta anular. |
| Ventas | Devolución parcial | 🔴 | No existe flujo independiente verificado. |
| Ventas | Nota crédito/débito | 🟡 | Registro local y emisión 33/34 condicionada a e-CF original. |
| Cotizaciones | Crear/cargar/anular | 🟢 | Cargar lleva líneas al POS; conversión no es automática. |
| Clientes | CRUD y cliente general | 🟢 | Datos básicos; sin límite/lista de precios. |
| Proveedores | CRUD | 🟢 | Datos básicos y exportación. |
| Compras | Pedido/anulación/borrador | 🟡 | Existe; modelo formal de compra/CxP es limitado. |
| Inventario | Producto y categoría | 🟢 | CRUD/desactivación, costo, precio, stock, imagen. |
| Inventario | Stock por almacén | 🟢 | Migración, salidas, entradas y transferencias. |
| Inventario | Kardex | 🟡 | Tabla/módulo existen; cobertura depende de que todos los caminos registren movimientos. |
| Repuestos | Código OEM | ⚪ | No implementado actualmente. |
| Repuestos | Compatibilidad vehículo | ⚪ | No implementado actualmente. |
| Repuestos | Equivalencias/sustitutos | ⚪ | No implementado actualmente. |
| Caja | Apertura/cierre/diferencia | 🟢 | Fondo, esperado, contado y diferencia. |
| Caja | Devoluciones/retiros formales | 🟡 | Hay egresos y reversión de anulación; no flujo completo de devolución. |
| Bancos | Cuentas/movimientos | 🟢 | Saldos y movimientos dentro de transacciones de pagos. |
| CxC | Abonos y saldo | 🟢 | Derivado de crédito menos abonos; plazo de pantalla. |
| CxP | Obligación y pago proveedor | 🔴 | No hay tabla/flujo formal verificable. |
| Reportes | Ventas/caja/inventario | 🟢 | Consultas y exportaciones; algunos PDF. |
| Impresión | HTML A4/ticket | 🟢 | Genera y abre documento local. |
| Impresión térmica | Envío directo | 🔴 | No implementado; depende del navegador/Windows. |
| Hardware POS | Lector/gaveta/balanza | 🔴 | No implementado. |
| Multiempresa | Separación de datos | 🔴 | Una empresa por base; sin `empresa_id`. |
| Multicaja | Varias cajas | 🟡 | Tabla/punto de venta y bloqueo; identificación principalmente por cajero. |
| Multisucursal | Sucursales completas | 🟡 | Sucursales/almacenes existen; filtros y permisos son incompletos. |
| Offline | Sin Internet/FactrAPI | 🟢 | Venta local y cola fiscal persistida. |
| Offline | Sin PostgreSQL | 🔴 | No hay almacenamiento local de contingencia. |
| FactrAPI | e-CF, estados, reintentos | 🟢 | Cliente HTTP, idempotencia, cola y caché. Requiere servicio/configuración real. |
| NCF | NCF tradicional | 🟢 | Secuencias locales y documento fiscal local. |
| Backups | Backup/restauración manual | 🟢 | `pg_dump`/`psql`; sin automatización ni nube. |
| Actualizaciones | Actualización automática | 🔴 | No implementado. |
| Prototipo | Pantalla Prueba | ⚫ | Maqueta visual separada del flujo real. |

## Conclusión descriptiva

El sistema actual es un POS local conectado a PostgreSQL con un conjunto amplio de módulos administrativos. Su núcleo transaccional de venta, caja, stock y crédito existe y tiene controles de concurrencia recientes. El modelo fiscal FactrAPI también tiene cliente HTTP, idempotencia, estados y cola persistida. Las principales fronteras objetivas del estado actual son: dependencia total de PostgreSQL para operar, ausencia de multiempresa real, multisucursal incompleto, compras/CxP no normalizadas, cálculo de ITBIS no aplicado en POS, falta de compatibilidad específica para repuestos y ausencia de integración de hardware/actualización automática.

Este documento no propone una reescritura ni cambios de implementación; deja esos puntos como insumo para la siguiente decisión de arquitectura/MVP.

## Anexo: refactorización posterior

Después de esta auditoría se inició una refactorización controlada documentada en `documentacion/REFACTORIZACION_ARQUITECTURA.md`. Se agregaron servicios y repositorios para ventas, inventario, caja, clientes, CxC, compras, cotizaciones, fiscal, reportes y configuración, y se reconectaron varias pantallas principales. El esquema PostgreSQL y la apariencia Tkinter no cambiaron. Algunas pantallas secundarias todavía conservan SQL directo como deuda explícita de migración.
