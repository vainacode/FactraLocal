import os
import db_conexion as sqlite3
import sys
import tkinter as tk
from tkinter import messagebox, ttk
from PIL import Image, ImageTk
from window_utils import posicionar_ventana

class FacturaDetalle(tk.Toplevel):
    def __init__(self, parent, factura_id=4):
        super().__init__(parent)
        self.parent = parent
        self.factura_id = factura_id
        self.title(f"Detalles de la Factura {factura_id}")
        posicionar_ventana(self, 980, 600, parent)
        self.resizable(False, False)
        self.configure(bg="#C6D9E3")
        self.transient(parent)
        self.grab_set()
        try:
            self.iconbitmap(self.rutas('icono.ico'))
        except Exception:
            pass

        self.db_name = "database.db"
        self.images = {}
        self.items_factura = []
        self.total_fac = 0.0
        self.medio_pago = "No disponible"

        self.widgets()
        self.cargar_detalles()

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
            text=f"Detalles de la Factura No.{self.factura_id}",
            font=("sans", 24, "bold"),
            bg="#C6D9E3",
            fg="#1E293B"
        )
        lbl_title.place(relx=0.5, y=30, anchor="center")

#============== 2. TABLA DE DETALLES ===============================================================#
        style = ttk.Style()
        style.configure("FD.Treeview.Heading", font=("sans", 9, "bold"), background="#E0E6ED")
        style.configure("FD.Treeview", font=("sans", 9), rowheight=24)

        cols = ("factura", "cliente", "producto", "precio", "impuesto", "cantidad", "total")
        self.tabla = ttk.Treeview(self, columns=cols, show="headings", style="FD.Treeview")
        self.tabla.place(x=20, y=70, width=940, height=350)

        titulos = [
            ("factura", "Factura", 70),
            ("cliente", "Cliente", 200),
            ("producto", "Producto", 320),
            ("precio", "Precio", 110),
            ("impuesto", "Impuesto", 100),
            ("cantidad", "Cantidad", 80),
            ("total", "Total", 120),
        ]

        for c, t, w in titulos:
            self.tabla.heading(c, text=t, anchor="center")
            self.tabla.column(c, width=w, anchor="center" if c in ("factura", "cantidad") else "w" if c in ("cliente", "producto") else "e")

        scroll_y = ttk.Scrollbar(self, orient="vertical", command=self.tabla.yview)
        self.tabla.configure(yscrollcommand=scroll_y.set)
        scroll_y.place(x=950, y=70, height=350)

#============== 3. INFORMACIÓN DE PAGO =============================================================#
        frame_pago = tk.LabelFrame(
            self,
            text="Información de Pago",
            font=("sans", 12, "bold"),
            bg="#C6D9E3",
            fg="#1E293B",
            padx=15,
            pady=10
        )
        frame_pago.place(x=20, y=435, width=940, height=80)

        self.lbl_metodo = tk.Label(
            frame_pago,
            text=f"Método de Pago: {self.medio_pago}",
            font=("sans", 12, "bold"),
            bg="#C6D9E3",
            fg="#0284C7"
        )
        self.lbl_metodo.place(x=30, y=10)

        self.lbl_total = tk.Label(
            frame_pago,
            text=f"Total: $ {self.total_fac:,.2f}",
            font=("sans", 12, "bold"),
            bg="#C6D9E3",
            fg="#16A34A"
        )
        self.lbl_total.place(x=360, y=10)

#============== 4. BOTONES REGENERAR ================================================================#
        ruta_fac = self.rutas("icono/factura.png")
        if os.path.exists(ruta_fac):
            img_f = Image.open(ruta_fac).resize((22, 22), Image.Resampling.LANCZOS)
            self.images["fac_regen"] = ImageTk.PhotoImage(img_f)
            ico_f = self.images["fac_regen"]
        else:
            ico_f = None

        ruta_tic = self.rutas("icono/facturapendiente.png")
        if os.path.exists(ruta_tic):
            img_t = Image.open(ruta_tic).resize((22, 22), Image.Resampling.LANCZOS)
            self.images["tic_regen"] = ImageTk.PhotoImage(img_t)
            ico_t = self.images["tic_regen"]
        else:
            ico_t = None

        btn_a4 = tk.Button(
            self,
            text="  Regenerar A4",
            image=ico_f,
            compound=tk.LEFT,
            font=("sans", 11, "bold"),
            bg="#EBEFF2",
            fg="#1E293B",
            relief="raised",
            bd=2,
            cursor="hand2",
            command=lambda: self.imprimir_formato("A4")
        )
        btn_a4.place(x=190, y=530, width=175, height=44)

        btn_80 = tk.Button(
            self,
            text="  Regenerar 80mm",
            image=ico_t,
            compound=tk.LEFT,
            font=("sans", 11, "bold"),
            bg="#EBEFF2",
            fg="#1E293B",
            relief="raised",
            bd=2,
            cursor="hand2",
            command=lambda: self.imprimir_formato("80mm")
        )
        btn_80.place(x=400, y=530, width=185, height=44)

        btn_50 = tk.Button(
            self,
            text="  Regenerar 50mm",
            image=ico_f,
            compound=tk.LEFT,
            font=("sans", 11, "bold"),
            bg="#EBEFF2",
            fg="#1E293B",
            relief="raised",
            bd=2,
            cursor="hand2",
            command=lambda: self.imprimir_formato("50mm")
        )
        btn_50.place(x=620, y=530, width=185, height=44)

    def cargar_detalles(self):
        for r in self.tabla.get_children():
            self.tabla.delete(r)

        self.items_factura = []
        total_real = 0.0
        medio_real = None
        try:
            with sqlite3.connect(self.db_name) as conn:
                cur = conn.cursor()
                cur.execute("SELECT factura, cliente, producto, precio, cantidad, total, medio_pago FROM ventas WHERE factura=?", (self.factura_id,))
                rows = cur.fetchall()
                if not rows:
                    cur.execute("SELECT factura, cliente, producto, precio, cantidad, total, COALESCE(medio_pago, 'Crédito') FROM facturas_pendientes WHERE factura=? AND estado IN ('Crédito', 'Pagada')", (self.factura_id,))
                    rows = cur.fetchall()
                if not rows:
                    cur.execute("SELECT factura, cliente, producto, precio, cantidad, total, medio_pago FROM facturas_anuladas WHERE factura=?", (self.factura_id,))
                    rows = cur.fetchall()
                for r in rows:
                    impuesto = 0.00
                    total_real += r[5] or 0.0
                    medio_real = r[6] or medio_real
                    self.items_factura.append((r[0], r[1], r[2], f"$ {r[3]:,.2f}", f"$ {impuesto:,.2f}", r[4], f"$ {r[5]:,.2f}"))
        except Exception as e:
            print("Error cargando detalle de factura:", e)

        if self.items_factura:
            self.total_fac = total_real
            self.medio_pago = medio_real or "Efectivo"
            self.lbl_total.config(text=f"Total: $ {self.total_fac:,.2f}")
            self.lbl_metodo.config(text=f"Método de Pago: {self.medio_pago}")

        for it in self.items_factura:
            self.tabla.insert("", tk.END, values=it)

    def imprimir_formato(self, formato):
        try:
            from documentos import dialogo_documento, generar_factura
            ruta = generar_factura(self.factura_id, formato=formato)
            dialogo_documento(self, "Factura generada", f"La factura #{self.factura_id} fue preparada en formato {formato} y está lista para imprimir.", ruta)
        except Exception as e:
            from documentos import dialogo_documento
            dialogo_documento(self, "No se pudo generar", str(e), error=True)
