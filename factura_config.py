import os
import db_conexion as sqlite3
import sys
import tkinter as tk
from tkinter import messagebox, ttk
from PIL import Image, ImageTk
from window_utils import posicionar_ventana

class FacturaConfig(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.title("Editar Factura")
        posicionar_ventana(self, 980, 600, parent)
        self.resizable(False, False)
        self.configure(bg="#C6D9E3")
        self.transient(parent)
        self.grab_set()
        try:
            self.iconbitmap(self.rutas('icono.ico'))
        except Exception:
            pass

        self.db_name = "database.db"
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
            text="EDITAR FACTURA Y TICKET",
            font=("sans", 22, "bold"),
            bg="#C6D9E3",
            fg="#1E293B"
        )
        lbl_title.place(relx=0.5, y=25, anchor="center")

#============== 2. GRUPO TITULOS PRINCIPALES (TOP-LEFT) ============================================#
        frame_titulos = tk.LabelFrame(
            self,
            text="Titulos Principales",
            font=("sans", 11, "bold"),
            bg="#C6D9E3",
            fg="#1E293B",
            padx=10,
            pady=8
        )
        frame_titulos.place(x=15, y=55, width=460, height=155)

        lbl_fa4 = tk.Label(frame_titulos, text="Factura A4:", font=("sans", 10, "bold"), bg="#C6D9E3", fg="#1E293B")
        lbl_fa4.place(x=5, y=10)
        self.ent_fa4 = ttk.Entry(frame_titulos, font=("sans", 10))
        self.ent_fa4.place(x=120, y=8, width=310, height=28)
        self.ent_fa4.insert(0, "Factura De Venta")

        lbl_t80 = tk.Label(frame_titulos, text="Ticket 80mm:", font=("sans", 10, "bold"), bg="#C6D9E3", fg="#1E293B")
        lbl_t80.place(x=5, y=48)
        self.ent_t80 = ttk.Entry(frame_titulos, font=("sans", 10))
        self.ent_t80.place(x=120, y=46, width=310, height=28)
        self.ent_t80.insert(0, "Ticket")

        lbl_t50 = tk.Label(frame_titulos, text="Ticket 50mm:", font=("sans", 10, "bold"), bg="#C6D9E3", fg="#1E293B")
        lbl_t50.place(x=5, y=86)
        self.ent_t50 = ttk.Entry(frame_titulos, font=("sans", 10))
        self.ent_t50.place(x=120, y=84, width=310, height=28)
        self.ent_t50.insert(0, "Ticket")

#============== 3. GRUPO TEXTOS DE PIE DE PÁGINA (TOP-RIGHT) =======================================#
        frame_pie = tk.LabelFrame(
            self,
            text="Textos de Pie de Página",
            font=("sans", 11, "bold"),
            bg="#C6D9E3",
            fg="#1E293B",
            padx=10,
            pady=8
        )
        frame_pie.place(x=495, y=55, width=470, height=155)

        # Agradecimiento
        lbl_agr = tk.Label(frame_pie, text="Agradecimiento:", font=("sans", 10, "bold"), bg="#C6D9E3", fg="#1E293B")
        lbl_agr.place(x=5, y=10)
        self.ent_agr = ttk.Entry(frame_pie, font=("sans", 10))
        self.ent_agr.place(x=135, y=8, width=245, height=28)
        self.ent_agr.insert(0, "¡Gracias por tu visita!")

        self.chk_agr_var = tk.BooleanVar(value=False)
        self.chk_agr = ttk.Checkbutton(frame_pie, text="Ocultar", variable=self.chk_agr_var)
        self.chk_agr.place(x=390, y=10)

        # Información
        lbl_inf = tk.Label(frame_pie, text="Información:", font=("sans", 10, "bold"), bg="#C6D9E3", fg="#1E293B")
        lbl_inf.place(x=5, y=48)
        self.ent_inf = ttk.Entry(frame_pie, font=("sans", 10))
        self.ent_inf.place(x=135, y=46, width=245, height=28)
        self.ent_inf.insert(0, "Siguenos en Facebook @TkPOS")

        self.chk_inf_var = tk.BooleanVar(value=False)
        self.chk_inf = ttk.Checkbutton(frame_pie, text="Ocultar", variable=self.chk_inf_var)
        self.chk_inf.place(x=390, y=48)

        # Copyright
        lbl_cpr = tk.Label(frame_pie, text="Copyright:", font=("sans", 10, "bold"), bg="#C6D9E3", fg="#1E293B")
        lbl_cpr.place(x=5, y=86)
        self.ent_cpr = ttk.Entry(frame_pie, font=("sans", 10))
        self.ent_cpr.place(x=135, y=84, width=245, height=28)
        self.ent_cpr.insert(0, "Instagram TkPOS")

        self.chk_cpr_var = tk.BooleanVar(value=False)
        self.chk_cpr = ttk.Checkbutton(frame_pie, text="Ocultar", variable=self.chk_cpr_var)
        self.chk_cpr.place(x=390, y=86)

