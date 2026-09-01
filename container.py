import os
import os
import db_conexion as sqlite3
import sys
import tkinter as tk
from tkinter import messagebox, ttk
from PIL import Image, ImageTk
from permisos import obtener_permisos, tiene_permiso
from servicios.servicio_configuracion import ServicioConfiguracion

class Container(tk.Frame):
    def __init__(self, padre, controlador):
        super().__init__(padre)
        self.controlador = controlador
        self.pack()
        self.place(x=0, y=0, width=1100, height=650)
        self.config(bg="#C6D9E3")
        self.images = {}
        self.servicio_configuracion = ServicioConfiguracion()
        self.botones_modulos = {}
        self.widgets()

    def rutas(self, ruta):
        try:
            rutabase = sys.__MEIPASS
        except Exception:
            rutabase = os.path.abspath(".")
        return os.path.join(rutabase, ruta)

    def logout(self):
        from login import Login
        if messagebox.askyesno("Cerrar sesión", "¿Está seguro de que desea salir del sistema?"):
            self.controlador.usuario_actual = None
            self.controlador.show_frame(Login)

    def reload_dashboard(self):
        self.actualizar_empresa()
        self.actualizar_usuario()
        messagebox.showinfo("Actualizar", "Datos del punto de venta actualizados correctamente.")

    def abrir_modulo(self, nombre):
        user_info = getattr(self.controlador, "usuario_actual", {})
        if not user_info or not user_info.get("id"):
            messagebox.showwarning("Sesión requerida", "Debe iniciar sesión para acceder al sistema.")
            return
        rol = user_info.get("rol")
        if not tiene_permiso(rol, nombre):
            messagebox.showwarning(
                "Acceso restringido",
                f"El rol {rol} no tiene permiso para acceder a {nombre}."
            )
            return

        if nombre == "Inventario":
            from inventarios import Inventarios
            Inventarios(self)
        elif nombre == "Ventas":
            from ventas import Ventas
            user_info = getattr(self.controlador, "usuario_actual", {})
            nombre_usuario = user_info.get("nombre") or user_info.get("username", "")
            Ventas(self, usuario=nombre_usuario, rol=user_info.get("rol"))
        elif nombre == "Reportes":
            from reportes import Reportes
            Reportes(self)
        elif nombre == "Cotizaciones":
            from cotizaciones import Cotizaciones
            user_info = getattr(self.controlador, "usuario_actual", {})
            nombre_usuario = user_info.get("nombre") or user_info.get("username", "")
            Cotizaciones(self, usuario=nombre_usuario)
        elif nombre == "Clientes":
            from clientes import Clientes
            Clientes(self)
        elif nombre in ("Pedidos", "Compras"):
            from compras import Compras
            Compras(self)
        elif nombre == "Configuración":
            from configuracion import Configuracion
            Configuracion(self)
        elif nombre in ("Caja", "Gestión Caja"):
            from gestion_caja import GestionCaja
            GestionCaja(self)
        elif nombre == "Gastos":
            from control_gastos import ControlGastos
            ControlGastos(self)
        elif nombre == "Cobros":
            from cuentas_por_cobrar import CuentasPorCobrar
            CuentasPorCobrar(self)
        elif nombre in ("Proveedores", "Proveedor"):
            from proveedores import Proveedores
            Proveedores(self)
        elif nombre == "Usuarios":
            from usuarios import Usuarios
            Usuarios(self)
        else:
            messagebox.showinfo("Módulo", f"Accediendo al módulo de {nombre}...")

    def abrir_prueba(self):
        """Abre la prueba y conserva la referencia para que no se cierre sola."""
        user_info = getattr(self.controlador, "usuario_actual", {})
        if not user_info or not user_info.get("id"):
            messagebox.showwarning("Sesión requerida", "Debe iniciar sesión para acceder al sistema.")
            return
        from prueba import Prueba
        if getattr(self, "ventana_prueba", None) is not None and self.ventana_prueba.winfo_exists():
            self.ventana_prueba.lift()
            self.ventana_prueba.focus_force()
            return
        self.ventana_prueba = Prueba(self, usuario=user_info.get("nombre") or user_info.get("username", "Demo"))

        def limpiar_referencia(evento):
            # Solo se limpia la referencia cuando se destruye la ventana de
            # Prueba, nunca por la destrucción de uno de sus controles.
            if evento.widget is self.ventana_prueba:
                self.ventana_prueba = None

        self.ventana_prueba.bind("<Destroy>", limpiar_referencia, add="+")

    def actualizar_usuario(self):
        user_info = getattr(self.controlador, "usuario_actual", {})
        if not user_info:
            return
        nombre = user_info.get("nombre") or user_info.get("username", "")
        rol = user_info.get("rol")
        if hasattr(self, 'lbl_user'):
            self.lbl_user.config(text=f" Bienvenido: {nombre}")
        if hasattr(self, 'lbl_role'):
            self.lbl_role.config(text=f" Rol: {rol}")
        self.aplicar_permisos()

    def aplicar_permisos(self):
        """Activa únicamente los botones permitidos para el usuario actual."""
        user_info = getattr(self.controlador, "usuario_actual", {})
        rol = user_info.get("rol") if user_info else None
        permitidos = obtener_permisos(rol)
        for modulo, boton in self.botones_modulos.items():
            boton.configure(state="normal" if modulo in permitidos else "disabled")

    def actualizar_empresa(self):
        """Recarga en la home el nombre, contacto y logo guardados en Configuración."""
        try:
            datos_empresa = self.servicio_configuracion.obtener_empresa()
            empresa = datos_empresa[:3] + (datos_empresa[5],) if datos_empresa else None
        except sqlite3.Error:
            empresa = None

        if not empresa:
            return

        nombre, direccion, telefono, logo_path = empresa
        if hasattr(self, "lbl_company"):
            self.lbl_company.config(text=nombre or "Mi empresa")
        if hasattr(self, "lbl_address"):
            self.lbl_address.config(text= direccion or "Dirección no configurada")
        if hasattr(self, "lbl_phone"):
            self.lbl_phone.config(text=telefono or "Teléfono no configurado")

        if hasattr(self, "lbl_logo") and logo_path:
            ruta_logo = self.rutas(logo_path) if not os.path.isabs(logo_path) else logo_path
            if os.path.exists(ruta_logo):
                try:
                    imagen = Image.open(ruta_logo).resize((210, 210), Image.Resampling.LANCZOS)
                    self.images["center_logo"] = ImageTk.PhotoImage(imagen)
                    self.lbl_logo.config(image=self.images["center_logo"])
                except Exception:
                    pass

    def widgets(self):
