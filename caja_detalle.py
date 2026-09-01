import os
import csv
import os
import db_conexion as sqlite3
import sys
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
from ventas_efectivo_detalle import VentasEfectivoDetalle
from window_utils import posicionar_ventana
from servicios.servicio_caja import ServicioCaja

class DetalleCaja(tk.Toplevel):
    def __init__(self, parent, caja_id=1):
        super().__init__(parent)
        self.parent = parent
        self.caja_id = caja_id
        self.db_name = "database.db"
        self.servicio_caja = ServicioCaja()
        self.title(f"Detalle de Caja - #{caja_id}")
        posicionar_ventana(self, 1060, 640, parent)
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
        self.cargar_datos_caja()

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
            text="DETALLE DE CAJA",
            font=("sans", 24, "bold"),
            bg="#C6D9E3",
            fg="#1E293B"
        )
        lbl_title.place(relx=0.5, y=25, anchor="center")

#============== 2. INFORMACIÓN DE LA CAJA ==========================================================#
        frame_info = tk.LabelFrame(
            self,
            text="Información de la Caja",
            font=("sans", 11, "bold"),
            bg="#C6D9E3",
            fg="#1E293B",
            padx=12,
            pady=4
        )
        frame_info.place(x=15, y=45, width=1030, height=60)

        cajero_val = "-"
        apertura_val = "-"
        estado_val = "SIN DATOS"
        self.fecha_caja = None
        self.monto_inicial = 0.0

        try:
            r = self.servicio_caja.obtener_detalle(self.caja_id)
            if r:
                self.fecha_caja = r[1]
                apertura_val = r[2]
                estado_val = (r[3] or "ABIERTA").upper()
                cajero_val = r[4] or "-"
                self.monto_inicial = r[5] or 0.0
        except Exception:
            pass

        lbl_idc = tk.Label(frame_info, text=f"ID Caja: #{self.caja_id}", font=("sans", 11, "bold"), bg="#C6D9E3", fg="#0284C7")
        lbl_idc.place(x=15, y=5)

        lbl_ap = tk.Label(frame_info, text=f"| Apertura: {apertura_val}", font=("sans", 10), bg="#C6D9E3", fg="#1E293B")
        lbl_ap.place(x=120, y=5)

        lbl_est = tk.Label(frame_info, text=f"| Estado: {estado_val}", font=("sans", 10, "bold"), bg="#C6D9E3", fg="#16A34A" if "ABIERTA" in estado_val else "#DC2626")
        lbl_est.place(x=520, y=5)

        lbl_usr = tk.Label(frame_info, text=f"| Cajero: {cajero_val}", font=("sans", 10, "bold"), bg="#C6D9E3", fg="#1E293B")
        lbl_usr.place(x=700, y=5)

