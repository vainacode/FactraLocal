import os
import sys
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
from window_utils import posicionar_ventana

class GenerarFacturaModal(tk.Toplevel):
    def __init__(self, parent, factura_id=1, callback_print=None):
        super().__init__(parent)
        self.parent = parent
        self.factura_id = factura_id
        self.callback_print = callback_print
        self.title("Generar Factura")
        posicionar_ventana(self, 620, 420, parent)
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
            text="Selecciona un tipo de Factura",
            font=("sans", 18, "bold"),
            bg="#C6D9E3",
            fg="#1E293B"
        )
        lbl_title.place(relx=0.5, y=30, anchor="center")

        opciones = [
            ("Factura A4", "factura.png", 30, 75, lambda: self.generar("A4")),
            ("Ticket 80 mm", "facturapendiente.png", 225, 75, lambda: self.generar("80mm")),
            ("Ticket 50 mm", "factura.png", 420, 75, lambda: self.generar("50mm")),
            ("No generar", "cancelar.png", 225, 240, self.destroy),
        ]

        for txt, ico_f, x_pos, y_pos, cmd in opciones:
            ruta_i = self.rutas(f"icono/{ico_f}")
            if os.path.exists(ruta_i):
                img_i = Image.open(ruta_i).resize((64, 64), Image.Resampling.LANCZOS)
                self.images[f"opt_{txt}"] = ImageTk.PhotoImage(img_i)
                ico_btn = self.images[f"opt_{txt}"]
            else:
                ico_btn = None

            btn = tk.Button(
                self,
                text=txt,
                image=ico_btn,
                compound=tk.TOP,
                font=("sans", 12, "bold"),
                bg="#EBEFF2",
                fg="#1E293B",
                activebackground="#D5E0E8",
                relief="raised",
                bd=2,
                cursor="hand2",
                command=cmd
            )
            btn.place(x=x_pos, y=y_pos, width=170, height=145)

    def generar(self, formato):
        try:
            from documentos import dialogo_documento, generar_factura
            ruta = generar_factura(self.factura_id, formato=formato)
            dialogo_documento(self, "Factura generada", f"La factura #{self.factura_id} fue preparada en formato {formato}.", ruta)
            if self.callback_print:
                self.callback_print(formato)
            self.destroy()
        except Exception as e:
            from documentos import dialogo_documento
            dialogo_documento(self, "No se pudo generar", str(e), error=True)
