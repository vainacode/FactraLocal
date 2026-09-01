import os
import db_conexion as sqlite3
import sys
import tkinter as tk
from tkinter import messagebox, ttk
from PIL import Image, ImageTk
from window_utils import posicionar_ventana
from servicios.servicio_configuracion import ServicioConfiguracion

class Sucursales(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.title("Gestión de Sucursales")
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
        self.images = {}
        self.sucursales = []
        self.sucursal_seleccionada = None
        self.servicio_configuracion = ServicioConfiguracion()

        self.widgets()
        self.cargar_sucursales()

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
            text="GESTIÓN DE SUCURSALES",
            font=("sans", 24, "bold"),
            bg="#DDE1E5",
            fg="#1E293B"
        )
        lbl_title.place(relx=0.5, y=25, anchor="center")

#============== 2. PANEL IZQUIERDO: FORMULARIO =====================================================#
        frame_form = tk.LabelFrame(
            self,
            text="Datos de la Sucursal",
            font=("sans", 13, "bold"),
            bg="#C6D9E3",
            fg="#1E293B",
            padx=15,
            pady=10
        )
        frame_form.place(x=20, y=60, width=390, height=515)

        # Nombre
        lbl_nom = tk.Label(frame_form, text="Nombre de Sucursal:", font=("sans", 10, "bold"), bg="#C6D9E3", fg="#1E293B")
        lbl_nom.place(x=10, y=5)

        self.ent_nombre = ttk.Entry(frame_form, font=("sans", 11))
        self.ent_nombre.place(x=10, y=28, width=335, height=28)

        # Dirección
        lbl_dir = tk.Label(frame_form, text="Dirección:", font=("sans", 10, "bold"), bg="#C6D9E3", fg="#1E293B")
        lbl_dir.place(x=10, y=65)

        self.ent_direccion = ttk.Entry(frame_form, font=("sans", 11))
        self.ent_direccion.place(x=10, y=88, width=335, height=28)

        # Teléfono
        lbl_tel = tk.Label(frame_form, text="Teléfono:", font=("sans", 10, "bold"), bg="#C6D9E3", fg="#1E293B")
        lbl_tel.place(x=10, y=125)

        self.ent_telefono = ttk.Entry(frame_form, font=("sans", 11))
        self.ent_telefono.place(x=10, y=148, width=335, height=28)

        # Encargado / Administrador
        lbl_enc = tk.Label(frame_form, text="Encargado / Administrador:", font=("sans", 10, "bold"), bg="#C6D9E3", fg="#1E293B")
        lbl_enc.place(x=10, y=185)

        self.ent_encargado = ttk.Entry(frame_form, font=("sans", 11))
        self.ent_encargado.place(x=10, y=208, width=335, height=28)

        # Ciudad
        lbl_ciu = tk.Label(frame_form, text="Ciudad:", font=("sans", 10, "bold"), bg="#C6D9E3", fg="#1E293B")
        lbl_ciu.place(x=10, y=245)

        self.ent_ciudad = ttk.Entry(frame_form, font=("sans", 11))
        self.ent_ciudad.place(x=10, y=268, width=335, height=28)

        # Estado
        lbl_est = tk.Label(frame_form, text="Estado:", font=("sans", 10, "bold"), bg="#C6D9E3", fg="#1E293B")
        lbl_est.place(x=10, y=305)

        self.cmb_estado = ttk.Combobox(frame_form, values=["Activo", "Inactivo"], font=("sans", 10), state="readonly")
        self.cmb_estado.current(0)
        self.cmb_estado.place(x=10, y=328, width=335, height=28)

        # Botones
        acciones = [
            ("Registrar", "agregar.png", self.registrar_sucursal, 0, 0),
            ("Editar", "editar.png", self.modificar_sucursal, 0, 1),
            ("Eliminar", "eliminar.png", self.eliminar_sucursal, 1, 0),
            ("Limpiar", "limpiar.png", self.limpiar_formulario, 1, 1),
        ]

        frame_btns = tk.Frame(frame_form, bg="#C6D9E3")
        frame_btns.place(x=10, y=375, width=340, height=110)

        for txt, ico_file, cmd, r, c in acciones:
            ruta_i = self.rutas(f"icono/{ico_file}")
            if os.path.exists(ruta_i):
                img_i = Image.open(ruta_i).resize((22, 22), Image.Resampling.LANCZOS)
                self.images[f"suc_btn_{ico_file}"] = ImageTk.PhotoImage(img_i)
                ico_btn = self.images[f"suc_btn_{ico_file}"]
            else:
                ico_btn = None

            btn = tk.Button(
                frame_btns,
                text=f"  {txt}",
                image=ico_btn,
                compound=tk.LEFT,
                font=("sans", 10, "bold"),
                bg="#EBEFF2",
                fg="#1E293B",
                relief="raised",
                bd=2,
                cursor="hand2",
                command=cmd
            )
            btn.place(x=c * 170, y=r * 52, width=155, height=44)

