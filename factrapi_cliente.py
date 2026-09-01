"""Cliente HTTP para FactrAPI (facturación electrónica DGII).

Implementa el contrato descrito en PLAN_FACTURACION_ELECTRONICA.md (sección 4),
tomado de G:\\bellotaHosting\\Factrapi\\docs\\GUIA-INTEGRACION-DESARROLLADORES.md
e INTEGRACION-SISTEMAS.md. Reglas clave que este módulo respeta:

- Nunca manda `empresaId`: el tenant lo determina la API Key (`x-api-key`).
- Toda operación de creación/acción repetible lleva `Idempotency-Key`.
- Reintenta con backoff+jitter solo en 5xx; respeta `Retry-After` en 429;
  nunca reintenta automáticamente 409/422 (son decisiones fiscales/de
  conflicto, no fallas transitorias).
- No inventa ni calcula totales fiscales: eso lo hace FactrAPI.

Sin URL base y API Key configuradas (Configuración > Numeración y
Facturación Electrónica), toda función de este módulo lanza
FactrAPINoConfigurado — el llamador debe manejarlo (encolar localmente,
avisar al usuario), nunca debe fallar la venta en sí.
"""
import json
import random
import time
import uuid

import requests

import db_conexion
from seguridad import descifrar_secreto


TIMEOUT_SEGUNDOS = 45
REINTENTOS_MAXIMOS = 3
CODIGOS_REINTENTABLES = {500, 502, 503, 504}


class FactrAPIError(Exception):
    """Error de negocio devuelto por FactrAPI (forma estándar de error)."""

    def __init__(self, status_code, codigo=None, mensaje=None, detalles=None, solicitud_id=None):
        self.status_code = status_code
        self.codigo = codigo
        self.mensaje = mensaje
        self.detalles = detalles or []
        self.solicitud_id = solicitud_id
        super().__init__(f"[{status_code}] {codigo}: {mensaje}")


class FactrAPINoConfigurado(Exception):
    """No hay URL base y/o API Key configuradas todavía."""


def datos_respuesta(respuesta):
    """Obtiene el objeto de negocio tanto si la API lo envuelve en `data`
    como si lo devuelve directamente."""
    if isinstance(respuesta, dict) and isinstance(respuesta.get("data"), dict):
        return respuesta["data"]
    return respuesta if isinstance(respuesta, dict) else {}


def _config():
    with db_conexion.connect() as conn:
        cur = conn.cursor()
        cur.execute('''
            SELECT factrapi_ambiente, factrapi_url_base, factrapi_api_key
            FROM configuracion_general WHERE id = 1
        ''')
        fila = cur.fetchone()
    if not fila or not fila[1] or not fila[2]:
        raise FactrAPINoConfigurado(
            "Falta configurar la URL base y/o la API Key de FactrAPI "
            "(Configuración > Numeración y Facturación Electrónica)."
        )
    ambiente, url_base, api_key = fila
    api_key = descifrar_secreto(api_key)
    return ambiente, url_base.rstrip("/"), api_key


def generar_idempotency_key(prefijo):
    """Genera una clave de idempotencia legible y estable para una operación
    puntual (ej. 'venta', 'anular', 'nota-credito'). Para reintentos, el
    llamador debe REUSAR la misma clave que generó la primera vez, nunca
    generar una nueva."""
    return f"pos-{prefijo}-{uuid.uuid4().hex[:16]}"


