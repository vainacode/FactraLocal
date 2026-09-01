import csv
import datetime
import os
import db_conexion as sqlite3
import sys
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageTk
from window_utils import posicionar_ventana

class ReporteCajaUsuario(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.title("Reporte Caja por Usuario")
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
        self.registros = []

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
            text="Reporte de Caja por Usuario",
            font=("sans", 22, "bold"),
            bg="#C6D9E3",
            fg="#1E293B"
        )
        lbl_title.place(relx=0.5, y=28, anchor="center")

#============== 2. FILTRO DE FECHAS (IZQUIERDA) ====================================================#
        frame_filtro = tk.Frame(self, bg="#DDE1E5", highlightbackground="#B8C4CE", highlightthickness=1)
        frame_filtro.place(x=15, y=60, width=350, height=135)

        # Desde
        lbl_desde = tk.Label(frame_filtro, text="Desde:", font=("sans", 13, "bold"), bg="#DDE1E5", fg="#1E293B")
        lbl_desde.place(x=15, y=15)

        self.ent_desde = ttk.Entry(frame_filtro, font=("sans", 11), justify="center")
        self.ent_desde.place(x=95, y=15, width=155, height=28)
        self.ent_desde.insert(0, datetime.datetime.now().strftime("%Y-%m-%d"))

        ruta_cal = self.rutas("icono/calendario.png")
        if os.path.exists(ruta_cal):
            img_cal = Image.open(ruta_cal).resize((22, 22), Image.Resampling.LANCZOS)
            self.images["cal_caja"] = ImageTk.PhotoImage(img_cal)
            btn_cal1 = tk.Button(frame_filtro, image=self.images["cal_caja"], bg="white", relief="solid", bd=1, cursor="hand2", command=lambda: self.abrir_datepicker(self.ent_desde))
            btn_cal1.place(x=255, y=15, width=32, height=28)

        # Hasta
        lbl_hasta = tk.Label(frame_filtro, text="Hasta:", font=("sans", 13, "bold"), bg="#DDE1E5", fg="#1E293B")
        lbl_hasta.place(x=15, y=55)

        self.ent_hasta = ttk.Entry(frame_filtro, font=("sans", 11), justify="center")
        self.ent_hasta.place(x=95, y=55, width=155, height=28)
        self.ent_hasta.insert(0, datetime.datetime.now().strftime("%Y-%m-%d"))

        if "cal_caja" in self.images:
            btn_cal2 = tk.Button(frame_filtro, image=self.images["cal_caja"], bg="white", relief="solid", bd=1, cursor="hand2", command=lambda: self.abrir_datepicker(self.ent_hasta))
            btn_cal2.place(x=255, y=55, width=32, height=28)

        # Botón Generar
        ruta_filtro = self.rutas("icono/filtrar.png")
        if not os.path.exists(ruta_filtro):
            ruta_filtro = self.rutas("icono/filtro.png")

        if os.path.exists(ruta_filtro):
            img_f = Image.open(ruta_filtro).resize((20, 20), Image.Resampling.LANCZOS)
            self.images["filtro_btn"] = ImageTk.PhotoImage(img_f)
            ico_f = self.images["filtro_btn"]
        else:
            ico_f = None

        btn_generar = tk.Button(
            frame_filtro,
            text="  Generar",
            image=ico_f,
            compound=tk.LEFT,
            font=("sans", 10, "bold"),
            bg="#EBEFF2",
            fg="#1E293B",
            relief="raised",
            bd=2,
            cursor="hand2",
            command=self.generar_reporte
        )
        btn_generar.place(x=105, y=92, width=125, height=34)