#============== 3. PANEL DERECHO: TABLA =============================================================#
        style = ttk.Style()
        style.configure("SUC.Treeview.Heading", font=("sans", 9, "bold"), background="#E0E6ED")
        style.configure("SUC.Treeview", font=("sans", 9), rowheight=24)

        cols = ("id", "nombre", "direccion", "telefono", "encargado", "estado")
        self.tabla = ttk.Treeview(self, columns=cols, show="headings", style="SUC.Treeview")
        self.tabla.place(x=430, y=65, width=530, height=510)

        titulos = [
            ("id", "ID", 40),
            ("nombre", "Sucursal", 140),
            ("direccion", "Dirección", 130),
            ("telefono", "Teléfono", 90),
            ("encargado", "Encargado", 100),
            ("estado", "Estado", 70),
        ]

        for c, t, w in titulos:
            self.tabla.heading(c, text=t, anchor="center")
            self.tabla.column(c, width=w, anchor="center" if c in ("id", "telefono", "estado") else "w")

        scroll_y = ttk.Scrollbar(self, orient="vertical", command=self.tabla.yview)
        self.tabla.configure(yscrollcommand=scroll_y.set)
        scroll_y.place(x=945, y=65, height=510)

        self.tabla.bind("<<TreeviewSelect>>", self.al_seleccionar)

    def cargar_sucursales(self):
        for r in self.tabla.get_children():
            self.tabla.delete(r)

        try:
            with sqlite3.connect(self.db_name) as conn:
                cur = conn.cursor()
                cur.execute("SELECT id, nombre, direccion, telefono, encargado, estado FROM sucursal")
                self.sucursales = cur.fetchall()
        except Exception:
            self.sucursales = []

        for s in self.sucursales:
            self.tabla.insert("", tk.END, values=s)

    def al_seleccionar(self, event=None):
        sel = self.tabla.selection()
        if not sel:
            return
        vals = self.tabla.item(sel[0], "values")
        self.sucursal_seleccionada = vals
        self.ent_nombre.delete(0, tk.END)
        self.ent_nombre.insert(0, vals[1])
        self.ent_direccion.delete(0, tk.END)
        self.ent_direccion.insert(0, vals[2])
        self.ent_telefono.delete(0, tk.END)
        self.ent_telefono.insert(0, vals[3])
        self.ent_encargado.delete(0, tk.END)
        self.ent_encargado.insert(0, vals[4] if len(vals) > 4 else "")
        self.cmb_estado.set(vals[5] if len(vals) > 5 else "Activo")

    def registrar_sucursal(self):
        nom = self.ent_nombre.get().strip()
        dir_s = self.ent_direccion.get().strip()
        tel = self.ent_telefono.get().strip()
        enc = self.ent_encargado.get().strip()
        est = self.cmb_estado.get()

        if not nom:
            messagebox.showwarning("Atención", "Ingrese el nombre de la sucursal.")
            return

        try:
            self.servicio_configuracion.crear_sucursal((nom, dir_s, tel, enc, est))
            messagebox.showinfo("Éxito", f"Sucursal '{nom}' registrada correctamente.")
            self.limpiar_formulario()
            self.cargar_sucursales()
        except Exception as e:
            messagebox.showerror("Error", f"Error registrando sucursal: {e}")

    def modificar_sucursal(self):
        if not self.sucursal_seleccionada:
            messagebox.showwarning("Atención", "Seleccione una sucursal para editar.")
            return

        nom = self.ent_nombre.get().strip()
        dir_s = self.ent_direccion.get().strip()
        tel = self.ent_telefono.get().strip()
        enc = self.ent_encargado.get().strip()
        est = self.cmb_estado.get()

        try:
            self.servicio_configuracion.actualizar_sucursal(self.sucursal_seleccionada[0], (nom, dir_s, tel, enc, est))
            messagebox.showinfo("Éxito", "Sucursal modificada correctamente.")
            self.limpiar_formulario()
            self.cargar_sucursales()
        except Exception as e:
            messagebox.showerror("Error", f"Error modificando sucursal: {e}")

    def eliminar_sucursal(self):
        if not self.sucursal_seleccionada:
            messagebox.showwarning("Atención", "Seleccione una sucursal para eliminar.")
            return

        resp = messagebox.askyesno("Confirmar", f"¿Está seguro de eliminar la sucursal '{self.sucursal_seleccionada[1]}'?")
        if resp:
            try:
                self.servicio_configuracion.eliminar_sucursal(self.sucursal_seleccionada[0])
                messagebox.showinfo("Éxito", "Sucursal eliminada.")
                self.limpiar_formulario()
                self.cargar_sucursales()
            except Exception as e:
                messagebox.showerror("Error", f"Error eliminando: {e}")

    def limpiar_formulario(self):
        self.sucursal_seleccionada = None
        self.ent_nombre.delete(0, tk.END)
        self.ent_direccion.delete(0, tk.END)
        self.ent_telefono.delete(0, tk.END)
        self.ent_encargado.delete(0, tk.END)
        self.ent_ciudad.delete(0, tk.END)
        self.cmb_estado.current(0)