#============== 3. MOVIMIENTOS (IZQUIERDA) =========================================================#
        frame_mov = tk.LabelFrame(
            self,
            text="MOVIMIENTOS",
            font=("sans", 11, "bold"),
            bg="#C6D9E3",
            fg="#16A34A",
            padx=10,
            pady=6
        )
        frame_mov.place(x=15, y=110, width=330, height=450)

        movs = [
            ("Monto Inicial:", "#1E293B", "lbl_mov_inicial"),
            ("+ Ventas en Efectivo:", "#16A34A", "lbl_mov_ef"),
            ("+ Abonos en Efectivo:", "#16A34A", "lbl_mov_abef"),
            ("+ Ingreso Manual:", "#16A34A", "lbl_mov_ingm"),
            ("- Egreso Manual:", "#DC2626", "lbl_mov_egm"),
            ("- Gastos:", "#DC2626", "lbl_mov_gastos"),
            ("- Compras:", "#DC2626", "lbl_mov_compras"),
        ]

        y_m = 8
        for t, c, attr in movs:
            lbl_t = tk.Label(frame_mov, text=t, font=("sans", 9, "bold" if "Monto" in t else "normal"), bg="#C6D9E3", fg=c, cursor="hand2" if "Ventas en Efectivo" in t else "")
            lbl_t.place(x=10, y=y_m)
            if "Ventas en Efectivo" in t:
                lbl_t.bind("<Button-1>", lambda e: VentasEfectivoDetalle(self))

            lbl_v = tk.Label(frame_mov, text="$ 0.00", font=("sans", 9, "bold"), bg="#C6D9E3", fg=c)
            lbl_v.place(x=225, y=y_m)
            setattr(self, attr, lbl_v)
            y_m += 26

        tk.Frame(frame_mov, bg="#16A34A", height=2).place(x=5, y=200, width=305)

        tk.Label(frame_mov, text="= EFECTIVO EN CAJA:", font=("sans", 10, "bold"), bg="#C6D9E3", fg="#16A34A").place(x=10, y=210)
        self.lbl_mov_efcaja = tk.Label(frame_mov, text="$ 0.00", font=("sans", 10, "bold"), bg="#C6D9E3", fg="#16A34A")
        self.lbl_mov_efcaja.place(x=215, y=210)

        tk.Label(frame_mov, text="+ Pagos Electrónicos:", font=("sans", 9), bg="#C6D9E3", fg="#0284C7").place(x=10, y=240)
        self.lbl_mov_pagoelec = tk.Label(frame_mov, text="$ 0.00", font=("sans", 9), bg="#C6D9E3", fg="#0284C7")
        self.lbl_mov_pagoelec.place(x=250, y=240)

        tk.Label(frame_mov, text="+ Abonos Electrónicos:", font=("sans", 9), bg="#C6D9E3", fg="#0284C7").place(x=10, y=265)
        self.lbl_mov_abelec = tk.Label(frame_mov, text="$ 0.00", font=("sans", 9), bg="#C6D9E3", fg="#0284C7")
        self.lbl_mov_abelec.place(x=250, y=265)

        tk.Frame(frame_mov, bg="#1E293B", height=2).place(x=5, y=300, width=305)

        tk.Label(frame_mov, text="= TOTAL:", font=("sans", 12, "bold"), bg="#C6D9E3", fg="#1E293B").place(x=10, y=315)
        self.lbl_mov_total = tk.Label(frame_mov, text="$ 0.00", font=("sans", 12, "bold"), bg="#C6D9E3", fg="#1E293B")
        self.lbl_mov_total.place(x=205, y=315)

#============== 4. TOTAL MEDIO DE PAGO (CENTRO) ====================================================#
        frame_med = tk.LabelFrame(
            self,
            text="TOTAL MEDIO DE PAGO",
            font=("sans", 11, "bold"),
            bg="#C6D9E3",
            fg="#D97706",
            padx=10,
            pady=6
        )
        frame_med.place(x=355, y=110, width=330, height=275)

        self.lbl_medios = {}
        medios = ["Efectivo", "Tarjeta de Débito", "Tarjeta de Crédito", "Transferencia", "Pago Mixto"]

        y_med = 6
        for medio in medios:
            tk.Label(frame_med, text=f"• {medio}:", font=("sans", 9), bg="#C6D9E3", fg="#1E293B").place(x=10, y=y_med)
            lbl_v = tk.Label(frame_med, text="$ 0.00", font=("sans", 9, "bold"), bg="#C6D9E3", fg="#D97706")
            lbl_v.place(x=150, y=y_med)
            lbl_c = tk.Label(frame_med, text="(0 ventas)", font=("sans", 8), bg="#C6D9E3", fg="#64748B")
            lbl_c.place(x=245, y=y_med)
            self.lbl_medios[medio] = (lbl_v, lbl_c)
            y_med += 24

        tk.Frame(frame_med, bg="#F59E0B", height=2).place(x=5, y=130, width=305)

        tk.Label(frame_med, text="Total (sin crédito):", font=("sans", 9, "bold"), bg="#C6D9E3", fg="#D97706").place(x=10, y=140)
        self.lbl_med_sincredito = tk.Label(frame_med, text="$ 0.00", font=("sans", 9, "bold"), bg="#C6D9E3", fg="#D97706")
        self.lbl_med_sincredito.place(x=210, y=140)

        tk.Label(frame_med, text="Ventas a Crédito:", font=("sans", 9), bg="#C6D9E3", fg="#EF4444").place(x=10, y=168)
        self.lbl_med_credito = tk.Label(frame_med, text="$ 0.00", font=("sans", 9), bg="#C6D9E3", fg="#EF4444")
        self.lbl_med_credito.place(x=250, y=168)

        tk.Frame(frame_med, bg="#1E293B", height=2).place(x=5, y=198, width=305)

        tk.Label(frame_med, text="TOTAL GENERAL:", font=("sans", 10, "bold"), bg="#C6D9E3", fg="#1E293B").place(x=10, y=210)
        self.lbl_med_total = tk.Label(frame_med, text="$ 0.00", font=("sans", 10, "bold"), bg="#C6D9E3", fg="#1E293B")
        self.lbl_med_total.place(x=210, y=210)

