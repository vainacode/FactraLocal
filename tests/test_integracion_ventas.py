import os
import unittest
from decimal import Decimal

import db_conexion
from dominio.ventas.modelos import ItemVenta, SolicitudVenta
from dominio.ventas.excepciones import StockInsuficienteError
from servicios.servicio_cuentas_cobrar import ServicioCuentasCobrar
from servicios.servicio_inventario import ServicioInventario
from servicios.servicio_ventas import ServicioVentas


@unittest.skipUnless(os.getenv("POS_RUN_INTEGRATION") == "1", "INTEGRATION_NOT_EXECUTED: requiere POS_RUN_INTEGRATION=1 y factra_test")
class IntegracionVentasTest(unittest.TestCase):
    """Pruebas reales de transacciones contra la base aislada factra_test."""

    @classmethod
    def setUpClass(cls):
        if db_conexion.DSN["dbname"] != "factra_test":
            raise RuntimeError("Las pruebas de integración solo pueden usar factra_test")

    def setUp(self):
        with db_conexion.connect("factra_test") as conn:
            conn.execute("TRUNCATE ventas, facturas_pendientes, facturas_anuladas, abonos_credito, movimientos_caja, movimientos_inventario, transferencias_almacen, inventario_almacen, inventario, almacenes, cajas, cuentas_bancarias, movimientos_bancarios, configuracion_general, numeracion_local RESTART IDENTITY CASCADE")
            conn.execute("INSERT INTO configuracion_general(id, almacen_id, modo_facturacion) VALUES(1, NULL, 'informal')")
            conn.execute("INSERT INTO numeracion_local(documento, siguiente) VALUES('ticket_venta', 1)")
            almacen = conn.execute("INSERT INTO almacenes(nombre, estado) VALUES('Almacén integración', 'Activo') RETURNING id").fetchone()[0]
            almacen_2 = conn.execute("INSERT INTO almacenes(nombre, estado) VALUES('Almacén destino', 'Activo') RETURNING id").fetchone()[0]
            producto = conn.execute("INSERT INTO inventario(nombre, proveedor, precio, costo, stock, estado) VALUES('Producto integración', 'Proveedor test', 10, 5, 5, 'Activo') RETURNING id").fetchone()[0]
            conn.execute("INSERT INTO inventario_almacen(producto_id, almacen_id, stock) VALUES(?,?,?)", (producto, almacen, 5))
            conn.execute("INSERT INTO inventario_almacen(producto_id, almacen_id, stock) VALUES(?,?,?)", (producto, almacen_2, 0))
            caja = conn.execute("INSERT INTO cajas(fecha_apertura,hora_apertura,monto_inicial,cajero,estado,total_ventas) VALUES('2026-09-01','10:00:00',100,'tester','Abierta',0) RETURNING id").fetchone()[0]
            conn.execute("INSERT INTO cuentas_bancarias(banco,numero_cuenta,tipo,saldo,estado) VALUES('Banco test','001','Corriente',0,'Activo')")
            conn.execute("UPDATE configuracion_general SET almacen_id=? WHERE id=1", (almacen,))
        self.almacen, self.almacen_2, self.producto, self.caja = almacen, almacen_2, producto, caja
        self.ventas = ServicioVentas()
        self.inventario = ServicioInventario()
        self.cxc = ServicioCuentasCobrar()

    def item(self, cantidad=1):
        return ItemVenta(self.producto, "Producto integración", cantidad, Decimal("10.00"), Decimal("5.00"))

    def solicitud(self, item, medio="Efectivo", almacen_id=None):
        return SolicitudVenta("Consumidor Final", [item], medio, "tester", self.caja, almacen_id or self.almacen, monto_recibido=Decimal("10000"))

    def consultar(self, sql, params=()):
        with db_conexion.connect("factra_test") as conn:
            return conn.execute(sql, params).fetchone()

    def test_venta_contado_descuenta_stock_y_falla_revierte(self):
        resultado = self.ventas.realizar_venta(self.solicitud(self.item(2)))
        self.assertEqual(resultado.total, Decimal("20.00"))
        self.assertEqual(self.consultar("SELECT stock FROM inventario WHERE id=?", (self.producto,))[0], 3)
        self.assertEqual(self.consultar("SELECT stock FROM inventario_almacen WHERE producto_id=? AND almacen_id=?", (self.producto, self.almacen))[0], 3)
        self.assertEqual(self.consultar("SELECT COUNT(*) FROM ventas")[0], 1)
        with self.assertRaises(StockInsuficienteError):
            self.ventas.realizar_venta(self.solicitud(self.item(99)))
        self.assertEqual(self.consultar("SELECT stock FROM inventario WHERE id=?", (self.producto,))[0], 3)
        self.assertEqual(self.consultar("SELECT COUNT(*) FROM ventas")[0], 1)

    def test_credito_crea_pendiente_y_descuenta_stock(self):
        resultado = self.ventas.realizar_venta(self.solicitud(self.item(2), "Venta a Crédito"))
        self.assertEqual(resultado.total, Decimal("20.00"))
        self.assertEqual(self.consultar("SELECT estado FROM facturas_pendientes WHERE factura=?", (resultado.numero_factura,))[0], "Crédito")
        self.assertEqual(self.consultar("SELECT stock FROM inventario WHERE id=?", (self.producto,))[0], 3)
        self.cxc.registrar_abono(resultado.numero_factura, "Consumidor Final", 5, "Efectivo", None, "tester")
        self.assertEqual(self.consultar("SELECT COALESCE(SUM(monto),0) FROM abonos_credito WHERE factura=?", (resultado.numero_factura,))[0], 5)

    def test_abono_anulacion_y_transferencia_son_atomicos(self):
        venta = self.ventas.realizar_venta(self.solicitud(self.item(1)))
        self.ventas.anular_venta(venta.numero_factura, "tester")
        self.assertEqual(self.consultar("SELECT COUNT(*) FROM ventas WHERE factura=?", (venta.numero_factura,))[0], 0)
        self.assertEqual(self.consultar("SELECT stock FROM inventario WHERE id=?", (self.producto,))[0], 5)
        self.inventario.transferir(self.producto, self.almacen, self.almacen_2, 2, "tester")
        self.assertEqual(self.consultar("SELECT stock FROM inventario_almacen WHERE producto_id=? AND almacen_id=?", (self.producto, self.almacen))[0], 3)
        self.assertEqual(self.consultar("SELECT stock FROM inventario_almacen WHERE producto_id=? AND almacen_id=?", (self.producto, self.almacen_2))[0], 2)