#============== 1. FRAME SUPERIOR (HEADER) =========================================================#
        frame_top = tk.Frame(self, bg="#DCE1E6", highlightbackground="#B8C4CE", highlightthickness=1)
        frame_top.pack()
        frame_top.place(x=0, y=0, width=1100, height=85)

        lbl_titulo = tk.Label(
            frame_top,
            text="PUNTO DE VENTA",
            font=("sans", 32, "bold"),
            bg="#DCE1E6",
            fg="#2C3E50"
        )
        lbl_titulo.place(relx=0.5, rely=0.5, anchor="center")

        # Botón de apagado / cerrar sesión (logout.png)
        ruta_power = self.rutas("icono/logout.png")
        if not os.path.exists(ruta_power):
            ruta_power = self.rutas("icono/dashboard/power.png")

        if os.path.exists(ruta_power):
            img_power_raw = Image.open(ruta_power).resize((46, 46), Image.Resampling.LANCZOS)
            self.images["power"] = ImageTk.PhotoImage(img_power_raw)
            btn_power = tk.Button(
                frame_top,
                image=self.images["power"],
                bg="#DCE1E6",
                activebackground="#DCE1E6",
                bd=0,
                relief="flat",
                cursor="hand2",
                command=self.logout
            )
            btn_power.place(x=1025, y=18, width=48, height=48)

#============== 2. COLUMNA IZQUIERDA (BOTONES) ====================================================#
        botones_izq = [
            ("Ventas", "btnventas.png", 105),
            ("Cotizaciones", "btncotizaciones.png", 175),
            ("Inventario", "btninventario.png", 245),
            ("Clientes", "btnclientes.png", 315),
            ("Proveedor", "btnproveedor.png", 385),
            ("Compras", "btnpedidos.png", 455),
        ]

        for texto, icon_file, y_pos in botones_izq:
            ruta_ico = self.rutas(f"icono/{icon_file}")
            if not os.path.exists(ruta_ico):
                # Fallback
                nom_base = icon_file.replace("btn", "").replace(".png", "")
                ruta_ico = self.rutas(f"icono/dashboard/{nom_base}.png")

            if os.path.exists(ruta_ico):
                img_btn_raw = Image.open(ruta_ico).resize((32, 32), Image.Resampling.LANCZOS)
                self.images[icon_file] = ImageTk.PhotoImage(img_btn_raw)
                ico = self.images[icon_file]
            else:
                ico = None

            btn = tk.Button(
                self,
                text=f"  {texto}",
                image=ico,
                compound=tk.LEFT,
                font=("sans", 14, "bold"),
                bg="#EBEFF2",
                fg="#2C3E50",
                activebackground="#D5E0E8",
                activeforeground="#1A252F",
                relief="raised",
                bd=2,
                anchor="w",
                padx=15,
                cursor="hand2",
                command=lambda t=texto: self.abrir_modulo(t)
            )
            btn.place(x=25, y=y_pos, width=235, height=56)
            self.botones_modulos[texto] = btn

        # Acceso temporal al prototipo. No se registra en permisos para no
        # modificar el control de acceso de los módulos existentes.
        btn_prueba = tk.Button(
            self,
            text="  Prueba",
            image=self._cargar_icono_prueba(),
            compound=tk.LEFT,
            font=("sans", 12, "bold"),
            bg="#F3D29B",
            fg="#2C3E50",
            activebackground="#EBC27F",
            relief="raised",
            bd=2,
            anchor="w",
            padx=15,
            cursor="hand2",
            command=self.abrir_prueba,
        )
        btn_prueba.place(x=25, y=525, width=235, height=56)

