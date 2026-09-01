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

class ReporteCuentasCobrar(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.title("Reporte de Cuentas por Cobrar")
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
            text="REPORTE DE CUENTAS POR COBRAR",
            font=("sans", 20, "bold"),
            bg="#C6D9E3",
            fg="#1E293B"
        )
        lbl_title.place(relx=0.5, y=25, anchor="center")

#============== 2. BARRA DE FILTROS ================================================================#
        frame_filtros = tk.LabelFrame(
            self,
            text="Filtros",
            font=("sans", 11, "bold"),
            bg="#C6D9E3",
            fg="#1E293B",
            padx=10,
            pady=4
        )
        frame_filtros.place(x=15, y=45, width=950, height=80)

        # Desde
        lbl_d = tk.Label(frame_filtros, text="Desde:", font=("sans", 10, "bold"), bg="#C6D9E3", fg="#1E293B")
        lbl_d.place(x=5, y=10)

        self.ent_desde = ttk.Entry(frame_filtros, font=("sans", 10), justify="center")
        self.ent_desde.place(x=60, y=8, width=115, height=28)
        self.ent_desde.insert(0, datetime.datetime.now().replace(day=1).strftime("%Y-%m-%d"))

        ruta_cal = self.rutas("icono/calendario.png")
        if os.path.exists(ruta_cal):
            self.images["cal_rcc"] = ImageTk.PhotoImage(Image.open(ruta_cal).resize((20, 20), Image.Resampling.LANCZOS))
            btn_c1 = tk.Button(frame_filtros, image=self.images["cal_rcc"], bg="white", relief="solid", bd=1, cursor="hand2", command=lambda: self.abrir_dp(self.ent_desde))
            btn_c1.place(x=180, y=8, width=28, height=28)

        # Hasta
        lbl_h = tk.Label(frame_filtros, text="Hasta:", font=("sans", 10, "bold"), bg="#C6D9E3", fg="#1E293B")
        lbl_h.place(x=220, y=10)

        self.ent_hasta = ttk.Entry(frame_filtros, font=("sans", 10), justify="center")
        self.ent_hasta.place(x=275, y=8, width=115, height=28)
        self.ent_hasta.insert(0, datetime.datetime.now().strftime("%Y-%m-%d"))

        if "cal_rcc" in self.images:
            btn_c2 = tk.Button(frame_filtros, image=self.images["cal_rcc"], bg="white", relief="solid", bd=1, cursor="hand2", command=lambda: self.abrir_dp(self.ent_hasta))
            btn_c2.place(x=395, y=8, width=28, height=28)

        # Estado
        lbl_est = tk.Label(frame_filtros, text="Estado:", font=("sans", 10, "bold"), bg="#C6D9E3", fg="#1E293B")
        lbl_est.place(x=435, y=10)

        self.cmb_estado = ttk.Combobox(frame_filtros, values=["Todos", "Al Día", "Vencidos", "Vencen Hoy"], font=("sans", 10), state="readonly")
        self.cmb_estado.current(0)
        self.cmb_estado.place(x=495, y=8, width=125, height=28)

        # Botón Generar Reporte
        ruta_rep = self.rutas("icono/reporte1.png")
        if not os.path.exists(ruta_rep):
            ruta_rep = self.rutas("icono/reporte.png")

        if os.path.exists(ruta_rep):
            self.images["rep_rcc_ico"] = ImageTk.PhotoImage(Image.open(ruta_rep).resize((20, 20), Image.Resampling.LANCZOS))
            ico_r = self.images["rep_rcc_ico"]
        else:
            ico_r = None

        btn_gen = tk.Button(frame_filtros, text="  Generar Reporte", image=ico_r, compound=tk.LEFT, font=("sans", 10, "bold"), bg="#22C55E", fg="white", relief="raised", bd=2, cursor="hand2", command=self.generar_reporte)
        btn_gen.place(x=635, y=5, width=155, height=34)

        # Botón Exportar Excel
        ruta_ex = self.rutas("icono/excel.png")
        if os.path.exists(ruta_ex):
            self.images["ex_rcc_ico"] = ImageTk.PhotoImage(Image.open(ruta_ex).resize((20, 20), Image.Resampling.LANCZOS))
            ico_ex = self.images["ex_rcc_ico"]
        else:
            ico_ex = None

        btn_ex = tk.Button(frame_filtros, text="  Exportar Excel", image=ico_ex, compound=tk.LEFT, font=("sans", 10, "bold"), bg="#15803D", fg="white", relief="raised", bd=2, cursor="hand2", command=self.exportar_excel)
        btn_ex.place(x=798, y=5, width=135, height=34)

