"""Auditoría no destructiva para revisar una base antes del corte."""
import json
import sys

import db_conexion


CONSULTAS = {
    "ventas_sin_caja": "SELECT COUNT(*) FROM ventas WHERE caja_id IS NULL",
    "ventas_sin_almacen": "SELECT COUNT(*) FROM ventas WHERE almacen_id IS NULL",
    "pendientes_sin_caja": "SELECT COUNT(*) FROM facturas_pendientes WHERE caja_id IS NULL",
    "abonos_sin_caja": "SELECT COUNT(*) FROM abonos_credito WHERE caja_id IS NULL",
    "usuarios_sin_hash": "SELECT COUNT(*) FROM usuarios WHERE password IS NULL OR password NOT LIKE 'pbkdf2_sha256$%%'",
    "nombres_usuario_duplicados": "SELECT COUNT(*) FROM (SELECT LOWER(username) FROM usuarios GROUP BY LOWER(username) HAVING COUNT(*) > 1) AS duplicados",
    "cajas_abiertas": "SELECT COUNT(*) FROM cajas WHERE estado = 'Abierta'",
    "comprobantes_sin_venta": "SELECT COUNT(*) FROM comprobantes_fiscales cf LEFT JOIN ventas v ON v.factura=cf.factura_local WHERE v.factura IS NULL AND cf.factura_local IS NOT NULL",
}

DETALLES = {
    "usuarios_duplicados": (
        "SELECT id, username, nombre, rol, estado FROM usuarios "
        "WHERE LOWER(username) IN (SELECT LOWER(username) FROM usuarios "
        "GROUP BY LOWER(username) HAVING COUNT(*) > 1) ORDER BY LOWER(username), id"
    ),
    "ventas_sin_caja_detalle": (
        "SELECT DISTINCT factura, cliente, fecha, cajero FROM ventas "
        "WHERE caja_id IS NULL ORDER BY factura"
    ),
    "ventas_sin_almacen_detalle": (
        "SELECT DISTINCT factura, cliente, fecha, cajero FROM ventas "
        "WHERE almacen_id IS NULL ORDER BY factura"
    ),
    "cajas_abiertas_detalle": (
        "SELECT id, cajero, fecha_apertura, monto_inicial, punto_venta_id "
        "FROM cajas WHERE estado = 'Abierta' ORDER BY id"
    ),
}


def auditar():
    with db_conexion.connect() as conn:
        return {nombre: int(conn.execute(sql).fetchone()[0] or 0) for nombre, sql in CONSULTAS.items()}


def main():
    try:
        resultado = auditar()
    except Exception as error:
        print(f"ERROR: no se pudo auditar la base: {error}")
        return 1
    if "--json" in sys.argv:
        print(json.dumps(resultado, ensure_ascii=False, indent=2))
    else:
        print("AUDITORÍA PREPRODUCCIÓN")
        for nombre, valor in resultado.items():
            print(f"{nombre}: {valor}")
        if "--detalles" in sys.argv:
            with db_conexion.connect() as conn:
                for nombre, sql in DETALLES.items():
                    filas = conn.execute(sql).fetchall()
                    if filas:
                        print(f"\n{nombre}:")
                        for fila in filas:
                            print("  " + " | ".join(str(valor or "") for valor in fila))
    # Una caja heredada abierta también impide el corte: debe cuadrarse y
    # cerrarse antes de poner el sistema en servicio.
    bloqueantes = ("ventas_sin_caja", "ventas_sin_almacen", "pendientes_sin_caja", "usuarios_sin_hash", "nombres_usuario_duplicados", "comprobantes_sin_venta", "cajas_abiertas")
    if any(resultado[nombre] for nombre in bloqueantes):
        print("REVISIÓN_MANUAL_REQUERIDA")
        return 1
    print("AUDITORÍA_PREPRODUCCIÓN_OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
