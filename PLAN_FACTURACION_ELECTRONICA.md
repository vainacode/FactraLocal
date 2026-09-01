# Plan: Numeración de comprobantes, Facturación Electrónica DGII (vía FactrAPI), Multi-Caja, Multi-Almacén y Notas de Crédito/Débito

**Estado: IMPLEMENTACIÓN EN PROGRESO. Fases 1 y varios bloques de las fases 2-6 implementados; quedan validaciones reales de entorno y cierres operativos.**
Este archivo existe para que cualquier sesión (esta u otra IA, en otra
computadora) pueda retomar el trabajo sin releer todo el historial de chat.
Está escrito para ser la fuente de verdad del alcance, las decisiones ya
tomadas, las que faltan por tomar, y el orden de implementación.

Última actualización de este plan: 2026-08-31. Si lo retomas después,
relee primero la sección "0. Qué ya cambió desde que se escribió esto"
(actualízala vos mismo al terminar cada fase).

---

## 0. Qué ya cambió desde que se escribió esto

_(Sección viva — cada sesión que avance una fase debe anotar aquí qué hizo,
en 1-3 líneas, con fecha. No borres entradas viejas.)_

- 2026-09-01: Se completaron los datos operativos de abastecimiento: 40
  líneas de pedidos de compra vinculadas a los productos, 40 movimientos de
  entrada inicial, 4 servicios, 2 promociones y 3 combos con sus detalles.
  Ventas, cajas y gastos permanecen en cero para no fabricar historial
  financiero.

- 2026-09-01: Se reinició la base activa y se cargó la configuración inicial
  de La Tienda de los Repuestos en Montecristi: RNC 40233658695, Jose Veras
  como administrador, sucursal, almacén, punto de venta, permisos, catálogo
  de 40 productos, proveedores, clientes y categorías. Existencias globales
  y por almacén quedaron conciliadas.

- 2026-08-31: El selector de productos ahora abre un listado visual con
  código, nombre, precio y stock; al seleccionar una fila muestra detalles
  del producto y permite devolverlo al punto de venta para agregarlo.

- 2026-08-31: Ventas ahora ofrece búsqueda manual por nombre, código o barra
  desde la lista de productos, sin depender del lector QR. El cierre de caja
  suma abonos en efectivo y muestra explícitamente faltante, sobrante o
  cuadre exacto con esperado y contado.

- 2026-08-31: Se corrigió el inicio de sesión cuando existen cuentas legadas
  que solo difieren por mayúsculas: ahora se prioriza el nombre exacto, por
  lo que la cuenta `admin` ya no queda bloqueada por la cuenta `Admin`.

- 2026-08-31: Se eliminaron cifras de demostración que todavía aparecían al
  abrir reportes de historial, caja, rentabilidad, costo de inventario y
  ventas totales; ahora todos parten de cero y se cargan solo desde datos
  reales. También se corrigió el reporte de caja para no duplicar las ventas
  a crédito.
- 2026-08-31: Se detectó y corrigió el esquema de instalación inicial: faltaba
  declarar varias tablas operativas nuevas y la tabla de auditoría podía
  existir sin permisos para el usuario de la aplicación. El esquema ahora
  incluye esas tablas y el preflight distingue tabla inexistente de tabla
  inaccesible; el registro de auditoría fue probado con la conexión activa.
- 2026-08-31: La auditoría de corte ahora muestra el detalle de las cajas
  abiertas y las considera bloqueantes, evitando iniciar producción con un
  saldo pendiente de cuadre.
- 2026-08-31: Se corrigió el cuadre de caja: el total de ventas ahora suma
  ventas contado y facturas a crédito, el contado incluye pagos electrónicos,
  y el efectivo esperado solo considera efectivo y movimientos físicos de
  caja. Se aplicó tanto al cierre desde Ventas como desde Gestión de Caja.
- 2026-08-31: Se comparó el esquema inicial con las tablas críticas del
  preflight y se incorporaron las que faltaban: comprobantes fiscales,
  secuencias NCF y FactrAPI, transferencias entre almacenes y sus estructuras
  operativas. El esquema ya cubre todas las tablas críticas declaradas.
- 2026-08-31: Se instaló el esquema en una base PostgreSQL temporal limpia,
  se ejecutó la migración dos veces con `pos_app` como propietario y ambas
  terminaron correctamente. La guía ahora deja explícito que el esquema no
  debe instalarse solamente como `postgres`, porque la migración necesita
  modificar el esquema con el usuario de la aplicación.
- 2026-08-31: El preflight ahora bloquea e-CF si la API Key de FactrAPI está
  almacenada en texto plano; la comprobación local confirmó cero claves sin
  cifrar.
- 2026-08-31: Se repitió la prueba de instalación limpia con el esquema
  actualizado: PostgreSQL terminó sin errores, las dos ejecuciones de
  migración devolvieron `True` y no faltó ninguna tabla crítica. La base
  temporal fue eliminada tras la prueba.
- 2026-08-31: El preflight principal ahora también bloquea cajas abiertas,
  abonos sin caja y comprobantes fiscales sin venta asociada; ya no depende
  de ejecutar la auditoría adicional para esas condiciones.
- 2026-08-31: Ventas ya no continúa con stock global si falla la lectura del
  almacén operativo; el preflight exige además que el almacén configurado esté
  activo. La base actual tiene el almacén operativo activo y validado.
- 2026-08-31: El formulario de productos ya no deja el stock agregado igual
  al de un solo almacén al editar existencias; ahora recalcula el total como
  suma de todos los almacenes. La base real fue auditada y tiene cero
  diferencias entre ambos valores.
- 2026-08-31: Se añadieron restricciones PostgreSQL de último nivel para
  impedir stock negativo global o por almacén y saldos bancarios negativos.
  La migración las aplicó correctamente sobre la base real y quedó
  comprobada su idempotencia.
- 2026-08-31: Se verificaron los privilegios efectivos del usuario `pos_app`
  sobre la base real: las 19 tablas críticas tienen permisos de lectura,
  inserción y actualización, y las 49 secuencias tienen permisos de uso,
  lectura y actualización.
- 2026-08-31: Se probó el cliente FactrAPI con un servidor HTTP simulado:
  crear y enviar usan las rutas esperadas, envían `x-api-key` e
  `Idempotency-Key`, y se procesan respuestas envueltas en `data`. Falta la
  prueba contra el ambiente real por requerir credenciales externas.
- 2026-08-31: La anulación ahora lista y procesa también facturas a crédito
  (`facturas_pendientes`), además de ventas contado; la reversión elimina el
  documento de su tabla de origen, repone inventario y conserva las
  validaciones de caja/banco. La consulta unificada fue probada en PostgreSQL.
- 2026-08-31: Se corrigieron impresión, detalle e historial de ventas para
  consultar también facturas a crédito en estados `Crédito/Pagada`, sin
  incluir borradores `Pendiente`. Las tres consultas unificadas fueron
  ejecutadas contra PostgreSQL y la compilación pasó.
