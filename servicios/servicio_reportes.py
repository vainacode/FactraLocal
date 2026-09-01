import db_conexion


class ServicioReportes:
    """Consultas de lectura para que las pantallas no construyan SQL nuevo."""
    def __init__(self, conexion=db_conexion):
        self.conexion = conexion

    def ventas_por_fecha(self, desde, hasta):
        with self.conexion.connect("database.db") as conn:
            return conn.execute("SELECT factura,cliente,producto,precio,cantidad,total,fecha,hora,cajero,COALESCE(medio_pago,'Efectivo') FROM ventas WHERE fecha BETWEEN ? AND ? ORDER BY factura DESC,id", (desde, hasta)).fetchall()

    def resumen_ventas(self):
        with self.conexion.connect("database.db") as conn:
            return conn.execute("SELECT COUNT(DISTINCT factura),COALESCE(SUM(total),0),COALESCE(SUM(cantidad),0) FROM ventas").fetchone()

    def stock_valorizado(self):
        with self.conexion.connect("database.db") as conn:
            return conn.execute("SELECT id,nombre,stock,costo,stock*costo AS valor FROM inventario WHERE estado != 'Inactivo' OR estado IS NULL ORDER BY nombre").fetchall()

    def ventas_totales(self, desde, hasta):
        with self.conexion.connect("database.db") as conn:
            filas = conn.execute("""SELECT factura, fecha, cliente, producto FROM ventas WHERE fecha BETWEEN ? AND ?
                UNION ALL SELECT factura, fecha_creacion, cliente, producto FROM facturas_pendientes
                WHERE estado IN ('Crédito','Pagada') AND fecha_creacion BETWEEN ? AND ?
                ORDER BY fecha DESC, factura DESC""", (desde, hasta, desde, hasta)).fetchall()
            total = conn.execute("""SELECT COALESCE(SUM(total),0) FROM (
                SELECT total, fecha FROM ventas UNION ALL SELECT total, fecha_creacion
                FROM facturas_pendientes WHERE estado IN ('Crédito','Pagada')) v
                WHERE fecha BETWEEN ? AND ?""", (desde, hasta)).fetchone()[0]
        return filas, total

    def ventas_mes(self, anio):
        with self.conexion.connect("database.db") as conn:
            return conn.execute("""SELECT factura,cantidad,total,fecha FROM ventas WHERE fecha LIKE ?
                UNION ALL SELECT factura,cantidad,total,fecha_creacion FROM facturas_pendientes
                WHERE estado IN ('Crédito','Pagada') AND fecha_creacion LIKE ?""", (f"{anio}%", f"{anio}%")).fetchall()

    def ganancias_mes(self, anio):
        with self.conexion.connect("database.db") as conn:
            ventas = conn.execute("""SELECT total,costo*cantidad,fecha FROM ventas WHERE fecha LIKE ?
                UNION ALL SELECT total,costo*cantidad,fecha_creacion FROM facturas_pendientes
                WHERE estado IN ('Crédito','Pagada') AND fecha_creacion LIKE ?""", (f"{anio}%", f"{anio}%")).fetchall()
            gastos = conn.execute("SELECT monto,fecha FROM gastos WHERE fecha LIKE ?", (f"{anio}%",)).fetchall()
        return ventas, gastos

    def ventas_producto(self):
        with self.conexion.connect("database.db") as conn:
            return conn.execute("""SELECT producto,cantidad,total,costo FROM ventas
                UNION ALL SELECT producto,cantidad,total,costo FROM facturas_pendientes
                WHERE estado IN ('Crédito','Pagada')""").fetchall()

    def ventas_cliente(self):
        with self.conexion.connect("database.db") as conn:
            return conn.execute("""SELECT cliente,factura,cantidad,total,fecha FROM ventas
                UNION ALL SELECT cliente,factura,cantidad,total,fecha_creacion FROM facturas_pendientes
                WHERE estado IN ('Crédito','Pagada')""").fetchall()

    def medios_pago(self, desde=None):
        with self.conexion.connect("database.db") as conn:
            filtro_v = " AND fecha >= ?" if desde else ""
            filtro_p = " AND fecha_creacion >= ?" if desde else ""
            params_v = (desde,) if desde else ()
            params_p = (desde,) if desde else ()
            ventas = conn.execute("SELECT COALESCE(medio_pago,'Efectivo'),COUNT(DISTINCT factura),COALESCE(SUM(total),0) FROM ventas WHERE 1=1"+filtro_v+" GROUP BY COALESCE(medio_pago,'Efectivo')", params_v).fetchall()
            credito = conn.execute("SELECT 'Venta a Crédito',COUNT(DISTINCT factura),COALESCE(SUM(total),0) FROM facturas_pendientes WHERE estado IN ('Crédito','Pagada')"+filtro_p, params_p).fetchone()
        return ventas, credito

    def cuentas_cobrar_reporte(self):
        with self.conexion.connect("database.db") as conn:
            filas = conn.execute("SELECT factura,cliente,SUM(total),MIN(fecha_creacion) FROM facturas_pendientes WHERE estado='Crédito' GROUP BY factura,cliente ORDER BY factura DESC").fetchall()
            total_abonos = conn.execute("SELECT COALESCE(SUM(monto),0) FROM abonos_credito").fetchone()[0] or 0
            abonos = {factura: monto for factura, monto in conn.execute("SELECT factura,COALESCE(SUM(monto),0) FROM abonos_credito GROUP BY factura").fetchall()}
        return filas, total_abonos, abonos

    def inventario_compras(self):
        with self.conexion.connect("database.db") as conn:
            return conn.execute("SELECT id,nombre,proveedor,costo,stock,categoria FROM inventario ORDER BY nombre ASC").fetchall()

    def gastos_mes(self, anio):
        with self.conexion.connect("database.db") as conn:
            return conn.execute("SELECT monto,fecha FROM gastos WHERE fecha LIKE ?", (f"{anio}%",)).fetchall()

    def rentabilidad(self, desde, hasta):
        with self.conexion.connect("database.db") as conn:
            return conn.execute("""SELECT producto,SUM(cantidad),SUM(total),SUM(costo*cantidad),
                SUM(total-(costo*cantidad)) FROM (SELECT producto,cantidad,total,costo,fecha FROM ventas
                UNION ALL SELECT producto,cantidad,total,costo,fecha_creacion FROM facturas_pendientes
                WHERE estado IN ('Crédito','Pagada')) v WHERE fecha BETWEEN ? AND ?
                GROUP BY producto ORDER BY SUM(total-(costo*cantidad)) DESC""", (desde, hasta)).fetchall()

    def ventas_efectivo(self, caja_id):
        with self.conexion.connect("database.db") as conn:
            return conn.execute("SELECT factura,cliente,COALESCE(medio_pago,'Efectivo'),total,fecha || ' ' || hora FROM ventas WHERE caja_id=? AND COALESCE(medio_pago,'Efectivo')='Efectivo' ORDER BY id", (caja_id,)).fetchall()
