import csv
import os
import db_conexion as sqlite3
import sys
import tkinter as tk
from servicios.servicio_reportes import ServicioReportes
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageTk
from window_utils import posicionar_ventana

class ReporteCostoInventario(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.title("Reporte costo total inventario")
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
        self.productos_costo = []

        self.widgets()
        self.generar_reporte()

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
            text="Reporte de Costo Total de Inventario",
            font=("sans", 24, "bold"),
            bg="#C6D9E3",
            fg="#1E293B"
        )
        lbl_title.place(relx=0.5, y=25, anchor="center")

#============== 2. PANEL IZQUIERDO: RESUMEN =======================================================#
        frame_res = tk.LabelFrame(
            self,
            text="Resumen",
            font=("sans", 13, "bold"),
            bg="#DDE1E5",
            fg="#1E293B",
            padx=12,
            pady=10
        )
        frame_res.place(x=15, y=60, width=355, height=350)

        # Botón Generar Reporte
        ruta_rep = self.rutas("icono/reporte1.png")
        if not os.path.exists(ruta_rep):
            ruta_rep = self.rutas("icono/reporte.png")

        if os.path.exists(ruta_rep):
            self.images["rep_rci_ico"] = ImageTk.PhotoImage(Image.open(ruta_rep).resize((22, 22), Image.Resampling.LANCZOS))
            ico_r = self.images["rep_rci_ico"]
        else:
            ico_r = None

        btn_gen = tk.Button(
            frame_res,
            text="  Generar Reporte",
            image=ico_r,
            compound=tk.LEFT,
            font=("sans", 11, "bold"),
            bg="#EBEFF2",
            fg="#1E293B",
            relief="raised",
            bd=2,
            cursor="hand2",
            command=self.generar_reporte
        )
        btn_gen.place(relx=0.5, y=35, width=190, height=44, anchor="center")

        # Tarjeta Costo Total Inventario
        frame_card_tot = tk.Frame(frame_res, bg="white", highlightbackground="#B8C4CE", highlightthickness=1)
        frame_card_tot.place(x=10, y=80, width=305, height=180)

        lbl_ct_tag = tk.Label(frame_card_tot, text="Costo Total Inventario", font=("sans", 10, "bold"), bg="white", fg="#475569")
        lbl_ct_tag.place(relx=0.5, y=20, anchor="center")

        self.lbl_gran_costo = tk.Label(frame_card_tot, text="$ 0.00", font=("sans", 14, "bold"), bg="white", fg="#1E293B")
        self.lbl_gran_costo.place(relx=0.5, y=55, anchor="center")

        # Nota al pie
        lbl_nota = tk.Label(
            self,
            text="El reporte de costo total de inventario muestra el costo de\nadquisición de todos los productos en stock",
            font=("sans", 9, "italic"),
            bg="#C6D9E3",
            fg="#475569",
            justify="center"
        )
        lbl_nota.place(x=15, y=425)

        # Botón Exportar a Excel
        ruta_ex = self.rutas("icono/excel.png")
        if os.path.exists(ruta_ex):
            self.images["ex_rci_ico"] = ImageTk.PhotoImage(Image.open(ruta_ex).resize((22, 22), Image.Resampling.LANCZOS))
            ico_x = self.images["ex_rci_ico"]
        else:
            ico_x = None

        btn_ex = tk.Button(
            self,
            text="  Exportar a Excel",
            image=ico_x,
            compound=tk.LEFT,
            font=("sans", 11, "bold"),
            bg="#15803D",
            fg="white",
            relief="raised",
            bd=2,
            cursor="hand2",
            command=self.exportar_excel
        )
        btn_ex.place(x=90, y=490, width=200, height=44)

#============== 3. PANEL DERECHO: TABLA DE PRODUCTOS ===============================================#
        style = ttk.Style()
        style.configure("RCI.Treeview.Heading", font=("sans", 9, "bold"), background="#E0E6ED")
        style.configure("RCI.Treeview", font=("sans", 9), rowheight=24)

        cols = ("producto", "costo_u", "stock", "total")
        self.tabla = ttk.Treeview(self, columns=cols, show="headings", style="RCI.Treeview")
        self.tabla.place(x=390, y=60, width=570, height=480)

        titulos = [
            ("producto", "Producto", 270),
            ("costo_u", "Costo Unit.", 100),
            ("stock", "Stock", 70),
            ("total", "Total", 110),
        ]

        for c, t, w in titulos:
            self.tabla.heading(c, text=t, anchor="center")
            self.tabla.column(c, width=w, anchor="center" if c == "stock" else "e" if c in ("costo_u", "total") else "w")

        scroll_y = ttk.Scrollbar(self, orient="vertical", command=self.tabla.yview)
        self.tabla.configure(yscrollcommand=scroll_y.set)
        scroll_y.place(x=945, y=60, height=480)

    def generar_reporte(self):
        for r in self.tabla.get_children():
            self.tabla.delete(r)

        self.productos_costo = []
        try:
            filas = [(r[1], r[3], r[2], r[3] * r[2]) for r in ServicioReportes().stock_valorizado()]
            self.productos_costo = [
                (nombre, f"$ {float(costo or 0):,.2f}", int(stock or 0), f"$ {float(total or 0):,.2f}")
                for nombre, costo, stock, total in filas
            ]
            total = sum(float(total or 0) for _, _, _, total in filas)
            self.lbl_gran_costo.config(text=f"$ {total:,.2f}")
        except Exception as error:
            messagebox.showerror("Error", f"No se pudo generar el reporte: {error}")

        for p in self.productos_costo:
            self.tabla.insert("", tk.END, values=p)

    def exportar_excel(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("Archivo CSV", "*.csv")], initialfile="Reporte_Costo_Inventario.csv")
        if file_path:
            try:
                with open(file_path, mode="w", newline="", encoding="utf-8-sig") as f:
                    w = csv.writer(f)
                    w.writerow(["Producto", "Costo Unit.", "Stock", "Total"])
                    for p in self.productos_costo:
                        w.writerow(p)
                messagebox.showinfo("Exportar", "Reporte de costo total de inventario exportado exitosamente.")
            except Exception as e:
                messagebox.showerror("Error", f"Error exportando: {e}")
