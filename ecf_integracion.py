"""Traduce una venta del POS al formato de comprobante e-CF de FactrAPI y
maneja el resultado (Fase 2 de PLAN_FACTURACION_ELECTRONICA.md).

Principio central del plan: el POS NUNCA calcula totales fiscales ni asigna
un e-NCF por su cuenta — solo junta los datos comerciales y se los manda a
FactrAPI. Si FactrAPI no responde (sin configurar, sin conexión, error
transitorio), la venta local YA se guardó igual (ver ventas.py) y este
módulo solo encola el comprobante para reintentarlo después; nunca revierte
ni inventa un número de factura.
"""
import datetime
import json

import db_conexion
import factrapi_cliente as fc

# FormaPagoType (catálogo DGII) — ver PLAN_FACTURACION_ELECTRONICA.md sección 4.
# "Pago Mixto" no tiene equivalente 1:1 en el catálogo (DGII espera montos
# separados por cada forma real); hasta que el POS registre el desglose de
# un pago mixto, se manda como "Otras Formas de pago" (8) y se dejó anotado
# en el plan como limitación conocida.
MEDIO_A_FORMA_PAGO = {
    "Efectivo": 1,
    "Transferencia": 2,
    "Tarjeta de Débito": 3,
    "Tarjeta de Crédito": 3,
    "Pago Mixto": 8,
}

UNIDAD_MEDIDA_DEFECTO = 43  # "Unidad" — el valor más común del catálogo unidades-medida.
TIPO_INGRESOS_DEFECTO = "01"  # 01 = Ingresos por operaciones (ventas normales del POS).


def _modo_facturacion():
    with db_conexion.connect() as conn:
        cur = conn.cursor()
        cur.execute("SELECT modo_facturacion, punto_venta_id FROM configuracion_general WHERE id = 1")
        fila = cur.fetchone()
    if not fila:
        return "informal", None
    return fila[0] or "informal", fila[1]


def _punto_venta_factrapi_id(conn, punto_venta_id):
    if not punto_venta_id:
        return None
    cur = conn.cursor()
    cur.execute("SELECT factrapi_punto_venta_id FROM puntos_venta WHERE id = ?", (punto_venta_id,))
    fila = cur.fetchone()
    return fila[0] if fila else None


def _datos_cliente_local(conn, cliente_nombre):
    cur = conn.cursor()
    cur.execute('''
        SELECT id, nombre, tipo_id, cedula, celular, direccion, correo, factrapi_cliente_id
        FROM clientes WHERE nombre = ?
    ''', (cliente_nombre,))
    return cur.fetchone()


def _tipo_ecf_para_cliente(tipo_id):
    """31 Crédito Fiscal si el cliente tiene identificación de tipo NIT
    (equivalente a RNC en el catálogo de tipo_id de este sistema), 32
    Consumo en cualquier otro caso (incluye 'Cliente General')."""
    return 31 if (tipo_id or "").upper() == "NIT" else 32


def _obtener_o_crear_cliente_factrapi(conn, cliente_local):
    (cid, nombre, tipo_id, cedula, celular, direccion, correo, factrapi_id) = cliente_local
    if factrapi_id:
        return factrapi_id

    datos = {"razonSocial": nombre}
    if (tipo_id or "").upper() == "NIT" and cedula:
        datos["rnc"] = str(cedula)
        # La razón social de un E31 debe coincidir con la identidad fiscal
        # devuelta por DGII; el nombre local no puede sobrescribirla.
        consulta_rnc = fc.consultar_rnc(str(cedula))
        consulta_rnc = fc.datos_respuesta(consulta_rnc)
        estado_rnc = str(consulta_rnc.get("estado", "")).upper()
        if estado_rnc and estado_rnc not in {"ACTIVO", "ACTIVA"}:
            raise fc.FactrAPIError(
                422, "RNC_NO_ACTIVO",
                f"El RNC {cedula} no está activo ante DGII.",
            )
        nombre_oficial = consulta_rnc.get("nombreRazonSocial")
        if nombre_oficial:
            datos["razonSocial"] = nombre_oficial
    if correo:
        datos["correo"] = correo
    if celular:
        datos["telefono"] = str(celular)
    if direccion:
        datos["direccion"] = direccion

    resultado = fc.crear_o_localizar_cliente(datos, idempotency_key=f"pos-cliente-{cid}")
    nuevo_id = fc.datos_respuesta(resultado).get("id")
    if nuevo_id:
        cur = conn.cursor()
        cur.execute("UPDATE clientes SET factrapi_cliente_id = ? WHERE id = ?", (nuevo_id, cid))
        conn.commit()
    return nuevo_id


