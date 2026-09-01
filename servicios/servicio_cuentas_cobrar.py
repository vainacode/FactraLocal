from datetime import datetime

import db_conexion


class ServicioCuentasCobrar:
    def __init__(self, conexion=db_conexion):
        self.conexion = conexion

    def listar_saldos(self, plazo_dias=30):
        resultado = []
        with self.conexion.connect("database.db") as conn:
            filas = conn.execute("SELECT factura,cliente,SUM(total),MIN(fecha_creacion) FROM facturas_pendientes WHERE estado='Crédito' GROUP BY factura,cliente ORDER BY factura DESC").fetchall()
            for factura, cliente, total, fecha in filas:
                abonado = conn.execute("SELECT COALESCE(SUM(monto),0) FROM abonos_credito WHERE factura=?", (factura,)).fetchone()[0] or 0
                saldo = float(total or 0) - float(abonado)
                if saldo <= 0.01:
                    conn.execute("UPDATE facturas_pendientes SET estado='Pagada' WHERE factura=? AND estado='Crédito'", (factura,))
                else:
                    resultado.append((factura, cliente, float(total or 0), saldo, fecha))
            conn.commit()
        return resultado

    def registrar_abono(self, factura, cliente, monto, medio_pago, cuenta_destino, cajero):
        ahora = datetime.now()
        with self.conexion.connect("database.db") as conn:
            caja = conn.execute("SELECT id FROM cajas WHERE estado='Abierta' AND cajero=? ORDER BY id DESC LIMIT 1 FOR UPDATE", (cajero,)).fetchone()
            if not caja:
                raise ValueError("Debe abrir una caja antes de registrar el abono.")
            lineas = conn.execute("SELECT total FROM facturas_pendientes WHERE factura=? AND estado='Crédito' FOR UPDATE", (factura,)).fetchall()
            total = sum(float(f[0] or 0) for f in lineas)
            abonado = float(conn.execute("SELECT COALESCE(SUM(monto),0) FROM abonos_credito WHERE factura=?", (factura,)).fetchone()[0] or 0)
            if not lineas or float(monto) <= 0 or float(monto) > total - abonado + 0.01:
                raise ValueError("El abono supera el saldo pendiente actualizado.")
            conn.execute("INSERT INTO abonos_credito(factura,cliente,monto,fecha,hora,cajero,metodo_pago,cuenta_destino,caja_id) VALUES(?,?,?,?,?,?,?,?,?)", (factura, cliente, monto, ahora.strftime("%Y-%m-%d"), ahora.strftime("%H:%M:%S"), cajero, medio_pago, cuenta_destino, caja[0]))
            conn.execute("INSERT INTO movimientos_caja(caja_id,tipo,concepto,monto,fecha,hora,usuario,medio_pago,cuenta_destino) VALUES(?, 'INGRESO', ?, ?, ?, ?, ?, ?, ?)", (caja[0], f"Abono factura #{factura}", monto, ahora.strftime("%Y-%m-%d"), ahora.strftime("%H:%M:%S"), cajero, medio_pago, cuenta_destino))
            if medio_pago != "Efectivo":
                from registro_financiero import registrar_movimiento_bancario
                registrar_movimiento_bancario(conn, cuenta_destino, monto, f"Abono factura #{factura} - {medio_pago}", "Depósito", cajero)
            conn.commit()

    def listar_abonos(self, factura):
        with self.conexion.connect("database.db") as conn:
            return conn.execute("SELECT monto,fecha,hora,cajero FROM abonos_credito WHERE factura=? ORDER BY id", (factura,)).fetchall()
