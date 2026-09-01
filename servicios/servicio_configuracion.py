import db_conexion


class ServicioConfiguracion:
    def __init__(self, conexion=db_conexion):
        self.conexion = conexion

    def obtener_empresa(self):
        with self.conexion.connect("database.db") as conn:
            return conn.execute("SELECT nombre,direccion,telefono,email,website,image_path,tipo_id,numero_id,nit,ciudad FROM empresa ORDER BY id LIMIT 1").fetchone()

    def obtener_general(self):
        with self.conexion.connect("database.db") as conn:
            return conn.execute("SELECT * FROM configuracion_general WHERE id=1").fetchone()

    def obtener_empresa_detalle(self):
        with self.conexion.connect("database.db") as conn:
            return conn.execute("SELECT nombre,nit,telefono,direccion,ciudad,email,image_path FROM empresa LIMIT 1").fetchone()

    def guardar_empresa(self, datos):
        with self.conexion.connect("database.db") as conn:
            conn.execute("DELETE FROM empresa")
            conn.execute("INSERT INTO empresa (nombre,nit,telefono,direccion,ciudad,email,image_path) VALUES (?,?,?,?,?,?,?)", datos)
            conn.commit()

    def obtener_moneda(self):
        with self.conexion.connect("database.db") as conn:
            return conn.execute("SELECT nombre,simbolo,codigo FROM moneda LIMIT 1").fetchone()

    def guardar_moneda(self, datos):
        with self.conexion.connect("database.db") as conn:
            conn.execute("DELETE FROM moneda")
            conn.execute("INSERT INTO moneda (nombre,simbolo,codigo) VALUES (?,?,?)", datos)
            conn.commit()

    def obtener_impuestos(self):
        with self.conexion.connect("database.db") as conn:
            return conn.execute("SELECT nombre_impuesto,porcentaje_impuesto,precios_incluyen_impuesto,desglosar_impuesto,margen_utilidad_defecto FROM configuracion_general WHERE id=1").fetchone()

    def guardar_impuestos(self, datos):
        with self.conexion.connect("database.db") as conn:
            conn.execute("UPDATE configuracion_general SET nombre_impuesto=?,porcentaje_impuesto=?,precios_incluyen_impuesto=?,desglosar_impuesto=?,margen_utilidad_defecto=? WHERE id=1", datos)
            conn.commit()

    def limpiar_registros_desarrollo(self):
        with self.conexion.connect("database.db") as conn:
            conn.execute("DELETE FROM ventas")
            conn.execute("DELETE FROM gastos")
            conn.commit()

    def crear_sucursal(self, datos):
        with self.conexion.connect("database.db") as conn:
            conn.execute("INSERT INTO sucursal(nombre,direccion,telefono,encargado,estado) VALUES(?,?,?,?,?)", datos); conn.commit()

    def actualizar_sucursal(self, sucursal_id, datos):
        with self.conexion.connect("database.db") as conn:
            conn.execute("UPDATE sucursal SET nombre=?,direccion=?,telefono=?,encargado=?,estado=? WHERE id=?", (*datos,sucursal_id)); conn.commit()

    def eliminar_sucursal(self, sucursal_id):
        with self.conexion.connect("database.db") as conn:
            conn.execute("DELETE FROM sucursal WHERE id=?", (sucursal_id,)); conn.commit()

    def guardar_nota_local(self, datos):
        with self.conexion.connect("database.db") as conn:
            conn.execute("INSERT INTO notas_credito_debito_locales(tipo,factura_afectada,motivo,monto,fecha,hora,cajero) VALUES(?,?,?,?,?,?,?)", datos); conn.commit()

    def crear_secuencia_ncf(self, datos):
        with self.conexion.connect("database.db") as conn:
            conn.execute("INSERT INTO secuencias_ncf_tradicional(tipo_ncf,secuencia_desde,secuencia_hasta,secuencia_actual,fecha_vencimiento) VALUES(?,?,?,?,?)", datos); conn.commit()

    def guardar_numeracion_fiscal(self, modo, punto_venta_id, codigo_pv, nombre_pv,
                                  sucursal_nom, ambiente, url_base, api_key_db):
        """Guarda atomicamente la configuración local y sincroniza el PV remoto si procede."""
        with self.conexion.connect("database.db") as conn:
            if codigo_pv and nombre_pv:
                sucursal_id = None
                if sucursal_nom:
                    fila = conn.execute("SELECT id FROM sucursal WHERE nombre=?", (sucursal_nom,)).fetchone()
                    sucursal_id = fila[0] if fila else None
                if punto_venta_id:
                    conn.execute("UPDATE puntos_venta SET codigo=?,nombre=?,sucursal_id=? WHERE id=?", (codigo_pv, nombre_pv, sucursal_id, punto_venta_id))
                else:
                    punto_venta_id = conn.execute("INSERT INTO puntos_venta(codigo,nombre,sucursal_id) VALUES(?,?,?) RETURNING id", (codigo_pv, nombre_pv, sucursal_id)).fetchone()[0]
            conn.execute("UPDATE configuracion_general SET modo_facturacion=?,punto_venta_id=?,factrapi_ambiente=?,factrapi_url_base=?,factrapi_api_key=? WHERE id=1", (modo, punto_venta_id, ambiente, url_base or None, api_key_db or None))
            conn.commit()

        if modo == "ecf_factrapi" and punto_venta_id and url_base and api_key_db:
            with self.conexion.connect("database.db") as conn:
                remoto = conn.execute("SELECT factrapi_punto_venta_id FROM puntos_venta WHERE id=?", (punto_venta_id,)).fetchone()
            if not remoto or not remoto[0]:
                import factrapi_cliente as fc
                creado = fc.crear_punto_venta(codigo_pv, nombre_pv, sucursal_nom or None)
                remoto_id = creado.get("id")
                if remoto_id:
                    with self.conexion.connect("database.db") as conn:
                        conn.execute("UPDATE puntos_venta SET factrapi_punto_venta_id=? WHERE id=?", (remoto_id, punto_venta_id))
                        conn.commit()
        return punto_venta_id
