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

class ReporteProductosRentables(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.title("Reporte de Productos Más Rentables")
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
        self.filas_rentabilidad = []

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
            text="Productos Más Rentables (Por Margen de Ganancia)",
            font=("sans", 20, "bold"),
            bg="#C6D9E3",
            fg="#1E293B"
        )
        lbl_title.place(relx=0.5, y=25, anchor="center")

#============== 2. BARRA DE FILTROS ================================================================#
        # Desde
        lbl_d = tk.Label(self, text="Desde:", font=("sans", 11, "bold"), bg="#C6D9E3", fg="#1E293B")
        lbl_d.place(x=15, y=55)

        self.ent_desde = ttk.Entry(self, font=("sans", 11), justify="center")
        self.ent_desde.place(x=85, y=55, width=145, height=28)
        hoy = datetime.date.today()
        self.ent_desde.insert(0, hoy.replace(day=1).strftime("%Y-%m-%d"))

        ruta_cal = self.rutas("icono/calendario.png")
        if os.path.exists(ruta_cal):
            img_cal = Image.open(ruta_cal).resize((20, 20), Image.Resampling.LANCZOS)
            self.images["cal_rent"] = ImageTk.PhotoImage(img_cal)
            btn_cal1 = tk.Button(self, image=self.images["cal_rent"], bg="white", relief="solid", bd=1, cursor="hand2", command=lambda: self.abrir_datepicker(self.ent_desde))
            btn_cal1.place(x=235, y=55, width=30, height=28)

        # Hasta
        lbl_h = tk.Label(self, text="Hasta:", font=("sans", 11, "bold"), bg="#C6D9E3", fg="#1E293B")
        lbl_h.place(x=280, y=55)

        self.ent_hasta = ttk.Entry(self, font=("sans", 11), justify="center")
        self.ent_hasta.place(x=345, y=55, width=145, height=28)
        self.ent_hasta.insert(0, datetime.datetime.now().strftime("%Y-%m-%d"))

        if "cal_rent" in self.images:
            btn_cal2 = tk.Button(self, image=self.images["cal_rent"], bg="white", relief="solid", bd=1, cursor="hand2", command=lambda: self.abrir_datepicker(self.ent_hasta))
            btn_cal2.place(x=495, y=55, width=30, height=28)

        # Botón Filtrar
        ruta_f = self.rutas("icono/filtrar.png")
        if os.path.exists(ruta_f):
            img_f = Image.open(ruta_f).resize((20, 20), Image.Resampling.LANCZOS)
            self.images["filtro_r"] = ImageTk.PhotoImage(img_f)
            ico_f = self.images["filtro_r"]
        else:
            ico_f = None

        btn_f = tk.Button(self, text="  Filtrar", image=ico_f, compound=tk.LEFT, font=("sans", 10, "bold"), bg="#EBEFF2", fg="#1E293B", relief="raised", bd=2, cursor="hand2", command=self.generar_reporte)
        btn_f.place(x=550, y=54, width=105, height=30)

        # Botón Exportar
        ruta_ex = self.rutas("icono/excel.png")
        if os.path.exists(ruta_ex):
            self.images["excel_r"] = ImageTk.PhotoImage(Image.open(ruta_ex).resize((20, 20), Image.Resampling.LANCZOS))
            ico_ex = self.images["excel_r"]
        else:
            ico_ex = None

        btn_ex = tk.Button(self, text="  Exportar", image=ico_ex, compound=tk.LEFT, font=("sans", 10, "bold"), bg="#EBEFF2", fg="#1E293B", relief="raised", bd=2, cursor="hand2", command=self.exportar_excel)
        btn_ex.place(x=665, y=54, width=115, height=30)

        # Buscar producto
        lbl_b = tk.Label(self, text="Buscar producto:", font=("sans", 10, "bold"), bg="#C6D9E3", fg="#1E293B")
        lbl_b.place(x=15, y=95)

        self.ent_buscar = ttk.Entry(self, font=("sans", 10))
        self.ent_buscar.place(x=150, y=93, width=250, height=26)
        self.ent_buscar.bind("<KeyRelease>", lambda e: self.filtrar_tabla())

