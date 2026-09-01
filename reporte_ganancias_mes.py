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

class ReporteGananciasMes(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.title("Reporte de Ganancias por Mes - La Casa de los Repuestos")
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
            text="REPORTE DE GANANCIAS POR MES",
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
        style.configure("GM.Treeview.Heading", font=("sans", 10, "bold"), background="#E0E6ED")
        style.configure("GM.Treeview", font=("sans", 10), rowheight=24)

        cols = ("mes", "ingresos", "costos", "gastos", "ganancia_neta", "margen")
        self.tabla = ttk.Treeview(self, columns=cols, show="headings", style="GM.Treeview")
        self.tabla.place(x=20, y=125, width=940, height=370)

        self.tabla.heading("mes", text="Mes", anchor="w")
        self.tabla.heading("ingresos", text="Ingresos Ventas (RD$)", anchor="e")
        self.tabla.heading("costos", text="Costo Mercancía (RD$)", anchor="e")
        self.tabla.heading("gastos", text="Gastos Operativos (RD$)", anchor="e")
        self.tabla.heading("ganancia_neta", text="Ganancia Neta (RD$)", anchor="e")
        self.tabla.heading("margen", text="Margen (%)", anchor="center")

        self.tabla.column("mes", width=180, anchor="w")
        self.tabla.column("ingresos", width=160, anchor="e")
        self.tabla.column("costos", width=160, anchor="e")
        self.tabla.column("gastos", width=150, anchor="e")
        self.tabla.column("ganancia_neta", width=170, anchor="e")
        self.tabla.column("margen", width=120, anchor="center")

        # Barra Inferior de Resumen
        frame_bot = tk.Frame(self, bg="#CAD8E2", highlightbackground="#A9BFCE", highlightthickness=1)
        frame_bot.place(x=20, y=505, width=940, height=75)

        self.lbl_tot_ingresos = tk.Label(frame_bot, text="Ingresos: RD$ 0.00", font=("sans", 11, "bold"), bg="#CAD8E2", fg="#1E293B")
        self.lbl_tot_ingresos.place(x=30, y=25)

        self.lbl_tot_costos = tk.Label(frame_bot, text="Costos/Gastos: RD$ 0.00", font=("sans", 11, "bold"), bg="#CAD8E2", fg="#1E293B")
        self.lbl_tot_costos.place(x=320, y=25)

        self.lbl_gran_ganancia = tk.Label(frame_bot, text="UTILIDAD NETA: RD$ 0.00", font=("sans", 13, "bold"), bg="#CAD8E2", fg="#166534")
        self.lbl_gran_ganancia.place(x=620, y=25)

    def cargar_datos(self):
        for r in self.tabla.get_children():
            self.tabla.delete(r)

        anio = self.cmb_anio.get()
        datos_meses = {i: {"ingresos": 0.0, "costos": 0.0, "gastos": 0.0} for i in range(1, 13)}

        try:
            ventas, gastos = ServicioReportes().ganancias_mes(anio)
            for tot, cst, fec in ventas:
                try:
                    m = int(fec.split("-")[1])
                    if 1 <= m <= 12:
                        datos_meses[m]["ingresos"] += float(tot or 0.0)
                        datos_meses[m]["costos"] += float(cst or 0.0)
                except Exception:
                    pass

            for mon, fec in gastos:
                try:
                    m = int(fec.split("-")[1])
                    if 1 <= m <= 12:
                        datos_meses[m]["gastos"] += float(mon or 0.0)
                except Exception:
                    pass
        except Exception as e:
            print("Error cargando ganancias por mes:", e)

        gran_ingresos = 0.0
        gran_costos = 0.0
        gran_gastos = 0.0

        for m in range(1, 13):
            mes_nom = self.meses_nombres[m - 1]
            ing = datos_meses[m]["ingresos"]
            cst = datos_meses[m]["costos"]
            gst = datos_meses[m]["gastos"]
            neta = ing - (cst + gst)
            margen = ((neta / ing) * 100) if ing > 0 else 0.0

            gran_ingresos += ing
            gran_costos += cst
            gran_gastos += gst

            self.tabla.insert("", tk.END, values=(
                f"  {mes_nom}",
                f"RD$ {ing:,.2f}",
                f"RD$ {cst:,.2f}",
                f"RD$ {gst:,.2f}",
                f"RD$ {neta:,.2f}",
                f"{margen:,.1f} %"
            ))

        gran_neta = gran_ingresos - (gran_costos + gran_gastos)
        self.lbl_tot_ingresos.config(text=f"Ingresos: RD$ {gran_ingresos:,.2f}")
        self.lbl_tot_costos.config(text=f"Costos + Gastos: RD$ {(gran_costos + gran_gastos):,.2f}")
        self.lbl_gran_ganancia.config(text=f"UTILIDAD NETA: RD$ {gran_neta:,.2f}")

    def exportar_csv(self):
        dest = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("Archivo CSV", "*.csv")],
            initialfile=f"Reporte_Ganancias_Por_Mes_{self.cmb_anio.get()}.csv"
        )
        if dest:
            try:
                with open(dest, mode="w", newline="", encoding="utf-8-sig") as f:
                    writer = csv.writer(f)
                    writer.writerow(["Mes", "Ingresos Ventas (RD$)", "Costo Mercancía (RD$)", "Gastos Operativos (RD$)", "Ganancia Neta (RD$)", "Margen (%)"])
                    for child in self.tabla.get_children():
                        writer.writerow(self.tabla.item(child, "values"))
                messagebox.showinfo("Exportación", f"Reporte exportado exitosamente a:\n{dest}")
            except Exception as e:
                messagebox.showerror("Error", f"Error exportando reporte: {e}")
