import os
import csv
import datetime
import db_conexion as sqlite3
import sys
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageTk
from window_utils import posicionar_ventana
from servicios.servicio_caja import ServicioCaja

class MovimientosBancarios(tk.Toplevel):
    def __init__(self, parent, banco_nom="", cuenta_num=""):
        super().__init__(parent)
        self.parent = parent
        user_info = getattr(getattr(parent, "controlador", None), "usuario_actual", {}) or {}
        self.usuario = getattr(parent, "usuario", None) or user_info.get("nombre") or user_info.get("username")
        self.banco_nom = banco_nom
        self.cuenta_num = cuenta_num
        self.title(f"Movimientos Bancarios - {banco_nom}")
        posicionar_ventana(self, 980, 600, parent)
        self.resizable(False, False)
        self.configure(bg="#DDE1E5")
        self.transient(parent)
        self.grab_set()
        try:
            self.iconbitmap(self.rutas('icono.ico'))
        except Exception:
            pass

        self.images = {}
        self.movimientos = []
        self.servicio_caja = ServicioCaja()

        self.widgets()
        self.cargar_movimientos()

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
            text="MOVIMIENTOS BANCARIOS",
            font=("sans", 24, "bold"),
            bg="#DDE1E5",
            fg="#1E293B"
        )
        lbl_title.place(relx=0.5, y=25, anchor="center")

        lbl_sub = tk.Label(
            self,
            text=f"Banco: {self.banco_nom} | Cuenta: {self.cuenta_num}",
            font=("sans", 12, "bold"),
            bg="#DDE1E5",
            fg="#475569"
        )
        lbl_sub.place(relx=0.5, y=55, anchor="center")

#============== 2. TABLA DE MOVIMIENTOS ============================================================#
        style = ttk.Style()
        style.configure("MB.Treeview.Heading", font=("sans", 9, "bold"), background="#E0E6ED")
        style.configure("MB.Treeview", font=("sans", 9), rowheight=24)

        cols = ("id", "tipo", "concepto", "monto", "fecha", "saldo")
        self.tabla = ttk.Treeview(self, columns=cols, show="headings", style="MB.Treeview")
        self.tabla.place(x=20, y=85, width=940, height=345)

        titulos = [
            ("id", "ID", 60),
            ("tipo", "Tipo", 120),
            ("concepto", "Concepto", 280),
            ("monto", "Monto", 140),
            ("fecha", "Fecha", 170),
            ("saldo", "Saldo", 150),
        ]

        for c, t, w in titulos:
            self.tabla.heading(c, text=t, anchor="center")
            self.tabla.column(c, width=w, anchor="center" if c in ("id", "tipo", "fecha") else "e" if c in ("monto", "saldo") else "w")

        scroll_y = ttk.Scrollbar(self, orient="vertical", command=self.tabla.yview)
        self.tabla.configure(yscrollcommand=scroll_y.set)
        scroll_y.place(x=950, y=85, height=345)

