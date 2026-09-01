import os
import sys
import tkinter as tk
from tkinter import messagebox, ttk
from PIL import Image, ImageTk
from window_utils import posicionar_ventana
from servicios.servicio_caja import ServicioCaja

class RegistrarAbonoModal(tk.Toplevel):
    def __init__(self, parent, factura_id=None, cliente="", saldo_pend="$ 0.00", callback_success=None):
        super().__init__(parent)
        self.parent = parent
        self.factura_id = factura_id
        self.cliente = cliente
        self.saldo_pend = saldo_pend
        self.callback_success = callback_success
        self.title("Registrar Abono")
        posicionar_ventana(self, 540, 500, parent)
        self.resizable(False, False)
        self.configure(bg="#C6D9E3")
        self.transient(parent)
        self.grab_set()
        try:
            self.iconbitmap(self.rutas('icono.ico'))
        except Exception:
            pass

        self.images = {}
        self.servicio_caja = ServicioCaja()
        self.widgets()

    def rutas(self, ruta):
        try:
            rutabase = sys.__MEIPASS
        except Exception:
            rutabase = os.path.abspath(".")
        return os.path.join(rutabase, ruta)

    def widgets(self):
        frame_box = tk.LabelFrame(
            self,
            text="Registrar Abono",
            font=("sans", 14, "bold"),
            bg="#C6D9E3",
            fg="#1E293B",
            padx=15,
            pady=10
        )
        frame_box.place(x=15, y=10, width=510, height=420)

        # Factura Header
        lbl_fac = tk.Label(frame_box, text=f"Factura: {self.factura_id}", font=("sans", 16, "bold"), bg="#C6D9E3", fg="#16A34A")
        lbl_fac.place(x=15, y=5)

        lbl_cli = tk.Label(frame_box, text=f"Cliente: {self.cliente}", font=("sans", 11, "bold"), bg="#C6D9E3", fg="#1E293B")
        lbl_cli.place(x=15, y=40)

        lbl_sal = tk.Label(frame_box, text=f"Saldo Pendiente: {self.saldo_pend}", font=("sans", 11, "bold"), bg="#C6D9E3", fg="#1E293B")
        lbl_sal.place(x=15, y=68)

        lbl_m = tk.Label(frame_box, text="Monto del Abono:", font=("sans", 11, "bold"), bg="#C6D9E3", fg="#1E293B")
        lbl_m.place(x=15, y=105)

        self.ent_monto = ttk.Entry(frame_box, font=("sans", 12), justify="center")
        self.ent_monto.place(x=15, y=130, width=450, height=34)
        self.ent_monto.focus_set()

        # Group Método de Pago
        frame_met = tk.LabelFrame(
            frame_box,
            text="Método de Pago",
            font=("sans", 11, "bold"),
            bg="#C6D9E3",
            fg="#1E293B",
            padx=10,
            pady=6
        )
        frame_met.place(x=15, y=175, width=450, height=85)

        self.metodo_pago = tk.StringVar(value="Efectivo")
        metodos = ["Efectivo", "Tarjeta de Débito", "Tarjeta de Crédito", "Transferencia"]

        x_pos = [15, 140, 280, 15]
        y_pos = [5, 5, 5, 32]
        for idx, m in enumerate(metodos):
            rb = ttk.Radiobutton(frame_met, text=m, value=m, variable=self.metodo_pago)
            rb.place(x=x_pos[idx], y=y_pos[idx])

        # Group Cuenta Bancaria
        frame_cta = tk.LabelFrame(
            frame_box,
            text="Cuenta Bancaria (solo pagos electrónicos)",
            font=("sans", 11, "bold"),
            bg="#C6D9E3",
            fg="#1E293B",
            padx=10,
            pady=6
        )
        frame_cta.place(x=15, y=270, width=450, height=75)

        lbl_c = tk.Label(frame_cta, text="Cuenta:", font=("sans", 10, "bold"), bg="#C6D9E3", fg="#1E293B")
        lbl_c.place(x=10, y=10)

        self.cmb_cta = ttk.Combobox(frame_cta, values=[], font=("sans", 10), state="readonly")
        try:
            cuentas = self.servicio_caja.listar_cuentas_pago()
            opciones = [f"{b} - {n} ({t})" for b, n, t in cuentas]
            self.cmb_cta["values"] = opciones
            if opciones:
                self.cmb_cta.current(0)
        except Exception:
            pass
        self.cmb_cta.place(x=80, y=8, width=340, height=28)

        # Botones Inferiores
        ruta_save = self.rutas("icono/guardar.png")
        if os.path.exists(ruta_save):
            self.images["save_ram"] = ImageTk.PhotoImage(Image.open(ruta_save).resize((20, 20), Image.Resampling.LANCZOS))
            ico_s = self.images["save_ram"]
        else:
            ico_s = None

        btn_save = tk.Button(
            self,
            text="  Registrar",
            image=ico_s,
            compound=tk.LEFT,
            font=("sans", 11, "bold"),
            bg="#EBEFF2",
            fg="#1E293B",
            relief="raised",
            bd=2,
            cursor="hand2",
            command=self.registrar
        )
        btn_save.place(x=130, y=442, width=130, height=42)

        ruta_close = self.rutas("icono/cancelar.png")
        if os.path.exists(ruta_close):
            self.images["close_ram"] = ImageTk.PhotoImage(Image.open(ruta_close).resize((20, 20), Image.Resampling.LANCZOS))
            ico_c = self.images["close_ram"]
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
        btn_close.place(x=280, y=442, width=130, height=42)

    def registrar(self):
        m = self.ent_monto.get().strip()
        if not m:
            messagebox.showwarning("Atención", "Ingrese el monto del abono.")
            return

        try:
            m_val = float(m.replace("$", "").replace(",", ""))
            if m_val <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Error", "Ingrese un monto numérico válido.")
            return

        try:
            saldo_val = float(str(self.saldo_pend).replace("$", "").replace(",", "").strip())
            if m_val > saldo_val + 0.01:
                messagebox.showerror("Error", f"El abono no puede ser mayor al saldo pendiente ({self.saldo_pend}).")
                return
        except ValueError:
            pass

        if self.callback_success:
            medio = self.metodo_pago.get().strip() or "Efectivo"
            cuenta = self.cmb_cta.get().strip()
            if medio != "Efectivo" and not cuenta:
                messagebox.showerror("Cuenta requerida", "Seleccione la cuenta bancaria del abono.")
                return
            self.callback_success(m_val, medio, cuenta)
        self.destroy()
