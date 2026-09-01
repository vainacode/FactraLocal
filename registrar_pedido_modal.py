import os
import sys
import tkinter as tk
from tkinter import messagebox, ttk
import datetime
import db_conexion
from PIL import Image, ImageTk
from window_utils import posicionar_ventana
from servicios.servicio_compras import ServicioCompras

class RegistrarPedidoModal(tk.Toplevel):
    def __init__(self, parent, pedido_info=None, callback_success=None):
        super().__init__(parent)
        self.parent = parent
        self.callback_success = callback_success
        self.servicio_compras = ServicioCompras()
        self.title("Registrar Pedido")
        posicionar_ventana(self, 880, 560, parent)
        self.resizable(False, False)
        self.configure(bg="#C6D9E3")
        self.transient(parent)
        self.grab_set()
        try:
            self.iconbitmap(self.rutas('icono.ico'))
        except Exception:
            pass

        self.images = {}
        self.pedido_info = pedido_info or []
        self.total_pedido = 0.0

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
            text="REGISTRAR PEDIDO",
            font=("sans", 20, "bold"),
            bg="#C6D9E3",
            fg="#1E293B"
        )
        lbl_title.place(relx=0.5, y=25, anchor="center")

#============== 2. RESUMEN DEL PEDIDO (TOP-LEFT) ===================================================#
        frame_res = tk.LabelFrame(
            self,
            text="Resumen del Pedido",
            font=("sans", 12, "bold"),
            bg="#C6D9E3",
            fg="#1E293B",
            padx=10,
            pady=8
        )
        frame_res.place(x=15, y=50, width=515, height=215)

        style = ttk.Style()
        style.configure("RPM.Treeview.Heading", font=("sans", 8, "bold"), background="#E0E6ED")
        style.configure("RPM.Treeview", font=("sans", 9), rowheight=22)

        cols = ("producto", "cant", "costo_u", "subtotal")
        self.tabla = ttk.Treeview(frame_res, columns=cols, show="headings", style="RPM.Treeview")
        self.tabla.place(x=5, y=5, width=485, height=125)

        self.tabla.heading("producto", text="Producto")
        self.tabla.heading("cant", text="Cant.")
        self.tabla.heading("costo_u", text="Costo c/u")
        self.tabla.heading("subtotal", text="Subtotal")

        self.tabla.column("producto", width=250, anchor="w")
        self.tabla.column("cant", width=50, anchor="center")
        self.tabla.column("costo_u", width=90, anchor="e")
        self.tabla.column("subtotal", width=95, anchor="e")

        for _, proveedor, producto, cantidad in self.pedido_info:
            try:
                cantidad_num = int(cantidad or 1)
            except (TypeError, ValueError):
                cantidad_num = 1
            costo = 0.0
            for item in getattr(self.parent, "productos_db", []):
                if item[1] == producto:
                    costo = float(item[3] or 0)
                    break
            subtotal = costo * cantidad_num
            self.total_pedido += subtotal
            self.tabla.insert("", tk.END, values=(producto, cantidad_num, f"$ {costo:,.2f}", f"$ {subtotal:,.2f}"))

        lbl_tot_tag = tk.Label(frame_res, text="TOTAL DEL PEDIDO:", font=("sans", 11, "bold"), bg="#C6D9E3", fg="#1E293B")
        lbl_tot_tag.place(x=15, y=145)

        self.lbl_tot_val = tk.Label(frame_res, text=f"$ {self.total_pedido:,.2f}", font=("sans", 12, "bold"), bg="white", fg="#1E293B", relief="solid", bd=1, padx=10, pady=2)
        self.lbl_tot_val.place(x=340, y=142, width=150)

#============== 3. OPCIONES DE PAGO (BOTTOM-LEFT) ===================================================#
        frame_pago = tk.LabelFrame(
            self,
            text="Opciones de Pago",
            font=("sans", 12, "bold"),
            bg="#C6D9E3",
            fg="#1E293B",
            padx=12,
            pady=8
        )
        frame_pago.place(x=15, y=275, width=515, height=195)

        lbl_mp = tk.Label(frame_pago, text="Monto del Pago:", font=("sans", 11, "bold"), bg="#C6D9E3", fg="#1E293B")
        lbl_mp.place(x=15, y=10)

        self.ent_monto_pago = ttk.Entry(frame_pago, font=("sans", 12), justify="center")
        self.ent_monto_pago.place(x=15, y=40, width=220, height=34)

        self.chk_tot_var = tk.BooleanVar(value=False)
        self.chk_tot = ttk.Checkbutton(frame_pago, text="Pagar el total del pedido", variable=self.chk_tot_var, command=self.al_marcar_total)
        self.chk_tot.place(x=260, y=45)

        lbl_note1 = tk.Label(frame_pago, text="• Deje vacío el monto para registrar sin pago inicial", font=("sans", 9, "italic"), bg="#C6D9E3", fg="#0284C7")
        lbl_note1.place(x=15, y=95)

        lbl_note2 = tk.Label(frame_pago, text="• El pedido quedará como 'Pendiente' hasta completar el pago", font=("sans", 9, "italic"), bg="#C6D9E3", fg="#0284C7")
        lbl_note2.place(x=15, y=125)

