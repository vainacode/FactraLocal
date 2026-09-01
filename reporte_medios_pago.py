import csv
import datetime
import os
import db_conexion as sqlite3
import sys
import tkinter as tk
from servicios.servicio_reportes import ServicioReportes
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageTk
from window_utils import posicionar_ventana

class ReporteMediosPago(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.title("Reporte de Ventas por Medios de Pago - La Casa de los Repuestos")
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
        lbl_title = tk.Label(
            self,
            text="REPORTE DE VENTAS POR MEDIOS DE PAGO",
            font=("sans", 20, "bold"),
            bg="#C6D9E3",
            fg="#1E293B"
        )
        lbl_title.place(relx=0.5, y=30, anchor="center")

        frame_top = tk.Frame(self, bg="#DDE1E5", highlightbackground="#B8C4CE", highlightthickness=1)
        frame_top.place(x=20, y=65, width=940, height=50)

        tk.Label(frame_top, text="Período:", font=("sans", 10, "bold"), bg="#DDE1E5", fg="#1E293B").place(x=15, y=14)
        self.cmb_periodo = ttk.Combobox(frame_top, values=["Hoy", "Esta Semana", "Este Mes", "Todo el Historial"], font=("sans", 10), state="readonly")
        self.cmb_periodo.set("Todo el Historial")
        self.cmb_periodo.place(x=80, y=11, width=180, height=28)
        self.cmb_periodo.bind("<<ComboboxSelected>>", lambda e: self.cargar_datos())

        # Botón Exportar CSV
        ruta_ex = self.rutas("icono/excel.png")
        if os.path.exists(ruta_ex):
            self.images["ex_ico"] = ImageTk.PhotoImage(Image.open(ruta_ex).resize((20, 20), Image.Resampling.LANCZOS))
            ico_ex = self.images["ex_ico"]
        else:
            ico_ex = None

        btn_exportar = tk.Button(
            frame_top,
            text="  Exportar CSV",
            image=ico_ex,
            compound=tk.LEFT,
            font=("sans", 10, "bold"),
            bg="#22C55E",
            fg="white",
            relief="raised",
            bd=2,
            cursor="hand2",
            command=self.exportar_csv
        )
        btn_exportar.place(x=800, y=9, width=125, height=32)

        # Tabla
        style = ttk.Style()
        style.configure("MP.Treeview.Heading", font=("sans", 10, "bold"), background="#E0E6ED")
        style.configure("MP.Treeview", font=("sans", 10), rowheight=26)

        cols = ("medio", "transacciones", "monto_total", "porcentaje")
        self.tabla = ttk.Treeview(self, columns=cols, show="headings", style="MP.Treeview")
        self.tabla.place(x=20, y=125, width=940, height=370)

        self.tabla.heading("medio", text="Método / Medio de Pago", anchor="w")
        self.tabla.heading("transacciones", text="Cantidad de Transacciones", anchor="center")
        self.tabla.heading("monto_total", text="Total Recaudado (RD$)", anchor="e")
        self.tabla.heading("porcentaje", text="Participación (%)", anchor="center")

        self.tabla.column("medio", width=340, anchor="w")
        self.tabla.column("transacciones", width=200, anchor="center")
        self.tabla.column("monto_total", width=240, anchor="e")
        self.tabla.column("porcentaje", width=160, anchor="center")

        frame_bot = tk.Frame(self, bg="#CAD8E2", highlightbackground="#A9BFCE", highlightthickness=1)
        frame_bot.place(x=20, y=505, width=940, height=75)

        self.lbl_tot_trans = tk.Label(frame_bot, text="Total Transacciones: 0", font=("sans", 11, "bold"), bg="#CAD8E2", fg="#1E293B")
        self.lbl_tot_trans.place(x=30, y=25)

        self.lbl_gran_total = tk.Label(frame_bot, text="TOTAL RECAUDADO: RD$ 0.00", font=("sans", 13, "bold"), bg="#CAD8E2", fg="#166534")
        self.lbl_gran_total.place(x=540, y=25)

    def cargar_datos(self):
        for r in self.tabla.get_children():
            self.tabla.delete(r)

        periodo = self.cmb_periodo.get()
        desde = None
        hoy = datetime.date.today()
        if periodo == "Hoy":
            desde = hoy
        elif periodo == "Esta Semana":
            desde = hoy - datetime.timedelta(days=hoy.weekday())
        elif periodo == "Este Mes":
            desde = hoy.replace(day=1)

        totales = {}
        try:
            fecha = desde.strftime("%Y-%m-%d") if desde else None
            ventas, credito = ServicioReportes().medios_pago(fecha)
            for medio, cantidad, monto in ventas:
                totales[medio] = [int(cantidad or 0), float(monto or 0)]
            medio, cantidad, monto = credito
            if cantidad:
                totales[medio] = [int(cantidad), float(monto or 0)]
        except Exception as e:
            print("Error cargando total ventas:", e)

        etiquetas = {
            "Efectivo": "💵 Efectivo (RD$)",
            "Tarjeta de Débito": "💳 Tarjeta de Débito",
            "Tarjeta de Crédito": "💳 Tarjeta de Crédito",
            "Transferencia": "🏦 Transferencia Bancaria",
            "Pago Mixto": "💳 Pago Mixto",
            "Venta a Crédito": "📝 Crédito Comercial / Cuenta Corriente",
        }
        gran_tot = sum(datos[1] for datos in totales.values())
        gran_cnt = sum(datos[0] for datos in totales.values())

        for m_nom, (cnt, mnt) in sorted(totales.items()):
            pct = ((mnt / gran_tot) * 100) if gran_tot > 0 else 0.0
            self.tabla.insert("", tk.END, values=(
                f"  {etiquetas.get(m_nom, m_nom)}",
                str(cnt),
                f"RD$ {mnt:,.2f}",
                f"{pct:,.1f} %"
            ))

        self.lbl_tot_trans.config(text=f"Total Transacciones: {gran_cnt}")
        self.lbl_gran_total.config(text=f"TOTAL RECAUDADO: RD$ {gran_tot:,.2f}")

    def exportar_csv(self):
        dest = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("Archivo CSV", "*.csv")],
            initialfile="Reporte_Medios_De_Pago.csv"
        )
        if dest:
            try:
                with open(dest, mode="w", newline="", encoding="utf-8-sig") as f:
                    writer = csv.writer(f)
                    writer.writerow(["Método / Medio de Pago", "Cantidad de Transacciones", "Total Recaudado (RD$)", "Participación (%)"])
                    for child in self.tabla.get_children():
                        writer.writerow(self.tabla.item(child, "values"))
                messagebox.showinfo("Exportación", f"Reporte exportado exitosamente a:\n{dest}")
            except Exception as e:
                messagebox.showerror("Error", f"Error exportando reporte: {e}")
