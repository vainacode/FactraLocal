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

class ReporteVentasTotales(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.title("Reporte ventas totales")
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
        self.filas_ventas = []

        self.widgets()
        self.generar_reporte()

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
            text="Reporte de ventas totales",
            font=("sans", 24, "bold"),
            bg="#C6D9E3",
            fg="#1E293B"
        )
        lbl_title.place(relx=0.5, y=25, anchor="center")

#============== 2. PANEL IZQUIERDO: FILTROS Y RESUMEN ==============================================#
        # Filtros
        frame_filtro = tk.Frame(self, bg="#DDE1E5", highlightbackground="#B8C4CE", highlightthickness=1)
        frame_filtro.place(x=15, y=60, width=355, height=135)

        # Desde
        lbl_d = tk.Label(frame_filtro, text="Desde:", font=("sans", 12, "bold"), bg="#DDE1E5", fg="#1E293B")
        lbl_d.place(x=15, y=12)

        self.ent_desde = ttk.Entry(frame_filtro, font=("sans", 11), justify="center")
        self.ent_desde.place(x=90, y=10, width=160, height=28)
        self.ent_desde.insert(0, datetime.datetime.now().strftime("%Y-%m-%d"))

        ruta_cal = self.rutas("icono/calendario.png")
        if os.path.exists(ruta_cal):
            self.images["cal_rvt"] = ImageTk.PhotoImage(Image.open(ruta_cal).resize((22, 22), Image.Resampling.LANCZOS))
            btn_cal1 = tk.Button(frame_filtro, image=self.images["cal_rvt"], bg="white", relief="solid", bd=1, cursor="hand2")
            btn_cal1.place(x=255, y=10, width=32, height=28)

        # Hasta
        lbl_h = tk.Label(frame_filtro, text="Hasta:", font=("sans", 12, "bold"), bg="#DDE1E5", fg="#1E293B")
        lbl_h.place(x=15, y=50)

        self.ent_hasta = ttk.Entry(frame_filtro, font=("sans", 11), justify="center")
        self.ent_hasta.place(x=90, y=48, width=160, height=28)
        self.ent_hasta.insert(0, datetime.datetime.now().strftime("%Y-%m-%d"))

        if "cal_rvt" in self.images:
            btn_cal2 = tk.Button(frame_filtro, image=self.images["cal_rvt"], bg="white", relief="solid", bd=1, cursor="hand2")
            btn_cal2.place(x=255, y=48, width=32, height=28)

        # Botón Generar
        ruta_filtro = self.rutas("icono/filtrar.png")
        if os.path.exists(ruta_filtro):
            self.images["filtro_rvt"] = ImageTk.PhotoImage(Image.open(ruta_filtro).resize((20, 20), Image.Resampling.LANCZOS))
            ico_f = self.images["filtro_rvt"]
        else:
            ico_f = None

        btn_gen = tk.Button(frame_filtro, text="  Generar", image=ico_f, compound=tk.LEFT, font=("sans", 10, "bold"), bg="#EBEFF2", fg="#1E293B", relief="raised", bd=2, cursor="hand2", command=self.generar_reporte)
        btn_gen.place(x=105, y=88, width=125, height=34)

        # Resumen Tabla Mini
        frame_res_mini = tk.Frame(self, bg="white", highlightbackground="#B8C4CE", highlightthickness=1)
        frame_res_mini.place(x=15, y=210, width=355, height=180)

        frame_th = tk.Frame(frame_res_mini, bg="#E0E6ED", height=30)
        frame_th.pack(fill="x")

        tk.Label(frame_th, text="Cantidad de facturas", font=("sans", 9, "bold"), bg="#E0E6ED", fg="#1E293B").place(x=20, y=5)
        tk.Label(frame_th, text="Total de Ventas", font=("sans", 9, "bold"), bg="#E0E6ED", fg="#1E293B").place(x=210, y=5)

        self.lbl_cant_fac = tk.Label(frame_res_mini, text="0", font=("sans", 10), bg="white", fg="#1E293B")
        self.lbl_cant_fac.place(x=65, y=45)

        self.lbl_tot_vt = tk.Label(frame_res_mini, text="$ 0.00", font=("sans", 10), bg="white", fg="#1E293B")
        self.lbl_tot_vt.place(x=225, y=45)

        # Nota al pie
        lbl_nota = tk.Label(
            self,
            text="El reporte de ventas totales equivale al total de\nlas ventas de los productos incluyendo costo y ganancia",
            font=("sans", 9, "italic"),
            bg="#C6D9E3",
            fg="#475569",
            justify="center"
        )
        lbl_nota.place(x=20, y=415)

        # Botón Exportar a Excel Verde
        ruta_ex = self.rutas("icono/excel.png")
        if os.path.exists(ruta_ex):
            self.images["ex_rvt_ico"] = ImageTk.PhotoImage(Image.open(ruta_ex).resize((22, 22), Image.Resampling.LANCZOS))
            ico_ex = self.images["ex_rvt_ico"]
        else:
            ico_ex = None

        btn_ex = tk.Button(self, text="  Exportar a Excel", image=ico_ex, compound=tk.LEFT, font=("sans", 11, "bold"), bg="#15803D", fg="white", relief="raised", bd=2, cursor="hand2", command=self.exportar_excel)
        btn_ex.place(x=85, y=485, width=200, height=44)

