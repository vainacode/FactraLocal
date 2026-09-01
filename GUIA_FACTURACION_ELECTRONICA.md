# Guía de puesta en marcha fiscal

## Preparación del entorno

Instalar las dependencias del proyecto antes de iniciar el POS:

```text
pip install -r requirements.txt
```

Configurar las variables de `.env.example` en el servicio o equipo que
ejecuta la aplicación; no guardar contraseñas ni API Keys en el código.

Antes del primer arranque, ejecutar `preflight_produccion.py`. La aplicación
debe mostrar `PREFLIGHT_PRODUCCION_OK`; si falla, corregir el mensaje antes
de permitir ventas.

El preflight también bloquea si existen cajas abiertas, abonos sin caja o
comprobantes fiscales sin venta asociada.

El preflight también confirma que el servidor PostgreSQL usa TLS obligatorio,
que `pg_dump` y `psql` están instalados y que existen las tablas de caja,
inventario, bancos, auditoría y facturación. En producción no se debe cambiar
`POS_DB_SSLMODE` a `prefer` o `disable`.

En modo e-CF también verifica que la API Key de FactrAPI esté cifrada en la
base de datos y que el punto de venta esté enlazado con FactrAPI.

Para revisar una base existente sin modificarla, ejecutar
`auditoria_preproduccion.py`. Si muestra `REVISIÓN_MANUAL_REQUERIDA`, resolver
los registros indicados antes del corte.

Para ver las facturas y usuarios concretos que requieren revisión, ejecutar
`auditoria_preproduccion.py --detalles`.

El corte también se detiene si hay cajas heredadas abiertas: cada una debe
cuadrarse y cerrarse antes de habilitar producción.

La migración convierte automáticamente contraseñas heredadas a PBKDF2. Después
de migrar una base existente, el administrador debe cambiar cualquier
contraseña inicial o compartida desde **Usuarios** y confirmar que cada cajero
tenga su propia cuenta.

Si se migra una instalación anterior, revisar que todas las ventas tengan caja
y almacén asociados. El preflight detiene el arranque si encuentra registros
históricos sin esos vínculos; no los reasigna automáticamente porque hacerlo
alteraría la trazabilidad contable.

## Antes de activar e-CF

1. Tener el RNC de la empresa activo ante la DGII.
2. Tener la empresa habilitada en FactrAPI y disponer de la URL del ambiente
   (`pruebas` o `producción`) y su API Key.
3. Configurar en **Configuración → Numeración y Facturación Electrónica** el
   modo `ecf_factrapi`, el punto de venta y las credenciales.
4. Verificar que los clientes con RNC tengan el documento correcto y que los
   productos tengan su indicador de facturación configurado.
5. Probar una venta E32 y una E31 en ambiente de pruebas antes de cambiar a
   producción.

## Comportamiento ante fallos

- La venta local se conserva aunque FactrAPI no responda.
- El comprobante queda en cola con su payload y llave de idempotencia para
  reintentar sin duplicarlo.
- El e-NCF solo se muestra cuando FactrAPI lo devuelve; el sistema no lo
  inventa localmente.
- Los estados pendientes se reconcilian desde Ventas y las secuencias se
  actualizan en el caché para mostrar alertas de agotamiento o vencimiento.

## Operación diaria

- Abrir una caja con el cajero y monto inicial antes de vender; al terminar,
  contar el efectivo y ejecutar el cierre/cuadre. No se deben dejar cajas
  abiertas de días anteriores.
- Realizar un respaldo PostgreSQL con `pg_dump` al cierre o según la política
  de la empresa y comprobar periódicamente que puede restaurarse en un entorno
  separado.
- Revisar el banner de secuencias al abrir Ventas.
- Revisar comprobantes pendientes o con error antes del cierre.
- Para un e-CF emitido, usar **Nota Crédito/Débito** o **Anular factura**;
  no borrar manualmente la venta.
- Para modo informal, configurar rangos NCF tradicionales y revisar sus
  alertas de disponibilidad y vencimiento.

## Salida a producción

La prueba real contra FactrAPI requiere que el administrador introduzca una
URL y API Key válidas. No se incluyen credenciales en el código ni en este
archivo. Después de validar en pruebas, guardar las credenciales de producción
desde la pantalla de configuración y emitir un comprobante controlado.
