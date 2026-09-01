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

class ReporteGastosMes(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.title("Reporte de Gastos por Mes - La Casa de los Repuestos")
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
        lbl_title = tk.Label(
            self,
            text="REPORTE DE GASTOS OPERATIVOS POR MES",
            font=("sans", 20, "bold"),
            bg="#C6D9E3",
            fg="#1E293B"
        )
        lbl_title.place(relx=0.5, y=30, anchor="center")

        frame_top = tk.Frame(self, bg="#DDE1E5", highlightbackground="#B8C4CE", highlightthickness=1)
        frame_top.place(x=20, y=65, width=940, height=50)

        tk.Label(frame_top, text="Año:", font=("sans", 11, "bold"), bg="#DDE1E5", fg="#1E293B").place(x=15, y=12)
        anio_actual = datetime.datetime.now().year
        self.cmb_anio = ttk.Combobox(frame_top, values=[str(y) for y in range(anio_actual - 3, anio_actual + 2)], font=("sans", 11), state="readonly")
        self.cmb_anio.set(str(anio_actual))
        self.cmb_anio.place(x=60, y=10, width=110, height=30)
        self.cmb_anio.bind("<<ComboboxSelected>>", lambda e: self.cargar_datos())

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
        style.configure("RG.Treeview.Heading", font=("sans", 10, "bold"), background="#E0E6ED")
        style.configure("RG.Treeview", font=("sans", 9), rowheight=24)

        cols = ("mes", "cant_gastos", "total_gastos", "promedio")
        self.tabla = ttk.Treeview(self, columns=cols, show="headings", style="RG.Treeview")
        self.tabla.place(x=20, y=125, width=940, height=370)

        self.tabla.heading("mes", text="Mes", anchor="w")
        self.tabla.heading("cant_gastos", text="Cantidad de Registros", anchor="center")
        self.tabla.heading("total_gastos", text="Total Gastos (RD$)", anchor="e")
        self.tabla.heading("promedio", text="Gasto Promedio (RD$)", anchor="e")

        self.tabla.column("mes", width=250, anchor="w")
        self.tabla.column("cant_gastos", width=200, anchor="center")
        self.tabla.column("total_gastos", width=240, anchor="e")
        self.tabla.column("promedio", width=250, anchor="e")

        frame_bot = tk.Frame(self, bg="#CAD8E2", highlightbackground="#A9BFCE", highlightthickness=1)
        frame_bot.place(x=20, y=505, width=940, height=75)

        self.lbl_tot_registros = tk.Label(frame_bot, text="Registros de Gastos: 0", font=("sans", 11, "bold"), bg="#CAD8E2", fg="#1E293B")
        self.lbl_tot_registros.place(x=30, y=25)

        self.lbl_gran_total = tk.Label(frame_bot, text="TOTAL GASTOS ANUAL: RD$ 0.00", font=("sans", 13, "bold"), bg="#CAD8E2", fg="#DC2626")
        self.lbl_gran_total.place(x=540, y=25)

    def cargar_datos(self):
        for r in self.tabla.get_children():
            self.tabla.delete(r)

        anio = self.cmb_anio.get()
        datos_meses = {i: {"cantidad": 0, "total": 0.0} for i in range(1, 13)}

        try:
            for mon, fec in ServicioReportes().gastos_mes(anio):
                    try:
                        m = int(fec.split("-")[1])
                        if 1 <= m <= 12:
                            datos_meses[m]["cantidad"] += 1
                            datos_meses[m]["total"] += float(mon or 0.0)
                    except Exception:
                        pass
        except Exception as e:
            print("Error cargando gastos por mes:", e)

        gran_cant = 0
        gran_total = 0.0

        for m in range(1, 13):
            mes_nom = self.meses_nombres[m - 1]
            cnt = datos_meses[m]["cantidad"]
            tot = datos_meses[m]["total"]
            prom = (tot / cnt) if cnt > 0 else 0.0

            gran_cant += cnt
            gran_total += tot

            self.tabla.insert("", tk.END, values=(
                f"  {mes_nom}",
                str(cnt),
                f"RD$ {tot:,.2f}",
                f"RD$ {prom:,.2f}"
            ))

        self.lbl_tot_registros.config(text=f"Registros de Gastos: {gran_cant}")
        self.lbl_gran_total.config(text=f"TOTAL GASTOS ANUAL: RD$ {gran_total:,.2f}")

    def exportar_csv(self):
        dest = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("Archivo CSV", "*.csv")],
            initialfile=f"Reporte_Gastos_Por_Mes_{self.cmb_anio.get()}.csv"
        )
        if dest:
            try:
                with open(dest, mode="w", newline="", encoding="utf-8-sig") as f:
                    writer = csv.writer(f)
                    writer.writerow(["Mes", "Cantidad de Registros", "Total Gastos (RD$)", "Gasto Promedio (RD$)"])
                    for child in self.tabla.get_children():
                        writer.writerow(self.tabla.item(child, "values"))
                messagebox.showinfo("Exportación", f"Reporte exportado exitosamente a:\n{dest}")
            except Exception as e:
                messagebox.showerror("Error", f"Error exportando reporte: {e}")
