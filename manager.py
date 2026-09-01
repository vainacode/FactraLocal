import os
import db_conexion as sqlite3
import sys
from tkinter import Tk, Frame, ttk
from ttkthemes import ThemedStyle
from login import Login, Registro
from container import Container
from window_utils import posicionar_ventana
from permisos import preparar_permisos
from seguridad import hash_password, PREFIJO


class EntrySeguro(ttk.Entry):
    """Entry que evita que una altura fija recorte el texto verticalmente."""

    def place(self, cnf=None, **kw):
        opciones = dict(cnf or {})
        opciones.update(kw)
        try:
            if float(opciones.get("height", 0)) < 32:
                opciones["height"] = 32
        except (TypeError, ValueError):
            pass
        return super().place(opciones)


def migrar_base_datos(db_name="database.db"):
    """Asegura que el esquema (PostgreSQL, factra_db) tenga las columnas/tablas
    requeridas por el flujo de ventas a crédito, facturas pendientes/anuladas
    y cuentas por cobrar. Idempotente: se puede ejecutar en cada arranque."""
    try:
        with sqlite3.connect(db_name) as conn:
            cur = conn.cursor()

            for tabla in ("ventas", "facturas_pendientes", "facturas_anuladas"):
                cur.execute('''
                    SELECT column_name FROM information_schema.columns
                    WHERE table_schema = 'public' AND table_name = ?
                ''', (tabla,))
                columnas = [c[0] for c in cur.fetchall()]
                if "medio_pago" not in columnas:
                    cur.execute(f"ALTER TABLE {tabla} ADD COLUMN medio_pago TEXT DEFAULT 'Efectivo'")
                if tabla in ("ventas", "facturas_pendientes") and "cuenta_destino" not in columnas:
                    cur.execute(f"ALTER TABLE {tabla} ADD COLUMN cuenta_destino TEXT")

            cur.execute('''
                SELECT column_name FROM information_schema.columns
                WHERE table_schema = 'public' AND table_name = 'facturas_anuladas'
            ''')
            columnas_fa = [c[0] for c in cur.fetchall()]
            if "anulo" not in columnas_fa:
                cur.execute("ALTER TABLE facturas_anuladas ADD COLUMN anulo TEXT")

            cur.execute('''
                CREATE TABLE IF NOT EXISTS abonos_credito (
                    id SERIAL PRIMARY KEY,
                    factura INTEGER,
                    cliente TEXT,
                    monto DOUBLE PRECISION,
                    fecha TEXT,
                    hora TEXT,
                    cajero TEXT,
                    metodo_pago TEXT,
                    cuenta_destino TEXT
                )
            ''')
            cur.execute('''
                SELECT column_name FROM information_schema.columns
                WHERE table_schema = 'public' AND table_name = 'abonos_credito'
            ''')
            columnas_abonos = [c[0] for c in cur.fetchall()]
            if "caja_id" not in columnas_abonos:
                cur.execute("ALTER TABLE abonos_credito ADD COLUMN caja_id INTEGER REFERENCES cajas(id)")

            cur.execute('''
                CREATE TABLE IF NOT EXISTS cotizaciones (
                    id SERIAL PRIMARY KEY,
                    cotizacion INTEGER,
                    cliente TEXT,
                    producto TEXT,
                    precio DOUBLE PRECISION,
                    cantidad INTEGER,
                    total DOUBLE PRECISION,
                    costo DOUBLE PRECISION,
                    fecha TEXT,
                    hora TEXT,
                    cajero TEXT,
                    estado TEXT
                )
            ''')

            # --- Fase 1 del plan de facturación electrónica (ver
            # PLAN_FACTURACION_ELECTRONICA.md): numeración atómica,
            # puntos de venta y configuración fiscal base. ---
            cur.execute('''
                CREATE TABLE IF NOT EXISTS puntos_venta (
                    id SERIAL PRIMARY KEY,
                    codigo VARCHAR(20) NOT NULL UNIQUE,
                    nombre VARCHAR(100) NOT NULL,
                    sucursal_id INTEGER REFERENCES sucursal(id),
                    factrapi_punto_venta_id VARCHAR(50),
                    estado VARCHAR(15) DEFAULT 'Activo' CHECK (estado IN ('Activo', 'Inactivo')),
                    fecha_creacion TIMESTAMP DEFAULT now()
                )
            ''')

            cur.execute('''
                CREATE TABLE IF NOT EXISTS numeracion_local (
                    id SERIAL PRIMARY KEY,
                    documento VARCHAR(30) NOT NULL UNIQUE,
                    siguiente BIGINT NOT NULL DEFAULT 1
                )
            ''')
            cur.execute("SELECT COALESCE(MAX(factura), 0) + 1 FROM ventas")
            siguiente_venta = cur.fetchone()[0]
            cur.execute("SELECT COALESCE(MAX(cotizacion), 0) + 1 FROM cotizaciones")
            siguiente_cotizacion = cur.fetchone()[0]
            cur.execute("SELECT COALESCE(MAX(numero_pedido), 0) + 1 FROM pedidos")
            siguiente_pedido = cur.fetchone()[0]

            cur.execute('''
                INSERT INTO numeracion_local (documento, siguiente) VALUES (?, ?)
                ON CONFLICT (documento) DO NOTHING
            ''', ("ticket_venta", siguiente_venta))
            cur.execute('''
                INSERT INTO numeracion_local (documento, siguiente) VALUES (?, ?)
                ON CONFLICT (documento) DO NOTHING
            ''', ("cotizacion", siguiente_cotizacion))
            cur.execute('''
                INSERT INTO numeracion_local (documento, siguiente) VALUES (?, ?)
                ON CONFLICT (documento) DO NOTHING
            ''', ("pedido", siguiente_pedido))

            cur.execute('''
                CREATE TABLE IF NOT EXISTS secuencias_ncf_tradicional (
                    id SERIAL PRIMARY KEY,
                    tipo_ncf VARCHAR(10) NOT NULL,
                    secuencia_desde BIGINT NOT NULL,
                    secuencia_hasta BIGINT NOT NULL,
                    secuencia_actual BIGINT NOT NULL,
                    fecha_vencimiento TEXT,
                    activa BOOLEAN DEFAULT TRUE,
                    fecha_creacion TIMESTAMP DEFAULT now()
                )
            ''')

            cur.execute('''
                SELECT column_name FROM information_schema.columns
                WHERE table_schema = 'public' AND table_name = 'configuracion_general'
            ''')
            columnas_cg = [c[0] for c in cur.fetchall()]
            columnas_cg_nuevas = {
                "modo_facturacion": "TEXT DEFAULT 'informal'",
                "punto_venta_id": "INTEGER REFERENCES puntos_venta(id)",
                "factrapi_ambiente": "TEXT DEFAULT 'pruebas'",
                "factrapi_url_base": "TEXT",
                "factrapi_api_key": "TEXT",
                "factrapi_empresa_verificada": "BOOLEAN DEFAULT FALSE",
            }
            for columna, definicion in columnas_cg_nuevas.items():
                if columna not in columnas_cg:
                    cur.execute(f"ALTER TABLE configuracion_general ADD COLUMN {columna} {definicion}")

            # --- Fase 2: comprobantes emitidos vía FactrAPI + cola offline. ---
            cur.execute('''
                CREATE TABLE IF NOT EXISTS comprobantes_fiscales (
                    id SERIAL PRIMARY KEY,
                    factura_local INTEGER NOT NULL,
                    factrapi_comprobante_id VARCHAR(50) UNIQUE,
                    tipo_ecf INTEGER NOT NULL,
                    e_ncf VARCHAR(20),
                    estado_actual VARCHAR(20) NOT NULL DEFAULT 'borrador',
                    solicitud_id VARCHAR(50),
                    idempotency_key VARCHAR(100) NOT NULL UNIQUE,
                    ncf_modificado VARCHAR(20),
                    codigo_modificacion INTEGER,
                    punto_venta_id INTEGER REFERENCES puntos_venta(id),
                    payload_enviado JSONB,
                    ultimo_error TEXT,
                    fecha_creacion TIMESTAMP DEFAULT now(),
                    fecha_actualizacion TIMESTAMP DEFAULT now()
                )
            ''')
            cur.execute('''
                CREATE INDEX IF NOT EXISTS idx_comprobantes_fiscales_factura
                ON comprobantes_fiscales (factura_local)
            ''')
            cur.execute('''
                CREATE INDEX IF NOT EXISTS idx_comprobantes_fiscales_estado
                ON comprobantes_fiscales (estado_actual)
            ''')

            cur.execute('''
                CREATE TABLE IF NOT EXISTS secuencias_cache (
                    id SERIAL PRIMARY KEY,
                    factrapi_secuencia_id VARCHAR(50) NOT NULL UNIQUE,
                    tipo_ecf INTEGER NOT NULL,
                    ambiente VARCHAR(20) NOT NULL,
                    secuencia_desde BIGINT NOT NULL,
                    secuencia_hasta BIGINT NOT NULL,
                    secuencia_actual BIGINT NOT NULL,
                    fecha_vencimiento TEXT NOT NULL,
                    activa BOOLEAN DEFAULT TRUE,
                    fecha_actualizacion TIMESTAMP DEFAULT now()
                )
            ''')

            # --- Fase 6: multi-almacén y notas de crédito/débito locales. ---
            cur.execute('''
                CREATE TABLE IF NOT EXISTS almacenes (
                    id SERIAL PRIMARY KEY,
                    nombre VARCHAR(100) NOT NULL,
                    sucursal_id INTEGER REFERENCES sucursal(id),
                    estado VARCHAR(15) DEFAULT 'Activo' CHECK (estado IN ('Activo', 'Inactivo'))
                )
            ''')
            cur.execute('''
                CREATE TABLE IF NOT EXISTS inventario_almacen (
                    id SERIAL PRIMARY KEY,
                    producto_id INTEGER NOT NULL REFERENCES inventario(id) ON DELETE CASCADE,
                    almacen_id INTEGER NOT NULL REFERENCES almacenes(id) ON DELETE CASCADE,
                    stock INTEGER NOT NULL DEFAULT 0,
                    UNIQUE (producto_id, almacen_id)
                )
            ''')
            # Defensa de último nivel en la base: ningún camino SQL externo
            # debe poder dejar existencias o saldos negativos.
            for tabla, columna, nombre_constraint in (
                ("inventario", "stock", "inventario_stock_no_negativo"),
                ("inventario_almacen", "stock", "inventario_almacen_stock_no_negativo"),
                ("cuentas_bancarias", "saldo", "cuentas_bancarias_saldo_no_negativo"),
            ):
                existe = cur.execute(
                    "SELECT 1 FROM pg_constraint WHERE conname = ?",
                    (nombre_constraint,),
                ).fetchone()
                if not existe:
                    cur.execute(
                        f"ALTER TABLE {tabla} ADD CONSTRAINT {nombre_constraint} CHECK ({columna} >= 0)"
                    )
            for tabla in ("ventas", "facturas_pendientes"):
                cur.execute('''
                    SELECT column_name FROM information_schema.columns
                    WHERE table_schema = 'public' AND table_name = ?
                ''', (tabla,))
                columnas_almacen = [c[0] for c in cur.fetchall()]
                if "almacen_id" not in columnas_almacen:
                    cur.execute(f"ALTER TABLE {tabla} ADD COLUMN almacen_id INTEGER REFERENCES almacenes(id)")
            cur.execute('''
                CREATE TABLE IF NOT EXISTS transferencias_almacen (
                    id SERIAL PRIMARY KEY,
                    producto_id INTEGER NOT NULL REFERENCES inventario(id),
                    almacen_origen_id INTEGER NOT NULL REFERENCES almacenes(id),
                    almacen_destino_id INTEGER NOT NULL REFERENCES almacenes(id),
                    cantidad INTEGER NOT NULL,
                    fecha TEXT NOT NULL,
                    hora TEXT NOT NULL,
                    usuario VARCHAR(150)
                )
            ''')
            cur.execute("SELECT id FROM almacenes ORDER BY id LIMIT 1")
            almacen_principal = cur.fetchone()
            if almacen_principal:
                almacen_principal_id = almacen_principal[0]
            else:
                cur.execute("INSERT INTO almacenes (nombre) VALUES ('Almacén Principal') RETURNING id")
                almacen_principal_id = cur.fetchone()[0]
            cur.execute("""
                INSERT INTO inventario_almacen (producto_id, almacen_id, stock)
                SELECT id, ?, stock FROM inventario
                ON CONFLICT (producto_id, almacen_id) DO NOTHING
            """, (almacen_principal_id,))
            cur.execute('''
                SELECT column_name FROM information_schema.columns
                WHERE table_schema = 'public' AND table_name = 'configuracion_general'
            ''')
            columnas_config_final = [c[0] for c in cur.fetchall()]
            if "almacen_id" not in columnas_config_final:
                cur.execute("ALTER TABLE configuracion_general ADD COLUMN almacen_id INTEGER REFERENCES almacenes(id)")
            cur.execute('''
                CREATE TABLE IF NOT EXISTS notas_credito_debito_locales (
                    id SERIAL PRIMARY KEY,
                    tipo VARCHAR(10) NOT NULL CHECK (tipo IN ('Credito', 'Debito')),
                    factura_afectada INTEGER NOT NULL,
                    motivo VARCHAR(255),
                    monto DOUBLE PRECISION NOT NULL,
                    fecha TEXT NOT NULL,
                    hora TEXT NOT NULL,
                    cajero VARCHAR(150)
                )
            ''')
            cur.execute('''
                CREATE TABLE IF NOT EXISTS documentos_fiscales_locales (
                    id SERIAL PRIMARY KEY,
                    factura_local INTEGER NOT NULL UNIQUE,
                    tipo_ncf VARCHAR(10) NOT NULL,
                    ncf VARCHAR(20) NOT NULL UNIQUE,
                    fecha TEXT NOT NULL,
                    cajero VARCHAR(150)
                )
            ''')
            cur.execute('''
                INSERT INTO numeracion_local (documento, siguiente)
                VALUES ('nota_credito_debito', 1)
                ON CONFLICT (documento) DO NOTHING
            ''')

            # --- Fase 2: mapeo con FactrAPI (cliente remoto, clasificación
            # fiscal por producto para indicadorFacturacion del e-CF). ---
            cur.execute('''
                SELECT column_name FROM information_schema.columns
                WHERE table_schema = 'public' AND table_name = 'clientes'
            ''')
            columnas_clientes = [c[0] for c in cur.fetchall()]
            if "factrapi_cliente_id" not in columnas_clientes:
                cur.execute("ALTER TABLE clientes ADD COLUMN factrapi_cliente_id VARCHAR(50)")

            cur.execute('''
                SELECT column_name FROM information_schema.columns
                WHERE table_schema = 'public' AND table_name = 'inventario'
            ''')
            columnas_inventario = [c[0] for c in cur.fetchall()]
            if "indicador_facturacion" not in columnas_inventario:
                # 0 No facturable, 1 Gravado 18%, 2 Gravado 16%, 3 Gravado 0%,
                # 4 Exento (catálogo DGII indicador-facturacion). Por
                # defecto 1 (gravado 18%, el caso más común); el usuario
                # puede marcar productos exentos individualmente.
                cur.execute("ALTER TABLE inventario ADD COLUMN indicador_facturacion INTEGER DEFAULT 1")
            if "codigo_barra" not in columnas_inventario:
                cur.execute("ALTER TABLE inventario ADD COLUMN codigo_barra VARCHAR(80)")
            cur.execute(
                "CREATE UNIQUE INDEX IF NOT EXISTS idx_inventario_codigo_barra "
                "ON inventario (codigo_barra) "
                "WHERE codigo_barra IS NOT NULL AND btrim(codigo_barra) <> ''"
            )

            cur.execute('''
                SELECT column_name FROM information_schema.columns
                WHERE table_schema = 'public' AND table_name = 'cajas'
            ''')
            columnas_cajas = [c[0] for c in cur.fetchall()]
            if "punto_venta_id" not in columnas_cajas:
                cur.execute("ALTER TABLE cajas ADD COLUMN punto_venta_id INTEGER REFERENCES puntos_venta(id)")
            for columna, definicion in {
                "monto_efectivo_esperado": "DOUBLE PRECISION DEFAULT 0",
                "monto_contado": "DOUBLE PRECISION",
                "diferencia_caja": "DOUBLE PRECISION",
            }.items():
                if columna not in columnas_cajas:
                    cur.execute(f"ALTER TABLE cajas ADD COLUMN {columna} {definicion}")
            # El control de apertura también debe existir a nivel de base de
            # datos para evitar dos cajas simultáneas por cajero bajo carreras
            # entre procesos o terminales.
            cur.execute(
                "CREATE UNIQUE INDEX IF NOT EXISTS idx_cajas_cajero_abierta "
                "ON cajas (cajero) WHERE estado = 'Abierta'"
            )
            for tabla in ("ventas", "facturas_pendientes"):
                cur.execute('''
                    SELECT column_name FROM information_schema.columns
                    WHERE table_schema = 'public' AND table_name = ?
                ''', (tabla,))
                columnas_sesion = [c[0] for c in cur.fetchall()]
                if "caja_id" not in columnas_sesion:
                    cur.execute(f"ALTER TABLE {tabla} ADD COLUMN caja_id INTEGER REFERENCES cajas(id)")
            cur.execute('''
                SELECT column_name FROM information_schema.columns
                WHERE table_schema = 'public' AND table_name = 'gastos'
            ''')
            columnas_gastos = [c[0] for c in cur.fetchall()]
            if "caja_id" not in columnas_gastos:
                cur.execute("ALTER TABLE gastos ADD COLUMN caja_id INTEGER REFERENCES cajas(id)")
            for columna, definicion in {
                "anulado": "BOOLEAN NOT NULL DEFAULT FALSE",
                "anulado_por": "VARCHAR(150)",
                "fecha_anulacion": "TIMESTAMP",
            }.items():
                if columna not in columnas_gastos:
                    cur.execute(f"ALTER TABLE gastos ADD COLUMN {columna} {definicion}")
            cur.execute('''
                CREATE TABLE IF NOT EXISTS movimientos_caja (
                    id SERIAL PRIMARY KEY,
                    caja_id INTEGER NOT NULL REFERENCES cajas(id),
                    tipo VARCHAR(10) NOT NULL CHECK (tipo IN ('INGRESO', 'EGRESO')),
                    concepto VARCHAR(255) NOT NULL,
                    monto DOUBLE PRECISION NOT NULL CHECK (monto >= 0),
                    fecha TEXT NOT NULL,
                    hora TEXT NOT NULL,
                    usuario VARCHAR(150)
                )
            ''')
            cur.execute('''
                SELECT column_name FROM information_schema.columns
                WHERE table_schema = 'public' AND table_name = 'movimientos_caja'
            ''')
            columnas_movimientos_caja = [c[0] for c in cur.fetchall()]
            if "medio_pago" not in columnas_movimientos_caja:
                cur.execute("ALTER TABLE movimientos_caja ADD COLUMN medio_pago VARCHAR(30) DEFAULT 'Efectivo'")
            if "cuenta_destino" not in columnas_movimientos_caja:
                cur.execute("ALTER TABLE movimientos_caja ADD COLUMN cuenta_destino VARCHAR(150)")
            cur.execute('''
                CREATE TABLE IF NOT EXISTS movimientos_bancarios (
                    id SERIAL PRIMARY KEY,
                    banco VARCHAR(150) NOT NULL,
                    numero_cuenta VARCHAR(80) NOT NULL,
                    tipo_movimiento VARCHAR(30) NOT NULL,
                    concepto VARCHAR(255) NOT NULL,
                    monto DOUBLE PRECISION NOT NULL CHECK (monto >= 0),
                    fecha TIMESTAMP DEFAULT now(),
                    hora TEXT,
                    usuario VARCHAR(150),
                    saldo DOUBLE PRECISION NOT NULL DEFAULT 0
                )
            ''')
            cur.execute('''
                SELECT column_name FROM information_schema.columns
                WHERE table_schema = 'public' AND table_name = 'movimientos_bancarios'
            ''')
            columnas_movimientos_bancarios = [c[0] for c in cur.fetchall()]
            for columna, definicion in {
                "tipo_movimiento": "VARCHAR(30)",
                "tipo": "VARCHAR(30)",
                "saldo": "DOUBLE PRECISION DEFAULT 0",
                "hora": "TEXT",
                "usuario": "VARCHAR(150)",
            }.items():
                if columna not in columnas_movimientos_bancarios:
                    cur.execute(f"ALTER TABLE movimientos_bancarios ADD COLUMN {columna} {definicion}")
            cur.execute("ALTER TABLE movimientos_bancarios DROP CONSTRAINT IF EXISTS movimientos_bancarios_tipo_movimiento_check")
            cur.execute("""ALTER TABLE movimientos_bancarios
                         ADD CONSTRAINT movimientos_bancarios_tipo_movimiento_check
                         CHECK (tipo_movimiento IN ('Ingreso', 'Egreso', 'Depósito', 'Retiro', 'Transferencia', 'Inicial'))""")
            cur.execute("UPDATE movimientos_bancarios SET tipo_movimiento=tipo WHERE tipo_movimiento IS NULL AND tipo IS NOT NULL")
            cur.execute("UPDATE movimientos_bancarios SET tipo=tipo_movimiento WHERE tipo IS NULL AND tipo_movimiento IS NOT NULL")
            cur.execute('''
                SELECT column_name FROM information_schema.columns
                WHERE table_schema = 'public' AND table_name = 'servicios'
            ''')
            columnas_servicios = [c[0] for c in cur.fetchall()]
            if "tipo_impuesto" not in columnas_servicios:
                cur.execute("ALTER TABLE servicios ADD COLUMN tipo_impuesto VARCHAR(30) DEFAULT 'Exento'")
            cur.execute('''
                CREATE TABLE IF NOT EXISTS pedidos_borradores (
                    id SERIAL PRIMARY KEY,
                    usuario VARCHAR(150),
                    datos JSONB NOT NULL,
                    fecha TIMESTAMP DEFAULT now()
                )
            ''')
            cur.execute('''
                CREATE TABLE IF NOT EXISTS auditoria_eventos (
                    id SERIAL PRIMARY KEY,
                    usuario_id INTEGER REFERENCES usuarios(id),
                    usuario VARCHAR(150),
                    evento VARCHAR(80) NOT NULL,
                    detalle TEXT,
                    fecha TIMESTAMP DEFAULT now()
                )
            ''')
            cur.execute('''
                CREATE TABLE IF NOT EXISTS movimientos_inventario (
                    id SERIAL PRIMARY KEY,
                    producto_id INTEGER NOT NULL REFERENCES inventario(id),
                    almacen_id INTEGER REFERENCES almacenes(id),
                    tipo VARCHAR(20) NOT NULL,
                    cantidad INTEGER NOT NULL CHECK (cantidad > 0),
                    referencia VARCHAR(100),
                    usuario VARCHAR(150),
                    fecha TEXT NOT NULL,
                    hora TEXT NOT NULL
                )
            ''')

            cur.execute("INSERT INTO configuracion_general (id) VALUES (1) ON CONFLICT (id) DO NOTHING")
            cur.execute(
                "CREATE UNIQUE INDEX IF NOT EXISTS idx_cuentas_bancarias_activas "
                "ON cuentas_bancarias (banco, numero_cuenta) "
                "WHERE estado = 'Activo'"
            )
            cur.execute("UPDATE usuarios SET rol = 'Cajero' WHERE rol = 'Vendedor' OR rol IS NULL OR rol = ''")
            # Migrar credenciales heredadas en texto plano antes de permitir
            # el arranque de producción. El login mantiene compatibilidad
            # temporal, pero una base migrada no debe conservar secretos así.
            cur.execute("SELECT id, password FROM usuarios")
            for usuario_id, password_almacenada in cur.fetchall():
                if password_almacenada and not str(password_almacenada).startswith(PREFIJO):
                    cur.execute(
                        "UPDATE usuarios SET password=? WHERE id=?",
                        (hash_password(str(password_almacenada)), usuario_id),
                    )
            duplicados_usuario = cur.execute(
                "SELECT COUNT(*) FROM (SELECT LOWER(username) FROM usuarios "
                "GROUP BY LOWER(username) HAVING COUNT(*) > 1) AS duplicados"
            ).fetchone()[0]
            if not duplicados_usuario:
                cur.execute(
                    "CREATE UNIQUE INDEX IF NOT EXISTS idx_usuarios_username_ci "
                    "ON usuarios (LOWER(username))"
                )
            cur.execute("""
                UPDATE configuracion_general SET almacen_id = COALESCE(almacen_id, ?)
                WHERE id = 1
            """, (almacen_principal_id,))

            conn.commit()
            return True
    except Exception as e:
        print("Error migrando base de datos:", e)
        return False

