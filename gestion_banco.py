import os
import db_conexion as sqlite3
import sys
import tkinter as tk
from tkinter import messagebox, ttk
from PIL import Image, ImageTk
from movimientos_bancarios import MovimientosBancarios
from window_utils import posicionar_ventana
from servicios.servicio_caja import ServicioCaja

class GestionBanco(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        user_info = getattr(getattr(parent, "controlador", None), "usuario_actual", {}) or {}
        self.usuario = getattr(parent, "usuario", None) or user_info.get("nombre") or user_info.get("username")
        self.title("Gestión de Banco")
        posicionar_ventana(self, 980, 600, parent)
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
        self.cuentas = []
        self.servicio_caja = ServicioCaja()

        self.widgets()
        self.cargar_cuentas()

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
            text="GESTIÓN DE BANCO",
            font=("sans", 24, "bold"),
            bg="#DDE1E5",
            fg="#1E293B"
        )
        lbl_title.place(relx=0.5, y=25, anchor="center")

#============== 2. REGISTRAR CUENTA ================================================================#
        frame_reg = tk.LabelFrame(
            self,
            text="Registrar cuenta",
            font=("sans", 13, "bold"),
            bg="#C6D9E3",
            fg="#1E293B",
            padx=15,
            pady=8
        )
        frame_reg.place(x=20, y=55, width=940, height=135)

        # Fila 1: Nombre & Tipo
        lbl_nom = tk.Label(frame_reg, text="Nombre:", font=("sans", 11, "bold"), bg="#C6D9E3", fg="#1E293B")
        lbl_nom.place(x=15, y=8)

        self.ent_nombre = ttk.Entry(frame_reg, font=("sans", 11))
        self.ent_nombre.place(x=15, y=32, width=380, height=30)

        lbl_tipo = tk.Label(frame_reg, text="Tipo:", font=("sans", 11, "bold"), bg="#C6D9E3", fg="#1E293B")
        lbl_tipo.place(x=450, y=8)

        self.cmb_tipo = ttk.Combobox(frame_reg, values=["Ahorros", "Corriente"], font=("sans", 11), state="readonly")
        self.cmb_tipo.current(0)
        self.cmb_tipo.place(x=450, y=32, width=380, height=30)

        # Fila 2: Nº Cuenta & Saldo
        lbl_num = tk.Label(frame_reg, text="Nº Cuenta:", font=("sans", 11, "bold"), bg="#C6D9E3", fg="#1E293B")
        lbl_num.place(x=15, y=68)

        self.ent_cuenta = ttk.Entry(frame_reg, font=("sans", 11))
        self.ent_cuenta.place(x=15, y=92, width=380, height=30)

        lbl_sal = tk.Label(frame_reg, text="Saldo:", font=("sans", 11, "bold"), bg="#C6D9E3", fg="#1E293B")
        lbl_sal.place(x=450, y=68)

        self.ent_saldo = ttk.Entry(frame_reg, font=("sans", 11), justify="right")
        self.ent_saldo.place(x=450, y=92, width=380, height=30)

#============== 3. TABLA DE CUENTAS ================================================================#
        style = ttk.Style()
        style.configure("GB.Treeview.Heading", font=("sans", 9, "bold"), background="#E0E6ED")
        style.configure("GB.Treeview", font=("sans", 9), rowheight=24)

        cols = ("id", "nombre", "cuenta", "tipo", "saldo")
        self.tabla = ttk.Treeview(self, columns=cols, show="headings", style="GB.Treeview")
        self.tabla.place(x=20, y=200, width=940, height=270)

        titulos = [
            ("id", "Id", 70),
            ("nombre", "Nombre", 250),
            ("cuenta", "Cuenta", 220),
            ("tipo", "Tipo", 180),
            ("saldo", "Saldo", 200),
        ]

        for c, t, w in titulos:
            self.tabla.heading(c, text=t, anchor="center")
            self.tabla.column(c, width=w, anchor="center" if c in ("id", "tipo", "cuenta") else "e" if c == "saldo" else "w")

        scroll_y = ttk.Scrollbar(self, orient="vertical", command=self.tabla.yview)
        self.tabla.configure(yscrollcommand=scroll_y.set)
        scroll_y.place(x=950, y=200, height=270)