#============== 3. RESUMEN DEL PERÍODO =============================================================#
        frame_res = tk.LabelFrame(self, text="Resumen del Período", font=("sans", 10, "bold"), bg="#C6D9E3", fg="#1E293B", padx=10, pady=6)
        frame_res.place(x=15, y=130, width=945, height=105)

        # Métricas Fila 1
        tk.Label(frame_res, text="Total Ingresos:", font=("sans", 9, "bold"), bg="#C6D9E3", fg="#475569").place(x=15, y=2)
        self.lbl_tot_ingresos = tk.Label(frame_res, text="$ 0.00", font=("sans", 10, "bold"), bg="#C6D9E3", fg="#166534")
        self.lbl_tot_ingresos.place(x=15, y=20)

        tk.Label(frame_res, text="Total Costos:", font=("sans", 9, "bold"), bg="#C6D9E3", fg="#475569").place(x=250, y=2)
        self.lbl_tot_costos = tk.Label(frame_res, text="$ 0.00", font=("sans", 10, "bold"), bg="#C6D9E3", fg="#DC2626")
        self.lbl_tot_costos.place(x=250, y=20)

        tk.Label(frame_res, text="Ganancia Total:", font=("sans", 9, "bold"), bg="#C6D9E3", fg="#475569").place(x=490, y=2)
        self.lbl_gan_total = tk.Label(frame_res, text="$ 0.00", font=("sans", 10, "bold"), bg="#C6D9E3", fg="#166534")
        self.lbl_gan_total.place(x=490, y=20)

        tk.Label(frame_res, text="Margen Promedio:", font=("sans", 9, "bold"), bg="#C6D9E3", fg="#475569").place(x=720, y=2)
        self.lbl_margen_prom = tk.Label(frame_res, text="0.0%", font=("sans", 10, "bold"), bg="#C6D9E3", fg="#EA580C")
        self.lbl_margen_prom.place(x=720, y=20)

        # Métricas Fila 2
        tk.Label(frame_res, text="Producto Más Rentable:", font=("sans", 9, "bold"), bg="#C6D9E3", fg="#475569").place(x=15, y=46)
        self.lbl_mas_rentable = tk.Label(frame_res, text="Sin datos", font=("sans", 9, "bold"), bg="#C6D9E3", fg="#166534")
        self.lbl_mas_rentable.place(x=15, y=63)

        tk.Label(frame_res, text="Menor Ganancia:", font=("sans", 9, "bold"), bg="#C6D9E3", fg="#475569").place(x=490, y=46)
        self.lbl_menor_ganancia = tk.Label(frame_res, text="Sin datos", font=("sans", 9, "bold"), bg="#C6D9E3", fg="#7C3AED")
        self.lbl_menor_ganancia.place(x=490, y=63)

