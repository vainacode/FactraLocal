"""Completa datos maestros y trazabilidad de abastecimiento sin crear ventas."""
import datetime
import db_conexion
from cargar_datos_tienda import insertar


def completar():
    fecha = (datetime.datetime.now() - datetime.timedelta(days=7)).strftime("%Y-%m-%d")
    hora = "09:00:00"
    with db_conexion.connect() as conn:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM pedidos")
        pedidos_existentes = cur.fetchone()[0]
        cur.execute("SELECT id, nombre, proveedor, costo, stock FROM inventario ORDER BY id")
        productos = cur.fetchall()
        cur.execute("SELECT id, nombre FROM almacenes WHERE estado='Activo' ORDER BY id LIMIT 1")
        almacen = cur.fetchone()
        if not almacen:
            raise RuntimeError("No existe un almacén activo para registrar las entradas.")

        # Cada pedido representa la compra que originó el stock inicial.
        if not pedidos_existentes:
            proveedores = {
                "Motor y lubricación": "Importadora AutoCaribe",
                "Frenos y suspensión": "Importadora AutoCaribe",
                "Eléctrico y encendido": "Distribuidora El Puente",
                "Carrocería y exterior": "Importadora AutoCaribe",
                "Repuestos para moto": "Repuestos Moto Norte",
                "Repuestos para bicicleta": "CicloPartes Dominicana",
                "Accesorios": "Distribuidora El Puente",
                "Herramientas": "Distribuidora El Puente",
            }
            pedidos_por_categoria = {}
            for producto_id, nombre, proveedor, costo, stock in productos:
                cur.execute("SELECT categoria FROM inventario WHERE id=?", (producto_id,))
                categoria = cur.fetchone()[0] or "Accesorios"
                pedidos_por_categoria.setdefault(categoria, []).append((producto_id, nombre, costo, stock, proveedores.get(categoria, proveedor)))
            for indice, (categoria, items) in enumerate(sorted(pedidos_por_categoria.items()), 1):
                numero = 1000 + indice
                for producto_id, nombre, costo, stock, proveedor in items:
                    insertar(cur, "pedidos", {
                        "numero_pedido": numero, "proveedor": proveedor,
                        "producto": nombre, "cantidad": stock, "fecha": fecha,
                        "hora": hora, "precio": costo, "costo": costo,
                    })
                    insertar(cur, "movimientos_inventario", {
                        "producto_id": producto_id, "almacen_id": almacen[0],
                        "tipo": "Entrada inicial", "cantidad": stock,
                        "referencia": f"Pedido de compra #{numero}",
                        "usuario": "Jose Veras", "fecha": fecha, "hora": hora,
                    })

        cur.execute("SELECT COUNT(*) FROM servicios")
        if cur.fetchone()[0] == 0:
            servicios = [
                ("Cambio de aceite", 650, 150, "Cambio de aceite y revisión básica", "Exento"),
                ("Instalación de batería", 500, 100, "Instalación y prueba de batería", "Exento"),
                ("Ajuste de frenos de bicicleta", 400, 80, "Ajuste de frenos y revisión", "Exento"),
                ("Instalación de accesorios", 800, 200, "Instalación de accesorio automotriz", "Exento"),
            ]
            for nombre, precio, costo, descripcion, impuesto in servicios:
                insertar(cur, "servicios", {"nombre": nombre, "precio": precio, "costo": costo, "descripcion": descripcion, "tipo_impuesto": impuesto, "estado": "Activo", "fecha_creacion": f"{fecha} {hora}"})

        cur.execute("SELECT COUNT(*) FROM promociones")
        if cur.fetchone()[0] == 0:
            promociones = [
                ("Descuento mantenimiento moto", "Porcentaje (%)", 5, "Promoción de temporada para motor y frenos"),
                ("Accesorios para ciclistas", "Porcentaje (%)", 10, "Descuento en accesorios de bicicleta"),
            ]
            for nombre, tipo, descuento, _descripcion in promociones:
                insertar(cur, "promociones", {"nombre": nombre, "tipo": tipo, "descuento": descuento, "fecha_inicio": fecha, "fecha_fin": "2027-12-31", "estado": "Activa"})

        cur.execute("SELECT COUNT(*) FROM combos")
        if cur.fetchone()[0] == 0:
            catalogo = {fila[1]: fila for fila in productos}
            combos = [
                ("Kit cambio de aceite", 850, ["Aceite motor 20W-50 1 qt", "Filtro de aceite Toyota Corolla"]),
                ("Kit seguridad bicicleta", 1500, ["Luz LED recargable bicicleta", "Candado de seguridad bicicleta"]),
                ("Kit mantenimiento moto", 850, ["Aceite 4T para motocicleta 20W-50", "Bujía para motocicleta"]),
            ]
            for nombre, precio_venta, nombres in combos:
                detalles = [catalogo[n] for n in nombres if n in catalogo]
                costo_total = sum(float(f[3] or 0) for f in detalles)
                combo_id = insertar(cur, "combos", {"nombre": nombre, "precio_venta": precio_venta, "costo_total": costo_total, "estado": "Activo"})
                for fila in detalles:
                    insertar(cur, "combo_detalle", {"combo_id": combo_id, "producto_id": fila[0], "producto_nombre": fila[1], "cantidad": 1, "costo_unitario": fila[3]})
        conn.commit()
        cur.execute("SELECT COUNT(*) FROM pedidos")
        pedidos = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM movimientos_inventario")
        movimientos = cur.fetchone()[0]
        print("DATOS_OPERATIVOS_COMPLETADOS", "pedidos", pedidos, "movimientos_inventario", movimientos)


if __name__ == "__main__":
    completar()
