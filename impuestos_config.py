import os
import db_conexion as sqlite3
import sys
import tkinter as tk
from tkinter import messagebox, ttk
from PIL import Image, ImageTk
from window_utils import posicionar_ventana
from servicios.servicio_configuracion import ServicioConfiguracion

class ImpuestosConfig(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.title("Configuración de Impuestos y Utilidad")
        posicionar_ventana(self, 640, 480, parent)
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
            text="IMPUESTOS Y UTILIDAD",
            font=("sans", 20, "bold"),
            bg="#DDE1E5",
            fg="#1E293B"
        )
        lbl_title.place(relx=0.5, y=25, anchor="center")

#============== 2. FORMULARIO IMPUESTOS =============================================================#
        frame_imp = tk.LabelFrame(
            self,
            text="Configuración de Impuestos (IVA)",
            font=("sans", 12, "bold"),
            bg="#C6D9E3",
            fg="#1E293B",
            padx=20,
            pady=10
        )
        frame_imp.place(x=20, y=55, width=600, height=160)

        lbl_nom = tk.Label(frame_imp, text="Nombre del Impuesto:", font=("sans", 10, "bold"), bg="#C6D9E3", fg="#1E293B")
        lbl_nom.place(x=15, y=8)

        self.ent_nom_imp = ttk.Entry(frame_imp, font=("sans", 11))
        self.ent_nom_imp.place(x=15, y=30, width=250, height=30)
        self.ent_nom_imp.insert(0, "IVA")

        lbl_pct = tk.Label(frame_imp, text="Porcentaje Predeterminado (%):", font=("sans", 10, "bold"), bg="#C6D9E3", fg="#1E293B")
        lbl_pct.place(x=300, y=8)

        self.spn_pct_imp = ttk.Spinbox(frame_imp, from_=0, to=100, font=("sans", 11, "bold"), justify="center")
        self.spn_pct_imp.place(x=300, y=30, width=240, height=30)
        self.spn_pct_imp.set("19")

        self.chk_incl_var = tk.BooleanVar(value=True)
        self.chk_incl = ttk.Checkbutton(frame_imp, text="Los precios de venta ya incluyen impuestos", variable=self.chk_incl_var)
        self.chk_incl.place(x=15, y=75)

        self.chk_desg_var = tk.BooleanVar(value=True)
        self.chk_desg = ttk.Checkbutton(frame_imp, text="Desglosar impuesto discriminado en el ticket", variable=self.chk_desg_var)
        self.chk_desg.place(x=15, y=100)

#============== 3. FORMULARIO MARGEN DE UTILIDAD ====================================================#
        frame_ut = tk.LabelFrame(
            self,
            text="Margen de Utilidad Sugerido",
            font=("sans", 12, "bold"),
            bg="#C6D9E3",
            fg="#1E293B",
            padx=20,
            pady=10
        )
        frame_ut.place(x=20, y=225, width=600, height=155)

        lbl_ut_pct = tk.Label(frame_ut, text="Margen de Ganancia Sugerido (%):", font=("sans", 10, "bold"), bg="#C6D9E3", fg="#1E293B")
        lbl_ut_pct.place(x=15, y=10)

        self.spn_utilidad = ttk.Spinbox(frame_ut, from_=0, to=500, font=("sans", 11, "bold"), justify="center")
        self.spn_utilidad.place(x=15, y=35, width=250, height=30)
        self.spn_utilidad.set("30")

        lbl_ut_info = tk.Label(
            frame_ut,
            text="Al registrar un producto nuevo, el precio de venta se calculará\nautomáticamente sumando este porcentaje sobre el costo de adquisición.",
            font=("sans", 9, "italic"),
            bg="#C6D9E3",
            fg="#475569",
            justify="left"
        )
        lbl_ut_info.place(x=15, y=75)

#============== 4. BOTONES INFERIORES ===============================================================#
        ruta_save = self.rutas("icono/guardar.png")
        if os.path.exists(ruta_save):
            self.images["save_imp_ico"] = ImageTk.PhotoImage(Image.open(ruta_save).resize((22, 22), Image.Resampling.LANCZOS))
            ico_s = self.images["save_imp_ico"]
        else:
            ico_s = None

        btn_save = tk.Button(
            self,
            text="  Guardar Configuración",
            image=ico_s,
            compound=tk.LEFT,
            font=("sans", 11, "bold"),
            bg="#22C55E",
            fg="white",
            relief="raised",
            bd=2,
            cursor="hand2",
            command=self.guardar_datos
        )
        btn_save.place(x=140, y=405, width=200, height=44)

        ruta_canc = self.rutas("icono/cancelar.png")
        if os.path.exists(ruta_canc):
            self.images["canc_imp_ico"] = ImageTk.PhotoImage(Image.open(ruta_canc).resize((22, 22), Image.Resampling.LANCZOS))
            ico_c = self.images["canc_imp_ico"]
        else:
            ico_c = None

        btn_canc = tk.Button(
            self,
            text="  Cancelar",
            image=ico_c,
            compound=tk.LEFT,
            font=("sans", 11, "bold"),
            bg="#EBEFF2",
            fg="#1E293B",
            relief="raised",
            bd=2,
            cursor="hand2",
            command=self.destroy
        )
        btn_canc.place(x=360, y=405, width=150, height=44)

    def cargar_datos(self):
        try:
            row = self.servicio_configuracion.obtener_impuestos()
            if row:
                    nom, pct_imp, incluye, desglosa, margen = row
                    self.ent_nom_imp.delete(0, tk.END)
                    self.ent_nom_imp.insert(0, nom or "IVA")
                    self.spn_pct_imp.set(str(pct_imp if pct_imp is not None else 0))
                    self.chk_incl_var.set(bool(incluye))
                    self.chk_desg_var.set(bool(desglosa))
                    self.spn_utilidad.set(str(margen if margen is not None else 30))
        except Exception:
            pass

    def guardar_datos(self):
        try:
            u_val = float(self.spn_utilidad.get().strip() or 30)
            pct_val = float(self.spn_pct_imp.get().strip() or 0)
            nom_val = self.ent_nom_imp.get().strip() or "IVA"

            self.servicio_configuracion.guardar_impuestos((nom_val, pct_val, self.chk_incl_var.get(), self.chk_desg_var.get(), u_val))
            messagebox.showinfo("Éxito", "Configuración de impuestos y utilidad guardada exitosamente.")
            self.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"Error guardando datos: {e}")
