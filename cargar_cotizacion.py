import os
import db_conexion as sqlite3
import sys
import tkinter as tk
from tkinter import messagebox, ttk
from PIL import Image, ImageTk
from window_utils import posicionar_ventana

class CargarCotizacion(tk.Toplevel):
    def __init__(self, parent, callback_load=None):
        super().__init__(parent)
        self.parent = parent
        self.callback_load = callback_load
        self.title("Cargar Cotización")
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
        self.cotizaciones = []
        self.pagina_actual = 1
        self.por_pagina = 14

        self.widgets()
        self.cargar_cotizaciones()

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
            text="Cargar Cotización",
            font=("sans", 24, "bold"),
            bg="#C6D9E3",
            fg="#1E293B"
        )
        lbl_title.place(relx=0.5, y=25, anchor="center")

#============== 2. BARRA DE FILTROS ================================================================#
        lbl_num = tk.Label(self, text="Número de Cotización:", font=("sans", 11, "bold"), bg="#C6D9E3", fg="#1E293B")
        lbl_num.place(x=20, y=55)

        self.ent_num = ttk.Entry(self, font=("sans", 11), justify="center")
        self.ent_num.place(x=195, y=53, width=175, height=28)

        lbl_cli = tk.Label(self, text="Nombre del Cliente:", font=("sans", 11, "bold"), bg="#C6D9E3", fg="#1E293B")
        lbl_cli.place(x=400, y=55)

        self.ent_cli = ttk.Entry(self, font=("sans", 11))
        self.ent_cli.place(x=560, y=53, width=200, height=28)

        ruta_f = self.rutas("icono/filtrar.png")
        if os.path.exists(ruta_f):
            img_f = Image.open(ruta_f).resize((20, 20), Image.Resampling.LANCZOS)
            self.images["filtro_cc"] = ImageTk.PhotoImage(img_f)
            ico_f = self.images["filtro_cc"]
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
            command=self.filtrar_cotizaciones
        )
        btn_f.place(x=780, y=50, width=105, height=34)

#============== 3. TABLA ===========================================================================#
        style = ttk.Style()
        style.configure("CC.Treeview.Heading", font=("sans", 9, "bold"), background="#E0E6ED")
        style.configure("CC.Treeview", font=("sans", 9), rowheight=24)

        cols = ("cotizacion", "cliente", "total", "fecha", "hora", "cajero")
        self.tabla = ttk.Treeview(self, columns=cols, show="headings", style="CC.Treeview")
        self.tabla.place(x=20, y=95, width=940, height=425)

        titulos = [
            ("cotizacion", "Cotización", 90),
            ("cliente", "Cliente", 300),
            ("total", "Total", 140),
            ("fecha", "Fecha", 130),
            ("hora", "Hora", 130),
            ("cajero", "Cajero", 130),
        ]

        for c, t, w in titulos:
            self.tabla.heading(c, text=t, anchor="center")
            self.tabla.column(c, width=w, anchor="center" if c in ("cotizacion", "fecha", "hora", "cajero") else "e" if c == "total" else "w")

        scroll_y = ttk.Scrollbar(self, orient="vertical", command=self.tabla.yview)
        self.tabla.configure(yscrollcommand=scroll_y.set)
        scroll_y.place(x=950, y=95, height=425)

