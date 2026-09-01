import os
import sys
import tkinter as tk
from tkinter import messagebox, ttk, simpledialog
from PIL import Image, ImageTk
from window_utils import posicionar_ventana
from servicios.servicio_caja import ServicioCaja

class RealizarPagoModal(tk.Toplevel):
    def __init__(self, parent, total_pagar=0.0, callback_confirm=None):
        super().__init__(parent)
        self.parent = parent
        self.total_pagar = total_pagar
        self.callback_confirm = callback_confirm
        self.title("Realizar pago")
        posicionar_ventana(self, 780, 560, parent)
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
        self.medio_seleccionado = tk.StringVar(value="Efectivo")
        self.descuento_aplicado = 0.00

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
            text="Realizar pago",
            font=("sans", 24, "bold"),
            bg="#C6D9E3",
            fg="#1E293B"
        )
        lbl_title.place(relx=0.5, y=25, anchor="center")

#============== 2. PANEL IZQUIERDO: DETALLES DE LA VENTA ===========================================#
        frame_detalles = tk.LabelFrame(
            self,
            text="Detalles de la venta",
            font=("sans", 12, "bold"),
            bg="#C6D9E3",
            fg="#1E293B",
            padx=12,
            pady=10
        )
        frame_detalles.place(x=20, y=55, width=360, height=270)

        self.lbl_tot_tag = tk.Label(
            frame_detalles,
            text=f"Total a pagar: $ {self.total_pagar:,.2f}",
            font=("sans", 14, "bold"),
            bg="#C6D9E3",
            fg="#16A34A"
        )
        self.lbl_tot_tag.place(relx=0.5, y=20, anchor="center")

        self.lbl_desc = tk.Label(
            frame_detalles,
            text=f"Descuento aplicado: $ {self.descuento_aplicado:,.2f}",
            font=("sans", 11, "bold"),
            bg="#C6D9E3",
            fg="#1E293B"
        )
        self.lbl_desc.place(relx=0.5, y=55, anchor="center")

        # Botón Aplicar Descuento
        ruta_desc = self.rutas("icono/descuento.png")
        if os.path.exists(ruta_desc):
            img_d = Image.open(ruta_desc).resize((22, 22), Image.Resampling.LANCZOS)
            self.images["desc_ico_p"] = ImageTk.PhotoImage(img_d)
            ico_d = self.images["desc_ico_p"]
        else:
            ico_d = None

        btn_desc = tk.Button(
            frame_detalles,
            text="  Aplicar Descuento",
            image=ico_d,
            compound=tk.LEFT,
            font=("sans", 10, "bold"),
            bg="#EBEFF2",
            fg="#1E293B",
            relief="raised",
            bd=2,
            cursor="hand2",
            command=self.abrir_descuento
        )
        btn_desc.place(relx=0.5, y=95, width=200, height=36, anchor="center")

        # Monto pagado
        lbl_mp = tk.Label(frame_detalles, text="Ingrese el monto pagado:", font=("sans", 12, "bold"), bg="#C6D9E3", fg="#1E293B")
        lbl_mp.place(relx=0.5, y=145, anchor="center")

        self.ent_monto_pagado = ttk.Entry(frame_detalles, font=("sans", 16, "bold"), justify="center")
        self.ent_monto_pagado.place(relx=0.5, y=185, width=240, height=40, anchor="center")
        self.ent_monto_pagado.insert(0, f"{self.total_pagar:.2f}")

#============== 3. PANEL DERECHO: MEDIOS DE PAGO CONTADO ===========================================#
        frame_contado = tk.LabelFrame(
            self,
            text="Medios de pago Contado",
            font=("sans", 12, "bold"),
            bg="#C6D9E3",
            fg="#1E293B",
            padx=10,
            pady=8
        )
        frame_contado.place(x=400, y=55, width=360, height=170)

        # Fila 1: Efectivo / Tarjeta Débito
        self.agregar_opcion_pago(frame_contado, "Efectivo", "mediospago.png", 10, 8)
        self.agregar_opcion_pago(frame_contado, "Tarjeta de Débito", "btncobros.png", 185, 8)

        # Fila 2: Tarjeta Crédito / Transferencia
        self.agregar_opcion_pago(frame_contado, "Tarjeta de Crédito", "pago3.png", 10, 56)
        self.agregar_opcion_pago(frame_contado, "Transferencia", "btnbanco.png", 185, 56)

        # Fila 3: Pago Mixto
        self.agregar_opcion_pago(frame_contado, "Pago Mixto", "abonospagados.png", 10, 104)

#============== 4. MEDIOS DE PAGO CRÉDITO ==========================================================#
        frame_credito = tk.LabelFrame(
            self,
            text="Medios de pago Crédito",
            font=("sans", 12, "bold"),
            bg="#C6D9E3",
            fg="#1E293B",
            padx=10,
            pady=8
        )
        frame_credito.place(x=400, y=235, width=360, height=90)

        self.agregar_opcion_pago(frame_credito, "Venta a Crédito", "abonospagados.png", 10, 12)

