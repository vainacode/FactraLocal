import os
import sys
import tkinter as tk
from tkinter import messagebox, ttk
from PIL import Image, ImageTk
from window_utils import posicionar_ventana

class CatalogoPdfModal(tk.Toplevel):
    def __init__(self, parent, callback_generar=None):
        super().__init__(parent)
        self.parent = parent
        self.callback_generar = callback_generar
        self.title("Opciones de Catálogo PDF")
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
            text="GENERAR CATÁLOGO PDF",
            font=("sans", 18, "bold"),
            bg="#C6D9E3",
            fg="#1E293B"
        )
        lbl_title.place(relx=0.5, y=30, anchor="center")

#============== 2. OPCIONES DE CATÁLOGO ============================================================#
        frame_box = tk.LabelFrame(
            self,
            text="Opciones de Catálogo",
            font=("sans", 13, "bold"),
            bg="#C6D9E3",
            fg="#1E293B",
            padx=20,
            pady=15
        )
        frame_box.place(x=20, y=60, width=500, height=280)

        # Tipo de Catálogo
        lbl_tc = tk.Label(frame_box, text="Tipo de Catálogo:", font=("sans", 12, "bold"), bg="#C6D9E3", fg="#1E293B")
        lbl_tc.pack(anchor="w", pady=(0, 8))

        self.tipo_cat = tk.StringVar(value="con_stock")

        rb_sin_stock = ttk.Radiobutton(
            frame_box,
            text="Catálogo sin información de stock",
            value="sin_stock",
            variable=self.tipo_cat
        )
        rb_sin_stock.pack(anchor="w", padx=15, pady=3)

        rb_con_stock = ttk.Radiobutton(
            frame_box,
            text="Catálogo con información de stock",
            value="con_stock",
            variable=self.tipo_cat
        )
        rb_con_stock.pack(anchor="w", padx=15, pady=3)

        # Línea Separadora
        tk.Frame(frame_box, bg="#CBD5E1", height=1).pack(fill="x", pady=15)

        # Productos a Incluir
        lbl_pi = tk.Label(frame_box, text="Productos a Incluir:", font=("sans", 12, "bold"), bg="#C6D9E3", fg="#1E293B")
        lbl_pi.pack(anchor="w", pady=(0, 8))

        self.incluir_prod = tk.StringVar(value="todos")

        rb_todos = ttk.Radiobutton(
            frame_box,
            text="Todos los productos",
            value="todos",
            variable=self.incluir_prod
        )
        rb_todos.pack(anchor="w", padx=15, pady=3)

        rb_disp = ttk.Radiobutton(
            frame_box,
            text="Solo productos con stock disponible",
            value="disponibles",
            variable=self.incluir_prod
        )
        rb_disp.pack(anchor="w", padx=15, pady=3)

#============== 3. BOTONES INFERIORES ===============================================================#
        btn_gen = tk.Button(
            self,
            text="Generar Catálogo",
            font=("sans", 12, "bold"),
            bg="#22C55E",
            fg="white",
            relief="raised",
            bd=2,
            cursor="hand2",
            command=self.generar
        )
        btn_gen.place(x=85, y=365, width=180, height=44)

        btn_cancel = tk.Button(
            self,
            text="Cancelar",
            font=("sans", 12, "bold"),
            bg="#EF4444",
            fg="white",
            relief="raised",
            bd=2,
            cursor="hand2",
            command=self.destroy
        )
        btn_cancel.place(x=285, y=365, width=170, height=44)

    def generar(self):
        t = self.tipo_cat.get()
        p = self.incluir_prod.get()
        messagebox.showinfo(
            "Catálogo Generado",
            f"Catálogo de productos PDF generado exitosamente.\n\nTipo: {'Con Stock' if t == 'con_stock' else 'Sin Stock'}\nProductos: {'Todos' if p == 'todos' else 'Solo con Stock'}"
        )
        if self.callback_generar:
            self.callback_generar(t, p)
        self.destroy()