#============== 4. TABLA ===========================================================================#
        style = ttk.Style()
        style.configure("Rent.Treeview.Heading", font=("sans", 8, "bold"), background="#E0E6ED")
        style.configure("Rent.Treeview", font=("sans", 9), rowheight=24)

        cols = ("num", "producto", "cant", "ingresos", "costo_tot", "ganancia", "margen")
        self.tabla = ttk.Treeview(self, columns=cols, show="headings", style="Rent.Treeview")
        self.tabla.place(x=15, y=245, width=945, height=335)

        titulos = [
            ("num", "#", 40),
            ("producto", "Producto", 330),
            ("cant", "Cant. Vendida", 90),
            ("ingresos", "Ingresos", 120),
            ("costo_tot", "Costo Total", 120),
            ("ganancia", "Ganancia", 120),
            ("margen", "Margen %", 100),
        ]

        for c, t, w in titulos:
            self.tabla.heading(c, text=t, anchor="center")
            self.tabla.column(c, width=w, anchor="center" if c in ("num", "cant", "margen") else "w" if c == "producto" else "e")

        scroll_y = ttk.Scrollbar(self, orient="vertical", command=self.tabla.yview)
        self.tabla.configure(yscrollcommand=scroll_y.set)
        scroll_y.place(x=960, y=245, height=335)

    def abrir_datepicker(self, target_entry):
        dialog = tk.Toplevel(self)
        dialog.title("Seleccionar fecha")
        posicionar_ventana(dialog, 280, 140, self)
        dialog.resizable(False, False)
        dialog.configure(bg="#C6D9E3")
        dialog.transient(self)
        dialog.grab_set()

        ent_f = ttk.Entry(dialog, font=("sans", 13), justify="center")
        ent_f.insert(0, target_entry.get().strip() or datetime.datetime.now().strftime("%Y-%m-%d"))
        ent_f.pack(pady=18, ipady=4)

        ruta_g = self.rutas("icono/guardar.png")
        if os.path.exists(ruta_g):
            self.images["save_dp_r"] = ImageTk.PhotoImage(Image.open(ruta_g).resize((20, 20), Image.Resampling.LANCZOS))
            ico_g = self.images["save_dp_r"]
        else:
            ico_g = None

        def aplicar():
            target_entry.delete(0, tk.END)
            target_entry.insert(0, ent_f.get().strip())
            dialog.destroy()

        btn_sel = tk.Button(dialog, text="  Seleccionar", image=ico_g, compound=tk.LEFT, font=("sans", 11, "bold"), bg="#EBEFF2", fg="#1E293B", relief="raised", bd=2, cursor="hand2", command=aplicar)
        btn_sel.pack()

    def generar_reporte(self):
        for r in self.tabla.get_children():
            self.tabla.delete(r)

        self.filas_rentabilidad = []
        try:
            filas = ServicioReportes().rentabilidad(self.ent_desde.get().strip(), self.ent_hasta.get().strip())
            for posicion, (producto, cantidad, ingresos, costos, ganancia) in enumerate(filas, start=1):
                ingresos = float(ingresos or 0)
                costos = float(costos or 0)
                ganancia = float(ganancia or 0)
                margen = (ganancia / ingresos * 100) if ingresos else 0
                self.filas_rentabilidad.append((posicion, producto, int(cantidad or 0),
                    f"$ {ingresos:,.2f}", f"$ {costos:,.2f}", f"$ {ganancia:,.2f}", f"{margen:.1f}%"))
            total_ingresos = sum(float(f[3].replace("$ ", "").replace(",", "")) for f in self.filas_rentabilidad)
            total_costos = sum(float(f[4].replace("$ ", "").replace(",", "")) for f in self.filas_rentabilidad)
            ganancia_total = total_ingresos - total_costos
            self.lbl_tot_ingresos.config(text=f"$ {total_ingresos:,.2f}")
            self.lbl_tot_costos.config(text=f"$ {total_costos:,.2f}")
            self.lbl_gan_total.config(text=f"$ {ganancia_total:,.2f}")
            self.lbl_margen_prom.config(text=f"{(ganancia_total / total_ingresos * 100) if total_ingresos else 0:.1f}%")
            if self.filas_rentabilidad:
                mejor = self.filas_rentabilidad[0]
                peor = min(self.filas_rentabilidad, key=lambda fila: float(fila[5].replace("$ ", "").replace(",", "")))
                self.lbl_mas_rentable.config(text=f"{mejor[1]} ({mejor[5]})")
                self.lbl_menor_ganancia.config(text=f"{peor[1]} ({peor[5]})")
        except Exception as error:
            messagebox.showerror("Error", f"No se pudo generar el reporte: {error}")

        self.tabla.tag_configure("top1", background="#DCFCE7")
        self.tabla.tag_configure("top2", background="#DBEAFE")
        self.tabla.tag_configure("top3", background="#FEF9C3")

        for f in self.filas_rentabilidad:
            tag = "top1" if f[0] == 1 else "top2" if f[0] == 2 else "top3" if f[0] == 3 else ""
            self.tabla.insert("", tk.END, values=f, tags=(tag,))

    def filtrar_tabla(self):
        q = self.ent_buscar.get().strip().lower()
        for r in self.tabla.get_children():
            self.tabla.delete(r)

        for f in self.filas_rentabilidad:
            if not q or q in f[1].lower():
                tag = "top1" if f[0] == 1 else "top2" if f[0] == 2 else "top3" if f[0] == 3 else ""
                self.tabla.insert("", tk.END, values=f, tags=(tag,))

    def exportar_excel(self):
        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("Archivo CSV", "*.csv")],
            initialfile="Reporte_Productos_Rentables.csv"
        )
        if file_path:
            try:
                with open(file_path, mode="w", newline="", encoding="utf-8-sig") as f:
                    w = csv.writer(f)
                    w.writerow(["#", "Producto", "Cant. Vendida", "Ingresos", "Costo Total", "Ganancia", "Margen %"])
                    for r in self.filas_rentabilidad:
                        w.writerow(r)
                messagebox.showinfo("Exportar", "Reporte de rentabilidad exportado exitosamente.")
            except Exception as e:
                messagebox.showerror("Error", f"Error al exportar: {e}")
