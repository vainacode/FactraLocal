import db_conexion


class ServicioClientes:
    def __init__(self, conexion=db_conexion):
        self.conexion = conexion

    def listar(self):
        with self.conexion.connect("database.db") as conn:
            return conn.execute("SELECT id,nombre,tipo_id,cedula,celular,direccion,correo FROM clientes WHERE estado != 'Inactivo' OR estado IS NULL ORDER BY nombre").fetchall()

    def obtener(self, cliente_id):
        with self.conexion.connect("database.db") as conn:
            return conn.execute("SELECT nombre,tipo_id,cedula,celular,direccion,correo FROM clientes WHERE id=?", (cliente_id,)).fetchone()

    def crear(self, nombre, tipo_id, cedula, celular, direccion, correo):
        with self.conexion.connect("database.db") as conn:
            fila = conn.execute("INSERT INTO clientes(nombre,tipo_id,cedula,celular,direccion,correo,estado) VALUES(?,?,?,?,?,?, 'Activo') RETURNING id", (nombre, tipo_id, cedula, celular, direccion, correo)).fetchone()
            conn.commit()
            return fila[0]

    def actualizar(self, cliente_id, nombre, tipo_id, cedula, celular, direccion, correo):
        with self.conexion.connect("database.db") as conn:
            conn.execute("UPDATE clientes SET nombre=?,tipo_id=?,cedula=?,celular=?,direccion=?,correo=? WHERE id=?", (nombre, tipo_id, cedula, celular, direccion, correo, cliente_id))
            conn.commit()

    def desactivar(self, cliente_id):
        with self.conexion.connect("database.db") as conn:
            conn.execute("UPDATE clientes SET estado='Inactivo' WHERE id=?", (cliente_id,))
            conn.commit()

    def filtrar(self, texto):
        patron = f"%{str(texto).lower()}%"
        with self.conexion.connect("database.db") as conn:
            return conn.execute("SELECT id,nombre,tipo_id,cedula,celular,direccion,correo FROM clientes WHERE (LOWER(nombre) LIKE ? OR CAST(cedula AS TEXT) LIKE ?) AND (estado != 'Inactivo' OR estado IS NULL) ORDER BY nombre", (patron, patron)).fetchall()

    def listar_para_defecto(self):
        with self.conexion.connect("database.db") as conn:
            clientes = conn.execute("SELECT nombre,cedula FROM clientes WHERE estado != 'Inactivo' OR estado IS NULL").fetchall()
            defecto = conn.execute("SELECT cliente_nombre FROM cliente_defecto WHERE id=1").fetchone()
        return clientes, (defecto[0] if defecto else None)

    def guardar_defecto(self, nombre, cedula):
        with self.conexion.connect("database.db") as conn:
            conn.execute("DELETE FROM cliente_defecto WHERE id=1")
            conn.execute("INSERT INTO cliente_defecto (id,cliente_nombre,cliente_cedula) VALUES (1,?,?)", (nombre, cedula))
            conn.commit()
