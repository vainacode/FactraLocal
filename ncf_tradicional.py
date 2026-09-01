import datetime

import db_conexion


TIPOS_NCF = (
    ("B01", "Crédito Fiscal"),
    ("B02", "Consumo"),
    ("B14", "Régimen Especial"),
    ("B15", "Gubernamental"),
    ("B04", "Nota de Crédito"),
)


def siguiente_ncf(tipo_ncf, conn=None):
    """Reserva atómicamente el próximo número de un rango autorizado."""
    propia = conn is None
    if propia:
        conn = db_conexion.connect()
    try:
        cur = conn.cursor()
        cur.execute("""
            UPDATE secuencias_ncf_tradicional
            SET secuencia_actual = secuencia_actual + 1
            WHERE tipo_ncf = ? AND activa = TRUE
              AND secuencia_actual <= secuencia_hasta
              AND (fecha_vencimiento IS NULL OR fecha_vencimiento = ''
                   OR fecha_vencimiento >= CURRENT_DATE::text)
            RETURNING tipo_ncf, secuencia_actual - 1, fecha_vencimiento
        """, (tipo_ncf,))
        fila = cur.fetchone()
        if not fila:
            raise ValueError(f"No hay una secuencia activa disponible para {tipo_ncf}.")
        if propia:
            conn.commit()
        return f"{fila[0]}{int(fila[1]):08d}", fila[2]
    finally:
        if propia:
            conn.close()


def alertas_ncf(umbral=50):
    alertas = []
    try:
        with db_conexion.connect() as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT tipo_ncf, secuencia_actual, secuencia_hasta, fecha_vencimiento
                FROM secuencias_ncf_tradicional WHERE activa = TRUE
            """)
            for tipo, actual, hasta, vencimiento in cur.fetchall():
                disponibles = int(hasta) - int(actual) + 1
                if disponibles <= umbral:
                    alertas.append(f"{tipo}: quedan {max(0, disponibles)}")
                if vencimiento:
                    try:
                        fecha = datetime.date.fromisoformat(str(vencimiento)[:10])
                        dias = (fecha - datetime.date.today()).days
                        if dias <= 30:
                            alertas.append(f"{tipo}: vence en {max(0, dias)} días")
                    except ValueError:
                        pass
    except db_conexion.Error:
        pass
    return alertas