#============== 5. OTROS DATOS (CENTRO-ABAJO) =======================================================#
        frame_otros = tk.LabelFrame(
            self,
            text="OTROS DATOS",
            font=("sans", 11, "bold"),
            bg="#C6D9E3",
            fg="#0284C7",
            padx=10,
            pady=6
        )
        frame_otros.place(x=355, y=390, width=330, height=170)

        tk.Label(frame_otros, text="Descuentos:", font=("sans", 9), bg="#C6D9E3", fg="#1E293B").place(x=15, y=15)
        self.lbl_otros_desc = tk.Label(frame_otros, text="$ 0.00", font=("sans", 9, "bold"), bg="#C6D9E3", fg="#0284C7")
        self.lbl_otros_desc.place(x=240, y=15)

        tk.Label(frame_otros, text="Impuestos:", font=("sans", 9), bg="#C6D9E3", fg="#1E293B").place(x=15, y=45)
        self.lbl_otros_imp = tk.Label(frame_otros, text="$ 0.00", font=("sans", 9, "bold"), bg="#C6D9E3", fg="#0284C7")
        self.lbl_otros_imp.place(x=240, y=45)

#============== 6. DETALLE DE GASTOS (DERECHA-ARRIBA) ===============================================#
        frame_gastos = tk.LabelFrame(
            self,
            text="DETALLE DE GASTOS",
            font=("sans", 11, "bold"),
            bg="#C6D9E3",
            fg="#DC2626",
            padx=10,
            pady=6
        )
        frame_gastos.place(x=695, y=110, width=350, height=275)

        tk.Label(frame_gastos, text="Total Gastos:", font=("sans", 11, "bold"), bg="#C6D9E3", fg="#DC2626").place(x=15, y=10)
        self.lbl_gastos_total = tk.Label(frame_gastos, text="$ 0.00", font=("sans", 11, "bold"), bg="#C6D9E3", fg="#DC2626")
        self.lbl_gastos_total.place(x=260, y=10)

        self.lbl_gastos_detalle = tk.Label(frame_gastos, text="No se registraron gastos", font=("sans", 9, "italic"), bg="#C6D9E3", fg="#64748B", justify="left", wraplength=320)
        self.lbl_gastos_detalle.place(x=15, y=55)

