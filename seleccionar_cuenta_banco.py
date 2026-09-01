import os
import db_conexion as sqlite3
import sys
import tkinter as tk
from tkinter import messagebox, ttk
from PIL import Image, ImageTk
from window_utils import posicionar_ventana
from servicios.servicio_caja import ServicioCaja

class SeleccionarCuentaBanco(tk.Toplevel):
    def __init__(self, parent, callback_confirm=None):
        super().__init__(parent)
        self.parent = parent
        self.callback_confirm = callback_confirm
        self.title("Seleccionar Cuenta Bancaria")
        posicionar_ventana(self, 740, 480, parent)
        self.resizable(False, False)
        self.configure(bg="#C6D9E3")
        self.transient(parent)
        self.grab_set()
        try:
            self.iconbitmap(self.rutas('icono.ico'))
        except Exception:
            pass

        self.images = {}
        self.servicio_caja = ServicioCaja()
        self.cuentas = []

        self.widgets()
        self.cargar_cuentas()

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
            text="Seleccione la Cuenta Bancaria",
            font=("sans", 18, "bold"),
            bg="#C6D9E3",
            fg="#1E293B"
        )
        lbl_title.place(relx=0.5, y=30, anchor="center")

#============== 2. TABLA ===========================================================================#
        style = ttk.Style()
        style.configure("SCB.Treeview.Heading", font=("sans", 10, "bold"), background="#E0E6ED")
        style.configure("SCB.Treeview", font=("sans", 10), rowheight=26)

        cols = ("id", "banco", "cuenta", "saldo")
        self.tabla = ttk.Treeview(self, columns=cols, show="headings", style="SCB.Treeview")
        self.tabla.place(x=20, y=70, width=700, height=310)

        titulos = [
            ("id", "ID", 70),
            ("banco", "Banco", 220),
            ("cuenta", "Número de Cuenta", 220),
            ("saldo", "Saldo Disponible", 190),
        ]

        for c, t, w in titulos:
            self.tabla.heading(c, text=t, anchor="center")
            self.tabla.column(c, width=w, anchor="center" if c in ("id", "cuenta") else "e" if c == "saldo" else "w")

        scroll_y = ttk.Scrollbar(self, orient="vertical", command=self.tabla.yview)
        self.tabla.configure(yscrollcommand=scroll_y.set)
        scroll_y.place(x=705, y=70, height=310)

#============== 3. BOTÓN CONFIRMAR =================================================================#
        btn_conf = tk.Button(
            self,
            text="Confirmar Selección",
            font=("sans", 12, "bold"),
            bg="#22C55E",
            fg="white",
            relief="raised",
            bd=2,
            cursor="hand2",
            command=self.confirmar
        )
        btn_conf.place(relx=0.5, y=425, width=220, height=44, anchor="center")

    def cargar_cuentas(self):
        for r in self.tabla.get_children():
            self.tabla.delete(r)

        try:
            rows = self.servicio_caja.listar_cuentas_banco()
            if rows:
                self.cuentas = [(r[0], r[1], r[2], f"RD$ {r[3]:,.2f}") for r in rows]
            else:
                self.cuentas = []
        except Exception:
            self.cuentas = []

        for c in self.cuentas:
            self.tabla.insert("", tk.END, values=c)

    def confirmar(self):
        sel = self.tabla.selection()
        if not sel and self.tabla.get_children():
            sel = [self.tabla.get_children()[0]]

        if not sel:
            messagebox.showwarning("Atención", "Seleccione una cuenta bancaria.")
            return

        vals = self.tabla.item(sel[0], "values")
        if self.callback_confirm:
            self.callback_confirm(vals[1], vals[2])
        self.destroy()
