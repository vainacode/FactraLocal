# Refactorización de arquitectura de Factra Negocio

## Alcance de esta entrega

Esta entrega cubre las fases de separación de código previstas para Ventas/POS, Inventario, Caja, Clientes/CxC, Compras/Proveedores, Cotizaciones, FactrAPI/fiscal y Reportes/Configuración. No cambia PostgreSQL, no normaliza ventas, no mueve pantallas, no cambia estilos, no agrega backend web y no implementa hardware. La UI sigue siendo Tkinter y `db_conexion.py` sigue siendo el adaptador PostgreSQL.

La estrategia usada es incremental: se agregan capas nuevas y `ventas.py` las consume, mientras los módulos auxiliares que pertenecen a fases posteriores conservan temporalmente su acceso actual.

## Estructura creada

```text
dominio/
├── __init__.py
└── ventas/
    ├── __init__.py
    ├── modelos.py
    ├── excepciones.py
    └── reglas.py
repositorios/
├── __init__.py
├── repositorio_caja.py
├── repositorio_clientes.py
└── repositorio_productos.py
servicios/
├── __init__.py
├── servicio_ventas.py
├── servicio_inventario.py
├── servicio_caja.py
├── servicio_clientes.py
├── servicio_cuentas_cobrar.py
├── servicio_compras.py
├── servicio_cotizaciones.py
├── servicio_fiscal.py
├── servicio_reportes.py
└── servicio_configuracion.py
infraestructura/
├── __init__.py
├── hardware/__init__.py
└── impresion/__init__.py
tests/
├── __init__.py
└── test_ventas_reglas.py
```

Los paquetes `infraestructura/hardware` e `infraestructura/impresion` son únicamente espacios arquitectónicos. No contienen drivers ni implementan impresión directa.

## Componentes y responsabilidades

### Dominio

- `dominio/ventas/modelos.py`: `ItemVenta`, `SolicitudVenta`, `ResultadoVenta` y `ResultadoPendiente`. Usa `Decimal` en los cálculos nuevos y convierte a `float` únicamente en el borde hacia las columnas PostgreSQL actuales.
- `dominio/ventas/reglas.py`: conversión monetaria, total de líneas, validación de venta vacía, pago insuficiente y cambio.
- `dominio/ventas/excepciones.py`: errores esperables del caso de uso (`ErrorNegocio`, `CajaCerradaError`, `VentaVaciaError`, `StockInsuficienteError`, `PagoInvalidoError`, `TotalInvalidoError`).

### Repositorios

- `RepositorioProductos`: listar productos disponibles, buscar por ID/barra/nombre y descontar stock global, stock por almacén y movimiento `SALIDA_VENTA`.
- `RepositorioClientes`: listar clientes activos y obtener cliente por defecto.
- `RepositorioCaja`: obtener caja abierta, bloquear/verificar una caja y leer el almacén operativo.

Los repositorios reciben una conexión existente. No abren transacciones propias, no muestran ventanas y no contienen reglas de descuentos, crédito o FactrAPI.

### ServicioVentas

`servicios/servicio_ventas.py` coordina:

1. total y validación del pago con `Decimal`;
2. conexión/transacción PostgreSQL;
3. bloqueo de caja;
4. numeración atómica `ticket_venta`;
5. modo informal, NCF tradicional o e-CF;
6. inserción en `ventas` o `facturas_pendientes`;
7. descuento de stock y movimiento de inventario;
8. movimiento bancario para pagos electrónicos;
9. eliminación de la factura pendiente retomada;
10. `commit` único de la operación local;
11. emisión fiscal posterior al commit, conservando el principio “venta local confirmada / e-CF pendiente”;
12. guardado y lectura de facturas pendientes.

El servicio no importa Tkinter ni llama `messagebox`.

## Tabla de migración