try:
    import ctypes
    myappid = 'vainacode.pos.version.4.4.7'
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
except Exception:
    pass

class Manager(Tk):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.title("La Casa de los Repuestos - Punto de Venta v4.4.7")
        self.resizable(False, False)
        self.configure(bg="#C6D9E3")
        posicionar_ventana(self, 1100, 650)

        self.set_app_icon()
        if not migrar_base_datos():
            from tkinter import messagebox
            messagebox.showerror(
                "No se pudo iniciar",
                "No fue posible conectar con la base de datos. Verifique la configuración "
                "de PostgreSQL y las variables de entorno."
            )
            self.destroy()
            return
        try:
            preparar_permisos()
        except Exception as error:
            # Sin la tabla de permisos no se puede garantizar el aislamiento
            # de un cajero. El arranque se detiene para no operar inseguro.
            messagebox.showerror("No se pudo iniciar", f"No fue posible preparar los permisos: {error}")
            self.destroy()
            return

        # El tema debe estar listo antes de crear los widgets ttk. Si se aplica
        # después, cambia el padding interno de los Entry y el texto queda
        # recortado cuando el control tiene una altura fija.
        self.set_theme()
        # Los módulos usan ttk.Entry directamente. Registrar esta variante
        # permite corregir también los formularios que se abren más adelante.
        ttk.Entry = EntrySeguro

        self.container = Frame(self, bg="#C6D9E3")
        self.container.pack(fill="both", expand=True)

        self.frames = {
            Login: None,
            Registro: None,
            Container: None
        }
        
        self.load_frames()

        self.show_frame(Login)

    def load_frames(self):
        for FrameClass in self.frames.keys():
            frame = FrameClass(self.container, self)
            self.frames[FrameClass] = frame

    def show_frame(self, frame_class):
        frame = self.frames[frame_class]
        self.title("La Casa de los Repuestos - Punto de Venta v4.4.7")
        frame.tkraise()
        if hasattr(frame, 'enfocar_usuario'):
            self.after(50, frame.enfocar_usuario)

    def set_theme(self):
        style = ThemedStyle(self)
        style.set_theme("breeze")
        # Reservar espacio vertical suficiente para que los caracteres no
        # choquen con el borde inferior en ninguna pantalla.
        style.configure("TEntry", padding=(6, 0))

    def rutas(self, ruta):
        try:
            rutabase = sys.__MEIPASS
        except Exception:
            rutabase = os.path.abspath(".")
        return os.path.join(rutabase, ruta)

    def set_app_icon(self):
        ruta_ico = self.rutas("icono.ico")
        if os.path.exists(ruta_ico):
            try:
                self.iconbitmap(ruta_ico)
            except Exception:
                pass

def main():
    app = Manager()
    app.mainloop()

if __name__ == "__main__":
    main()
