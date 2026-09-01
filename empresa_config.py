import os
import db_conexion as sqlite3
import sys
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageTk
from window_utils import posicionar_ventana
from servicios.servicio_configuracion import ServicioConfiguracion

class EmpresaConfig(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.title("Configuración de Mi Empresa")
        posicionar_ventana(self, 880, 580, parent)
        self.resizable(False, False)
        self.configure(bg="#DDE1E5")
        self.transient(parent)
        self.grab_set()
        try:
            self.iconbitmap(self.rutas('icono.ico'))
        except Exception:
            pass

        self.db_name = "database.db"
        self.servicio_configuracion = ServicioConfiguracion()
        self.images = {}
        self.ruta_logo = ""

        self.widgets()
        self.cargar_datos()

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
            text="DATOS DE LA EMPRESA",
            font=("sans", 22, "bold"),
            bg="#DDE1E5",
            fg="#1E293B"
        )
        lbl_title.place(relx=0.5, y=25, anchor="center")

#============== 2. PANEL IZQUIERDO: FORMULARIO =====================================================#
        frame_form = tk.LabelFrame(
            self,
            text="Información Fiscal y Comercial",
            font=("sans", 12, "bold"),
            bg="#C6D9E3",
            fg="#1E293B",
            padx=15,
            pady=8
        )
        frame_form.place(x=20, y=55, width=540, height=440)

        campos = [
            # Separación de 53 px: evita que el siguiente label tape los
            # últimos píxeles del Entry anterior (especialmente el nombre
            # comercial, que aparecía visualmente cortado).
            ("Nombre Comercial:", "ent_nom_com", 5),
            ("Razón Social:", "ent_razon", 58),
            ("NIT / Documento Fiscal:", "ent_nit", 111),
            ("Teléfono de Contacto:", "ent_tel", 164),
            ("Dirección:", "ent_dir", 217),
            ("Ciudad / Municipio:", "ent_ciu", 270),
            ("Correo Electrónico:", "ent_email", 323),
            ("Mensaje de Pie en Ticket:", "ent_msg", 376),
        ]

        self.entries = {}
        for label_text, var_name, y_pos in campos:
            lbl = tk.Label(frame_form, text=label_text, font=("sans", 10, "bold"), bg="#C6D9E3", fg="#1E293B")
            lbl.place(x=10, y=y_pos)

            ent = ttk.Entry(frame_form, font=("sans", 10))
            ent.place(x=10, y=y_pos + 22, width=500, height=34)
            self.entries[var_name] = ent

#============== 3. PANEL DERECHO: LOGO DE LA EMPRESA ===============================================#
        frame_logo = tk.LabelFrame(
            self,
            text="Logo de la Empresa",
            font=("sans", 12, "bold"),
            bg="#C6D9E3",
            fg="#1E293B",
            padx=12,
            pady=8
        )
        frame_logo.place(x=580, y=55, width=280, height=440)

        self.lbl_preview_logo = tk.Label(frame_logo, text="Sin Logo", bg="white", relief="solid", bd=1)
        self.lbl_preview_logo.place(x=20, y=20, width=220, height=220)

        btn_sel_logo = tk.Button(
            frame_logo,
            text="  Seleccionar Logo",
            font=("sans", 10, "bold"),
            bg="#EBEFF2",
            fg="#1E293B",
            relief="raised",
            bd=2,
            cursor="hand2",
            command=self.seleccionar_logo
        )
        btn_sel_logo.place(x=35, y=260, width=190, height=38)

        lbl_logo_info = tk.Label(
            frame_logo,
            text="Formatos: PNG, JPG\nTamaño rec.: 256x256 px",
            font=("sans", 9, "italic"),
            bg="#C6D9E3",
            fg="#64748B",
            justify="center"
        )
        lbl_logo_info.place(x=25, y=320)

#============== 4. BOTÓN GUARDAR ===================================================================#
        ruta_save = self.rutas("icono/guardar.png")
        if os.path.exists(ruta_save):
            self.images["save_emp_ico"] = ImageTk.PhotoImage(Image.open(ruta_save).resize((22, 22), Image.Resampling.LANCZOS))
            ico_s = self.images["save_emp_ico"]
        else:
            ico_s = None

        btn_save = tk.Button(
            self,
            text="  Guardar Configuración",
            image=ico_s,
            compound=tk.LEFT,
            font=("sans", 12, "bold"),
            bg="#22C55E",
            fg="white",
            relief="raised",
            bd=2,
            cursor="hand2",
            command=self.guardar_datos
        )
        btn_save.place(relx=0.5, y=530, width=240, height=44, anchor="center")

    def cargar_datos(self):
        try:
            row = self.servicio_configuracion.obtener_empresa_detalle()
            if row:
                    self.entries["ent_nom_com"].insert(0, row[0] or "")
                    self.entries["ent_razon"].insert(0, row[0] or "")
                    self.entries["ent_nit"].insert(0, row[1] or "")
                    self.entries["ent_tel"].insert(0, row[2] or "")
                    self.entries["ent_dir"].insert(0, row[3] or "")
                    self.entries["ent_ciu"].insert(0, row[4] or "")
                    self.entries["ent_email"].insert(0, row[5] or "")
                    self.entries["ent_msg"].insert(0, "")
                    ruta_guardada = row[6] or ""
                    if ruta_guardada:
                        self.ruta_logo = ruta_guardada
                        ruta_logo = ruta_guardada if os.path.isabs(ruta_guardada) else self.rutas(ruta_guardada)
                        if os.path.exists(ruta_logo):
                            self.mostrar_preview_logo(ruta_logo)
                    return
        except Exception:
            pass

        # En una instalación nueva los campos deben quedar vacíos para que
        # el administrador configure sus propios datos, sin valores de demo.

    def seleccionar_logo(self):
        f = filedialog.askopenfilename(filetypes=[("Imágenes", "*.png *.jpg *.jpeg")])
        if f:
            self.ruta_logo = f
            self.mostrar_preview_logo(f)

    def mostrar_preview_logo(self, path):
        try:
            img = Image.open(path).resize((200, 200), Image.Resampling.LANCZOS)
            self.images["emp_logo_prev"] = ImageTk.PhotoImage(img)
            self.lbl_preview_logo.config(image=self.images["emp_logo_prev"], text="")
        except Exception:
            pass

    def guardar_datos(self):
        nom = self.entries["ent_nom_com"].get().strip()
        nit = self.entries["ent_nit"].get().strip()
        tel = self.entries["ent_tel"].get().strip()
        dir_e = self.entries["ent_dir"].get().strip()
        ciu = self.entries["ent_ciu"].get().strip()
        em = self.entries["ent_email"].get().strip()

        try:
            self.servicio_configuracion.guardar_empresa((nom, nit, tel, dir_e, ciu, em, self.ruta_logo or ""))
            # EmpresaConfig normalmente se abre desde Configuración, que a su
            # vez pertenece a la home. Propagar el refresh hasta el contenedor.
            destino = self.parent
            vistos = set()
            while destino is not None and id(destino) not in vistos:
                vistos.add(id(destino))
                if hasattr(destino, "actualizar_empresa"):
                    destino.actualizar_empresa()
                    break
                destino = getattr(destino, "parent", None)
            messagebox.showinfo("Éxito", "Datos de la empresa guardados correctamente.")
            self.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"Error guardando datos: {e}")