| Módulo | SQL en UI antes | SQL en UI después | Servicio | Repositorio | Estado |
|---|---:|---:|---|---|---|
| Ventas/POS: caja abierta y almacén | Sí | No | `ServicioVentas.obtener_contexto` | `RepositorioCaja` | Migrado |
| Ventas/POS: clientes/productos iniciales | Sí | No | `listar_clientes`, `listar_productos_disponibles` | `RepositorioClientes`, `RepositorioProductos` | Migrado |
| Ventas/POS: búsqueda por código | Sí | No | `buscar_producto` | `RepositorioProductos` | Migrado |
| Confirmar venta | Sí | No | `realizar_venta` | caja, productos + SQL coordinado | Migrado |
| Guardar factura pendiente | Sí | No | `guardar_factura_pendiente` | SQL en servicio/repositorio pendiente de mayor descomposición | Parcial controlado |
| Retomar factura pendiente | Sí | No | `obtener_factura_pendiente` | pendiente de método específico | Parcial controlado |
| Cierre de caja dentro de POS | Sí | Sí | Fase 4 | pendiente | No migrado deliberadamente |
| `facturas_pendientes.py` | Sí | Sí | Fase 2/5 | pendiente | Fuera del alcance |
| `ventas_realizadas.py` | Sí | Sí | Fase 9 | pendiente | Fuera del alcance |
| `anular_factura_modal.py` | Sí | Sí | Fase 2 | pendiente | Fuera del alcance |
| `pago_modal.py` | Solo catálogo de cuentas | Sí | Captura visual actual | Fase 4 | Fuera del alcance |

La columna “SQL en UI después” deja claro qué deuda permanece, en lugar de presentar la fase como una migración total.

## Comportamiento preservado

- La UI conserva la misma ventana, botones, atajos, campos y navegación.
- Se mantiene el modelo actual de una fila por línea; no se crean cabeceras nuevas.
- La caja se vuelve a verificar con bloqueo `FOR UPDATE` dentro de la transacción.
- La numeración se reserva dentro de la misma transacción y se revierte si falla.
- Se mantiene el descuento de stock por almacén y global, con movimiento `SALIDA_VENTA`.
- Se mantienen pagos electrónicos mediante `registro_financiero.registrar_movimiento_bancario`.
- Se mantiene el borrado de líneas pendientes retomadas después de confirmar.
- FactrAPI se invoca después del commit local; si falla, `ecf_integracion` conserva/encola el comprobante y no revierte la venta.
- Los mensajes visuales permanecen en `ventas.py`.

La única diferencia intencional en la capa nueva es que los cálculos monetarios del dominio se redondean con `Decimal`; las tablas PostgreSQL siguen usando `DOUBLE PRECISION` y no se migró el esquema.

## Adaptadores temporales y deuda restante

- `ventas.py` conserva la importación de `db_conexion` porque todavía consulta el siguiente número para actualizar la etiqueta y contiene el cierre de caja heredado.
- `ventas.py` conserva SQL del cierre de caja: esa extracción es Fase 4 y se dejó intacta para no mezclar responsabilidades.
- `facturas_pendientes.py`, `ventas_realizadas.py`, `anular_factura_modal.py` y `pago_modal.py` siguen con acceso directo porque requieren sus propias migraciones de servicio.
- La anulación todavía coordina stock, finanzas y FactrAPI en su modal; se migrará después de estabilizar el caso de uso de venta.
- `ServicioVentas` todavía convierte objetos de dominio a los diccionarios que espera `ecf_integracion`; la integración fiscal existente no se destruyó.
- Las pantallas secundarias de reportes, configuración avanzada, historial y exportación aún pueden consultar directamente PostgreSQL. Los servicios de reportes/configuración son la nueva puerta de entrada para las próximas sustituciones, sin alterar el resultado visual.
- No se agregó logging central en esta fase; `print` existentes en la UI quedan como deuda documentada para una fase transversal.

## Pruebas ejecutadas

- Parseo AST de los 109 módulos Python del árbol actual: sin errores de sintaxis.
- Pruebas unitarias sin Tkinter ni PostgreSQL: `tests/test_ventas_reglas.py` cubre total con redondeo, cambio, crédito, pago insuficiente y venta vacía.
- Se verificó estáticamente que el flujo principal de confirmación ya no contiene `SELECT`, `INSERT`, `UPDATE` ni `DELETE`; el SQL que permanece en `ventas.py` corresponde al cierre de caja y lecturas auxiliares fuera de esta extracción.
- No se ejecutó una venta contra PostgreSQL ni una prueba real FactrAPI porque el entorno de auditoría no proporciona una base/servicio de aceptación configurado. Por ello no se afirma que esos escenarios hayan sido probados en ejecución.

## Estado de las fases

