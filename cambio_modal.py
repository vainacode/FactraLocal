import os
import sys
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
from window_utils import posicionar_ventana

class CambioModal(tk.Toplevel):
    def __init__(self, parent, total_pagar=0.0, dinero_recibido=0.0, cambio=0.0, medio_pago="Efectivo", callback_continuar=None):
        super().__init__(parent)
        self.parent = parent
        self.total_pagar = total_pagar
        self.dinero_recibido = dinero_recibido
        self.cambio = cambio
        self.medio_pago = medio_pago
        self.callback_continuar = callback_continuar

        self.title("Dinero a Devolver - Cambio")
        posicionar_ventana(self, 540, 440, parent)
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
#============== 1. HEADER ==========================================================================#
        lbl_title = tk.Label(
            self,
            text="CAMBIO A DEVOLVER",
            font=("sans", 20, "bold"),
            bg="#C6D9E3",
            fg="#1E293B"
        )
        lbl_title.place(relx=0.5, y=30, anchor="center")

        lbl_sub = tk.Label(
            self,
            text=f"Medio de Pago: {self.medio_pago}",
            font=("sans", 11, "italic"),
            bg="#C6D9E3",
            fg="#475569"
        )
        lbl_sub.place(relx=0.5, y=55, anchor="center")

#============== 2. TARJETAS DE VALORES =============================================================#
        frame_cards = tk.Frame(self, bg="#C6D9E3")
        frame_cards.place(x=20, y=75, width=500, height=275)

        # Card 1: Total a Pagar
        frame_tot = tk.Frame(frame_cards, bg="#F1F5F9", highlightbackground="#CBD5E1", highlightthickness=1)
        frame_tot.place(x=15, y=5, width=225, height=75)

        tk.Label(frame_tot, text="Total Factura", font=("sans", 9, "bold"), bg="#F1F5F9", fg="#64748B").pack(anchor="w", padx=12, pady=(6, 0))
        tk.Label(frame_tot, text=f"$ {self.total_pagar:,.2f}", font=("sans", 14, "bold"), bg="#F1F5F9", fg="#0F172A").pack(anchor="w", padx=12, pady=(2, 0))

        # Card 2: Dinero Recibido
        frame_rec = tk.Frame(frame_cards, bg="#F1F5F9", highlightbackground="#CBD5E1", highlightthickness=1)
        frame_rec.place(x=260, y=5, width=225, height=75)

        tk.Label(frame_rec, text="Dinero Recibido", font=("sans", 9, "bold"), bg="#F1F5F9", fg="#64748B").pack(anchor="w", padx=12, pady=(6, 0))
        tk.Label(frame_rec, text=f"$ {self.dinero_recibido:,.2f}", font=("sans", 14, "bold"), bg="#F1F5F9", fg="#0284C7").pack(anchor="w", padx=12, pady=(2, 0))

        # Card 3: CAMBIO / DEVUELTA (GRANDE Y DESTACADO)
        frame_cambio = tk.Frame(frame_cards, bg="#DCFCE7", highlightbackground="#22C55E", highlightthickness=2)
        frame_cambio.place(x=15, y=95, width=470, height=165)

        ruta_din = self.rutas("icono/ingresodinero.png")
        if not os.path.exists(ruta_din):
            ruta_din = self.rutas("icono/pago.png")

        if os.path.exists(ruta_din):
            self.images["din_ico"] = ImageTk.PhotoImage(Image.open(ruta_din).resize((44, 44), Image.Resampling.LANCZOS))
            lbl_ico = tk.Label(frame_cambio, image=self.images["din_ico"], bg="#DCFCE7")
            lbl_ico.place(x=25, y=35)

        tk.Label(
            frame_cambio,
            text="ENTREGAR AL CLIENTE:",
            font=("sans", 12, "bold"),
            bg="#DCFCE7",
            fg="#15803D"
        ).place(x=95, y=25)

        lbl_val_cambio = tk.Label(
            frame_cambio,
            text=f"$ {self.cambio:,.2f}",
            font=("sans", 30, "bold"),
            bg="#DCFCE7",
            fg="#16A34A"
        )
        lbl_val_cambio.place(x=95, y=60)

#============== 3. BOTÓN CONTINUAR =================================================================#
        ruta_ok = self.rutas("icono/guardar.png")
        if os.path.exists(ruta_ok):
            self.images["ok_camb_ico"] = ImageTk.PhotoImage(Image.open(ruta_ok).resize((22, 22), Image.Resampling.LANCZOS))
            ico_ok = self.images["ok_camb_ico"]
        else:
            ico_ok = None

        btn_cont = tk.Button(
            self,
            text="  Continuar y Generar Factura",
            image=ico_ok,
            compound=tk.LEFT,
            font=("sans", 12, "bold"),
            bg="#22C55E",
            fg="white",
            relief="raised",
            bd=2,
            cursor="hand2",
            command=self.continuar
        )
        btn_cont.place(relx=0.5, y=388, width=300, height=48, anchor="center")

        # Atajo teclado Enter
        self.bind("<Return>", lambda e: self.continuar())
        self.focus_set()

    def continuar(self):
        self.destroy()
        if self.callback_continuar:
            self.callback_continuar()