#============== 3. RESUMEN DEL PERÍODO (DERECHA) ===================================================#
        frame_resumen = tk.LabelFrame(
            self,
            text="Resumen del Período",
            font=("sans", 10, "bold"),
            bg="#C6D9E3",
            fg="#1E293B",
            padx=10,
            pady=6
        )
        frame_resumen.place(x=380, y=60, width=580, height=95)

        # Fila 1: Ventas Contado, Ventas Crédito, Total General
        tk.Label(frame_resumen, text="Ventas Contado:", font=("sans", 8, "bold"), bg="#C6D9E3", fg="#475569").place(x=5, y=2)
        self.lbl_v_contado = tk.Label(frame_resumen, text="$ 0.00", font=("sans", 10, "bold"), bg="#C6D9E3", fg="#0284C7")
        self.lbl_v_contado.place(x=5, y=20)

        tk.Label(frame_resumen, text="Ventas Crédito:", font=("sans", 8, "bold"), bg="#C6D9E3", fg="#475569").place(x=200, y=2)
        self.lbl_v_credito = tk.Label(frame_resumen, text="$ 0.00", font=("sans", 10, "bold"), bg="#C6D9E3", fg="#9333EA")
        self.lbl_v_credito.place(x=200, y=20)

        tk.Label(frame_resumen, text="Total General:", font=("sans", 8, "bold"), bg="#C6D9E3", fg="#475569").place(x=400, y=2)
        self.lbl_v_total = tk.Label(frame_resumen, text="$ 0.00", font=("sans", 10, "bold"), bg="#C6D9E3", fg="#166534")
        self.lbl_v_total.place(x=400, y=20)

        # Fila 2: Abonos Crédito, Gastos, Efectivo en Caja
        tk.Label(frame_resumen, text="Abonos Crédito:", font=("sans", 8, "bold"), bg="#C6D9E3", fg="#475569").place(x=5, y=42)
        self.lbl_abonos = tk.Label(frame_resumen, text="$ 0.00", font=("sans", 10, "bold"), bg="#C6D9E3", fg="#0284C7")
        self.lbl_abonos.place(x=5, y=60)

        tk.Label(frame_resumen, text="Gastos:", font=("sans", 8, "bold"), bg="#C6D9E3", fg="#475569").place(x=200, y=42)
        self.lbl_gastos = tk.Label(frame_resumen, text="$ 0.00", font=("sans", 10, "bold"), bg="#C6D9E3", fg="#DC2626")
        self.lbl_gastos.place(x=200, y=60)

        tk.Label(frame_resumen, text="Efectivo en Caja:", font=("sans", 8, "bold"), bg="#C6D9E3", fg="#475569").place(x=400, y=42)
        self.lbl_efectivo = tk.Label(frame_resumen, text="$ 0.00", font=("sans", 10, "bold"), bg="#C6D9E3", fg="#0284C7")
        self.lbl_efectivo.place(x=400, y=60)

        # Nota al pie de resumen
        lbl_nota = tk.Label(
            self,
            text="Total Ventas = Ventas Contado + Ventas Crédito. Las filas en verde son cajas aún abiertas.",
            font=("sans", 9, "italic"),
            bg="#C6D9E3",
            fg="#475569"
        )
        lbl_nota.place(x=390, y=165)

#============== 4. TABLA ===========================================================================#
        style = ttk.Style()
        style.configure("Caja.Treeview.Heading", font=("sans", 8, "bold"), background="#E0E6ED")
        style.configure("Caja.Treeview", font=("sans", 9), rowheight=26)

        cols = ("hora_cierre", "monto_ini", "v_contado", "v_credito", "tot_ventas", "abonos", "gastos", "descuento", "efectivo_caja")
        self.tabla = ttk.Treeview(self, columns=cols, show="headings", style="Caja.Treeview")
        self.tabla.place(x=15, y=210, width=945, height=315)

        titulos = [
            ("hora_cierre", "Hora Cierre", 110),
            ("monto_ini", "Monto Inicial", 100),
            ("v_contado", "Ventas Contado", 105),
            ("v_credito", "Ventas Crédito", 105),
            ("tot_ventas", "Total Ventas", 105),
            ("abonos", "Abonos Crédito", 100),
            ("gastos", "Gastos", 90),
            ("descuento", "Descuento", 95),
            ("efectivo_caja", "Efectivo en Caja", 115),
        ]

        for c, t, w in titulos:
            self.tabla.heading(c, text=t, anchor="center")
            self.tabla.column(c, width=w, anchor="center")

        scroll_y = ttk.Scrollbar(self, orient="vertical", command=self.tabla.yview)
        self.tabla.configure(yscrollcommand=scroll_y.set)
        scroll_y.place(x=960, y=210, height=315)

