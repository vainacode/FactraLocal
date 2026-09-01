import os
import sys
import tkinter as tk
from tkinter import messagebox, ttk
from PIL import Image, ImageTk
from historial_producto import HistorialProducto
from reporte_caja import ReporteCajaUsuario
from reporte_rentabilidad import ReporteProductosRentables
from window_utils import posicionar_ventana

class Reportes(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.title("Punto de Venta Versión 4.4.7")
        posicionar_ventana(self, 1100, 650, parent)
        self.resizable(False, False)
        self.configure(bg="#C6D9E3")
        self.transient(parent)
        self.grab_set()
        try:
            self.iconbitmap(self.rutas('icono.ico'))
        except Exception:
            pass

        self.images = {}
        self.widgets()

    def rutas(self, ruta):
        try:
            rutabase = sys.__MEIPASS
        except Exception:
            rutabase = os.path.abspath(".")
        return os.path.join(rutabase, ruta)

    def widgets(self):
#============== 1. HEADER ==========================================================================#
        frame_header = tk.Frame(self, bg="#DDE1E5", highlightbackground="#B8C4CE", highlightthickness=1)
        frame_header.pack()
        frame_header.place(x=0, y=0, width=1100, height=75)

        lbl_titulo = tk.Label(
            frame_header,
            text="REPORTES",
            font=("sans", 28, "bold"),
            bg="#DDE1E5",
            fg="#1E293B"
        )
        lbl_titulo.place(relx=0.5, rely=0.5, anchor="center")

#============== 2. COLUMNAS DE REPORTES (4 COLUMNAS) ===============================================#
        columnas_reportes = [
            # Columna 1 (x=20)
            [
                ("Reporte\nventas totales", "reporte1.png", lambda: self.abrir_ventas_totales()),
                ("Reporte\nganancias", "reporte2.png", lambda: ReporteProductosRentables(self)),
                ("Reporte costo\ntotal inventario", "totalinv.png", lambda: self.abrir_costo_inventario()),
                ("Reporte costo\ntotal ventas", "reporte4.png", lambda: self.abrir_reporte("Costo Total Ventas")),
                ("Reporte\nmedios de pago", "mediospago.png", lambda: self.abrir_reporte("Medios de Pago")),
                ("Historial\nProductos", "historialprecios.png", lambda: HistorialProducto(self)),
            ],
            # Columna 2 (x=290)
            [
                ("Reporte\nVentas por Mes", "graficoventas.png", lambda: self.abrir_reporte("Ventas por Mes")),
                ("Reporte\nGanancias Mes", "graficoganancias.png", lambda: self.abrir_reporte("Ganancias por Mes")),
                ("Reporte\npor Categorias", "graficocategorias.png", lambda: self.abrir_reporte("Reporte por Categorías")),
                ("Reporte\npor Sucursal", "graficosucursal.png", lambda: self.abrir_reporte("Reporte por Sucursal")),
                ("Compras\npor Producto", "reportecompras.png", lambda: self.abrir_reporte("Compras por Producto")),
            ],
            # Columna 3 (x=560)
            [
                ("Reporte\nGastos por Mes", "btngastos.png", lambda: self.abrir_reporte("Gastos por Mes")),
                ("Reporte Cuenta\npor Cobrar", "btncobros.png", lambda: self.abrir_cuentas_cobrar()),
                ("Resumen\nBancario", "btnbanco.png", lambda: self.abrir_reporte("Resumen Bancario")),
                ("Reporte Caja\npor Usuario", "reportecajero.png", lambda: ReporteCajaUsuario(self)),
                ("Reporte Cuenta\npor Pagar", "pago3.png", lambda: self.abrir_reporte("Cuentas por Pagar")),
            ],
            # Columna 4 (x=830)
            [
                ("Reporte Ventas\npor Producto", "reporte_producto.png", lambda: self.abrir_reporte("Ventas por Producto")),
                ("Productos\nBajo Stock", "bajastock.png", lambda: self.abrir_reporte("Productos Bajo Stock")),
                ("Reporte Ventas\npor Cliente", "reporte-cliente.png", lambda: self.abrir_reporte("Ventas por Cliente")),
                ("Ganancias\npor Producto", "graficoganancias.png", lambda: ReporteProductosRentables(self)),
            ]
        ]

        x_cols = [20, 290, 560, 830]

        for i, col_items in enumerate(columnas_reportes):
            x_pos = x_cols[i]
            # Contenedor de la columna
            frame_col = tk.Frame(
                self,
                bg="#C6D9E3",
                highlightbackground="#A9BFCE",
                highlightthickness=1
            )
            frame_col.place(x=x_pos, y=90, width=250, height=540)

            y_item = 8
            for txt, ico_f, cmd in col_items:
                ruta_i = self.rutas(f"icono/{ico_f}")
                if not os.path.exists(ruta_i):
                    nom_alt = ico_f.replace("reporte", "grafico").replace("btn", "")
                    ruta_i = self.rutas(f"icono/{nom_alt}")
                if not os.path.exists(ruta_i):
                    ruta_i = self.rutas("icono/reporte.png")

                if os.path.exists(ruta_i):
                    img_raw = Image.open(ruta_i).resize((34, 34), Image.Resampling.LANCZOS)
                    self.images[f"rep_{ico_f}"] = ImageTk.PhotoImage(img_raw)
                    ico_btn = self.images[f"rep_{ico_f}"]
                else:
                    ico_btn = None

                btn_rep = tk.Button(
                    frame_col,
                    text=f"  {txt}",
                    image=ico_btn,
                    compound=tk.LEFT,
                    font=("sans", 11, "bold"),
                    bg="#EBEFF2",
                    fg="#1E293B",
                    activebackground="#D5E0E8",
                    activeforeground="#1A252F",
                    relief="raised",
                    bd=2,
                    anchor="w",
                    padx=12,
                    cursor="hand2",
                    command=cmd
                )
                btn_rep.place(x=8, y=y_item, width=232, height=76)
                y_item += 86

    def abrir_ventas_totales(self):
        from reporte_ventas_totales import ReporteVentasTotales
        ReporteVentasTotales(self)

    def abrir_cuentas_cobrar(self):
        from reporte_cuentas_cobrar import ReporteCuentasCobrar
        ReporteCuentasCobrar(self)

    def abrir_costo_inventario(self):
        from reporte_costo_inventario import ReporteCostoInventario
        ReporteCostoInventario(self)

    def abrir_reporte(self, nombre):
        if nombre == "Resumen Bancario":
            from movimientos_bancarios import MovimientosBancarios
            MovimientosBancarios(self)
        elif nombre == "Productos Bajo Stock":
            from alerta_stock_bajo import AlertaStockBajo
            AlertaStockBajo(self)
        elif nombre == "Reporte por Categorías":
            from categorias import Categorias
            Categorias(self)
        elif nombre == "Reporte por Sucursal":
            from sucursales import Sucursales
            Sucursales(self)
        elif nombre == "Ventas por Mes":
            from reporte_ventas_mes import ReporteVentasMes
            ReporteVentasMes(self)
        elif nombre == "Ganancias por Mes":
            from reporte_ganancias_mes import ReporteGananciasMes
            ReporteGananciasMes(self)
        elif nombre == "Ventas por Producto":
            from reporte_ventas_producto import ReporteVentasProducto
            ReporteVentasProducto(self)
        elif nombre == "Ventas por Cliente":
            from reporte_ventas_cliente import ReporteVentasCliente
            ReporteVentasCliente(self)
        elif nombre == "Compras por Producto":
            from reporte_compras_producto import ReporteComprasProducto
            ReporteComprasProducto(self)
        elif nombre == "Gastos por Mes":
            from reporte_gastos_mes import ReporteGastosMes
            ReporteGastosMes(self)
        elif nombre == "Cuentas por Pagar":
            from reporte_cuentas_pagar import ReporteCuentasPagar
            ReporteCuentasPagar(self)
        elif nombre == "Medios de Pago":
            from reporte_medios_pago import ReporteMediosPago
            ReporteMediosPago(self)
        elif nombre == "Costo Total Ventas":
            from reporte_costo_inventario import ReporteCostoInventario
            ReporteCostoInventario(self)
        else:
            from reporte_ventas_totales import ReporteVentasTotales
            ReporteVentasTotales(self)