#============== 4. GRUPO TEXTOS DE ENCABEZADO (BOTTOM-LEFT) =========================================#
        frame_enc = tk.LabelFrame(
            self,
            text="Textos de Encabezado",
            font=("sans", 11, "bold"),
            bg="#C6D9E3",
            fg="#1E293B",
            padx=10,
            pady=8
        )
        frame_enc.place(x=15, y=220, width=460, height=195)

        # Cliente
        lbl_tc = tk.Label(frame_enc, text="Texto Cliente:", font=("sans", 10, "bold"), bg="#C6D9E3", fg="#1E293B")
        lbl_tc.place(x=5, y=8)
        self.ent_tc = ttk.Entry(frame_enc, font=("sans", 10))
        self.ent_tc.place(x=135, y=6, width=230, height=28)
        self.ent_tc.insert(0, "Cliente")

        self.chk_tc_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(frame_enc, text="Ocultar", variable=self.chk_tc_var).place(x=375, y=8)

        # Factura
        lbl_tf = tk.Label(frame_enc, text="Texto Factura:", font=("sans", 10, "bold"), bg="#C6D9E3", fg="#1E293B")
        lbl_tf.place(x=5, y=46)
        self.ent_tf = ttk.Entry(frame_enc, font=("sans", 10))
        self.ent_tf.place(x=135, y=44, width=230, height=28)
        self.ent_tf.insert(0, "Número de Factura")

        self.chk_tf_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(frame_enc, text="Ocultar", variable=self.chk_tf_var).place(x=375, y=46)

        # Fecha
        lbl_tfe = tk.Label(frame_enc, text="Texto Fecha:", font=("sans", 10, "bold"), bg="#C6D9E3", fg="#1E293B")
        lbl_tfe.place(x=5, y=84)
        self.ent_tfe = ttk.Entry(frame_enc, font=("sans", 10))
        self.ent_tfe.place(x=135, y=82, width=230, height=28)
        self.ent_tfe.insert(0, "Fecha")

        self.chk_tfe_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(frame_enc, text="Ocultar", variable=self.chk_tfe_var).place(x=375, y=84)

        # Cajero
        lbl_tcaj = tk.Label(frame_enc, text="Texto Cajero:", font=("sans", 10, "bold"), bg="#C6D9E3", fg="#1E293B")
        lbl_tcaj.place(x=5, y=122)
        self.ent_tcaj = ttk.Entry(frame_enc, font=("sans", 10))
        self.ent_tcaj.place(x=135, y=120, width=230, height=28)
        self.ent_tcaj.insert(0, "Atendido por")

        self.chk_tcaj_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(frame_enc, text="Ocultar", variable=self.chk_tcaj_var).place(x=375, y=122)

#============== 5. OTRAS OPCIONES (BOTTOM-LEFT LOWER) ===============================================#
        frame_otras = tk.LabelFrame(
            self,
            text="Otras Opciones",
            font=("sans", 11, "bold"),
            bg="#C6D9E3",
            fg="#1E293B",
            padx=10,
            pady=8
        )
        frame_otras.place(x=15, y=425, width=460, height=65)

        self.chk_logo_var = tk.BooleanVar(value=False)
        lbl_ml = tk.Label(frame_otras, text="Mostrar Logo:", font=("sans", 10, "bold"), bg="#C6D9E3", fg="#1E293B")
        lbl_ml.place(x=5, y=6)
        ttk.Checkbutton(frame_otras, text="Ocultar", variable=self.chk_logo_var).place(x=115, y=6)

        self.chk_arts_var = tk.BooleanVar(value=False)
        lbl_ma = tk.Label(frame_otras, text="Mostrar Cant. Articulos:", font=("sans", 10, "bold"), bg="#C6D9E3", fg="#1E293B")
        lbl_ma.place(x=200, y=6)
        ttk.Checkbutton(frame_otras, text="Ocultar", variable=self.chk_arts_var).place(x=375, y=6)

#============== 6. GRUPO INFORMACIÓN (BOTTOM-RIGHT) ================================================#
        frame_info_help = tk.LabelFrame(
            self,
            text="Información",
            font=("sans", 11, "bold"),
            bg="#C6D9E3",
            fg="#1E293B",
            padx=15,
            pady=12
        )
        frame_info_help.place(x=495, y=220, width=470, height=270)

        info_text = (
            "- Personalice los textos que aparecen en sus facturas y tickets.\n\n"
            "- Marque 'Ocultar' en cada campo si no desea que se muestre en la impresión.\n\n"
            "- Los cambios se aplicarán al generar la próxima factura o ticket.\n\n"
            "- No olvide presionar 'Guardar' para conservar los cambios."
        )

        lbl_h_txt = tk.Label(
            frame_info_help,
            text=info_text,
            font=("sans", 10),
            bg="white",
            fg="#334155",
            justify="left",
            wraplength=420,
            padx=12,
            pady=12,
            relief="solid",
            bd=1
        )
        lbl_h_txt.pack(fill="both", expand=True)

#============== 7. BOTONES INFERIORES ===============================================================#
        ruta_save = self.rutas("icono/guardar.png")
        if os.path.exists(ruta_save):
            img_s = Image.open(ruta_save).resize((22, 22), Image.Resampling.LANCZOS)
            self.images["save_fcfg"] = ImageTk.PhotoImage(img_s)
            ico_s = self.images["save_fcfg"]
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
            command=self.guardar_configuracion
        )
        btn_save.place(x=340, y=515, width=150, height=44)

        ruta_close = self.rutas("icono/cancelar.png")
        if os.path.exists(ruta_close):
            img_c = Image.open(ruta_close).resize((22, 22), Image.Resampling.LANCZOS)
            self.images["close_fcfg"] = ImageTk.PhotoImage(img_c)
            ico_c = self.images["close_fcfg"]
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
        btn_close.place(x=515, y=515, width=150, height=44)

    def cargar_datos(self):
        try:
            with sqlite3.connect(self.db_name) as conn:
                cur = conn.cursor()
                cur.execute("SELECT * FROM info_factura LIMIT 1")
                row = cur.fetchone()
                if row:
                    pass
        except Exception:
            pass

    def guardar_configuracion(self):
        messagebox.showinfo("Éxito", "Configuración de factura y ticket guardada exitosamente.")
        self.destroy()