#============== 3. RESUMEN GENERAL (IZQUIERDA) =====================================================#
        frame_res = tk.LabelFrame(
            self,
            text="Resumen General",
            font=("sans", 11, "bold"),
            bg="#C6D9E3",
            fg="#1E293B",
            padx=12,
            pady=8
        )
        frame_res.place(x=15, y=130, width=470, height=215)

        tk.Label(frame_res, text="Total Créditos Pendientes:", font=("sans", 10, "bold"), bg="#C6D9E3", fg="#1E293B").place(x=10, y=5)
        self.lbl_tot_pend = tk.Label(frame_res, text="0", font=("sans", 10, "bold"), bg="#C6D9E3", fg="#1E293B")
        self.lbl_tot_pend.place(x=400, y=5)

        tk.Label(frame_res, text="Monto Total por Cobrar:", font=("sans", 10, "bold"), bg="#C6D9E3", fg="#1E293B").place(x=10, y=30)
        self.lbl_tot_cobrar = tk.Label(frame_res, text="$ 0.00", font=("sans", 10, "bold"), bg="#C6D9E3", fg="#1E293B")
        self.lbl_tot_cobrar.place(x=380, y=30)

        # Estados con colores
        self.lbl_venc_cnt = tk.Label(frame_res, text="🔴  Vencidos (0):", font=("sans", 9, "bold"), bg="#C6D9E3", fg="#DC2626")
        self.lbl_venc_cnt.place(x=15, y=60)
        self.lbl_venc_monto = tk.Label(frame_res, text="$ 0.00", font=("sans", 9, "bold"), bg="#C6D9E3", fg="#DC2626")
        self.lbl_venc_monto.place(x=380, y=60)

        self.lbl_vhoy_cnt = tk.Label(frame_res, text="🟠  Vencen Hoy (0):", font=("sans", 9, "bold"), bg="#C6D9E3", fg="#EA580C")
        self.lbl_vhoy_cnt.place(x=15, y=85)
        self.lbl_vhoy_monto = tk.Label(frame_res, text="$ 0.00", font=("sans", 9, "bold"), bg="#C6D9E3", fg="#EA580C")
        self.lbl_vhoy_monto.place(x=380, y=85)

        self.lbl_prox_cnt = tk.Label(frame_res, text="🟡  Próximos 1-7 días (0):", font=("sans", 9, "bold"), bg="#C6D9E3", fg="#CA8A04")
        self.lbl_prox_cnt.place(x=15, y=110)
        self.lbl_prox_monto = tk.Label(frame_res, text="$ 0.00", font=("sans", 9, "bold"), bg="#C6D9E3", fg="#CA8A04")
        self.lbl_prox_monto.place(x=380, y=110)

        self.lbl_aldia_cnt = tk.Label(frame_res, text="🟢  Al Día >7 días (0):", font=("sans", 9, "bold"), bg="#C6D9E3", fg="#16A34A")
        self.lbl_aldia_cnt.place(x=15, y=135)
        self.lbl_aldia_monto = tk.Label(frame_res, text="$ 0.00", font=("sans", 9, "bold"), bg="#C6D9E3", fg="#16A34A")
        self.lbl_aldia_monto.place(x=380, y=135)

        tk.Label(frame_res, text="Total Abonos Recibidos:", font=("sans", 9, "bold"), bg="#C6D9E3", fg="#0284C7").place(x=10, y=165)
        self.lbl_abonos_monto = tk.Label(frame_res, text="$ 0.00", font=("sans", 9, "bold"), bg="#C6D9E3", fg="#0284C7")
        self.lbl_abonos_monto.place(x=380, y=165)

#============== 4. TOP 5 CLIENTES CON MAYOR DEUDA (DERECHA) ========================================#
        frame_top = tk.LabelFrame(
            self,
            text="Top 5 Clientes con Mayor Deuda",
            font=("sans", 11, "bold"),
            bg="#C6D9E3",
            fg="#1E293B",
            padx=8,
            pady=6
        )
        frame_top.place(x=500, y=130, width=465, height=215)

        style = ttk.Style()
        style.configure("TopC.Treeview.Heading", font=("sans", 9, "bold"), background="#E0E6ED")
        style.configure("TopC.Treeview", font=("sans", 9), rowheight=24)

        self.tabla_top = ttk.Treeview(frame_top, columns=("cliente", "deuda"), show="headings", style="TopC.Treeview")
        self.tabla_top.place(x=5, y=5, width=440, height=175)

        self.tabla_top.heading("cliente", text="Cliente", anchor="center")
        self.tabla_top.heading("deuda", text="Deuda Total", anchor="center")

        self.tabla_top.column("cliente", width=280, anchor="w")
        self.tabla_top.column("deuda", width=140, anchor="e")

