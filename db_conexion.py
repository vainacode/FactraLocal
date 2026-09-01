"""Capa de compatibilidad para conectar el sistema (escrito contra la API
de sqlite3) a la base de datos PostgreSQL (factra_db).

El resto del proyecto sigue usando exactamente el mismo patrón de
siempre:

    import db_conexion as sqlite3
    ...
    with sqlite3.connect(self.db_name) as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM ventas WHERE factura = ?", (factura,))

Este módulo traduce los placeholders "?" de sqlite3 a "%s" de psycopg2 y
envuelve la conexión/cursor para que el resto del código no necesite
cambiar ni una consulta.
"""
import os
import psycopg2

# Alias de excepciones para que "except sqlite3.Error as e:" siga funcionando.
Error = psycopg2.Error
IntegrityError = psycopg2.IntegrityError
OperationalError = psycopg2.OperationalError
ProgrammingError = psycopg2.ProgrammingError

_ENTORNO = os.getenv("POS_ENV", "development").lower()
DSN = {
    "host": os.getenv("POS_DB_HOST", "localhost"),
    "port": int(os.getenv("POS_DB_PORT", "5432")),
    "dbname": os.getenv("POS_DB_NAME", "factra_db"),
    "user": os.getenv("POS_DB_USER", "pos_app"),
    "password": os.getenv("POS_DB_PASSWORD", ""),
    # En producción se exige TLS salvo que el administrador lo cambie
    # explícitamente para una instalación local controlada.
    "sslmode": os.getenv("POS_DB_SSLMODE", "require" if _ENTORNO == "production" else "prefer"),
}


def _traducir(sql):
    """Convierte los placeholders '?' (estilo sqlite3) a '%s' (estilo psycopg2)."""
    return sql.replace("?", "%s")


class _CursorWrapper:
    def __init__(self, cur):
        self._cur = cur

    def execute(self, sql, params=()):
        self._cur.execute(_traducir(sql), params)
        return self

    def executemany(self, sql, seq_params):
        self._cur.executemany(_traducir(sql), seq_params)
        return self

    def fetchone(self):
        return self._cur.fetchone()

    def fetchall(self):
        return self._cur.fetchall()

    def fetchmany(self, size=None):
        return self._cur.fetchmany(size) if size is not None else self._cur.fetchmany()

    def __iter__(self):
        return iter(self._cur)

    def __getattr__(self, nombre):
        return getattr(self._cur, nombre)


class _ConnWrapper:
    def __init__(self, conn):
        self._conn = conn

    def cursor(self):
        return _CursorWrapper(self._conn.cursor())

    def execute(self, sql, params=()):
        """Equivalente a sqlite3.Connection.execute(...) (atajo usado en documentos.py)."""
        cur = self.cursor()
        cur.execute(sql, params)
        return cur

    def commit(self):
        self._conn.commit()

    def rollback(self):
        self._conn.rollback()

    def close(self):
        self._conn.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # Confirma o revierte y siempre libera la conexión PostgreSQL. A
        # diferencia de sqlite3, psycopg2 no cierra la conexión al salir del
        # context manager; dejarla abierta en cada pantalla termina agotando
        # las conexiones disponibles durante una jornada larga.
        try:
            if exc_type is None:
                self._conn.commit()
            else:
                self._conn.rollback()
        finally:
            self._conn.close()
        return False

    def __getattr__(self, nombre):
        return getattr(self._conn, nombre)


def connect(db_name=None, *args, **kwargs):
    """Firma compatible con sqlite3.connect(db_name); db_name se ignora
    porque la conexión real va siempre a factra_db en PostgreSQL."""
    if _ENTORNO == "production" and not DSN["password"]:
        raise OperationalError(
            "Falta POS_DB_PASSWORD. Configure las credenciales fuera del código "
            "antes de iniciar el sistema en producción."
        )
    conn = psycopg2.connect(**DSN)
    return _ConnWrapper(conn)


def ver_siguiente_numero(documento):
    """Consulta (sin reservar) cuál es el próximo número de `documento`, solo
    para mostrarlo en pantalla mientras el cajero arma la venta/cotización.
    El número real se asigna recién en siguiente_numero(), al confirmar —
    por eso el número mostrado aquí puede correrse si hay más de una caja
    activa (es solo una vista previa, no una reserva)."""
    with connect() as conn:
        cur = conn.cursor()
        cur.execute("SELECT siguiente FROM numeracion_local WHERE documento = ?", (documento,))
        fila = cur.fetchone()
        return fila[0] if fila else 1


def siguiente_numero(documento, conn=None):
    """Asigna atómicamente el siguiente número correlativo para `documento`
    ('ticket_venta', 'cotizacion', 'pedido', ...) usando la tabla
    numeracion_local (ver PLAN_FACTURACION_ELECTRONICA.md, Fase 1).

    Es seguro con múltiples cajas/procesos concurrentes: el UPDATE ...
    RETURNING es atómico en PostgreSQL, nunca lee y luego escribe por
    separado (eso permitiría que dos cajas obtuvieran el mismo número).

    Si `conn` se pasa (una conexión/transacción ya abierta), el número
    asignado queda sujeto al commit/rollback de esa transacción — si la
    venta falla y se revierte, el número también se libera. Si no se pasa
    `conn`, se usa una conexión propia con commit inmediato (el número
    queda tomado aunque la operación que lo pidió falle después).
    """
    propia = conn is None
    if propia:
        conn = connect()
    try:
        cur = conn.cursor()
        cur.execute('''
            UPDATE numeracion_local SET siguiente = siguiente + 1
            WHERE documento = ?
            RETURNING siguiente - 1
        ''', (documento,))
        fila = cur.fetchone()
        if fila is None:
            raise ValueError(f"Documento de numeración desconocido: {documento}")
        numero = fila[0]
        if propia:
            conn.commit()
        return numero
    finally:
        if propia:
            conn.close()
