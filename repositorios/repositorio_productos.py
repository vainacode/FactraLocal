class RepositorioProductos:
    def listar_disponibles(self, conn, almacen_id=None):
        if almacen_id:
            return conn.execute("""
                SELECT i.id, i.nombre, i.precio, COALESCE(ia.stock, i.stock), i.costo, i.codigo_barra
                FROM inventario i LEFT JOIN inventario_almacen ia
                  ON ia.producto_id = i.id AND ia.almacen_id = ?
                WHERE (i.estado != 'Inactivo' OR i.estado IS NULL)
                  AND COALESCE(ia.stock, 0) > 0
            """, (almacen_id,)).fetchall()
        return conn.execute("""
            SELECT id, nombre, precio, stock, costo, codigo_barra
            FROM inventario
            WHERE (estado != 'Inactivo' OR estado IS NULL) AND stock > 0
        """).fetchall()

    def buscar(self, conn, texto, almacen_id=None):
        patron = f"%{str(texto).lower()}%"
        if almacen_id:
            return conn.execute("""
                SELECT i.id, i.nombre, i.precio, COALESCE(ia.stock, 0), i.costo, i.codigo_barra
                FROM inventario i LEFT JOIN inventario_almacen ia
                  ON ia.producto_id = i.id AND ia.almacen_id = ?
                WHERE (i.id::text = ? OR i.codigo_barra = ? OR LOWER(i.nombre) LIKE ?)
                  AND (i.estado != 'Inactivo' OR i.estado IS NULL)
                  AND COALESCE(ia.stock, 0) > 0
            """, (almacen_id, str(texto), str(texto), patron)).fetchone()
        return conn.execute("""
            SELECT id, nombre, precio, stock, costo, codigo_barra
            FROM inventario
            WHERE (id::text = ? OR codigo_barra = ? OR LOWER(nombre) LIKE ?)
              AND (estado != 'Inactivo' OR estado IS NULL) AND stock > 0
        """, (str(texto), str(texto), patron)).fetchone()

    def descontar(self, conn, producto_id, cantidad, almacen_id, factura, usuario, fecha, hora, nombre):
        if almacen_id:
            cur = conn.cursor()
            cur.execute("""
                UPDATE inventario_almacen SET stock = stock - ?
                WHERE producto_id = ? AND almacen_id = ? AND stock >= ?
            """, (cantidad, producto_id, almacen_id, cantidad))
            if cur.rowcount != 1:
                raise ValueError(f"Stock insuficiente en el almacén para {nombre}.")
            cur.execute("""
                INSERT INTO movimientos_inventario
                    (producto_id, almacen_id, tipo, cantidad, referencia, usuario, fecha, hora)
                VALUES (?, ?, 'SALIDA_VENTA', ?, ?, ?, ?, ?)
            """, (producto_id, almacen_id, cantidad, str(factura), usuario, fecha, hora))
        cur = conn.cursor()
        cur.execute("""
            UPDATE inventario SET stock = stock - ? WHERE id = ? AND stock >= ?
        """, (cantidad, producto_id, cantidad))
        if cur.rowcount != 1:
            raise ValueError(f"Stock insuficiente para {nombre}.")

