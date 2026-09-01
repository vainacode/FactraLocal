import csv
import datetime
import os
import db_conexion as sqlite3
import sys
import tkinter as tk
from servicios.servicio_reportes import ServicioReportes
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageTk
from window_utils import posicionar_ventana

class ReporteVentasProducto(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.title("Reporte de Ventas por Producto - La Casa de los Repuestos")
        posicionar_ventana(self, 1000, 600, parent)
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

        self.widgets()
        self.cargar_datos()

    def rutas(self, ruta):
        try:
            rutabase = sys.__MEIPASS
        except Exception:
            rutabase = os.path.abspath(".")
        return os.path.join(rutabase, ruta)

    def widgets(self):
        # Header
        lbl_title = tk.Label(
            self,
            text="REPORTE DE VENTAS POR PRODUCTO",
            font=("sans", 22, "bold"),
            bg="#C6D9E3",
            fg="#1E293B"
        )
        lbl_title.place(relx=0.5, y=30, anchor="center")

        # Filtros
        frame_top = tk.Frame(self, bg="#DDE1E5", highlightbackground="#B8C4CE", highlightthickness=1)
        frame_top.place(x=20, y=65, width=960, height=50)

        tk.Label(frame_top, text="Buscar:", font=("sans", 10, "bold"), bg="#DDE1E5", fg="#1E293B").place(x=15, y=14)
        self.ent_buscar = ttk.Entry(frame_top, font=("sans", 10))
        self.ent_buscar.place(x=70, y=11, width=220, height=28)
        self.ent_buscar.bind("<KeyRelease>", lambda e: self.cargar_datos())

        tk.Label(frame_top, text="Ordenar:", font=("sans", 10, "bold"), bg="#DDE1E5", fg="#1E293B").place(x=310, y=14)
        self.cmb_orden = ttk.Combobox(frame_top, values=["Más Vendidos", "Mayor Ingreso", "Mayor Margen", "Nombre A-Z"], font=("sans", 10), state="readonly")
        self.cmb_orden.set("Más Vendidos")
        self.cmb_orden.place(x=375, y=11, width=150, height=28)
        self.cmb_orden.bind("<<ComboboxSelected>>", lambda e: self.cargar_datos())

        # Botón Exportar CSV
        ruta_ex = self.rutas("icono/excel.png")
        if os.path.exists(ruta_ex):
            self.images["ex_ico"] = ImageTk.PhotoImage(Image.open(ruta_ex).resize((20, 20), Image.Resampling.LANCZOS))
            ico_ex = self.images["ex_ico"]
        else:
            ico_ex = None

        btn_exportar = tk.Button(
            frame_top,
            text="  Exportar CSV",
            image=ico_ex,
            compound=tk.LEFT,
            font=("sans", 10, "bold"),
            bg="#22C55E",
            fg="white",
            relief="raised",
            bd=2,
            cursor="hand2",
            command=self.exportar_csv
        )
        btn_exportar.place(x=820, y=9, width=125, height=32)

        # Tabla
        style = ttk.Style()
        style.configure("VP.Treeview.Heading", font=("sans", 10, "bold"), background="#E0E6ED")
        style.configure("VP.Treeview", font=("sans", 9), rowheight=24)

        cols = ("ranking", "producto", "unidades", "total_ingresos", "costo_total", "ganancia", "margen")
        self.tabla = ttk.Treeview(self, columns=cols, show="headings", style="VP.Treeview")
        self.tabla.place(x=20, y=125, width=960, height=370)

        self.tabla.heading("ranking", text="#", anchor="center")
        self.tabla.heading("producto", text="Repuesto / Artículo", anchor="w")
        self.tabla.heading("unidades", text="Cant. Vendida", anchor="center")
        self.tabla.heading("total_ingresos", text="Total Ingresos (RD$)", anchor="e")
        self.tabla.heading("costo_total", text="Costo Total (RD$)", anchor="e")
        self.tabla.heading("ganancia", text="Ganancia Neta (RD$)", anchor="e")
        self.tabla.heading("margen", text="Margen (%)", anchor="center")

        self.tabla.column("ranking", width=40, anchor="center")
        self.tabla.column("producto", width=340, anchor="w")
        self.tabla.column("unidades", width=100, anchor="center")
        self.tabla.column("total_ingresos", width=140, anchor="e")
        self.tabla.column("costo_total", width=130, anchor="e")
        self.tabla.column("ganancia", width=130, anchor="e")
        self.tabla.column("margen", width=80, anchor="center")

        # Barra Inferior
        frame_bot = tk.Frame(self, bg="#CAD8E2", highlightbackground="#A9BFCE", highlightthickness=1)
        frame_bot.place(x=20, y=505, width=960, height=75)

        self.lbl_tot_items = tk.Label(frame_bot, text="Repuestos Listados: 0", font=("sans", 11, "bold"), bg="#CAD8E2", fg="#1E293B")
        self.lbl_tot_items.place(x=30, y=25)

        self.lbl_tot_unidades = tk.Label(frame_bot, text="Total Unidades: 0", font=("sans", 11, "bold"), bg="#CAD8E2", fg="#1E293B")
        self.lbl_tot_unidades.place(x=320, y=25)

        self.lbl_gran_total = tk.Label(frame_bot, text="TOTAL RECAUDADO: RD$ 0.00", font=("sans", 13, "bold"), bg="#CAD8E2", fg="#166534")
        self.lbl_gran_total.place(x=600, y=25)

    def cargar_datos(self):
        for r in self.tabla.get_children():
            self.tabla.delete(r)

        filtro = self.ent_buscar.get().strip().lower()
        orden = self.cmb_orden.get()

        prods_dict = {}
        try:
            for prod, cant, tot, cst in ServicioReportes().ventas_producto():
                    prod_nom = prod or "Repuesto General"
                    if prod_nom not in prods_dict:
                        prods_dict[prod_nom] = {"unidades": 0, "ingresos": 0.0, "costos": 0.0}
                    c = int(cant or 1)
                    t = float(tot or 0.0)
                    cs = float(cst or 0.0) * c
                    prods_dict[prod_nom]["unidades"] += c
                    prods_dict[prod_nom]["ingresos"] += t
                    prods_dict[prod_nom]["costos"] += cs
        except Exception as e:
            print("Error cargando ventas por producto:", e)

        lista = []
        for p, d in prods_dict.items():
            if filtro and filtro not in p.lower():
                continue
            gan = d["ingresos"] - d["costos"]
            mrg = ((gan / d["ingresos"]) * 100) if d["ingresos"] > 0 else 0.0
            lista.append({
                "producto": p,
                "unidades": d["unidades"],
                "ingresos": d["ingresos"],
                "costos": d["costos"],
                "ganancia": gan,
                "margen": mrg
            })

        if orden == "Más Vendidos":
            lista.sort(key=lambda x: x["unidades"], reverse=True)
        elif orden == "Mayor Ingreso":
            lista.sort(key=lambda x: x["ingresos"], reverse=True)
        elif orden == "Mayor Margen":
            lista.sort(key=lambda x: x["margen"], reverse=True)
        elif orden == "Nombre A-Z":
            lista.sort(key=lambda x: x["producto"].lower())

        tot_u = 0
        tot_ing = 0.0
        for i, item in enumerate(lista, 1):
            tot_u += item["unidades"]
            tot_ing += item["ingresos"]
            self.tabla.insert("", tk.END, values=(
                str(i),
                f"  {item['producto']}",
                str(item["unidades"]),
                f"RD$ {item['ingresos']:,.2f}",
                f"RD$ {item['costos']:,.2f}",
                f"RD$ {item['ganancia']:,.2f}",
                f"{item['margen']:,.1f} %"
            ))

        self.lbl_tot_items.config(text=f"Repuestos Listados: {len(lista)}")
        self.lbl_tot_unidades.config(text=f"Total Unidades: {tot_u}")
        self.lbl_gran_total.config(text=f"TOTAL RECAUDADO: RD$ {tot_ing:,.2f}")

    def exportar_csv(self):
        dest = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("Archivo CSV", "*.csv")],
            initialfile="Reporte_Ventas_Por_Producto.csv"
        )
        if dest:
            try:
                with open(dest, mode="w", newline="", encoding="utf-8-sig") as f:
                    writer = csv.writer(f)
                    writer.writerow(["#", "Repuesto / Artículo", "Cant. Vendida", "Total Ingresos (RD$)", "Costo Total (RD$)", "Ganancia Neta (RD$)", "Margen (%)"])
                    for child in self.tabla.get_children():
                        writer.writerow(self.tabla.item(child, "values"))
                messagebox.showinfo("Exportación", f"Reporte exportado exitosamente a:\n{dest}")
            except Exception as e:
                messagebox.showerror("Error", f"Error exportando reporte: {e}")
