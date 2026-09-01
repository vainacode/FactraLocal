import csv
import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import db_conexion as sqlite3
from window_utils import posicionar_ventana
from servicios.servicio_inventario import ServicioInventario


class KardexInventario(tk.Toplevel):
    def __init__(self, parent, producto_id=None):
        super().__init__(parent)
        self.parent = parent
        self.db_name = "database.db"
        self.servicio_inventario = ServicioInventario()
        self.producto_id = producto_id
        self.filas = []
        self.title("Kardex de inventario")
        posicionar_ventana(self, 1040, 600, parent)
        self.resizable(False, False)
        self.configure(bg="#C6D9E3")
        self.transient(parent)
        self.grab_set()
        self._crear_interfaz()
        self._cargar_productos()
        self._cargar()

    def _crear_interfaz(self):
        tk.Label(self, text="KARDEX DE INVENTARIO", font=("sans", 22, "bold"),
                 bg="#C6D9E3", fg="#1E293B").pack(pady=(15, 8))
        barra = tk.Frame(self, bg="#DDE1E5")
        barra.pack(fill="x", padx=18, pady=(0, 10), ipady=8)
        tk.Label(barra, text="Producto:", font=("sans", 10, "bold"),
                 bg="#DDE1E5").pack(side="left", padx=(12, 5))
        self.cmb_producto = ttk.Combobox(barra, state="readonly", width=42)
        self.cmb_producto.pack(side="left")
        self.cmb_producto.bind("<<ComboboxSelected>>", lambda e: self._cargar())
        tk.Button(barra, text="Refrescar", command=self._cargar,
                  bg="#EBEFF2", relief="raised").pack(side="left", padx=10)
        tk.Button(barra, text="Exportar CSV", command=self._exportar,
                  bg="#15803D", fg="white", relief="raised").pack(side="right", padx=12)

        columnas = ("fecha", "hora", "producto", "almacen", "tipo", "cantidad", "referencia", "usuario")
        self.tabla = ttk.Treeview(self, columns=columnas, show="headings")
        titulos = {
            "fecha": ("Fecha", 90), "hora": ("Hora", 75), "producto": ("Producto", 240),
            "almacen": ("Almacén", 130), "tipo": ("Movimiento", 145),
            "cantidad": ("Cantidad", 75), "referencia": ("Referencia", 105),
            "usuario": ("Usuario", 120),
        }
        for col in columnas:
            self.tabla.heading(col, text=titulos[col][0])
            self.tabla.column(col, width=titulos[col][1],
                              anchor="center" if col in ("fecha", "hora", "cantidad") else "w")
        self.tabla.pack(fill="both", expand=True, padx=18, pady=(0, 18))

    def _cargar_productos(self):
        try:
            filas = [(r[0], r[1]) for r in self.servicio_inventario.listar_productos(activos=False)]
            self.productos = filas
            self.cmb_producto["values"] = ["Todos"] + [f"{i} - {n}" for i, n in filas]
            if self.producto_id:
                for indice, (identificador, _) in enumerate(filas, start=1):
                    if identificador == self.producto_id:
                        self.cmb_producto.current(indice)
                        break
                else:
                    self.cmb_producto.current(0)
            else:
                self.cmb_producto.current(0)
        except Exception as error:
            messagebox.showerror("Error", f"No se pudieron cargar los productos: {error}")

    def _cargar(self):
        for item in self.tabla.get_children():
            self.tabla.delete(item)
        try:
            seleccion = self.cmb_producto.get()
            producto_id = None if not seleccion or seleccion == "Todos" else int(seleccion.split(" - ", 1)[0])
            filas = self.servicio_inventario.listar_kardex(producto_id)
            self.filas = filas
            for fila in filas:
                self.tabla.insert("", tk.END, values=fila)
        except Exception as error:
            messagebox.showerror("Error", f"No se pudo cargar el kardex: {error}")

    def _exportar(self):
        ruta = filedialog.asksaveasfilename(defaultextension=".csv",
                                            filetypes=[("CSV", "*.csv")],
                                            initialfile="Kardex_Inventario.csv")
        if not ruta:
            return
        try:
            with open(ruta, "w", newline="", encoding="utf-8-sig") as archivo:
                escritor = csv.writer(archivo)
                escritor.writerow(["Fecha", "Hora", "Producto", "Almacén", "Movimiento", "Cantidad", "Referencia", "Usuario"])
                escritor.writerows(self.filas)
            messagebox.showinfo("Exportación completada", "El kardex fue exportado correctamente.")
        except OSError as error:
            messagebox.showerror("Error", f"No se pudo exportar el kardex: {error}")
