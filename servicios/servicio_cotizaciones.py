from datetime import datetime

import db_conexion


class ServicioCotizaciones:
    def __init__(self, conexion=db_conexion):
        self.conexion = conexion

    def registrar(self, cliente, items, cajero, estado="Registrada"):
        ahora = datetime.now()
        with self.conexion.connect("database.db") as conn:
            numero = self.conexion.siguiente_numero("cotizacion", conn=conn)
            for item in items:
                conn.execute("INSERT INTO cotizaciones(cotizacion,cliente,producto,precio,cantidad,total,costo,fecha,hora,cajero,estado) VALUES(?,?,?,?,?,?,?,?,?,?,?)", (numero, cliente, item["producto"], item["precio"], item["cantidad"], item["total"], item["costo"], ahora.strftime("%Y-%m-%d"), ahora.strftime("%H:%M:%S"), cajero, estado))
            conn.commit()
        return numero

    def obtener_lineas_pendientes(self, numero):
        with self.conexion.connect("database.db") as conn:
            return conn.execute("SELECT producto,precio,cantidad,total,costo FROM cotizaciones WHERE cotizacion=? AND estado='Pendiente'", (numero,)).fetchall()

    def listar_clientes(self):
        with self.conexion.connect("database.db") as conn:
            return [fila[0] for fila in conn.execute("SELECT nombre FROM clientes WHERE estado != 'Inactivo' OR estado IS NULL").fetchall()]

    def listar_productos(self):
        with self.conexion.connect("database.db") as conn:
            return conn.execute("SELECT id,nombre,precio,stock,costo FROM inventario WHERE (estado != 'Inactivo' OR estado IS NULL) AND stock > 0").fetchall()

    def eliminar(self, numero):
        with self.conexion.connect("database.db") as conn:
            filas = conn.execute("SELECT producto,precio,cantidad,total,costo FROM cotizaciones WHERE cotizacion=?", (numero,)).fetchall()
            conn.execute("DELETE FROM cotizaciones WHERE cotizacion=?", (numero,))
            conn.commit()
        return filas
