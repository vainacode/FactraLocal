import csv
import os
import db_conexion as sqlite3
import sys
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageTk
from window_utils import posicionar_ventana
from servicios.servicio_inventario import ServicioInventario

class AlertaStockBajo(tk.Toplevel):
    def __init__(self, parent, stock_min=10):
        super().__init__(parent)
        self.parent = parent
        self.stock_min = stock_min
        self.title("Alerta de Stock Bajo")
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
        self.servicio_inventario = ServicioInventario()
        self.images = {}
        self.productos_bajos = []

        self.widgets()
        self.cargar_productos_bajos()

    def rutas(self, ruta):
        try:
            rutabase = sys.__MEIPASS
        except Exception:
            rutabase = os.path.abspath(".")
        return os.path.join(rutabase, ruta)

    def widgets(self):
#============== 1. HEADER CON ICONO DE ADVERTENCIA ==================================================#
        lbl_head = tk.Label(
            self,
            text=f"⚠️  Stock Bajo - 25 productos (Stock mínimo {self.stock_min})",
            font=("sans", 18, "bold"),
            bg="#C6D9E3",
            fg="#78350F"
        )
        lbl_head.place(x=25, y=18)

#============== 2. TABLA DE PRODUCTOS ==============================================================#
        style = ttk.Style()
        style.configure("ASB.Treeview.Heading", font=("sans", 9, "bold"), background="#E0E6ED")
        style.configure("ASB.Treeview", font=("sans", 9), rowheight=24)

        cols = ("producto", "proveedor", "categoria", "stock", "precio", "codigo")
        self.tabla = ttk.Treeview(self, columns=cols, show="headings", style="ASB.Treeview")
        self.tabla.place(x=20, y=60, width=940, height=470)

        titulos = [
            ("producto", "Producto", 280),
            ("proveedor", "Proveedor", 150),
            ("categoria", "Categoría", 180),
            ("stock", "Stock", 70),
            ("precio", "Precio", 120),
            ("codigo", "Código", 100),
        ]

        for c, t, w in titulos:
            self.tabla.heading(c, text=t, anchor="center")
            self.tabla.column(c, width=w, anchor="center" if c in ("stock", "codigo") else "e" if c == "precio" else "w")

        scroll_y = ttk.Scrollbar(self, orient="vertical", command=self.tabla.yview)
        self.tabla.configure(yscrollcommand=scroll_y.set)
        scroll_y.place(x=950, y=60, height=470)

#============== 3. BARRA INFERIOR ==================================================================#
        self.lbl_tot = tk.Label(
            self,
            text="Total productos con stock bajo: 25",
            font=("sans", 11, "bold"),
            bg="#C6D9E3",
            fg="#1E293B"
        )
        self.lbl_tot.place(x=25, y=548)

        ruta_ex = self.rutas("icono/excel.png")
        if os.path.exists(ruta_ex):
            self.images["ex_asb_ico"] = ImageTk.PhotoImage(Image.open(ruta_ex).resize((22, 22), Image.Resampling.LANCZOS))
            ico_ex = self.images["ex_asb_ico"]
        else:
            ico_ex = None

        btn_ex = tk.Button(
            self,
            text="  Exportar Excel",
            image=ico_ex,
            compound=tk.LEFT,
            font=("sans", 11, "bold"),
            bg="#15803D",
            fg="white",
            relief="raised",
            bd=2,
            cursor="hand2",
            command=self.exportar_excel
        )
        btn_ex.place(x=770, y=540, width=190, height=42)

    def cargar_productos_bajos(self):
        for r in self.tabla.get_children():
            self.tabla.delete(r)

        self.productos_bajos = []
        try:
            filas = self.servicio_inventario.listar_stock_bajo()
            self.productos_bajos = [
                (n, p or "Sin proveedor", c or "Sin categoría", m, f"$ {float(co or 0):,.2f}", s)
                for n, p, c, m, co, s in filas
            ]
        except Exception as error:
            messagebox.showerror("Error", f"No se pudo cargar el inventario bajo: {error}")

        self.tabla.tag_configure("low_stk", background="#FEF9C3")

        for p in self.productos_bajos:
            self.tabla.insert("", tk.END, values=p, tags=("low_stk",))

        self.lbl_tot.config(text=f"Total productos con stock bajo: {len(self.productos_bajos)}")

    def exportar_excel(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("Archivo CSV", "*.csv")], initialfile="Alerta_Stock_Bajo.csv")
        if file_path:
            try:
                with open(file_path, mode="w", newline="", encoding="utf-8-sig") as f:
                    w = csv.writer(f)
                    w.writerow(["Producto", "Proveedor", "Categoría", "Stock", "Precio", "Código"])
                    for p in self.productos_bajos:
                        w.writerow(p)
                messagebox.showinfo("Exportar", "Alerta de stock bajo exportada a Excel correctamente.")
            except Exception as e:
                messagebox.showerror("Error", f"Error exportando: {e}")
