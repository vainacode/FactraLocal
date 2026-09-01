import datetime
import os
import db_conexion as sqlite3
import sys
import tkinter as tk
from tkinter import messagebox, ttk
from PIL import Image, ImageTk
from window_utils import posicionar_ventana
from servicios.servicio_caja import ServicioCaja

class AbrirCajaModal(tk.Toplevel):
    def __init__(self, parent, usuario="", callback_exito=None):
        super().__init__(parent)
        self.parent = parent
        self.usuario = usuario
        self.callback_exito = callback_exito
        self.title("Apertura de Turno de Caja")
        posicionar_ventana(self, 520, 420, parent)
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

        self.widgets()

    def rutas(self, ruta):
        try:
            rutabase = sys.__MEIPASS
        except Exception:
            rutabase = os.path.abspath(".")
        return os.path.join(rutabase, ruta)

    def widgets(self):
        # Header
        lbl_title = tk.Label(
            self,
            text="APERTURA DE CAJA",
            font=("sans", 18, "bold"),
            bg="#DDE1E5",
            fg="#1E293B"
        )
        lbl_title.place(relx=0.5, y=25, anchor="center")

        # Contenedor Formulario
        frame_box = tk.LabelFrame(
            self,
            text="Datos de la Apertura",
            font=("sans", 11, "bold"),
            bg="#C6D9E3",
            fg="#1E293B",
            padx=15,
            pady=10
        )
        frame_box.place(x=20, y=55, width=480, height=280)

        # 1. Cajero / Usuario
        lbl_caj = tk.Label(frame_box, text="Cajero Responsable:", font=("sans", 10, "bold"), bg="#C6D9E3", fg="#1E293B")
        lbl_caj.place(x=15, y=10)

        self.ent_cajero = ttk.Entry(frame_box, font=("sans", 11))
        self.ent_cajero.insert(0, self.usuario)
        self.ent_cajero.config(state="readonly")
        self.ent_cajero.place(x=15, y=32, width=420, height=30)

        # 2. Monto Inicial (Fondo de Caja)
        lbl_monto = tk.Label(frame_box, text="Monto Inicial en Efectivo (RD$):", font=("sans", 10, "bold"), bg="#C6D9E3", fg="#1E293B")
        lbl_monto.place(x=15, y=70)

        self.ent_monto = ttk.Entry(frame_box, font=("sans", 12, "bold"), justify="right")
        self.ent_monto.place(x=15, y=92, width=420, height=32)
        self.ent_monto.focus_set()
        self.ent_monto.select_range(0, tk.END)

        # 3. Observaciones / Turno
        lbl_obs = tk.Label(frame_box, text="Observaciones / Turno:", font=("sans", 10, "bold"), bg="#C6D9E3", fg="#1E293B")
        lbl_obs.place(x=15, y=132)

        self.ent_obs = ttk.Entry(frame_box, font=("sans", 11))
        self.ent_obs.place(x=15, y=154, width=420, height=30)

        # 4. Fecha y Hora informativa
        ahora = datetime.datetime.now()
        lbl_fec = tk.Label(
            frame_box,
            text=f"Fecha y Hora: {ahora.strftime('%d/%m/%Y %I:%M:%S %p')}",
            font=("sans", 9, "italic"),
            bg="#C6D9E3",
            fg="#475569"
        )
        lbl_fec.place(x=15, y=200)

        # Botones
        ruta_abrir = self.rutas("icono/abrircaja.png")
        if os.path.exists(ruta_abrir):
            self.images["ab_caja_ico"] = ImageTk.PhotoImage(Image.open(ruta_abrir).resize((22, 22), Image.Resampling.LANCZOS))
            ico_ab = self.images["ab_caja_ico"]
        else:
            ico_ab = None

        btn_confirmar = tk.Button(
            self,
            text="  Abrir Caja",
            image=ico_ab,
            compound=tk.LEFT,
            font=("sans", 11, "bold"),
            bg="#22C55E",
            fg="white",
            relief="raised",
            bd=2,
            cursor="hand2",
            command=self.confirmar_apertura
        )
        btn_confirmar.place(x=100, y=350, width=170, height=44)

        btn_cancelar = tk.Button(
            self,
            text="Cancelar",
            font=("sans", 11, "bold"),
            bg="#EBEFF2",
            fg="#1E293B",
            relief="raised",
            bd=2,
            cursor="hand2",
            command=self.destroy
        )
        btn_cancelar.place(x=290, y=350, width=130, height=44)

    def confirmar_apertura(self):
        if not self.usuario.strip():
            messagebox.showerror("Sesión requerida", "No se puede abrir una caja sin un usuario autenticado.")
            return
        monto_str = self.ent_monto.get().strip().replace("RD$", "").replace("$", "").replace(",", "")
        obs = self.ent_obs.get().strip()

        try:
            monto_inicial = float(monto_str)
            if monto_inicial < 0:
                raise ValueError()
        except ValueError:
            messagebox.showerror("Error", "Ingrese un monto inicial válido (mayor o igual a 0).")
            return

        ahora = datetime.datetime.now()
        fecha_str = ahora.strftime("%Y-%m-%d")
        hora_str = ahora.strftime("%H:%M:%S")

        try:
            ServicioCaja().abrir(self.usuario, monto_inicial, observaciones=obs)

            messagebox.showinfo("Éxito", f"Caja abierta exitosamente con un fondo inicial de RD$ {monto_inicial:,.2f}")
            if self.callback_exito:
                self.callback_exito("ABIERTA", monto_inicial)
            self.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"Error al abrir la caja: {e}")