#============== 7. INFO CRÉDITOS (DERECHA-ABAJO) ===================================================#
        frame_cred = tk.LabelFrame(
            self,
            text="INFO CRÉDITOS",
            font=("sans", 11, "bold"),
            bg="#C6D9E3",
            fg="#7C3AED",
            padx=10,
            pady=6
        )
        frame_cred.place(x=695, y=390, width=350, height=170)

        tk.Label(frame_cred, text="Ventas a Crédito:", font=("sans", 9), bg="#C6D9E3", fg="#1E293B").place(x=15, y=10)
        self.lbl_cred_ventas = tk.Label(frame_cred, text="$ 0.00", font=("sans", 9, "bold"), bg="#C6D9E3", fg="#7C3AED")
        self.lbl_cred_ventas.place(x=260, y=10)

        tk.Label(frame_cred, text="Saldo Pendiente:", font=("sans", 9), bg="#C6D9E3", fg="#1E293B").place(x=15, y=38)
        self.lbl_cred_saldo = tk.Label(frame_cred, text="$ 0.00", font=("sans", 9, "bold"), bg="#C6D9E3", fg="#7C3AED")
        self.lbl_cred_saldo.place(x=260, y=38)

        tk.Label(frame_cred, text="Total Abonado:", font=("sans", 9), bg="#C6D9E3", fg="#1E293B").place(x=15, y=66)
        self.lbl_cred_abonado = tk.Label(frame_cred, text="$ 0.00", font=("sans", 9, "bold"), bg="#C6D9E3", fg="#7C3AED")
        self.lbl_cred_abonado.place(x=260, y=66)