#============== 4. OPCIONES ========================================================================#
        frame_opc = tk.LabelFrame(
            self,
            text="Opciones",
            font=("sans", 12, "bold"),
            bg="#C6D9E3",
            fg="#1E293B",
            padx=15,
            pady=6
        )
        frame_opc.place(x=20, y=480, width=940, height=95)

        # Botón Registrar
        ruta_reg = self.rutas("icono/agregar.png")
        if os.path.exists(ruta_reg):
            self.images["reg_gb_ico"] = ImageTk.PhotoImage(Image.open(ruta_reg).resize((22, 22), Image.Resampling.LANCZOS))
            ico_r = self.images["reg_gb_ico"]
        else:
            ico_r = None

        btn_reg = tk.Button(frame_opc, text="  Registrar", image=ico_r, compound=tk.LEFT, font=("sans", 11, "bold"), bg="#EBEFF2", fg="#1E293B", relief="raised", bd=2, cursor="hand2", command=self.registrar_cuenta)
        btn_reg.place(x=30, y=10, width=220, height=44)

        # Botón Editar
        ruta_ed = self.rutas("icono/editar.png")
        if os.path.exists(ruta_ed):
            self.images["ed_gb_ico"] = ImageTk.PhotoImage(Image.open(ruta_ed).resize((22, 22), Image.Resampling.LANCZOS))
            ico_e = self.images["ed_gb_ico"]
        else:
            ico_e = None

        btn_ed = tk.Button(frame_opc, text="  Editar", image=ico_e, compound=tk.LEFT, font=("sans", 11, "bold"), bg="#EBEFF2", fg="#1E293B", relief="raised", bd=2, cursor="hand2", command=self.editar_cuenta)
        btn_ed.place(x=300, y=10, width=220, height=44)

        # Botón Movimientos
        ruta_mov = self.rutas("icono/btnbanco.png")
        if not os.path.exists(ruta_mov):
            ruta_mov = self.rutas("icono/mediospago.png")

        if os.path.exists(ruta_mov):
            self.images["mov_gb_ico"] = ImageTk.PhotoImage(Image.open(ruta_mov).resize((22, 22), Image.Resampling.LANCZOS))
            ico_m = self.images["mov_gb_ico"]
        else:
            ico_m = None

        btn_mov = tk.Button(frame_opc, text="  Movimientos", image=ico_m, compound=tk.LEFT, font=("sans", 11, "bold"), bg="#EBEFF2", fg="#1E293B", relief="raised", bd=2, cursor="hand2", command=self.ver_movimientos)
        btn_mov.place(x=570, y=10, width=240, height=44)

    def cargar_cuentas(self):
        for r in self.tabla.get_children():
            self.tabla.delete(r)

        try:
            with sqlite3.connect(self.db_name) as conn:
                cur = conn.cursor()
                cur.execute("SELECT id, banco, numero_cuenta, tipo, saldo FROM cuentas_bancarias WHERE estado = 'Activo'")
                rows = cur.fetchall()
                if rows:
                    self.cuentas = [(r[0], r[1], r[2], r[3], f"RD$ {r[4]:,.2f}") for r in rows]
                else:
                    self.cuentas = []
        except Exception:
            self.cuentas = []

        for c in self.cuentas:
            self.tabla.insert("", tk.END, values=c)

    def registrar_cuenta(self):
        nom = self.ent_nombre.get().strip()
        num = self.ent_cuenta.get().strip()
        sal = self.ent_saldo.get().strip() or "0"
        tip = self.cmb_tipo.get()

        if not nom or not num:
            messagebox.showwarning("Atención", "Ingrese el nombre del banco y el número de cuenta.")
            return

        try:
            sal_f = float(sal.replace("$", "").replace(",", ""))
            if sal_f < 0:
                raise ValueError
            self.servicio_caja.crear_cuenta_banco((nom, num, tip, sal_f))
            self.cargar_cuentas()
            messagebox.showinfo("Éxito", f"Cuenta bancaria '{nom}' registrada exitosamente.")
            self.ent_nombre.delete(0, tk.END)
            self.ent_cuenta.delete(0, tk.END)
            self.ent_saldo.delete(0, tk.END)
        except ValueError:
            messagebox.showerror("Error", "Ingrese un saldo numérico válido.")

    def editar_cuenta(self):
        sel = self.tabla.selection()
        if not sel:
            messagebox.showwarning("Atención", "Seleccione una cuenta bancaria de la tabla para editar.")
            return
        vals = self.tabla.item(sel[0], "values")
        try:
            saldo = float((self.ent_saldo.get().strip() or vals[4]).replace("RD$", "").replace("$", "").replace(",", ""))
            self.servicio_caja.actualizar_cuenta_banco(vals[0], (self.ent_nombre.get().strip() or vals[1], self.ent_cuenta.get().strip() or vals[2], self.cmb_tipo.get() or vals[3], saldo))
            self.cargar_cuentas()
            messagebox.showinfo("Editar", "Cuenta bancaria actualizada correctamente.")
        except (ValueError, sqlite3.Error) as error:
            messagebox.showerror("Error", f"No se pudo actualizar la cuenta: {error}")

    def ver_movimientos(self):
        sel = self.tabla.selection()
        if sel:
            vals = self.tabla.item(sel[0], "values")
            MovimientosBancarios(self, banco_nom=vals[1], cuenta_num=vals[2])
        else:
            messagebox.showwarning("Atención", "Seleccione una cuenta bancaria para ver sus movimientos.")