#============== 4. BARRA INFERIOR ==================================================================#
        ruta_ant = self.rutas("icono/izquierda.png")
        if os.path.exists(ruta_ant):
            img_a = Image.open(ruta_ant).resize((18, 18), Image.Resampling.LANCZOS)
            self.images["ant_cc"] = ImageTk.PhotoImage(img_a)
            ico_a = self.images["ant_cc"]
        else:
            ico_a = None

        btn_ant = tk.Button(self, text="  Anterior", image=ico_a, compound=tk.LEFT, font=("sans", 10, "bold"), bg="#EBEFF2", fg="#1E293B", relief="raised", bd=2, cursor="hand2", command=self.pag_ant)
        btn_ant.place(x=20, y=535, width=105, height=36)

        ruta_sig = self.rutas("icono/derecha.png")
        if os.path.exists(ruta_sig):
            img_s = Image.open(ruta_sig).resize((18, 18), Image.Resampling.LANCZOS)
            self.images["sig_cc"] = ImageTk.PhotoImage(img_s)
            ico_s = self.images["sig_cc"]
        else:
            ico_s = None

        btn_sig = tk.Button(self, text="  Siguiente", image=ico_s, compound=tk.RIGHT, font=("sans", 10, "bold"), bg="#EBEFF2", fg="#1E293B", relief="raised", bd=2, cursor="hand2", command=self.pag_sig)
        btn_sig.place(x=135, y=535, width=105, height=36)

        ruta_carg = self.rutas("icono/cargarcotizacion1.png")
        if not os.path.exists(ruta_carg):
            ruta_carg = self.rutas("icono/factura.png")

        if os.path.exists(ruta_carg):
            img_c = Image.open(ruta_carg).resize((22, 22), Image.Resampling.LANCZOS)
            self.images["carg_cc_ico"] = ImageTk.PhotoImage(img_c)
            ico_c = self.images["carg_cc_ico"]
        else:
            ico_c = None

        btn_cargar_sel = tk.Button(
            self,
            text="  Cargar Cotización Seleccionada",
            image=ico_c,
            compound=tk.LEFT,
            font=("sans", 11, "bold"),
            bg="#22C55E",
            fg="white",
            relief="raised",
            bd=2,
            cursor="hand2",
            command=self.cargar_seleccionada
        )
        btn_cargar_sel.place(x=310, y=530, width=355, height=44)

    def cargar_cotizaciones(self):
        self.cotizaciones = []
        try:
            with sqlite3.connect(self.db_name) as conn:
                cur = conn.cursor()
                cur.execute('''
                    SELECT cotizacion, cliente, SUM(total), fecha, hora, cajero
                    FROM cotizaciones
                    GROUP BY cotizacion, cliente, fecha, hora, cajero
                    ORDER BY cotizacion DESC
                ''')
                for cot, cliente, total, fecha, hora, cajero in cur.fetchall():
                    self.cotizaciones.append((cot, cliente, f"{total:,.2f}", fecha, hora, cajero or "No registrado"))
        except Exception as e:
            print("Error cargando cotizaciones:", e)

        self.pagina_actual = 1
        self.renderizar_tabla()

    def renderizar_tabla(self):
        for r in self.tabla.get_children():
            self.tabla.delete(r)

        self.tabla.tag_configure("sel_row", background="#38BDF8", foreground="#FFFFFF")

        inicio = (self.pagina_actual - 1) * self.por_pagina
        fin = inicio + self.por_pagina
        for c in self.cotizaciones[inicio:fin]:
            item_id = self.tabla.insert("", tk.END, values=c)
            self.tabla.item(item_id, tags=("sel_row",))

    def pag_ant(self):
        if self.pagina_actual > 1:
            self.pagina_actual -= 1
            self.renderizar_tabla()

    def pag_sig(self):
        total_pags = max(1, (len(self.cotizaciones) + self.por_pagina - 1) // self.por_pagina)
        if self.pagina_actual < total_pags:
            self.pagina_actual += 1
            self.renderizar_tabla()

    def cargar_seleccionada(self):
        sel = self.tabla.selection()
        if not sel and self.tabla.get_children():
            sel = [self.tabla.get_children()[0]]

        if not sel:
            messagebox.showwarning("Atención", "Seleccione una cotización para cargar.")
            return

        vals = self.tabla.item(sel[0], "values")
        if self.callback_load:
            self.callback_load(vals[0])
        messagebox.showinfo("Cotización Cargada", f"Cotización #{vals[0]} cargada al punto de cotización exitosamente.")
        self.destroy()

    def filtrar_cotizaciones(self):
        num_c = self.ent_num.get().strip()
        nom_c = self.ent_cli.get().strip().lower()

        for r in self.tabla.get_children():
            self.tabla.delete(r)

        for c in self.cotizaciones:
            match_num = not num_c or str(c[0]) == num_c
            match_nom = not nom_c or nom_c in c[1].lower()
            if match_num and match_nom:
                self.tabla.insert("", tk.END, values=c)