#============== 4. INFORMACIÓN DE NUEVOS COSTOS (RIGHT CARD) ========================================#
        frame_costos = tk.LabelFrame(
            self,
            text="Información de Nuevos Costos",
            font=("sans", 12, "bold"),
            bg="#C6D9E3",
            fg="#1E293B",
            padx=12,
            pady=10
        )
        frame_costos.place(x=545, y=50, width=320, height=420)

        card_interior = tk.Frame(frame_costos, bg="white", highlightbackground="#B8C4CE", highlightthickness=1)
        card_interior.pack(fill="both", expand=True, padx=4, pady=4)

        lbl_p_tag = tk.Label(
            card_interior,
            text="📦 Detalle del pedido actual",
            font=("sans", 9, "bold"),
            bg="white",
            fg="#0284C7",
            wraplength=270,
            justify="left"
        )
        lbl_p_tag.pack(anchor="w", padx=10, pady=8)

        detalles_costo = [
            f"• Productos en el pedido: {len(self.pedido_info)}",
            f"• Total calculado: $ {self.total_pedido:,.2f}",
            "• El stock se actualiza al recibir la mercancía.",
        ]

        for dt in detalles_costo:
            color = "#EA580C" if "nuevo" in dt else "#475569"
            lbl_d = tk.Label(card_interior, text=dt, font=("sans", 9), bg="white", fg=color)
            lbl_d.pack(anchor="w", padx=15, pady=2)

        tk.Frame(card_interior, bg="#CBD5E1", height=1).pack(fill="x", padx=10, pady=10)

        total_unidades = sum(int(item[3] or 0) for item in self.pedido_info if str(item[3] or "").isdigit())
        lbl_tot_u = tk.Label(card_interior, text=f"✔ Total unidades: {total_unidades}", font=("sans", 10, "bold"), bg="white", fg="#16A34A")
        lbl_tot_u.pack(anchor="w", padx=15, pady=4)

        lbl_nvo_c = tk.Label(card_interior, text=f"✔ Costo pedido: $ {self.total_pedido:,.2f}", font=("sans", 10, "bold"), bg="white", fg="#16A34A")
        lbl_nvo_c.pack(anchor="w", padx=15, pady=4)

#============== 5. BOTONES INFERIORES ===============================================================#
        ruta_reg = self.rutas("icono/btnpedidos.png")
        if not os.path.exists(ruta_reg):
            ruta_reg = self.rutas("icono/guardar.png")

        if os.path.exists(ruta_reg):
            self.images["reg_ped_ico"] = ImageTk.PhotoImage(Image.open(ruta_reg).resize((22, 22), Image.Resampling.LANCZOS))
            ico_r = self.images["reg_ped_ico"]
        else:
            ico_r = None

        btn_reg = tk.Button(
            self,
            text="  Registrar Pedido",
            image=ico_r,
            compound=tk.LEFT,
            font=("sans", 11, "bold"),
            bg="#22C55E",
            fg="white",
            relief="raised",
            bd=2,
            cursor="hand2",
            command=self.confirmar_registro
        )
        btn_reg.place(x=240, y=490, width=200, height=44)

        ruta_close = self.rutas("icono/cancelar.png")
        if os.path.exists(ruta_close):
            self.images["close_rpm"] = ImageTk.PhotoImage(Image.open(ruta_close).resize((22, 22), Image.Resampling.LANCZOS))
            ico_c = self.images["close_rpm"]
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
        btn_close.place(x=460, y=490, width=150, height=44)

    def al_marcar_total(self):
        if self.chk_tot_var.get():
            self.ent_monto_pago.delete(0, tk.END)
            self.ent_monto_pago.insert(0, f"{self.total_pedido:.2f}")
        else:
            self.ent_monto_pago.delete(0, tk.END)

    def confirmar_registro(self):
        if not self.pedido_info:
            messagebox.showwarning("Pedido vacío", "No hay productos para registrar.")
            return
        try:
            detalles = []
            for _, proveedor, producto, cantidad in self.pedido_info:
                try:
                    cantidad_num = int(cantidad or 1)
                except (TypeError, ValueError):
                    raise ValueError(f"Cantidad inválida para {producto}.")
                if cantidad_num <= 0:
                    raise ValueError(f"La cantidad de {producto} debe ser mayor que cero.")
                precio = costo = 0.0
                for item in getattr(self.parent, "productos_db", []):
                    if item[1] == producto:
                        precio, costo = float(item[2] or 0), float(item[3] or 0)
                        break
                detalles.append({"proveedor": proveedor, "producto": producto, "cantidad": cantidad_num, "precio": precio, "costo": costo})
            numero = self.servicio_compras.registrar_pedido(detalles[0]["proveedor"], detalles, getattr(self.parent, "usuario", None), self.pedido_info[0][0])
            messagebox.showinfo("Éxito", "Pedido a proveedor registrado correctamente.")
            if self.callback_success:
                self.callback_success()
            self.destroy()
        except Exception as error:
            messagebox.showerror("Error", f"No se pudo registrar el pedido: {error}")
