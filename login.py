import os
import db_conexion as sqlite3
import sys
import tkinter as tk
from tkinter import Button, Entry, Frame, Label, messagebox, ttk
from PIL import Image, ImageTk
from container import Container
from seguridad import hash_password, verificar_password, registrar_evento, validar_password
from servicios.servicio_usuarios import ServicioUsuarios

class Login(tk.Frame):
    db_name = "database.db"

    def __init__(self, padre, controlador):
        super().__init__(padre)
        self.controlador = controlador
        self.servicio_usuarios = ServicioUsuarios()
        self.pack()
        self.place(x=0, y=0, width=1100, height=650)
        self.images = {}
        self.widgets()

    @staticmethod
    def _buscar_usuario(cursor, username):
        """Busca primero el nombre exacto para no bloquear cuentas legadas.

        La migración impide crear nuevas cuentas que solo difieran por
        mayúsculas, pero puede haber datos antiguos con esa duplicidad. En
        ese caso, una coincidencia exacta es inequívoca y debe poder iniciar
        sesión; solo se rechaza cuando no hay coincidencia exacta y quedan
        varias coincidencias equivalentes.
        """
        consulta = "SELECT id, username, password, rol, nombre, estado FROM usuarios WHERE username=?"
        cursor.execute(consulta, (username,))
        exactas = cursor.fetchall()
        if len(exactas) == 1:
            return exactas[0], False
        if len(exactas) > 1:
            return None, True

        consulta = "SELECT id, username, password, rol, nombre, estado FROM usuarios WHERE LOWER(username)=LOWER(?)"
        cursor.execute(consulta, (username,))
        equivalentes = cursor.fetchall()
        if len(equivalentes) == 1:
            return equivalentes[0], False
        return None, bool(equivalentes)

    def rutas(self, ruta):
        try:
            rutabase = sys.__MEIPASS
        except Exception:
            rutabase = os.path.abspath(".")
        return os.path.join(rutabase, ruta)

    def validacion(self, user, pas):
        return len(user) > 0 and len(pas) > 0

    def login(self):
        user = self.username.get().strip()
        pas = self.password.get().strip()

        if self.validacion(user, pas):
            try:
                with sqlite3.connect(self.db_name) as conn:
                    cursor = conn.cursor()
                    usuario_data, usuario_ambiguo = self._buscar_usuario(cursor, user)
                    result = [usuario_data] if usuario_data else []

                    if usuario_ambiguo:
                        # No elegir arbitrariamente entre cuentas que solo
                        # difieren en mayúsculas: el acceso sería ambiguo.
                        registrar_evento(None, user, "LOGIN_FALLIDO", "Nombre de usuario duplicado; requiere depuración")

                    if result and str(result[0][5] or "Activo").lower() == "inactivo":
                        result = []
                    elif result:
                        password_ok, legacy = verificar_password(pas, usuario_data[2])
                        if not password_ok:
                            result = []
                        elif legacy:
                            self.servicio_usuarios.actualizar_password_legacy(usuario_data[0], pas)
                    if result:
                        nombre_completo = usuario_data[4] if len(usuario_data) > 4 and usuario_data[4] else usuario_data[1]
                        # Guardar información completa del usuario logueado en el controlador
                        self.controlador.usuario_actual = {
                            "id": usuario_data[0],
                            "username": usuario_data[1],
                            # Nunca elevar privilegios por un rol vacío o
                            # corrupto; la migración asigna Cajero a legados.
                            "rol": usuario_data[3] if len(usuario_data) > 3 and usuario_data[3] in ("Administrador", "Supervisor", "Cajero") else "Cajero",
                            "nombre": nombre_completo
                        }
                        self.control1()
                        registrar_evento(usuario_data[0], usuario_data[1], "LOGIN_EXITOSO")
                        from dialogos import mostrar_dialogo
                        # Esperar a que la home termine de levantarse para que el
                        # diálogo quede visible al frente y centrado sobre ella.
                        self.controlador.after(
                            120,
                            lambda: mostrar_dialogo(
                                self.controlador,
                                "Inicio de sesión correcto",
                                f"Bienvenido {nombre_completo}"
                            )
                        )
                    else:
                        registrar_evento(None, user, "LOGIN_FALLIDO", "Credenciales inválidas o usuario inactivo")
                        self.username.delete(0, 'end')
                        self.password.delete(0, 'end')
                        from dialogos import mostrar_dialogo
                        mostrar_dialogo(self.controlador, "Acceso denegado", "Usuario y/o contraseña incorrecta.", "error")
            except sqlite3.Error as e:
                from dialogos import mostrar_dialogo
                mostrar_dialogo(self.controlador, "Error de conexión", f"No se conectó a la base de datos: {e}", "error")
        else:
            from dialogos import mostrar_dialogo
            mostrar_dialogo(self.controlador, "Datos incompletos", "Llene todas las casillas.", "warning")

    def password_command(self):
        if self.password.cget('show') == "*":
            self.password.config(show="")
            if "eye_closed" in self.images:
                self.btn_ojo.config(image=self.images["eye_closed"])
        else:
            self.password.config(show="*")
            if "eye_open" in self.images:
                self.btn_ojo.config(image=self.images["eye_open"])

    def control1(self):
        container_frame = self.controlador.frames.get(Container)
        if container_frame and hasattr(container_frame, 'actualizar_usuario'):
            container_frame.actualizar_usuario()
        self.controlador.show_frame(Container)

    def control2(self):
        self.controlador.show_frame(Registro)

    def widgets(self):