def _indicadores_facturacion(conn, ids_producto):
    ids_validos = [i for i in ids_producto if i is not None]
    if not ids_validos:
        return {}
    cur = conn.cursor()
    cur.execute('''
        SELECT id, COALESCE(indicador_facturacion, 1) FROM inventario WHERE id = ANY(?)
    ''', (ids_validos,))
    return dict(cur.fetchall())


def _armar_detalles(conn, items):
    indicadores = _indicadores_facturacion(conn, [item.get("id") for item in items])
    detalles = []
    for i, item in enumerate(items, start=1):
        indicador = item.get("indicador_facturacion") or indicadores.get(item.get("id"), 1)
        detalles.append({
            "numeroLinea": i,
            "nombreItem": item["producto"],
            "indicadorBienoServicio": 1,
            "indicadorFacturacion": indicador,
            "cantidadItem": item["cantidad"],
            "unidadMedida": UNIDAD_MEDIDA_DEFECTO,
            "precioUnitarioItem": item["precio"],
        })
    return detalles


def emitir_venta_ecf(factura_local, cliente_nombre, items, medio_pago, total, punto_venta_codigo=None, es_credito=False):
    """Intenta crear y enviar el e-CF de una venta que YA se guardó en la
    tabla `ventas` local. Devuelve un dict:
        {"ok": True, "eNCF": "...", "estado": "..."}                 si se pudo emitir
        {"ok": False, "motivo": "...", "encolado": True/False}       si no
    Nunca lanza excepción — cualquier falla queda encolada para reintento.
    """
    idempotency_key = f"pos-venta-{factura_local}"

    try:
        with db_conexion.connect() as conn:
            _, punto_venta_id = _modo_facturacion()
            punto_venta_factrapi_id = _punto_venta_factrapi_id(conn, punto_venta_id)
            cliente_local = _datos_cliente_local(conn, cliente_nombre)
            tipo_id = cliente_local[2] if cliente_local else None
            if cliente_local:
                cliente_factrapi_id = _obtener_o_crear_cliente_factrapi(conn, cliente_local)
            else:
                consumidor = {"razonSocial": cliente_nombre or "Consumidor Final"}
                creado_cliente = fc.crear_o_localizar_cliente(
                    consumidor, idempotency_key="pos-cliente-general"
                )
                cliente_factrapi_id = fc.datos_respuesta(creado_cliente).get("id")
            detalles = _armar_detalles(conn, items)

        if not cliente_factrapi_id:
            raise fc.FactrAPIError(422, "CLIENTE_INVALIDO", "No se pudo identificar el cliente en FactrAPI.")

        forma_pago = 4 if es_credito else MEDIO_A_FORMA_PAGO.get(medio_pago, 8)
        payload = {
            "tipoECF": _tipo_ecf_para_cliente(tipo_id),
            "clienteId": cliente_factrapi_id,
            "tipoIngresos": TIPO_INGRESOS_DEFECTO,
            "tipoPago": 2 if es_credito else 1,
            "formasPago": [{"formaPago": forma_pago, "montoPago": total}],
            "detalles": detalles,
        }
        if punto_venta_factrapi_id:
            payload["puntoVentaId"] = punto_venta_factrapi_id

        # Se registra antes de la llamada remota. Si hay timeout, la misma
        # llave permite reintentar sin crear un segundo comprobante.
        _guardar_comprobante_local(
            factura_local, None, payload["tipoECF"], None, "pendiente_creacion",
            None, idempotency_key, payload, punto_venta_id
        )
        creado = fc.datos_respuesta(fc.crear_comprobante(payload, idempotency_key))
        comprobante_id = creado.get("id")
        e_ncf = creado.get("eNCF")
        estado = creado.get("estadoActual", "firmado")
        solicitud_id = creado.get("solicitudId")

        _guardar_comprobante_local(
            factura_local, comprobante_id, payload["tipoECF"], e_ncf, estado,
            solicitud_id, idempotency_key, payload, punto_venta_id
        )

        try:
            fc.enviar_comprobante(comprobante_id, f"{idempotency_key}-enviar")
            _actualizar_estado_comprobante(comprobante_id, "pendiente")
            estado = "pendiente"
        except (fc.FactrAPIError, Exception) as e:
            # El comprobante ya quedó creado/firmado con e-NCF real; el envío
            # a DGII se puede reintentar después (consultar_comprobante /
            # Fase 3) sin perder el número ya asignado.
            _registrar_error_comprobante(comprobante_id, str(e))

        return {"ok": True, "eNCF": e_ncf, "estado": estado, "comprobante_id": comprobante_id}

    except fc.FactrAPINoConfigurado as e:
        _encolar_venta(factura_local, cliente_nombre, medio_pago, total, items, idempotency_key, str(e), es_credito)
        return {"ok": False, "motivo": str(e), "encolado": True}
    except fc.FactrAPIError as e:
        # 409/422 son decisiones fiscales/de conflicto: no se reintentan
        # solas, pero tampoco se pierde la venta local ya guardada.
        _registrar_error_por_key(idempotency_key, f"{e.codigo}: {e.mensaje}", "error_creacion")
        return {"ok": False, "motivo": f"{e.codigo}: {e.mensaje}", "encolado": False}
    except Exception as e:
        _encolar_venta(factura_local, cliente_nombre, medio_pago, total, items, idempotency_key, str(e), es_credito)
        return {"ok": False, "motivo": str(e), "encolado": True}


