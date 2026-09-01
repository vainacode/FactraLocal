import os
import db_conexion as sqlite3
import sys
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
from window_utils import posicionar_ventana

class DetalleComboModal(tk.Toplevel):
    def __init__(self, parent, combo_nombre="Teclado + Mouse"):
        super().__init__(parent)
        self.parent = parent
        self.combo_nombre = combo_nombre
        self.title(f"Detalles del Combo: {combo_nombre}")
        posicionar_ventana(self, 820, 460, parent)
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
        self.cargar_datos()

    def rutas(self, ruta):
        try:
            rutabase = sys.__MEIPASS
        except Exception:
            rutabase = os.path.abspath(".")
        return os.path.join(rutabase, ruta)

    def widgets(self):
#============== 1. INFORMACIÓN DEL COMBO ============================================================#
        frame_info = tk.LabelFrame(
            self,
            text="Información del Combo",
            font=("sans", 13, "bold"),
            bg="#C6D9E3",
            fg="#1E293B",
            padx=15,
            pady=10
        )
        frame_info.place(x=15, y=10, width=790, height=135)

        # Columna 1
        lbl_nom_tag = tk.Label(frame_info, text="Nombre:", font=("sans", 11, "bold"), bg="#C6D9E3", fg="#1E293B")
        lbl_nom_tag.place(x=10, y=8)
        self.lbl_nombre = tk.Label(frame_info, text=self.combo_nombre, font=("sans", 11), bg="#C6D9E3", fg="#1E293B")
        self.lbl_nombre.place(x=150, y=8)

        lbl_pv_tag = tk.Label(frame_info, text="Precio de Venta:", font=("sans", 11, "bold"), bg="#C6D9E3", fg="#1E293B")
        lbl_pv_tag.place(x=10, y=38)
        self.lbl_pv = tk.Label(frame_info, text="$ 0.00", font=("sans", 11, "bold"), bg="#C6D9E3", fg="#16A34A")
        self.lbl_pv.place(x=150, y=38)

        lbl_ct_tag = tk.Label(frame_info, text="Costo Total:", font=("sans", 11, "bold"), bg="#C6D9E3", fg="#1E293B")
        lbl_ct_tag.place(x=10, y=68)
        self.lbl_ct = tk.Label(frame_info, text="$ 0.00", font=("sans", 11, "bold"), bg="#C6D9E3", fg="#DC2626")
        self.lbl_ct.place(x=150, y=68)

        # Columna 2
        lbl_gan_tag = tk.Label(frame_info, text="Ganancia:", font=("sans", 11, "bold"), bg="#C6D9E3", fg="#1E293B")
        lbl_gan_tag.place(x=430, y=38)
        self.lbl_gan = tk.Label(frame_info, text="$ 0.00", font=("sans", 11, "bold"), bg="#C6D9E3", fg="#2563EB")
        self.lbl_gan.place(x=540, y=38)

        lbl_cant_tag = tk.Label(frame_info, text="Cantidad:", font=("sans", 11, "bold"), bg="#C6D9E3", fg="#1E293B")
        lbl_cant_tag.place(x=430, y=68)
        self.lbl_cant = tk.Label(frame_info, text="0 unidad(es)", font=("sans", 11), bg="#C6D9E3", fg="#1E293B")
        self.lbl_cant.place(x=540, y=68)

#============== 2. PRODUCTOS DEL COMBO =============================================================#
        frame_prods = tk.LabelFrame(
            self,
            text="Productos del Combo",
            font=("sans", 13, "bold"),
            bg="#C6D9E3",
            fg="#1E293B",
            padx=10,
            pady=8
        )
        frame_prods.place(x=15, y=155, width=790, height=225)

        style = ttk.Style()
        style.configure("DetCombo.Treeview.Heading", font=("sans", 9, "bold"), background="#E0E6ED")
        style.configure("DetCombo.Treeview", font=("sans", 10), rowheight=24)

        cols = ("producto", "cantidad", "costo_u", "subtotal")
        self.tabla = ttk.Treeview(frame_prods, columns=cols, show="headings", style="DetCombo.Treeview")
        self.tabla.place(x=10, y=10, width=745, height=175)

        titulos = [
            ("producto", "Producto", 390),
            ("cantidad", "Cantidad", 110),
            ("costo_u", "Costo Unitario", 120),
            ("subtotal", "Subtotal", 120),
        ]

        for c, t, w in titulos:
            self.tabla.heading(c, text=t, anchor="center")
            self.tabla.column(c, width=w, anchor="w" if c == "producto" else "center" if c == "cantidad" else "e")

        scroll_y = ttk.Scrollbar(frame_prods, orient="vertical", command=self.tabla.yview)
        self.tabla.configure(yscrollcommand=scroll_y.set)
        scroll_y.place(x=755, y=10, height=175)

#============== 3. BOTÓN CERRAR ====================================================================#
        ruta_close = self.rutas("icono/cancelar.png")
        if os.path.exists(ruta_close):
            img_c = Image.open(ruta_close).resize((22, 22), Image.Resampling.LANCZOS)
            self.images["close_det_cmb"] = ImageTk.PhotoImage(img_c)
            ico_c = self.images["close_det_cmb"]
        else:
            ico_c = None

        btn_close = tk.Button(
            self,
            text="  Cerrar",
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
        btn_close.place(relx=0.5, y=410, width=130, height=38, anchor="center")

    def cargar_datos(self):
        for r in self.tabla.get_children():
            self.tabla.delete(r)

        items = []
        try:
            with sqlite3.connect("database.db") as conn:
                filas = conn.execute("""
                    SELECT producto, cantidad, costo_unitario, subtotal
                    FROM combo_detalle WHERE combo_nombre = ?
                """, (self.combo_nombre,)).fetchall()
            items = [(p, f"{c}", f"$ {float(cu or 0):,.2f}", f"$ {float(st or 0):,.2f}") for p, c, cu, st in filas]
        except Exception:
            # La base existente puede no tener todavía el módulo de detalle.
            # No se muestran productos inventados en ese caso.
            items = []
        for it in items:
            self.tabla.insert("", tk.END, values=it)