def _peticion(metodo, ruta, json_body=None, headers_extra=None, con_idempotencia=False):
    ambiente, url_base, api_key = _config()

    headers = {
        "Content-Type": "application/json",
        "x-api-key": api_key,
    }
    if headers_extra:
        headers.update(headers_extra)

    url = f"{url_base}{ruta}"
    ultimo_error = None

    for intento in range(REINTENTOS_MAXIMOS + 1):
        try:
            resp = requests.request(
                metodo, url, json=json_body, headers=headers, timeout=TIMEOUT_SEGUNDOS
            )
        except requests.exceptions.RequestException as e:
            ultimo_error = e
            if intento < REINTENTOS_MAXIMOS:
                time.sleep(_espera_backoff(intento))
                continue
            raise

        if resp.status_code == 429:
            retry_after = resp.headers.get("Retry-After")
            espera = float(retry_after) if retry_after else _espera_backoff(intento)
            if intento < REINTENTOS_MAXIMOS:
                time.sleep(espera)
                continue
            _lanzar_error(resp)

        if resp.status_code in CODIGOS_REINTENTABLES and intento < REINTENTOS_MAXIMOS:
            time.sleep(_espera_backoff(intento))
            continue

        if not resp.ok:
            _lanzar_error(resp)

        if resp.status_code == 204 or not resp.content:
            return {}
        return resp.json()

    if ultimo_error:
        raise ultimo_error
    raise RuntimeError("No se pudo completar la petición a FactrAPI tras los reintentos.")


def _espera_backoff(intento):
    base = min(2 ** intento, 8)
    return base + random.uniform(0, 0.5)


def _lanzar_error(resp):
    try:
        cuerpo = resp.json()
    except ValueError:
        cuerpo = {}
    raise FactrAPIError(
        status_code=resp.status_code,
        codigo=cuerpo.get("codigo"),
        mensaje=cuerpo.get("mensaje") or resp.text[:300],
        detalles=cuerpo.get("detalles"),
        solicitud_id=cuerpo.get("solicitudId") or resp.headers.get("X-Solicitud-Id"),
    )


# ---------------------------------------------------------------------
# Clientes
# ---------------------------------------------------------------------

def crear_o_localizar_cliente(datos, idempotency_key=None):
    """datos: dict con rnc/razonSocial/nombreComercial/correo/telefono/
    direccion/municipioCodigo/provinciaCodigo según corresponda."""
    headers = {"Idempotency-Key": idempotency_key} if idempotency_key else None
    return _peticion("POST", "/api/v1/clientes", json_body=datos, headers_extra=headers)


def consultar_rnc(rnc):
    return _peticion("GET", f"/api/v1/consulta-rnc/{rnc}")


# ---------------------------------------------------------------------
# Comprobantes
# ---------------------------------------------------------------------

def crear_comprobante(payload, idempotency_key):
    """payload: dict con tipoECF/clienteId/tipoIngresos/tipoPago/
    formasPago[]/detalles[] (ver sección 4 del plan/la guía). El
    Idempotency-Key debe guardarse ANTES de esta llamada para poder
    reintentar sin duplicar en caso de timeout."""
    return _peticion(
        "POST", "/api/v1/comprobantes", json_body=payload,
        headers_extra={"Idempotency-Key": idempotency_key},
    )


def enviar_comprobante(comprobante_id, idempotency_key=None):
    key = idempotency_key or f"pos-enviar-{comprobante_id}"
    return _peticion(
        "POST", f"/api/v1/comprobantes/{comprobante_id}/enviar",
        headers_extra={"Idempotency-Key": key},
    )


def consultar_comprobante(comprobante_id):
    return _peticion("POST", f"/api/v1/comprobantes/{comprobante_id}/consultar")


def anular_comprobante(comprobante_id, motivo=None):
    body = {"motivo": motivo} if motivo else {}
    return _peticion(
        "POST", f"/api/v1/comprobantes/{comprobante_id}/anular", json_body=body,
        headers_extra={"Idempotency-Key": f"pos-anular-{comprobante_id}"},
    )


def obtener_xml(comprobante_id):
    return _peticion("GET", f"/api/v1/comprobantes/{comprobante_id}/xml")


def obtener_representacion_impresa(comprobante_id):
    return _peticion("GET", f"/api/v1/comprobantes/{comprobante_id}/representacion-impresa")


# ---------------------------------------------------------------------
# Puntos de venta y secuencias
# ---------------------------------------------------------------------

