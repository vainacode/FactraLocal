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

class ReporteVentasMes(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.title("Reporte de Ventas por Mes - La Casa de los Repuestos")
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
        self.meses_nombres = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]

        self.widgets()
        self.cargar_datos()

    def rutas(self, ruta):
        try:
            rutabase = sys.__MEIPASS
        except Exception:
            rutabase = os.path.abspath(".")
        return os.path.join(rutabase, ruta)

    def widgets(self):
        # Header
        lbl_title = tk.Label(
            self,
            text="REPORTE DE VENTAS POR MES",
            font=("sans", 22, "bold"),
            bg="#C6D9E3",
            fg="#1E293B"
        )
        lbl_title.place(relx=0.5, y=30, anchor="center")

        # Filtro de Año
        frame_top = tk.Frame(self, bg="#DDE1E5", highlightbackground="#B8C4CE", highlightthickness=1)
        frame_top.place(x=20, y=65, width=940, height=50)

        tk.Label(frame_top, text="Año:", font=("sans", 11, "bold"), bg="#DDE1E5", fg="#1E293B").place(x=15, y=12)
        anio_actual = datetime.datetime.now().year
        self.cmb_anio = ttk.Combobox(frame_top, values=[str(y) for y in range(anio_actual - 3, anio_actual + 2)], font=("sans", 11), state="readonly")
        self.cmb_anio.set(str(anio_actual))
        self.cmb_anio.place(x=60, y=10, width=110, height=30)
        self.cmb_anio.bind("<<ComboboxSelected>>", lambda e: self.cargar_datos())

        btn_consultar = tk.Button(
            frame_top,
            text="Consultar",
            font=("sans", 10, "bold"),
            bg="#0284C7",
            fg="white",
            relief="raised",
            bd=2,
            cursor="hand2",
            command=self.cargar_datos
        )
        btn_consultar.place(x=185, y=9, width=110, height=32)

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

        # Tabla de Datos
        style = ttk.Style()
        style.configure("VM.Treeview.Heading", font=("sans", 10, "bold"), background="#E0E6ED")
        style.configure("VM.Treeview", font=("sans", 10), rowheight=24)

        cols = ("mes", "facturas", "articulos", "total_ventas", "ticket_prom")
        self.tabla = ttk.Treeview(self, columns=cols, show="headings", style="VM.Treeview")
        self.tabla.place(x=20, y=125, width=940, height=370)

        self.tabla.heading("mes", text="Mes", anchor="w")
        self.tabla.heading("facturas", text="Facturas Emitidas", anchor="center")
        self.tabla.heading("articulos", text="Cant. Repuestos Vendidos", anchor="center")
        self.tabla.heading("total_ventas", text="Total Ventas (RD$)", anchor="e")
        self.tabla.heading("ticket_prom", text="Ticket Promedio (RD$)", anchor="e")

        self.tabla.column("mes", width=220, anchor="w")
        self.tabla.column("facturas", width=160, anchor="center")
        self.tabla.column("articulos", width=180, anchor="center")
        self.tabla.column("total_ventas", width=190, anchor="e")
        self.tabla.column("ticket_prom", width=190, anchor="e")

        # Barra Inferior de Resumen
        frame_bot = tk.Frame(self, bg="#CAD8E2", highlightbackground="#A9BFCE", highlightthickness=1)
        frame_bot.place(x=20, y=505, width=940, height=75)

        self.lbl_tot_facturas = tk.Label(frame_bot, text="Total Facturas: 0", font=("sans", 11, "bold"), bg="#CAD8E2", fg="#1E293B")
        self.lbl_tot_facturas.place(x=30, y=25)

        self.lbl_tot_reps = tk.Label(frame_bot, text="Repuestos Vendidos: 0", font=("sans", 11, "bold"), bg="#CAD8E2", fg="#1E293B")
        self.lbl_tot_reps.place(x=300, y=25)

        self.lbl_gran_total = tk.Label(frame_bot, text="TOTAL ANUAL: RD$ 0.00", font=("sans", 13, "bold"), bg="#CAD8E2", fg="#166534")
        self.lbl_gran_total.place(x=620, y=25)

    def cargar_datos(self):
        for r in self.tabla.get_children():
            self.tabla.delete(r)

        anio = self.cmb_anio.get()
        datos_meses = {i: {"facturas": set(), "articulos": 0, "total": 0.0} for i in range(1, 13)}

        try:
            rows = ServicioReportes().ventas_mes(anio)
            for fac, cant, tot, fec in rows:
                try:
                    m = int(fec.split("-")[1])
                    if 1 <= m <= 12:
                        datos_meses[m]["facturas"].add(fac)
                        datos_meses[m]["articulos"] += int(cant or 1)
                        datos_meses[m]["total"] += float(tot or 0.0)
                except Exception:
                    pass
        except Exception as e:
            print("Error cargando ventas por mes:", e)

        gran_total = 0.0
        gran_facturas = 0
        gran_articulos = 0

        for m in range(1, 13):
            mes_nom = self.meses_nombres[m - 1]
            num_facs = len(datos_meses[m]["facturas"])
            num_arts = datos_meses[m]["articulos"]
            tot_v = datos_meses[m]["total"]
            ticket_prom = (tot_v / num_facs) if num_facs > 0 else 0.0

            gran_total += tot_v
            gran_facturas += num_facs
            gran_articulos += num_arts

            self.tabla.insert("", tk.END, values=(
                f"  {mes_nom}",
                str(num_facs),
                str(num_arts),
                f"RD$ {tot_v:,.2f}",
                f"RD$ {ticket_prom:,.2f}"
            ))

        self.lbl_tot_facturas.config(text=f"Total Facturas: {gran_facturas}")
        self.lbl_tot_reps.config(text=f"Repuestos Vendidos: {gran_articulos}")
        self.lbl_gran_total.config(text=f"TOTAL ANUAL: RD$ {gran_total:,.2f}")

    def exportar_csv(self):
        dest = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("Archivo CSV", "*.csv")],
            initialfile=f"Reporte_Ventas_Por_Mes_{self.cmb_anio.get()}.csv"
        )
        if dest:
            try:
                with open(dest, mode="w", newline="", encoding="utf-8-sig") as f:
                    writer = csv.writer(f)
                    writer.writerow(["Mes", "Facturas Emitidas", "Cant. Repuestos Vendidos", "Total Ventas (RD$)", "Ticket Promedio (RD$)"])
                    for child in self.tabla.get_children():
                        writer.writerow(self.tabla.item(child, "values"))
                messagebox.showinfo("Exportación", f"Reporte exportado exitosamente a:\n{dest}")
            except Exception as e:
                messagebox.showerror("Error", f"Error exportando reporte: {e}")