#============== 5. BOTÓN EXPORTAR ==================================================================#
        ruta_ex = self.rutas("icono/excel.png")
        if os.path.exists(ruta_ex):
            self.images["excel_caja"] = ImageTk.PhotoImage(Image.open(ruta_ex).resize((22, 22), Image.Resampling.LANCZOS))
            ico_ex = self.images["excel_caja"]
        else:
            ico_ex = None

        btn_ex = tk.Button(
            self,
            text="  Exportar a Excel",
            image=ico_ex,
            compound=tk.LEFT,
            font=("sans", 11, "bold"),
            bg="#EBEFF2",
            fg="#1E293B",
            relief="raised",
            bd=2,
            cursor="hand2",
            command=self.exportar_excel
        )
        btn_ex.place(relx=0.5, y=560, width=180, height=40, anchor="center")

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
            self.images["save_dp"] = ImageTk.PhotoImage(Image.open(ruta_g).resize((20, 20), Image.Resampling.LANCZOS))
            ico_g = self.images["save_dp"]
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

        # Consultar exclusivamente la sesión real; nunca mostrar cifras de
        # demostración si la base no tiene movimientos.
        total_ventas = 0.0
        v_contado = 0.0
        v_credito = 0.0
        monto_ini = 0.0
        abonos = 0.0
        gastos = 0.0
        descuento = 0.0
        efectivo_caja = 0.0
        estado = "Sin caja"
        try:
            with sqlite3.connect(self.db_name) as conn:
                cur = conn.cursor()
                cur.execute("SELECT id, monto_inicial, estado, COALESCE(monto_contado, 0), COALESCE(diferencia_caja, 0) FROM cajas ORDER BY id DESC LIMIT 1")
                caja = cur.fetchone()
                if caja:
                    caja_id, monto_ini, estado, contado, diferencia = caja
                    cur.execute("SELECT COALESCE(SUM(total), 0) FROM ventas WHERE caja_id = ?", (caja_id,))
                    v_contado = float(cur.fetchone()[0] or 0)
                    cur.execute("SELECT COALESCE(SUM(total), 0) FROM ventas WHERE caja_id = ? AND COALESCE(medio_pago, 'Efectivo') = 'Efectivo'", (caja_id,))
                    efectivo_ventas = float(cur.fetchone()[0] or 0)
                    cur.execute("SELECT COALESCE(SUM(total), 0) FROM facturas_pendientes WHERE caja_id = ? AND estado IN ('Crédito', 'Pagada')", (caja_id,))
                    v_credito = float(cur.fetchone()[0] or 0)
                    total_ventas = v_contado + v_credito
                    cur.execute("SELECT COALESCE(SUM(monto), 0) FROM abonos_credito WHERE caja_id = ?", (caja_id,))
                    abonos = float(cur.fetchone()[0] or 0)
                    cur.execute("SELECT COALESCE(SUM(monto), 0) FROM abonos_credito WHERE caja_id = ? AND COALESCE(metodo_pago, 'Efectivo') = 'Efectivo'", (caja_id,))
                    abonos_efectivo = float(cur.fetchone()[0] or 0)
                    cur.execute("SELECT COALESCE(SUM(CASE WHEN tipo='INGRESO' THEN monto ELSE 0 END), 0), COALESCE(SUM(CASE WHEN tipo='EGRESO' THEN monto ELSE 0 END), 0) FROM movimientos_caja WHERE caja_id = ?", (caja_id,))
                    ingresos, egresos = cur.fetchone()
                    cur.execute("SELECT COALESCE(SUM(monto), 0) FROM gastos WHERE caja_id = ? AND COALESCE(origen, 'Caja') = 'Caja' AND COALESCE(anulado, FALSE) = FALSE", (caja_id,))
                    gastos = float(cur.fetchone()[0] or 0)
                    egresos = float(egresos or 0) + gastos
                    efectivo_caja = float(monto_ini or 0) + efectivo_ventas + abonos_efectivo + float(ingresos or 0) - float(egresos or 0)
                    if str(estado).lower() == "cerrada":
                        efectivo_caja = float(contado or 0)
        except Exception:
            self.registros = []
            self.lbl_v_contado.config(text="$ 0.00")
            self.lbl_v_credito.config(text="$ 0.00")
            self.lbl_v_total.config(text="$ 0.00")
            self.lbl_abonos.config(text="$ 0.00")
            self.lbl_gastos.config(text="$ 0.00")
            self.lbl_efectivo.config(text="$ 0.00")
            return

        self.lbl_v_contado.config(text=f"$ {v_contado:,.2f}")
        self.lbl_v_credito.config(text=f"$ {v_credito:,.2f}")
        self.lbl_v_total.config(text=f"$ {total_ventas:,.2f}")
        self.lbl_abonos.config(text=f"$ {abonos:,.2f}")
        self.lbl_gastos.config(text=f"$ {gastos:,.2f}")
        self.lbl_efectivo.config(text=f"$ {efectivo_caja:,.2f}")

        row = (
            estado,
            f"$ {monto_ini:,.2f}",
            f"$ {v_contado:,.2f}",
            f"$ {v_credito:,.2f}",
            f"$ {total_ventas:,.2f}",
            f"$ {abonos:,.2f}",
            f"$ {gastos:,.2f}",
            f"$ {descuento:,.2f}",
            f"$ {efectivo_caja:,.2f}"
        )
        self.registros = [row]
        item_id = self.tabla.insert("", tk.END, values=row)
        self.tabla.tag_configure("abierta", background="#38BDF8", foreground="#FFFFFF")
        self.tabla.item(item_id, tags=("abierta",))

    def exportar_excel(self):
        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("Archivo CSV", "*.csv")],
            initialfile="Reporte_Caja_Usuario.csv"
        )
        if file_path:
            try:
                with open(file_path, mode="w", newline="", encoding="utf-8-sig") as f:
                    w = csv.writer(f)
                    w.writerow(["Hora Cierre", "Monto Inicial", "Ventas Contado", "Ventas Crédito", "Total Ventas", "Abonos Crédito", "Gastos", "Descuento", "Efectivo en Caja"])
                    for r in self.registros:
                        w.writerow(r)
                messagebox.showinfo("Exportar", "Reporte de caja exportado exitosamente.")
            except Exception as e:
                messagebox.showerror("Error", f"Error al exportar: {e}")