def crear_punto_venta(codigo, nombre, sucursal=None):
    body = {"codigo": codigo, "nombre": nombre}
    if sucursal:
        body["sucursal"] = sucursal
    return _peticion(
        "POST", "/api/v1/puntos-venta", json_body=body,
        headers_extra={"Idempotency-Key": f"pos-punto-venta-{codigo}"},
    )


def listar_puntos_venta():
    return _peticion("GET", "/api/v1/puntos-venta")


def listar_secuencias():
    return _peticion("GET", "/api/v1/secuencias")


def refrescar_cache_secuencias():
    """Sincroniza las secuencias remotas para que la UI pueda alertar sin
    llamar a FactrAPI durante cada venta."""
    respuesta = listar_secuencias()
    if isinstance(respuesta, list):
        secuencias = respuesta
    else:
        secuencias = respuesta.get("data", respuesta.get("items", []))
    if not isinstance(secuencias, list):
        secuencias = []

    with db_conexion.connect() as conn:
        cur = conn.cursor()
        for secuencia in secuencias:
            sid = secuencia.get("id")
            if not sid:
                continue
            desde = int(secuencia.get("secuenciaDesde", 0))
            hasta = int(secuencia.get("secuenciaHasta", 0))
            actual = int(secuencia.get("secuenciaActual", desde))
            vencimiento = secuencia.get("fechaVencimiento") or ""
            cur.execute("""
                INSERT INTO secuencias_cache
                    (factrapi_secuencia_id, tipo_ecf, ambiente, secuencia_desde,
                     secuencia_hasta, secuencia_actual, fecha_vencimiento, activa)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT (factrapi_secuencia_id) DO UPDATE SET
                    tipo_ecf = EXCLUDED.tipo_ecf,
                    ambiente = EXCLUDED.ambiente,
                    secuencia_desde = EXCLUDED.secuencia_desde,
                    secuencia_hasta = EXCLUDED.secuencia_hasta,
                    secuencia_actual = EXCLUDED.secuencia_actual,
                    fecha_vencimiento = EXCLUDED.fecha_vencimiento,
                    activa = EXCLUDED.activa,
                    fecha_actualizacion = now()
            """, (sid, secuencia.get("tipoECF", 0), secuencia.get("ambiente", ""),
                  desde, hasta, actual, vencimiento, bool(secuencia.get("activa", True))))
        conn.commit()
    return len(secuencias)


