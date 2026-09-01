import os
import db_conexion as sqlite3
import sys
import tkinter as tk
from tkinter import messagebox, ttk
from PIL import Image, ImageTk
from factura_detalle import FacturaDetalle
from window_utils import posicionar_ventana

class FacturasAnuladas(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.title("Facturas Anuladas")
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
        self.anuladas = []
        self.pagina_actual = 1
        self.por_pagina = 14

        self.widgets()
        self.cargar_anuladas()

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
            text="Facturas Anuladas",
            font=("sans", 24, "bold"),
            bg="#C6D9E3",
            fg="#1E293B"
        )
        lbl_title.place(relx=0.5, y=25, anchor="center")

#============== 2. BARRA DE FILTROS ================================================================#
        lbl_num = tk.Label(self, text="Número de Factura:", font=("sans", 11, "bold"), bg="#C6D9E3", fg="#1E293B")
        lbl_num.place(x=20, y=55)

        self.ent_num = ttk.Entry(self, font=("sans", 11), justify="center")
        self.ent_num.place(x=175, y=53, width=175, height=28)

        lbl_cli = tk.Label(self, text="Nombre del Cliente:", font=("sans", 11, "bold"), bg="#C6D9E3", fg="#1E293B")
        lbl_cli.place(x=380, y=55)

        self.ent_cli = ttk.Entry(self, font=("sans", 11))
        self.ent_cli.place(x=540, y=53, width=200, height=28)

        ruta_f = self.rutas("icono/filtrar.png")
        if os.path.exists(ruta_f):
            img_f = Image.open(ruta_f).resize((20, 20), Image.Resampling.LANCZOS)
            self.images["filtro_an"] = ImageTk.PhotoImage(img_f)
            ico_f = self.images["filtro_an"]
        else:
            ico_f = None

        btn_f = tk.Button(
            self,
            text="  Filtrar",
            image=ico_f,
            compound=tk.LEFT,
            font=("sans", 11, "bold"),
            bg="#EBEFF2",
            fg="#1E293B",
            relief="raised",
            bd=2,
            cursor="hand2",
            command=self.filtrar_anuladas
        )
        btn_f.place(x=760, y=50, width=105, height=34)

#============== 3. TABLA DE FACTURAS ANULADAS =======================================================#
        style = ttk.Style()
        style.configure("FA.Treeview.Heading", font=("sans", 9, "bold"), background="#E0E6ED")
        style.configure("FA.Treeview", font=("sans", 9), rowheight=24)

        cols = ("factura", "cliente", "total", "fecha", "hora", "anulo", "medio_pago")
        self.tabla = ttk.Treeview(self, columns=cols, show="headings", style="FA.Treeview")
        self.tabla.place(x=20, y=95, width=940, height=425)

        titulos = [
            ("factura", "Factura", 70),
            ("cliente", "Cliente", 240),
            ("total", "Total", 130),
            ("fecha", "Fecha", 110),
            ("hora", "Hora", 110),
            ("anulo", "Anuló", 120),
            ("medio_pago", "Medio Pago", 140),
        ]

        for c, t, w in titulos:
            self.tabla.heading(c, text=t, anchor="center")
            self.tabla.column(c, width=w, anchor="center" if c in ("factura", "fecha", "hora", "anulo", "medio_pago") else "e" if c == "total" else "w")

        scroll_y = ttk.Scrollbar(self, orient="vertical", command=self.tabla.yview)
        self.tabla.configure(yscrollcommand=scroll_y.set)
        scroll_y.place(x=950, y=95, height=425)

        self.tabla.bind("<Double-1>", self.al_hacer_doble_click)

#============== 4. BARRA INFERIOR ==================================================================#
        ruta_ant = self.rutas("icono/izquierda.png")
        if os.path.exists(ruta_ant):
            img_a = Image.open(ruta_ant).resize((18, 18), Image.Resampling.LANCZOS)
            self.images["ant_an"] = ImageTk.PhotoImage(img_a)
            ico_a = self.images["ant_an"]
        else:
            ico_a = None

        btn_ant = tk.Button(self, text="  Anterior", image=ico_a, compound=tk.LEFT, font=("sans", 10, "bold"), bg="#EBEFF2", fg="#1E293B", relief="raised", bd=2, cursor="hand2", command=self.pag_ant)
        btn_ant.place(x=20, y=535, width=105, height=36)

        ruta_sig = self.rutas("icono/derecha.png")
        if os.path.exists(ruta_sig):
            img_s = Image.open(ruta_sig).resize((18, 18), Image.Resampling.LANCZOS)
            self.images["sig_an"] = ImageTk.PhotoImage(img_s)
            ico_s = self.images["sig_an"]
        else:
            ico_s = None

        btn_sig = tk.Button(self, text="  Siguiente", image=ico_s, compound=tk.RIGHT, font=("sans", 10, "bold"), bg="#EBEFF2", fg="#1E293B", relief="raised", bd=2, cursor="hand2", command=self.pag_sig)
        btn_sig.place(x=135, y=535, width=105, height=36)

        lbl_hint = tk.Label(self, text="Doble click en una factura anulada para ver el detalle", font=("sans", 10, "bold"), bg="#C6D9E3", fg="#1E293B")
        lbl_hint.place(x=310, y=542)

    def cargar_anuladas(self):
        self.anuladas = []
        try:
            with sqlite3.connect(self.db_name) as conn:
                cur = conn.cursor()
                cur.execute('''
                    SELECT factura, cliente, SUM(total), fecha, hora, anulo, medio_pago
                    FROM facturas_anuladas
                    GROUP BY factura, cliente, fecha, hora, anulo, medio_pago
                    ORDER BY factura DESC
                ''')
                for factura, cliente, total, fecha, hora, anulo, medio in cur.fetchall():
                    self.anuladas.append((
                        factura, cliente, f"$ {total:,.2f}", fecha, hora,
                        anulo or "No registrado", medio or "No registrado"
                    ))
        except Exception as e:
            print("Error cargando facturas anuladas:", e)

        self.renderizar_tabla()

    def renderizar_tabla(self):
        for r in self.tabla.get_children():
            self.tabla.delete(r)

        inicio = (self.pagina_actual - 1) * self.por_pagina
        fin = inicio + self.por_pagina
        for v in self.anuladas[inicio:fin]:
            self.tabla.insert("", tk.END, values=v)

    def al_hacer_doble_click(self, event=None):
        sel = self.tabla.selection()
        if not sel:
            return
        vals = self.tabla.item(sel[0], "values")
        if vals:
            FacturaDetalle(self, factura_id=vals[0])

    def filtrar_anuladas(self):
        num_f = self.ent_num.get().strip()
        nom_c = self.ent_cli.get().strip().lower()

        for r in self.tabla.get_children():
            self.tabla.delete(r)

        for v in self.anuladas:
            match_num = not num_f or str(v[0]) == num_f
            match_nom = not nom_c or nom_c in v[1].lower()
            if match_num and match_nom:
                self.tabla.insert("", tk.END, values=v)

    def pag_ant(self):
        if self.pagina_actual > 1:
            self.pagina_actual -= 1
            self.renderizar_tabla()

    def pag_sig(self):
        total_pags = max(1, (len(self.anuladas) + self.por_pagina - 1) // self.por_pagina)
        if self.pagina_actual < total_pags:
            self.pagina_actual += 1
            self.renderizar_tabla()