#============== 8. BOTONES INFERIORES ===============================================================#
        ruta_pdf = self.rutas("icono/pdf.png")
        if os.path.exists(ruta_pdf):
            self.images["pdf_dc"] = ImageTk.PhotoImage(Image.open(ruta_pdf).resize((22, 22), Image.Resampling.LANCZOS))
            ico_pdf = self.images["pdf_dc"]
        else:
            ico_pdf = None

        btn_pdf = tk.Button(self, text="  Exportar PDF", image=ico_pdf, compound=tk.LEFT, font=("sans", 10, "bold"), bg="#EBEFF2", fg="#1E293B", relief="raised", bd=2, cursor="hand2", command=self.exportar_pdf)
        btn_pdf.place(x=340, y=575, width=155, height=42)

        ruta_ref = self.rutas("icono/actualizar1.png")
        if not os.path.exists(ruta_ref):
            ruta_ref = self.rutas("icono/actualizar.png")

        if os.path.exists(ruta_ref):
            self.images["ref_dc"] = ImageTk.PhotoImage(Image.open(ruta_ref).resize((22, 22), Image.Resampling.LANCZOS))
            btn_ref = tk.Button(self, image=self.images["ref_dc"], bg="#EBEFF2", relief="raised", bd=2, cursor="hand2", command=self.cargar_datos_caja)
            btn_ref.place(x=505, y=575, width=42, height=42)

        ruta_close = self.rutas("icono/cancelar.png")
        if os.path.exists(ruta_close):
            self.images["cls_dc"] = ImageTk.PhotoImage(Image.open(ruta_close).resize((22, 22), Image.Resampling.LANCZOS))
            ico_c = self.images["cls_dc"]
        else:
            ico_c = None

        btn_close = tk.Button(self, text="  Cerrar", image=ico_c, compound=tk.LEFT, font=("sans", 10, "bold"), bg="#EBEFF2", fg="#1E293B", relief="raised", bd=2, cursor="hand2", command=self.destroy)
        btn_close.place(x=558, y=575, width=130, height=42)

    def exportar_pdf(self):
        destino = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("Archivo CSV", "*.csv")],
            initialfile=f"Detalle_Caja_{self.caja_id}.csv",
        )
        if not destino:
            return
        try:
            with open(destino, "w", newline="", encoding="utf-8-sig") as archivo:
                writer = csv.writer(archivo)
                writer.writerow(["Caja", "Tipo", "Referencia", "Importe", "Fecha", "Hora", "Usuario"])
                ventas, gastos, movimientos = self.servicio_caja.detalle_exportacion(self.caja_id)
                writer.writerows([[self.caja_id, *fila] for fila in ventas])
                writer.writerows([[self.caja_id, *fila] for fila in gastos])
                writer.writerows([[self.caja_id, *fila] for fila in movimientos])
            messagebox.showinfo("Exportar", f"Detalle exportado en:\n{destino}")
        except Exception as error:
            messagebox.showerror("Error", f"No se pudo exportar el detalle: {error}")

    def cargar_datos_caja(self):
        if not self.fecha_caja:
            return

        medios_electronicos = {"Tarjeta de Débito", "Tarjeta de Crédito", "Transferencia"}
        ventas_por_medio = {}
        total_ventas = 0.0
        total_efectivo = 0.0
        total_electronico = 0.0
        total_gastos = 0.0
        detalle_gastos = []
        total_descuentos = 0.0
        total_credito = 0.0
        saldo_credito_pend = 0.0
        total_abonado = 0.0
        ingresos_caja = 0.0
        egresos_caja = 0.0

        try:
            ventas, total_gastos, detalle_gastos, ingresos_caja, egresos_caja, total_descuentos, creditos_dia, abonos, total_abonado = self.servicio_caja.detalle_caja(self.caja_id, self.fecha_caja)
            for medio, cnt, monto in ventas:
                    monto = monto or 0.0
                    ventas_por_medio[medio] = (cnt, monto)
                    total_ventas += monto
                    if medio in medios_electronicos:
                        total_electronico += monto
                    elif medio != "Pago Mixto":
                        total_efectivo += monto

            total_credito = sum(t for _, t in creditos_dia)
            for factura, total in creditos_dia:
                saldo_credito_pend += max(0.0, total - abonos.get(factura, 0.0))
        except Exception as e:
            print("Error cargando datos de caja:", e)

        efectivo_en_caja = self.monto_inicial + total_efectivo + float(ingresos_caja or 0) - float(egresos_caja or 0) - total_gastos
        total_general = self.monto_inicial + total_ventas

        self.lbl_mov_inicial.config(text=f"$ {self.monto_inicial:,.2f}")
        self.lbl_mov_ef.config(text=f"$ {total_efectivo:,.2f}")
        self.lbl_mov_gastos.config(text=f"$ {total_gastos:,.2f}")
        self.lbl_mov_efcaja.config(text=f"$ {efectivo_en_caja:,.2f}")
        self.lbl_mov_pagoelec.config(text=f"$ {total_electronico:,.2f}")
        self.lbl_mov_total.config(text=f"$ {total_general:,.2f}")

        for medio, (lbl_v, lbl_c) in self.lbl_medios.items():
            cnt, monto = ventas_por_medio.get(medio, (0, 0.0))
            lbl_v.config(text=f"$ {monto:,.2f}")
            lbl_c.config(text=f"({cnt} venta{'s' if cnt != 1 else ''})")

        self.lbl_med_sincredito.config(text=f"$ {total_ventas:,.2f}")
        self.lbl_med_credito.config(text=f"$ {total_credito:,.2f}")
        self.lbl_med_total.config(text=f"$ {(total_ventas + total_credito):,.2f}")

        self.lbl_otros_desc.config(text=f"$ {total_descuentos:,.2f}")

        self.lbl_gastos_total.config(text=f"$ {total_gastos:,.2f}")
        if detalle_gastos:
            texto = "\n".join(f"• {c}: $ {m:,.2f}" for c, m in detalle_gastos[:5])
            self.lbl_gastos_detalle.config(text=texto)
        else:
            self.lbl_gastos_detalle.config(text="No se registraron gastos")

        self.lbl_cred_ventas.config(text=f"$ {total_credito:,.2f}")
        self.lbl_cred_saldo.config(text=f"$ {saldo_credito_pend:,.2f}")
        self.lbl_cred_abonado.config(text=f"$ {total_abonado:,.2f}")