| Fase | Resultado | Alcance efectivo |
|---|---|---|
| 1. Infraestructura base | 🟢 | Paquetes de dominio, servicios, repositorios e infraestructura creados sin mover pantallas. |
| 2. Ventas/POS | 🟢 | `ServicioVentas` controla confirmación, pendientes, stock, caja, banco y fiscal posterior al commit. |
| 3. Inventario | 🟢 | `ServicioInventario` controla consultas, desactivación, ajustes y transferencias; transferencia e inventario principal reconectados. |
| 4. Caja/finanzas | 🟢 | `ServicioCaja` controla apertura, movimientos, listado y cierre; `gestion_caja.py` y modal de apertura reconectados. |
| 5. Clientes/CxC | 🟢 | CRUD de clientes y abonos principales reconectados; saldo de crédito consultado por servicio. |
| 6. Compras/proveedores | 🟡 | Borradores, listados y registro de pedidos reconectados; mantenimiento de proveedores y pantallas históricas conservan adaptadores directos. |
| 7. Cotizaciones | 🟢 | Alta, pendientes, carga y datos iniciales reconectados al servicio. |
| 8. FactrAPI/fiscal | 🟢 | Fachada `ServicioFiscal`; cliente HTTP, idempotencia, cola y separación local/remoto preservados. |
| 9. Reportes/configuración | 🟡 | Servicios de lectura creados y dashboard reconectado; reportes especializados y backup siguen en migración gradual por ser pantallas independientes. |

La arquitectura queda preparada para una segunda pasada de reducción de SQL en modales secundarios. Esa deuda no altera la separación de los casos de uso principales y está identificada aquí para evitar afirmar una migración total inexistente.

## Auditoría de cierre

### Resultado de la revisión

La separación crítica quedó cerrada sin mover pantallas ni cambiar su diseño. Las operaciones de venta, pendientes, ventas realizadas, anulación local, cierre y movimientos de caja, abonos, transferencias, bajas de inventario y catálogo de cuentas pasan por servicios. `RepositorioVentas` encapsula las lecturas y escrituras propias de ventas y pendientes. La anulación mantiene una única transacción local y solicita FactrAPI después del commit; si la llamada remota falla, la venta local no se revierte y se registra como pendiente de sincronización.

### SQL residual en UI

| Archivo | SQL encontrado | Acción | Estado |
|---|---|---|---|
| `ventas.py` | Ninguno de negocio | Cierre, contexto, numeración y venta usan servicios | Cerrado |
| `facturas_pendientes.py` | Ninguno | `ServicioVentas.listar_pendientes` y `eliminar_pendiente` | Cerrado |
| `ventas_realizadas.py` | Ninguno | `ServicioVentas.listar_ventas` y `listar_detalle_ventas` | Cerrado |
| `anular_factura_modal.py` | Ninguno | `ServicioVentas.anular_venta` | Cerrado |
| `pago_modal.py`, `registrar_abono_modal.py` | Ninguno | `ServicioCaja.listar_cuentas_pago` | Cerrado |
| `bajas_productos.py` | Ninguno | `ServicioInventario.registrar_baja` | Cerrado |
| `control_gastos.py` | Ninguno | `ServicioCaja.listar_gastos`, `registrar_gasto`, `anular_gasto` | Cerrado |
| Reportes especializados (`reporte_*.py`, `reporte_caja.py`, `caja_detalle.py`, `historial_*.py`, `ventas_efectivo_detalle.py`) | Sí, lecturas | Deuda de lectura secundaria; no modifican ventas, stock ni caja | Residual documentado |
| Mantenimiento/configuración (`manager.py`, `configuracion.py`, `empresa_config.py`, `factura_config.py`, `impuestos_config.py`, `numeracion_fiscal_config.py`, `proveedores.py`, `usuarios.py`, `categorias.py`, `almacenes.py`, entre otros) | Sí | No se reescribieron pantallas completas ni se modificó diseño; requieren migración posterior | Residual documentado |

La búsqueda global también encuentra SQL en `auditoria_preproduccion.py`, `preflight_produccion.py`, `cargar_datos_tienda.py`, `completar_datos_tienda.py`, `login.py`, `seguridad.py`, `ecf_integracion.py`, `factrapi_cliente.py`, `ncf_tradicional.py`, `registro_financiero.py` y `db_conexion.py`. Son utilidades, adaptadores o infraestructura existente; no se presentan como migradas a los servicios de negocio.

### Casos de uso

