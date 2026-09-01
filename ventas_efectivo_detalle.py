import os
import db_conexion as sqlite3
import sys
import tkinter as tk
from servicios.servicio_reportes import ServicioReportes
from tkinter import messagebox, ttk
from PIL import Image, ImageTk
from window_utils import posicionar_ventana

class VentasEfectivoDetalle(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.title("Detalle de Ventas en Efectivo")
        posicionar_ventana(self, 960, 540, parent)
        self.resizable(False, False)
        self.configure(bg="#C6D9E3")
        self.transient(parent)
        self.grab_set()
        try:
            self.iconbitmap(self.rutas('icono.ico'))
        except Exception:
            pass

        self.images = {}
        self.db_name = "database.db"
        self.caja_id = getattr(parent, "caja_id", None)
        self.ventas_efectivo = []

        self.widgets()
        self.cargar_datos()

    def rutas(self, ruta):
        try:
            rutabase = sys.__MEIPASS
        except Exception:
            rutabase = os.path.abspath(".")
        return os.path.join(rutabase, ruta)

    def widgets(self):
#============== 1. HEADER ==========================================================================#
        lbl_title = tk.Label(
            self,
            text="DETALLE DE VENTAS EN EFECTIVO",
            font=("sans", 20, "bold"),
            bg="#C6D9E3",
            fg="#1E293B"
        )
        lbl_title.place(relx=0.5, y=25, anchor="center")

        lbl_sub = tk.Label(
            self,
            text="Período: sesión de caja seleccionada",
            font=("sans", 10),
            bg="#C6D9E3",
            fg="#64748B"
        )
        lbl_sub.place(relx=0.5, y=55, anchor="center")

#============== 2. TABLA ===========================================================================#
        style = ttk.Style()
        style.configure("VED.Treeview.Heading", font=("sans", 9, "bold"), background="#E0E6ED")
        style.configure("VED.Treeview", font=("sans", 9), rowheight=24)

        cols = ("factura", "cliente", "metodo", "monto", "fecha_hora")
        self.tabla = ttk.Treeview(self, columns=cols, show="headings", style="VED.Treeview")
        self.tabla.place(x=20, y=85, width=920, height=425)

        titulos = [
            ("factura", "Factura", 90),
            ("cliente", "Cliente", 280),
            ("metodo", "Método de Pago", 160),
            ("monto", "Monto en Efectivo", 170),
            ("fecha_hora", "Fecha y Hora", 200),
        ]

        for c, t, w in titulos:
            self.tabla.heading(c, text=t, anchor="center")
            self.tabla.column(c, width=w, anchor="center" if c in ("factura", "metodo", "fecha_hora") else "e" if c == "monto" else "w")

        scroll_y = ttk.Scrollbar(self, orient="vertical", command=self.tabla.yview)
        self.tabla.configure(yscrollcommand=scroll_y.set)
        scroll_y.place(x=925, y=85, height=425)

    def cargar_datos(self):
        for r in self.tabla.get_children():
            self.tabla.delete(r)

        self.ventas_efectivo = []
        try:
            self.ventas_efectivo = ServicioReportes().ventas_efectivo(self.caja_id)
            self.ventas_efectivo = [(f, c, m, f"$ {float(t or 0):,.2f}", fh) for f, c, m, t, fh in self.ventas_efectivo]
        except Exception:
            self.ventas_efectivo = []

        for v in self.ventas_efectivo:
            self.tabla.insert("", tk.END, values=v)
