import csv
import os
import db_conexion as sqlite3
import sys
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageTk
from window_utils import posicionar_ventana
from servicios.servicio_inventario import ServicioInventario

class StockMinimoIndividual(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.title("Configurar Stock Mínimo Individual")
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
        self.productos_db = []
        self.items_stock_ind = []

        self.widgets()
        self.cargar_productos_combo()
        self.cargar_tabla()

    def rutas(self, ruta):
        try:
            rutabase = sys.__MEIPASS
        except Exception:
            rutabase = os.path.abspath(".")
        return os.path.join(rutabase, ruta)

    def widgets(self):
#============== 1. ASIGNAR STOCK MÍNIMO INDIVIDUAL ==================================================#
        frame_asig = tk.LabelFrame(
            self,
            text="Asignar Stock Mínimo Individual",
            font=("sans", 13, "bold"),
            bg="#C6D9E3",
            fg="#1E293B",
            padx=15,
            pady=10
        )
        frame_asig.place(x=15, y=15, width=950, height=130)

        # Producto
        lbl_p = tk.Label(frame_asig, text="Producto:", font=("sans", 11, "bold"), bg="#C6D9E3", fg="#1E293B")
        lbl_p.place(x=10, y=10)

        self.cmb_producto = ttk.Combobox(frame_asig, font=("sans", 11))
        self.cmb_producto.place(x=130, y=8, width=570, height=30)

        ruta_rel = self.rutas("icono/actualizar1.png")
        if not os.path.exists(ruta_rel):
            ruta_rel = self.rutas("icono/actualizar.png")

        if os.path.exists(ruta_rel):
            self.images["rel_smi"] = ImageTk.PhotoImage(Image.open(ruta_rel).resize((22, 22), Image.Resampling.LANCZOS))
            ico_r = self.images["rel_smi"]
        else:
            ico_r = None

        btn_rel = tk.Button(
            frame_asig,
            text="  Refrescar",
            image=ico_r,
            compound=tk.LEFT,
            font=("sans", 10, "bold"),
            bg="#EBEFF2",
            fg="#1E293B",
            relief="raised",
            bd=2,
            cursor="hand2",
            command=self.cargar_productos_combo
        )
        btn_rel.place(x=730, y=6, width=130, height=34)

        # Stock Mínimo
        lbl_sm = tk.Label(frame_asig, text="Stock Mínimo:", font=("sans", 11, "bold"), bg="#C6D9E3", fg="#1E293B")
        lbl_sm.place(x=10, y=55)

        self.ent_stock_min = ttk.Entry(frame_asig, font=("sans", 11), justify="center")
        self.ent_stock_min.place(x=130, y=53, width=170, height=30)

        ruta_save = self.rutas("icono/guardar.png")
        if os.path.exists(ruta_save):
            self.images["save_smi"] = ImageTk.PhotoImage(Image.open(ruta_save).resize((22, 22), Image.Resampling.LANCZOS))
            ico_s = self.images["save_smi"]
        else:
            ico_s = None

        btn_save = tk.Button(
            frame_asig,
            text="  Guardar",
            image=ico_s,
            compound=tk.LEFT,
            font=("sans", 11, "bold"),
            bg="#EBEFF2",
            fg="#1E293B",
            relief="raised",
            bd=2,
            cursor="hand2",
            command=self.guardar_individual
        )
        btn_save.place(x=340, y=50, width=130, height=36)

#============== 2. PRODUCTOS CON STOCK MÍNIMO INDIVIDUAL ============================================#
        frame_tabla = tk.LabelFrame(
            self,
            text="Productos con Stock Mínimo Individual",
            font=("sans", 13, "bold"),
            bg="#C6D9E3",
            fg="#1E293B",
            padx=10,
            pady=8
        )
        frame_tabla.place(x=15, y=155, width=950, height=365)

        style = ttk.Style()
        style.configure("SMI.Treeview.Heading", font=("sans", 9, "bold"), background="#E0E6ED")
        style.configure("SMI.Treeview", font=("sans", 9), rowheight=24)

        cols = ("id", "producto", "stock_actual", "stock_minimo")
        self.tabla = ttk.Treeview(frame_tabla, columns=cols, show="headings", style="SMI.Treeview")
        self.tabla.place(x=10, y=10, width=905, height=315)

        self.tabla.heading("id", text="ID")
        self.tabla.heading("producto", text="Producto")
        self.tabla.heading("stock_actual", text="Stock Actual")
        self.tabla.heading("stock_minimo", text="Stock Mínimo")

        self.tabla.column("id", width=60, anchor="center")
        self.tabla.column("producto", width=490, anchor="w")
        self.tabla.column("stock_actual", width=170, anchor="center")
        self.tabla.column("stock_minimo", width=170, anchor="center")

        scroll_y = ttk.Scrollbar(frame_tabla, orient="vertical", command=self.tabla.yview)
        self.tabla.configure(yscrollcommand=scroll_y.set)
        scroll_y.place(x=918, y=10, height=315)

#============== 3. BOTONES INFERIORES ===============================================================#
        ruta_filt = self.rutas("icono/filtrar.png")
        if os.path.exists(ruta_filt):
            self.images["filt_smi"] = ImageTk.PhotoImage(Image.open(ruta_filt).resize((22, 22), Image.Resampling.LANCZOS))
            ico_f = self.images["filt_smi"]
        else:
            ico_f = None

        btn_filt = tk.Button(
            self,
            text="  Filtro: Inactivo",
            image=ico_f,
            compound=tk.LEFT,
            font=("sans", 10, "bold"),
            bg="#EBEFF2",
            fg="#1E293B",
            relief="raised",
            bd=2,
            cursor="hand2"
        )
        btn_filt.place(x=25, y=535, width=170, height=42)

        ruta_del = self.rutas("icono/eliminar.png")
        if os.path.exists(ruta_del):
            self.images["del_smi"] = ImageTk.PhotoImage(Image.open(ruta_del).resize((22, 22), Image.Resampling.LANCZOS))
            ico_d = self.images["del_smi"]
        else:
            ico_d = None

        btn_del = tk.Button(
            self,
            text="  Eliminar",
            image=ico_d,
            compound=tk.LEFT,
            font=("sans", 10, "bold"),
            bg="#EBEFF2",
            fg="#1E293B",
            relief="raised",
            bd=2,
            cursor="hand2",
            command=self.eliminar_seleccionado
        )
        btn_del.place(x=220, y=535, width=170, height=42)

        ruta_ex = self.rutas("icono/excel.png")
        if os.path.exists(ruta_ex):
            self.images["ex_smi"] = ImageTk.PhotoImage(Image.open(ruta_ex).resize((22, 22), Image.Resampling.LANCZOS))
            ico_x = self.images["ex_smi"]
        else:
            ico_x = None

        btn_ex = tk.Button(
            self,
            text="  Exportar",
            image=ico_x,
            compound=tk.LEFT,
            font=("sans", 10, "bold"),
            bg="#EBEFF2",
            fg="#1E293B",
            relief="raised",
            bd=2,
            cursor="hand2",
            command=self.exportar_excel
        )
        btn_ex.place(x=415, y=535, width=170, height=42)

    def cargar_productos_combo(self):
        try:
            self.productos_db = self.servicio_inventario.listar_productos_stock()
            nombres = [f"{p[0]} - {p[1]} (Stock: {p[2]})" for p in self.productos_db]
            self.cmb_producto["values"] = nombres
        except Exception as e:
            print("Error:", e)

    def cargar_tabla(self):
        for r in self.tabla.get_children():
            self.tabla.delete(r)
        try:
            filas = self.servicio_inventario.listar_stock_minimo()
            self.items_stock_ind = filas
            for fila in filas:
                self.tabla.insert("", tk.END, values=fila)
        except sqlite3.Error as error:
            messagebox.showerror("Error", f"No se pudo cargar la configuración de stock mínimo: {error}")

    def guardar_individual(self):
        sel = self.cmb_producto.get()
        sm = self.ent_stock_min.get().strip()
        if not sel or not sm:
            messagebox.showwarning("Atención", "Seleccione un producto e ingrese el stock mínimo.")
            return

        try:
            sm_val = int(sm)
            prod_id = int(sel.split(" - ")[0])
            nom = sel.split(" - ")[1].split(" (Stock:")[0]

            self.servicio_inventario.guardar_stock_minimo(prod_id, sm_val)
            self.cargar_tabla()
            messagebox.showinfo("Éxito", f"Stock mínimo individual de {sm_val} asignado a '{nom}'.")
            self.ent_stock_min.delete(0, tk.END)
        except ValueError:
            messagebox.showerror("Error", "Ingrese un valor numérico entero.")

    def eliminar_seleccionado(self):
        sel = self.tabla.selection()
        if not sel:
            messagebox.showwarning("Atención", "Seleccione un registro para eliminar.")
            return
        try:
            prod_id = self.tabla.item(sel[0], "values")[0]
            self.servicio_inventario.eliminar_stock_minimo(prod_id)
            self.cargar_tabla()
            messagebox.showinfo("Éxito", "Configuración individual eliminada.")
        except sqlite3.Error as error:
            messagebox.showerror("Error", f"No se pudo eliminar la configuración: {error}")

    def exportar_excel(self):
        destino = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("Archivo CSV", "*.csv")], initialfile="Stock_Minimo.csv")
        if not destino:
            return
        try:
            with open(destino, "w", newline="", encoding="utf-8-sig") as archivo:
                escritor = csv.writer(archivo)
                escritor.writerow(["ID Producto", "Producto", "Stock Actual", "Stock Mínimo"])
                escritor.writerows(self.items_stock_ind)
            messagebox.showinfo("Exportar", f"Datos exportados en:\n{destino}")
        except OSError as error:
            messagebox.showerror("Error", f"No se pudo exportar: {error}")
