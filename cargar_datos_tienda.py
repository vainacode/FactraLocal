"""Reinicia y carga los datos iniciales de La Tienda de los Repuestos.

Uso intencional: este archivo borra todos los registros de la base conectada.
"""
import datetime
import os
import db_conexion
from seguridad import hash_password


def columnas(cur, tabla):
    cur.execute(
        "SELECT column_name FROM information_schema.columns "
        "WHERE table_schema='public' AND table_name=?",
        (tabla,),
    )
    return {fila[0] for fila in cur.fetchall()}


def insertar(cur, tabla, datos):
    disponibles = columnas(cur, tabla)
    datos = {clave: valor for clave, valor in datos.items() if clave in disponibles}
    if not datos:
        return None
    nombres = list(datos)
    marcadores = ", ".join("?" for _ in nombres)
    if "id" in disponibles:
        cur.execute(
            f'INSERT INTO "{tabla}" ({", ".join(nombres)}) VALUES ({marcadores}) RETURNING id',
            tuple(datos[nombre] for nombre in nombres),
        )
        fila = cur.fetchone()
        return fila[0] if fila else None
    cur.execute(
        f'INSERT INTO "{tabla}" ({", ".join(nombres)}) VALUES ({marcadores})',
        tuple(datos[nombre] for nombre in nombres),
    )
    return None


