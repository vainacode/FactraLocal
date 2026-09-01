import db_conexion
from seguridad import hash_password, validar_password


class ServicioUsuarios:
    def __init__(self, conexion=db_conexion):
        self.conexion = conexion

    def listar(self):
        with self.conexion.connect("database.db") as conn:
            return conn.execute("SELECT id,COALESCE(nombre,username),username,rol,telefono,estado FROM usuarios ORDER BY id").fetchall()

    def crear(self, nombre, username, password, rol, telefono, estado):
        if not validar_password(password):
            raise ValueError("Use al menos 8 caracteres, incluyendo letras y números.")
        with self.conexion.connect("database.db") as conn:
            if conn.execute("SELECT 1 FROM usuarios WHERE LOWER(username)=LOWER(?)", (username,)).fetchone():
                raise ValueError("Ya existe un usuario con ese nombre de acceso.")
            conn.execute("INSERT INTO usuarios(nombre,username,password,rol,telefono,estado) VALUES(?,?,?,?,?,?)", (nombre, username, hash_password(password), rol, telefono, estado))
            conn.commit()

    def actualizar_password_legacy(self, usuario_id, password):
        with self.conexion.connect("database.db") as conn:
            conn.execute("UPDATE usuarios SET password=? WHERE id=?", (hash_password(password), usuario_id))
            conn.commit()

    def registrar_cajero_publico(self, username, password):
        if not validar_password(password):
            raise ValueError("Use al menos 8 caracteres, incluyendo letras y números.")
        with self.conexion.connect("database.db") as conn:
            if conn.execute("SELECT 1 FROM usuarios WHERE LOWER(username)=LOWER(?)", (username,)).fetchone():
                return False
            conn.execute("INSERT INTO usuarios(username,password,rol) VALUES(?,?,?)", (username, hash_password(password), "Cajero"))
            conn.commit()
            return True

    def actualizar(self, usuario_id, nombre, username, password, rol, telefono, estado):
        with self.conexion.connect("database.db") as conn:
            if conn.execute("SELECT 1 FROM usuarios WHERE LOWER(username)=LOWER(?) AND id<>?", (username, usuario_id)).fetchone():
                raise ValueError("Ya existe otro usuario con ese nombre de acceso.")
            actual = conn.execute("SELECT rol,estado FROM usuarios WHERE id=?", (usuario_id,)).fetchone() or (None,None)
            if actual[0] == "Administrador" and (rol != "Administrador" or estado == "Inactivo"):
                activos = conn.execute("SELECT COUNT(*) FROM usuarios WHERE rol='Administrador' AND estado!='Inactivo'").fetchone()[0]
                if activos <= 1:
                    raise ValueError("Debe conservar al menos un administrador activo.")
            if password:
                if not validar_password(password):
                    raise ValueError("Use al menos 8 caracteres, incluyendo letras y números.")
                conn.execute("UPDATE usuarios SET nombre=?,username=?,password=?,rol=?,telefono=?,estado=? WHERE id=?", (nombre,username,hash_password(password),rol,telefono,estado,usuario_id))
            else:
                conn.execute("UPDATE usuarios SET nombre=?,username=?,rol=?,telefono=?,estado=? WHERE id=?", (nombre,username,rol,telefono,estado,usuario_id))
            conn.commit()

    def inactivar(self, usuario_id, usuario_actual_id=None):
        with self.conexion.connect("database.db") as conn:
            if usuario_actual_id is not None and str(usuario_actual_id) == str(usuario_id):
                raise ValueError("No puede inactivar el usuario de la sesión actual.")
            rol = (conn.execute("SELECT rol FROM usuarios WHERE id=?", (usuario_id,)).fetchone() or (None,))[0]
            if rol == "Administrador" and conn.execute("SELECT COUNT(*) FROM usuarios WHERE rol='Administrador' AND estado!='Inactivo'").fetchone()[0] <= 1:
                raise ValueError("Debe existir al menos un administrador activo.")
            conn.execute("UPDATE usuarios SET estado='Inactivo' WHERE id=?", (usuario_id,))
            conn.commit()
