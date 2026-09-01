import os
import db_conexion as sqlite3
import sys
import tkinter as tk
from tkinter import messagebox, ttk
from PIL import Image, ImageTk
from window_utils import posicionar_ventana
from servicios.servicio_configuracion import ServicioConfiguracion

class MonedaConfig(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.title("Configuración de Moneda y Formato")
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
            text="CONFIGURACIÓN DE MONEDA",
            font=("sans", 20, "bold"),
            bg="#DDE1E5",
            fg="#1E293B"
        )
        lbl_title.place(relx=0.5, y=25, anchor="center")

#============== 2. FORMULARIO ======================================================================#
        frame_box = tk.LabelFrame(
            self,
            text="Formato Monetario",
            font=("sans", 12, "bold"),
            bg="#C6D9E3",
            fg="#1E293B",
            padx=20,
            pady=15
        )
        frame_box.place(x=20, y=55, width=600, height=330)

        # Nombre de la Moneda
        lbl_nom = tk.Label(frame_box, text="Nombre de la Moneda:", font=("sans", 10, "bold"), bg="#C6D9E3", fg="#1E293B")
        lbl_nom.place(x=15, y=10)

        self.ent_nombre = ttk.Entry(frame_box, font=("sans", 11))
        self.ent_nombre.place(x=15, y=32, width=250, height=30)

        # Código ISO
        lbl_iso = tk.Label(frame_box, text="Código ISO:", font=("sans", 10, "bold"), bg="#C6D9E3", fg="#1E293B")
        lbl_iso.place(x=300, y=10)

        self.ent_iso = ttk.Entry(frame_box, font=("sans", 11), justify="center")
        self.ent_iso.place(x=300, y=32, width=240, height=30)

        # Símbolo
        lbl_sim = tk.Label(frame_box, text="Símbolo:", font=("sans", 10, "bold"), bg="#C6D9E3", fg="#1E293B")
        lbl_sim.place(x=15, y=75)

        self.ent_simbolo = ttk.Entry(frame_box, font=("sans", 11), justify="center")
        self.ent_simbolo.place(x=15, y=98, width=250, height=30)

        # Posición
        lbl_pos = tk.Label(frame_box, text="Posición del Símbolo:", font=("sans", 10, "bold"), bg="#C6D9E3", fg="#1E293B")
        lbl_pos.place(x=300, y=75)

        self.cmb_pos = ttk.Combobox(frame_box, values=["Izquierda ($ 100.00)", "Derecha (100.00 $)"], font=("sans", 10), state="readonly")
        self.cmb_pos.current(0)
        self.cmb_pos.place(x=300, y=98, width=240, height=30)

        # Separador Miles & Decimales
        lbl_mil = tk.Label(frame_box, text="Separador de Miles:", font=("sans", 10, "bold"), bg="#C6D9E3", fg="#1E293B")
        lbl_mil.place(x=15, y=140)

        self.cmb_miles = ttk.Combobox(frame_box, values=["Punto (.)", "Coma (,)", "Espacio ( )"], font=("sans", 10), state="readonly")
        self.cmb_miles.current(0)
        self.cmb_miles.place(x=15, y=163, width=250, height=30)

        lbl_dec = tk.Label(frame_box, text="Separador Decimal:", font=("sans", 10, "bold"), bg="#C6D9E3", fg="#1E293B")
        lbl_dec.place(x=300, y=140)

        self.cmb_decimal = ttk.Combobox(frame_box, values=["Punto (.)", "Coma (,)"], font=("sans", 10), state="readonly")
        self.cmb_decimal.current(1)
        self.cmb_decimal.place(x=300, y=163, width=240, height=30)

        # Vista Previa
        lbl_prev_tag = tk.Label(frame_box, text="Vista Previa de Precio:", font=("sans", 10, "bold"), bg="#C6D9E3", fg="#475569")
        lbl_prev_tag.place(x=15, y=210)

        self.lbl_preview = tk.Label(frame_box, text="$ 150.000,00", font=("sans", 14, "bold"), bg="white", fg="#16A34A", relief="solid", bd=1)
        self.lbl_preview.place(x=15, y=235, width=525, height=36)

#============== 3. BOTONES INFERIORES ===============================================================#
        ruta_save = self.rutas("icono/guardar.png")
        if os.path.exists(ruta_save):
            self.images["save_mon_ico"] = ImageTk.PhotoImage(Image.open(ruta_save).resize((22, 22), Image.Resampling.LANCZOS))
            ico_s = self.images["save_mon_ico"]
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
        btn_save.place(x=140, y=410, width=200, height=44)

        ruta_canc = self.rutas("icono/cancelar.png")
        if os.path.exists(ruta_canc):
            self.images["canc_mon_ico"] = ImageTk.PhotoImage(Image.open(ruta_canc).resize((22, 22), Image.Resampling.LANCZOS))
            ico_c = self.images["canc_mon_ico"]
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
        btn_canc.place(x=360, y=410, width=150, height=44)

    def cargar_datos(self):
        try:
            row = self.servicio_configuracion.obtener_moneda()
            if row:
                    self.ent_nombre.insert(0, row[0] or "Peso Dominicano")
                    self.ent_simbolo.insert(0, row[1] or "RD$")
                    self.ent_iso.insert(0, row[2] or "DOP")
                    return
        except Exception:
            pass

        self.ent_nombre.insert(0, "Peso Dominicano")
        self.ent_iso.insert(0, "DOP")
        self.ent_simbolo.insert(0, "RD$")

    def guardar_datos(self):
        nom = self.ent_nombre.get().strip()
        sim = self.ent_simbolo.get().strip()
        iso = self.ent_iso.get().strip()

        try:
            self.servicio_configuracion.guardar_moneda((nom, sim, iso))
            messagebox.showinfo("Éxito", "Configuración monetaria guardada correctamente.")
            self.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"Error guardando moneda: {e}")