def cargar():
    ahora = datetime.datetime.now()
    fecha = ahora.strftime("%Y-%m-%d")
    hora = ahora.strftime("%H:%M:%S")
    with db_conexion.connect() as conn:
        cur = conn.cursor()
        # El truncado requiere ser propietario de todas las tablas. En la
        # instalación actual lo ejecuta previamente el administrador de BD.
        if os.getenv("POS_SEED_ALREADY_CLEARED") != "1":
            raise RuntimeError("Ejecute primero el vaciado administrativo de la base de datos.")

        # Seguridad y permisos.
        roles = {}
        for nombre in ("Administrador", "Supervisor", "Cajero"):
            roles[nombre] = insertar(cur, "roles", {"nombre": nombre})
        modulos = ("Ventas", "Cotizaciones", "Inventario", "Clientes", "Proveedor", "Compras", "Cobros", "Reportes", "Configuración", "Gastos", "Usuarios", "Gestión Caja")
        permisos = {modulo: insertar(cur, "permisos", {"modulo": modulo}) for modulo in modulos}
        permitidos = {
            "Administrador": set(modulos),
            "Supervisor": {"Ventas", "Cotizaciones", "Inventario", "Clientes", "Proveedor", "Compras", "Cobros", "Reportes", "Gastos", "Gestión Caja"},
            "Cajero": {"Ventas", "Cotizaciones", "Clientes", "Cobros", "Gestión Caja"},
        }
        for rol, modulos_rol in permitidos.items():
            for modulo in modulos:
                insertar(cur, "permisos_rol", {"id_rol": roles[rol], "id_permiso": permisos[modulo]})
                insertar(cur, "roles_permisos", {"rol": rol, "modulo": modulo, "permitido": modulo in modulos_rol})

        empresa_id = insertar(cur, "empresa", {
            "nombre": "La Tienda de los Repuestos",
            "direccion": "Calle Duarte, Montecristi, República Dominicana",
            "telefono": "809-000-0000",
            "email": "info@latiendadelosrepuestos.com",
            "website": "",
            "tipo_id": "RNC",
            "numero_id": "40233658695",
            "nit": "40233658695",
            "ciudad": "Montecristi",
        })
        sucursal_id = insertar(cur, "sucursal", {
            "nombre": "Sucursal Principal Montecristi",
            "direccion": "Calle Duarte, Montecristi, República Dominicana",
            "telefono": "809-000-0000",
            "encargado": "Jose Veras",
            "estado": "Activo",
        })
        insertar(cur, "moneda", {"nombre": "Peso dominicano", "simbolo": "RD$", "codigo": "DOP"})
        insertar(cur, "impuestos", {"nombre": "ITBIS", "porcentaje": 18, "estado": "Activo"})
        insertar(cur, "info_factura", {
            "factura_a4": "Factura de Venta",
            "texto_cliente": "Cliente",
            "texto_factura": "Número de Factura",
            "texto_fecha": "Fecha",
            "texto_cajero": "Cajero",
            "texto_agradecimiento": "Gracias por comprar en La Tienda de los Repuestos.",
            "mostrar_cliente": True, "mostrar_factura": True, "mostrar_fecha": True,
            "mostrar_cajero": True, "mostrar_agradecimiento": True,
        })

        insertar(cur, "clientes", {"nombre": "Cliente General", "cedula": "-", "celular": "-", "direccion": "-", "correo": "-", "tipo_id": "Consumidor Final", "estado": "Activo"})
        insertar(cur, "clientes", {"nombre": "Consumidor Final", "cedula": "-", "celular": "-", "direccion": "-", "correo": "-", "tipo_id": "Consumidor Final", "estado": "Activo"})
        insertar(cur, "clientes", {"nombre": "Taller Montecristi Auto", "cedula": "-", "celular": "809-000-0001", "direccion": "Montecristi, República Dominicana", "correo": "-", "tipo_id": "RNC", "estado": "Activo"})
        insertar(cur, "cliente_defecto", {"id": 1, "cliente_nombre": "Cliente General", "cliente_cedula": "-"})

        proveedores = [
            ("Importadora AutoCaribe", "RNC-000000001", "809-000-0010"),
            ("Repuestos Moto Norte", "RNC-000000002", "809-000-0011"),
            ("CicloPartes Dominicana", "RNC-000000003", "809-000-0012"),
            ("Distribuidora El Puente", "RNC-000000004", "809-000-0013"),
        ]
        for nombre, nit, telefono in proveedores:
            insertar(cur, "proveedores", {"nombre": nombre, "nit": nit, "telefono": telefono, "contacto": "Ventas", "email": "-", "direccion": "República Dominicana", "ciudad": "Montecristi", "estado": "Activo"})

        categorias = {
            "Motor y lubricación": "Aceites, filtros, bujías y componentes del motor",
            "Frenos y suspensión": "Pastillas, discos, amortiguadores y dirección",
            "Eléctrico y encendido": "Baterías, luces, fusibles y accesorios eléctricos",
            "Carrocería y exterior": "Espejos, limpiaparabrisas y piezas exteriores",
            "Repuestos para moto": "Componentes y mantenimiento para motocicletas",
            "Repuestos para bicicleta": "Componentes de transmisión, frenos y ruedas",
            "Accesorios": "Accesorios para auto, moto y bicicleta",
            "Herramientas": "Herramientas y equipos para mantenimiento",
        }
        for nombre, descripcion in categorias.items():
            insertar(cur, "categorias", {"nombre": nombre, "descripcion": descripcion})

        productos = [
            ("Aceite motor 20W-50 1 qt", "Motor y lubricación", 380, 250, 40, "750000000001"),
            ("Aceite sintético 5W-30 1 qt", "Motor y lubricación", 650, 430, 25, "750000000002"),
            ("Filtro de aceite Toyota Corolla", "Motor y lubricación", 450, 290, 18, "750000000003"),
            ("Filtro de aire universal auto", "Motor y lubricación", 520, 330, 20, "750000000004"),
            ("Filtro de combustible diesel", "Motor y lubricación", 780, 510, 12, "750000000005"),
            ("Bujía de encendido estándar", "Motor y lubricación", 180, 105, 50, "750000000006"),
            ("Bujía iridium", "Motor y lubricación", 650, 420, 16, "750000000007"),
            ("Pastillas de freno delanteras Corolla", "Frenos y suspensión", 1850, 1200, 10, "750000000008"),
            ("Pastillas de freno traseras Hyundai", "Frenos y suspensión", 1650, 1050, 8, "750000000009"),
            ("Disco de freno delantero universal", "Frenos y suspensión", 2800, 1950, 6, "750000000010"),
            ("Amortiguador delantero auto", "Frenos y suspensión", 4200, 3000, 8, "750000000011"),
            ("Terminal de dirección", "Frenos y suspensión", 950, 590, 14, "750000000012"),
            ("Rótula inferior", "Frenos y suspensión", 1100, 700, 12, "750000000013"),
            ("Batería 12V 60Ah", "Eléctrico y encendido", 7800, 5900, 6, "750000000014"),
            ("Batería 12V 45Ah", "Eléctrico y encendido", 5900, 4300, 8, "750000000015"),
            ("Bombillo H4 halógeno", "Eléctrico y encendido", 280, 160, 30, "750000000016"),
            ("Bombillo LED H4", "Eléctrico y encendido", 1250, 800, 15, "750000000017"),
            ("Fusibles automotrices surtidos", "Eléctrico y encendido", 450, 260, 20, "750000000018"),
            ("Limpiaparabrisas 22 pulgadas", "Carrocería y exterior", 750, 460, 18, "750000000019"),
            ("Espejo lateral universal", "Carrocería y exterior", 1850, 1150, 8, "750000000020"),
            ("Cámara de reversa", "Accesorios", 2400, 1550, 8, "750000000021"),
            ("Cargador USB para auto", "Accesorios", 650, 350, 25, "750000000022"),
            ("Alfombra de goma universal", "Accesorios", 2200, 1400, 10, "750000000023"),
            ("Casco para motocicleta certificado", "Accesorios", 3200, 2200, 12, "750000000024"),
            ("Aceite 4T para motocicleta 20W-50", "Repuestos para moto", 390, 250, 35, "750000000025"),
            ("Kit de arrastre motocicleta 428", "Repuestos para moto", 2450, 1650, 10, "750000000026"),
            ("Pastillas de freno moto delanteras", "Repuestos para moto", 550, 330, 20, "750000000027"),
            ("Bujía para motocicleta", "Repuestos para moto", 220, 125, 35, "750000000028"),
            ("Cable de acelerador moto", "Repuestos para moto", 380, 220, 18, "750000000029"),
            ("Cámara de aire moto  rin 18", "Repuestos para moto", 520, 330, 15, "750000000030"),
            ("Cadena para bicicleta 7 velocidades", "Repuestos para bicicleta", 780, 480, 15, "750000000031"),
            ("Pastillas de freno bicicleta", "Repuestos para bicicleta", 420, 240, 25, "750000000032"),
            ("Cámara de aire bicicleta 26", "Repuestos para bicicleta", 300, 170, 30, "750000000033"),
            ("Cubierta bicicleta 26 x 1.95", "Repuestos para bicicleta", 850, 540, 18, "750000000034"),
            ("Pedales de bicicleta aluminio", "Repuestos para bicicleta", 950, 600, 12, "750000000035"),
            ("Luz LED recargable bicicleta", "Accesorios", 650, 380, 20, "750000000036"),
            ("Candado de seguridad bicicleta", "Accesorios", 900, 530, 15, "750000000037"),
            ("Juego de llaves combinadas 8 piezas", "Herramientas", 1450, 900, 10, "750000000038"),
            ("Gato hidráulico 2 toneladas", "Herramientas", 4600, 3200, 5, "750000000039"),
            ("Compresor de aire portátil 12V", "Herramientas", 2800, 1850, 8, "750000000040"),
        ]
        proveedor_default = "Importadora AutoCaribe"
        productos_ids = []
        for nombre, categoria, precio, costo, stock, codigo in productos:
            producto_id = insertar(cur, "inventario", {"nombre": nombre, "proveedor": proveedor_default, "precio": precio, "costo": costo, "stock": stock, "categoria": categoria, "sucursal": "Sucursal Principal Montecristi", "codigo_barra": codigo, "estado": "Activo", "indicador_facturacion": 1})
            productos_ids.append((producto_id, stock))

        almacen_id = insertar(cur, "almacenes", {"nombre": "Almacén Principal Montecristi", "sucursal_id": sucursal_id, "estado": "Activo"})
        punto_venta_id = insertar(cur, "puntos_venta", {"codigo": "PV-MONTE-01", "nombre": "Punto de Venta Principal", "sucursal_id": sucursal_id, "estado": "Activo"})
        for producto_id, stock in productos_ids:
            insertar(cur, "inventario_almacen", {"producto_id": producto_id, "almacen_id": almacen_id, "stock": stock})
            insertar(cur, "stock_minimo", {"id_producto": producto_id, "stock_minimo": max(2, stock // 5)})

        insertar(cur, "configuracion_general", {"id": 1, "nombre_impuesto": "ITBIS", "porcentaje_impuesto": 18, "precios_incluyen_impuesto": True, "desglosar_impuesto": True, "margen_utilidad_defecto": 30, "almacen_id": almacen_id, "punto_venta_id": punto_venta_id, "modo_facturacion": "informal", "factrapi_ambiente": "pruebas", "factrapi_empresa_verificada": False})
        insertar(cur, "numeracion_local", {"documento": "ticket_venta", "siguiente": 1})
        insertar(cur, "numeracion_local", {"documento": "cotizacion", "siguiente": 1})
        insertar(cur, "cuentas_bancarias", {"banco": "Banco de Reservas", "numero_cuenta": "CONFIGURAR", "tipo": "Cuenta corriente", "saldo": 0, "estado": "Activo"})

        insertar(cur, "usuarios", {"username": "admin", "password": hash_password("admin"), "rol": "Administrador", "nombre": "Jose Veras", "telefono": "809-000-0000", "estado": "Activo"})
        conn.commit()
        print("DATOS_TIENDA_CARGADOS", len(productos_ids), "productos", "empresa_id", empresa_id, "almacen_id", almacen_id, "punto_venta_id", punto_venta_id)


if __name__ == "__main__":
    cargar()
