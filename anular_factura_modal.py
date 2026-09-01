import os
import sys
import tkinter as tk
from tkinter import messagebox, ttk
from PIL import Image, ImageTk
from facturas_anuladas import FacturasAnuladas
from window_utils import posicionar_ventana
from servicios.servicio_ventas import ServicioVentas


class AnularFacturaModal(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.title("Anular Venta")
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
        self.servicio_ventas = ServicioVentas()
        self.images = {}
        self.facturas = []
        self.pagina_actual = 1
        self.por_pagina = 14

        self.widgets()
        self.cargar_facturas()

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
            text="Anular Factura",
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
            self.images["filt_afm"] = ImageTk.PhotoImage(Image.open(ruta_f).resize((20, 20), Image.Resampling.LANCZOS))
            ico_f = self.images["filt_afm"]
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
            command=self.filtrar_facturas
        )
        btn_f.place(x=760, y=50, width=105, height=34)

#============== 3. TABLA DE FACTURAS ===============================================================#
        style = ttk.Style()
        style.configure("AFM.Treeview.Heading", font=("sans", 9, "bold"), background="#E0E6ED")
        style.configure("AFM.Treeview", font=("sans", 9), rowheight=24)

        cols = ("factura", "cliente", "total", "fecha", "hora", "cajero", "medio_pago")
        self.tabla = ttk.Treeview(self, columns=cols, show="headings", style="AFM.Treeview")
        self.tabla.place(x=20, y=95, width=940, height=425)

        titulos = [
            ("factura", "Factura", 70),
            ("cliente", "Cliente", 240),
            ("total", "Total", 130),
            ("fecha", "Fecha", 110),
            ("hora", "Hora", 110),
            ("cajero", "Cajero", 120),
            ("medio_pago", "Medio Pago", 140),
        ]

        for c, t, w in titulos:
            self.tabla.heading(c, text=t, anchor="center")
            self.tabla.column(c, width=w, anchor="center" if c in ("factura", "fecha", "hora", "cajero", "medio_pago") else "e" if c == "total" else "w")

        scroll_y = ttk.Scrollbar(self, orient="vertical", command=self.tabla.yview)
        self.tabla.configure(yscrollcommand=scroll_y.set)
        scroll_y.place(x=950, y=95, height=425)