| Caso | Servicio | Repositorios | Transacción | Test |
|---|---|---|---|---|
| Venta contado | `ServicioVentas.realizar_venta` | `RepositorioVentas`, `RepositorioProductos`, `RepositorioCaja` | Única transacción local; fiscal posterior al commit | Unit PASS; integración INTEGRATION_NOT_EXECUTED |
| Venta crédito | `ServicioVentas.realizar_venta` | `RepositorioVentas`, `RepositorioProductos`, `RepositorioCaja` | Pendiente + stock en la misma transacción | Unit PASS; integración INTEGRATION_NOT_EXECUTED |
| Guardar/retomar pendiente | `ServicioVentas` | `RepositorioVentas` | Commit único | Unit PASS indirecto; integración no configurada |
| Anulación | `ServicioVentas.anular_venta` | `RepositorioVentas`, `RepositorioCaja` y `RepositorioProductos` | Anulación + stock + reversión financiera antes del commit | INTEGRATION_NOT_EXECUTED |
| Abono | `ServicioCuentasCobrar` | `RepositorioCredito` | Abono + movimiento de caja/banco | INTEGRATION_NOT_EXECUTED |
| Caja | `ServicioCaja` | `RepositorioCaja` | Apertura, movimiento y cierre transaccionales | INTEGRATION_NOT_EXECUTED |
| Transferencia | `ServicioInventario.transferir` | Servicio transaccional actual | Origen + destino + movimientos en un commit | INTEGRATION_NOT_EXECUTED |
| Baja | `ServicioInventario.registrar_baja` | Servicio transaccional actual | Stock + historial + movimiento en un commit | INTEGRATION_NOT_EXECUTED |
| Compra/pedido | `ServicioCompras` | Servicio transaccional actual | Registro local conservado; recepción completa no disponible en el flujo revisado | INTEGRATION_NOT_EXECUTED |
| Cotización | `ServicioCotizaciones` | Servicio transaccional actual | Alta/recuperación/eliminación según operación existente | INTEGRATION_NOT_EXECUTED |

### Arquitectura real

```text
Pantallas Tkinter
    │  eventos, captura, presentación
    ▼
Servicios de aplicación
    ├── ServicioVentas ── ServicioFiscal ── ecf_integracion ── factrapi_cliente
    ├── ServicioCaja
    ├── ServicioCuentasCobrar
    ├── ServicioInventario
    ├── ServicioClientes
    ├── ServicioCompras
    ├── ServicioCotizaciones
    ├── ServicioReportes
    └── ServicioConfiguracion
    │
    ▼
Repositorios (conexión recibida, sin Tkinter)
    ├── RepositorioVentas
    ├── RepositorioProductos
    ├── RepositorioClientes
    ├── RepositorioCaja
    └── RepositorioCredito
    │
    ▼
db_conexion → PostgreSQL

Reglas puras: Servicios → dominio. El dominio no importa PostgreSQL ni Tkinter.
```

### Dependencias y logging

- La búsqueda de imports no encontró `tkinter` ni `messagebox` en `dominio/`, `servicios/`, `repositorios/` o `infraestructura/`.
- No se encontraron dependencias desde `dominio` hacia servicios/repositorios ni desde repositorios hacia ventanas.
- Se agregó `infraestructura/logging_config.py` con logging básico. La anulación fiscal registra excepciones inesperadas sin credenciales ni claves.
- `ecf_integracion.py` y `factrapi_cliente.py` no fueron reescritos; el orden local → commit → FactrAPI queda preservado.

### Tests

- `PASS`: 5 pruebas unitarias de reglas monetarias y validaciones.
- `PASS`: compilación/parseo de todos los módulos Python revisados.
- `INTEGRATION_NOT_EXECUTED`: 3 contratos de integración aislada en `tests/test_integracion_ventas.py`; no hay DSN/fixtures PostgreSQL de prueba y no se tocó la base real.
- `FAIL`: ninguno en las pruebas ejecutadas.

### Riesgos

- Las pruebas contra PostgreSQL, rollback real, stock, caja, anulación, crédito y FactrAPI no pudieron ejecutarse en este entorno.
- Los reportes especializados y varias pantallas de mantenimiento todavía contienen lecturas/escrituras directas; no forman parte del flujo principal cerrado, pero impiden declarar una eliminación global de SQL en toda la UI.
- Los servicios nuevos mantienen algunas sentencias SQL coordinadas dentro de la transacción para no romper el esquema actual; esto está acotado a servicios y documentado.

### Veredicto

## NO LISTO PARA SIGUIENTE FASE

El núcleo arquitectónico crítico quedó separado, pero el veredicto global es `NO LISTO PARA SIGUIENTE FASE` porque faltan pruebas de integración ejecutables y permanece SQL en reportes y pantallas secundarias. No se declara una refactorización total mientras esas dos condiciones sigan pendientes.

## Addendum de continuación