#=============== FRAME IZQUIERDO =================================================================#
        fondo = tk.Frame(self, bg="#DDE1E5", highlightbackground="#B8C4CE", highlightthickness=1)
        fondo.pack()
        fondo.place(x=0, y=0, width=550, height=650)

        # 1. Logo circular con sombra / Logo1.png
        ruta_logo = self.rutas("imagenes/Logo1.png")
        if not os.path.exists(ruta_logo):
            ruta_logo = self.rutas("icono/dashboard/center_logo.png")
        
        if os.path.exists(ruta_logo):
            img_logo = Image.open(ruta_logo).resize((220, 220), Image.Resampling.LANCZOS)
            self.images["logo"] = ImageTk.PhotoImage(img_logo)
            lbl_logo = tk.Label(fondo, image=self.images["logo"], bg="#DDE1E5")
            lbl_logo.place(x=165, y=35, width=220, height=220)

        # 2. Información de la Empresa
        lbl_empresa = tk.Label(
            fondo,
            text="La Casa de los Repuestos",
            font=("sans", 17, "bold"),
            bg="#DDE1E5",
            fg="#1E293B",
            anchor="center"
        )
        lbl_empresa.place(x=0, y=275, width=550)

        lbl_calle = tk.Label(
            fondo,
            text="Av. 27 de Febrero # 145",
            font=("sans", 13, "bold"),
            bg="#DDE1E5",
            fg="#334155",
            anchor="center"
        )
        lbl_calle.place(x=0, y=312, width=550)

        lbl_telefono = tk.Label(
            fondo,
            text="+1 (809) 567-8900",
            font=("sans", 13, "bold"),
            bg="#DDE1E5",
            fg="#334155",
            anchor="center"
        )
        lbl_telefono.place(x=0, y=345, width=550)

        # 3. Textos de Copyright
        lbl_autor = tk.Label(
            fondo,
            text="Software creado por Kevin Arboleda",
            font=("sans", 11, "bold"),
            bg="#DDE1E5",
            fg="#334155",
            anchor="center"
        )
        lbl_autor.place(x=0, y=435, width=550)

        lbl_copy = tk.Label(
            fondo,
            text="Copyright @ InnovaSoft Code 2024",
            font=("sans", 11, "bold"),
            bg="#DDE1E5",
            fg="#334155",
            anchor="center"
        )
        lbl_copy.place(x=0, y=465, width=550)

        # 4. Banner InnovaSoft Code
        ruta_innova = self.rutas("imagenes/innova1.png")
        if os.path.exists(ruta_innova):
            img_innova = Image.open(ruta_innova).resize((370, 60), Image.Resampling.LANCZOS)
            self.images["innova"] = ImageTk.PhotoImage(img_innova)
            lbl_innova = tk.Label(fondo, image=self.images["innova"], bg="#DDE1E5")
            lbl_innova.place(x=90, y=510)