#============== 4. BARRA INFERIOR ==================================================================#
        ruta_ant = self.rutas("icono/izquierda.png")
        if os.path.exists(ruta_ant):
            self.images["ant_afm"] = ImageTk.PhotoImage(Image.open(ruta_ant).resize((18, 18), Image.Resampling.LANCZOS))
            ico_a = self.images["ant_afm"]
        else:
            ico_a = None

        btn_ant = tk.Button(self, text="  Anterior", image=ico_a, compound=tk.LEFT, font=("sans", 10, "bold"), bg="#EBEFF2", fg="#1E293B", relief="raised", bd=2, cursor="hand2", command=self.pag_ant)
        btn_ant.place(x=20, y=535, width=105, height=36)

        ruta_sig = self.rutas("icono/derecha.png")
        if os.path.exists(ruta_sig):
            self.images["sig_afm"] = ImageTk.PhotoImage(Image.open(ruta_sig).resize((18, 18), Image.Resampling.LANCZOS))
            ico_s = self.images["sig_afm"]
        else:
            ico_s = None

        btn_sig = tk.Button(self, text="  Siguiente", image=ico_s, compound=tk.RIGHT, font=("sans", 10, "bold"), bg="#EBEFF2", fg="#1E293B", relief="raised", bd=2, cursor="hand2", command=self.pag_sig)
        btn_sig.place(x=135, y=535, width=105, height=36)

        ruta_anular = self.rutas("icono/eliminar.png")
        if os.path.exists(ruta_anular):
            self.images["anul_afm_ico"] = ImageTk.PhotoImage(Image.open(ruta_anular).resize((20, 20), Image.Resampling.LANCZOS))
            ico_an = self.images["anul_afm_ico"]
        else:
            ico_an = None

        btn_anular = tk.Button(
            self,
            text="  Anular Factura",
            image=ico_an,
            compound=tk.LEFT,
            font=("sans", 10, "bold"),
            bg="#EBEFF2",
            fg="#1E293B",
            relief="raised",
            bd=2,
            cursor="hand2",
            command=self.anular_seleccionada
        )
        btn_anular.place(x=500, y=535, width=200, height=38)

        btn_nota = tk.Button(
            self, text="  Nota Crédito/Débito", font=("sans", 10, "bold"),
            bg="#FEF3C7", fg="#92400E", relief="raised", bd=2,
            cursor="hand2", command=self.abrir_nota
        )
        btn_nota.place(x=260, y=535, width=225, height=38)

        ruta_ver_anul = self.rutas("icono/ojo.png")
        if not os.path.exists(ruta_ver_anul):
            ruta_ver_anul = self.rutas("icono/factura.png")

        if os.path.exists(ruta_ver_anul):
            self.images["ver_anul_ico"] = ImageTk.PhotoImage(Image.open(ruta_ver_anul).resize((20, 20), Image.Resampling.LANCZOS))
            ico_va = self.images["ver_anul_ico"]
        else:
            ico_va = None

        btn_ver_anul = tk.Button(
            self,
            text="  Ver Facturas Anuladas",
            image=ico_va,
            compound=tk.LEFT,
            font=("sans", 10, "bold"),
            bg="#EBEFF2",
            fg="#1E293B",
            relief="raised",
            bd=2,
            cursor="hand2",
            command=lambda: FacturasAnuladas(self)
        )
        btn_ver_anul.place(x=715, y=535, width=225, height=38)

    def cargar_facturas(self):
        self.facturas = []
        try:
            for factura, cliente, total, fecha, hora, cajero, medio in self.servicio_ventas.listar_ventas():
                    self.facturas.append((
                        factura, cliente, f"$ {total:,.2f}", fecha, hora,
                        cajero or "No registrado", medio or "No registrado"
                    ))
        except Exception as e:
            print("Error cargando facturas:", e)

        self.renderizar_tabla(self.facturas)

    def renderizar_tabla(self, datos):
        for r in self.tabla.get_children():
            self.tabla.delete(r)

        inicio = (self.pagina_actual - 1) * self.por_pagina
        fin = inicio + self.por_pagina
        for f in datos[inicio:fin]:
            self.tabla.insert("", tk.END, values=f)

    def pag_ant(self):
        if self.pagina_actual > 1:
            self.pagina_actual -= 1
            self.renderizar_tabla(self.facturas)

    def pag_sig(self):
        total_pags = max(1, (len(self.facturas) + self.por_pagina - 1) // self.por_pagina)
        if self.pagina_actual < total_pags:
            self.pagina_actual += 1
            self.renderizar_tabla(self.facturas)

    def anular_seleccionada(self):
        sel = self.tabla.selection()
        if not sel:
            messagebox.showwarning("Atención", "Seleccione la factura que desea anular.")
            return

        vals = self.tabla.item(sel[0], "values")
        num_factura = vals[0]
        resp = messagebox.askyesno("Confirmar Anulación", f"¿Está seguro de anular la factura #{num_factura} por {vals[2]}?\n\nLos productos se reincorporarán al stock.")
        if not resp:
            return

        anulo = getattr(self.parent, "usuario", "")
        if not anulo:
            messagebox.showerror("Sesión requerida", "No se puede anular sin un usuario autenticado.")
            return
        try:
            resultado = self.servicio_ventas.anular_venta(num_factura, anulo)
            if resultado.get("fiscal_pendiente"):
                messagebox.showwarning("Anulación local registrada", "La operación local fue confirmada; la anulación fiscal quedó pendiente de sincronización.")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo anular la factura: {e}")
            return

        messagebox.showinfo("Factura Anulada", f"Factura #{num_factura} anulada correctamente.")
        self.cargar_facturas()

    def filtrar_facturas(self):
        num_f = self.ent_num.get().strip()
        nom_c = self.ent_cli.get().strip().lower()

        filtradas = [
            f for f in self.facturas
            if (not num_f or str(f[0]) == num_f) and (not nom_c or nom_c in f[1].lower())
        ]
        self.pagina_actual = 1
        self.renderizar_tabla(filtradas)

    def abrir_nota(self):
        from nota_credito_debito import NotaCreditoDebito
        seleccion = self.tabla.selection()
        factura = self.tabla.item(seleccion[0], "values")[0] if seleccion else None
        NotaCreditoDebito(self, factura=factura)