#============== 5. SELECCIONAR CUENTA BANCARIA =====================================================#
        frame_cuenta = tk.LabelFrame(
            self,
            text="Seleccionar Cuenta Bancaria",
            font=("sans", 12, "bold"),
            bg="#C6D9E3",
            fg="#1E293B",
            padx=10,
            pady=6
        )
        frame_cuenta.place(x=20, y=340, width=740, height=85)

        lbl_cta = tk.Label(frame_cuenta, text="Cuenta:", font=("sans", 12, "bold"), bg="#C6D9E3", fg="#1E293B")
        lbl_cta.place(x=15, y=12)

        self.cmb_cuenta = ttk.Combobox(frame_cuenta, values=[], font=("sans", 11), state="readonly")
        try:
            cuentas = self.servicio_caja.listar_cuentas_pago()
            opciones = [f"{b} - {n} ({t})" for b, n, t in cuentas]
            self.cmb_cuenta["values"] = opciones
            if opciones:
                self.cmb_cuenta.current(0)
        except Exception:
            pass
        self.cmb_cuenta.place(x=110, y=10, width=600, height=32)

#============== 6. BOTÓN CONFIRMAR PAGO ============================================================#
        ruta_conf = self.rutas("icono/pago.png")
        if not os.path.exists(ruta_conf):
            ruta_conf = self.rutas("icono/btncobros.png")

        if os.path.exists(ruta_conf):
            img_c = Image.open(ruta_conf).resize((28, 28), Image.Resampling.LANCZOS)
            self.images["conf_pago_ico"] = ImageTk.PhotoImage(img_c)
            ico_conf = self.images["conf_pago_ico"]
        else:
            ico_conf = None

        btn_confirm = tk.Button(
            self,
            text="  Confirmar Pago",
            image=ico_conf,
            compound=tk.LEFT,
            font=("sans", 14, "bold"),
            bg="#EBEFF2",
            fg="#1E293B",
            relief="raised",
            bd=3,
            cursor="hand2",
            command=self.confirmar_pago
        )
        btn_confirm.place(relx=0.5, y=475, width=230, height=52, anchor="center")

    def agregar_opcion_pago(self, parent, valor, ico_file, x_pos, y_pos):
        rb = ttk.Radiobutton(parent, text="", value=valor, variable=self.medio_seleccionado)
        rb.place(x=x_pos, y=y_pos + 4)

        ruta_i = self.rutas(f"icono/{ico_file}")
        if os.path.exists(ruta_i):
            img_i = Image.open(ruta_i).resize((22, 22), Image.Resampling.LANCZOS)
            self.images[f"rb_{valor}"] = ImageTk.PhotoImage(img_i)
            lbl_ico = tk.Label(parent, image=self.images[f"rb_{valor}"], bg="#C6D9E3")
            lbl_ico.place(x=x_pos + 22, y=y_pos + 2)

        lbl_txt = tk.Label(parent, text=valor, font=("sans", 9, "bold"), bg="#C6D9E3", fg="#1E293B")
        lbl_txt.place(x=x_pos + 50, y=y_pos + 4)

    def abrir_descuento(self):
        tipo = simpledialog.askstring("Descuento", "Escriba P para porcentaje o M para monto fijo:", parent=self)
        if not tipo:
            return
        valor = simpledialog.askfloat("Descuento", "Indique el valor del descuento:", parent=self, minvalue=0)
        if valor is None:
            return
        if tipo.strip().upper() == "P":
            if valor > 100:
                messagebox.showwarning("Descuento inválido", "El porcentaje no puede superar 100%.")
                return
            descuento = self.total_pagar * valor / 100
        elif tipo.strip().upper() == "M":
            descuento = valor
        else:
            messagebox.showwarning("Descuento inválido", "Seleccione P o M.")
            return
        if descuento >= self.total_pagar:
            messagebox.showwarning("Descuento inválido", "El descuento debe ser menor que el total.")
            return
        self.descuento_aplicado = round(descuento, 2)
        self.total_pagar = round(self.total_pagar - descuento, 2)
        self.lbl_tot_tag.config(text=f"Total a pagar: $ {self.total_pagar:,.2f}")
        self.lbl_desc.config(text=f"Descuento aplicado: $ {self.descuento_aplicado:,.2f}")
        self.ent_monto_pagado.delete(0, tk.END)
        self.ent_monto_pagado.insert(0, f"{self.total_pagar:.2f}")

    def confirmar_pago(self):
        try:
            medio = self.medio_seleccionado.get()
            if medio == "Venta a Crédito":
                monto_rec = 0.0
            else:
                monto_rec = float(self.ent_monto_pagado.get().strip() or 0)
                if monto_rec < self.total_pagar:
                    messagebox.showerror("Pago Insuficiente", "El monto ingresado es menor al total a pagar.")
                    return

            cambio = max(0, monto_rec - self.total_pagar)

            def al_completar_cambio():
                if self.callback_confirm:
                    # El total puede haber cambiado por un descuento. Se
                    # entrega al flujo de venta para que el importe guardado
                    # y el comprobante fiscal coincidan con lo cobrado.
                    self.callback_confirm(medio, monto_rec, cambio, self.total_pagar, self.cmb_cuenta.get())
                self.destroy()
                from generar_factura_modal import GenerarFacturaModal
                GenerarFacturaModal(self.parent)

            if medio == "Venta a Crédito":
                al_completar_cambio()
                return

            from cambio_modal import CambioModal
            CambioModal(
                self,
                total_pagar=self.total_pagar,
                dinero_recibido=monto_rec,
                cambio=cambio,
                medio_pago=medio,
                callback_continuar=al_completar_cambio
            )
        except ValueError:
            messagebox.showerror("Error", "Ingrese un monto numérico válido.")
