import os
import db_conexion as sqlite3
import sys
import tkinter as tk
from tkinter import ttk
from window_utils import posicionar_ventana

class ClienteDetalle(tk.Toplevel):
    def __init__(self, parent, cliente_id=None, cliente_nom=""):
        super().__init__(parent)
        self.parent = parent
        self.cliente_id = cliente_id
        self.cliente_nom = cliente_nom
        self.title(f"Detalle Cliente: {cliente_nom}")
        posicionar_ventana(self, 980, 600, parent)
        self.resizable(False, False)
        self.configure(bg="#DDE1E5")
        self.transient(parent)
        self.grab_set()
        try:
            self.iconbitmap(self.rutas('icono.ico'))
        except Exception:
            pass

        self.db_name = "database.db"
        self.images = {}
        self.facturas = []

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
            text="INFORMACIÓN DEL CLIENTE",
            font=("sans", 24, "bold"),
            bg="#DDE1E5",
            fg="#1E293B"
        )
        lbl_title.place(relx=0.5, y=25, anchor="center")

#============== 2. DATOS PERSONALES (IZQUIERDA) ====================================================#
        frame_dp = tk.LabelFrame(
            self,
            text="DATOS PERSONALES",
            font=("sans", 12, "bold"),
            bg="#C6D9E3",
            fg="#1E293B",
            padx=15,
            pady=10
        )
        frame_dp.place(x=20, y=55, width=460, height=200)

        datos = [
            ("Nombre:", self.cliente_nom),
            ("Identificación:", "-"),
            ("Celular:", "-"),
            ("Correo:", "-"),
            ("Dirección:", "-"),
        ]

        y_d = 8
        for t, v in datos:
            lbl_t = tk.Label(frame_dp, text=t, font=("sans", 10, "bold"), bg="#C6D9E3", fg="#1E293B")
            lbl_t.place(x=15, y=y_d)

            lbl_v = tk.Label(frame_dp, text=v, font=("sans", 10), bg="#C6D9E3", fg="#1E293B")
            lbl_v.place(x=130, y=y_d)
            y_d += 28

#============== 3. ESTADÍSTICAS (DERECHA) ==========================================================#
        frame_est = tk.LabelFrame(
            self,
            text="ESTADÍSTICAS",
            font=("sans", 12, "bold"),
            bg="#C6D9E3",
            fg="#1E293B",
            padx=15,
            pady=10
        )
        frame_est.place(x=500, y=55, width=460, height=200)

        stats = [
            ("Total Facturado:", "$ 0.00", "#16A34A"),
            ("Número de Facturas:", "0", "#0284C7"),
            ("Créditos Pendientes:", "0", "#DC2626"),
            ("Saldo Pendiente:", "$ 0.00", "#DC2626"),
            ("Total Abonado:", "$ 0.00", "#D97706"),
            ("Última Compra:", "-", "#7C3AED"),
        ]

        y_s = 6
        for t, v, col in stats:
            lbl_t = tk.Label(frame_est, text=t, font=("sans", 9, "bold"), bg="#C6D9E3", fg="#1E293B")
            lbl_t.place(x=15, y=y_s)

            lbl_v = tk.Label(frame_est, text=v, font=("sans", 9, "bold"), bg="#C6D9E3", fg=col)
            lbl_v.place(x=165, y=y_s)
            y_s += 26

#============== 4. HISTORIAL DE FACTURAS (ÚLTIMAS 10) ==============================================#
        frame_hist = tk.LabelFrame(
            self,
            text="HISTORIAL DE FACTURAS (ÚLTIMAS 10)",
            font=("sans", 12, "bold"),
            bg="#C6D9E3",
            fg="#1E293B",
            padx=10,
            pady=6
        )
        frame_hist.place(x=20, y=265, width=940, height=265)

        style = ttk.Style()
        style.configure("CD.Treeview.Heading", font=("sans", 9, "bold"), background="#E0E6ED")
        style.configure("CD.Treeview", font=("sans", 9), rowheight=24)

        cols = ("factura", "fecha", "productos", "total", "saldo", "estado", "medio_pago")
        self.tabla = ttk.Treeview(frame_hist, columns=cols, show="headings", style="CD.Treeview")
        self.tabla.place(x=5, y=5, width=905, height=225)

        titulos = [
            ("factura", "Factura", 70),
            ("fecha", "Fecha", 160),
            ("productos", "Productos", 80),
            ("total", "Total", 130),
            ("saldo", "Saldo", 120),
            ("estado", "Estado", 110),
            ("medio_pago", "Medio Pago", 130),
        ]

        for c, t, w in titulos:
            self.tabla.heading(c, text=t, anchor="center")
            self.tabla.column(c, width=w, anchor="center" if c in ("factura", "fecha", "productos", "estado", "medio_pago") else "e")

        scroll_y = ttk.Scrollbar(frame_hist, orient="vertical", command=self.tabla.yview)
        self.tabla.configure(yscrollcommand=scroll_y.set)
        scroll_y.place(x=912, y=5, height=225)

#============== 5. BOTÓN CERRAR =====================================================================#
        btn_cerrar = tk.Button(
            self,
            text="Cerrar",
            font=("sans", 12, "bold"),
            bg="#EF4444",
            fg="white",
            relief="raised",
            bd=2,
            cursor="hand2",
            command=self.destroy
        )
        btn_cerrar.place(relx=0.5, y=555, width=170, height=40, anchor="center")

    def cargar_datos(self):
        for r in self.tabla.get_children():
            self.tabla.delete(r)

        self.facturas = []

        for f in self.facturas:
            self.tabla.insert("", tk.END, values=f)
