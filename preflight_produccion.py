"""Comprobaciones previas al primer arranque en producción.

Ejecutar con POS_ENV=production y las variables POS_DB_* configuradas.
No imprime contraseñas ni API Keys.
"""
import importlib
import glob
import os
import shutil
import sys


DEPENDENCIAS = ("psycopg2", "requests", "PIL", "ttkthemes", "reportlab", "cryptography", "barcode")
TABLAS_CRITICAS = (
    "usuarios", "roles_permisos", "ventas", "cajas", "inventario",
    "numeracion_local", "comprobantes_fiscales", "movimientos_caja",
    "movimientos_bancarios", "cuentas_bancarias", "abonos_credito",
    "inventario_almacen", "movimientos_inventario", "auditoria_eventos",
    "empresa", "puntos_venta", "almacenes", "configuracion_general",
    "facturas_pendientes",
)


def _herramienta_postgres(nombre):
    encontrada = shutil.which(nombre)
    if encontrada:
        return encontrada
    rutas = []
    for raiz in (r"C:\Program Files\PostgreSQL", r"C:\Program Files (x86)\PostgreSQL"):
        rutas.extend(glob.glob(os.path.join(raiz, "*", "bin", f"{nombre}.exe")))
    return sorted(rutas, reverse=True)[0] if rutas else None