- 2026-08-31: Se extendió la consolidación contado/crédito a los reportes por
  cliente, producto, mes, ganancias, rentabilidad y ventas totales. Las
  consultas de consolidación se ejecutaron en PostgreSQL y todos los módulos
  de reportes importan correctamente.
- 2026-08-31: La plantilla de impresión ahora distingue facturas informales
  de comprobantes e-CF: no muestra "Pendiente de emisión" ni "Comprobante
  Fiscal Electrónico" cuando el documento no aplica a facturación electrónica.
  La carga de una factura real fue verificada.
- 2026-08-31: Se probó el ciclo real de respaldo y recuperación: `pg_dump`
  generó un archivo válido de 129 KB, se restauró en una base temporal sin
  errores y conservó 52 tablas y los 4 usuarios. La base y el archivo de
  prueba fueron eliminados después de la verificación.

- 2026-08-31: Se eliminó el último circuito de códigos de barras ficticios:
  `inventario.codigo_barra` quedó en el esquema y en la migración, el alta y
  edición de productos lo persisten con validación de duplicados, el gestor
  de códigos guarda realmente la asignación y ventas/etiquetas consultan el
  valor real. Se eliminaron también los ejemplos visibles al abrir esas
  pantallas. Sintaxis e importación de todos los módulos verificadas.

- 2026-08-31: Documento creado. Nada implementado aún. Se investigó a fondo
  el proyecto FactrAPI en `G:\bellotaHosting\Factrapi` (schema Prisma, guías
  de integración para desarrolladores) para basar este plan en el contrato
  real de la API, no en suposiciones.
- 2026-08-31: Se resolvieron las decisiones 3.1, 3.2, 3.4, 3.5 y 3.6 con el
  usuario (ver sección 3, ahora movida a "resuelta"). Sigue pendiente 3.3
  (URL/API Key de FactrAPI para desarrollo) — nada más está bloqueando el
  arranque de la Fase 1. Todavía no se escribió código de ninguna fase.
