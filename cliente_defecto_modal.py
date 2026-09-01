import os
import db_conexion as sqlite3
import sys
import tkinter as tk
from tkinter import messagebox, ttk
from PIL import Image, ImageTk
from window_utils import posicionar_ventana
from servicios.servicio_clientes import ServicioClientes

class ClienteDefectoModal(tk.Toplevel):
    def __init__(self, parent, callback_guardar=None):
        super().__init__(parent)
        self.parent = parent
        self.callback_guardar = callback_guardar
        self.title("Configurar Cliente por Defecto")
        posicionar_ventana(self, 520, 320, parent)
        self.resizable(False, False)
        self.configure(bg="#C6D9E3")
        self.transient(parent)
        self.grab_set()
        try:
            self.iconbitmap(self.rutas('icono.ico'))
        except Exception:
            pass

        self.db_name = "database.db"
        self.servicio_clientes = ServicioClientes()
        self.images = {}
        self.clientes_list = []

        self.widgets()
        self.cargar_clientes()

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
            text="CLIENTE POR DEFECTO",
            font=("sans", 18, "bold"),
            bg="#C6D9E3",
            fg="#1E293B"
        )
        lbl_title.place(relx=0.5, y=30, anchor="center")

#============== 2. CONTENIDO =======================================================================#
        frame_box = tk.LabelFrame(
            self,
            text="Configuración de Venta Rápida",
            font=("sans", 12, "bold"),
            bg="#C6D9E3",
            fg="#1E293B",
            padx=15,
            pady=10
        )
        frame_box.place(x=20, y=60, width=480, height=170)

        lbl_c = tk.Label(frame_box, text="Seleccione el Cliente Predeterminado:", font=("sans", 10, "bold"), bg="#C6D9E3", fg="#1E293B")
        lbl_c.pack(anchor="w", pady=(5, 5))

        self.cmb_cliente = ttk.Combobox(frame_box, font=("sans", 11), state="readonly")
        self.cmb_cliente.pack(fill="x", pady=5)

        self.chk_auto_var = tk.BooleanVar(value=True)
        self.chk_auto = ttk.Checkbutton(frame_box, text="Cargar automáticamente al abrir el módulo de ventas", variable=self.chk_auto_var)
        self.chk_auto.pack(anchor="w", pady=10)

#============== 3. BOTONES INFERIORES ===============================================================#
        ruta_save = self.rutas("icono/guardar.png")
        if os.path.exists(ruta_save):
            self.images["save_cd_ico"] = ImageTk.PhotoImage(Image.open(ruta_save).resize((20, 20), Image.Resampling.LANCZOS))
            ico_s = self.images["save_cd_ico"]
        else:
            ico_s = None

        btn_save = tk.Button(
            self,
            text="  Guardar",
            image=ico_s,
            compound=tk.LEFT,
            font=("sans", 11, "bold"),
            bg="#22C55E",
            fg="white",
            relief="raised",
            bd=2,
            cursor="hand2",
            command=self.guardar
        )
        btn_save.place(x=120, y=250, width=130, height=42)

        ruta_canc = self.rutas("icono/cancelar.png")
        if os.path.exists(ruta_canc):
            self.images["canc_cd_ico"] = ImageTk.PhotoImage(Image.open(ruta_canc).resize((20, 20), Image.Resampling.LANCZOS))
            ico_c = self.images["canc_cd_ico"]
        else:
            ico_c = None

        btn_canc = tk.Button(
            self,
            text="  Cancelar",
            image=ico_c,
            compound=tk.LEFT,
            font=("sans", 11, "bold"),
            bg="#EF4444",
            fg="white",
            relief="raised",
            bd=2,
            cursor="hand2",
            command=self.destroy
        )
        btn_canc.place(x=270, y=250, width=130, height=42)

    def cargar_clientes(self):
        self.clientes_datos = []
        actual_nombre = None
        try:
            rows, actual_nombre = self.servicio_clientes.listar_para_defecto()
            self.clientes_datos = [(r[0], r[1] or "") for r in rows]
        except Exception:
            pass

        self.clientes_list = [f"{n} ({c})" if c else n for n, c in self.clientes_datos]
        self.cmb_cliente["values"] = self.clientes_list

        idx = 0
        if actual_nombre:
            for i, (n, _) in enumerate(self.clientes_datos):
                if n == actual_nombre:
                    idx = i
                    break
        if self.clientes_list:
            self.cmb_cliente.current(idx)

    def guardar(self):
        idx = self.cmb_cliente.current()
        if idx < 0:
            messagebox.showwarning("Atención", "Seleccione un cliente.")
            return

        nombre, cedula = self.clientes_datos[idx]
        try:
            self.servicio_clientes.guardar_defecto(nombre, cedula)
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar el cliente por defecto: {e}")
            return

        messagebox.showinfo("Éxito", f"'{nombre}' establecido como cliente predeterminado para ventas rápidas.")
        if self.callback_guardar:
            self.callback_guardar(nombre)
        self.destroy()
