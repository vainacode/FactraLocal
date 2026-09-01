class RepositorioClientes:
    def listar_nombres(self, conn):
        return [fila[0] for fila in conn.execute(
            "SELECT nombre FROM clientes WHERE estado != 'Inactivo' OR estado IS NULL"
        ).fetchall()]

    def obtener_nombre_defecto(self, conn):
        fila = conn.execute("SELECT cliente_nombre FROM cliente_defecto WHERE id = 1").fetchone()
        return fila[0] if fila else None