- 2026-08-31: **Fase 1 implementada y probada** (numeración local atómica +
  puntos de venta + configuración base):
  - `manager.py` (`migrar_base_datos`): tablas nuevas `puntos_venta`,
    `numeracion_local` (sembrada desde el máximo real de `ventas`/
    `cotizaciones`/`pedidos`, no desde 1), `secuencias_ncf_tradicional`
    (esquema listo, sin UI todavía — eso es Fase 6); columnas nuevas en
    `configuracion_general` (`modo_facturacion`, `punto_venta_id`,
    `factrapi_ambiente`, `factrapi_url_base`, `factrapi_api_key`,
    `factrapi_empresa_verificada`) y en `cajas` (`punto_venta_id`); fila
    singleton `id=1` de `configuracion_general` garantizada.
  - `db_conexion.py`: `siguiente_numero(documento, conn=None)` (asignación
    atómica vía `UPDATE ... RETURNING`, segura entre cajas concurrentes) y
    `ver_siguiente_numero(documento)` (solo lectura, para mostrar en
    pantalla sin reservar).
  - `ventas.py`, `cotizaciones.py`, `compras.py`: reemplazado el
    `MAX(...)+1`/hardcodeado (`compras.py` tenía literalmente
    `self.numero_pedido = 2` fijo) por la numeración atómica nueva. En
    `ventas.py` la reserva ocurre DENTRO de la misma transacción que
    inserta la venta (rollback = número liberado).
  - Pantalla nueva `numeracion_fiscal_config.py` ("Numeración y
    Facturación Electrónica" en Configuración): modo de facturación,
    punto de venta fijo de la instalación (alta/edición), campos de
    conexión FactrAPI y numeración local actual de
    solo lectura.
  - Probado: las 53 pantallas del sistema siguen abriendo sin excepción;
    numeración atómica verificada con 2 llamadas consecutivas reales
    (devuelven números consecutivos, sin duplicar); guardar la
    configuración persiste correctamente en PostgreSQL.
  - **Gap histórico detectado durante la Fase 1 (ya resuelto)**:
    `compras.py` → `registrar_pedido()` abre
    `RegistrarPedidoModal`, que **no persiste nada en absoluto** — ni usa
    el `pedido_info` que se le pasa, ni escribe en la tabla `pedidos`, solo
    muestra un mensaje de éxito falso con datos de ejemplo hardcodeados.
    `ver_pedidos()` y `guardar_borrador()` de `compras.py` también son
    stubs. La numeración de pedidos ya quedó correcta (para cuando se
    arregle esto), pero el módulo de Compras/Pedidos a proveedores en sí
    sigue sin funcionar de verdad — es un bug preexistente del mismo tipo
    que los que se corrigieron en la sesión de migración a PostgreSQL, no
    algo que rompió este plan. Marcado para una futura sesión de
  correcciones (no es parte de las 7 fases de este documento). Este hueco fue
  corregido posteriormente: el modal persiste cada línea en `pedidos`, y
  `ver_pedidos()`/`guardar_borrador()` consultan y guardan datos reales.

- 2026-08-31: Auditoría y continuación de la implementación. El punto de
  continuidad real de Claude era una **Fase 2 parcial** (`factrapi_cliente.py`
  y `ecf_integracion.py`) junto con tablas preparatorias de Fases 3 y 6;
  no había avisos de secuencia, UI de NCF/almacenes ni flujo de notas.
  Se añadieron: caché/alertas locales de secuencias, reconciliación de estados
  técnicos, validación de RNC para E31, sincronización del `puntoVentaId`,
  anulación remota de e-CF, notas de crédito/débito formales e informales,
  configuración de rangos NCF tradicionales y gestión inicial de almacenes.
  La venta usa el almacén seleccionado y el modo `ncf_tradicional` reserva
  B02 atómicamente. Las tablas fueron migradas y verificadas en PostgreSQL.
  **Pendiente para cerrar:** prueba contra una URL/API Key real de FactrAPI,
  historial dedicado de notas, emisión de todos los tipos NCF configurables,
  y completar reportes/transferencias y el procedimiento de producción.

- 2026-08-31: Se cerraron más huecos de la integración: el cliente final
  ahora se crea/localiza automáticamente para E32, los clientes con RNC
  pasan por consulta de identidad DGII, las notas formales envían el monto
  de corrección como detalle, y el POS reconcilia estados técnicos en vez
  de consultar continuamente. Se añadieron historial local/formal de notas,
  transferencias atómicas entre almacenes y selección del almacén operativo.

- 2026-08-31: Se corrigió la recuperación ante fallos: el comprobante se
  persiste en estado `pendiente_creacion` antes de llamar a FactrAPI, se
  agregaron llaves idempotentes para crear/enviar/anular y se normalizó la
  lectura de respuestas envueltas en `data`. Los documentos impresos ya no
  inventan un e-NCF: muestran el real o "Pendiente de emisión".
  Las ventas ahora guardan `almacen_id`, restauran stock en el almacén
  correcto al anular y las aperturas de caja guardan el punto de venta.
  Se agregó `GUIA_FACTURACION_ELECTRONICA.md` con requisitos operativos,
  contingencia y salida a producción.

- 2026-08-31: Se corrigió el control operativo del POS: Ventas ya no inicia
  con una caja ficticiamente abierta, exige una sesión del cajero y valida su
  estado dentro de la transacción. Cada venta queda ligada a `caja_id`.
  Gestión de Caja ahora registra ingresos/egresos y el cierre solicita el
  efectivo contado, calculando y guardando esperado, contado y diferencia.

- 2026-08-31: Revisión de preparación para producción: los descuentos del
  cobro ahora se reflejan en líneas, totales y e-CF; el detalle de caja filtra
  por caja y considera movimientos/gastos; combos, proveedores y movimientos
  bancarios dejaron de mostrar confirmaciones simuladas. Se eliminó la carga
  de datos de demostración en clientes, ventas, categorías, servicios,
  sucursales, promociones, cuentas y reportes. Se agregó persistencia para
  `movimientos_bancarios`. La compilación de todos los módulos Python pasó.
  Sigue siendo requisito externo configurar PostgreSQL mediante variables
  `POS_DB_*`, ejecutar migración en el entorno destino y probar FactrAPI con
  credenciales reales de pruebas antes de activar producción.

- 2026-08-31: La auditoría final detectó y corrigió una indentación que
  truncaba la verificación PBKDF2 de contraseñas; se probó hash correcto,
  contraseña incorrecta y compatibilidad heredada. Se retiró una contraseña
  real de `postgresql/README.md`, se añadió `cuenta_destino` para pagos y
  abonos, y PostgreSQL usa `sslmode=require` por defecto en producción.
  Se añadió `requirements.txt` con las dependencias de ejecución, incluido
  `reportlab` para los PDF reales.
- 2026-08-31: La configuración de FactrAPI migra automáticamente una API Key
  heredada en claro a formato cifrado al guardar; en producción bloquea la
  activación de e-CF si falta la clave externa de cifrado.
- 2026-08-31: Se reforzó el preflight y el control operativo: se eliminó la
  pérdida prematura de facturas pendientes, se corrigieron permisos por
  defecto y errores que mostraban cierres/ventas exitosos sin confirmación,
  se hizo persistente el mantenimiento de servicios, cuentas y stock mínimo,
  y se añadió el chequeo de dependencias y esquema para el despliegue.
- 2026-08-31: Se protegió la administración de usuarios para conservar al
  menos un administrador activo y evitar inactivar la cuenta de la sesión.
  El preflight ahora valida administrador activo y matriz de permisos.
- 2026-08-31: Validación de ejecución contra PostgreSQL local `factra_db`:
  `preflight_produccion.py` pasó con código 0, la migración fue idempotente,
  se verificó la columna de códigos de barras, roles/permisos y el rollback
  de la secuencia atómica. El flujo e-CF real sigue requiriendo una URL y
  credencial FactrAPI de pruebas configuradas por el administrador.
- 2026-08-31: La validación de la base local detectó contraseñas heredadas en
  claro. `migrar_base_datos` ahora las convierte automáticamente a PBKDF2 y
  `preflight_produccion.py` rechaza cualquier contraseña sin hash; la prueba
  posterior dejó cero credenciales sin hash y volvió a pasar el preflight.
- 2026-08-31: Se reforzó el respaldo/restauración en Windows: la pantalla
  localiza `pg_dump` y `psql` en el PATH o en instalaciones estándar de
  PostgreSQL. Se verificó la detección y que `pg_dump` genere una salida SQL
  válida en la base local.
- 2026-08-31: El preflight de producción ahora rechaza `sslmode=prefer` y
  `disable`; solo permite conexiones PostgreSQL con `require`, `verify-ca` o
  `verify-full`. El PostgreSQL local usado para pruebas no tiene SSL, por lo
  que debe habilitarse TLS en el servidor destinado a producción.
- 2026-08-31: Se endureció la administración de cuentas: los formularios de
  alta y cambio exigen contraseñas de al menos 8 caracteres con letras y
  números, y el rol inicial pasó de Administrador a Cajero para evitar una
  elevación accidental de privilegios.
- 2026-08-31: Se corrigió el solapamiento vertical del formulario de Empresa:
  los labels de los campos ya no cubren la parte inferior del Entry siguiente.
  El ajuste aplica a nombre comercial, razón social, dirección y todos los
  campos del formulario.
- 2026-08-31: Se alineó el cliente del POS con las respuestas de FactrAPI:
  clientes, comprobantes, notas y consultas RNC aceptan tanto respuestas
  directas como respuestas envueltas en `data`, evitando perder el ID o e-NCF
  cuando cambia el envoltorio HTTP.
- 2026-08-31: Se completó el control de cobros a crédito: los abonos exigen
  caja abierta, se ligan a `caja_id`, conservan medio/cuenta de pago y generan
  un ingreso auditable en `movimientos_caja`. El cuadre filtra esos ingresos
  por efectivo para no contar transferencias como dinero físico.
- 2026-08-31: El gestor de códigos dejó de dibujar patrones decorativos:
  ahora genera imágenes de barras reales con `python-barcode`, valida EAN-13,
  UPC-A y CODE-128, calcula verificadores cuando corresponde y guarda el
  código normalizado en el producto.
- 2026-08-31: La exportación de etiquetas ahora incluye la imagen de barras
  real y el texto del código; si el producto no tiene código, la etiqueta lo
  indica explícitamente sin inventar uno.
- 2026-08-31: Se corrigió la compatibilidad de movimientos bancarios con
  instalaciones existentes (`tipo_movimiento`/`tipo`, `cuenta_id`, `saldo`,
  fecha y hora). Las ventas electrónicas, abonos y movimientos manuales ahora
  actualizan el saldo de la cuenta dentro de la misma transacción; se probó
  commit/rollback real e idempotencia de la migración.
- 2026-08-31: El preflight ahora exige empresa configurada, al menos un punto
  de venta activo y un almacén activo, además de la base, permisos y seguridad
  ya validados. Así no se puede habilitar producción con una instalación sin
  identidad comercial u operación de inventario.
- 2026-08-31: Se corrigió la anulación de e-CF confirmada por FactrAPI: además
  de actualizar el estado fiscal, archiva la venta anulada, restaura el stock
  agregado y del almacén correspondiente, y registra el movimiento de entrada
  para mantener la trazabilidad local.
- 2026-08-31: Se cerró un hueco de auditoría financiera: los movimientos
  bancarios manuales, las ventas no cobradas en efectivo y los abonos ahora
  guardan el usuario responsable. El preflight también verifica explícitamente
  `python-barcode`, y se repitieron compilación, importación y migración
  idempotente sin errores.
- 2026-08-31: Se añadió protección contra retiros, transferencias o cobros
  automáticos que dejarían una cuenta bancaria con saldo negativo. Los pedidos
  a proveedores y sus borradores también quedaron confirmados como persistentes
  en base de datos, eliminando el antiguo hueco documentado.
- 2026-08-31: Se corrigió la liberación de conexiones PostgreSQL: cada bloque
  transaccional confirma o revierte y cierra la conexión al salir. Esto evita
  agotar conexiones después de muchas operaciones durante una jornada.
- 2026-08-31: El preflight de producción ahora comprueba también `pg_dump` y
  `psql`, valida las tablas financieras/inventario/auditoría completas y, si
  está activo e-CF, exige URL y API Key de FactrAPI junto con la clave externa
  de cifrado.
- 2026-08-31: El preflight fiscal también exige que el punto de venta local
  esté enlazado con su identificador remoto de FactrAPI antes de permitir el
  arranque en modo e-CF.
- 2026-08-31: El preflight ahora detecta datos históricos sin caja o almacén
  y facturas pendientes sin caja. No se reasignan ni borran automáticamente:
  deben revisarse antes del corte para conservar la trazabilidad contable.
- 2026-08-31: Se añadió `auditoria_preproduccion.py`, una revisión no
  destructiva que muestra vínculos históricos, credenciales, cajas abiertas
  y comprobantes huérfanos antes del corte.
- 2026-08-31: Se corrigió la anulación de facturas locales: se restauran
  inventario y almacén, se registra el reembolso en la caja o la reversión
  bancaria, se exige usuario autenticado y se bloquea la operación si la caja
  original ya está cerrada.
- 2026-08-31: Se añadió un índice único parcial para impedir dos cajas abiertas
  simultáneamente para el mismo cajero incluso si concurren dos terminales.
- 2026-08-31: Se añadió unicidad de códigos de barras no vacíos a nivel de
  PostgreSQL, además de la validación de la interfaz, para evitar duplicados
  bajo concurrencia entre terminales.
- 2026-08-31: Se corrigió el callback del modal de pagos: la confirmación ya
  recibe la cuenta bancaria seleccionada, evitando que las ventas con tarjeta
  o transferencia fallen al confirmar por una firma de función incompleta.
- 2026-08-31: `auditoria_preproduccion.py --detalles` ahora muestra los IDs
  y responsables concretos de usuarios duplicados y ventas históricas sin caja
  o almacén, para resolverlos con trazabilidad.
- 2026-08-31: El registro de usuarios ya no muestra éxito si la inserción
  falla y rechaza nombres de acceso duplicados de forma case-insensitive,
  incluso en el flujo de registro controlado de desarrollo.
- 2026-08-31: Los cierres de caja y la anulación de gastos ahora verifican
  `rowcount` antes de confirmar éxito, evitando mensajes incorrectos cuando
  otra terminal ya completó la operación.
- 2026-08-31: Las cuentas bancarias activas ahora tienen unicidad por banco y
  número tanto en PostgreSQL como en la validación del formulario.
- 2026-08-31: Las búsquedas de Ventas por almacén ya no muestran el stock
  global cuando el producto no está asignado al almacén operativo; así se
  evita ofrecer un producto que luego no puede descontarse de ese almacén.
- 2026-08-31: Se eliminó la distribución ficticia del reporte de medios de
  pago. Ahora agrupa ventas y créditos reales por medio y período, y muestra
  cero cuando no existen transacciones.
- 2026-08-31: La pantalla de Gastos ya no inicia con fecha y hora de ejemplo;
  muestra la fecha y hora reales desde el primer instante.
- 2026-08-31: El reporte de caja dejó de mostrar un abono ficticio de RD$5,000
  y ahora suma los abonos reales de la caja; también excluye facturas guardadas
  como pendientes de las ventas a crédito confirmadas.
- 2026-08-31: Los reportes de rentabilidad y el formulario de promociones ya
  no usan fechas vencidas hardcodeadas; calculan sus fechas iniciales con el
  día actual.
- 2026-08-31: La auditoría detectó nombres de usuario duplicados en la base
  heredada. El login ya rechaza accesos ambiguos, los formularios impiden crear
  nuevos duplicados y el preflight/auditoría bloquean el corte hasta depurarlos.
- 2026-08-31: La migración crea además un índice único case-insensitive para
  nombres de usuario cuando la base ya no contiene duplicados; así el problema
  no puede volver a aparecer por concurrencia después de la depuración.

---

## 1. Por qué existe este plan

El usuario detectó que el sistema actual (Punto de Venta en Python/Tkinter +
PostgreSQL, ya migrado — ver `postgresql/README.md`) **numera facturas con
un simple `MAX(factura)+1` local**, sin ningún concepto de:

- Secuencias fiscales autorizadas (NCF/e-NCF) con rango, vencimiento y
  aviso de agotamiento.
- Facturación electrónica DGII (República Dominicana) — el diferencial que
  el usuario quiere que tenga su sistema frente a la competencia.
- Múltiples cajas/terminales con numeración fiscal centralizada (crítico:
  si dos cajas asignan e-NCF de forma independiente, se duplican o se
  pierden números — esto NO se puede resolver con un `MAX()+1` local).
- Múltiples almacenes/sucursales con stock independiente.
- Notas de crédito/débito (corrección fiscal formal de una factura ya
  emitida — hoy el sistema solo sabe "anular y borrar", que no es lo mismo
  y es inválido para un e-CF ya aceptado por DGII).
- Avisos cuando una secuencia se está agotando o vence.
- Convivencia entre negocios informales (sin RNC / no obligados a e-CF
  todavía) y negocios formales dados de alta en DGII.

El usuario ya tiene una plataforma propia para todo lo fiscal: **FactrAPI**
(`G:\bellotaHosting\Factrapi`), un backend NestJS+Prisma multiempresa que
YA implementa: autenticación de tenants, clientes, catálogos DGII
completos, secuencias de e-NCF, generación/firma/envío de XML a DGII,
webhooks, reportes 606/607/contable, recordatorios de secuencia y
certificado, multi-punto-de-venta, contingencia offline, etc. **No hay que
reconstruir nada de eso en el POS.** El POS (este proyecto) debe consumirlo
como cliente HTTP, exactamente como está documentado para "Factra POS" en
`docs/GUIA-INTEGRACION-DESARROLLADORES.md` e `docs/INTEGRACION-SISTEMAS.md`
de FactrAPI.

**Regla de oro de todo este plan: el POS nunca genera un e-NCF ni firma un
XML localmente.** Eso lo hace FactrAPI. El POS solo:
1. Junta los datos comerciales de la venta (cliente, líneas, impuestos por
   línea, forma de pago).
2. Se los manda a FactrAPI.
3. Guarda lo que FactrAPI le devuelve (id, eNCF, estado) y lo muestra/imprime.
4. Hace seguimiento del estado (webhook o consulta) hasta que quede
   `aceptado`, `rechazado` o `anulado`.

---

## 2. Decisiones que YA están tomadas (no las vuelvas a discutir)

1. **FactrAPI es el motor fiscal único.** El POS es un cliente de FactrAPI,
   no un competidor de esa lógica. Esto reduce brutalmente el alcance: no
   hay que implementar firma XML, XSD, comunicación P2P con DGII, cálculo
   de ITBIS por el POS, etc. — todo eso ya existe en FactrAPI.
2. **El dinero se maneja como `float`/`DOUBLE PRECISION` en el POS** (ya
   migrado así, ver `postgresql/README.md`) pero **FactrAPI recibe
   precios/cantidades y ES FACTRAPI quien calcula los totales con
   Decimal** — el POS nunca debe mandar totales ya calculados ni confiar
   en ellos para lo fiscal. Sí puede seguir mostrando su propio total
   estimado en pantalla mientras arma el carrito (UX), pero el total
   *fiscal* final es el que devuelve FactrAPI al crear el comprobante.
3. **`fecha`/`hora` siguen siendo `TEXT` en el POS** (ver
   `postgresql/README.md`), no se tocan por esta iniciativa.
4. **La API Key de FactrAPI se guarda solo en la base de datos del POS**
   (nunca hardcodeada, nunca en un archivo de config en texto plano fuera
   de la BD), y las llamadas a FactrAPI las hace el propio proceso Python
   del POS actuando como "backend" (no hay separación cliente/servidor en
   esta app de escritorio, así que el POS mismo es "el servidor" a efectos
   de la guía de integración de FactrAPI).
5. **Idempotencia obligatoria**: cada venta que dispare la creación de un
   comprobante en FactrAPI debe generar un `Idempotency-Key` estable
   (ej. `pos-{puntoVentaCodigo}-{numero_factura_local}-{timestamp}`) y
   guardarlo ANTES de llamar a la API, para poder reintentar sin duplicar.
6. **Multi-caja fiscal = secuencia centralizada.** Ninguna caja asigna
   e-NCF localmente. Todas piden el siguiente número a FactrAPI (que lo
   asigna atómicamente por empresa). El POS solo etiqueta cada comprobante
   con su `puntoVentaId` para trazabilidad/reportes, no para numerar.

---

## 3. Decisiones — RESUELTAS el 2026-08-31 (más una que sigue pendiente)

### 3.1 Modos de facturación — RESUELTO: los 3 conviven

El sistema debe soportar **3 modos**, configurables (ver 5.1):

- **(A) Informal / ticket sin valor fiscal** — lo que el sistema ya hace
  hoy (numeración local).
- **(B) NCF tradicional (rangos autorizados directamente por DGII, sin
  e-CF)** — **confirmado que se necesita.** FactrAPI NO lo modela (su
  `Secuencia` solo cubre e-NCF, `tipoECF` 31-47). Este modo se construye
  100% local: tabla de rangos autorizados por tipo de comprobante
  (B01/B02/B14/B15, etc. — falta confirmar con el usuario la lista exacta
  de tipos NCF tradicionales que necesita antes de programarlo, ver nueva
  pregunta 3.1.a) + correlativo dentro de ese rango, sin ayuda de FactrAPI.
- **(C) e-CF vía FactrAPI** — el caso completo, con envío real a DGII.

**Pregunta nueva 3.1.a (pendiente)**: para el modo (B), ¿qué tipos de NCF
tradicional necesita el usuario soportar (B01 Crédito Fiscal, B02 Consumo,
B14 Régimen Especial, B15 Gubernamental, B04 Nota de Crédito, etc.), y de
dónde salen los rangos autorizados (¿los captura el usuario a mano en una
pantalla de "Configurar rangos NCF", como hace hoy con las secuencias que
DGII le entrega en un oficio/portal)? Se resuelve al programar la Fase 1/6
de este modo, no bloquea el arranque de las demás fases.

### 3.2 Alcance de tipos de e-CF — RESUELTO

`31` (Crédito Fiscal), `32` (Consumo), `33`/`34` (Notas de Débito/Crédito)
y `43` (Gastos Menores) entran en el alcance. `41` (Compras), `44`
(Regímenes Especiales), `45` (Gubernamental), `46` (Exportaciones) y `47`
(Pagos al Exterior) quedan fuera de esta iniciativa por ahora (se pueden
agregar después, el catálogo ya está documentado en la sección 4).

### 3.3 Ambiente de FactrAPI para desarrollo — PENDIENTE (única que sigue abierta)

Falta: URL base del ambiente de Pruebas y una API Key `ft_test_...` para
poder programar y probar el cliente HTTP real. Sin esto, la Fase 2
(cliente FactrAPI) se puede escribir pero no probar contra el servicio real
— se puede avanzar con un stub/mock mientras tanto si el usuario lo pide.

### 3.4 Multi-almacén — RESUELTO: opción real

Stock real por almacén (tabla `inventario_almacen`) con transferencias
entre almacenes. Ver el detalle ya escrito en la sección 5.5 — queda
confirmado, ya no es condicional.

### 3.5 Multi-caja — RESUELTO: instalación fija

Cada PC/instalación se configura una sola vez con su `PuntoVenta` fijo
(config de aplicación, un valor en `configuracion_general` o en
`puntos_venta` marcado como "el de esta instalación"). No hay selección de
caja en el login.

### 3.6 Notas de crédito/débito — RESUELTO: asistente automático

Un único flujo ("Anular/Corregir factura") que decide internamente si
corresponde `POST /comprobantes/{id}/anular` o generar una Nota de
Crédito/Débito (33/34), guiando al cajero paso a paso.

---

## 4. Contrato de integración con FactrAPI (resumen operativo)

_(Extraído y condensado de `docs/GUIA-INTEGRACION-DESARROLLADORES.md` e
`docs/INTEGRACION-SISTEMAS.md` de FactrAPI. Si hay dudas, esos dos archivos
son la fuente de verdad — no este resumen.)_

- **Base URL**: `/api/v1` para todo lo de negocio. Autenticación
  servidor-a-servidor con header `x-api-key: ft_live_...` (o `ft_test_...`
  en pruebas). **Nunca mandar `empresaId`** — el tenant lo determina la key.
- **Flujo de una venta con e-CF**:
  1. `POST /api/v1/clientes` (crear/localizar cliente).
  2. Si el cliente tiene RNC: `GET /api/v1/consulta-rnc/{rnc}` antes de
     facturar tipo `31`, y no dejar que el usuario pise esos datos oficiales
     a mano.
  3. `POST /api/v1/comprobantes` con `Idempotency-Key` único. Body: ver
     sección 4 de la guía (`tipoECF`, `clienteId`, `tipoIngresos`,
     `tipoPago`, `formasPago[]`, `detalles[]` con
     `indicadorBienoServicio`/`indicadorFacturacion`/`cantidadItem`/
     `unidadMedida`/`precioUnitarioItem`). Guardar de la respuesta: `id`,
     `eNCF`, `estadoActual`, `solicitudId`, totales.
  4. `POST /api/v1/comprobantes/{id}/enviar` (dispara el envío real a
     DGII; pasa a `pendiente`).
  5. Seguimiento por webhook (preferido) o
     `POST /api/v1/comprobantes/{id}/consultar` (reconciliación, no
     polling agresivo).
  6. Fiscalmente terminado solo en `aceptado`, `rechazado` o `anulado`.
- **Catálogos DGII** (consumir de `GET /api/v1/catalogos`, no
  hardcodear salvo para desarrollo/pruebas rápidas — la lista real vive en
  FactrAPI y puede tener más entradas de las que este plan documenta):
  - `tipos-ecf`: 31 Crédito Fiscal, 32 Consumo, 33 Nota Débito,
    34 Nota Crédito, 41 Compras, 43 Gastos Menores, 44 Regímenes
    Especiales, 45 Gubernamental, 46 Exportaciones, 47 Pagos al Exterior.
  - `formas-pago` (`formaPago`, hasta 7 por documento): 1 Efectivo,
    2 Cheque/Transferencia/Depósito, 3 Tarjeta Débito/Crédito,
    4 Venta a Crédito, 5 Bonos/Certificados regalo, 6 Permuta,
    7 Nota de crédito, 8 Otras.
  - `tipos-pago` (`tipoPago`, condición): 1 Contado, 2 Crédito, 3 Gratuito.
  - `indicador-facturacion` (por línea): 0 No facturable, 1 Gravado 18%,
    2 Gravado 16%, 3 Gravado 0%, 4 Exento.
  - `codigos-modificacion` (para Notas 33/34): 1 Anula el NCF modificado,
    2 Corrige texto, 3 Corrige montos, 4 Reemplazo por contingencia,
    5 Referencia a Factura de Consumo.
  - Además existen catálogos de `unidades-medida`,
    `indicador-bien-servicio`, `provincia-municipio` (usar los códigos de
    6 dígitos, no el nombre libre, para el XML), `monedas`, etc.
- **Multi-caja**: registrar cada caja como `PuntoVenta`
  (`POST /api/v1/puntos-venta`, `codigo` estable ej. `S01-C01`), mandar
  `puntoVentaId` en cada comprobante.
- **Notas de Crédito/Débito**: comprobante tipo `33`/`34` con
  `ncfModificado`, `rncOtroContribuyente`, `fechaNcfModificado`,
  `codigoModificacion` apuntando al e-NCF original.
- **Anulación**: `POST /api/v1/comprobantes/{id}/anular` (dentro de las
  reglas/ventana que aplique; no es un DELETE local).
- **Secuencias**: `GET /api/v1/secuencias` (listar) y
  `GET /api/v1/secuencias/{id}` — cada una tiene `tipoECF`, `ambiente`,
  `secuenciaDesde`, `secuenciaHasta`, `secuenciaActual`,
  `fechaVencimiento`, `activa`. **El POS debe leer esto para mostrar un
  aviso local de "quedan N comprobantes" o "vence el DD/MM"**, además de
  que FactrAPI ya manda sus propios recordatorios por su lado
  (`TipoRecordatorio.secuencia` en su base — es un aviso administrativo del
  SaaS, no sustituye que el cajero vea el aviso en pantalla mientras
  trabaja).
- **Idempotencia**: header `Idempotency-Key` estable por operación
  comercial. Mismo timeout → repetir exactamente la misma key y el mismo
  body; nunca generar una key nueva en el reintento.
- **Errores**: forma estándar
  `{ exito, codigo, mensaje, detalles, solicitudId }`. Programar contra
  `codigo` + status HTTP + `estadoActual`, nunca contra el texto de
  `mensaje`. `409` = conflicto (no reintentar solo), `422` = validación (no
  reintentar sin corregir), `429` = backpressure (respetar `Retry-After`),
  `5xx` = posible transitorio (reintentar con backoff).
- **Webhooks**: `POST /api/v1/webhooks` para registrar destino. Firma
  `X-FactrAPI-Firma: sha256=...` HMAC del cuerpo crudo — el POS necesita
  poder recibir esto, lo cual implica **levantar un pequeño servidor HTTP
  local/expuesto** (o usar polling controlado como alternativa si el POS no
  puede exponer un endpoint público — ver sección 6.2, es una decisión
  técnica pendiente).
- **Offline/contingencia**: el POS debe guardar localmente el payload +
  `Idempotency-Key` de cualquier venta que no se pudo mandar por falta de
  conexión, y reintentarla tal cual al recuperar internet. El modo
  `contingencia` completo requiere secuencia/certificado/procedimiento
  autorizado específico — no activarlo "automáticamente" sin que el
  usuario confirme que lo tiene habilitado con DGII.

---

## 5. Cambios de modelo de datos propuestos (PostgreSQL, `factra_db`)

Todo esto es propuesta — falta validarla contra las decisiones pendientes
de la sección 3 antes de aplicarla. Nombrar todo en español, consistente
con el resto del esquema (ver `postgresql/esquema.sql`).

### 5.1 Configuración fiscal de la empresa

```sql
-- Extiende configuracion_general (o tabla nueva 1-fila "configuracion_fiscal")
ALTER TABLE configuracion_general ADD COLUMN modo_facturacion TEXT DEFAULT 'informal';
  -- 'informal' | 'ncf_tradicional' | 'ecf_factrapi'
ALTER TABLE configuracion_general ADD COLUMN factrapi_ambiente TEXT DEFAULT 'pruebas';
  -- 'pruebas' | 'certificacion' | 'produccion'
ALTER TABLE configuracion_general ADD COLUMN factrapi_url_base TEXT;
ALTER TABLE configuracion_general ADD COLUMN factrapi_api_key TEXT;  -- cifrar en reposo, ver 6.3
ALTER TABLE configuracion_general ADD COLUMN factrapi_empresa_verificada BOOLEAN DEFAULT FALSE;
```

### 5.2 Puntos de venta (cajas/terminales)

```sql
CREATE TABLE puntos_venta (
    id                    SERIAL PRIMARY KEY,
    codigo                VARCHAR(20) NOT NULL UNIQUE,  -- ej. 'S01-C01'
    nombre                VARCHAR(100) NOT NULL,
    sucursal_id           INTEGER REFERENCES sucursal(id),
    factrapi_punto_venta_id VARCHAR(50),  -- id devuelto por FactrAPI al registrar
    estado                VARCHAR(15) DEFAULT 'Activo' CHECK (estado IN ('Activo','Inactivo')),
    fecha_creacion        TIMESTAMP DEFAULT now()
);

-- cajas (turnos) pasa a referenciar el punto de venta donde se abrió:
ALTER TABLE cajas ADD COLUMN punto_venta_id INTEGER REFERENCES puntos_venta(id);
```

### 5.3 Secuencias / numeración local

```sql
-- Espejo LOCAL y liviano del estado de secuencias de FactrAPI, para poder
-- mostrar avisos sin llamar a la API en cada venta. Se refresca periódicamente
-- (ver 6.4) y NUNCA se usa para asignar el número real — solo para UI.
CREATE TABLE secuencias_cache (
    id                  SERIAL PRIMARY KEY,
    factrapi_secuencia_id VARCHAR(50) NOT NULL UNIQUE,
    tipo_ecf            INTEGER NOT NULL,
    ambiente            VARCHAR(20) NOT NULL,
    secuencia_desde     BIGINT NOT NULL,
    secuencia_hasta     BIGINT NOT NULL,
    secuencia_actual    BIGINT NOT NULL,
    fecha_vencimiento   TEXT NOT NULL,
    activa              BOOLEAN DEFAULT TRUE,
    fecha_actualizacion TIMESTAMP DEFAULT now()
);

-- Numeración local para modo 'informal' (tickets sin valor fiscal),
-- independiente por tipo de documento para no chocar con e-CF:
CREATE TABLE numeracion_local (
    id            SERIAL PRIMARY KEY,
    documento     VARCHAR(30) NOT NULL UNIQUE,  -- 'ticket_venta','cotizacion','pedido', etc.
    siguiente     BIGINT NOT NULL DEFAULT 1
);
```

### 5.4 Comprobantes fiscales emitidos vía FactrAPI

```sql
-- Vínculo entre una venta local (factura de la tabla `ventas`) y el
-- comprobante fiscal real en FactrAPI. Una venta puede no tener fila aquí
-- (modo informal) o tener una (modo e-CF).
CREATE TABLE comprobantes_fiscales (
    id                    SERIAL PRIMARY KEY,
    factura_local         INTEGER NOT NULL,          -- ventas.factura
    factrapi_comprobante_id VARCHAR(50) NOT NULL UNIQUE,
    tipo_ecf              INTEGER NOT NULL,
    e_ncf                 VARCHAR(20),
    estado_actual         VARCHAR(20) NOT NULL,       -- espejo de EstadoComprobante
    solicitud_id          VARCHAR(50),
    idempotency_key       VARCHAR(100) NOT NULL UNIQUE,
    ncf_modificado         VARCHAR(20),               -- para notas 33/34
    codigo_modificacion    INTEGER,
    punto_venta_id        INTEGER REFERENCES puntos_venta(id),
    payload_enviado       JSONB,                      -- para reintento offline
    fecha_creacion        TIMESTAMP DEFAULT now(),
    fecha_actualizacion   TIMESTAMP DEFAULT now()
);
CREATE INDEX idx_comprobantes_fiscales_factura ON comprobantes_fiscales (factura_local);
CREATE INDEX idx_comprobantes_fiscales_estado ON comprobantes_fiscales (estado_actual);

-- Cola de reintento offline (ver 6.5)
CREATE TABLE cola_envios_pendientes (
    id                SERIAL PRIMARY KEY,
    idempotency_key   VARCHAR(100) NOT NULL UNIQUE,
    endpoint          VARCHAR(100) NOT NULL,
    payload           JSONB NOT NULL,
    intentos          INTEGER DEFAULT 0,
    ultimo_error      TEXT,
    fecha_creacion    TIMESTAMP DEFAULT now()
);
```

### 5.5 Multi-almacén

```sql
CREATE TABLE almacenes (
    id        SERIAL PRIMARY KEY,
    nombre    VARCHAR(100) NOT NULL,
    sucursal_id INTEGER REFERENCES sucursal(id),
    estado    VARCHAR(15) DEFAULT 'Activo' CHECK (estado IN ('Activo','Inactivo'))
);

CREATE TABLE inventario_almacen (
    id           SERIAL PRIMARY KEY,
    producto_id  INTEGER NOT NULL REFERENCES inventario(id) ON DELETE CASCADE,
    almacen_id   INTEGER NOT NULL REFERENCES almacenes(id) ON DELETE CASCADE,
    stock        INTEGER NOT NULL DEFAULT 0,
    UNIQUE (producto_id, almacen_id)
);

CREATE TABLE transferencias_almacen (
    id               SERIAL PRIMARY KEY,
    producto_id      INTEGER NOT NULL REFERENCES inventario(id),
    almacen_origen_id INTEGER NOT NULL REFERENCES almacenes(id),
    almacen_destino_id INTEGER NOT NULL REFERENCES almacenes(id),
    cantidad         INTEGER NOT NULL,
    fecha            TEXT NOT NULL,
    hora             TEXT NOT NULL,
    usuario          VARCHAR(150)
);
```

_(Nota: `inventario.stock` actual quedaría como total agregado, o se
elimina y se calcula con `SUM(inventario_almacen.stock)` — decidir al
implementar, impacta muchas pantallas: `ventas.py`, `producto_modal.py`,
`compras.py`, `alerta_stock_bajo.py`, todos los reportes de inventario.)_

### 5.6 Notas de crédito/débito (representación local, espejo de FactrAPI)

Se apoya en `comprobantes_fiscales` (tipo_ecf 33/34 + `ncf_modificado`).
Para modo informal (sin FactrAPI) hace falta además una tabla local propia,
ya que hoy no existe ningún concepto de nota de crédito/débito interna:

```sql
CREATE TABLE notas_credito_debito_locales (
    id              SERIAL PRIMARY KEY,
    tipo            VARCHAR(10) NOT NULL CHECK (tipo IN ('Credito','Debito')),
    factura_afectada INTEGER NOT NULL,  -- ventas.factura original
    motivo          VARCHAR(255),
    monto           DOUBLE PRECISION NOT NULL,
    fecha           TEXT NOT NULL,
    hora            TEXT NOT NULL,
    cajero          VARCHAR(150)
);
```

### 5.7 NCF tradicional (modo B, sin FactrAPI)

Rangos que DGII entrega directamente al contribuyente (fuera de e-CF).
El usuario los captura a mano en una pantalla de configuración; el sistema
solo controla el correlativo y avisa cuando se agota, igual que hace
FactrAPI con las secuencias de e-CF pero completamente local.

```sql
CREATE TABLE secuencias_ncf_tradicional (
    id                SERIAL PRIMARY KEY,
    tipo_ncf          VARCHAR(10) NOT NULL,   -- 'B01','B02','B14','B15','B04', etc. (confirmar lista exacta, pregunta 3.1.a)
    secuencia_desde   BIGINT NOT NULL,
    secuencia_hasta   BIGINT NOT NULL,
    secuencia_actual  BIGINT NOT NULL,
    fecha_vencimiento TEXT,
    activa            BOOLEAN DEFAULT TRUE,
    fecha_creacion    TIMESTAMP DEFAULT now()
);
```

`ventas.py`/el asistente de facturación deben asignar el siguiente número
con `UPDATE secuencias_ncf_tradicional SET secuencia_actual = secuencia_actual + 1
WHERE id = ? RETURNING secuencia_actual` (atómico, mismo principio que
FactrAPI usa para e-NCF: nunca `MAX()+1`), y mostrar el mismo tipo de
aviso de agotamiento que para e-CF (Fase 3).

---

## 6. Cuestiones técnicas a resolver antes de programar

1. **Cliente HTTP en Python**: el proyecto no tiene ninguna dependencia de
   red hoy (todo es Tkinter + `sqlite3`/`psycopg2`). Hace falta agregar
   `requests` (o `httpx`) al entorno, y un módulo nuevo `factrapi_cliente.py`
   que centralice: base URL por ambiente, header `x-api-key`, timeout
   30-60s, reintentos con backoff+jitter en `5xx`, manejo de `429` con
   `Retry-After`, y el `Idempotency-Key`.
2. **Webhooks vs. polling**: recibir webhooks requiere que el POS exponga
   un endpoint HTTP público — no es trivial para una app de escritorio
   corriendo en la PC de una tienda (NAT, IP dinámica, etc.). Alternativas:
   (a) un pequeño servicio intermediario en un servidor del usuario que sí
   reciba el webhook y el POS lo consulte, o (b) el POS hace **polling
   controlado** con `POST /comprobantes/{id}/consultar` para los
   comprobantes que sigan en estado técnico (no `aceptado`/`rechazado`/
   `anulado`), con backoff, tal como la guía permite como reconciliación.
   **Recomendación para la v1: polling controlado**, más simple y sin
   requerir infraestructura pública; migrar a webhooks si más adelante hay
   un componente servidor propio del usuario.
3. **Cifrado de la API Key en la base de datos**: no guardarla en texto
   plano en PostgreSQL. Evaluar `cryptography` (Fernet) con una clave
   derivada de una passphrase local (ej. guardada en el registro de
   Windows o un archivo protegido por el SO), documentando bien el
   trade-off para una app de escritorio de un solo usuario.
4. **Refresco del caché de secuencias**: job periódico (ej. al abrir el
   módulo de Ventas, o cada N minutos con `after()` de Tkinter) que llama
   `GET /api/v1/secuencias` y actualiza `secuencias_cache`, comparando
   `secuencia_actual` contra `secuencia_hasta` para decidir el aviso
   (ej. "quedan 50 o menos" / "vence en 30 días o menos" — umbrales a
   definir con el usuario).
5. **Cola offline**: `cola_envios_pendientes` + un hilo/job en background
   que reintenta al recuperar conexión. Debe ser IDÉNTICO al payload
   original (mismo `Idempotency-Key`) — nunca reconstruir la venta desde
   cero en el reintento.
6. **No romper lo que ya funciona**: el modo informal actual (numeración
   local, `ventas`/`facturas_pendientes`/`facturas_anuladas`, cuentas por
   cobrar, etc., todo lo que ya se migró a PostgreSQL y se dejó funcionando
   en la sesión anterior) debe seguir funcionando igual para negocios que
   configuren `modo_facturacion = 'informal'`. La integración con FactrAPI
   es una capa adicional que se activa por configuración, no un reemplazo
   obligatorio.

---

## 7. Roadmap por fases

Cada fase debe dejar el sistema funcionando (no fases a medias que rompan
lo existente). Actualizar la sección 0 al cerrar cada una.

### Fase 0 — Decisiones (bloqueante, no requiere código)
Resolver la sección 3 completa con el usuario. Sin esto, cualquier código
de facturación electrónica corre el riesgo de rehacerse.

### Fase 1 — Numeración y configuración base (sin FactrAPI todavía)
- Pantalla nueva en Configuración: "Numeración y Comprobantes Fiscales".
- Tablas `configuracion_general` (columnas nuevas), `puntos_venta`,
  `numeracion_local`.
- Reemplazar los `MAX(...)+1` locales de `ventas.py`/`cotizaciones.py`/
  `compras.py` por `numeracion_local` (con `UPDATE ... RETURNING` atómico,
  no lectura+escritura separada — importante también en modo informal para
  evitar números repetidos con multi-caja).
- Vincular `cajas.punto_venta_id`. Pantalla o selector de punto de venta al
  operar (según lo que decida 3.5).

### Fase 2 — Cliente FactrAPI + modo e-CF para Ventas (implementada, falta prueba real)
- `factrapi_cliente.py`: autenticación, manejo de errores/reintentos,
  `Idempotency-Key`.
- Alta de empresa/cliente/puntoVenta contra FactrAPI desde Configuración.
- `ventas.py`: cuando `modo_facturacion = 'ecf_factrapi'`, el flujo de
  pago crea el comprobante en FactrAPI (tipo 32 o 31 según el cliente),
  lo envía, guarda en `comprobantes_fiscales`, y solo entonces confirma la
  venta al cajero con el e-NCF real. Si fallá la conexión: cola offline
  (sección 6.5), nunca se pierde la venta ni se inventa un número local.
- Reemplazar la impresión/generación de `documentos.py` para mostrar el
  e-NCF real cuando exista.

### Fase 3 — Avisos de secuencia (implementada)
- Refresco periódico de `secuencias_cache` (sección 6.4).
- Banner/alerta visible en Ventas y en un tablero de Configuración cuando
  una secuencia esté por agotarse o vencer.

### Fase 4 — Notas de crédito/débito (implementación inicial)
- Asistente de anulación/corrección (según 3.6): decide entre
  `/comprobantes/{id}/anular` y crear un tipo 33/34.
- Pantalla de historial de notas de crédito/débito (formal e informal).
- Reemplaza/community con `anular_factura_modal.py` actual, que hoy solo
  sabe hacer el equivalente informal (mover filas y restaurar stock).

### Fase 5 — Multi-caja completo (base implementada; reportes históricos pendientes)
- Alta de `PuntoVenta` en FactrAPI reflejada en `puntos_venta` local.
- Reportes por caja/punto de venta (ya hay algo de esto en
  `reporte_caja.py`, `caja_detalle.py` — extenderlos con `punto_venta_id`).

### Fase 6 — Multi-almacén y NCF tradicional (base implementada; cobertura de pantallas pendiente)
- Multi-almacén: es el bloque más grande de reescritura de UI (toda
  pantalla que hoy asume `inventario.stock` como un solo número) —
  `inventarios.py`, `producto_modal.py`, `ventas.py`, `compras.py`,
  `alerta_stock_bajo.py`, reportes de inventario.
- NCF tradicional (modo B, sección 5.7): pantalla de configuración de
  rangos, asignación atómica de correlativo, mismo aviso de agotamiento
  que la Fase 3. Requiere resolver antes la pregunta 3.1.a (lista exacta
  de tipos NCF tradicionales y cómo se capturan los rangos).

### Fase 7 — Soporte formal/informal pulido
- Que el toggle de modo de facturación en Configuración sea seguro de
  cambiar (validaciones, no perder historial, mensajes claros de qué
  implica cada modo).
- Documentación de usuario final (no solo este plan técnico) sobre qué
  hace falta tener listo con DGII/FactrAPI antes de activar e-CF en
  producción (RNC, certificado `.p12`, secuencias autorizadas — ver la
  "Lista de salida a producción", sección 11 de la guía de FactrAPI).

---

## 8. Riesgos y advertencias explícitas

- **No inventar reglas fiscales.** Todo lo que sea "¿esto es válido para
  DGII?" se resuelve preguntando a FactrAPI (sus catálogos, sus
  validaciones, sus códigos de error) o al usuario — nunca asumiendo.
- **No marcar nada como `aceptado` localmente.** Solo FactrAPI sabe si DGII
  aceptó un comprobante. El POS refleja el estado que le devuelven, no lo
  decide.
- **Multi-caja sin secuencia centralizada = e-NCF duplicados** — un bug
  aquí no es cosmético, es un incumplimiento fiscal real. Cualquier código
  que toque numeración fiscal debe revisarse con más cuidado que el resto
  del sistema.
- **La API Key es un secreto de producción real.** Tratarla con el mismo
  cuidado que engaña llevar en `postgresql/README.md` a la contraseña de
  PostgreSQL: nunca en capturas de pantalla, nunca en texto plano
  compartible.
- **Este plan es grande.** Si el contexto de la sesión que lo ejecuta se
  agota a mitad de una fase, debe dejar la sección 0 actualizada con
  exactamente qué se hizo y qué falta de esa fase, no solo "en progreso".
