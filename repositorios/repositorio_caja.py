class RepositorioCaja:
    def obtener_abierta(self, conn, usuario):
        return conn.execute(
            "SELECT id FROM cajas WHERE estado = 'Abierta' AND cajero = ? ORDER BY id DESC LIMIT 1",
            (usuario,),
        ).fetchone()

    def verificar_abierta(self, conn, caja_id):
        fila = conn.execute("SELECT estado FROM cajas WHERE id = ? FOR UPDATE", (caja_id,)).fetchone()
        return bool(fila and str(fila[0]).lower() == "abierta")

    def obtener_almacen_operativo(self, conn):
        fila = conn.execute("SELECT almacen_id FROM configuracion_general WHERE id = 1").fetchone()
        return fila[0] if fila and fila[0] else None