def obtener_alertas_secuencias(umbral_disponibles=50, dias_vencimiento=30):
    """Devuelve mensajes para las secuencias activas próximas a agotarse o
    vencer. No modifica datos ni consulta la API."""
    import datetime
    alertas = []
    try:
        with db_conexion.connect() as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT tipo_ecf, ambiente, secuencia_actual, secuencia_hasta,
                       fecha_vencimiento
                FROM secuencias_cache WHERE activa = TRUE
                ORDER BY tipo_ecf
            """)
            filas = cur.fetchall()
    except db_conexion.Error:
        return alertas

    ahora = datetime.datetime.now(datetime.timezone.utc)
    for tipo, ambiente, actual, hasta, fecha in filas:
        disponibles = int(hasta) - int(actual) + 1
        if disponibles <= umbral_disponibles:
            alertas.append(f"E{int(tipo):02d} ({ambiente}): quedan {max(0, disponibles)}")
        if fecha:
            try:
                vencimiento = datetime.datetime.fromisoformat(str(fecha).replace("Z", "+00:00"))
                if vencimiento.tzinfo is None:
                    vencimiento = vencimiento.replace(tzinfo=datetime.timezone.utc)
                dias = (vencimiento - ahora).days
                if dias <= dias_vencimiento:
                    alertas.append(f"E{int(tipo):02d} ({ambiente}): vence en {max(0, dias)} días")
            except (TypeError, ValueError):
                pass
    return alertas


# ---------------------------------------------------------------------
# Catálogos
# ---------------------------------------------------------------------

def obtener_catalogo(nombre):
    return _peticion("GET", f"/api/v1/catalogos/{nombre}")


# ---------------------------------------------------------------------
# Cola offline (contingencia por falta de conexión)
#
# Fuente única de verdad: la tabla `comprobantes_fiscales`. Cada venta con
# e-CF tiene ahí una fila con su propio `idempotency_key`, `payload_enviado`
# y `estado_actual` — no existe una cola genérica separada, para no tener
# dos lugares que puedan quedar desincronizados sobre "qué falta reenviar".
# `ecf_integracion.py` es quien escribe esas filas al vender; este módulo
# solo sabe reintentar las que quedaron en un estado no terminal.
# ---------------------------------------------------------------------

ESTADOS_PENDIENTES_REINTENTO = ("pendiente_conexion", "error_creacion")
ESTADOS_NO_TERMINALES = ("borrador", "firmado", "pendiente", "enviado", "procesando", "error")


def reintentar_comprobantes_pendientes(maximo=20):
    """Reintenta crear en FactrAPI los comprobantes que quedaron encolados
    localmente (sin conexión o sin configuración al momento de la venta).
    Devuelve (procesados, fallidos). Pensado para llamarse periódicamente
    (ej. al abrir Ventas) — nunca bloquea la venta que lo originó, que ya
    quedó guardada en `ventas`/`facturas_pendientes` de todas formas."""
    procesados, fallidos = 0, 0
    with db_conexion.connect() as conn:
        cur = conn.cursor()
        cur.execute('''
            SELECT id, factura_local, idempotency_key, payload_enviado
            FROM comprobantes_fiscales
            WHERE estado_actual = ANY(?) AND factrapi_comprobante_id IS NULL
            ORDER BY fecha_creacion ASC LIMIT ?
        ''', (list(ESTADOS_PENDIENTES_REINTENTO), maximo))
        pendientes = cur.fetchall()

    for fila_id, factura_local, idempotency_key, payload_venta in pendientes:
        datos = payload_venta if isinstance(payload_venta, dict) else json.loads(payload_venta)
        try:
            import ecf_integracion
            resultado = ecf_integracion.emitir_venta_ecf(
                factura_local, datos.get("cliente"), datos.get("items", []),
                datos.get("medio_pago"), datos.get("total"),
                es_credito=datos.get("es_credito", False),
            )
            if resultado.get("ok"):
                procesados += 1
            else:
                fallidos += 1
        except Exception as e:
            fallidos += 1
            with db_conexion.connect() as conn:
                cur = conn.cursor()
                cur.execute('''
                    UPDATE comprobantes_fiscales SET ultimo_error = ?, fecha_actualizacion = now()
                    WHERE id = ?
                ''', (str(e)[:500], fila_id))
                conn.commit()

    return procesados, fallidos


def reconciliar_comprobantes_pendientes(maximo=20):
    """Consulta estados técnicos existentes sin crear documentos nuevos."""
    with db_conexion.connect() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT id, factrapi_comprobante_id FROM comprobantes_fiscales
            WHERE factrapi_comprobante_id IS NOT NULL
              AND estado_actual = ANY(?)
            ORDER BY fecha_actualizacion ASC LIMIT ?
        """, (list(ESTADOS_NO_TERMINALES), maximo))
        pendientes = cur.fetchall()

    actualizados = 0
    for fila_id, comprobante_id in pendientes:
        try:
            respuesta = consultar_comprobante(comprobante_id)
            datos = respuesta.get("data", respuesta) if isinstance(respuesta, dict) else {}
            estado = datos.get("estadoActual")
            if estado:
                with db_conexion.connect() as conn:
                    conn.execute("""
                        UPDATE comprobantes_fiscales
                        SET estado_actual = ?, fecha_actualizacion = now(), ultimo_error = NULL
                        WHERE id = ?
                    """, (estado, fila_id))
                    conn.commit()
                actualizados += 1
        except Exception as error:
            with db_conexion.connect() as conn:
                conn.execute("""
                    UPDATE comprobantes_fiscales SET ultimo_error = ?, fecha_actualizacion = now()
                    WHERE id = ?
                """, (str(error)[:500], fila_id))
                conn.commit()
    return actualizados