#=============== FRAME DERECHO ==================================================================#
        fondo2 = tk.Frame(self, bg="#C6D9E3", highlightbackground="#B8C4CE", highlightthickness=1)
        fondo2.pack()
        fondo2.place(x=550, y=0, width=550, height=650)

        # Título
        lbl_titulo = tk.Label(
            fondo2,
            text="Inicio de sesión",
            font=("sans", 32, "bold"),
            bg="#C6D9E3",
            fg="#1E293B",
            anchor="center"
        )
        lbl_titulo.place(x=0, y=60, width=550)

        # --- Campo Nombre de usuario ---
        lbl_user = tk.Label(
            fondo2,
            text="Nombre de usuario",
            font=("sans", 18, "bold"),
            bg="#C6D9E3",
            fg="#1E293B"
        )
        lbl_user.place(x=145, y=155)

        # Icono de usuario a la izquierda del Entry
        ruta_user_ico = self.rutas("icono/userimg.png")
        if not os.path.exists(ruta_user_ico):
            ruta_user_ico = self.rutas("icono/login_user.png")

        if os.path.exists(ruta_user_ico):
            img_user_raw = Image.open(ruta_user_ico).resize((28, 28), Image.Resampling.LANCZOS)
            self.images["user_ico"] = ImageTk.PhotoImage(img_user_raw)
            lbl_user_img = tk.Label(
                fondo2,
                image=self.images["user_ico"],
                bg="white",
                relief="solid",
                bd=1
            )
            lbl_user_img.place(x=145, y=195, width=38, height=38)

        self.username = ttk.Entry(fondo2, font=("sans", 14, "bold"))
        self.username.place(x=183, y=195, width=192, height=38)
        self.username.bind('<Return>', lambda event: self.password.focus_set() if not self.password.get() else self.login())
        self.username.bind('<Tab>', lambda event: (self.password.focus_set(), "break")[1])

        # --- Campo Contraseña ---
        lbl_pas = tk.Label(
            fondo2,
            text="Contraseña",
            font=("sans", 18, "bold"),
            bg="#C6D9E3",
            fg="#1E293B"
        )
        lbl_pas.place(x=145, y=250)

        # Icono de candado a la izquierda del Entry
        ruta_lock_ico = self.rutas("icono/pasimg.png")
        if not os.path.exists(ruta_lock_ico):
            ruta_lock_ico = self.rutas("icono/login_lock.png")

        if os.path.exists(ruta_lock_ico):
            img_lock_raw = Image.open(ruta_lock_ico).resize((28, 28), Image.Resampling.LANCZOS)
            self.images["lock_ico"] = ImageTk.PhotoImage(img_lock_raw)
            lbl_lock_img = tk.Label(
                fondo2,
                image=self.images["lock_ico"],
                bg="white",
                relief="solid",
                bd=1
            )
            lbl_lock_img.place(x=145, y=290, width=38, height=38)

        self.password = ttk.Entry(fondo2, show="*", font=("sans", 14, "bold"))
        self.password.place(x=183, y=290, width=192, height=38)
        self.password.bind('<Return>', lambda event: self.login())
        self.password.bind('<Tab>', lambda event: (self.btn_iniciar.focus_set(), "break")[1])
        self.password.bind('<Shift-Tab>', lambda event: (self.username.focus_set(), "break")[1])

        # Botón de ojo para alternar visibilidad de contraseña
        ruta_eye_open = self.rutas("icono/mostrar.png")
        if not os.path.exists(ruta_eye_open):
            ruta_eye_open = self.rutas("icono/login_eye.png")

        ruta_eye_closed = self.rutas("icono/ocultar.png")
        if not os.path.exists(ruta_eye_closed):
            ruta_eye_closed = self.rutas("icono/login_eye_closed.png")

        if os.path.exists(ruta_eye_open):
            img_open = Image.open(ruta_eye_open).resize((28, 28), Image.Resampling.LANCZOS)
            self.images["eye_open"] = ImageTk.PhotoImage(img_open)
            if os.path.exists(ruta_eye_closed):
                img_closed = Image.open(ruta_eye_closed).resize((28, 28), Image.Resampling.LANCZOS)
                self.images["eye_closed"] = ImageTk.PhotoImage(img_closed)
            else:
                self.images["eye_closed"] = self.images["eye_open"]

            self.btn_ojo = tk.Button(
                fondo2,
                image=self.images["eye_open"],
                bg="#C6D9E3",
                activebackground="#C6D9E3",
                bd=0,
                relief="flat",
                cursor="hand2",
                takefocus=0,
                command=self.password_command
            )
            self.btn_ojo.place(x=388, y=294, width=30, height=30)

        # --- Botones Iniciar y Registrar ---
        ruta_iniciar = self.rutas("icono/iniciar.png")
        if os.path.exists(ruta_iniciar):
            img_iniciar = Image.open(ruta_iniciar).resize((32, 32), Image.Resampling.LANCZOS)
            self.images["iniciar"] = ImageTk.PhotoImage(img_iniciar)
            ico_iniciar = self.images["iniciar"]
        else:
            ico_iniciar = None

        self.btn_iniciar = tk.Button(
            fondo2,
            text="  Iniciar",
            image=ico_iniciar,
            compound=tk.LEFT,
            font=("sans", 14, "bold"),
            bg="#EBEFF2",
            fg="#1E293B",
            activebackground="#D5E0E8",
            relief="raised",
            bd=2,
            cursor="hand2",
            takefocus=1,
            command=self.login
        )
        self.btn_iniciar.place(x=145, y=365, width=230, height=46)
        self.btn_iniciar.bind('<Return>', lambda e: self.login())
        self.btn_iniciar.bind('<space>', lambda e: self.login())
        self.btn_iniciar.bind('<Tab>', lambda e: (self.btn_registrar.focus_set(), "break")[1])
        self.btn_iniciar.bind('<Shift-Tab>', lambda e: (self.password.focus_set(), "break")[1])
        self.btn_iniciar.bind('<FocusIn>', lambda e: self.btn_iniciar.config(bg="#D5E0E8", relief="solid"))
        self.btn_iniciar.bind('<FocusOut>', lambda e: self.btn_iniciar.config(bg="#EBEFF2", relief="raised"))

        ruta_reg = self.rutas("icono/registrar.png")
        if os.path.exists(ruta_reg):
            img_reg = Image.open(ruta_reg).resize((32, 32), Image.Resampling.LANCZOS)
            self.images["registrar"] = ImageTk.PhotoImage(img_reg)
            ico_reg = self.images["registrar"]
        else:
            ico_reg = None

        self.btn_registrar = tk.Button(
            fondo2,
            text="  Registrar",
            image=ico_reg,
            compound=tk.LEFT,
            font=("sans", 14, "bold"),
            bg="#EBEFF2",
            fg="#1E293B",
            activebackground="#D5E0E8",
            relief="raised",
            bd=2,
            cursor="hand2",
            takefocus=1,
            command=self.control2
        )
        self.btn_registrar.place(x=145, y=425, width=230, height=46)
        if os.getenv("POS_ENV", "development").lower() == "production":
            self.btn_registrar.config(state="disabled", text="Registro administrado")
        self.btn_registrar.bind('<Return>', lambda e: self.control2())
        self.btn_registrar.bind('<space>', lambda e: self.control2())
        self.btn_registrar.bind('<Tab>', lambda e: (self.username.focus_set(), "break")[1])
        self.btn_registrar.bind('<Shift-Tab>', lambda e: (self.btn_iniciar.focus_set(), "break")[1])
        self.btn_registrar.bind('<FocusIn>', lambda e: self.btn_registrar.config(bg="#D5E0E8", relief="solid"))
        # --- Texto de Versión (en verde) ---
        lbl_version = tk.Label(
            fondo2,
            text="Versión 4.4.7",
            font=("sans", 11, "bold"),
            bg="#C6D9E3",
            fg="#2E7D32",
            anchor="center"
        )
        lbl_version.place(x=0, y=500, width=550)

        self.after(50, self.enfocar_usuario)

    def enfocar_usuario(self):
        if hasattr(self, 'username'):
            self.username.focus_force()
            self.username.select_range(0, tk.END)


