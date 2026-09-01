import datetime
import tkinter as tk
from tkinter import messagebox, ttk

import db_conexion as sqlite3
from window_utils import posicionar_ventana
from servicios.servicio_inventario import ServicioInventario


class Almacenes(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.servicio_inventario = ServicioInventario()
        self.title("Multi-almacén")
        posicionar_ventana(self, 850, 520, parent)
        self.resizable(False, False)
        self.configure(bg="#DDE1E5")
        self.transient(parent)
        self.grab_set()
        self.crear_interfaz()
        self.cargar_datos()

    def crear_interfaz(self):
        tk.Label(self, text="ALMACENES Y TRANSFERENCIAS", font=("sans", 21, "bold"),
                 bg="#DDE1E5", fg="#1E293B").pack(pady=(16, 10))
        marco = tk.LabelFrame(self, text="Nuevo almacén", font=("sans", 11, "bold"),
                              bg="#C6D9E3", fg="#1E293B", padx=10, pady=8)
        marco.pack(fill="x", padx=20)
        tk.Label(marco, text="Nombre:", bg="#C6D9E3", font=("sans", 10, "bold")).pack(side="left")
        self.ent_nombre = ttk.Entry(marco, width=35)
        self.ent_nombre.pack(side="left", padx=8)
        tk.Button(marco, text="Agregar", command=self.agregar, bg="#15803D", fg="white",
                  font=("sans", 10, "bold")).pack(side="left", padx=8)

        self.tabla = ttk.Treeview(self, columns=("id", "nombre", "sucursal", "estado"), show="headings")
        self.tabla.pack(fill="both", expand=True, padx=20, pady=14)
        for col, texto, ancho in (("id", "ID", 60), ("nombre", "Almacén", 300),
                                  ("sucursal", "Sucursal", 250), ("estado", "Estado", 120)):
            self.tabla.heading(col, text=texto)
            self.tabla.column(col, width=ancho, anchor="center")

        tk.Label(self, text="Seleccione un almacén para usarlo como almacén de esta instalación.",
                 bg="#DDE1E5", fg="#475569", font=("sans", 9, "italic")).pack()
        tk.Button(self, text="Usar seleccionado", command=self.seleccionar,
                  bg="#2563EB", fg="white", font=("sans", 10, "bold")).pack(pady=10, ipadx=12, ipady=4)
        tk.Button(self, text="Transferir existencias", command=self.transferir,
                  bg="#FEF3C7", fg="#92400E", font=("sans", 10, "bold")).pack(pady=(0, 14), ipadx=12, ipady=4)

    def cargar_datos(self):
        for item in self.tabla.get_children():
            self.tabla.delete(item)
        try:
            with sqlite3.connect("database.db") as conn:
                filas = conn.execute("""
                    SELECT a.id, a.nombre, COALESCE(s.nombre, ''), a.estado
                    FROM almacenes a LEFT JOIN sucursal s ON s.id = a.sucursal_id
                    ORDER BY a.id
                """).fetchall()
            for fila in filas:
                self.tabla.insert("", tk.END, values=fila)
        except sqlite3.Error as error:
            messagebox.showerror("Error", f"No se pudieron cargar los almacenes: {error}")

    def agregar(self):
        nombre = self.ent_nombre.get().strip()
        if not nombre:
            messagebox.showwarning("Atención", "Ingrese el nombre del almacén.")
            return
        try:
            self.servicio_inventario.crear_almacen(nombre)
            self.ent_nombre.delete(0, tk.END)
            self.cargar_datos()
        except sqlite3.Error as error:
            messagebox.showerror("Error", f"No se pudo crear el almacén: {error}")

    def seleccionar(self):
        seleccion = self.tabla.selection()
        if not seleccion:
            messagebox.showwarning("Atención", "Seleccione un almacén.")
            return
        almacen_id = self.tabla.item(seleccion[0], "values")[0]
        try:
            self.servicio_inventario.seleccionar_almacen(almacen_id)
            messagebox.showinfo("Almacén seleccionado", "Este almacén será utilizado por la instalación.")
        except sqlite3.Error as error:
            messagebox.showerror("Error", f"No se pudo seleccionar el almacén: {error}")

    def transferir(self):
        from transferencia_almacen import TransferenciaAlmacen
        TransferenciaAlmacen(self)
