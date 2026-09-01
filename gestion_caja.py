import datetime
import os
import db_conexion as sqlite3
import sys
import tkinter as tk
from tkinter import messagebox, ttk, simpledialog
from PIL import Image, ImageTk
from caja_detalle import DetalleCaja
from window_utils import posicionar_ventana
from servicios.servicio_caja import ServicioCaja
from dominio.caja.excepciones import CajaError

class GestionCaja(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.title("Punto de Venta Versión 4.4.7 - Gestión de Caja")
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
        self.servicio_caja = ServicioCaja()
        user_info = getattr(getattr(parent, "controlador", None), "usuario_actual", {})
        self.usuario = user_info.get("nombre") or user_info.get("username")
        self.rol = user_info.get("rol")
        self.images = {}
        self.registros_caja = []
        self.pagina_actual = 1
        self.por_pagina = 12

        self.widgets()
        self.cargar_cajas()

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
            text="GESTIÓN DE CAJA",
            font=("sans", 28, "bold"),
            bg="#DDE1E5",
            fg="#1E293B"
        )
        lbl_titulo.place(relx=0.5, y=35, anchor="center")

#============== 2. FILTROS DE BÚSQUEDA =============================================================#
        frame_filtros = tk.LabelFrame(
            self,
            text="Filtros de Búsqueda",
            font=("sans", 12, "bold"),
            bg="#C6D9E3",
            fg="#1E293B",
            padx=12,
            pady=8
        )
        frame_filtros.place(x=20, y=70, width=1060, height=85)

        # Buscar ID
        lbl_id = tk.Label(frame_filtros, text="Buscar ID:", font=("sans", 11, "bold"), bg="#C6D9E3", fg="#1E293B")
        lbl_id.place(x=10, y=10)

        self.ent_id = ttk.Entry(frame_filtros, font=("sans", 11), justify="center")
        self.ent_id.place(x=95, y=8, width=140, height=30)

        # Estado
        lbl_est = tk.Label(frame_filtros, text="Estado:", font=("sans", 11, "bold"), bg="#C6D9E3", fg="#1E293B")
        lbl_est.place(x=260, y=10)

        self.cmb_estado = ttk.Combobox(frame_filtros, values=["Todas", "Abierta", "Cerrada"], font=("sans", 11), state="readonly")
        self.cmb_estado.current(0)
        self.cmb_estado.place(x=325, y=8, width=130, height=30)

        # Fecha
        lbl_fec = tk.Label(frame_filtros, text="Fecha:", font=("sans", 11, "bold"), bg="#C6D9E3", fg="#1E293B")
        lbl_fec.place(x=480, y=10)

        self.ent_fecha = ttk.Entry(frame_filtros, font=("sans", 11), justify="center")
        self.ent_fecha.place(x=540, y=8, width=140, height=30)

        ruta_cal = self.rutas("icono/calendario.png")
        if os.path.exists(ruta_cal):
            self.images["cal_gc_ico"] = ImageTk.PhotoImage(Image.open(ruta_cal).resize((20, 20), Image.Resampling.LANCZOS))
            btn_cal = tk.Button(frame_filtros, image=self.images["cal_gc_ico"], bg="white", relief="solid", bd=1, cursor="hand2", command=self.hoy_en_fecha)
            btn_cal.place(x=685, y=8, width=30, height=30)

        # Botón Buscar
        ruta_b = self.rutas("icono/buscar.png")
        if os.path.exists(ruta_b):
            self.images["b_gc_ico"] = ImageTk.PhotoImage(Image.open(ruta_b).resize((22, 22), Image.Resampling.LANCZOS))
            btn_b = tk.Button(frame_filtros, image=self.images["b_gc_ico"], bg="white", relief="solid", bd=1, cursor="hand2", command=self.filtrar)
            btn_b.place(x=835, y=6, width=36, height=34)

        # Botón Limpiar
        ruta_l = self.rutas("icono/limpiar.png")
        if os.path.exists(ruta_l):
            self.images["l_gc_ico"] = ImageTk.PhotoImage(Image.open(ruta_l).resize((20, 20), Image.Resampling.LANCZOS))
            ico_l = self.images["l_gc_ico"]
        else:
            ico_l = None

        btn_l = tk.Button(frame_filtros, text="  Limpiar", image=ico_l, compound=tk.LEFT, font=("sans", 10, "bold"), bg="#EBEFF2", fg="#1E293B", relief="raised", bd=2, cursor="hand2", command=self.limpiar_filtros)
        btn_l.place(x=885, y=6, width=115, height=34)