class Registro(tk.Frame):
    db_name = "database.db"

    def __init__(self, padre, controlador):
        super().__init__(padre)
        self.controlador = controlador
        self.pack()
        self.place(x=0, y=0, width=1100, height=650)
        self.images = {}
        self.widgets()

    def rutas(self, ruta):
        try:
            rutabase = sys.__MEIPASS
        except Exception:
            rutabase = os.path.abspath(".")
        return os.path.join(rutabase, ruta)

    def validacion(self, user, pas):
        return len(user) > 0 and len(pas) > 0

    def create_table(self):
        consulta = '''
        CREATE TABLE IF NOT EXISTS usuarios (
            id SERIAL PRIMARY KEY,
            username TEXT,
            password TEXT,
            rol TEXT
        )
        '''
        self.eje_consulta(consulta)

    def eje_consulta(self, consulta, parametros=()):
        try:
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()
                cursor.execute(consulta, parametros)
                conn.commit()
                return cursor.rowcount == 1
        except sqlite3.Error as e:
            from dialogos import mostrar_dialogo
            mostrar_dialogo(self.controlador, "Error de base de datos", f"Error al ejecutar la consulta: {e}", "error")
            return False

    def registro(self):
        user = self.username.get()
        pas = self.password.get()
        key = self.key.get()
        if os.getenv("POS_ENV", "development").lower() == "production":
            from dialogos import mostrar_dialogo
            mostrar_dialogo(
                self.controlador,
                "Registro restringido",
                "En producción, las cuentas deben ser creadas por un administrador desde Usuarios.",
                "warning",
            )
            return
        if self.validacion(user, pas):
            if not validar_password(pas):
                from dialogos import mostrar_dialogo
                mostrar_dialogo(self.controlador, "Contraseña no válida", "Use al menos 8 caracteres, incluyendo letras y números.", "warning")
                self.username.delete(0, 'end')
                self.password.delete(0, 'end')
            else:
                clave_registro = os.getenv("POS_REGISTRATION_KEY", "")
                if clave_registro and key == clave_registro:
                    if not self.servicio_usuarios.registrar_cajero_publico(user, pas):
                        from dialogos import mostrar_dialogo
                        mostrar_dialogo(self.controlador, "Usuario duplicado", "Ya existe un usuario con ese nombre de acceso.", "warning")
                        return
                    self.control2()
                    from dialogos import mostrar_dialogo
                    mostrar_dialogo(self.controlador, "Registro completado", "Usuario creado correctamente.")
                else:
                    from dialogos import mostrar_dialogo
                    mostrar_dialogo(self.controlador, "Código incorrecto", "Error al ingresar el código de registro.", "error")
        else:
            from dialogos import mostrar_dialogo
            mostrar_dialogo(self.controlador, "Datos incompletos", "Llene sus datos.", "warning")

    def password_command(self):
        if self.password.cget('show') == "*":
            self.password.config(show="")
            if "eye_closed" in self.images:
                self.btn_ojo.config(image=self.images["eye_closed"])
        else:
            self.password.config(show="*")
            if "eye_open" in self.images:
                self.btn_ojo.config(image=self.images["eye_open"])

    def control1(self):
        self.controlador.show_frame(Container)

    def control2(self):
        self.controlador.show_frame(Login)

    def widgets(self):
