import os
import sys
import tkinter as tk
from tkinter import messagebox, ttk
from PIL import Image, ImageTk
from window_utils import posicionar_ventana
from servicios.servicio_inventario import ServicioInventario

class BajasProductos(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.title("Registro de Bajas y Mermas de Productos")
        posicionar_ventana(self, 980, 600, parent)
        self.resizable(False, False)
        self.configure(bg="#DDE1E5")
        self.transient(parent)
        self.grab_set()
        try:
            self.iconbitmap(self.rutas('icono.ico'))
        except Exception:
            pass

        self.db_name = "database.db"
        self.servicio_inventario = ServicioInventario()
        self.images = {}
        self.bajas = []
        self.productos_db = []

        self.widgets()
        self.cargar_productos_combo()
        self.cargar_bajas()

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
            text="BAJAS Y PÉRDIDAS DE PRODUCTOS",
            font=("sans", 24, "bold"),
            bg="#DDE1E5",
            fg="#1E293B"
        )
        lbl_title.place(relx=0.5, y=25, anchor="center")

#============== 2. PANEL IZQUIERDO: FORMULARIO =====================================================#
        frame_form = tk.LabelFrame(
            self,
            text="Registrar Baja de Stock",
            font=("sans", 13, "bold"),
            bg="#C6D9E3",
            fg="#1E293B",
            padx=15,
            pady=10
        )
        frame_form.place(x=20, y=60, width=390, height=515)

        # Producto
        lbl_p = tk.Label(frame_form, text="Producto:", font=("sans", 10, "bold"), bg="#C6D9E3", fg="#1E293B")
        lbl_p.place(x=10, y=5)

        self.cmb_producto = ttk.Combobox(frame_form, font=("sans", 10))
        self.cmb_producto.place(x=10, y=28, width=335, height=28)

        # Cantidad
        lbl_c = tk.Label(frame_form, text="Cantidad a Retirar:", font=("sans", 10, "bold"), bg="#C6D9E3", fg="#1E293B")
        lbl_c.place(x=10, y=65)

        self.ent_cantidad = ttk.Entry(frame_form, font=("sans", 11), justify="center")
        self.ent_cantidad.place(x=10, y=88, width=335, height=28)

        # Motivo
        lbl_m = tk.Label(frame_form, text="Motivo de la Baja:", font=("sans", 10, "bold"), bg="#C6D9E3", fg="#1E293B")
        lbl_m.place(x=10, y=125)

        self.cmb_motivo = ttk.Combobox(frame_form, values=["Vencimiento", "Daño / Avería", "Pérdida / Hurto", "Uso Interno", "Ajuste Inventario"], font=("sans", 10), state="readonly")
        self.cmb_motivo.current(0)
        self.cmb_motivo.place(x=10, y=148, width=335, height=28)

        # Observación
        lbl_obs = tk.Label(frame_form, text="Observaciones:", font=("sans", 10, "bold"), bg="#C6D9E3", fg="#1E293B")
        lbl_obs.place(x=10, y=185)

        self.txt_obs = tk.Text(frame_form, font=("sans", 10), wrap="word", relief="solid", bd=1)
        self.txt_obs.place(x=10, y=208, width=335, height=120)

        # Botón Registrar Baja
        ruta_reg = self.rutas("icono/eliminar.png")
        if os.path.exists(ruta_reg):
            self.images["reg_baja_ico"] = ImageTk.PhotoImage(Image.open(ruta_reg).resize((22, 22), Image.Resampling.LANCZOS))
            ico_r = self.images["reg_baja_ico"]
        else:
            ico_r = None

        btn_reg = tk.Button(
            frame_form,
            text="  Registrar Baja de Stock",
            image=ico_r,
            compound=tk.LEFT,
            font=("sans", 11, "bold"),
            bg="#EF4444",
            fg="white",
            relief="raised",
            bd=2,
            cursor="hand2",
            command=self.registrar_baja
        )
        btn_reg.place(x=10, y=360, width=335, height=44)

#============== 3. PANEL DERECHO: HISTORIAL =========================================================#
        style = ttk.Style()
        style.configure("BAJ.Treeview.Heading", font=("sans", 9, "bold"), background="#E0E6ED")
        style.configure("BAJ.Treeview", font=("sans", 9), rowheight=24)

        cols = ("id", "producto", "cantidad", "motivo", "fecha", "responsable")
        self.tabla = ttk.Treeview(self, columns=cols, show="headings", style="BAJ.Treeview")
        self.tabla.place(x=430, y=65, width=530, height=510)

        titulos = [
            ("id", "ID", 40),
            ("producto", "Producto", 170),
            ("cantidad", "Cant", 50),
            ("motivo", "Motivo", 110),
            ("fecha", "Fecha", 90),
            ("responsable", "Responsable", 90),
        ]

        for c, t, w in titulos:
            self.tabla.heading(c, text=t, anchor="center")
            self.tabla.column(c, width=w, anchor="center" if c in ("id", "cantidad", "fecha", "responsable") else "w")

        scroll_y = ttk.Scrollbar(self, orient="vertical", command=self.tabla.yview)
        self.tabla.configure(yscrollcommand=scroll_y.set)
        scroll_y.place(x=945, y=65, height=510)

    def cargar_productos_combo(self):
        try:
            self.productos_db = self.servicio_inventario.listar_productos_basicos()
            self.productos_db = [self.servicio_inventario.obtener_producto(p[0]) for p in self.productos_db]
            nombres = [f"{p[0]} - {p[1]} (Stock: {p[5]})" for p in self.productos_db]
            self.cmb_producto["values"] = nombres
            if nombres:
                self.cmb_producto.current(0)
        except Exception:
            pass

    def cargar_bajas(self):
        for r in self.tabla.get_children():
            self.tabla.delete(r)

        try:
            self.bajas = self.servicio_inventario.listar_bajas()
        except Exception as error:
            self.bajas = []
            messagebox.showerror("Error", f"No se pudo cargar el historial de bajas: {error}")

        for b in self.bajas:
            self.tabla.insert("", tk.END, values=b)

    def registrar_baja(self):
        sel = self.cmb_producto.get()
        cant_s = self.ent_cantidad.get().strip()
        mot = self.cmb_motivo.get()
        obs = self.txt_obs.get("1.0", tk.END).strip()

        if not sel or not cant_s:
            messagebox.showwarning("Atención", "Seleccione un producto e ingrese la cantidad.")
            return

        try:
            cant = int(cant_s)
            prod_id = int(sel.split(" - ")[0])
            prod_nom = sel.split(" - ")[1].split(" (Stock:")[0]
            usuario = getattr(self.parent, "usuario", None)
            if not usuario:
                user_info = getattr(getattr(self.parent, "parent", None), "controlador", None)
                user_data = getattr(user_info, "usuario_actual", {}) or {}
                usuario = user_data.get("nombre") or user_data.get("username") or ""
            if not usuario:
                raise ValueError("No hay un usuario autenticado para registrar la baja.")
            self.servicio_inventario.registrar_baja(prod_id, prod_nom, cant, mot, obs, usuario)

            messagebox.showinfo("Éxito", f"Baja de {cant} unidad(es) de '{prod_nom}' registrada y stock descontado.")
            self.ent_cantidad.delete(0, tk.END)
            self.txt_obs.delete("1.0", tk.END)
            self.cargar_bajas()
            self.cargar_productos_combo()
        except ValueError:
            messagebox.showerror("Error", "Ingrese una cantidad numérica entera.")
        except Exception as e:
            messagebox.showerror("Error", f"Error registrando baja: {e}")
