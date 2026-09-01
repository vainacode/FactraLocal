import os
import sys
import tkinter as tk
from tkinter import messagebox, ttk
from PIL import Image, ImageTk
from window_utils import posicionar_ventana
from servicios.servicio_ventas import ServicioVentas

class FacturasPendientes(tk.Toplevel):
    def __init__(self, parent, callback_retomar=None):
        super().__init__(parent)
        self.parent = parent
        self.callback_retomar = callback_retomar
        self.title("Facturas en Espera / Pendientes")
        posicionar_ventana(self, 880, 520, parent)
        self.resizable(False, False)
        self.configure(bg="#DDE1E5")
        self.transient(parent)
        self.grab_set()
        try:
            self.iconbitmap(self.rutas('icono.ico'))
        except Exception:
            pass

        self.db_name = "database.db"
        self.servicio_ventas = ServicioVentas()
        self.images = {}
        self.pendientes = []

        self.widgets()
        self.cargar_pendientes()

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
            text="FACTURAS EN ESPERA",
            font=("sans", 22, "bold"),
            bg="#DDE1E5",
            fg="#1E293B"
        )
        lbl_title.place(relx=0.5, y=25, anchor="center")

#============== 2. TABLA ===========================================================================#
        style = ttk.Style()
        style.configure("FP.Treeview.Heading", font=("sans", 9, "bold"), background="#E0E6ED")
        style.configure("FP.Treeview", font=("sans", 9), rowheight=24)

        cols = ("id", "factura", "cliente", "items", "total", "fecha_hora")
        self.tabla = ttk.Treeview(self, columns=cols, show="headings", style="FP.Treeview")
        self.tabla.place(x=20, y=65, width=840, height=365)

        titulos = [
            ("id", "ID", 40),
            ("factura", "Nº Factura", 90),
            ("cliente", "Cliente", 250),
            ("items", "Artículos", 80),
            ("total", "Total", 140),
            ("fecha_hora", "Fecha y Hora", 180),
        ]

        for c, t, w in titulos:
            self.tabla.heading(c, text=t, anchor="center")
            self.tabla.column(c, width=w, anchor="center" if c in ("id", "factura", "items", "fecha_hora") else "e" if c == "total" else "w")

        scroll_y = ttk.Scrollbar(self, orient="vertical", command=self.tabla.yview)
        self.tabla.configure(yscrollcommand=scroll_y.set)
        scroll_y.place(x=845, y=65, height=365)

#============== 3. BOTONES INFERIORES ===============================================================#
        ruta_ret = self.rutas("icono/cargarfactura.png")
        if not os.path.exists(ruta_ret):
            ruta_ret = self.rutas("icono/factura.png")

        if os.path.exists(ruta_ret):
            self.images["ret_fp_ico"] = ImageTk.PhotoImage(Image.open(ruta_ret).resize((22, 22), Image.Resampling.LANCZOS))
            ico_r = self.images["ret_fp_ico"]
        else:
            ico_r = None

        btn_ret = tk.Button(
            self,
            text="  Retomar Venta al Carrito",
            image=ico_r,
            compound=tk.LEFT,
            font=("sans", 11, "bold"),
            bg="#22C55E",
            fg="white",
            relief="raised",
            bd=2,
            cursor="hand2",
            command=self.retomar_venta
        )
        btn_ret.place(x=170, y=450, width=250, height=44)

        ruta_del = self.rutas("icono/eliminar.png")
        if os.path.exists(ruta_del):
            self.images["del_fp_ico"] = ImageTk.PhotoImage(Image.open(ruta_del).resize((22, 22), Image.Resampling.LANCZOS))
            ico_d = self.images["del_fp_ico"]
        else:
            ico_d = None

        btn_del = tk.Button(
            self,
            text="  Eliminar",
            image=ico_d,
            compound=tk.LEFT,
            font=("sans", 11, "bold"),
            bg="#EF4444",
            fg="white",
            relief="raised",
            bd=2,
            cursor="hand2",
            command=self.eliminar
        )
        btn_del.place(x=440, y=450, width=150, height=44)

        btn_canc = tk.Button(
            self,
            text="Cerrar",
            font=("sans", 11, "bold"),
            bg="#EBEFF2",
            fg="#1E293B",
            relief="raised",
            bd=2,
            cursor="hand2",
            command=self.destroy
        )
        btn_canc.place(x=610, y=450, width=120, height=44)

    def cargar_pendientes(self):
        for r in self.tabla.get_children():
            self.tabla.delete(r)

        self.pendientes = []
        try:
            for idx, (factura, cliente, items, total, fecha_hora) in enumerate(self.servicio_ventas.listar_pendientes(), start=1):
                    self.pendientes.append((idx, factura, cliente, items, f"$ {total:,.2f}", fecha_hora))
        except Exception as e:
            print("Error cargando facturas pendientes:", e)

        for p in self.pendientes:
            self.tabla.insert("", tk.END, values=p)

    def retomar_venta(self):
        sel = self.tabla.selection()
        if not sel and self.tabla.get_children():
            sel = [self.tabla.get_children()[0]]

        if not sel:
            messagebox.showwarning("Atención", "Seleccione una venta en espera para retomar.")
            return

        vals = self.tabla.item(sel[0], "values")
        if self.callback_retomar:
            self.callback_retomar(vals[1])
        messagebox.showinfo("Venta Retomada", f"Factura #{vals[1]} ({vals[2]}) cargada nuevamente al punto de venta.")
        self.destroy()

    def eliminar(self):
        sel = self.tabla.selection()
        if not sel:
            messagebox.showwarning("Atención", "Seleccione una venta para eliminar.")
            return

        vals = self.tabla.item(sel[0], "values")
        if not messagebox.askyesno("Confirmar", f"¿Desea eliminar la factura pendiente #{vals[1]}?"):
            return

        try:
            self.servicio_ventas.eliminar_pendiente(vals[1])
            self.cargar_pendientes()
            messagebox.showinfo("Éxito", "Factura en espera eliminada.")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo eliminar la factura: {e}")