#=============== FRAME IZQUIERDO =================================================================#
        fondo = tk.Frame(self, bg="#DDE1E5", highlightbackground="#B8C4CE", highlightthickness=1)
        fondo.pack()
        fondo.place(x=0, y=0, width=550, height=650)

        ruta_logo = self.rutas("imagenes/Logo1.png")
        if not os.path.exists(ruta_logo):
            ruta_logo = self.rutas("icono/dashboard/center_logo.png")

        if os.path.exists(ruta_logo):
            img_logo = Image.open(ruta_logo).resize((220, 220), Image.Resampling.LANCZOS)
            self.images["logo"] = ImageTk.PhotoImage(img_logo)
            lbl_logo = tk.Label(fondo, image=self.images["logo"], bg="#DDE1E5")
            lbl_logo.place(x=165, y=35, width=220, height=220)

        lbl_empresa = tk.Label(
            fondo,
            text="La Casa de los Repuestos",
            font=("sans", 17, "bold"),
            bg="#DDE1E5",
            fg="#1E293B",
            anchor="center"
        )
        lbl_empresa.place(x=0, y=275, width=550)

        lbl_calle = tk.Label(
            fondo,
            text="Av. 27 de Febrero # 145",
            font=("sans", 13, "bold"),
            bg="#DDE1E5",
            fg="#334155",
            anchor="center"
        )
        lbl_calle.place(x=0, y=312, width=550)

        lbl_telefono = tk.Label(
            fondo,
            text="+1 (809) 567-8900",
            font=("sans", 13, "bold"),
            bg="#DDE1E5",
            fg="#334155",
            anchor="center"
        )
        lbl_telefono.place(x=0, y=345, width=550)

        lbl_autor = tk.Label(
            fondo,
            text="Software creado por Kevin Arboleda",
            font=("sans", 11, "bold"),
            bg="#DDE1E5",
            fg="#334155",
            anchor="center"
        )
        lbl_autor.place(x=0, y=435, width=550)

        lbl_copy = tk.Label(
            fondo,
            text="Copyright @ InnovaSoft Code 2024",
            font=("sans", 11, "bold"),
            bg="#DDE1E5",
            fg="#334155",
            anchor="center"
        )
        lbl_copy.place(x=0, y=465, width=550)

        ruta_innova = self.rutas("imagenes/innova1.png")
        if os.path.exists(ruta_innova):
            img_innova = Image.open(ruta_innova).resize((370, 60), Image.Resampling.LANCZOS)
            self.images["innova"] = ImageTk.PhotoImage(img_innova)
            lbl_innova = tk.Label(fondo, image=self.images["innova"], bg="#DDE1E5")
            lbl_innova.place(x=90, y=510)

