import os
import sys
import tkinter as tk
from tkinter import messagebox, ttk
from PIL import Image, ImageTk
from window_utils import posicionar_ventana

class StockMinimoModal(tk.Toplevel):
    def __init__(self, parent, stock_actual=10, callback_guardar=None):
        super().__init__(parent)
        self.parent = parent
        self.callback_guardar = callback_guardar
        self.title("Configurar Stock Mínimo")
        posicionar_ventana(self, 450, 260, parent)
        self.resizable(False, False)
        self.configure(bg="#C6D9E3")
        self.transient(parent)
        self.grab_set()
        try:
            self.iconbitmap(self.rutas('icono.ico'))
        except Exception:
            pass

        self.images = {}
        self.widgets(stock_actual)

    def rutas(self, ruta):
        try:
            rutabase = sys.__MEIPASS
        except Exception:
            rutabase = os.path.abspath(".")
        return os.path.join(rutabase, ruta)

    def widgets(self, stock_actual):
        frame_box = tk.LabelFrame(
            self,
            text="Stock mínimo global",
            font=("sans", 14, "bold"),
            bg="#C6D9E3",
            fg="#1E293B",
            padx=15,
            pady=15
        )
        frame_box.place(x=20, y=15, width=410, height=220)

        lbl_tag = tk.Label(frame_box, text="Stock mínimo:", font=("sans", 13, "bold"), bg="#C6D9E3", fg="#1E293B")
        lbl_tag.place(x=20, y=25)

        self.spn_stock = ttk.Spinbox(frame_box, from_=1, to=10000, font=("sans", 13, "bold"), justify="center")
        self.spn_stock.place(x=175, y=22, width=170, height=36)
        self.spn_stock.set(str(stock_actual))

        ruta_save = self.rutas("icono/guardar.png")
        if os.path.exists(ruta_save):
            self.images["save_smm"] = ImageTk.PhotoImage(Image.open(ruta_save).resize((22, 22), Image.Resampling.LANCZOS))
            ico_s = self.images["save_smm"]
        else:
            ico_s = None

        btn_save = tk.Button(
            frame_box,
            text="  Guardar",
            image=ico_s,
            compound=tk.LEFT,
            font=("sans", 12, "bold"),
            bg="#EBEFF2",
            fg="#1E293B",
            relief="raised",
            bd=2,
            cursor="hand2",
            command=self.guardar
        )
        btn_save.place(relx=0.5, y=120, width=160, height=44, anchor="center")

    def guardar(self):
        try:
            val = int(self.spn_stock.get().strip())
            messagebox.showinfo("Stock Mínimo", f"Stock mínimo global configurado en {val} unidades.")
            if self.callback_guardar:
                self.callback_guardar(val)
            self.destroy()
        except ValueError:
            messagebox.showerror("Error", "Ingrese un número entero válido.")
