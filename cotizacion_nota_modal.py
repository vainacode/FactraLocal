import os
import sys
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
from window_utils import posicionar_ventana

class CotizacionNotaModal(tk.Toplevel):
    def __init__(self, parent, nota_actual="Cotización con vigencia de 15 días", callback_guardar=None):
        super().__init__(parent)
        self.parent = parent
        self.callback_guardar = callback_guardar
        self.title("Añadir Nota a Cotización")
        posicionar_ventana(self, 520, 340, parent)
        self.resizable(False, False)
        self.configure(bg="#C6D9E3")
        self.transient(parent)
        self.grab_set()
        try:
            self.iconbitmap(self.rutas('icono.ico'))
        except Exception:
            pass

        self.images = {}
        self.widgets(nota_actual)

    def rutas(self, ruta):
        try:
            rutabase = sys.__MEIPASS
        except Exception:
            rutabase = os.path.abspath(".")
        return os.path.join(rutabase, ruta)

    def widgets(self, nota_actual):
        lbl_title = tk.Label(
            self,
            text="Nota de la Cotización",
            font=("sans", 18, "bold"),
            bg="#C6D9E3",
            fg="#1E293B"
        )
        lbl_title.place(relx=0.5, y=25, anchor="center")

        lbl_sub = tk.Label(
            self,
            text="Ingrese la nota para esta cotización:",
            font=("sans", 11, "bold"),
            bg="#C6D9E3",
            fg="#1E293B"
        )
        lbl_sub.place(x=25, y=55)

        self.txt_nota = tk.Text(self, font=("sans", 11), wrap="word", relief="solid", bd=1)
        self.txt_nota.place(x=25, y=85, width=470, height=160)
        self.txt_nota.insert("1.0", nota_actual)
        self.txt_nota.focus_set()

        # Botones inferiores
        ruta_save = self.rutas("icono/guardar.png")
        if os.path.exists(ruta_save):
            self.images["save_cnm"] = ImageTk.PhotoImage(Image.open(ruta_save).resize((22, 22), Image.Resampling.LANCZOS))
            ico_s = self.images["save_cnm"]
        else:
            ico_s = None

        btn_save = tk.Button(
            self,
            text="  Guardar",
            image=ico_s,
            compound=tk.LEFT,
            font=("sans", 11, "bold"),
            bg="#EBEFF2",
            fg="#1E293B",
            relief="raised",
            bd=2,
            cursor="hand2",
            command=self.guardar
        )
        btn_save.place(x=120, y=270, width=130, height=42)

        ruta_close = self.rutas("icono/cancelar.png")
        if os.path.exists(ruta_close):
            self.images["close_cnm"] = ImageTk.PhotoImage(Image.open(ruta_close).resize((22, 22), Image.Resampling.LANCZOS))
            ico_c = self.images["close_cnm"]
        else:
            ico_c = None

        btn_close = tk.Button(
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
        btn_close.place(x=270, y=270, width=130, height=42)

    def guardar(self):
        nota = self.txt_nota.get("1.0", tk.END).strip()
        messagebox.showinfo("Nota Guardada", "Nota de cotización guardada exitosamente.")
        if self.callback_guardar:
            self.callback_guardar(nota)
        self.destroy()
