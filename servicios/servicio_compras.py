import json
from datetime import datetime

import db_conexion


class ServicioCompras:
    def __init__(self, conexion=db_conexion):
        self.conexion = conexion

    def guardar_borrador(self, usuario, datos):
        with self.conexion.connect("database.db") as conn:
            conn.execute("INSERT INTO pedidos_borradores(usuario,datos) VALUES(?,?)", (usuario, json.dumps(datos)))
            conn.commit()

    def obtener_borrador(self, usuario):
        with self.conexion.connect("database.db") as conn:
            fila = conn.execute("SELECT id,datos FROM pedidos_borradores WHERE usuario=? ORDER BY id DESC LIMIT 1", (usuario,)).fetchone()
        return (fila[0], json.loads(fila[1]) if fila else None) if fila else None

    def listar_productos(self):
        with self.conexion.connect("database.db") as conn:
            return conn.execute("SELECT id,nombre,precio,costo,stock,proveedor FROM inventario WHERE estado != 'Inactivo' OR estado IS NULL ORDER BY nombre").fetchall()

    def listar_pedidos(self):
        with self.conexion.connect("database.db") as conn:
            return conn.execute("SELECT numero_pedido,proveedor,producto,cantidad,fecha FROM pedidos ORDER BY id DESC").fetchall()

    def registrar_pedido(self, proveedor, items, usuario=None, numero=None):
        ahora = datetime.now()
        with self.conexion.connect("database.db") as conn:
            numero = numero if numero is not None else self.conexion.siguiente_numero("pedido", conn=conn)
            for item in items:
                conn.execute("INSERT INTO pedidos(numero_pedido,proveedor,producto,cantidad,fecha,hora,precio,costo) VALUES(?,?,?,?,?,?,?,?)", (numero, item.get("proveedor", proveedor), item["producto"], item["cantidad"], ahora.strftime("%Y-%m-%d"), ahora.strftime("%H:%M:%S"), item.get("precio", 0), item.get("costo", 0)))
            conn.commit()
        return numero

    def listar_proveedores(self):
        with self.conexion.connect("database.db") as conn:
            return conn.execute("SELECT id,nombre,nit,telefono,contacto,ciudad FROM proveedores ORDER BY nombre").fetchall()

    def crear_proveedor(self, datos):
        with self.conexion.connect("database.db") as conn:
            fila = conn.execute("INSERT INTO proveedores (nombre,nit,telefono,contacto,email,direccion,ciudad) VALUES (?,?,?,?,?,?,?) RETURNING id", datos).fetchone()
            conn.commit()
            return fila[0]

    def actualizar_proveedor(self, proveedor_id, datos):
        with self.conexion.connect("database.db") as conn:
            conn.execute("UPDATE proveedores SET nombre=?,nit=?,telefono=?,contacto=?,email=?,direccion=?,ciudad=? WHERE id=?", (*datos, proveedor_id))
            conn.commit()

    def eliminar_proveedor(self, proveedor_id):
        with self.conexion.connect("database.db") as conn:
            conn.execute("DELETE FROM proveedores WHERE id=?", (proveedor_id,))
            conn.commit()
