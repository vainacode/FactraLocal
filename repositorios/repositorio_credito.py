class RepositorioCredito:
    def listar(self, conn):
        return conn.execute("SELECT factura,cliente,SUM(total),MIN(fecha_creacion) FROM facturas_pendientes WHERE estado='Crédito' GROUP BY factura,cliente ORDER BY factura DESC").fetchall()

    def abonos(self, conn, factura):
        return conn.execute("SELECT monto,fecha,hora,cajero FROM abonos_credito WHERE factura=? ORDER BY id", (factura,)).fetchall()
