import datetime
import os
import db_conexion as sqlite3
import sys
import tkinter as tk
from tkinter import messagebox, ttk
from PIL import Image, ImageTk
from registrar_abono_modal import RegistrarAbonoModal
from window_utils import posicionar_ventana
from servicios.servicio_cuentas_cobrar import ServicioCuentasCobrar

PLAZO_DIAS_DEFECTO = 30

class CuentasPorCobrar(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.title("Punto de Venta Versión 4.4.7 - Cuentas por Cobrar")
        posicionar_ventana(self, 1100, 650, parent)
        self.resizable(False, False)
        self.configure(bg="#DDE1E5")
        self.transient(parent)
        self.grab_set()
        try:
            self.iconbitmap(self.rutas('icono.ico'))
        except Exception:
            pass

        self.db_name = "database.db"
        self.servicio_cxc = ServicioCuentasCobrar()
        self.images = {}
        self.creditos = []
        self.plazo_dias = PLAZO_DIAS_DEFECTO
        self.pagina_actual = 1
        self.por_pagina = 15

        self.widgets()
        self.cargar_creditos()

    def rutas(self, ruta):
        try:
            rutabase = sys.__MEIPASS
        except Exception:
            rutabase = os.path.abspath(".")
        return os.path.join(rutabase, ruta)

    def widgets(self):
#============== 1. HEADER ==========================================================================#
        lbl_titulo = tk.Label(
            self,
            text="CUENTAS POR COBRAR",
            font=("sans", 28, "bold"),
            bg="#DDE1E5",
            fg="#1E293B"
        )
        lbl_titulo.place(relx=0.5, y=35, anchor="center")

#============== 2. BARRA SUPERIOR DE BÚSQUEDA Y ACCIONES ===========================================#
        lbl_b = tk.Label(self, text="Buscar:", font=("sans", 13, "bold"), bg="#DDE1E5", fg="#1E293B")
        lbl_b.place(x=25, y=70)

        self.ent_buscar = ttk.Entry(self, font=("sans", 11))
        self.ent_buscar.place(x=105, y=68, width=220, height=30)
        self.ent_buscar.bind("<KeyRelease>", lambda e: self.filtrar_creditos())

        ruta_b = self.rutas("icono/buscar.png")
        if os.path.exists(ruta_b):
            self.images["b_cpc_ico"] = ImageTk.PhotoImage(Image.open(ruta_b).resize((22, 22), Image.Resampling.LANCZOS))
            btn_b = tk.Button(self, image=self.images["b_cpc_ico"], bg="white", relief="solid", bd=1, cursor="hand2", command=self.filtrar_creditos)
            btn_b.place(x=330, y=68, width=32, height=30)

        # 3 Botones a la derecha: Refrescar, Configurar Plazo, Ver Alertas
        ruta_ref = self.rutas("icono/actualizar1.png")
        if not os.path.exists(ruta_ref):
            ruta_ref = self.rutas("icono/actualizar.png")

        if os.path.exists(ruta_ref):
            self.images["ref_cpc_ico"] = ImageTk.PhotoImage(Image.open(ruta_ref).resize((22, 22), Image.Resampling.LANCZOS))
            btn_ref = tk.Button(self, image=self.images["ref_cpc_ico"], bg="#EBEFF2", relief="raised", bd=2, cursor="hand2", command=self.cargar_creditos)
            btn_ref.place(x=730, y=65, width=42, height=36)

        ruta_plazo = self.rutas("icono/reloj.png")
        if not os.path.exists(ruta_plazo):
            ruta_plazo = self.rutas("icono/calendario.png")

        if os.path.exists(ruta_plazo):
            self.images["plazo_cpc_ico"] = ImageTk.PhotoImage(Image.open(ruta_plazo).resize((20, 20), Image.Resampling.LANCZOS))
            ico_plz = self.images["plazo_cpc_ico"]
        else:
            ico_plz = None

        btn_plazo = tk.Button(self, text="  Configurar Plazo", image=ico_plz, compound=tk.LEFT, font=("sans", 10, "bold"), bg="#EBEFF2", fg="#1E293B", relief="raised", bd=2, cursor="hand2", command=self.configurar_plazo)
        btn_plazo.place(x=780, y=65, width=170, height=36)

        btn_alert = tk.Button(self, text="  ⚠️ Ver Alertas", font=("sans", 10, "bold"), bg="#EBEFF2", fg="#1E293B", relief="raised", bd=2, cursor="hand2", command=self.ver_alertas)
        btn_alert.place(x=960, y=65, width=120, height=36)

#============== 3. TABLA DE CUENTAS POR COBRAR =====================================================#
        style = ttk.Style()
        style.configure("CPC.Treeview.Heading", font=("sans", 9, "bold"), background="#E0E6ED")
        style.configure("CPC.Treeview", font=("sans", 9), rowheight=24)

        cols = ("factura", "cliente", "total_cred", "saldo_pend", "fecha_venta", "plazo", "dias_rest", "estado")
        self.tabla = ttk.Treeview(self, columns=cols, show="headings", style="CPC.Treeview")
        self.tabla.place(x=20, y=110, width=1060, height=450)

        titulos = [
            ("factura", "Factura", 70),
            ("cliente", "Cliente", 230),
            ("total_cred", "Total Crédito", 130),
            ("saldo_pend", "Saldo Pendiente", 130),
            ("fecha_venta", "Fecha de Venta", 120),
            ("plazo", "Plazo (días)", 110),
            ("dias_rest", "Días Restantes", 120),
            ("estado", "Estado", 110),
        ]

        for c, t, w in titulos:
            self.tabla.heading(c, text=t, anchor="center")
            self.tabla.column(c, width=w, anchor="center" if c in ("factura", "fecha_venta", "plazo", "dias_rest", "estado") else "e" if "Total" in t or "Saldo" in t else "w")

        scroll_y = ttk.Scrollbar(self, orient="vertical", command=self.tabla.yview)
        self.tabla.configure(yscrollcommand=scroll_y.set)
        scroll_y.place(x=1082, y=110, height=450)

#============== 4. BARRA INFERIOR ==================================================================#
        # 4 Botones de acción a la izquierda
        acciones_cpc = [
            ("Registrar", "mediospago.png", self.abrir_registrar_abono),
            ("Historial", "factura.png", self.ver_historial),
            ("Ver Abonos", "ojo.png", self.ver_abonos),
            ("Anulados", "cancelar.png", self.ver_anulados),
        ]

        x_ac = 20
        for txt, ico_f, cmd in acciones_cpc:
            ruta_i = self.rutas(f"icono/{ico_f}")
            if not os.path.exists(ruta_i):
                ruta_i = self.rutas("icono/guardar.png")

            if os.path.exists(ruta_i):
                img_i = Image.open(ruta_i).resize((22, 22), Image.Resampling.LANCZOS)
                self.images[f"ac_cpc_{ico_f}"] = ImageTk.PhotoImage(img_i)
                ico_btn = self.images[f"ac_cpc_{ico_f}"]
            else:
                ico_btn = None

            btn = tk.Button(
                self,
                text=f"  {txt}",
                image=ico_btn,
                compound=tk.LEFT,
                font=("sans", 10, "bold"),
                bg="#EBEFF2",
                fg="#1E293B",
                relief="raised",
                bd=2,
                cursor="hand2",
                command=cmd
            )
            btn.place(x=x_ac, y=575, width=130, height=42)
            x_ac += 138

        # Paginador a la derecha
        ruta_ant = self.rutas("icono/izquierda.png")
        if os.path.exists(ruta_ant):
            self.images["ant_cpc"] = ImageTk.PhotoImage(Image.open(ruta_ant).resize((18, 18), Image.Resampling.LANCZOS))
            ico_a = self.images["ant_cpc"]
        else:
            ico_a = None

        btn_ant = tk.Button(self, text="  Anterior", image=ico_a, compound=tk.LEFT, font=("sans", 10, "bold"), bg="#EBEFF2", fg="#1E293B", relief="raised", bd=2, cursor="hand2", command=self.pag_ant)
        btn_ant.place(x=660, y=575, width=110, height=42)

        self.lbl_pag = tk.Label(self, text="Página 1 de 1", font=("sans", 10, "bold"), bg="#DDE1E5", fg="#1E293B")
        self.lbl_pag.place(x=785, y=585)

        ruta_sig = self.rutas("icono/derecha.png")
        if os.path.exists(ruta_sig):
            self.images["sig_cpc"] = ImageTk.PhotoImage(Image.open(ruta_sig).resize((18, 18), Image.Resampling.LANCZOS))
            ico_s = self.images["sig_cpc"]
        else:
            ico_s = None

        btn_sig = tk.Button(self, text="  Siguiente", image=ico_s, compound=tk.RIGHT, font=("sans", 10, "bold"), bg="#EBEFF2", fg="#1E293B", relief="raised", bd=2, cursor="hand2", command=self.pag_sig)
        btn_sig.place(x=930, y=575, width=110, height=42)

    def cargar_creditos(self):
        self.creditos = []
        try:
            for factura, cliente, total, saldo, fecha_venta in self.servicio_cxc.listar_saldos(self.plazo_dias):
                try:
                    f_venta = datetime.datetime.strptime(str(fecha_venta), "%Y-%m-%d")
                    dias_rest = self.plazo_dias - (datetime.datetime.now() - f_venta).days
                except Exception:
                    dias_rest = self.plazo_dias
                estado = "Vencido" if dias_rest < 0 else ("Por Vencer" if dias_rest <= 5 else "Pendiente")
                self.creditos.append((factura, cliente, f"$ {total:,.2f}", f"$ {saldo:,.2f}", str(fecha_venta), str(self.plazo_dias), f"{dias_rest} días" if dias_rest >= 0 else "Vencido", estado))
        except Exception as e:
            print("Error cargando cuentas por cobrar:", e)

        self.pagina_actual = 1
        self.renderizar_tabla(self.creditos)

    def renderizar_tabla(self, datos):
        for r in self.tabla.get_children():
            self.tabla.delete(r)

        self.tabla.tag_configure("cred_vencido", background="#FEE2E2")
        self.tabla.tag_configure("cred_por_vencer", background="#FEF3C7")
        self.tabla.tag_configure("cred_activo", background="#DCFCE7")

        inicio = (self.pagina_actual - 1) * self.por_pagina
        fin = inicio + self.por_pagina
        total_pags = max(1, (len(datos) + self.por_pagina - 1) // self.por_pagina)
        self.lbl_pag.config(text=f"Página {self.pagina_actual} de {total_pags}")

        for c in datos[inicio:fin]:
            tag = "cred_vencido" if c[7] == "Vencido" else "cred_por_vencer" if c[7] == "Por Vencer" else "cred_activo"
            self.tabla.insert("", tk.END, values=c, tags=(tag,))

    def pag_ant(self):
        if self.pagina_actual > 1:
            self.pagina_actual -= 1
            self.renderizar_tabla(self.creditos)

    def pag_sig(self):
        total_pags = max(1, (len(self.creditos) + self.por_pagina - 1) // self.por_pagina)
        if self.pagina_actual < total_pags:
            self.pagina_actual += 1
            self.renderizar_tabla(self.creditos)

    def filtrar_creditos(self):
        q = self.ent_buscar.get().strip().lower()
        filtrados = [c for c in self.creditos if not q or q in str(c[0]).lower() or q in c[1].lower()]
        self.pagina_actual = 1
        self.renderizar_tabla(filtrados)

    def abrir_registrar_abono(self):
        sel = self.tabla.selection()
        if not sel:
            messagebox.showwarning("Atención", "Seleccione una cuenta por cobrar para registrar el abono.")
            return

        vals = self.tabla.item(sel[0], "values")
        factura_id = vals[0]
        cajero = getattr(self.parent, "usuario", "")
        if not cajero:
            user_info = getattr(getattr(self.parent, "controlador", None), "usuario_actual", {}) or {}
            cajero = user_info.get("nombre") or user_info.get("username") or ""
        if not cajero:
            messagebox.showerror("Sesión requerida", "No se puede registrar un abono sin un usuario autenticado.")
            return

        def al_abonar(monto, medio_pago, cuenta_destino):
            try:
                if medio_pago != "Efectivo" and not cuenta_destino:
                    raise ValueError("Seleccione la cuenta bancaria del abono.")
                self.servicio_cxc.registrar_abono(
                    factura_id, vals[1], monto, medio_pago, cuenta_destino or None, cajero,
                )
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo registrar el abono: {e}")
                return
            messagebox.showinfo("Abono Registrado", f"Abono de $ {monto:,.2f} registrado exitosamente para la Factura #{factura_id}.")
            self.cargar_creditos()

        RegistrarAbonoModal(self, factura_id=factura_id, cliente=vals[1], saldo_pend=vals[3], callback_success=al_abonar)

    def configurar_plazo(self):
        dialog = tk.Toplevel(self)
        dialog.title("Configurar Plazo")
        posicionar_ventana(dialog, 320, 150, self)
        dialog.resizable(False, False)
        dialog.configure(bg="#C6D9E3")
        dialog.transient(self)
        dialog.grab_set()

        tk.Label(dialog, text="Plazo de crédito por defecto (días):", font=("sans", 10, "bold"), bg="#C6D9E3").pack(pady=10)
        ent = ttk.Entry(dialog, font=("sans", 12), justify="center")
        ent.insert(0, str(self.plazo_dias))
        ent.pack(pady=5)

        def guardar():
            try:
                dias = int(ent.get().strip())
                if dias <= 0:
                    raise ValueError
                self.plazo_dias = dias
                dialog.destroy()
                self.cargar_creditos()
            except ValueError:
                messagebox.showerror("Error", "Ingrese un número de días válido.")

        tk.Button(dialog, text="Guardar", command=guardar, bg="#EBEFF2", font=("sans", 10, "bold")).pack(pady=8)

    def ver_alertas(self):
        vencidos = [c for c in self.creditos if c[7] == "Vencido"]
        if not vencidos:
            messagebox.showinfo("Alertas", "No hay cuentas vencidas actualmente.")
            return
        detalle = "\n".join(f"Factura #{c[0]} - {c[1]} - Saldo {c[3]}" for c in vencidos)
        messagebox.showwarning("Cuentas Vencidas", f"Cuentas por cobrar vencidas:\n\n{detalle}")

    def ver_historial(self):
        from reporte_cuentas_cobrar import ReporteCuentasCobrar
        ReporteCuentasCobrar(self)

    def ver_abonos(self):
        sel = self.tabla.selection()
        if not sel:
            messagebox.showwarning("Atención", "Seleccione una cuenta para ver sus abonos.")
            return

        vals = self.tabla.item(sel[0], "values")
        try:
            abonos = self.servicio_cxc.listar_abonos(vals[0])
        except Exception as e:
            messagebox.showerror("Error", f"No se pudieron cargar los abonos: {e}")
            return

        if not abonos:
            messagebox.showinfo("Abonos", f"La factura #{vals[0]} no tiene abonos registrados.")
            return

        detalle = "\n".join(f"$ {m:,.2f}  -  {f} {h}  -  {c}" for m, f, h, c in abonos)
        messagebox.showinfo("Abonos Registrados", f"Factura #{vals[0]} - {vals[1]}\n\n{detalle}")

    def ver_anulados(self):
        messagebox.showinfo("Créditos Anulados", "Las facturas a crédito anuladas se pueden consultar desde Ventas > Anular Factura > Ver Facturas Anuladas.")