#============== 3. REGISTRAR NUEVO MOVIMIENTO =======================================================#
        frame_nuevo = tk.LabelFrame(
            self,
            text="Registrar Nuevo Movimiento",
            font=("sans", 12, "bold"),
            bg="#C6D9E3",
            fg="#1E293B",
            padx=12,
            pady=6
        )
        frame_nuevo.place(x=20, y=440, width=940, height=140)

        # Fila de inputs
        lbl_t = tk.Label(frame_nuevo, text="Tipo:", font=("sans", 10, "bold"), bg="#C6D9E3", fg="#1E293B")
        lbl_t.place(x=15, y=5)

        self.cmb_tipo = ttk.Combobox(frame_nuevo, values=["Depósito", "Retiro", "Transferencia", "Inicial"], font=("sans", 10), state="readonly")
        self.cmb_tipo.current(0)
        self.cmb_tipo.place(x=15, y=28, width=170, height=28)

        lbl_c = tk.Label(frame_nuevo, text="Concepto:", font=("sans", 10, "bold"), bg="#C6D9E3", fg="#1E293B")
        lbl_c.place(x=210, y=5)

        self.ent_concepto = ttk.Entry(frame_nuevo, font=("sans", 10))
        self.ent_concepto.place(x=210, y=28, width=330, height=28)

        lbl_m = tk.Label(frame_nuevo, text="Monto:", font=("sans", 10, "bold"), bg="#C6D9E3", fg="#1E293B")
        lbl_m.place(x=560, y=5)

        self.ent_monto = ttk.Entry(frame_nuevo, font=("sans", 10), justify="right")
        self.ent_monto.place(x=560, y=28, width=170, height=28)

        # Fila de botones
        ruta_reg = self.rutas("icono/guardar.png")
        if os.path.exists(ruta_reg):
            self.images["reg_mb_ico"] = ImageTk.PhotoImage(Image.open(ruta_reg).resize((20, 20), Image.Resampling.LANCZOS))
            ico_r = self.images["reg_mb_ico"]
        else:
            ico_r = None

        btn_reg = tk.Button(frame_nuevo, text="  Registrar", image=ico_r, compound=tk.LEFT, font=("sans", 10, "bold"), bg="#EBEFF2", fg="#1E293B", relief="raised", bd=2, cursor="hand2", command=self.registrar)
        btn_reg.place(x=15, y=68, width=135, height=36)

        ruta_lim = self.rutas("icono/limpiar.png")
        if os.path.exists(ruta_lim):
            self.images["lim_mb_ico"] = ImageTk.PhotoImage(Image.open(ruta_lim).resize((20, 20), Image.Resampling.LANCZOS))
            ico_l = self.images["lim_mb_ico"]
        else:
            ico_l = None

        btn_lim = tk.Button(frame_nuevo, text="  Limpiar", image=ico_l, compound=tk.LEFT, font=("sans", 10, "bold"), bg="#EBEFF2", fg="#1E293B", relief="raised", bd=2, cursor="hand2", command=self.limpiar)
        btn_lim.place(x=165, y=68, width=135, height=36)

        ruta_ed = self.rutas("icono/editar.png")
        if os.path.exists(ruta_ed):
            self.images["ed_mb_ico"] = ImageTk.PhotoImage(Image.open(ruta_ed).resize((20, 20), Image.Resampling.LANCZOS))
            ico_e = self.images["ed_mb_ico"]
        else:
            ico_e = None

        btn_ed = tk.Button(frame_nuevo, text="  Editar", image=ico_e, compound=tk.LEFT, font=("sans", 10, "bold"), bg="#EBEFF2", fg="#1E293B", relief="raised", bd=2, cursor="hand2")
        btn_ed.place(x=315, y=68, width=135, height=36)

        ruta_del = self.rutas("icono/eliminar.png")
        if os.path.exists(ruta_del):
            self.images["del_mb_ico"] = ImageTk.PhotoImage(Image.open(ruta_del).resize((20, 20), Image.Resampling.LANCZOS))
            ico_d = self.images["del_mb_ico"]
        else:
            ico_d = None

        btn_del = tk.Button(frame_nuevo, text="  Eliminar", image=ico_d, compound=tk.LEFT, font=("sans", 10, "bold"), bg="#EF4444", fg="white", relief="raised", bd=2, cursor="hand2")
        btn_del.place(x=465, y=68, width=135, height=36)

        ruta_pdf = self.rutas("icono/pdf.png")
        if os.path.exists(ruta_pdf):
            self.images["pdf_mb_ico"] = ImageTk.PhotoImage(Image.open(ruta_pdf).resize((20, 20), Image.Resampling.LANCZOS))
            ico_p = self.images["pdf_mb_ico"]
        else:
            ico_p = None

        btn_pdf = tk.Button(frame_nuevo, text="  Exportar PDF", image=ico_p, compound=tk.LEFT, font=("sans", 10, "bold"), bg="#15803D", fg="white", relief="raised", bd=2, cursor="hand2", command=self.exportar_pdf)
        btn_pdf.place(x=615, y=68, width=155, height=36)

    def cargar_movimientos(self):
        for r in self.tabla.get_children():
            self.tabla.delete(r)

        self.movimientos = []
        try:
            with sqlite3.connect("database.db") as conn:
                filas = conn.execute("""
                    SELECT id, COALESCE(tipo_movimiento, tipo), concepto, monto, fecha, saldo
                    FROM movimientos_bancarios
                    WHERE banco = ? AND numero_cuenta = ? ORDER BY fecha, id
                """, (self.banco_nom, self.cuenta_num)).fetchall()
            self.movimientos = [(i, t, c, f"$ {float(m or 0):,.2f}", str(f), f"$ {float(s or 0):,.2f}") for i, t, c, m, f, s in filas]
        except Exception:
            self.movimientos = []

        for m in self.movimientos:
            self.tabla.insert("", tk.END, values=m)

    def registrar(self):
        conc = self.ent_concepto.get().strip()
        mont = self.ent_monto.get().strip()
        tip = self.cmb_tipo.get()

        if not conc or not mont:
            messagebox.showwarning("Atención", "Ingrese el concepto y el monto del movimiento.")
            return

        try:
            m_val = float(mont.replace("$", "").replace(",", ""))
            if m_val <= 0:
                raise ValueError
            self.servicio_caja.registrar_movimiento_bancario(self.banco_nom, self.cuenta_num, tip, conc, m_val, getattr(self, "usuario", None))
            self.cargar_movimientos()
            messagebox.showinfo("Éxito", "Movimiento bancario registrado exitosamente.")
            self.limpiar()
        except ValueError:
            messagebox.showerror("Error", "Ingrese un monto numérico válido.")

    def limpiar(self):
        self.ent_concepto.delete(0, tk.END)
        self.ent_monto.delete(0, tk.END)

    def exportar_pdf(self):
        destino = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("Archivo CSV", "*.csv")], initialfile="Movimientos_Bancarios.csv")
        if not destino:
            return
        try:
            with open(destino, "w", newline="", encoding="utf-8-sig") as archivo:
                writer = csv.writer(archivo)
                writer.writerow(["ID", "Tipo", "Concepto", "Monto", "Fecha", "Saldo"])
                writer.writerows(self.movimientos)
            messagebox.showinfo("Exportar", f"Movimientos exportados en:\n{destino}")
        except Exception as error:
            messagebox.showerror("Error", f"No se pudo exportar: {error}")