def _guardar_comprobante_local(factura_local, comprobante_id, tipo_ecf, e_ncf, estado, solicitud_id, idempotency_key, payload, punto_venta_id=None):
    with db_conexion.connect() as conn:
        cur = conn.cursor()
        cur.execute('''
            INSERT INTO comprobantes_fiscales
                (factura_local, factrapi_comprobante_id, tipo_ecf, e_ncf, estado_actual,
                 solicitud_id, idempotency_key, punto_venta_id, payload_enviado)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT (idempotency_key) DO UPDATE SET
                factrapi_comprobante_id = EXCLUDED.factrapi_comprobante_id,
                e_ncf = EXCLUDED.e_ncf,
                estado_actual = EXCLUDED.estado_actual,
                tipo_ecf = EXCLUDED.tipo_ecf,
                solicitud_id = EXCLUDED.solicitud_id,
                punto_venta_id = EXCLUDED.punto_venta_id,
                payload_enviado = EXCLUDED.payload_enviado,
                fecha_actualizacion = now()
        ''', (factura_local, comprobante_id, tipo_ecf, e_ncf, estado, solicitud_id, idempotency_key, punto_venta_id, json.dumps(payload)))
        conn.commit()


def _actualizar_estado_comprobante(comprobante_id, estado):
    with db_conexion.connect() as conn:
        cur = conn.cursor()
        cur.execute('''
            UPDATE comprobantes_fiscales SET estado_actual = ?, fecha_actualizacion = now()
            WHERE factrapi_comprobante_id = ?
        ''', (estado, comprobante_id))
        conn.commit()


def _registrar_error_comprobante(comprobante_id, error):
    with db_conexion.connect() as conn:
        cur = conn.cursor()
        cur.execute('''
            UPDATE comprobantes_fiscales SET ultimo_error = ?, fecha_actualizacion = now()
            WHERE factrapi_comprobante_id = ?
        ''', (error[:500], comprobante_id))
        conn.commit()


def _registrar_error_por_key(idempotency_key, error, estado="error"):
    with db_conexion.connect() as conn:
        conn.execute('''
            UPDATE comprobantes_fiscales
            SET estado_actual = ?, ultimo_error = ?, fecha_actualizacion = now()
            WHERE idempotency_key = ?
        ''', (estado, error[:500], idempotency_key))
        conn.commit()


