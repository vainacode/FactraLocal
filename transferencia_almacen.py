import datetime
import tkinter as tk
from tkinter import messagebox, ttk

import db_conexion as sqlite3
from window_utils import posicionar_ventana
from servicios.servicio_inventario import ServicioInventario


class TransferenciaAlmacen(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Transferencia entre almacenes")
        posicionar_ventana(self, 520, 350, parent)
        self.resizable(False, False)
        self.configure(bg="#DDE1E5")
        self.transient(parent)
        self.grab_set()
        self.servicio_inventario = ServicioInventario()
        self.crear_interfaz()
        self.cargar_opciones()

    def crear_interfaz(self):
        tk.Label(self, text="TRANSFERIR EXISTENCIAS", font=("sans", 19, "bold"),
                 bg="#DDE1E5", fg="#1E293B").pack(pady=(18, 14))
        marco = tk.LabelFrame(self, text="Datos de transferencia", font=("sans", 11, "bold"),
                              bg="#C6D9E3", fg="#1E293B", padx=15, pady=10)
        marco.pack(fill="x", padx=20)
        self.origen = self._campo(marco, "Origen:", 0)
        self.destino = self._campo(marco, "Destino:", 1)
        self.producto = self._campo(marco, "Producto:", 2)
        self.cantidad = ttk.Entry(marco, width=28)
        tk.Label(marco, text="Cantidad:", bg="#C6D9E3", font=("sans", 10, "bold")).grid(row=3, column=0, sticky="w", pady=6)
        self.cantidad.grid(row=3, column=1, pady=6)
        tk.Button(self, text="Ejecutar transferencia", command=self.ejecutar, bg="#2563EB", fg="white",
                  font=("sans", 10, "bold")).pack(pady=18, ipadx=15, ipady=5)

    def _campo(self, parent, texto, fila):
        tk.Label(parent, text=texto, bg="#C6D9E3", font=("sans", 10, "bold")).grid(row=fila, column=0, sticky="w", pady=6)
        combo = ttk.Combobox(parent, width=25, state="readonly")
        combo.grid(row=fila, column=1, pady=6)
        return combo

    def cargar_opciones(self):
        try:
            almacenes = [(fila[0], fila[1]) for fila in self.servicio_inventario.listar_almacenes()]
            productos = self.servicio_inventario.listar_productos_basicos()
            self.almacenes = almacenes
            self.productos_db = productos
            self.origen["values"] = [f"{i} - {n}" for i, n in almacenes]
            self.destino["values"] = [f"{i} - {n}" for i, n in almacenes]
            self.producto["values"] = [f"{i} - {n}" for i, n in productos]
            if len(almacenes) >= 2:
                self.origen.current(0); self.destino.current(1)
            if productos:
                self.producto.current(0)
        except Exception as error:
            messagebox.showerror("Error", f"No se pudieron cargar las opciones: {error}")

    def ejecutar(self):
        try:
            origen = int(self.origen.get().split(" - ")[0])
            destino = int(self.destino.get().split(" - ")[0])
            producto = int(self.producto.get().split(" - ")[0])
            cantidad = int(self.cantidad.get().strip())
            if origen == destino or cantidad <= 0:
                raise ValueError
            usuario = getattr(self.parent, "usuario", "")
            if not usuario:
                user_info = getattr(getattr(self.parent, "parent", None), "controlador", None)
                user_data = getattr(user_info, "usuario_actual", {}) or {}
                usuario = user_data.get("nombre") or user_data.get("username") or ""
            if not usuario:
                raise ValueError("No hay un usuario autenticado para registrar la transferencia.")
            self.servicio_inventario.transferir(producto, origen, destino, cantidad, usuario)
            messagebox.showinfo("Transferencia completada", "Las existencias fueron transferidas correctamente.")
            self.destroy()
        except (ValueError, TypeError):
            messagebox.showwarning("Datos inválidos", "Revise origen, destino y cantidad.")
        except Exception as error:
            messagebox.showerror("Error", f"No se pudo ejecutar la transferencia: {error}")
