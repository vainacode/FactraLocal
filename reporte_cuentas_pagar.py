import csv
import datetime
import os
import db_conexion as sqlite3
import sys
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageTk
from window_utils import posicionar_ventana

class ReporteCuentasPagar(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.title("Reporte de Cuentas por Pagar - La Casa de los Repuestos")
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
            text="REPORTE DE CUENTAS POR PAGAR A PROVEEDORES",
            font=("sans", 20, "bold"),
            bg="#C6D9E3",
            fg="#1E293B"
        )
        lbl_title.place(relx=0.5, y=30, anchor="center")

        frame_top = tk.Frame(self, bg="#DDE1E5", highlightbackground="#B8C4CE", highlightthickness=1)
        frame_top.place(x=20, y=65, width=940, height=50)

        tk.Label(frame_top, text="Buscar:", font=("sans", 10, "bold"), bg="#DDE1E5", fg="#1E293B").place(x=15, y=14)
        self.ent_buscar = ttk.Entry(frame_top, font=("sans", 10))
        self.ent_buscar.place(x=70, y=11, width=240, height=28)
        self.ent_buscar.bind("<KeyRelease>", lambda e: self.cargar_datos())

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
        style.configure("CPG.Treeview.Heading", font=("sans", 10, "bold"), background="#E0E6ED")
        style.configure("CPG.Treeview", font=("sans", 9), rowheight=24)

        cols = ("id", "proveedor", "factura", "fecha", "total_factura", "abonado", "saldo_pendiente", "estado")
        self.tabla = ttk.Treeview(self, columns=cols, show="headings", style="CPG.Treeview")
        self.tabla.place(x=20, y=125, width=940, height=370)

        self.tabla.heading("id", text="#", anchor="center")
        self.tabla.heading("proveedor", text="Proveedor / Distribuidora", anchor="w")
        self.tabla.heading("factura", text="No. Factura Prov.", anchor="center")
        self.tabla.heading("fecha", text="Fecha Emisión", anchor="center")
        self.tabla.heading("total_factura", text="Total (RD$)", anchor="e")
        self.tabla.heading("abonado", text="Abonado (RD$)", anchor="e")
        self.tabla.heading("saldo_pendiente", text="Saldo Pendiente (RD$)", anchor="e")
        self.tabla.heading("estado", text="Estado", anchor="center")

        self.tabla.column("id", width=35, anchor="center")
        self.tabla.column("proveedor", width=250, anchor="w")
        self.tabla.column("factura", width=120, anchor="center")
        self.tabla.column("fecha", width=100, anchor="center")
        self.tabla.column("total_factura", width=120, anchor="e")
        self.tabla.column("abonado", width=110, anchor="e")
        self.tabla.column("saldo_pendiente", width=125, anchor="e")
        self.tabla.column("estado", width=80, anchor="center")

        frame_bot = tk.Frame(self, bg="#CAD8E2", highlightbackground="#A9BFCE", highlightthickness=1)
        frame_bot.place(x=20, y=505, width=940, height=75)

        self.lbl_tot_facturas = tk.Label(frame_bot, text="Cuentas Pendientes: 0", font=("sans", 11, "bold"), bg="#CAD8E2", fg="#1E293B")
        self.lbl_tot_facturas.place(x=30, y=25)

        self.lbl_gran_saldo = tk.Label(frame_bot, text="TOTAL POR PAGAR: RD$ 0.00", font=("sans", 13, "bold"), bg="#CAD8E2", fg="#DC2626")
        self.lbl_gran_saldo.place(x=540, y=25)

    def cargar_datos(self):
        for r in self.tabla.get_children():
            self.tabla.delete(r)

        filtro = self.ent_buscar.get().strip().lower()

        # Solo se presentan compras registradas; no se insertan datos de ejemplo.
        compras_list = []

        tot_saldo = 0.0
        cant_pend = 0

        for r in compras_list:
            cid, prov, fac, fec, tot, ab, sal, est = r
            if filtro and filtro not in prov.lower() and filtro not in fac.lower():
                continue
            if sal > 0:
                tot_saldo += sal
                cant_pend += 1

            self.tabla.insert("", tk.END, values=(
                str(cid),
                f"  {prov}",
                fac,
                fec,
                f"RD$ {tot:,.2f}",
                f"RD$ {ab:,.2f}",
                f"RD$ {sal:,.2f}",
                est
            ))

        self.lbl_tot_facturas.config(text=f"Cuentas Pendientes: {cant_pend}")
        self.lbl_gran_saldo.config(text=f"TOTAL POR PAGAR: RD$ {tot_saldo:,.2f}")

    def exportar_csv(self):
        dest = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("Archivo CSV", "*.csv")],
            initialfile="Reporte_Cuentas_Por_Pagar.csv"
        )
        if dest:
            try:
                with open(dest, mode="w", newline="", encoding="utf-8-sig") as f:
                    writer = csv.writer(f)
                    writer.writerow(["#", "Proveedor", "No. Factura Prov.", "Fecha Emisión", "Total (RD$)", "Abonado (RD$)", "Saldo Pendiente (RD$)", "Estado"])
                    for child in self.tabla.get_children():
                        writer.writerow(self.tabla.item(child, "values"))
                messagebox.showinfo("Exportación", f"Reporte exportado exitosamente a:\n{dest}")
            except Exception as e:
                messagebox.showerror("Error", f"Error exportando reporte: {e}")
