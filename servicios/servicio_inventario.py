from datetime import datetime

import db_conexion
from dominio.inventario.excepciones import AlmacenesInvalidosError, StockInsuficienteError


class ServicioInventario:
    def __init__(self, conexion=db_conexion):
        self.conexion = conexion

    def listar_productos(self, activos=True):
        with self.conexion.connect("database.db") as conn:
            filtro = " WHERE estado != 'Inactivo' OR estado IS NULL" if activos else ""
            return conn.execute(
                f"SELECT id, nombre, proveedor, precio, costo, stock, categoria, sucursal, codigo_barra, image_path, estado FROM inventario{filtro} ORDER BY nombre"
            ).fetchall()

    def filtrar_productos(self, texto):
        patron = f"%{str(texto).lower()}%"
        with self.conexion.connect("database.db") as conn:
            return conn.execute("SELECT id,nombre,proveedor,precio,costo,stock,categoria,sucursal,codigo_barra,image_path,estado FROM inventario WHERE (LOWER(nombre) LIKE ? OR CAST(id AS TEXT) LIKE ?) AND (estado != 'Inactivo' OR estado IS NULL) ORDER BY nombre", (patron, patron)).fetchall()

    def desactivar(self, producto_id):
        with self.conexion.connect("database.db") as conn:
            conn.execute("UPDATE inventario SET estado='Inactivo' WHERE id=?", (producto_id,))
            conn.commit()

    def catalogos_producto(self):
        with self.conexion.connect("database.db") as conn:
            provs = [x[0] for x in conn.execute("SELECT nombre FROM proveedores").fetchall()]
            cats = [x[0] for x in conn.execute("SELECT nombre FROM categorias").fetchall()]
            sucs = [x[0] for x in conn.execute("SELECT nombre FROM sucursal").fetchall()]
        return provs, cats, sucs

    def obtener_producto(self, producto_id):
        with self.conexion.connect("database.db") as conn:
            return conn.execute("SELECT id,nombre,proveedor,precio,costo,stock,categoria,sucursal,codigo_barra,image_path,estado FROM inventario WHERE id=?", (producto_id,)).fetchone()

    def guardar_producto(self, producto_id, nombre, proveedor, precio, costo, stock, categoria, sucursal, codigo_barra, image_path, estado):
        with self.conexion.connect("database.db") as conn:
            if codigo_barra:
                conflicto = conn.execute("SELECT id FROM inventario WHERE codigo_barra=? AND id<>COALESCE(?,0)", (codigo_barra, producto_id)).fetchone()
                if conflicto:
                    raise ValueError("Ese código de barras ya está asignado a otro producto.")
            if producto_id:
                conn.execute("UPDATE inventario SET nombre=?,proveedor=?,precio=?,costo=?,stock=?,categoria=?,sucursal=?,codigo_barra=?,image_path=?,estado=? WHERE id=?", (nombre, proveedor, precio, costo, stock, categoria, sucursal, codigo_barra or None, image_path, estado, producto_id))
                guardado = producto_id
            else:
                guardado = conn.execute("INSERT INTO inventario(nombre,proveedor,precio,costo,stock,categoria,sucursal,codigo_barra,image_path,estado) VALUES(?,?,?,?,?,?,?,?,?,?) RETURNING id", (nombre, proveedor, precio, costo, stock, categoria, sucursal, codigo_barra or None, image_path, estado)).fetchone()[0]
            almacen = conn.execute("SELECT almacen_id FROM configuracion_general WHERE id=1").fetchone()
            if almacen and almacen[0]:
                conn.execute("INSERT INTO inventario_almacen(producto_id,almacen_id,stock) VALUES(?,?,?) ON CONFLICT(producto_id,almacen_id) DO UPDATE SET stock=EXCLUDED.stock", (guardado, almacen[0], stock))
                conn.execute("UPDATE inventario SET stock=(SELECT COALESCE(SUM(stock),0) FROM inventario_almacen WHERE producto_id=?) WHERE id=?", (guardado, guardado))
            conn.commit()
            return guardado

    def listar_almacenes(self):
        with self.conexion.connect("database.db") as conn:
            return conn.execute("SELECT id, nombre, sucursal_id, estado FROM almacenes WHERE estado = 'Activo' ORDER BY nombre").fetchall()

    def listar_productos_basicos(self):
        with self.conexion.connect("database.db") as conn:
            return conn.execute("SELECT id, nombre FROM inventario WHERE estado != 'Inactivo' OR estado IS NULL ORDER BY nombre").fetchall()

    def listar_productos_stock(self):
        with self.conexion.connect("database.db") as conn:
            return conn.execute("SELECT id,nombre,stock FROM inventario WHERE estado != 'Inactivo' OR estado IS NULL").fetchall()

    def listar_stock_minimo(self):
        with self.conexion.connect("database.db") as conn:
            return conn.execute("SELECT i.id,i.nombre,i.stock,sm.stock_minimo FROM stock_minimo sm JOIN inventario i ON i.id=sm.id_producto WHERE i.estado != 'Inactivo' OR i.estado IS NULL ORDER BY i.nombre").fetchall()

    def guardar_stock_minimo(self, producto_id, minimo):
        with self.conexion.connect("database.db") as conn:
            conn.execute("INSERT INTO stock_minimo(id_producto,stock_minimo) VALUES(?,?) ON CONFLICT(id_producto) DO UPDATE SET stock_minimo=EXCLUDED.stock_minimo", (producto_id, minimo))
            conn.commit()

    def eliminar_stock_minimo(self, producto_id):
        with self.conexion.connect("database.db") as conn:
            conn.execute("DELETE FROM stock_minimo WHERE id_producto=?", (producto_id,))
            conn.commit()

    def listar_stock_bajo(self):
        with self.conexion.connect("database.db") as conn:
            return conn.execute("""SELECT i.nombre,i.proveedor,i.categoria,COALESCE(sm.stock_minimo,0),i.costo,i.stock FROM inventario i LEFT JOIN stock_minimo sm ON i.id=sm.id_producto WHERE (i.estado != 'Inactivo' OR i.estado IS NULL) AND i.stock <= COALESCE(sm.stock_minimo,0) ORDER BY i.nombre""").fetchall()

    def listar_kardex(self, producto_id=None):
        with self.conexion.connect("database.db") as conn:
            base = """SELECT m.fecha,m.hora,i.nombre,COALESCE(a.nombre,'General'),m.tipo,m.cantidad,COALESCE(m.referencia,''),COALESCE(m.usuario,'') FROM movimientos_inventario m JOIN inventario i ON i.id=m.producto_id LEFT JOIN almacenes a ON a.id=m.almacen_id"""
            if producto_id:
                return conn.execute(base + " WHERE m.producto_id=? ORDER BY m.id DESC", (producto_id,)).fetchall()
            return conn.execute(base + " ORDER BY m.id DESC").fetchall()

    def crear_almacen(self, nombre):
        with self.conexion.connect("database.db") as conn:
            conn.execute("INSERT INTO almacenes(nombre) VALUES(?)", (nombre,)); conn.commit()

    def seleccionar_almacen(self, almacen_id):
        with self.conexion.connect("database.db") as conn:
            conn.execute("UPDATE configuracion_general SET almacen_id=? WHERE id=1", (almacen_id,)); conn.commit()

    def crear_categoria(self, nombre, descripcion):
        with self.conexion.connect("database.db") as conn:
            conn.execute("INSERT INTO categorias(nombre,descripcion) VALUES(?,?)", (nombre,descripcion)); conn.commit()

    def actualizar_categoria(self, categoria_id, nombre, descripcion):
        with self.conexion.connect("database.db") as conn:
            conn.execute("UPDATE categorias SET nombre=?,descripcion=? WHERE id=?", (nombre,descripcion,categoria_id)); conn.commit()

    def eliminar_categoria(self, categoria_id):
        with self.conexion.connect("database.db") as conn:
            conn.execute("DELETE FROM categorias WHERE id=?", (categoria_id,)); conn.commit()

    def importar_productos(self, productos, foto_default):
        with self.conexion.connect("database.db") as conn:
            for _, nombre, proveedor, precio, costo, stock, categoria, sucursal in productos:
                conn.execute("INSERT INTO inventario(nombre,proveedor,precio,costo,stock,categoria,sucursal,image_path,estado) VALUES(?,?,?,?,?,?,?,?, 'Activo')", (nombre,proveedor,precio,costo,stock,categoria,sucursal,foto_default))
            conn.commit()

    def actualizar_codigo_barra(self, producto_id, codigo):
        with self.conexion.connect("database.db") as conn:
            conn.execute("UPDATE inventario SET codigo_barra=? WHERE id=?", (codigo, producto_id)); conn.commit()

    def crear_promocion(self, datos):
        with self.conexion.connect("database.db") as conn:
            conn.execute("INSERT INTO promociones(nombre,tipo,descuento,fecha_inicio,fecha_fin,estado) VALUES(?,?,?,?,?,?)", datos); conn.commit()

    def actualizar_promocion(self, promocion_id, datos):
        with self.conexion.connect("database.db") as conn:
            conn.execute("UPDATE promociones SET nombre=?,tipo=?,descuento=?,estado=? WHERE id=?", (*datos,promocion_id)); conn.commit()

    def eliminar_promocion(self, promocion_id):
        with self.conexion.connect("database.db") as conn:
            conn.execute("DELETE FROM promociones WHERE id=?", (promocion_id,)); conn.commit()

    def crear_servicio_catalogo(self, datos):
        with self.conexion.connect("database.db") as conn:
            conn.execute("INSERT INTO servicios(nombre,precio,costo,descripcion,tipo_impuesto,estado,fecha_creacion) VALUES(?,?,?,?,?,'Activo',CURRENT_TIMESTAMP)", datos); conn.commit()

    def actualizar_servicio_catalogo(self, servicio_id, datos):
        with self.conexion.connect("database.db") as conn:
            conn.execute("UPDATE servicios SET nombre=?,precio=?,costo=?,descripcion=?,tipo_impuesto=? WHERE id=?", (*datos,servicio_id)); conn.commit()

    def desactivar_servicio_catalogo(self, servicio_id):
        with self.conexion.connect("database.db") as conn:
            conn.execute("UPDATE servicios SET estado='Inactivo' WHERE id=?", (servicio_id,)); conn.commit()

    def cambiar_estado_combo(self, nombre, estado):
        if estado not in ("Activo", "Inactivo"):
            raise ValueError("Estado de combo no válido.")
        with self.conexion.connect("database.db") as conn:
            conn.execute("UPDATE combos SET estado=? WHERE nombre=?", (estado, nombre)); conn.commit()

    def listar_bajas(self):
        with self.conexion.connect("database.db") as conn:
            return conn.execute("SELECT id, producto, cantidad, motivo, fecha, responsable FROM bajas_productos ORDER BY id DESC").fetchall()

    def registrar_baja(self, producto_id, producto, cantidad, motivo, observaciones, usuario):
        if int(cantidad) <= 0:
            raise StockInsuficienteError("La cantidad debe ser mayor que cero.")
        ahora = datetime.now()
        with self.conexion.connect("database.db") as conn:
            almacen = conn.execute("SELECT almacen_id FROM configuracion_general WHERE id=1").fetchone()
            almacen_id = almacen[0] if almacen else None
            cur = conn.cursor()
            cur.execute("UPDATE inventario SET stock=stock-? WHERE id=? AND stock>=?", (cantidad, producto_id, cantidad))
            if cur.rowcount != 1:
                raise StockInsuficienteError("La cantidad supera el stock disponible.")
            if almacen_id:
                cur.execute("UPDATE inventario_almacen SET stock=stock-? WHERE producto_id=? AND almacen_id=? AND stock>=?", (cantidad, producto_id, almacen_id, cantidad))
                if cur.rowcount != 1:
                    raise StockInsuficienteError("La cantidad supera el stock disponible en el almacén.")
                cur.execute("""
                    INSERT INTO movimientos_inventario
                        (producto_id, almacen_id, tipo, cantidad, referencia, usuario, fecha, hora)
                    VALUES (?, ?, 'SALIDA_BAJA', ?, ?, ?, ?, ?)
                """, (producto_id, almacen_id, cantidad, motivo or "Baja", usuario,
                      ahora.strftime("%Y-%m-%d"), ahora.strftime("%H:%M:%S")))
            cur.execute("""
                INSERT INTO bajas_productos (producto, cantidad, motivo, fecha, responsable, observaciones)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (producto, cantidad, motivo, ahora.strftime("%Y-%m-%d"), usuario, observaciones))
            conn.commit()

    def ajustar_stock(self, producto_id, almacen_id, cantidad, tipo, referencia, usuario):
        if int(cantidad) <= 0:
            raise StockInsuficienteError("La cantidad debe ser mayor que cero.")
        if tipo not in ("ENTRADA_COMPRA", "SALIDA_VENTA", "AJUSTE", "TRANSFERENCIA"):
            raise ValueError("Tipo de movimiento de inventario no válido.")
        ahora = datetime.now()
        with self.conexion.connect("database.db") as conn:
            if tipo.startswith("SALIDA"):
                cur = conn.cursor()
                cur.execute("UPDATE inventario_almacen SET stock=stock-? WHERE producto_id=? AND almacen_id=? AND stock>=?", (cantidad, producto_id, almacen_id, cantidad))
                if cur.rowcount != 1:
                    raise StockInsuficienteError("Existencia insuficiente en el almacén.")
                cur.execute("UPDATE inventario SET stock=stock-? WHERE id=? AND stock>=?", (cantidad, producto_id, cantidad))
                if cur.rowcount != 1:
                    raise StockInsuficienteError("Existencia global insuficiente.")
            else:
                conn.execute("INSERT INTO inventario_almacen(producto_id, almacen_id, stock) VALUES(?,?,?) ON CONFLICT(producto_id, almacen_id) DO UPDATE SET stock=inventario_almacen.stock+EXCLUDED.stock", (producto_id, almacen_id, cantidad))
                conn.execute("UPDATE inventario SET stock=stock+? WHERE id=?", (cantidad, producto_id))
            conn.execute("INSERT INTO movimientos_inventario(producto_id, almacen_id, tipo, cantidad, referencia, usuario, fecha, hora) VALUES(?,?,?,?,?,?,?,?)", (producto_id, almacen_id, tipo, cantidad, referencia, usuario, ahora.strftime("%Y-%m-%d"), ahora.strftime("%H:%M:%S")))
            conn.commit()

    def transferir(self, producto_id, origen_id, destino_id, cantidad, usuario):
        if origen_id == destino_id:
            raise AlmacenesInvalidosError("El almacén de origen y destino deben ser diferentes.")
        if int(cantidad) <= 0:
            raise StockInsuficienteError("La cantidad debe ser mayor que cero.")
        ahora = datetime.now()
        with self.conexion.connect("database.db") as conn:
            cur = conn.cursor()
            cur.execute("UPDATE inventario_almacen SET stock=stock-? WHERE producto_id=? AND almacen_id=? AND stock>=?", (cantidad, producto_id, origen_id, cantidad))
            if cur.rowcount != 1:
                raise StockInsuficienteError("No hay existencia suficiente en el almacén de origen.")
            cur.execute("INSERT INTO inventario_almacen(producto_id, almacen_id, stock) VALUES(?,?,?) ON CONFLICT(producto_id, almacen_id) DO UPDATE SET stock=inventario_almacen.stock+EXCLUDED.stock", (producto_id, destino_id, cantidad))
            cur.execute("INSERT INTO transferencias_almacen(producto_id, almacen_origen_id, almacen_destino_id, cantidad, fecha, hora, usuario) VALUES(?,?,?,?,?,?,?)", (producto_id, origen_id, destino_id, cantidad, ahora.strftime("%Y-%m-%d"), ahora.strftime("%H:%M:%S"), usuario))
            cur.execute("INSERT INTO movimientos_inventario(producto_id, almacen_id, tipo, cantidad, referencia, usuario, fecha, hora) VALUES(?,?, 'TRASPASO_SALIDA', ?, ?, ?, ?, ?)", (producto_id, origen_id, cantidad, f"a:{destino_id}", usuario, ahora.strftime("%Y-%m-%d"), ahora.strftime("%H:%M:%S")))
            cur.execute("INSERT INTO movimientos_inventario(producto_id, almacen_id, tipo, cantidad, referencia, usuario, fecha, hora) VALUES(?,?, 'TRASPASO_ENTRADA', ?, ?, ?, ?, ?)", (producto_id, destino_id, cantidad, f"desde:{origen_id}", usuario, ahora.strftime("%Y-%m-%d"), ahora.strftime("%H:%M:%S")))
            conn.commit()
