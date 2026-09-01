import csv
import os
import sys
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageTk
from factura_detalle import FacturaDetalle
from window_utils import posicionar_ventana
from servicios.servicio_ventas import ServicioVentas

class VentasRealizadas(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.title("Ventas Realizadas")
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
        self.ventas = []
        self.pagina_actual = 1
        self.por_pagina = 14

        self.widgets()
        self.cargar_ventas()

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
            text="Ventas Realizadas",
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
            self.images["filtro_vr"] = ImageTk.PhotoImage(img_f)
            ico_f = self.images["filtro_vr"]
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
            command=self.filtrar_ventas
        )
        btn_f.place(x=760, y=50, width=105, height=34)

#============== 3. TABLA DE VENTAS =================================================================#
        style = ttk.Style()
        style.configure("VR.Treeview.Heading", font=("sans", 9, "bold"), background="#E0E6ED")
        style.configure("VR.Treeview", font=("sans", 9), rowheight=24)

        cols = ("factura", "cliente", "total", "fecha", "hora", "cajero", "medio_pago")
        self.tabla = ttk.Treeview(self, columns=cols, show="headings", style="VR.Treeview")
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

        self.tabla.bind("<Double-1>", self.al_hacer_doble_click)

#============== 4. BARRA INFERIOR ==================================================================#
        ruta_ant = self.rutas("icono/izquierda.png")
        if os.path.exists(ruta_ant):
            img_a = Image.open(ruta_ant).resize((18, 18), Image.Resampling.LANCZOS)
            self.images["ant_vr"] = ImageTk.PhotoImage(img_a)
            ico_a = self.images["ant_vr"]
        else:
            ico_a = None

        btn_ant = tk.Button(self, text="  Anterior", image=ico_a, compound=tk.LEFT, font=("sans", 10, "bold"), bg="#EBEFF2", fg="#1E293B", relief="raised", bd=2, cursor="hand2", command=self.pag_anterior)
        btn_ant.place(x=20, y=535, width=105, height=36)

        ruta_sig = self.rutas("icono/derecha.png")
        if os.path.exists(ruta_sig):
            img_s = Image.open(ruta_sig).resize((18, 18), Image.Resampling.LANCZOS)
            self.images["sig_vr"] = ImageTk.PhotoImage(img_s)
            ico_s = self.images["sig_vr"]
        else:
            ico_s = None

        btn_sig = tk.Button(self, text="  Siguiente", image=ico_s, compound=tk.RIGHT, font=("sans", 10, "bold"), bg="#EBEFF2", fg="#1E293B", relief="raised", bd=2, cursor="hand2", command=self.pag_siguiente)
        btn_sig.place(x=135, y=535, width=105, height=36)

        lbl_hint = tk.Label(self, text="Doble click en una factura para ver el detalle", font=("sans", 10, "bold"), bg="#C6D9E3", fg="#1E293B")
        lbl_hint.place(x=290, y=542)

        ruta_ex = self.rutas("icono/excel.png")
        if os.path.exists(ruta_ex):
            img_x = Image.open(ruta_ex).resize((20, 20), Image.Resampling.LANCZOS)
            self.images["ex_vr"] = ImageTk.PhotoImage(img_x)
            ico_x = self.images["ex_vr"]
        else:
            ico_x = None

        btn_gen = tk.Button(self, text="  General", image=ico_x, compound=tk.LEFT, font=("sans", 10, "bold"), bg="#EBEFF2", fg="#1E293B", relief="raised", bd=2, cursor="hand2", command=self.exportar_general)
        btn_gen.place(x=655, y=535, width=130, height=36)

        btn_det = tk.Button(self, text="  Detalle", image=ico_x, compound=tk.LEFT, font=("sans", 10, "bold"), bg="#EBEFF2", fg="#1E293B", relief="raised", bd=2, cursor="hand2", command=self.exportar_detalle)
        btn_det.place(x=805, y=535, width=130, height=36)

    def cargar_ventas(self):
        try:
            rows = self.servicio_ventas.listar_ventas()
            self.ventas = []
            for r in rows:
                    self.ventas.append((r[0], r[1], f"$ {r[2] or 0:,.2f}", r[3], r[4], r[5] or "", r[6]))

            self.renderizar_tabla()
        except Exception as e:
            print("Error cargando ventas:", e)

    def renderizar_tabla(self):
        for r in self.tabla.get_children():
            self.tabla.delete(r)

        inicio = (self.pagina_actual - 1) * self.por_pagina
        fin = inicio + self.por_pagina
        for v in self.ventas[inicio:fin]:
            self.tabla.insert("", tk.END, values=v)

    def al_hacer_doble_click(self, event=None):
        sel = self.tabla.selection()
        if not sel:
            return
        vals = self.tabla.item(sel[0], "values")
        if vals:
            fac_id = vals[0]
            FacturaDetalle(self, factura_id=fac_id)

    def filtrar_ventas(self):
        num_f = self.ent_num.get().strip()
        nom_c = self.ent_cli.get().strip().lower()

        filtradas = []
        for v in self.ventas:
            match_num = not num_f or str(v[0]) == num_f
            match_nom = not nom_c or nom_c in v[1].lower()
            if match_num and match_nom:
                filtradas.append(v)

        for r in self.tabla.get_children():
            self.tabla.delete(r)
        for v in filtradas:
            self.tabla.insert("", tk.END, values=v)

    def pag_anterior(self):
        if self.pagina_actual > 1:
            self.pagina_actual -= 1
            self.renderizar_tabla()

    def pag_siguiente(self):
        total_pags = max(1, (len(self.ventas) + self.por_pagina - 1) // self.por_pagina)
        if self.pagina_actual < total_pags:
            self.pagina_actual += 1
            self.renderizar_tabla()

    def exportar_general(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("Archivo CSV", "*.csv")], initialfile="Ventas_Realizadas.csv")
        if file_path:
            try:
                with open(file_path, mode="w", newline="", encoding="utf-8-sig") as f:
                    w = csv.writer(f)
                    w.writerow(["Factura", "Cliente", "Total", "Fecha", "Hora", "Cajero", "Medio Pago"])
                    for v in self.ventas:
                        w.writerow(v)
                messagebox.showinfo("Exportar", "Ventas exportadas exitosamente.")
            except Exception as e:
                messagebox.showerror("Error", f"Error exportando: {e}")

    def exportar_detalle(self):
        destino = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("Archivo CSV", "*.csv")],
            initialfile="Detalle_Ventas.csv",
        )
        if not destino:
            return
        try:
            with open(destino, "w", newline="", encoding="utf-8-sig") as archivo:
                writer = csv.writer(archivo)
                writer.writerow(["Factura", "Cliente", "Producto", "Precio", "Cantidad", "Total", "Fecha", "Hora", "Cajero", "Medio Pago"])
                rows = self.servicio_ventas.listar_detalle_ventas()
                writer.writerows(rows)
            messagebox.showinfo("Exportar detalle", f"Detalle exportado en:\n{destino}")
        except Exception as error:
            messagebox.showerror("Error", f"No se pudo exportar el detalle: {error}")
