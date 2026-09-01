import os
import sys
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
from window_utils import posicionar_ventana

class DestinoGastoModal(tk.Toplevel):
    def __init__(self, parent, callback_destino=None):
        super().__init__(parent)
        self.parent = parent
        self.callback_destino = callback_destino
        self.title("Destino del Gasto")
        posicionar_ventana(self, 540, 240, parent)
        self.resizable(False, False)
        self.configure(bg="#C6D9E3")
        self.transient(parent)
        self.grab_set()
        try:
            self.iconbitmap(self.rutas('icono.ico'))
        except Exception:
            pass

        self.images = {}
        self.widgets()

    def rutas(self, ruta):
        try:
            rutabase = sys.__MEIPASS
        except Exception:
            rutabase = os.path.abspath(".")
        return os.path.join(rutabase, ruta)

    def widgets(self):
        lbl_title = tk.Label(
            self,
            text="¿Dónde desea registrar el gasto?",
            font=("sans", 16, "bold"),
            bg="#C6D9E3",
            fg="#1E293B"
        )
        lbl_title.place(relx=0.5, y=35, anchor="center")

        opciones = [
            ("Caja Abierta", "abrircaja.png", 20, "Caja"),
            ("Banco", "btnbanco.png", 190, "Banco"),
            ("Solo Registro", "historialprecios.png", 360, "Registro"),
        ]

        for txt, ico_f, x_pos, dest_key in opciones:
            ruta_i = self.rutas(f"icono/{ico_f}")
            if not os.path.exists(ruta_i):
                ruta_i = self.rutas("icono/guardar.png")

            if os.path.exists(ruta_i):
                img_i = Image.open(ruta_i).resize((32, 32), Image.Resampling.LANCZOS)
                self.images[f"dg_{ico_f}"] = ImageTk.PhotoImage(img_i)
                ico_btn = self.images[f"dg_{ico_f}"]
            else:
                ico_btn = None

            btn = tk.Button(
                self,
                text=f"  {txt}",
                image=ico_btn,
                compound=tk.LEFT,
                font=("sans", 11, "bold"),
                bg="#EBEFF2",
                fg="#1E293B",
                relief="raised",
                bd=2,
                cursor="hand2",
                command=lambda d=dest_key: self.seleccionar(d)
            )
            btn.place(x=x_pos, y=95, width=160, height=65)

    def seleccionar(self, destino):
        self.destroy()
        if self.callback_destino:
            self.callback_destino(destino)