#============== 3. TABLA DE CAJAS ==================================================================#
        style = ttk.Style()
        style.configure("GC.Treeview.Heading", font=("sans", 9, "bold"), background="#E0E6ED")
        style.configure("GC.Treeview", font=("sans", 9), rowheight=24)

        cols = ("id", "fecha_ap", "monto_ini", "efectivo_caja", "estado", "tot_ventas", "fecha_ci", "impuesto", "descuento")
        self.tabla = ttk.Treeview(self, columns=cols, show="headings", style="GC.Treeview")
        self.tabla.place(x=20, y=165, width=1060, height=400)

        titulos = [
            ("id", "ID", 40),
            ("fecha_ap", "Fecha Apertura", 160),
            ("monto_ini", "Monto Inicial", 110),
            ("efectivo_caja", "Efectivo en Caja", 130),
            ("estado", "Estado", 100),
            ("tot_ventas", "Total Ventas", 120),
            ("fecha_ci", "Fecha Cierre", 150),
            ("impuesto", "Impuesto", 110),
            ("descuento", "Descuento", 110),
        ]

        for c, t, w in titulos:
            self.tabla.heading(c, text=t, anchor="center")
            self.tabla.column(c, width=w, anchor="center" if c in ("id", "estado", "fecha_ap", "fecha_ci") else "e")

        scroll_y = ttk.Scrollbar(self, orient="vertical", command=self.tabla.yview)
        self.tabla.configure(yscrollcommand=scroll_y.set)
        scroll_y.place(x=1082, y=165, height=400)

        self.tabla.bind("<Double-1>", self.al_hacer_doble_click)