#=============== FRAME DERECHO ==================================================================#
        fondo2 = tk.Frame(self, bg="#C6D9E3", highlightbackground="#B8C4CE", highlightthickness=1)
        fondo2.pack()
        fondo2.place(x=550, y=0, width=550, height=650)

        lbl_titulo = tk.Label(
            fondo2,
            text="Registrarse",
            font=("sans", 32, "bold"),
            bg="#C6D9E3",
            fg="#1E293B",
            anchor="center"
        )
        lbl_titulo.place(x=0, y=60, width=550)

        # Usuario
        lbl_user = tk.Label(fondo2, text="Nombre de usuario", font=("sans", 16, "bold"), bg="#C6D9E3", fg="#1E293B")
        lbl_user.place(x=145, y=140)

        ruta_user_ico = self.rutas("icono/userimg.png")
        if not os.path.exists(ruta_user_ico):
            ruta_user_ico = self.rutas("icono/login_user.png")

        if os.path.exists(ruta_user_ico):
            img_user_raw = Image.open(ruta_user_ico).resize((28, 28), Image.Resampling.LANCZOS)
            self.images["user_ico"] = ImageTk.PhotoImage(img_user_raw)
            lbl_user_img = tk.Label(fondo2, image=self.images["user_ico"], bg="white", relief="solid", bd=1)
            lbl_user_img.place(x=145, y=175, width=38, height=38)

        self.username = ttk.Entry(fondo2, font=("sans", 14, "bold"))
        self.username.place(x=183, y=175, width=192, height=38)
        self.username.bind('<Return>', lambda event: self.password.focus_set() if not self.password.get() else self.registro())
        self.username.bind('<Tab>', lambda event: (self.password.focus_set(), "break")[1])

        # Contraseña
        lbl_pas = tk.Label(fondo2, text="Contraseña", font=("sans", 16, "bold"), bg="#C6D9E3", fg="#1E293B")
        lbl_pas.place(x=145, y=220)

        ruta_lock_ico = self.rutas("icono/pasimg.png")
        if not os.path.exists(ruta_lock_ico):
            ruta_lock_ico = self.rutas("icono/login_lock.png")

        if os.path.exists(ruta_lock_ico):
            img_lock_raw = Image.open(ruta_lock_ico).resize((28, 28), Image.Resampling.LANCZOS)
            self.images["lock_ico"] = ImageTk.PhotoImage(img_lock_raw)
            lbl_lock_img = tk.Label(fondo2, image=self.images["lock_ico"], bg="white", relief="solid", bd=1)
            lbl_lock_img.place(x=145, y=255, width=38, height=38)

        self.password = ttk.Entry(fondo2, show="*", font=("sans", 14, "bold"))
        self.password.place(x=183, y=255, width=192, height=38)
        self.password.bind('<Return>', lambda event: self.key.focus_set() if not self.key.get() else self.registro())
        self.password.bind('<Tab>', lambda event: (self.key.focus_set(), "break")[1])
        self.password.bind('<Shift-Tab>', lambda event: (self.username.focus_set(), "break")[1])

        # Botón de ojo
        ruta_eye_open = self.rutas("icono/mostrar.png")
        if not os.path.exists(ruta_eye_open):
            ruta_eye_open = self.rutas("icono/login_eye.png")

        ruta_eye_closed = self.rutas("icono/ocultar.png")
        if not os.path.exists(ruta_eye_closed):
            ruta_eye_closed = self.rutas("icono/login_eye_closed.png")

        if os.path.exists(ruta_eye_open):
            img_open = Image.open(ruta_eye_open).resize((28, 28), Image.Resampling.LANCZOS)
            self.images["eye_open"] = ImageTk.PhotoImage(img_open)
            if os.path.exists(ruta_eye_closed):
                img_closed = Image.open(ruta_eye_closed).resize((28, 28), Image.Resampling.LANCZOS)
                self.images["eye_closed"] = ImageTk.PhotoImage(img_closed)
            else:
                self.images["eye_closed"] = self.images["eye_open"]

            self.btn_ojo = tk.Button(
                fondo2,
                image=self.images["eye_open"],
                bg="#C6D9E3",
                activebackground="#C6D9E3",
                bd=0,
                relief="flat",
                cursor="hand2",
                takefocus=0,
                command=self.password_command
            )
            self.btn_ojo.place(x=388, y=259, width=30, height=30)

        # Código de Registro
        lbl_key = tk.Label(fondo2, text="Código de registro", font=("sans", 16, "bold"), bg="#C6D9E3", fg="#1E293B")
        lbl_key.place(x=145, y=300)

        ruta_key_ico = self.rutas("icono/keyimg.png")
        if not os.path.exists(ruta_key_ico):
            ruta_key_ico = ruta_lock_ico

        if os.path.exists(ruta_key_ico):
            img_key_raw = Image.open(ruta_key_ico).resize((28, 28), Image.Resampling.LANCZOS)
            self.images["key_ico"] = ImageTk.PhotoImage(img_key_raw)
            lbl_key_img = tk.Label(fondo2, image=self.images["key_ico"], bg="white", relief="solid", bd=1)
            lbl_key_img.place(x=145, y=335, width=38, height=38)

        self.key = ttk.Entry(fondo2, show="*", font=("sans", 14, "bold"))
        self.key.place(x=183, y=335, width=192, height=38)
        self.key.bind('<Return>', lambda event: self.registro())
        self.key.bind('<Tab>', lambda event: (self.btn_registrar.focus_set(), "break")[1])
        self.key.bind('<Shift-Tab>', lambda event: (self.password.focus_set(), "break")[1])

        # Botones
        ruta_reg = self.rutas("icono/registrar.png")
        if os.path.exists(ruta_reg):
            img_reg = Image.open(ruta_reg).resize((32, 32), Image.Resampling.LANCZOS)
            self.images["registrar"] = ImageTk.PhotoImage(img_reg)
            ico_reg = self.images["registrar"]
        else:
            ico_reg = None

        self.btn_registrar = tk.Button(
            fondo2,
            text="  Registrarse",
            image=ico_reg,
            compound=tk.LEFT,
            font=("sans", 14, "bold"),
            bg="#EBEFF2",
            fg="#1E293B",
            activebackground="#D5E0E8",
            relief="raised",
            bd=2,
            cursor="hand2",
            takefocus=1,
            command=self.registro
        )
        self.btn_registrar.place(x=145, y=395, width=230, height=46)
        if os.getenv("POS_ENV", "development").lower() == "production":
            self.btn_registrar.config(state="disabled", text="Registro deshabilitado")
        self.btn_registrar.bind('<Return>', lambda e: self.registro())
        self.btn_registrar.bind('<space>', lambda e: self.registro())
        self.btn_registrar.bind('<Tab>', lambda e: (self.btn_regresar.focus_set(), "break")[1])
        self.btn_registrar.bind('<Shift-Tab>', lambda e: (self.key.focus_set(), "break")[1])
        self.btn_registrar.bind('<FocusIn>', lambda e: self.btn_registrar.config(bg="#D5E0E8", relief="solid"))
        self.btn_registrar.bind('<FocusOut>', lambda e: self.btn_registrar.config(bg="#EBEFF2", relief="raised"))

        ruta_back = self.rutas("icono/regresar.png")
        if os.path.exists(ruta_back):
            img_back = Image.open(ruta_back).resize((32, 32), Image.Resampling.LANCZOS)
            self.images["regresar"] = ImageTk.PhotoImage(img_back)
            ico_back = self.images["regresar"]
        else:
            ico_back = None

        self.btn_regresar = tk.Button(
            fondo2,
            text="  Regresar",
            image=ico_back,
            compound=tk.LEFT,
            font=("sans", 14, "bold"),
            bg="#EBEFF2",
            fg="#1E293B",
            activebackground="#D5E0E8",
            relief="raised",
            bd=2,
            cursor="hand2",
            takefocus=1,
            command=self.control2
        )
        self.btn_regresar.place(x=145, y=455, width=230, height=46)
        self.btn_regresar.bind('<Return>', lambda e: self.control2())
        self.btn_regresar.bind('<space>', lambda e: self.control2())
        self.btn_regresar.bind('<Tab>', lambda e: (self.username.focus_set(), "break")[1])
        self.btn_regresar.bind('<Shift-Tab>', lambda e: (self.btn_registrar.focus_set(), "break")[1])
        lbl_version = tk.Label(
            fondo2,
            text="Versión 4.4.7",
            font=("sans", 11, "bold"),
            bg="#C6D9E3",
            fg="#2E7D32",
            anchor="center"
        )
        lbl_version.place(x=0, y=520, width=550)

        self.after(50, self.enfocar_usuario)

    def enfocar_usuario(self):
        if hasattr(self, 'username'):
            self.username.focus_force()
            self.username.select_range(0, tk.END)
