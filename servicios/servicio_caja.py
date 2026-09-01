from datetime import datetime

import db_conexion
from dominio.caja.excepciones import CajaNoAbiertaError, MontoInvalidoError


class ServicioCaja:
    def __init__(self, conexion=db_conexion):
        self.conexion = conexion

    def obtener_abierta(self, usuario=None):
        with self.conexion.connect("database.db") as conn:
            if usuario:
                return conn.execute("SELECT id, monto_inicial FROM cajas WHERE estado='Abierta' AND cajero=? ORDER BY id DESC LIMIT 1", (usuario,)).fetchone()
            return conn.execute("SELECT id, monto_inicial FROM cajas WHERE estado='Abierta' ORDER BY id DESC LIMIT 1").fetchone()

    def listar(self):
        with self.conexion.connect("database.db") as conn:
            return conn.execute("SELECT id, fecha_apertura || ' ' || hora_apertura, monto_inicial, (monto_inicial + total_ventas), estado, total_ventas, COALESCE(fecha_cierre || ' ' || hora_cierre, 'N/A') FROM cajas ORDER BY id DESC").fetchall()

    def listar_cuentas_pago(self):
        with self.conexion.connect("database.db") as conn:
            return conn.execute("SELECT banco, numero_cuenta, tipo FROM cuentas_bancarias WHERE estado = 'Activo' ORDER BY banco").fetchall()

    def listar_cuentas_banco(self):
        with self.conexion.connect("database.db") as conn:
            return conn.execute("SELECT id,banco,numero_cuenta,saldo FROM cuentas_bancarias WHERE estado='Activo' ORDER BY banco").fetchall()

    def crear_cuenta_banco(self, datos):
        with self.conexion.connect("database.db") as conn:
            conn.execute("INSERT INTO cuentas_bancarias(banco,numero_cuenta,tipo,saldo,estado) VALUES(?,?,?,?, 'Activo')", datos); conn.commit()

    def actualizar_cuenta_banco(self, cuenta_id, datos):
        with self.conexion.connect("database.db") as conn:
            conn.execute("UPDATE cuentas_bancarias SET banco=?,numero_cuenta=?,tipo=?,saldo=? WHERE id=?", (*datos,cuenta_id)); conn.commit()

    def registrar_movimiento_bancario(self, banco, numero_cuenta, tipo, concepto, monto, usuario=None):
        valor = float(monto or 0)
        if valor <= 0:
            raise MontoInvalidoError("El monto debe ser mayor que cero.")
        ahora = datetime.now()
        with self.conexion.connect("database.db") as conn:
            fila = conn.execute("SELECT id,COALESCE(saldo,0) FROM cuentas_bancarias WHERE banco=? AND numero_cuenta=? AND estado='Activo' FOR UPDATE", (banco, numero_cuenta)).fetchone()
            if not fila:
                raise ValueError("La cuenta bancaria activa no existe.")
            saldo_anterior = float(fila[1] or 0)
            saldo_nuevo = saldo_anterior + valor if tipo in ("Depósito", "Inicial") else saldo_anterior - valor
            if saldo_nuevo < 0:
                raise ValueError("El movimiento dejaría la cuenta bancaria con saldo negativo.")
            conn.execute("INSERT INTO movimientos_bancarios(cuenta_id,banco,numero_cuenta,tipo_movimiento,tipo,concepto,monto,fecha,hora,usuario,saldo) VALUES(?,?,?,?,?,?,?,?,?,?,?)", (fila[0], banco, numero_cuenta, tipo, tipo, concepto, valor, ahora.strftime("%Y-%m-%d"), ahora.strftime("%H:%M:%S"), usuario, saldo_nuevo))
            conn.execute("UPDATE cuentas_bancarias SET saldo=? WHERE id=?", (saldo_nuevo, fila[0]))
            conn.commit()

    def resumen_cierre(self, caja_id):
        with self.conexion.connect("database.db") as conn:
            cur = conn.cursor()
            fila = cur.execute("SELECT monto_inicial FROM cajas WHERE id=? AND estado='Abierta'", (caja_id,)).fetchone()
            if not fila:
                raise CajaNoAbiertaError("No hay una caja abierta para cerrar.")
            inicial = float(fila[0] or 0)
            efectivo = float((cur.execute("SELECT COALESCE(SUM(total),0) FROM ventas WHERE caja_id=? AND COALESCE(medio_pago,'Efectivo')='Efectivo'", (caja_id,)).fetchone()[0]) or 0)
            abonos = float((cur.execute("SELECT COALESCE(SUM(monto),0) FROM abonos_credito WHERE caja_id=? AND COALESCE(metodo_pago,'Efectivo')='Efectivo'", (caja_id,)).fetchone()[0]) or 0)
            ingresos, egresos = cur.execute("SELECT COALESCE(SUM(CASE WHEN tipo='INGRESO' AND COALESCE(medio_pago,'Efectivo')='Efectivo' THEN monto ELSE 0 END),0), COALESCE(SUM(CASE WHEN tipo='EGRESO' AND COALESCE(medio_pago,'Efectivo')='Efectivo' THEN monto ELSE 0 END),0) FROM movimientos_caja WHERE caja_id=?", (caja_id,)).fetchone()
            egresos += float((cur.execute("SELECT COALESCE(SUM(monto),0) FROM gastos WHERE caja_id=? AND COALESCE(origen,'Caja')='Caja' AND COALESCE(anulado,FALSE)=FALSE", (caja_id,)).fetchone()[0]) or 0)
            return {"esperado": inicial + efectivo + abonos + float(ingresos or 0) - float(egresos or 0)}

    def abrir(self, usuario, monto_inicial, punto_venta_id=None, observaciones=None):
        monto = float(monto_inicial or 0)
        if monto < 0:
            raise MontoInvalidoError("El fondo inicial no puede ser negativo.")
        ahora = datetime.now()
        with self.conexion.connect("database.db") as conn:
            if self.obtener_abierta_en_conexion(conn, usuario):
                raise ValueError("Ya existe una caja abierta para este cajero.")
            if punto_venta_id is None:
                fila_pv = conn.execute("SELECT punto_venta_id FROM configuracion_general WHERE id=1").fetchone()
                punto_venta_id = (fila_pv or [None])[0]
            fila = conn.execute("INSERT INTO cajas(fecha_apertura,hora_apertura,monto_inicial,cajero,estado,total_ventas,monto_final,observaciones,punto_venta_id) VALUES(?,?,?,?, 'Abierta',0.0,0.0,?,?) RETURNING id", (ahora.strftime("%Y-%m-%d"), ahora.strftime("%H:%M:%S"), monto, usuario, observaciones, punto_venta_id)).fetchone()
            conn.commit()
            return fila[0]

    @staticmethod
    def obtener_abierta_en_conexion(conn, usuario):
        return conn.execute("SELECT id FROM cajas WHERE estado='Abierta' AND cajero=? ORDER BY id DESC LIMIT 1", (usuario,)).fetchone()

    def registrar_movimiento(self, usuario, tipo, concepto, monto, medio_pago="Efectivo"):
        valor = float(monto or 0)
        if valor <= 0:
            raise MontoInvalidoError("El monto debe ser mayor que cero.")
        caja = self.obtener_abierta(usuario)
        if not caja:
            raise CajaNoAbiertaError("Debe abrir una caja antes de registrar movimientos.")
        ahora = datetime.now()
        with self.conexion.connect("database.db") as conn:
            conn.execute("INSERT INTO movimientos_caja(caja_id,tipo,concepto,monto,fecha,hora,usuario,medio_pago) VALUES(?,?,?,?,?,?,?,?)", (caja[0], tipo, concepto, valor, ahora.strftime("%Y-%m-%d"), ahora.strftime("%H:%M:%S"), usuario, medio_pago))
            conn.commit()
        return caja[0]

    def listar_gastos(self):
        with self.conexion.connect("database.db") as conn:
            return conn.execute("SELECT id, concepto, monto, entidad, fecha, origen FROM gastos WHERE COALESCE(anulado, FALSE)=FALSE ORDER BY id DESC").fetchall()

    def detalle_exportacion(self, caja_id):
        with self.conexion.connect("database.db") as conn:
            ventas = conn.execute("SELECT 'Venta',factura,total,fecha,hora,cajero FROM ventas WHERE caja_id=? ORDER BY id", (caja_id,)).fetchall()
            gastos = conn.execute("SELECT 'Gasto',concepto,-monto,fecha,hora,usuario FROM gastos WHERE caja_id=? AND COALESCE(anulado,FALSE)=FALSE ORDER BY id", (caja_id,)).fetchall()
            movimientos = conn.execute("SELECT tipo,referencia,monto,fecha,hora,usuario FROM movimientos_caja WHERE caja_id=? ORDER BY id", (caja_id,)).fetchall()
        return ventas, gastos, movimientos

    def obtener_detalle(self, caja_id):
        with self.conexion.connect("database.db") as conn:
            return conn.execute("SELECT id,fecha_apertura,fecha_apertura || ' ' || hora_apertura,estado,cajero,monto_inicial FROM cajas WHERE id=?", (caja_id,)).fetchone()

    def detalle_caja(self, caja_id, fecha_caja):
        with self.conexion.connect("database.db") as conn:
            ventas = conn.execute("""SELECT COALESCE(medio_pago,'Efectivo'),COUNT(DISTINCT factura),SUM(total)
                FROM ventas WHERE caja_id=? GROUP BY COALESCE(medio_pago,'Efectivo')""", (caja_id,)).fetchall()
            total_gastos = conn.execute("SELECT COALESCE(SUM(monto),0) FROM gastos WHERE caja_id=? AND COALESCE(anulado,FALSE)=FALSE", (caja_id,)).fetchone()[0] or 0
            detalle_gastos = conn.execute("SELECT concepto,monto FROM gastos WHERE caja_id=? AND COALESCE(anulado,FALSE)=FALSE ORDER BY id DESC", (caja_id,)).fetchall()
            ingresos, egresos = conn.execute("SELECT COALESCE(SUM(CASE WHEN tipo='INGRESO' THEN monto ELSE 0 END),0),COALESCE(SUM(CASE WHEN tipo='EGRESO' THEN monto ELSE 0 END),0) FROM movimientos_caja WHERE caja_id=?", (caja_id,)).fetchone()
            descuentos = conn.execute("SELECT COALESCE(SUM(monto_descuento),0) FROM descuentos_ventas WHERE fecha=?", (fecha_caja,)).fetchone()[0] or 0
            creditos = conn.execute("SELECT factura,SUM(total) FROM facturas_pendientes WHERE estado='Crédito' AND caja_id=? GROUP BY factura", (caja_id,)).fetchall()
            abonos = {f: m for f,m in conn.execute("SELECT factura,COALESCE(SUM(monto),0) FROM abonos_credito GROUP BY factura").fetchall()}
            abonado_dia = conn.execute("SELECT COALESCE(SUM(monto),0) FROM abonos_credito WHERE fecha=?", (fecha_caja,)).fetchone()[0] or 0
        return ventas, total_gastos, detalle_gastos, ingresos, egresos, descuentos, creditos, abonos, abonado_dia

    def registrar_gasto(self, concepto, monto, entidad, fecha, origen, usuario=None):
        valor = float(monto or 0)
        if valor <= 0:
            raise MontoInvalidoError("El monto debe ser mayor que cero.")
        with self.conexion.connect("database.db") as conn:
            caja_id = None
            if origen == "Caja":
                caja = self.obtener_abierta_en_conexion(conn, usuario)
                if not caja:
                    raise CajaNoAbiertaError("No hay una caja abierta para registrar este gasto.")
                caja_id = caja[0]
            conn.execute("INSERT INTO gastos (concepto, monto, valor, entidad, fecha, origen, caja_id) VALUES (?, ?, ?, ?, ?, ?, ?)", (concepto, valor, valor, entidad or "General", fecha, origen, caja_id))
            conn.commit()

    def anular_gasto(self, gasto_id, usuario):
        with self.conexion.connect("database.db") as conn:
            cur = conn.cursor()
            cur.execute("UPDATE gastos SET anulado=TRUE, anulado_por=?, fecha_anulacion=now() WHERE id=? AND COALESCE(anulado,FALSE)=FALSE", (usuario, gasto_id))
            if cur.rowcount != 1:
                raise ValueError("El gasto ya estaba anulado o no existe.")
            conn.commit()

    def cerrar(self, caja_id, contado):
        ahora = datetime.now()
        with self.conexion.connect("database.db") as conn:
            cur = conn.cursor()
            cur.execute("SELECT monto_inicial FROM cajas WHERE id=? AND estado='Abierta' FOR UPDATE", (caja_id,))
            fila = cur.fetchone()
            if not fila:
                raise CajaNoAbiertaError("No hay una caja abierta para cerrar.")
            inicial = float(fila[0] or 0)
            ventas = float((cur.execute("SELECT COALESCE(SUM(total),0) FROM ventas WHERE caja_id=?", (caja_id,)).fetchone()[0]) or 0)
            credito = float((cur.execute("SELECT COALESCE(SUM(total),0) FROM facturas_pendientes WHERE caja_id=? AND estado IN ('Crédito','Pagada')", (caja_id,)).fetchone()[0]) or 0)
            efectivo = float((cur.execute("SELECT COALESCE(SUM(total),0) FROM ventas WHERE caja_id=? AND COALESCE(medio_pago,'Efectivo')='Efectivo'", (caja_id,)).fetchone()[0]) or 0)
            abonos = float((cur.execute("SELECT COALESCE(SUM(monto),0) FROM abonos_credito WHERE caja_id=? AND COALESCE(metodo_pago,'Efectivo')='Efectivo'", (caja_id,)).fetchone()[0]) or 0)
            ingresos, egresos = cur.execute("SELECT COALESCE(SUM(CASE WHEN tipo='INGRESO' AND COALESCE(medio_pago,'Efectivo')='Efectivo' THEN monto ELSE 0 END),0), COALESCE(SUM(CASE WHEN tipo='EGRESO' AND COALESCE(medio_pago,'Efectivo')='Efectivo' THEN monto ELSE 0 END),0) FROM movimientos_caja WHERE caja_id=?", (caja_id,)).fetchone()
            egresos += float((cur.execute("SELECT COALESCE(SUM(monto),0) FROM gastos WHERE caja_id=? AND COALESCE(origen,'Caja')='Caja' AND COALESCE(anulado,FALSE)=FALSE", (caja_id,)).fetchone()[0]) or 0)
            esperado = inicial + efectivo + abonos + float(ingresos or 0) - float(egresos or 0)
            diferencia = round(float(contado) - esperado, 2)
            cur.execute("UPDATE cajas SET estado='Cerrada',fecha_cierre=?,hora_cierre=?,total_ventas=?,monto_efectivo_esperado=?,monto_contado=?,diferencia_caja=?,monto_final=? WHERE id=? AND estado='Abierta'", (ahora.strftime("%Y-%m-%d"), ahora.strftime("%H:%M:%S"), ventas + credito, esperado, contado, diferencia, contado, caja_id))
            if cur.rowcount != 1:
                raise CajaNoAbiertaError("La caja ya fue cerrada por otro proceso.")
            conn.commit()
        return {"esperado": esperado, "contado": float(contado), "diferencia": diferencia, "total_ventas": ventas + credito}