def main():
    errores = []
    entorno = os.getenv("POS_ENV", "development").lower()
    if entorno != "production":
        errores.append("POS_ENV debe ser 'production'.")
    for nombre in ("POS_DB_HOST", "POS_DB_NAME", "POS_DB_USER", "POS_DB_PASSWORD"):
        if not os.getenv(nombre):
            errores.append(f"Falta la variable {nombre}.")
    sslmode = os.getenv("POS_DB_SSLMODE", "require").lower()
    if sslmode not in ("require", "verify-ca", "verify-full"):
        errores.append("POS_DB_SSLMODE debe ser require, verify-ca o verify-full en producción.")
    for modulo in DEPENDENCIAS:
        try:
            importlib.import_module(modulo)
        except ImportError:
            errores.append(f"Falta la dependencia Python: {modulo}.")
    for herramienta in ("pg_dump", "psql"):
        if not _herramienta_postgres(herramienta):
            errores.append(f"No se encontró la herramienta PostgreSQL: {herramienta}.")

    if errores:
        for error in errores:
            print(f"ERROR: {error}")
        return 1

    import db_conexion
    import manager
    if not manager.migrar_base_datos():
        print("ERROR: no se pudo completar la migración de PostgreSQL.")
        return 1
    from permisos import preparar_permisos
    try:
        preparar_permisos()
    except Exception as error:
        print(f"ERROR: no se pudo preparar la matriz de permisos: {error}")
        return 1
    try:
        with db_conexion.connect() as conn:
            # information_schema oculta tablas para las que el usuario de la
            # aplicación no tiene privilegios. pg_catalog permite distinguir
            # una tabla inexistente de una tabla existente pero inaccesible.
            filas = conn.execute(
                "SELECT c.relname FROM pg_class c "
                "JOIN pg_namespace n ON n.oid = c.relnamespace "
                "WHERE n.nspname = 'public' AND c.relkind IN ('r', 'p') "
                "AND c.relname = ANY(?)",
                (list(TABLAS_CRITICAS),),
            ).fetchall()
            modo = conn.execute(
                "SELECT modo_facturacion, factrapi_url_base, factrapi_api_key, punto_venta_id "
                "FROM configuracion_general WHERE id = 1"
            ).fetchone()
            punto_venta_remoto = None
            if modo and modo[3]:
                punto_venta_remoto = conn.execute(
                    "SELECT factrapi_punto_venta_id FROM puntos_venta WHERE id = ?",
                    (modo[3],),
                ).fetchone()
            administradores = conn.execute("SELECT COUNT(*) FROM usuarios WHERE rol = 'Administrador' AND estado != 'Inactivo'").fetchone()[0]
            usuarios_duplicados = conn.execute(
                "SELECT COUNT(*) FROM (SELECT LOWER(username) FROM usuarios GROUP BY LOWER(username) HAVING COUNT(*) > 1) AS duplicados"
            ).fetchone()[0]
            permisos = conn.execute("SELECT COUNT(*) FROM roles_permisos").fetchone()[0]
            contrasenas_sin_hash = conn.execute(
                "SELECT COUNT(*) FROM usuarios WHERE password IS NULL OR password NOT LIKE 'pbkdf2_sha256$%%'"
            ).fetchone()[0]
            empresa_configurada = conn.execute(
                "SELECT COUNT(*) FROM empresa WHERE NULLIF(BTRIM(COALESCE(nombre, '')), '') IS NOT NULL"
            ).fetchone()[0]
            puntos_venta_activos = conn.execute(
                "SELECT COUNT(*) FROM puntos_venta WHERE estado = 'Activo'"
            ).fetchone()[0]
            almacenes_activos = conn.execute(
                "SELECT COUNT(*) FROM almacenes WHERE estado = 'Activo'"
            ).fetchone()[0]
            almacen_configurado = conn.execute(
                "SELECT COUNT(*) FROM configuracion_general cg "
                "JOIN almacenes a ON a.id = cg.almacen_id "
                "WHERE cg.id = 1 AND a.estado = 'Activo'"
            ).fetchone()[0]
            ventas_sin_caja = conn.execute(
                "SELECT COUNT(*) FROM ventas WHERE caja_id IS NULL"
            ).fetchone()[0]
            ventas_sin_almacen = conn.execute(
                "SELECT COUNT(*) FROM ventas WHERE almacen_id IS NULL"
            ).fetchone()[0]
            pendientes_sin_caja = conn.execute(
                "SELECT COUNT(*) FROM facturas_pendientes WHERE caja_id IS NULL"
            ).fetchone()[0]
            abonos_sin_caja = conn.execute(
                "SELECT COUNT(*) FROM abonos_credito WHERE caja_id IS NULL"
            ).fetchone()[0]
            cajas_abiertas = conn.execute(
                "SELECT COUNT(*) FROM cajas WHERE estado = 'Abierta'"
            ).fetchone()[0]
            comprobantes_sin_venta = conn.execute(
                "SELECT COUNT(*) FROM comprobantes_fiscales cf "
                "LEFT JOIN ventas v ON v.factura = cf.factura_local "
                "WHERE v.factura IS NULL AND cf.factura_local IS NOT NULL"
            ).fetchone()[0]
            api_key_sin_cifrar = 0
            if modo and modo[0] == "ecf_factrapi" and modo[2]:
                api_key_sin_cifrar = conn.execute(
                    "SELECT COUNT(*) FROM configuracion_general "
                    "WHERE id = 1 AND factrapi_api_key IS NOT NULL "
                    "AND factrapi_api_key NOT LIKE 'fernet$%%'"
                ).fetchone()[0]
            # La auditoría es obligatoria: comprobar acceso real, no solo que
            # el objeto aparezca en el catálogo del servidor.
            conn.execute("SELECT 1 FROM auditoria_eventos LIMIT 1").fetchone()
        presentes = {fila[0] for fila in filas}
    except Exception as error:
        print(f"ERROR: no se pudo verificar el esquema: {error}")
        return 1

    faltantes = sorted(set(TABLAS_CRITICAS) - presentes)
    if faltantes:
        print("ERROR: faltan tablas críticas: " + ", ".join(faltantes))
        return 1
    if administradores < 1:
        print("ERROR: no existe un administrador activo.")
        return 1
    if usuarios_duplicados:
        print("ERROR: existen nombres de usuario duplicados; resuélvalos antes de producción.")
        return 1
    if permisos < 1:
        print("ERROR: la matriz de roles y permisos está vacía.")
        return 1
    if contrasenas_sin_hash:
        print("ERROR: existen contraseñas de usuarios sin hash seguro.")
        return 1
    if not empresa_configurada:
        print("ERROR: la empresa no tiene nombre comercial configurado.")
        return 1
    if puntos_venta_activos < 1:
        print("ERROR: no existe un punto de venta activo.")
        return 1
    if almacenes_activos < 1:
        print("ERROR: no existe un almacén activo.")
        return 1
    if not almacen_configurado:
        print("ERROR: no hay un almacén operativo activo configurado en el punto de venta.")
        return 1
    if ventas_sin_caja:
        print(f"ERROR: existen {ventas_sin_caja} ventas históricas sin caja; revise esos registros antes de producción.")
        return 1
    if ventas_sin_almacen:
        print(f"ERROR: existen {ventas_sin_almacen} ventas históricas sin almacén; revise esos registros antes de producción.")
        return 1
    if pendientes_sin_caja:
        print(f"ERROR: existen {pendientes_sin_caja} facturas pendientes sin caja; no se puede garantizar el cuadre.")
        return 1
    if abonos_sin_caja:
        print(f"ERROR: existen {abonos_sin_caja} abonos sin caja asociada; revise el historial antes de producción.")
        return 1
    if cajas_abiertas:
        print(f"ERROR: existen {cajas_abiertas} cajas abiertas; deben cuadrarse y cerrarse antes del corte.")
        return 1
    if comprobantes_sin_venta:
        print(f"ERROR: existen {comprobantes_sin_venta} comprobantes fiscales sin venta asociada.")
        return 1
    if modo and modo[0] == "ecf_factrapi":
        if not os.getenv("POS_FACTRAPI_ENCRYPTION_KEY"):
            print("ERROR: falta POS_FACTRAPI_ENCRYPTION_KEY para el modo e-CF.")
            return 1
        if not modo[1] or not modo[2]:
            print("ERROR: el modo e-CF requiere URL y API Key de FactrAPI configuradas.")
            return 1
        if not modo[3] or not punto_venta_remoto or not punto_venta_remoto[0]:
            print("ERROR: el punto de venta e-CF no está enlazado con FactrAPI.")
            return 1
        if api_key_sin_cifrar:
            print("ERROR: la API Key de FactrAPI está almacenada sin cifrar.")
            return 1
    print("PREFLIGHT_PRODUCCION_OK")
    print("PostgreSQL, migración, dependencias y tablas críticas verificadas.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
