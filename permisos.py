import db_conexion as sqlite3


MODULOS = (
    "Ventas",
    "Cotizaciones",
    "Inventario",
    "Clientes",
    "Proveedor",
    "Compras",
    "Cobros",
    "Reportes",
    "Configuración",
    "Gastos",
    "Usuarios",
    "Gestión Caja",
)

ROLES = ("Administrador", "Supervisor", "Cajero")

PERMISOS_PREDETERMINADOS = {
    "Administrador": set(MODULOS),
    "Supervisor": {
        "Ventas", "Cotizaciones", "Inventario", "Clientes", "Proveedor",
        "Compras", "Cobros", "Reportes", "Gastos", "Gestión Caja",
    },
    "Cajero": {"Ventas", "Cotizaciones", "Clientes", "Cobros", "Gestión Caja"},
}


def preparar_permisos():
    """Crea la tabla y sus valores iniciales sin borrar personalizaciones."""
    with sqlite3.connect("database.db") as conn:
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS roles_permisos (
                id SERIAL PRIMARY KEY,
                rol VARCHAR(30) NOT NULL,
                modulo VARCHAR(60) NOT NULL,
                permitido BOOLEAN NOT NULL DEFAULT FALSE,
                UNIQUE (rol, modulo)
            )
        """)
        for rol in ROLES:
            for modulo in MODULOS:
                cur.execute("""
                    INSERT INTO roles_permisos (rol, modulo, permitido)
                    VALUES (?, ?, ?)
                    ON CONFLICT (rol, modulo) DO NOTHING
                """, (rol, modulo, modulo in PERMISOS_PREDETERMINADOS[rol]))
        conn.commit()


def obtener_permisos(rol):
    if not rol:
        return set()
    if rol == "Administrador":
        return set(MODULOS)
    try:
        with sqlite3.connect("database.db") as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT modulo FROM roles_permisos WHERE rol = ? AND permitido = TRUE",
                (rol,),
            )
            return {fila[0] for fila in cur.fetchall()}
    except sqlite3.Error:
        return set(PERMISOS_PREDETERMINADOS.get(rol, set()))


def tiene_permiso(rol, modulo):
    return modulo in obtener_permisos(rol)


def guardar_permisos(rol, modulos):
    if rol == "Administrador":
        modulos = set(MODULOS)
    else:
        modulos = set(modulos)
    with sqlite3.connect("database.db") as conn:
        cur = conn.cursor()
        for modulo in MODULOS:
            cur.execute(
                "UPDATE roles_permisos SET permitido = ? WHERE rol = ? AND modulo = ?",
                (modulo in modulos, rol, modulo),
            )
        conn.commit()