#============== 4. BARRA INFERIOR DE ACCIONES =======================================================#
        ruta_izq = self.rutas("icono/izquierda.png")
        if os.path.exists(ruta_izq):
            self.images["izq_gc"] = ImageTk.PhotoImage(Image.open(ruta_izq).resize((18, 18), Image.Resampling.LANCZOS))
            btn_izq = tk.Button(self, image=self.images["izq_gc"], bg="#EBEFF2", relief="raised", bd=1, cursor="hand2")
            btn_izq.place(x=25, y=580, width=24, height=24)

        ruta_der = self.rutas("icono/derecha.png")
        if os.path.exists(ruta_der):
            self.images["der_gc"] = ImageTk.PhotoImage(Image.open(ruta_der).resize((18, 18), Image.Resampling.LANCZOS))
            btn_der = tk.Button(self, image=self.images["der_gc"], bg="#EBEFF2", relief="raised", bd=1, cursor="hand2")
            btn_der.place(x=53, y=580, width=24, height=24)

        self.lbl_pag = tk.Label(self, text="Página 1 de 1", font=("sans", 10, "bold"), bg="#DDE1E5", fg="#1E293B")
        self.lbl_pag.place(x=85, y=582)

        # Botones: Abrir, Cerrar, Ingreso, Egreso
        botones_caja = [
            ("Abrir", "abrircaja.png", self.abrir_caja),
            ("Cerrar", "cerrarcaja.png", self.cerrar_caja),
            ("Ingreso", "mediospago.png", self.ingreso_manual),
            ("Egreso", "pago3.png", self.egreso_manual),
        ]

        x_b = 510
        for txt, ico_f, cmd in botones_caja:
            ruta_i = self.rutas(f"icono/{ico_f}")
            if os.path.exists(ruta_i):
                img_i = Image.open(ruta_i).resize((22, 22), Image.Resampling.LANCZOS)
                self.images[f"btn_gc_{ico_f}"] = ImageTk.PhotoImage(img_i)
                ico_btn = self.images[f"btn_gc_{ico_f}"]
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
            btn.place(x=x_b, y=575, width=125, height=40)
            x_b += 138

    def cargar_cajas(self):
        for r in self.tabla.get_children():
            self.tabla.delete(r)

        try:
            rows = self.servicio_caja.listar()
            self.registros_caja = []
            for r in rows:
                cid = r[0]
                f_ap = r[1]
                m_ini = f"RD$ {r[2]:,.2f}"
                m_ef = f"RD$ {r[3]:,.2f}"
                est = r[4].lower() if r[4] else "abierta"
                tot_v = f"RD$ {r[5]:,.2f}"
                f_ci = r[6]
                imp = "RD$ 0.00"
                desc = "RD$ 0.00"
                self.registros_caja.append((cid, f_ap, m_ini, m_ef, est, tot_v, f_ci, imp, desc))
        except Exception:
            self.registros_caja = []

        self.tabla.tag_configure("caja_abierta", background="#DCFCE7")
        self.tabla.tag_configure("caja_cerrada", background="#F8FAFC")

        for c in self.registros_caja:
            tag = "caja_abierta" if "abierta" in c[4].lower() else "caja_cerrada"
            self.tabla.insert("", tk.END, values=c, tags=(tag,))

    def al_hacer_doble_click(self, event=None):
        sel = self.tabla.selection()
        if not sel:
            return
        vals = self.tabla.item(sel[0], "values")
        if vals:
            DetalleCaja(self, caja_id=vals[0])

    def hoy_en_fecha(self):
        self.ent_fecha.delete(0, tk.END)
        self.ent_fecha.insert(0, datetime.datetime.now().strftime("%Y-%m-%d"))
        self.filtrar()

    def filtrar(self):
        id_f = self.ent_id.get().strip()
        fecha_f = self.ent_fecha.get().strip()
        estado_f = self.cmb_estado.get()

        for r in self.tabla.get_children():
            self.tabla.delete(r)

        for c in self.registros_caja:
            if id_f and str(c[0]) != id_f:
                continue
            if fecha_f and fecha_f not in c[1]:
                continue
            if estado_f != "Todas" and estado_f.lower() != c[4].lower():
                continue
            tag = "caja_abierta" if "abierta" in c[4].lower() else "caja_cerrada"
            self.tabla.insert("", tk.END, values=c, tags=(tag,))

    def limpiar_filtros(self):
        self.ent_id.delete(0, tk.END)
        self.ent_fecha.delete(0, tk.END)
        self.cmb_estado.current(0)
        self.cargar_cajas()

    def abrir_caja(self):
        from abrir_caja_modal import AbrirCajaModal
        def al_abrir(estado, monto):
            self.cargar_cajas()
        if not self.usuario:
            messagebox.showwarning("Sesión requerida", "Debe iniciar sesión para abrir una caja.")
            return
        AbrirCajaModal(self, usuario=self.usuario, callback_exito=al_abrir)

    def cerrar_caja(self):
        from reporte_caja import ReporteCajaUsuario
        if self.rol not in ("Administrador", "Supervisor"):
            messagebox.showwarning("Acceso restringido", "Solo un supervisor o administrador puede cerrar una caja.")
            return
        if messagebox.askyesno("Cerrar Caja", "¿Desea cerrar el turno actual de caja?\n\nAl confirmar se generará y mostrará el Reporte de Caja."):
            try:
                caja = self.servicio_caja.obtener_abierta()
                if not caja:
                    messagebox.showwarning("Caja cerrada", "No hay una caja abierta para cerrar.")
                    return
                contado = simpledialog.askfloat("Cuadre de caja", "Indique el efectivo contado físicamente:", parent=self, minvalue=0)
                if contado is None:
                    return
                resultado_cierre = self.servicio_caja.cerrar(caja[0], contado)
            except Exception as e:
                messagebox.showerror("Error cerrando caja", f"La caja no se cerró:\n{e}")
                return

            self.cargar_cajas()
            diferencia = resultado_cierre["diferencia"]
            if diferencia < 0:
                resultado = f"FALTANTE: RD$ {abs(diferencia):,.2f}"
            elif diferencia > 0:
                resultado = f"SOBRANTE: RD$ {diferencia:,.2f}"
            else:
                resultado = "CUADRE EXACTO"
            messagebox.showinfo("Caja Cerrada", f"La caja se cerró correctamente.\n\nEsperado: RD$ {resultado_cierre['esperado']:,.2f}\nContado: RD$ {resultado_cierre['contado']:,.2f}\n{resultado}\n\nA continuación se mostrará el reporte.")
            ReporteCajaUsuario(self)

    def ingreso_manual(self):
        self.registrar_movimiento("INGRESO")

    def egreso_manual(self):
        self.registrar_movimiento("EGRESO")

    def registrar_movimiento(self, tipo):
        usuario = self.usuario
        if not usuario:
            messagebox.showwarning("Sesión requerida", "Debe iniciar sesión para registrar movimientos.")
            return
        concepto = simpledialog.askstring("Concepto", "Indique el concepto del movimiento:", parent=self)
        if not concepto or not concepto.strip():
            return
        monto = simpledialog.askfloat("Monto", "Indique el monto en RD$:", parent=self, minvalue=0.01)
        if monto is None:
            return
        try:
            self.servicio_caja.registrar_movimiento(usuario, tipo, concepto.strip(), monto)
            self.cargar_cajas()
            messagebox.showinfo("Movimiento registrado", f"{tipo.title()} registrado por RD$ {monto:,.2f}.")
        except Exception as error:
            messagebox.showerror("Error", f"No se pudo registrar el movimiento: {error}")