#============== 3. PANEL CENTRAL ==================================================================#
        frame_center = tk.Frame(
            self,
            bg="#CAD8E2",
            highlightbackground="#A9BFCE",
            highlightthickness=1
        )
        frame_center.pack()
        frame_center.place(x=280, y=100, width=540, height=485)

        # Botón de recarga en la esquina superior derecha del panel central
        ruta_reload = self.rutas("icono/actualizar1.png")
        if not os.path.exists(ruta_reload):
            ruta_reload = self.rutas("icono/actualizar.png")
        if not os.path.exists(ruta_reload):
            ruta_reload = self.rutas("icono/dashboard/reload.png")

        if os.path.exists(ruta_reload):
            img_reload_raw = Image.open(ruta_reload).resize((24, 24), Image.Resampling.LANCZOS)
            self.images["reload"] = ImageTk.PhotoImage(img_reload_raw)
            btn_reload = tk.Button(
                frame_center,
                image=self.images["reload"],
                bg="#CAD8E2",
                activebackground="#CAD8E2",
                bd=0,
                relief="flat",
                cursor="hand2",
                command=self.reload_dashboard
            )
            btn_reload.place(x=495, y=15, width=26, height=26)

        # Logo central (Logo1.png)
        ruta_center_logo = self.rutas("imagenes/Logo1.png")
        if not os.path.exists(ruta_center_logo):
            ruta_center_logo = self.rutas("icono/dashboard/center_logo.png")

        if os.path.exists(ruta_center_logo):
            img_logo_raw = Image.open(ruta_center_logo).resize((210, 210), Image.Resampling.LANCZOS)
            self.images["center_logo"] = ImageTk.PhotoImage(img_logo_raw)
            self.lbl_logo = tk.Label(
                frame_center,
                image=self.images["center_logo"],
                bg="#CAD8E2"
            )
            self.lbl_logo.place(x=165, y=35, width=210, height=210)

        # Datos de la empresa en el centro
        self.lbl_company = tk.Label(
            frame_center,
            text="Empresa no configurada",
            font=("sans", 16, "bold"),
            bg="#CAD8E2",
            fg="#1E293B"
        )
        self.lbl_company.place(x=0, y=260, width=540)

        self.lbl_address = tk.Label(
            frame_center,
            text="Dirección no configurada",
            font=("sans", 13, "bold"),
            bg="#CAD8E2",
            fg="#334155"
        )
        self.lbl_address.place(x=0, y=295, width=540)

        self.lbl_phone = tk.Label(
            frame_center,
            text="Teléfono no configurado",
            font=("sans", 13, "bold"),
            bg="#CAD8E2",
            fg="#334155"
        )
        self.lbl_phone.place(x=0, y=328, width=540)

        lbl_author = tk.Label(
            frame_center,
            text="Software creado por Kevin Arboleda @ 2024",
            font=("sans", 10, "bold"),
            bg="#CAD8E2",
            fg="#475569"
        )
        lbl_author.place(x=0, y=442, width=540)