#============== 5. DETALLE DE CRÉDITOS (INFERIOR) ===================================================#
        frame_det = tk.LabelFrame(
            self,
            text="Detalle de Créditos",
            font=("sans", 11, "bold"),
            bg="#C6D9E3",
            fg="#1E293B",
            padx=8,
            pady=6
        )
        frame_det.place(x=15, y=350, width=950, height=235)

        cols = ("fact", "cliente", "saldo", "dias", "estado")
        self.tabla_det = ttk.Treeview(frame_det, columns=cols, show="headings", style="TopC.Treeview")
        self.tabla_det.place(x=5, y=5, width=915, height=195)

        titulos = [
            ("fact", "Fact.", 80),
            ("cliente", "Cliente", 340),
            ("saldo", "Saldo", 150),
            ("dias", "Días Rest.", 140),
            ("estado", "Estado", 180),
        ]

        for c, t, w in titulos:
            self.tabla_det.heading(c, text=t, anchor="center")
            self.tabla_det.column(c, width=w, anchor="center" if c in ("fact", "dias", "estado") else "w" if c == "cliente" else "e")

        scroll_y = ttk.Scrollbar(frame_det, orient="vertical", command=self.tabla_det.yview)
        self.tabla_det.configure(yscrollcommand=scroll_y.set)
        scroll_y.place(x=922, y=5, height=195)

    def abrir_dp(self, target_entry):
        import calendar

        try:
            actual = datetime.datetime.strptime(target_entry.get().strip(), "%Y-%m-%d")
        except Exception:
            actual = datetime.datetime.now()

        estado = {"anio": actual.year, "mes": actual.month}

        dialog = tk.Toplevel(self)
        dialog.title("Seleccionar Fecha")
        posicionar_ventana(dialog, 260, 260, self)
        dialog.resizable(False, False)
        dialog.configure(bg="#C6D9E3")
        dialog.transient(self)
        dialog.grab_set()

        frame_nav = tk.Frame(dialog, bg="#C6D9E3")
        frame_nav.pack(pady=5)

        lbl_mes = tk.Label(frame_nav, text="", font=("sans", 11, "bold"), bg="#C6D9E3", fg="#1E293B", width=16, anchor="center")
        frame_dias = tk.Frame(dialog, bg="#C6D9E3")
        frame_dias.pack(pady=5)

        def dibujar():
            for w in frame_dias.winfo_children():
                w.destroy()
            lbl_mes.config(text=f"{calendar.month_name[estado['mes']].capitalize()} {estado['anio']}")
            for i, d in enumerate(["Lu", "Ma", "Mi", "Ju", "Vi", "Sa", "Do"]):
                tk.Label(frame_dias, text=d, font=("sans", 8, "bold"), bg="#C6D9E3", fg="#334155", width=3).grid(row=0, column=i)

            cal = calendar.Calendar(firstweekday=0)
            fila = 1
            for semana in cal.monthdayscalendar(estado["anio"], estado["mes"]):
                for i, dia in enumerate(semana):
                    if dia == 0:
                        tk.Label(frame_dias, text="", bg="#C6D9E3", width=3).grid(row=fila, column=i)
                    else:
                        tk.Button(
                            frame_dias, text=str(dia), width=3, font=("sans", 8),
                            command=lambda d=dia: seleccionar(d)
                        ).grid(row=fila, column=i, padx=1, pady=1)
                fila += 1

        def seleccionar(dia):
            fecha = f"{estado['anio']}-{estado['mes']:02d}-{dia:02d}"
            target_entry.delete(0, tk.END)
            target_entry.insert(0, fecha)
            dialog.destroy()

        def cambiar_mes(delta):
            m = estado["mes"] + delta
            a = estado["anio"]
            if m > 12:
                m, a = 1, a + 1
            elif m < 1:
                m, a = 12, a - 1
            estado["mes"], estado["anio"] = m, a
            dibujar()

        tk.Button(frame_nav, text="◀", command=lambda: cambiar_mes(-1), font=("sans", 9, "bold")).pack(side="left", padx=5)
        lbl_mes.pack(side="left")
        tk.Button(frame_nav, text="▶", command=lambda: cambiar_mes(1), font=("sans", 9, "bold")).pack(side="left", padx=5)

        dibujar()

    def generar_reporte(self):
        for r in self.tabla_top.get_children():
            self.tabla_top.delete(r)
        for r in self.tabla_det.get_children():
            self.tabla_det.delete(r)

        desde = self.ent_desde.get().strip()
        hasta = self.ent_hasta.get().strip()
        filtro_estado = self.cmb_estado.get()

        creditos = []
        deuda_por_cliente = {}
        total_abonos = 0.0
        try:
            filas, total_abonos, abonos = ServicioReportes().cuentas_cobrar_reporte()
            for factura, cliente, total, fecha_venta in filas:
                    if desde and fecha_venta < desde:
                        continue
                    if hasta and fecha_venta > hasta:
                        continue

                    abonado = abonos.get(factura, 0.0)
                    saldo = total - abonado
                    if saldo <= 0.01:
                        continue

                    try:
                        f_venta = datetime.datetime.strptime(fecha_venta, "%Y-%m-%d")
                        dias_rest = 30 - (datetime.datetime.now() - f_venta).days
                    except Exception:
                        dias_rest = 30

                    if dias_rest < 0:
                        estado_c = "Vencidos"
                    elif dias_rest == 0:
                        estado_c = "Vencen Hoy"
                    elif dias_rest <= 7:
                        estado_c = "Próximos 1-7 días"
                    else:
                        estado_c = "Al Día"

                    if filtro_estado != "Todos" and filtro_estado != estado_c:
                        continue

                    creditos.append((factura, cliente, saldo, dias_rest, estado_c))
                    deuda_por_cliente[cliente] = deuda_por_cliente.get(cliente, 0.0) + saldo
        except Exception as e:
            print("Error generando reporte de cuentas por cobrar:", e)

        cnt = {"Vencidos": 0, "Vencen Hoy": 0, "Próximos 1-7 días": 0, "Al Día": 0}
        mnt = {"Vencidos": 0.0, "Vencen Hoy": 0.0, "Próximos 1-7 días": 0.0, "Al Día": 0.0}
        total_deuda = 0.0

        for factura, cliente, saldo, dias_rest, estado_c in creditos:
            cnt[estado_c] += 1
            mnt[estado_c] += saldo
            total_deuda += saldo
            dias_txt = f"{dias_rest} días" if dias_rest >= 0 else "Vencido"
            self.tabla_det.insert("", tk.END, values=(
                factura, cliente, f"$ {saldo:,.2f}", dias_txt, estado_c
            ))

        for cliente, deuda in sorted(deuda_por_cliente.items(), key=lambda x: x[1], reverse=True)[:5]:
            self.tabla_top.insert("", tk.END, values=(cliente, f"$ {deuda:,.2f}"))

        self.lbl_tot_pend.config(text=str(len(creditos)))
        self.lbl_tot_cobrar.config(text=f"$ {total_deuda:,.2f}")
        self.lbl_venc_cnt.config(text=f"🔴  Vencidos ({cnt['Vencidos']}):")
        self.lbl_venc_monto.config(text=f"$ {mnt['Vencidos']:,.2f}")
        self.lbl_vhoy_cnt.config(text=f"🟠  Vencen Hoy ({cnt['Vencen Hoy']}):")
        self.lbl_vhoy_monto.config(text=f"$ {mnt['Vencen Hoy']:,.2f}")
        self.lbl_prox_cnt.config(text=f"🟡  Próximos 1-7 días ({cnt['Próximos 1-7 días']}):")
        self.lbl_prox_monto.config(text=f"$ {mnt['Próximos 1-7 días']:,.2f}")
        self.lbl_aldia_cnt.config(text=f"🟢  Al Día >7 días ({cnt['Al Día']}):")
        self.lbl_aldia_monto.config(text=f"$ {mnt['Al Día']:,.2f}")
        self.lbl_abonos_monto.config(text=f"$ {total_abonos:,.2f}")

    def exportar_excel(self):
        dest = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("Archivo CSV", "*.csv")],
            initialfile="Reporte_Cuentas_Por_Cobrar.csv"
        )
        if not dest:
            return
        try:
            with open(dest, mode="w", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f)
                writer.writerow(["Factura", "Cliente", "Saldo", "Días Restantes", "Estado"])
                for child in self.tabla_det.get_children():
                    writer.writerow(self.tabla_det.item(child, "values"))
            messagebox.showinfo("Exportación", f"Reporte de Cuentas por Cobrar exportado exitosamente a:\n{dest}")
        except Exception as e:
            messagebox.showerror("Error", f"Error exportando reporte: {e}")
