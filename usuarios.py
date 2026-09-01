import datetime
import os
import db_conexion as sqlite3
import sys
import tkinter as tk
from tkinter import messagebox, ttk
from seguridad import hash_password, validar_password
from PIL import Image, ImageTk
from window_utils import posicionar_ventana
from servicios.servicio_usuarios import ServicioUsuarios

class Usuarios(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.title("Punto de Venta Versión 4.4.7 - Gestión de Usuarios")
        posicionar_ventana(self, 1100, 650, parent)
        self.resizable(False, False)
        self.configure(bg="#DDE1E5")
        self.transient(parent)
        self.grab_set()
        try:
            self.iconbitmap(self.rutas('icono.ico'))
        except Exception:
            pass

        self.db_name = "database.db"
        self.servicio_usuarios = ServicioUsuarios()
        self.images = {}
        self.usuarios_list = []
        self.usuario_seleccionado = None

        self.widgets()
        self.actualizar_reloj()
        self.cargar_usuarios()

    def rutas(self, ruta):
        try:
            rutabase = sys.__MEIPASS
        except Exception:
            rutabase = os.path.abspath(".")
        return os.path.join(rutabase, ruta)

    def widgets(self):
#============== 1. HEADER ==========================================================================#
        lbl_titulo = tk.Label(
            self,
            text="GESTIÓN DE USUARIOS",
            font=("sans", 28, "bold"),
            bg="#DDE1E5",
            fg="#1E293B"
        )
        lbl_titulo.place(relx=0.5, y=35, anchor="center")

        # Fecha y Hora Top-Right
        frame_time = tk.Frame(self, bg="#DDE1E5")
        frame_time.place(x=780, y=20, width=300, height=35)

        ruta_cal = self.rutas("icono/calendario.png")
        if os.path.exists(ruta_cal):
            self.images["cal_usr"] = ImageTk.PhotoImage(Image.open(ruta_cal).resize((22, 22), Image.Resampling.LANCZOS))
            tk.Label(frame_time, image=self.images["cal_usr"], bg="#DDE1E5").place(x=0, y=5)

        self.lbl_fecha = tk.Label(frame_time, text="", font=("sans", 11, "bold"), bg="#DDE1E5", fg="#1E293B")
        self.lbl_fecha.place(x=30, y=6)

        ruta_rel = self.rutas("icono/reloj.png")
        if not os.path.exists(ruta_rel):
            ruta_rel = self.rutas("icono/calendario.png")

        if os.path.exists(ruta_rel):
            self.images["rel_usr"] = ImageTk.PhotoImage(Image.open(ruta_rel).resize((22, 22), Image.Resampling.LANCZOS))
            tk.Label(frame_time, image=self.images["rel_usr"], bg="#DDE1E5").place(x=150, y=5)

        self.lbl_hora = tk.Label(frame_time, text="", font=("sans", 11, "bold"), bg="#DDE1E5", fg="#1E293B")
        self.lbl_hora.place(x=180, y=6)

#============== 2. PANEL IZQUIERDO: FORMULARIO =====================================================#
        frame_form = tk.LabelFrame(
            self,
            text="Datos del Usuario",
            font=("sans", 13, "bold"),
            bg="#C6D9E3",
            fg="#1E293B",
            padx=15,
            pady=10
        )
        frame_form.place(x=20, y=70, width=420, height=545)

        # Nombre Completo
        lbl_nom = tk.Label(frame_form, text="Nombre Completo:", font=("sans", 11, "bold"), bg="#C6D9E3", fg="#1E293B")
        lbl_nom.place(x=10, y=5)

        self.ent_nombre = ttk.Entry(frame_form, font=("sans", 11))
        self.ent_nombre.place(x=10, y=28, width=365, height=30)

        # Usuario (Username)
        lbl_u = tk.Label(frame_form, text="Nombre de Usuario:", font=("sans", 11, "bold"), bg="#C6D9E3", fg="#1E293B")
        lbl_u.place(x=10, y=65)

        self.ent_usuario = ttk.Entry(frame_form, font=("sans", 11))
        self.ent_usuario.place(x=10, y=88, width=365, height=30)

        # Contraseña
        lbl_p = tk.Label(frame_form, text="Contraseña:", font=("sans", 11, "bold"), bg="#C6D9E3", fg="#1E293B")
        lbl_p.place(x=10, y=125)

        self.ent_password = ttk.Entry(frame_form, font=("sans", 11), show="*")
        self.ent_password.place(x=10, y=148, width=325, height=30)

        self.ver_pass_var = False
        ruta_ojo = self.rutas("icono/mostrar.png")
        if not os.path.exists(ruta_ojo):
            ruta_ojo = self.rutas("icono/ojo.png")

        if os.path.exists(ruta_ojo):
            self.images["ojo_usr"] = ImageTk.PhotoImage(Image.open(ruta_ojo).resize((20, 20), Image.Resampling.LANCZOS))
            btn_ojo = tk.Button(frame_form, image=self.images["ojo_usr"], bg="white", relief="solid", bd=1, cursor="hand2", command=self.toggle_password)
            btn_ojo.place(x=340, y=148, width=35, height=30)

        # Rol
        lbl_rol = tk.Label(frame_form, text="Rol del Usuario:", font=("sans", 11, "bold"), bg="#C6D9E3", fg="#1E293B")
        lbl_rol.place(x=10, y=185)

        self.cmb_rol = ttk.Combobox(frame_form, values=["Administrador", "Cajero", "Supervisor"], font=("sans", 11), state="readonly")
        self.cmb_rol.set("Cajero")
        self.cmb_rol.place(x=10, y=208, width=365, height=30)

        # Teléfono
        lbl_tel = tk.Label(frame_form, text="Teléfono / Celular:", font=("sans", 11, "bold"), bg="#C6D9E3", fg="#1E293B")
        lbl_tel.place(x=10, y=245)

        self.ent_telefono = ttk.Entry(frame_form, font=("sans", 11))
        self.ent_telefono.place(x=10, y=268, width=365, height=30)

        # Estado
        lbl_est = tk.Label(frame_form, text="Estado:", font=("sans", 11, "bold"), bg="#C6D9E3", fg="#1E293B")
        lbl_est.place(x=10, y=305)

        self.cmb_estado = ttk.Combobox(frame_form, values=["Activo", "Inactivo"], font=("sans", 11), state="readonly")
        self.cmb_estado.current(0)
        self.cmb_estado.place(x=10, y=328, width=365, height=30)

        # Botones de Acción (4 Botones Cuadrados)
        acciones = [
            ("Registrar", "agregar.png", self.registrar_usuario, 0, 0),
            ("Modificar", "editar.png", self.modificar_usuario, 0, 1),
            ("Inactivar", "eliminar.png", self.inactivar_usuario, 1, 0),
            ("Limpiar", "limpiar.png", self.limpiar_formulario, 1, 1),
        ]

        frame_btns = tk.Frame(frame_form, bg="#C6D9E3")
        frame_btns.place(x=15, y=375, width=360, height=140)

        for txt, ico_file, cmd, r, c in acciones:
            ruta_i = self.rutas(f"icono/{ico_file}")
            if os.path.exists(ruta_i):
                img_i = Image.open(ruta_i).resize((24, 24), Image.Resampling.LANCZOS)
                self.images[f"usr_btn_{ico_file}"] = ImageTk.PhotoImage(img_i)
                ico_btn = self.images[f"usr_btn_{ico_file}"]
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
            btn.place(x=c * 180, y=r * 65, width=165, height=52)

#============== 3. PANEL DERECHO: TABLA =============================================================#
        lbl_b = tk.Label(self, text="Buscar:", font=("sans", 12, "bold"), bg="#DDE1E5", fg="#1E293B")
        lbl_b.place(x=460, y=75)

        self.ent_buscar = ttk.Entry(self, font=("sans", 11))
        self.ent_buscar.place(x=530, y=73, width=220, height=30)
        self.ent_buscar.bind("<KeyRelease>", lambda e: self.filtrar_usuarios())

        ruta_b = self.rutas("icono/buscar.png")
        if os.path.exists(ruta_b):
            self.images["b_usr_ico"] = ImageTk.PhotoImage(Image.open(ruta_b).resize((22, 22), Image.Resampling.LANCZOS))
            btn_b = tk.Button(self, image=self.images["b_usr_ico"], bg="white", relief="solid", bd=1, cursor="hand2")
            btn_b.place(x=755, y=73, width=32, height=30)

        # Botón Roles & Permisos
        ruta_rol = self.rutas("icono/roles.png")
        if not os.path.exists(ruta_rol):
            ruta_rol = self.rutas("icono/permisos.png")

        if os.path.exists(ruta_rol):
            self.images["rol_usr_ico"] = ImageTk.PhotoImage(Image.open(ruta_rol).resize((22, 22), Image.Resampling.LANCZOS))
            ico_rol = self.images["rol_usr_ico"]
        else:
            ico_rol = None

        btn_rol = tk.Button(
            self,
            text="  Roles y Permisos",
            image=ico_rol,
            compound=tk.LEFT,
            font=("sans", 10, "bold"),
            bg="#EBEFF2",
            fg="#1E293B",
            relief="raised",
            bd=2,
            cursor="hand2",
            command=self.abrir_roles_permisos
        )
        btn_rol.place(x=895, y=70, width=185, height=36)

        # Tabla
        style = ttk.Style()
        style.configure("USR.Treeview.Heading", font=("sans", 9, "bold"), background="#E0E6ED")
        style.configure("USR.Treeview", font=("sans", 9), rowheight=24)

        cols = ("id", "nombre", "usuario", "rol", "telefono", "estado")
        self.tabla = ttk.Treeview(self, columns=cols, show="headings", style="USR.Treeview")
        self.tabla.place(x=460, y=115, width=620, height=500)

        titulos = [
            ("id", "ID", 40),
            ("nombre", "Nombre Completo", 190),
            ("usuario", "Usuario", 110),
            ("rol", "Rol", 110),
            ("telefono", "Teléfono", 100),
            ("estado", "Estado", 70),
        ]

        for c, t, w in titulos:
            self.tabla.heading(c, text=t, anchor="center")
            self.tabla.column(c, width=w, anchor="center" if c in ("id", "rol", "telefono", "estado") else "w")

        scroll_y = ttk.Scrollbar(self, orient="vertical", command=self.tabla.yview)
        self.tabla.configure(yscrollcommand=scroll_y.set)
        scroll_y.place(x=1082, y=115, height=500)

        self.tabla.bind("<<TreeviewSelect>>", self.al_seleccionar)

    def toggle_password(self):
        if self.ver_pass_var:
            self.ent_password.config(show="*")
            self.ver_pass_var = False
        else:
            self.ent_password.config(show="")
            self.ver_pass_var = True

    def actualizar_reloj(self):
        ahora = datetime.datetime.now()
        self.lbl_fecha.config(text=ahora.strftime("%d-%m-%Y"))
        self.lbl_hora.config(text=ahora.strftime("%H:%M:%S"))
        self.after(1000, self.actualizar_reloj)

    def cargar_usuarios(self):
        for r in self.tabla.get_children():
            self.tabla.delete(r)

        try:
            self.usuarios_list = self.servicio_usuarios.listar()
        except Exception as error:
            self.usuarios_list = []
            messagebox.showerror("Error", f"No se pudieron cargar los usuarios: {error}")

        for u in self.usuarios_list:
            self.tabla.insert("", tk.END, values=u)

    def al_seleccionar(self, event=None):
        sel = self.tabla.selection()
        if not sel:
            return
        vals = self.tabla.item(sel[0], "values")
        self.usuario_seleccionado = vals
        self.ent_nombre.delete(0, tk.END)
        self.ent_nombre.insert(0, vals[1])
        self.ent_usuario.delete(0, tk.END)
        self.ent_usuario.insert(0, vals[2])
        self.cmb_rol.set(vals[3])
        self.ent_telefono.delete(0, tk.END)
        self.ent_telefono.insert(0, vals[4] if len(vals) > 4 else "")
        self.cmb_estado.set(vals[5] if len(vals) > 5 else "Activo")

    def registrar_usuario(self):
        nom = self.ent_nombre.get().strip()
        usr = self.ent_usuario.get().strip()
        pwd = self.ent_password.get().strip()
        rol = self.cmb_rol.get()
        tel = self.ent_telefono.get().strip()
        est = self.cmb_estado.get()

        if not nom or not usr or not pwd:
            messagebox.showwarning("Atención", "Nombre, usuario y contraseña son obligatorios.")
            return
        if not validar_password(pwd):
            messagebox.showwarning("Contraseña no válida", "Use al menos 8 caracteres, incluyendo letras y números.")
            return

        try:
            self.servicio_usuarios.crear(nom, usr, pwd, rol, tel, est)
            messagebox.showinfo("Éxito", f"Usuario '{usr}' registrado correctamente.")
            self.limpiar_formulario()
            self.cargar_usuarios()
        except Exception as e:
            messagebox.showerror("Error", f"Error registrando usuario: {e}")

    def modificar_usuario(self):
        if not self.usuario_seleccionado:
            messagebox.showwarning("Atención", "Seleccione un usuario para modificar.")
            return

        nom = self.ent_nombre.get().strip()
        usr = self.ent_usuario.get().strip()
        pwd = self.ent_password.get().strip()
        rol = self.cmb_rol.get()
        tel = self.ent_telefono.get().strip()
        est = self.cmb_estado.get()

        try:
            self.servicio_usuarios.actualizar(self.usuario_seleccionado[0], nom, usr, pwd, rol, tel, est)
            # Si se modificó el usuario actualmente conectado, actualizar la sesión
            # y la home inmediatamente, sin obligar a cerrar sesión.
            actual = getattr(self.parent.controlador, "usuario_actual", None)
            if actual and str(actual.get("id")) == str(self.usuario_seleccionado[0]):
                actual.update({"username": usr, "nombre": nom, "rol": rol})
                if hasattr(self.parent, "actualizar_usuario"):
                    self.parent.actualizar_usuario()
            messagebox.showinfo("Éxito", "Usuario modificado correctamente.")
            self.limpiar_formulario()
            self.cargar_usuarios()
        except Exception as e:
            messagebox.showerror("Error", f"Error modificando usuario: {e}")

    def inactivar_usuario(self):
        if not self.usuario_seleccionado:
            messagebox.showwarning("Atención", "Seleccione un usuario para inactivar.")
            return

        try:
            actual = getattr(self.parent.controlador, "usuario_actual", {}) or {}
            self.servicio_usuarios.inactivar(self.usuario_seleccionado[0], actual.get("id"))
            messagebox.showinfo("Éxito", "Usuario inactivado correctamente.")
            self.limpiar_formulario()
            self.cargar_usuarios()
        except Exception as e:
            messagebox.showerror("Error", f"Error inactivando usuario: {e}")

    def limpiar_formulario(self):
        self.usuario_seleccionado = None
        self.ent_nombre.delete(0, tk.END)
        self.ent_usuario.delete(0, tk.END)
        self.ent_password.delete(0, tk.END)
        self.ent_telefono.delete(0, tk.END)
        self.cmb_rol.set("Cajero")
        self.cmb_estado.current(0)

    def filtrar_usuarios(self):
        q = self.ent_buscar.get().strip().lower()
        for r in self.tabla.get_children():
            self.tabla.delete(r)

        for u in self.usuarios_list:
            if not q or q in str(u[1]).lower() or q in str(u[2]).lower() or q in str(u[3]).lower():
                self.tabla.insert("", tk.END, values=u)

    def abrir_roles_permisos(self):
        from roles_permisos import RolesPermisos
        RolesPermisos(self)
