import csv
import os
import db_conexion as sqlite3
import sys
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageTk
from window_utils import posicionar_ventana
from servicios.servicio_inventario import ServicioInventario

class ImportarProductosModal(tk.Toplevel):
    def __init__(self, parent, callback_refresh=None):
        super().__init__(parent)
        self.parent = parent
        self.callback_refresh = callback_refresh
        self.title("Importación Masiva de Productos")
        posicionar_ventana(self, 900, 560, parent)
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
        self.productos_a_importar = []
        self.servicio_inventario = ServicioInventario()

        self.widgets()

    def rutas(self, ruta):
        try:
            rutabase = sys.__MEIPASS
        except Exception:
            rutabase = os.path.abspath(".")
        return os.path.join(rutabase, ruta)

    def widgets(self):
        # Header
        lbl_titulo = tk.Label(
            self,
            text="IMPORTAR PRODUCTOS DESDE ARCHIVO (CSV / EXCEL)",
            font=("sans", 16, "bold"),
            bg="#DDE1E5",
            fg="#1E293B"
        )
        lbl_titulo.place(relx=0.5, y=25, anchor="center")

        # Barra Superior de Acciones
        frame_top = tk.Frame(self, bg="#C6D9E3", highlightbackground="#B8C4CE", highlightthickness=1)
        frame_top.place(x=20, y=50, width=860, height=55)

        ruta_folder = self.rutas("icono/excel.png")
        if os.path.exists(ruta_folder):
            self.images["excel_ico"] = ImageTk.PhotoImage(Image.open(ruta_folder).resize((22, 22), Image.Resampling.LANCZOS))
            ico_ex = self.images["excel_ico"]
        else:
            ico_ex = None

        btn_seleccionar = tk.Button(
            frame_top,
            text="  Seleccionar Archivo CSV",
            image=ico_ex,
            compound=tk.LEFT,
            font=("sans", 10, "bold"),
            bg="#22C55E",
            fg="white",
            relief="raised",
            bd=2,
            cursor="hand2",
            command=self.seleccionar_archivo
        )
        btn_seleccionar.place(x=15, y=10, width=220, height=34)

        ruta_plantilla = self.rutas("icono/plantilla.png")
        if os.path.exists(ruta_plantilla):
            self.images["plant_ico"] = ImageTk.PhotoImage(Image.open(ruta_plantilla).resize((20, 20), Image.Resampling.LANCZOS))
            ico_pl = self.images["plant_ico"]
        else:
            ico_pl = None

        btn_plantilla = tk.Button(
            frame_top,
            text="  Descargar Plantilla Ejemplo",
            image=ico_pl,
            compound=tk.LEFT,
            font=("sans", 10, "bold"),
            bg="#EBEFF2",
            fg="#1E293B",
            relief="raised",
            bd=2,
            cursor="hand2",
            command=self.descargar_plantilla
        )
        btn_plantilla.place(x=250, y=10, width=230, height=34)

        self.lbl_archivo = tk.Label(frame_top, text="Ningún archivo seleccionado", font=("sans", 9, "italic"), bg="#C6D9E3", fg="#475569")
        self.lbl_archivo.place(x=500, y=18)

        # Tabla de Vista Previa
        frame_tabla = tk.LabelFrame(
            self,
            text="Vista Previa de Productos a Importar",
            font=("sans", 10, "bold"),
            bg="#DDE1E5",
            fg="#1E293B"
        )
        frame_tabla.place(x=20, y=115, width=860, height=370)

        style = ttk.Style()
        style.configure("Imp.Treeview.Heading", font=("sans", 9, "bold"), background="#E0E6ED")
        style.configure("Imp.Treeview", font=("sans", 9), rowheight=22)

        cols = ("num", "nombre", "proveedor", "precio", "costo", "stock", "categoria")
        self.tabla = ttk.Treeview(frame_tabla, columns=cols, show="headings", style="Imp.Treeview")
        self.tabla.place(x=10, y=10, width=820, height=320)

        self.tabla.heading("num", text="#", anchor="center")
        self.tabla.heading("nombre", text="Nombre del Producto", anchor="w")
        self.tabla.heading("proveedor", text="Proveedor", anchor="w")
        self.tabla.heading("precio", text="Precio Venta (RD$)", anchor="e")
        self.tabla.heading("costo", text="Costo (RD$)", anchor="e")
        self.tabla.heading("stock", text="Stock Inicial", anchor="center")
        self.tabla.heading("categoria", text="Categoría", anchor="center")

        self.tabla.column("num", width=35, anchor="center")
        self.tabla.column("nombre", width=270, anchor="w")
        self.tabla.column("proveedor", width=140, anchor="w")
        self.tabla.column("precio", width=110, anchor="e")
        self.tabla.column("costo", width=100, anchor="e")
        self.tabla.column("stock", width=80, anchor="center")
        self.tabla.column("categoria", width=110, anchor="center")

        scroll = ttk.Scrollbar(frame_tabla, orient="vertical", command=self.tabla.yview)
        self.tabla.configure(yscrollcommand=scroll.set)
        scroll.place(x=832, y=10, height=320)

        # Barra Inferior de Confirmación
        self.lbl_resumen = tk.Label(self, text="Productos listos: 0", font=("sans", 10, "bold"), bg="#DDE1E5", fg="#1E293B")
        self.lbl_resumen.place(x=25, y=505)

        btn_confirmar = tk.Button(
            self,
            text="  Procesar e Importar al Inventario",
            font=("sans", 11, "bold"),
            bg="#0284C7",
            fg="white",
            relief="raised",
            bd=2,
            cursor="hand2",
            command=self.guardar_en_bd
        )
        btn_confirmar.place(x=540, y=498, width=240, height=42)

        btn_cancelar = tk.Button(
            self,
            text="Cerrar",
            font=("sans", 10, "bold"),
            bg="#EBEFF2",
            fg="#1E293B",
            relief="raised",
            bd=2,
            cursor="hand2",
            command=self.destroy
        )
        btn_cancelar.place(x=790, y=498, width=90, height=42)

    def descargar_plantilla(self):
        dest = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("Archivo CSV", "*.csv")],
            initialfile="plantilla_productos_repuestos.csv"
        )
        if dest:
            try:
                with open(dest, mode="w", newline="", encoding="utf-8-sig") as f:
                    writer = csv.writer(f)
                    writer.writerow(["Nombre del Producto", "Proveedor", "Precio Venta", "Costo Compra", "Stock Inicial", "Categoria", "Sucursal"])
                    writer.writerow(["Pastillas de Freno Delanteras Cerámica Toyota Corolla", "DISAUTODOM", "2450.00", "1500.00", "25", "Frenos", "Principal"])
                    writer.writerow(["Filtro de Aceite Sintético Original Honda Civic", "Autopartes del Caribe", "650.00", "380.00", "40", "Filtros", "Principal"])
                    writer.writerow(["Bujía de Iridio Laser NGK Spark Plug", "Autopartes del Caribe", "850.00", "490.00", "60", "Motor", "Principal"])
                messagebox.showinfo("Plantilla Generada", f"Plantilla descargada correctamente en:\n{dest}")
            except Exception as e:
                messagebox.showerror("Error", f"Error al generar la plantilla: {e}")

    def seleccionar_archivo(self):
        file_path = filedialog.askopenfilename(
            title="Seleccionar archivo CSV",
            filetypes=[("Archivos CSV", "*.csv"), ("Archivos de Texto", "*.txt"), ("Todos los archivos", "*.*")]
        )
        if not file_path:
            return

        self.lbl_archivo.config(text=os.path.basename(file_path))
        self.productos_a_importar.clear()
        for r in self.tabla.get_children():
            self.tabla.delete(r)

        try:
            with open(file_path, mode="r", encoding="utf-8-sig") as f:
                # Detectar delimitador (, o ;)
                first_line = f.readline()
                delimiter = ";" if ";" in first_line else ","
                f.seek(0)
                reader = csv.reader(f, delimiter=delimiter)
                headers = next(reader, None)

                idx = 1
                for row in reader:
                    if not row or not any(row):
                        continue
                    nombre = row[0].strip() if len(row) > 0 else ""
                    proveedor = row[1].strip() if len(row) > 1 else ""
                    if not proveedor:
                        raise ValueError(f"El proveedor es obligatorio para el producto '{nombre}'.")
                    try:
                        precio = float(row[2].strip().replace("RD$", "").replace("$", "").replace(",", "")) if len(row) > 2 else 0.0
                    except Exception:
                        precio = 0.0
                    try:
                        costo = float(row[3].strip().replace("RD$", "").replace("$", "").replace(",", "")) if len(row) > 3 else 0.0
                    except Exception:
                        costo = 0.0
                    try:
                        stock = int(float(row[4].strip())) if len(row) > 4 else 10
                    except Exception:
                        stock = 10
                    categoria = row[5].strip() if len(row) > 5 and row[5].strip() else "Repuestos"
                    sucursal = row[6].strip() if len(row) > 6 and row[6].strip() else "Principal"

                    if nombre:
                        item = (idx, nombre, proveedor, precio, costo, stock, categoria, sucursal)
                        self.productos_a_importar.append(item)
                        self.tabla.insert("", tk.END, values=(idx, nombre, proveedor, f"RD$ {precio:,.2f}", f"RD$ {costo:,.2f}", stock, categoria))
                        idx += 1

            self.lbl_resumen.config(text=f"Productos listos para importar: {len(self.productos_a_importar)}")
            if not self.productos_a_importar:
                messagebox.showwarning("Atención", "No se encontraron filas con datos válidos en el archivo.")
        except Exception as e:
            messagebox.showerror("Error al leer archivo", f"No se pudo leer el archivo seleccionado:\n{e}")

    def guardar_en_bd(self):
        if not self.productos_a_importar:
            messagebox.showwarning("Atención", "Por favor seleccione primero un archivo CSV con productos.")
            return

        if not messagebox.askyesno("Confirmar Importación", f"¿Desea importar {len(self.productos_a_importar)} productos a la base de datos?"):
            return

        try:
            foto_default = "productos/coca_cola_PNG8914.png"
            insertados = len(self.productos_a_importar)
            self.servicio_inventario.importar_productos(self.productos_a_importar, foto_default)

            messagebox.showinfo("Éxito", f"¡Se importaron {insertados} productos exitosamente a la base de datos!")
            if self.callback_refresh:
                self.callback_refresh()
            self.destroy()
        except Exception as e:
            messagebox.showerror("Error de Base de Datos", f"Error al insertar productos: {e}")