#============== 3. PANEL DERECHO: TABLA DE PRODUCTOS ===============================================#
        style = ttk.Style()
        style.configure("RVT.Treeview.Heading", font=("sans", 9, "bold"), background="#E0E6ED")
        style.configure("RVT.Treeview", font=("sans", 9), rowheight=24)

        cols = ("factura", "fecha", "cliente", "producto")
        self.tabla = ttk.Treeview(self, columns=cols, show="headings", style="RVT.Treeview")
        self.tabla.place(x=390, y=60, width=570, height=480)

        titulos = [
            ("factura", "Factura", 70),
            ("fecha", "Fecha", 100),
            ("cliente", "Cliente", 170),
            ("producto", "Producto", 215),
        ]

        for c, t, w in titulos:
            self.tabla.heading(c, text=t, anchor="center")
            self.tabla.column(c, width=w, anchor="center" if c in ("factura", "fecha") else "w")

        scroll_y = ttk.Scrollbar(self, orient="vertical", command=self.tabla.yview)
        self.tabla.configure(yscrollcommand=scroll_y.set)
        scroll_y.place(x=945, y=60, height=480)

    def generar_reporte(self):
        for r in self.tabla.get_children():
            self.tabla.delete(r)

        self.filas_ventas = []
        try:
            self.filas_ventas, total = ServicioReportes().ventas_totales(self.ent_desde.get().strip(), self.ent_hasta.get().strip())
            self.lbl_cant_fac.config(text=str(len({fila[0] for fila in self.filas_ventas})))
            self.lbl_tot_vt.config(text=f"$ {float(total or 0):,.2f}")
        except Exception as error:
            messagebox.showerror("Error", f"No se pudo generar el reporte: {error}")

        for f in self.filas_ventas:
            self.tabla.insert("", tk.END, values=f)

    def exportar_excel(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("Archivo CSV", "*.csv")], initialfile="Reporte_Ventas_Totales.csv")
        if file_path:
            try:
                with open(file_path, mode="w", newline="", encoding="utf-8-sig") as f:
                    w = csv.writer(f)
                    w.writerow(["Factura", "Fecha", "Cliente", "Producto"])
                    for row in self.filas_ventas:
                        w.writerow(row)
                messagebox.showinfo("Exportar", "Reporte de ventas totales exportado exitosamente.")
            except Exception as e:
                messagebox.showerror("Error", f"Error exportando: {e}")
