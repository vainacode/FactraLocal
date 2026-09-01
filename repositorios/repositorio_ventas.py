class RepositorioVentas:
    """Persistencia de ventas, pendientes y anulaciones."""

    def listar_realizadas(self, conn):
        return conn.execute("""
            SELECT factura, cliente, SUM(total), fecha, hora, cajero,
                   COALESCE(medio_pago, 'Efectivo')
            FROM ventas
            GROUP BY factura, cliente, fecha, hora, cajero, medio_pago
            UNION ALL
            SELECT factura, cliente, SUM(total), MIN(fecha_creacion),
                   MIN(hora_creacion), cajero, COALESCE(medio_pago, 'Crédito')
            FROM facturas_pendientes
            WHERE estado IN ('Crédito', 'Pagada')
            GROUP BY factura, cliente, cajero, medio_pago
            ORDER BY factura DESC
        """).fetchall()

    def listar_detalle(self, conn):
        return conn.execute("""
            SELECT factura, cliente, producto, precio, cantidad, total, fecha,
                   hora, cajero, COALESCE(medio_pago, 'Efectivo')
            FROM ventas ORDER BY factura DESC, id
        """).fetchall()

    def listar_pendientes(self, conn):
        return conn.execute("""
            SELECT factura, cliente, COUNT(*), SUM(total),
                   MIN(fecha_creacion || ' ' || hora_creacion)
            FROM facturas_pendientes
            WHERE estado = 'Pendiente'
            GROUP BY factura, cliente ORDER BY factura DESC
        """).fetchall()

    def obtener_pendiente(self, conn, factura):
        return conn.execute("""
            SELECT producto, precio, cantidad, total, costo
            FROM facturas_pendientes WHERE factura = ? AND estado = 'Pendiente'
        """, (factura,)).fetchall()

    def eliminar_pendiente(self, conn, factura):
        conn.execute("DELETE FROM facturas_pendientes WHERE factura = ? AND estado = 'Pendiente'", (factura,))

    def obtener_items_para_anulacion(self, conn, factura):
        items = conn.execute("""
            SELECT factura, cliente, producto, precio, cantidad, total, fecha,
                   hora, costo, cajero, COALESCE(medio_pago, 'Efectivo'),
                   cuenta_destino, almacen_id, caja_id
            FROM ventas WHERE factura = ?
        """, (factura,)).fetchall()
        if items:
            return items
        return conn.execute("""
            SELECT factura, cliente, producto, precio, cantidad, total,
                   fecha_creacion, hora_creacion, costo, cajero,
                   COALESCE(medio_pago, 'Crédito'), cuenta_destino,
                   almacen_id, caja_id
            FROM facturas_pendientes
            WHERE factura = ? AND estado IN ('Crédito', 'Pagada')
        """, (factura,)).fetchall()

    def obtener_comprobante_fiscal(self, conn, factura):
        return conn.execute("""
            SELECT factrapi_comprobante_id, estado_actual, e_ncf
            FROM comprobantes_fiscales
            WHERE factura_local = ? AND factrapi_comprobante_id IS NOT NULL
              AND tipo_ecf NOT IN (33, 34)
            ORDER BY id DESC LIMIT 1
        """, (factura,)).fetchone()

    def registrar_anulacion(self, conn, item, usuario):
        factura, cliente, producto, precio, cantidad, total, fecha, hora, costo, cajero, medio = item[:11]
        conn.execute("""
            INSERT INTO facturas_anuladas
                (factura, cliente, producto, precio, cantidad, total, fecha,
                 hora, costo, cajero, medio_pago, anulo)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (factura, cliente, producto, precio, cantidad, total, fecha,
              hora, costo, cajero, medio, usuario))

    def eliminar_venta_y_credito(self, conn, factura):
        conn.execute("DELETE FROM ventas WHERE factura = ?", (factura,))
        conn.execute("DELETE FROM facturas_pendientes WHERE factura = ? AND estado IN ('Crédito', 'Pagada')", (factura,))

    def actualizar_estado_fiscal(self, conn, comprobante_id, estado):
        conn.execute("""
            UPDATE comprobantes_fiscales
            SET estado_actual = ?, fecha_actualizacion = now(), ultimo_error = NULL
            WHERE factrapi_comprobante_id = ?
        """, (estado, comprobante_id))

    def listar_anuladas(self, conn):
        return conn.execute("SELECT factura,cliente,SUM(total),fecha,hora,anulo,medio_pago FROM facturas_anuladas GROUP BY factura,cliente,fecha,hora,anulo,medio_pago ORDER BY factura DESC").fetchall()

    def obtener_detalle(self, conn, factura):
        rows = conn.execute("SELECT factura,cliente,producto,precio,cantidad,total,medio_pago FROM ventas WHERE factura=?", (factura,)).fetchall()
        if rows:
            return rows
        rows = conn.execute("SELECT factura,cliente,producto,precio,cantidad,total,COALESCE(medio_pago,'Crédito') FROM facturas_pendientes WHERE factura=? AND estado IN ('Crédito','Pagada')", (factura,)).fetchall()
        if rows:
            return rows
        return conn.execute("SELECT factura,cliente,producto,precio,cantidad,total,medio_pago FROM facturas_anuladas WHERE factura=?", (factura,)).fetchall()