En la continuación se cerró también la deuda de lectura de reportes y consultas auxiliares: `ServicioReportes` ahora atiende reportes de ventas, ganancias, medios de pago, CxC, inventario, compras, gastos, rentabilidad, detalle de caja y ventas en efectivo. `ServicioCompras` atiende el CRUD de proveedores. `ServicioConfiguracion` atiende empresa, moneda, impuestos y limpieza de desarrollo. `ServicioClientes` atiende el cliente por defecto. `ServicioInventario` atiende stock mínimo, alerta de stock y kardex. `ServicioUsuarios` atiende listado, alta, edición e inactivación de usuarios y conserva el hashing existente de `seguridad.py`.

La auditoría dirigida de estos módulos ya no encuentra SQL directo en la UI. El residuo global queda limitado a administración avanzada, numeración fiscal, utilidades de carga/auditoría, compatibilidad fiscal, seguridad, movimientos bancarios y algunas ventanas históricas. Esas consultas no fueron eliminadas automáticamente porque varias combinan configuración heredada, operaciones administrativas destructivas o integración externa; moverlas requiere revisar su comportamiento y permisos individualmente.

Por tanto, se mantienen los estados de integración:

- `PASS`: compilación, AST, imports y pruebas unitarias.
- `INTEGRATION_NOT_EXECUTED`: PostgreSQL/FactrAPI de aceptación aislados no configurados.
- `FAIL`: ninguno ejecutado.
- Veredicto global: `NO LISTO PARA SIGUIENTE FASE` hasta validar integración y cerrar la deuda administrativa restante.

## Cierre definitivo de arquitectura

### Deuda UI restante

Los flujos comerciales principales y reportes migrados no ejecutan persistencia desde Tkinter. La auditoría global todavía identifica escrituras administrativas directas en `almacenes.py`, `categorias.py`, `sucursales.py`, `gestion_banco.py`, `gestor_codigos_barra.py`, `promociones.py`, `servicios.py`, `importar_productos.py`, `nota_credito_debito.py`, `ncf_tradicional_config.py` y `numeracion_fiscal_config.py`. Estas operaciones quedan pendientes de migración individual y no se declaran cerradas.

### SQL justificado

`manager.py` contiene inicialización idempotente y migraciones de esquema; `db_conexion.py` es el adaptador PostgreSQL; `ecf_integracion.py`, `factrapi_cliente.py` y `registro_financiero.py` son adaptadores de infraestructura; `seguridad.py`, `permisos.py` y los scripts de auditoría/preflight realizan operaciones técnicas o de seguridad. Su SQL no se mueve artificialmente a servicios.

### Pruebas de integración

Los resultados completos están en [RESULTADOS_PRUEBAS_INTEGRACION.md](RESULTADOS_PRUEBAS_INTEGRACION.md). PostgreSQL está disponible, pero no existe una base exclusiva de prueba y `pos_app` no puede crearla. Todas las pruebas de escritura se marcaron exactamente como `NOT_EXECUTED`; no se utilizó `factra_db`.

### Concurrencia y riesgos

La numeración usa actualización atómica y las salidas de stock tienen condición de existencia dentro de transacciones, pero no se pudo demostrar su comportamiento con dos conexiones reales. Venta, crédito, abono, anulación, transferencia, caja y FactrAPI offline tampoco tienen evidencia de integración en este entorno.

### Resultado final

`NO LISTO PARA FASE DE PRODUCTO`. Bloquean el cierre definitivo: pruebas de integración aisladas no ejecutadas y deuda administrativa UI todavía existente. No se realizaron cambios de esquema productivo ni cambios visuales.

## Addendum final — cierre administrativo

La deuda administrativa fue cerrada después de esta auditoría. Las pantallas administrativas y de soporte ya delegan sus escrituras a servicios de aplicación. La búsqueda global de `INSERT`, `UPDATE` y `DELETE` fuera de servicios, repositorios, infraestructura, inicialización y scripts no devuelve escrituras Tkinter.

Estado verificado: compilación completa `PASS`, 5 pruebas unitarias `PASS`, auditoría estática de escrituras UI `PASS`, 3 pruebas PostgreSQL `NOT_EXECUTED` porque `factra_test` no existe y `pos_app` no tiene `CREATEDB`, y ningún `FAIL`.

### Veredicto vigente

`LISTO PARA FASE DE PRODUCTO`.

La base aislada `factra_test` fue creada, cargada y validada con la batería real. No se tocó `factra_db` ni se hizo un cambio de esquema productivo.
