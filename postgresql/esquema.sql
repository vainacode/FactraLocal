-- =====================================================================
-- ESQUEMA POSTGRESQL - PUNTO DE VENTA "LA CASA DE LOS REPUESTOS"
-- Base de datos: factra_db
-- Migracion desde la base SQLite (database.db) del sistema.
-- =====================================================================
-- Este script se ejecuta DENTRO de la base de datos factra_db, ya
-- creada previamente con:
--   CREATE DATABASE factra_db WITH OWNER = pos_app ENCODING = 'UTF8' TEMPLATE = template1;

-- El usuario de la aplicación debe ser propietario del esquema/tablas o
-- recibir permisos explícitos sobre auditoria_eventos y su secuencia. La
-- auditoría es obligatoria para accesos, anulaciones y cambios sensibles.
--
-- Para aplicarlo:
--   psql -U postgres -h localhost -d factra_db -f esquema.sql
-- =====================================================================

BEGIN;

-- ---------------------------------------------------------------------
-- 1. USUARIOS Y SEGURIDAD
-- ---------------------------------------------------------------------

CREATE TABLE usuarios (
    id          SERIAL PRIMARY KEY,
    username    VARCHAR(50)  NOT NULL UNIQUE,
    password    VARCHAR(255) NOT NULL,
    rol         VARCHAR(30)  NOT NULL DEFAULT 'Cajero',
    nombre      VARCHAR(150),
    telefono    VARCHAR(20),
    estado      VARCHAR(15)  NOT NULL DEFAULT 'Activo'
                CHECK (estado IN ('Activo', 'Inactivo'))
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_usuarios_username_ci
    ON usuarios (LOWER(username));

CREATE TABLE roles (
    id      SERIAL PRIMARY KEY,
    nombre  VARCHAR(50) NOT NULL UNIQUE
);

CREATE TABLE permisos (
    id      SERIAL PRIMARY KEY,
    modulo  VARCHAR(80) NOT NULL UNIQUE
);

CREATE TABLE permisos_rol (
    id_rol      INTEGER NOT NULL REFERENCES roles(id)    ON DELETE CASCADE,
    id_permiso  INTEGER NOT NULL REFERENCES permisos(id) ON DELETE CASCADE,
    PRIMARY KEY (id_rol, id_permiso)
);

-- ---------------------------------------------------------------------
-- 2. EMPRESA, SUCURSALES Y CONFIGURACION GENERAL
-- ---------------------------------------------------------------------

CREATE TABLE empresa (
    id          SERIAL PRIMARY KEY,
    nombre      VARCHAR(150),
    direccion   VARCHAR(255),
    telefono    VARCHAR(20),
    email       VARCHAR(120),
    website     VARCHAR(150),
    image_path  TEXT,
    tipo_id     VARCHAR(20),
    numero_id   VARCHAR(30),
    nit         VARCHAR(30),
    ciudad      VARCHAR(100)
);

CREATE TABLE sucursal (
    id          SERIAL PRIMARY KEY,
    nombre      VARCHAR(150) NOT NULL,
    direccion   VARCHAR(255),
    telefono    VARCHAR(20),
    encargado   VARCHAR(150),
    estado      VARCHAR(15) DEFAULT 'Activo'
                CHECK (estado IN ('Activo', 'Inactivo'))
);

CREATE TABLE moneda (
    id       SERIAL PRIMARY KEY,
    nombre   VARCHAR(50),
    simbolo  VARCHAR(5) DEFAULT '$',
    codigo   VARCHAR(10)
);

CREATE TABLE impuestos (
    id           SERIAL PRIMARY KEY,
    nombre       VARCHAR(80) NOT NULL,
    porcentaje   DOUBLE PRECISION NOT NULL DEFAULT 0,
    estado       VARCHAR(15) DEFAULT 'Activo'
                 CHECK (estado IN ('Activo', 'Inactivo'))
);

CREATE TABLE info_factura (
    id                      SERIAL PRIMARY KEY,
    factura_a4              VARCHAR(150) DEFAULT 'Factura de Venta',
    texto_cliente           VARCHAR(150) DEFAULT 'Cliente',
    texto_factura           VARCHAR(150) DEFAULT 'Numero de Factura',
    texto_fecha             VARCHAR(150) DEFAULT 'Fecha',
    texto_cajero            VARCHAR(150) DEFAULT 'Cajero',
    texto_agradecimiento    TEXT DEFAULT 'Gracias por tu compra, vuelve pronto!',
    texto_informacion       TEXT DEFAULT 'Para mas informacion, visite nuestro sitio web o siganos en nuestras redes sociales',
    texto_copyright         TEXT DEFAULT 'Software creado por Kevin Arboleda / InnovaSoft Code @ 2024',
    mostrar_cliente         BOOLEAN DEFAULT FALSE,
    mostrar_factura         BOOLEAN DEFAULT FALSE,
    mostrar_fecha           BOOLEAN DEFAULT FALSE,
    mostrar_cajero          BOOLEAN DEFAULT FALSE,
    mostrar_agradecimiento  BOOLEAN DEFAULT FALSE,
    mostrar_informacion     BOOLEAN DEFAULT FALSE,
    mostrar_copyright       BOOLEAN DEFAULT FALSE
);

-- ---------------------------------------------------------------------
-- 3. CLIENTES Y PROVEEDORES
-- ---------------------------------------------------------------------

-- Nota: "cedula" NO es única a propósito. La pantalla de Clientes siembra
-- registros de muestra la primera vez que se abre usando "-" como
-- marcador para varios clientes sin identificación real.
CREATE TABLE clientes (
    id          SERIAL PRIMARY KEY,
    nombre      VARCHAR(150) NOT NULL,
    cedula      VARCHAR(30)  NOT NULL,
    celular     VARCHAR(20)  NOT NULL,
    direccion   VARCHAR(255) NOT NULL,
    correo      VARCHAR(120) NOT NULL,
    tipo_id     VARCHAR(20),
    estado      VARCHAR(15) NOT NULL DEFAULT 'Activo'
                CHECK (estado IN ('Activo', 'Inactivo'))
);

CREATE TABLE cliente_defecto (
    id              SMALLINT PRIMARY KEY DEFAULT 1 CHECK (id = 1),
    cliente_nombre  VARCHAR(150) NOT NULL,
    cliente_cedula  VARCHAR(30)  NOT NULL
);

CREATE TABLE proveedores (
    id          SERIAL PRIMARY KEY,
    nombre      VARCHAR(150) NOT NULL,
    nit         VARCHAR(30),
    telefono    VARCHAR(20),
    contacto    VARCHAR(150),
    email       VARCHAR(120),
    direccion   VARCHAR(255),
    ciudad      VARCHAR(100),
    estado      VARCHAR(15) DEFAULT 'Activo'
                CHECK (estado IN ('Activo', 'Inactivo'))
);

-- ---------------------------------------------------------------------
-- 4. CATALOGO: CATEGORIAS, INVENTARIO, SERVICIOS, COMBOS, PROMOCIONES
-- ---------------------------------------------------------------------

CREATE TABLE categorias (
    id           SERIAL PRIMARY KEY,
    nombre       VARCHAR(100) NOT NULL UNIQUE,
    descripcion  TEXT
);

CREATE TABLE inventario (
    id          SERIAL PRIMARY KEY,
    nombre      VARCHAR(200) NOT NULL,
    proveedor   VARCHAR(150) NOT NULL,
    precio      DOUBLE PRECISION NOT NULL DEFAULT 0,
    costo       DOUBLE PRECISION NOT NULL DEFAULT 0,
    stock       INTEGER NOT NULL DEFAULT 0 CHECK (stock >= 0),
    categoria   VARCHAR(100),
    sucursal    VARCHAR(150),
    codigo_barra VARCHAR(80),
    image_path  TEXT,
    estado      VARCHAR(15) NOT NULL DEFAULT 'Activo'
                CHECK (estado IN ('Activo', 'Inactivo'))
);
CREATE INDEX idx_inventario_nombre ON inventario (nombre);
CREATE INDEX idx_inventario_categoria ON inventario (categoria);
CREATE UNIQUE INDEX IF NOT EXISTS idx_inventario_codigo_barra
    ON inventario (codigo_barra)
    WHERE codigo_barra IS NOT NULL AND btrim(codigo_barra) <> '';

-- Configuración global de impuestos (IVA) y margen de utilidad sugerido
-- (una sola fila; pantalla "Impuestos" en Configuración).
CREATE TABLE configuracion_general (
    id                        SMALLINT PRIMARY KEY DEFAULT 1 CHECK (id = 1),
    nombre_impuesto           VARCHAR(50) DEFAULT 'IVA',
    porcentaje_impuesto       DOUBLE PRECISION DEFAULT 0,
    precios_incluyen_impuesto BOOLEAN DEFAULT TRUE,
    desglosar_impuesto        BOOLEAN DEFAULT TRUE,
    margen_utilidad_defecto   DOUBLE PRECISION DEFAULT 30
);

CREATE TABLE stock_minimo (
    id           SERIAL PRIMARY KEY,
    id_producto  INTEGER NOT NULL UNIQUE REFERENCES inventario(id) ON DELETE CASCADE,
    stock_minimo INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE historial_precios (
    id               SERIAL PRIMARY KEY,
    id_producto      INTEGER NOT NULL REFERENCES inventario(id) ON DELETE CASCADE,
    nombre_producto  VARCHAR(200) NOT NULL,
    precio_anterior  DOUBLE PRECISION,
    precio_nuevo     DOUBLE PRECISION NOT NULL,
    costo_anterior   DOUBLE PRECISION,
    costo_nuevo      DOUBLE PRECISION NOT NULL,
    stock_anterior   INTEGER,
    stock_nuevo      INTEGER NOT NULL,
    fecha            TEXT NOT NULL,
    hora             TEXT NOT NULL,
    usuario          VARCHAR(150) NOT NULL,
    motivo           VARCHAR(255) NOT NULL,
    numero_pedido    INTEGER
);
CREATE INDEX idx_historial_precios_producto ON historial_precios (id_producto);

CREATE TABLE bajas_productos (
    id            SERIAL PRIMARY KEY,
    producto      VARCHAR(200) NOT NULL,
    cantidad      INTEGER NOT NULL,
    motivo        VARCHAR(255),
    fecha         TEXT NOT NULL,
    responsable   VARCHAR(150),
    observaciones TEXT
);

CREATE TABLE servicios (
    id               SERIAL PRIMARY KEY,
    nombre           VARCHAR(200) NOT NULL,
    precio           DOUBLE PRECISION NOT NULL DEFAULT 0,
    costo            DOUBLE PRECISION NOT NULL DEFAULT 0,
    descripcion      TEXT,
    tipo_impuesto    VARCHAR(30) DEFAULT 'Exento',
    estado           VARCHAR(15) DEFAULT 'Activo'
                     CHECK (estado IN ('Activo', 'Inactivo')),
    fecha_creacion   TEXT
);

CREATE TABLE combos (
    id            SERIAL PRIMARY KEY,
    nombre        VARCHAR(200) NOT NULL,
    precio_venta  DOUBLE PRECISION NOT NULL,
    costo_total   DOUBLE PRECISION NOT NULL,
    estado        VARCHAR(15) DEFAULT 'Activo'
                  CHECK (estado IN ('Activo', 'Inactivo'))
);

CREATE TABLE combo_detalle (
    id                SERIAL PRIMARY KEY,
    combo_id          INTEGER NOT NULL REFERENCES combos(id)    ON DELETE CASCADE,
    producto_id       INTEGER NOT NULL REFERENCES inventario(id) ON DELETE RESTRICT,
    producto_nombre   VARCHAR(200) NOT NULL,
    cantidad          INTEGER NOT NULL,
    costo_unitario    DOUBLE PRECISION NOT NULL
);
CREATE INDEX idx_combo_detalle_combo ON combo_detalle (combo_id);

-- Reglas de descuento por promoción (% o valor fijo, con vigencia).
CREATE TABLE promociones (
    id             SERIAL PRIMARY KEY,
    nombre         VARCHAR(200) NOT NULL,
    tipo           VARCHAR(20)  NOT NULL DEFAULT 'Porcentaje (%)'
                   CHECK (tipo IN ('Porcentaje (%)', 'Valor Fijo ($)')),
    descuento      DOUBLE PRECISION NOT NULL,
    fecha_inicio   TEXT,
    fecha_fin      TEXT,
    estado         VARCHAR(15) DEFAULT 'Activa'
                   CHECK (estado IN ('Activa', 'Inactiva'))
);

-- ---------------------------------------------------------------------
-- 5. CAJA Y CUENTAS BANCARIAS
-- ---------------------------------------------------------------------

-- Debe existir antes de cajas y ventas, que mantienen una referencia a él.
CREATE TABLE IF NOT EXISTS puntos_venta (
    id INTEGER GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
    codigo VARCHAR(20) NOT NULL UNIQUE,
    nombre VARCHAR(100) NOT NULL,
    sucursal_id INTEGER REFERENCES sucursal(id),
    factrapi_punto_venta_id VARCHAR(50),
    estado VARCHAR(15) DEFAULT 'Activo' CHECK (estado IN ('Activo', 'Inactivo')),
    fecha_creacion TIMESTAMP DEFAULT now()
);

CREATE TABLE cajas (
    id              SERIAL PRIMARY KEY,
    fecha_apertura  TEXT NOT NULL,
    hora_apertura   TEXT NOT NULL,
    monto_inicial   DOUBLE PRECISION NOT NULL DEFAULT 0,
    cajero          VARCHAR(150) NOT NULL,
    fecha_cierre    TEXT,
    hora_cierre     TEXT,
    monto_final     DOUBLE PRECISION,
    total_ventas    DOUBLE PRECISION DEFAULT 0,
    estado          VARCHAR(15) NOT NULL DEFAULT 'Abierta'
                    CHECK (estado IN ('Abierta', 'Cerrada')),
    observaciones   TEXT,
    punto_venta_id  INTEGER REFERENCES puntos_venta(id),
    monto_efectivo_esperado DOUBLE PRECISION DEFAULT 0,
    monto_contado   DOUBLE PRECISION,
    diferencia_caja DOUBLE PRECISION
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_cajas_cajero_abierta
    ON cajas (cajero) WHERE estado = 'Abierta';
CREATE INDEX idx_cajas_estado ON cajas (estado);

CREATE TABLE movimientos_caja (
    id              SERIAL PRIMARY KEY,
    caja_id         INTEGER NOT NULL REFERENCES cajas(id),
    tipo            VARCHAR(10) NOT NULL CHECK (tipo IN ('INGRESO', 'EGRESO')),
    concepto        VARCHAR(255) NOT NULL,
    monto           DOUBLE PRECISION NOT NULL CHECK (monto >= 0),
    fecha           TEXT NOT NULL,
    hora            TEXT NOT NULL,
    usuario         VARCHAR(150),
    medio_pago      VARCHAR(30) DEFAULT 'Efectivo',
    cuenta_destino  VARCHAR(150)
);
CREATE INDEX idx_movimientos_caja_caja ON movimientos_caja (caja_id);

CREATE TABLE cuentas_bancarias (
    id              SERIAL PRIMARY KEY,
    banco           VARCHAR(150) NOT NULL,
    numero_cuenta   VARCHAR(50)  NOT NULL,
    tipo            VARCHAR(30),
    saldo           DOUBLE PRECISION NOT NULL DEFAULT 0 CHECK (saldo >= 0),
    estado          VARCHAR(15) DEFAULT 'Activo'
                    CHECK (estado IN ('Activo', 'Inactivo'))
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_cuentas_bancarias_activas
    ON cuentas_bancarias (banco, numero_cuenta)
    WHERE estado = 'Activo';

CREATE TABLE movimientos_bancarios (
    id               SERIAL PRIMARY KEY,
    cuenta_id        INTEGER REFERENCES cuentas_bancarias(id) ON DELETE SET NULL,
    banco            VARCHAR(150),
    numero_cuenta    VARCHAR(50),
    tipo_movimiento  VARCHAR(20) CHECK (tipo_movimiento IN ('Ingreso', 'Egreso', 'Depósito', 'Retiro', 'Transferencia', 'Inicial')),
    concepto         VARCHAR(255),
    monto            DOUBLE PRECISION NOT NULL,
    fecha            TEXT NOT NULL,
    hora             TEXT NOT NULL,
    usuario          VARCHAR(150),
    saldo            DOUBLE PRECISION NOT NULL DEFAULT 0,
    tipo             VARCHAR(30)
);
CREATE INDEX idx_movimientos_bancarios_cuenta ON movimientos_bancarios (cuenta_id);
CREATE INDEX idx_movimientos_bancarios_fecha ON movimientos_bancarios (fecha);

-- ---------------------------------------------------------------------
-- 6. VENTAS, FACTURAS PENDIENTES Y FACTURAS ANULADAS
-- ---------------------------------------------------------------------
-- Nota: cada renglon representa UNA linea de producto dentro de una
-- factura (varias filas comparten el mismo numero de "factura"),
-- igual que en la base SQLite original.

CREATE TABLE ventas (
    id          SERIAL PRIMARY KEY,
    factura     INTEGER NOT NULL,
    cliente     VARCHAR(150) NOT NULL,
    producto    VARCHAR(200) NOT NULL,
    precio      DOUBLE PRECISION NOT NULL,
    cantidad    INTEGER NOT NULL,
    total       DOUBLE PRECISION NOT NULL,
    fecha       TEXT NOT NULL,
    hora        TEXT NOT NULL,
    costo       DOUBLE PRECISION NOT NULL,
    cajero      VARCHAR(150),
    medio_pago  VARCHAR(30) DEFAULT 'Efectivo'
                CHECK (medio_pago IN ('Efectivo', 'Tarjeta de Débito', 'Tarjeta de Crédito', 'Transferencia', 'Pago Mixto'))
);
CREATE INDEX idx_ventas_factura ON ventas (factura);
CREATE INDEX idx_ventas_fecha ON ventas (fecha);
CREATE INDEX idx_ventas_cliente ON ventas (cliente);

CREATE TABLE facturas_pendientes (
    id               SERIAL PRIMARY KEY,
    factura          INTEGER NOT NULL,
    cliente          VARCHAR(150) NOT NULL,
    producto         VARCHAR(200) NOT NULL,
    precio           DOUBLE PRECISION NOT NULL,
    cantidad         INTEGER NOT NULL,
    total            DOUBLE PRECISION NOT NULL,
    costo            DOUBLE PRECISION NOT NULL,
    fecha_creacion   TEXT NOT NULL,
    hora_creacion    TEXT NOT NULL,
    cajero           VARCHAR(150),
    estado           VARCHAR(15) NOT NULL DEFAULT 'Pendiente'
                     CHECK (estado IN ('Pendiente', 'Crédito', 'Pagada')),
    medio_pago       VARCHAR(30)
);
CREATE INDEX idx_facturas_pendientes_factura ON facturas_pendientes (factura);
CREATE INDEX idx_facturas_pendientes_estado ON facturas_pendientes (estado);

CREATE TABLE facturas_anuladas (
    id          SERIAL PRIMARY KEY,
    factura     INTEGER NOT NULL,
    cliente     VARCHAR(150),
    producto    VARCHAR(200),
    precio      DOUBLE PRECISION,
    cantidad    INTEGER,
    total       DOUBLE PRECISION,
    fecha       TEXT,
    hora        TEXT,
    costo       DOUBLE PRECISION,
    cajero      VARCHAR(150),
    medio_pago  VARCHAR(30) DEFAULT 'Efectivo',
    anulo       VARCHAR(150)
);
CREATE INDEX idx_facturas_anuladas_factura ON facturas_anuladas (factura);

CREATE TABLE descuentos_ventas (
    id                     SERIAL PRIMARY KEY,
    factura                INTEGER NOT NULL,
    tipo_descuento         VARCHAR(20) NOT NULL CHECK (tipo_descuento IN ('Porcentaje', 'Monto Fijo')),
    valor_ingresado        DOUBLE PRECISION NOT NULL,
    monto_descuento        DOUBLE PRECISION NOT NULL,
    total_original         DOUBLE PRECISION NOT NULL,
    total_con_descuento    DOUBLE PRECISION NOT NULL,
    fecha                  TEXT NOT NULL,
    hora                   TEXT NOT NULL,
    cajero                 VARCHAR(150) NOT NULL
);
CREATE INDEX idx_descuentos_ventas_factura ON descuentos_ventas (factura);

CREATE TABLE nota_ventas (
    id           SERIAL PRIMARY KEY,
    factura      INTEGER NOT NULL,
    observacion  TEXT
);

-- ---------------------------------------------------------------------
-- 7. COTIZACIONES
-- ---------------------------------------------------------------------

CREATE TABLE cotizaciones (
    id           SERIAL PRIMARY KEY,
    cotizacion   INTEGER NOT NULL,
    cliente      VARCHAR(150),
    producto     VARCHAR(200),
    precio       DOUBLE PRECISION,
    cantidad     INTEGER,
    total        DOUBLE PRECISION,
    costo        DOUBLE PRECISION,
    fecha        TEXT,
    hora         TEXT,
    cajero       VARCHAR(150),
    estado       VARCHAR(15) DEFAULT 'Pendiente'
                 CHECK (estado IN ('Pendiente', 'Registrada'))
);
CREATE INDEX idx_cotizaciones_numero ON cotizaciones (cotizacion);

-- ---------------------------------------------------------------------
-- 8. CUENTAS POR COBRAR (ABONOS A VENTAS A CREDITO)
-- ---------------------------------------------------------------------

CREATE TABLE abonos_credito (
    id               SERIAL PRIMARY KEY,
    factura          INTEGER NOT NULL,
    cliente          VARCHAR(150),
    monto            DOUBLE PRECISION NOT NULL CHECK (monto > 0),
    fecha            TEXT NOT NULL,
    hora             TEXT NOT NULL,
    cajero           VARCHAR(150),
    metodo_pago      VARCHAR(30),
    cuenta_destino   VARCHAR(150),
    caja_id          INTEGER REFERENCES cajas(id)
);
CREATE INDEX idx_abonos_credito_factura ON abonos_credito (factura);

-- ---------------------------------------------------------------------
-- 9. COMPRAS / PEDIDOS A PROVEEDORES
-- ---------------------------------------------------------------------

CREATE TABLE pedidos (
    id              SERIAL PRIMARY KEY,
    numero_pedido   INTEGER NOT NULL,
    proveedor       VARCHAR(150) NOT NULL,
    producto        VARCHAR(200) NOT NULL,
    cantidad        INTEGER NOT NULL,
    fecha           TEXT NOT NULL,
    hora            TEXT NOT NULL,
    precio          DOUBLE PRECISION DEFAULT 0,
    costo           DOUBLE PRECISION DEFAULT 0
);
CREATE INDEX idx_pedidos_numero ON pedidos (numero_pedido);

CREATE TABLE pedidos_anulados (
    id              SERIAL PRIMARY KEY,
    numero_pedido   INTEGER,
    proveedor       VARCHAR(150),
    producto        VARCHAR(200),
    cantidad        INTEGER,
    fecha           TEXT,
    hora            TEXT,
    precio          DOUBLE PRECISION DEFAULT 0,
    costo           DOUBLE PRECISION DEFAULT 0,
    usuario         VARCHAR(150),
    motivo          VARCHAR(255)
);

-- ---------------------------------------------------------------------
-- 10. GASTOS
-- ---------------------------------------------------------------------

CREATE TABLE gastos (
    id        SERIAL PRIMARY KEY,
    concepto  VARCHAR(200) NOT NULL,
    monto     DOUBLE PRECISION NOT NULL,
    valor     DOUBLE PRECISION,
    entidad   VARCHAR(150),
    fecha     TEXT NOT NULL,
    origen    VARCHAR(50)
);
CREATE INDEX idx_gastos_fecha ON gastos (fecha);

-- ---------------------------------------------------------------------
-- 11. OPERACIÓN MULTI-PUNTO, INVENTARIO Y AUDITORÍA
-- ---------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS puntos_venta (
    id INTEGER GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
    codigo VARCHAR(20) NOT NULL UNIQUE,
    nombre VARCHAR(100) NOT NULL,
    sucursal_id INTEGER REFERENCES sucursal(id),
    factrapi_punto_venta_id VARCHAR(50),
    estado VARCHAR(15) DEFAULT 'Activo' CHECK (estado IN ('Activo', 'Inactivo')),
    fecha_creacion TIMESTAMP DEFAULT now()
);

CREATE TABLE IF NOT EXISTS almacenes (
    id INTEGER GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    sucursal_id INTEGER REFERENCES sucursal(id),
    estado VARCHAR(15) DEFAULT 'Activo' CHECK (estado IN ('Activo', 'Inactivo'))
);

CREATE TABLE IF NOT EXISTS inventario_almacen (
    id INTEGER GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
    producto_id INTEGER NOT NULL REFERENCES inventario(id) ON DELETE CASCADE,
    almacen_id INTEGER NOT NULL REFERENCES almacenes(id) ON DELETE CASCADE,
    stock INTEGER NOT NULL DEFAULT 0 CHECK (stock >= 0),
    UNIQUE (producto_id, almacen_id)
);

CREATE TABLE IF NOT EXISTS transferencias_almacen (
    id INTEGER GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
    producto_id INTEGER NOT NULL REFERENCES inventario(id),
    almacen_origen_id INTEGER NOT NULL REFERENCES almacenes(id),
    almacen_destino_id INTEGER NOT NULL REFERENCES almacenes(id),
    cantidad INTEGER NOT NULL CHECK (cantidad > 0),
    fecha TEXT NOT NULL,
    hora TEXT NOT NULL,
    usuario VARCHAR(150)
);

CREATE TABLE IF NOT EXISTS movimientos_inventario (
    id INTEGER GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
    producto_id INTEGER NOT NULL REFERENCES inventario(id),
    almacen_id INTEGER REFERENCES almacenes(id),
    tipo VARCHAR(20) NOT NULL,
    cantidad INTEGER NOT NULL CHECK (cantidad > 0),
    referencia VARCHAR(100),
    usuario VARCHAR(150),
    fecha TEXT NOT NULL,
    hora TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS numeracion_local (
    id INTEGER GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
    documento VARCHAR(30) NOT NULL UNIQUE,
    siguiente BIGINT NOT NULL DEFAULT 1 CHECK (siguiente > 0)
);

CREATE TABLE IF NOT EXISTS secuencias_ncf_tradicional (
    id INTEGER GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
    tipo_ncf VARCHAR(10) NOT NULL,
    secuencia_desde BIGINT NOT NULL,
    secuencia_hasta BIGINT NOT NULL,
    secuencia_actual BIGINT NOT NULL,
    fecha_vencimiento TEXT,
    activa BOOLEAN DEFAULT TRUE,
    fecha_creacion TIMESTAMP DEFAULT now()
);

CREATE TABLE IF NOT EXISTS comprobantes_fiscales (
    id INTEGER GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
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
);
CREATE INDEX IF NOT EXISTS idx_comprobantes_fiscales_factura ON comprobantes_fiscales (factura_local);
CREATE INDEX IF NOT EXISTS idx_comprobantes_fiscales_estado ON comprobantes_fiscales (estado_actual);

CREATE TABLE IF NOT EXISTS secuencias_cache (
    id INTEGER GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
    factrapi_secuencia_id VARCHAR(50) NOT NULL UNIQUE,
    tipo_ecf INTEGER NOT NULL,
    ambiente VARCHAR(20) NOT NULL,
    secuencia_desde BIGINT NOT NULL,
    secuencia_hasta BIGINT NOT NULL,
    secuencia_actual BIGINT NOT NULL,
    fecha_vencimiento TEXT NOT NULL,
    activa BOOLEAN DEFAULT TRUE,
    fecha_actualizacion TIMESTAMP DEFAULT now()
);

CREATE TABLE IF NOT EXISTS roles_permisos (
    id INTEGER GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
    rol VARCHAR(50) NOT NULL,
    modulo VARCHAR(100) NOT NULL,
    permitido BOOLEAN NOT NULL DEFAULT FALSE,
    UNIQUE (rol, modulo)
);

CREATE TABLE IF NOT EXISTS notas_credito_debito_locales (
    id INTEGER GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
    tipo VARCHAR(10) NOT NULL CHECK (tipo IN ('Credito', 'Debito')),
    factura_afectada INTEGER NOT NULL,
    motivo VARCHAR(255),
    monto DOUBLE PRECISION NOT NULL CHECK (monto >= 0),
    fecha TEXT NOT NULL,
    hora TEXT NOT NULL,
    cajero VARCHAR(150)
);

CREATE TABLE IF NOT EXISTS documentos_fiscales_locales (
    id INTEGER GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
    factura_local INTEGER NOT NULL UNIQUE,
    tipo_ncf VARCHAR(10) NOT NULL,
    ncf VARCHAR(20) NOT NULL UNIQUE,
    fecha TEXT NOT NULL,
    cajero VARCHAR(150)
);

CREATE TABLE IF NOT EXISTS pedidos_borradores (
    id INTEGER GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
    usuario VARCHAR(150),
    datos JSONB NOT NULL,
    fecha TIMESTAMP DEFAULT now()
);

CREATE TABLE IF NOT EXISTS auditoria_eventos (
    id INTEGER GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
    usuario_id INTEGER REFERENCES usuarios(id),
    usuario VARCHAR(150),
    evento VARCHAR(80) NOT NULL,
    detalle TEXT,
    fecha TIMESTAMP DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_auditoria_eventos_fecha
    ON auditoria_eventos (fecha);

COMMIT;
