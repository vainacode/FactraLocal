import datetime
from decimal import Decimal

import db_conexion
from infraestructura.logging_config import logger
from dominio.ventas.excepciones import CajaCerradaError, StockInsuficienteError
from dominio.ventas.modelos import ItemVenta, ResultadoPendiente, ResultadoVenta, SolicitudVenta
from dominio.ventas.reglas import calcular_cambio, dinero, total_items, validar_pago
from repositorios.repositorio_caja import RepositorioCaja
from repositorios.repositorio_productos import RepositorioProductos
from repositorios.repositorio_ventas import RepositorioVentas


class ServicioVentas:
    """Caso de uso transaccional para ventas y facturas en espera.

    Conserva el modelo actual de una fila por línea y deja FactrAPI fuera de
    la transacción local: el comprobante fiscal se intenta después del commit.
    """

    def __init__(self, conexion=db_conexion, productos=None, caja=None, ventas=None):
        self.conexion = conexion
        self.productos = productos or RepositorioProductos()
        self.caja = caja or RepositorioCaja()
        self.ventas = ventas or RepositorioVentas()

    def obtener_contexto(self, usuario):
        with self.conexion.connect("database.db") as conn:
            caja = self.caja.obtener_abierta(conn, usuario)
            almacen = self.caja.obtener_almacen_operativo(conn)
        return (caja[0] if caja else None), almacen

    def obtener_siguiente_factura(self):
        return self.conexion.ver_siguiente_numero("ticket_venta")

    def listar_clientes(self):
        from repositorios.repositorio_clientes import RepositorioClientes
        with self.conexion.connect("database.db") as conn:
            repo = RepositorioClientes()
            clientes = repo.listar_nombres(conn)
            defecto = repo.obtener_nombre_defecto(conn)
        return clientes, defecto

    def listar_productos_disponibles(self, almacen_id):
        with self.conexion.connect("database.db") as conn:
            return self.productos.listar_disponibles(conn, almacen_id)

    def buscar_producto(self, texto, almacen_id):
        with self.conexion.connect("database.db") as conn:
            return self.productos.buscar(conn, texto, almacen_id)

    def realizar_venta(self, solicitud: SolicitudVenta) -> ResultadoVenta:
        total_original = total_items(solicitud.items)
        total = dinero(solicitud.total if solicitud.total is not None else total_original)
        validar_pago(solicitud.medio_pago, solicitud.cuenta_destino)
        es_credito = solicitud.medio_pago == "Venta a Crédito"
        ahora = datetime.datetime.now()
        fecha, hora = ahora.strftime("%Y-%m-%d"), ahora.strftime("%H:%M:%S")
        items = self._ajustar_items(solicitud.items, total, total_original)
        cambio = calcular_cambio(solicitud.medio_pago, solicitud.monto_recibido, total)
        ncf_tradicional = None

        with self.conexion.connect("database.db") as conn:
            if not self.caja.verificar_abierta(conn, solicitud.caja_id):
                raise CajaCerradaError("La caja se cerró antes de confirmar la venta. Abra una nueva caja.")

            factura = self.conexion.siguiente_numero("ticket_venta", conn=conn)
            modo_row = conn.execute(
                "SELECT modo_facturacion FROM configuracion_general WHERE id = 1"
            ).fetchone()
            modo = modo_row[0] if modo_row else "informal"
            if modo == "ncf_tradicional":
                from ncf_tradicional import siguiente_ncf
                ncf_tradicional, _ = siguiente_ncf("B02", conn=conn)

            cur = conn.cursor()
            for item in items:
                valores = (
                    factura, solicitud.cliente, item.producto, float(item.precio),
                    item.cantidad, float(item.total), float(item.costo), fecha,
                    hora, solicitud.usuario, solicitud.cuenta_destino,
                    solicitud.almacen_id, solicitud.caja_id,
                )
                if es_credito:
                    cur.execute("""
                        INSERT INTO facturas_pendientes
                            (factura, cliente, producto, precio, cantidad, total, costo,
                             fecha_creacion, hora_creacion, cajero, estado, medio_pago,
                             cuenta_destino, almacen_id, caja_id)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Crédito', 'Crédito', ?, ?, ?)
                    """, valores)
                else:
                    cur.execute("""
                        INSERT INTO ventas
                            (factura, cliente, producto, precio, cantidad, total, fecha,
                             hora, costo, cajero, medio_pago, cuenta_destino, almacen_id, caja_id)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (factura, solicitud.cliente, item.producto, float(item.precio),
                          item.cantidad, float(item.total), fecha, hora, float(item.costo),
                          solicitud.usuario, solicitud.medio_pago, solicitud.cuenta_destino,
                          solicitud.almacen_id, solicitud.caja_id))
                try:
                    self.productos.descontar(
                        conn, item.producto_id, item.cantidad, solicitud.almacen_id,
                        factura, solicitud.usuario, fecha, hora, item.producto,
                    )
                except ValueError as error:
                    raise StockInsuficienteError(str(error)) from error

            if ncf_tradicional:
                cur.execute("""
                    INSERT INTO documentos_fiscales_locales
                        (factura_local, tipo_ncf, ncf, fecha, cajero)
                    VALUES (?, 'B02', ?, ?, ?)
                """, (factura, ncf_tradicional, fecha, solicitud.usuario))

            if not es_credito and solicitud.medio_pago not in ("Efectivo", "Venta a Crédito"):
                from registro_financiero import registrar_movimiento_bancario
                registrar_movimiento_bancario(
                    conn, solicitud.cuenta_destino, float(total),
                    f"Venta #{factura} - {solicitud.medio_pago}", "Depósito", solicitud.usuario,
                )
            if solicitud.factura_pendiente_retomada is not None:
                cur.execute(
                    "DELETE FROM facturas_pendientes WHERE factura = ? AND estado = 'Pendiente'",
                    (solicitud.factura_pendiente_retomada,),
                )
            conn.commit()

        fiscal = self._emitir_fiscal_si_corresponde(
            modo, factura, solicitud, items, total, es_credito
        )
        return ResultadoVenta(
            numero_factura=factura, total=total, cambio=cambio,
            ncf_tradicional=ncf_tradicional,
            ncf_electronico=fiscal.get("eNCF") if fiscal else None,
            estado_fiscal=fiscal.get("estado") if fiscal else None,
            comprobante_id=fiscal.get("comprobante_id") if fiscal else None,
            fiscal_pendiente=bool(fiscal and not fiscal.get("ok")),
            motivo_fiscal=fiscal.get("motivo") if fiscal else None,
        )

    def guardar_factura_pendiente(self, cliente, items, usuario, caja_id, almacen_id):
        total = total_items(items)
        ahora = datetime.datetime.now()
        with self.conexion.connect("database.db") as conn:
            factura = self.conexion.siguiente_numero("ticket_venta", conn=conn)
            for item in items:
                conn.execute("""
                    INSERT INTO facturas_pendientes
                        (factura, cliente, producto, precio, cantidad, total, costo,
                         fecha_creacion, hora_creacion, cajero, estado, medio_pago,
                         cuenta_destino, almacen_id, caja_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Pendiente', NULL, NULL, ?, ?)
                """, (factura, cliente, item.producto, float(item.precio), item.cantidad,
                      float(item.total), float(item.costo), ahora.strftime("%Y-%m-%d"),
                      ahora.strftime("%H:%M:%S"), usuario, almacen_id, caja_id))
            conn.commit()
        return ResultadoPendiente(factura, total)

    def obtener_factura_pendiente(self, numero_factura):
        with self.conexion.connect("database.db") as conn:
            return self.ventas.obtener_pendiente(conn, numero_factura)

    def listar_ventas(self):
        with self.conexion.connect("database.db") as conn:
            return self.ventas.listar_realizadas(conn)

    def listar_detalle_ventas(self):
        with self.conexion.connect("database.db") as conn:
            return self.ventas.listar_detalle(conn)

    def listar_anuladas(self):
        with self.conexion.connect("database.db") as conn:
            return self.ventas.listar_anuladas(conn)

    def obtener_detalle_venta(self, factura):
        with self.conexion.connect("database.db") as conn:
            return self.ventas.obtener_detalle(conn, factura)

    def listar_pendientes(self):
        with self.conexion.connect("database.db") as conn:
            return self.ventas.listar_pendientes(conn)

    def eliminar_pendiente(self, factura):
        with self.conexion.connect("database.db") as conn:
            self.ventas.eliminar_pendiente(conn, factura)
            conn.commit()

    def anular_venta(self, factura, usuario):
        """Anula localmente de forma atómica venta, stock y movimiento financiero."""
        import datetime as _datetime
        from registro_financiero import registrar_movimiento_bancario
        with self.conexion.connect("database.db") as conn:
            items = self.ventas.obtener_items_para_anulacion(conn, factura)
            if not items:
                raise ValueError(f"No se encontró la venta #{factura}.")
            grupos = {}
            for item in items:
                medio, cuenta, caja_id = item[10], item[11], item[13]
                if medio in ("Venta a Crédito", "Crédito"):
                    continue
                grupos[(medio, cuenta, caja_id)] = grupos.get((medio, cuenta, caja_id), 0.0) + float(item[5] or 0)
            for medio, cuenta, caja_id in grupos:
                if medio == "Efectivo":
                    if not caja_id or not self.caja.verificar_abierta(conn, caja_id):
                        raise ValueError("La caja original está cerrada o no existe; gestione el reembolso mediante un ajuste autorizado.")
                elif not cuenta:
                    raise ValueError("La venta no tiene cuenta bancaria asociada para registrar el reembolso.")
            for item in items:
                self.ventas.registrar_anulacion(conn, item, usuario)
                producto = conn.execute("SELECT id FROM inventario WHERE nombre = ?", (item[2],)).fetchone()
                if not producto:
                    raise ValueError(f"No se encontró el producto '{item[2]}' para restaurar el inventario.")
                cantidad, almacen_id = item[4], item[12]
                conn.execute("UPDATE inventario SET stock = stock + ? WHERE id = ?", (cantidad, producto[0]))
                if almacen_id:
                    conn.execute("""
                        INSERT INTO inventario_almacen (producto_id, almacen_id, stock)
                        VALUES (?, ?, ?) ON CONFLICT (producto_id, almacen_id)
                        DO UPDATE SET stock = inventario_almacen.stock + EXCLUDED.stock
                    """, (producto[0], almacen_id, cantidad))
                    ahora = _datetime.datetime.now()
                    conn.execute("""
                        INSERT INTO movimientos_inventario
                            (producto_id, almacen_id, tipo, cantidad, referencia, usuario, fecha, hora)
                        VALUES (?, ?, 'ENTRADA_ANULACION', ?, ?, ?, ?, ?)
                    """, (producto[0], almacen_id, cantidad, str(factura), usuario,
                          ahora.strftime("%Y-%m-%d"), ahora.strftime("%H:%M:%S")))
            ahora = _datetime.datetime.now()
            for (medio, cuenta, caja_id), monto in grupos.items():
                concepto = f"Reembolso por anulación factura #{factura}"
                if medio == "Efectivo":
                    conn.execute("""
                        INSERT INTO movimientos_caja
                            (caja_id, tipo, concepto, monto, fecha, hora, usuario, medio_pago, cuenta_destino)
                        VALUES (?, 'EGRESO', ?, ?, ?, ?, ?, 'Efectivo', NULL)
                    """, (caja_id, concepto, monto, ahora.strftime("%Y-%m-%d"), ahora.strftime("%H:%M:%S"), usuario))
                else:
                    registrar_movimiento_bancario(conn, cuenta, monto, concepto, "Retiro", usuario)
            comprobante = self.ventas.obtener_comprobante_fiscal(conn, factura)
            self.ventas.eliminar_venta_y_credito(conn, factura)
            conn.commit()
        fiscal_pendiente = bool(comprobante)
        if comprobante:
            from servicios.servicio_fiscal import ServicioFiscal
            try:
                respuesta = ServicioFiscal.anular_comprobante(comprobante[0], f"Anulación solicitada por {usuario}")
                estado = respuesta.get("estadoActual", "anulado")
                with self.conexion.connect("database.db") as conn:
                    self.ventas.actualizar_estado_fiscal(conn, comprobante[0], estado)
                    conn.commit()
                fiscal_pendiente = str(estado).lower() != "anulado"
            except Exception:
                logger.exception("Error al solicitar anulación fiscal de la factura %s", factura)
                fiscal_pendiente = True
        return {"factura": factura, "fiscal_pendiente": fiscal_pendiente}

    @staticmethod
    def _ajustar_items(items, total, total_original):
        factor = total / total_original if total_original else Decimal("1")
        return [ItemVenta(
            producto_id=item.producto_id, producto=item.producto, cantidad=item.cantidad,
            precio=dinero(item.precio * factor), costo=dinero(item.costo),
        ) for item in items]

    @staticmethod
    def _emitir_fiscal_si_corresponde(modo, factura, solicitud, items, total, es_credito):
        if modo != "ecf_factrapi":
            return None
        from servicios.servicio_fiscal import ServicioFiscal
        payload_items = [{
            "id": item.producto_id, "producto": item.producto,
            "precio": float(item.precio), "costo": float(item.costo),
            "cantidad": item.cantidad, "total": float(item.total), "impuesto": 0.0,
        } for item in items]
        return ServicioFiscal.emitir_venta(
            factura, solicitud.cliente, payload_items, solicitud.medio_pago,
            float(total), es_credito=es_credito,
        )