#============== 4. COLUMNA DERECHA (BOTONES) =====================================================#
        botones_der = [
            ("Cobros", "btncobros.png", 105),
            ("Reportes", "btnreportes.png", 175),
            ("Configuración", "configuracion.png", 245),
            ("Gastos", "btngastos.png", 315),
            ("Usuarios", "btnusuarios.png", 385),
            ("Gestión Caja", "btncaja.png", 455),
        ]

        for texto, icon_file, y_pos in botones_der:
            ruta_ico = self.rutas(f"icono/{icon_file}")
            if not os.path.exists(ruta_ico):
                nom_base = icon_file.replace("btn", "").replace(".png", "")
                ruta_ico = self.rutas(f"icono/dashboard/{nom_base}.png")

            if os.path.exists(ruta_ico):
                img_btn_raw = Image.open(ruta_ico).resize((32, 32), Image.Resampling.LANCZOS)
                self.images[icon_file] = ImageTk.PhotoImage(img_btn_raw)
                ico = self.images[icon_file]
            else:
                ico = None

            btn = tk.Button(
                self,
                text=f"  {texto}",
                image=ico,
                compound=tk.LEFT,
                font=("sans", 14, "bold"),
                bg="#EBEFF2",
                fg="#2C3E50",
                activebackground="#D5E0E8",
                activeforeground="#1A252F",
                relief="raised",
                bd=2,
                anchor="w",
                padx=15,
                cursor="hand2",
                command=lambda t=texto: self.abrir_modulo(t)
            )
            btn.place(x=840, y=y_pos, width=235, height=56)
            self.botones_modulos[texto] = btn

#============== 5. FRAME INFERIOR (BARRA DE ESTADO / FOOTER) =======================================#
        frame_bottom = tk.Frame(
            self,
            bg="#D4DEE5",
            highlightbackground="#B8C4CE",
            highlightthickness=1
        )
        frame_bottom.pack()
        frame_bottom.place(x=0, y=605, width=1100, height=45)

        # Usuario conectado (user_icon.png)
        ruta_user = self.rutas("icono/user_icon.png")
        if not os.path.exists(ruta_user):
            ruta_user = self.rutas("icono/dashboard/user_icon.png")

        if os.path.exists(ruta_user):
            img_user_raw = Image.open(ruta_user).resize((20, 20), Image.Resampling.LANCZOS)
            self.images["user_icon"] = ImageTk.PhotoImage(img_user_raw)
            self.lbl_user = tk.Label(
                frame_bottom,
            text=" Bienvenido: -",
                image=self.images["user_icon"],
                compound=tk.LEFT,
                font=("sans", 11, "bold"),
                bg="#D4DEE5",
                fg="#1E293B"
            )
        else:
            self.lbl_user = tk.Label(
                frame_bottom,
                text=" Bienvenido: -",
                font=("sans", 11, "bold"),
                bg="#D4DEE5",
                fg="#1E293B"
            )
        self.lbl_user.place(x=20, y=10)

        # Rol (rol_icon.png)
        ruta_role = self.rutas("icono/rol_icon.png")
        if not os.path.exists(ruta_role):
            ruta_role = self.rutas("icono/dashboard/role_icon.png")

        if os.path.exists(ruta_role):
            img_role_raw = Image.open(ruta_role).resize((20, 20), Image.Resampling.LANCZOS)
            self.images["role_icon"] = ImageTk.PhotoImage(img_role_raw)
            self.lbl_role = tk.Label(
                frame_bottom,
                text=" Rol: -",
                image=self.images["role_icon"],
                compound=tk.LEFT,
                font=("sans", 11, "bold"),
                bg="#D4DEE5",
                fg="#1E293B"
            )
        else:
            self.lbl_role = tk.Label(
                frame_bottom,
                text=" Rol: -",
                font=("sans", 11, "bold"),
                bg="#D4DEE5",
                fg="#1E293B"
            )
        self.lbl_role.place(x=450, y=10)

        # Versión + Info (btninformacion.png)
        lbl_ver = tk.Label(
            frame_bottom,
            text="Versión 4.4.7",
            font=("sans", 11, "bold"),
            bg="#D4DEE5",
            fg="#1E293B"
        )
        lbl_ver.place(x=950, y=10)

        ruta_info = self.rutas("icono/btninformacion.png")
        if not os.path.exists(ruta_info):
            ruta_info = self.rutas("icono/dashboard/info_icon.png")

        if os.path.exists(ruta_info):
            img_info_raw = Image.open(ruta_info).resize((20, 20), Image.Resampling.LANCZOS)
            self.images["info_icon"] = ImageTk.PhotoImage(img_info_raw)
            lbl_info = tk.Label(
                frame_bottom,
                image=self.images["info_icon"],
                bg="#D4DEE5"
            )
            lbl_info.place(x=1055, y=11)

        # Cargar siempre los datos actuales, no los valores fijos del diseño.
        self.actualizar_empresa()
        self.aplicar_permisos()

    def _cargar_icono_prueba(self):
        ruta = self.rutas("icono/consultar.png")
        if not os.path.exists(ruta):
            ruta = self.rutas("icono/buscar.png")
        if not os.path.exists(ruta):
            return None
        try:
            imagen = Image.open(ruta).resize((30, 30), Image.Resampling.LANCZOS)
            self.images["prueba"] = ImageTk.PhotoImage(imagen)
            return self.images["prueba"]
        except Exception:
            return None
