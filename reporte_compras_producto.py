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

class ReporteComprasProducto(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.title("Reporte de Compras por Producto - La Casa de los Repuestos")
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
            text="REPORTE DE COMPRAS Y PEDIDOS POR PRODUCTO",
            font=("sans", 20, "bold"),
            bg="#C6D9E3",
            fg="#1E293B"
        )
        lbl_title.place(relx=0.5, y=30, anchor="center")

        # Filtros
        frame_top = tk.Frame(self, bg="#DDE1E5", highlightbackground="#B8C4CE", highlightthickness=1)
        frame_top.place(x=20, y=65, width=940, height=50)

        tk.Label(frame_top, text="Buscar:", font=("sans", 10, "bold"), bg="#DDE1E5", fg="#1E293B").place(x=15, y=14)
        self.ent_buscar = ttk.Entry(frame_top, font=("sans", 10))
        self.ent_buscar.place(x=70, y=11, width=240, height=28)
        self.ent_buscar.bind("<KeyRelease>", lambda e: self.cargar_datos())

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
        btn_exportar.place(x=800, y=9, width=125, height=32)

        # Tabla
        style = ttk.Style()
        style.configure("CP.Treeview.Heading", font=("sans", 10, "bold"), background="#E0E6ED")
        style.configure("CP.Treeview", font=("sans", 9), rowheight=24)

        cols = ("id", "producto", "proveedor", "costo_unit", "stock_actual", "categoria")
        self.tabla = ttk.Treeview(self, columns=cols, show="headings", style="CP.Treeview")
        self.tabla.place(x=20, y=125, width=940, height=370)

        self.tabla.heading("id", text="#", anchor="center")
        self.tabla.heading("producto", text="Repuesto / Artículo", anchor="w")
        self.tabla.heading("proveedor", text="Proveedor Principal", anchor="w")
        self.tabla.heading("costo_unit", text="Costo de Compra (RD$)", anchor="e")
        self.tabla.heading("stock_actual", text="Stock Disponible", anchor="center")
        self.tabla.heading("categoria", text="Categoría", anchor="center")

        self.tabla.column("id", width=40, anchor="center")
        self.tabla.column("producto", width=330, anchor="w")
        self.tabla.column("proveedor", width=180, anchor="w")
        self.tabla.column("costo_unit", width=160, anchor="e")
        self.tabla.column("stock_actual", width=110, anchor="center")
        self.tabla.column("categoria", width=120, anchor="center")

        # Barra Inferior
        frame_bot = tk.Frame(self, bg="#CAD8E2", highlightbackground="#A9BFCE", highlightthickness=1)
        frame_bot.place(x=20, y=505, width=940, height=75)

        self.lbl_tot_prods = tk.Label(frame_bot, text="Repuestos en Catálogo: 0", font=("sans", 11, "bold"), bg="#CAD8E2", fg="#1E293B")
        self.lbl_tot_prods.place(x=30, y=25)

        self.lbl_gran_inversion = tk.Label(frame_bot, text="VALOR TOTAL EN COMPRAS: RD$ 0.00", font=("sans", 13, "bold"), bg="#CAD8E2", fg="#166534")
        self.lbl_gran_inversion.place(x=540, y=25)

    def cargar_datos(self):
        for r in self.tabla.get_children():
            self.tabla.delete(r)

        filtro = self.ent_buscar.get().strip().lower()

        try:
            rows = ServicioReportes().inventario_compras()
        except Exception as e:
            rows = []
            print("Error cargando compras por producto:", e)

        tot_inversion = 0.0
        cant_mostrada = 0

        for r in rows:
            pid, nom, prov, cst, stk, cat = r
            if filtro and filtro not in nom.lower() and filtro not in (prov or "").lower():
                continue
            costo_val = float(cst or 0.0)
            stock_val = int(stk or 0)
            tot_inversion += (costo_val * stock_val)
            cant_mostrada += 1

            self.tabla.insert("", tk.END, values=(
                str(pid),
                f"  {nom}",
                prov or "Sin proveedor",
                f"RD$ {costo_val:,.2f}",
                str(stock_val),
                cat or "Repuestos"
            ))

        self.lbl_tot_prods.config(text=f"Repuestos Listados: {cant_mostrada}")
        self.lbl_gran_inversion.config(text=f"VALOR EN INVENTARIO: RD$ {tot_inversion:,.2f}")

    def exportar_csv(self):
        dest = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("Archivo CSV", "*.csv")],
            initialfile="Reporte_Compras_Por_Producto.csv"
        )
        if dest:
            try:
                with open(dest, mode="w", newline="", encoding="utf-8-sig") as f:
                    writer = csv.writer(f)
                    writer.writerow(["#", "Repuesto / Artículo", "Proveedor", "Costo de Compra (RD$)", "Stock", "Categoría"])
                    for child in self.tabla.get_children():
                        writer.writerow(self.tabla.item(child, "values"))
                messagebox.showinfo("Exportación", f"Reporte exportado exitosamente a:\n{dest}")
            except Exception as e:
                messagebox.showerror("Error", f"Error exportando reporte: {e}")