def _encolar_venta(factura_local, cliente_nombre, medio_pago, total, items, idempotency_key, error, es_credito=False):
    import json
    with db_conexion.connect() as conn:
        cur = conn.cursor()
        cur.execute('''
            INSERT INTO comprobantes_fiscales
                (factura_local, tipo_ecf, estado_actual, idempotency_key, payload_enviado, ultimo_error)
            VALUES (?, 0, 'pendiente_conexion', ?, ?, ?)
            ON CONFLICT (idempotency_key) DO UPDATE SET
                ultimo_error = EXCLUDED.ultimo_error,
                estado_actual = 'pendiente_conexion',
                payload_enviado = EXCLUDED.payload_enviado,
                fecha_actualizacion = now()
        ''', (factura_local, idempotency_key, json.dumps({
            "cliente": cliente_nombre, "medio_pago": medio_pago, "total": total, "items": items,
            "es_credito": es_credito,
            "fecha": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }), error[:500]))
        conn.commit()


def emitir_nota(factura_local, tipo, motivo, monto, cajero):
    """Emite una nota 33/34 contra el e-CF original, conservando su vínculo."""
    tipo_ecf = 34 if tipo == "Credito" else 33
    with db_conexion.connect() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT c.factrapi_comprobante_id, c.e_ncf, c.punto_venta_id,
                   c.tipo_ecf, cl.factrapi_cliente_id, MIN(v.fecha)
            FROM comprobantes_fiscales c
            JOIN ventas v ON v.factura = c.factura_local
            LEFT JOIN clientes cl ON cl.nombre = v.cliente
            WHERE c.factura_local = ? AND c.factrapi_comprobante_id IS NOT NULL
              AND c.tipo_ecf NOT IN (33, 34)
            GROUP BY c.factrapi_comprobante_id, c.e_ncf, c.punto_venta_id,
                     c.tipo_ecf, cl.factrapi_cliente_id
        """, (factura_local,))
        original = cur.fetchone()
        if not original:
            raise ValueError("La factura no tiene un e-CF emitido en FactrAPI.")
        cur.execute("""
            SELECT producto, precio, cantidad, id
            FROM ventas WHERE factura = ? ORDER BY id
        """, (factura_local,))
        items = cur.fetchall()

    fecha_original = original[5] or datetime.datetime.now().strftime("%Y-%m-%d")
    if not original[4]:
        raise ValueError("La factura no tiene un cliente sincronizado con FactrAPI.")
    payload = {
        "tipoECF": tipo_ecf,
        "clienteId": original[4],
        "tipoIngresos": "01",
        "tipoPago": 1,
        "detalles": [{
            "numeroLinea": 1,
            "nombreItem": f"Ajuste por nota {tipo.lower()}",
            "indicadorBienoServicio": 1,
            "indicadorFacturacion": 1,
            "cantidadItem": 1,
            "unidadMedida": UNIDAD_MEDIDA_DEFECTO,
            "precioUnitarioItem": monto,
        }],
        "informacionReferencia": {
            "ncfModificado": original[1],
            "fechaNcfModificado": f"{fecha_original}T00:00:00.000Z",
            "codigoModificacion": 1 if tipo == "Credito" else 3,
        },
        "informacionAdicionalEmisor": (motivo or "")[:250],
    }
    key = f"pos-nota-{tipo.lower()}-{factura_local}"
    creado = fc.crear_comprobante(payload, key)
    creado = fc.datos_respuesta(creado)
    comprobante_id = creado.get("id")
    if not comprobante_id:
        raise ValueError("FactrAPI no devolvió el identificador de la nota.")
    with db_conexion.connect() as conn:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO comprobantes_fiscales
                (factura_local, factrapi_comprobante_id, tipo_ecf, e_ncf,
                 estado_actual, idempotency_key, ncf_modificado, codigo_modificacion,
                 punto_venta_id, payload_enviado)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT (idempotency_key) DO UPDATE SET
                factrapi_comprobante_id = EXCLUDED.factrapi_comprobante_id,
                e_ncf = EXCLUDED.e_ncf, estado_actual = EXCLUDED.estado_actual
        """, (factura_local, comprobante_id, tipo_ecf, creado.get("eNCF"),
              creado.get("estadoActual", "firmado"), key, original[1],
              1 if tipo == "Credito" else 3, original[2], json.dumps(payload)))
        conn.commit()
    fc.enviar_comprobante(comprobante_id, f"{key}-enviar")
    return creado
