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

class ReporteVentasCliente(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.title("Reporte de Ventas por Cliente - La Casa de los Repuestos")
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
        # Header
        lbl_title = tk.Label(
            self,
            text="REPORTE DE VENTAS POR CLIENTE",
            font=("sans", 22, "bold"),
            bg="#C6D9E3",
            fg="#1E293B"
        )
        lbl_title.place(relx=0.5, y=30, anchor="center")

        # Filtros
        frame_top = tk.Frame(self, bg="#DDE1E5", highlightbackground="#B8C4CE", highlightthickness=1)
        frame_top.place(x=20, y=65, width=940, height=50)

        tk.Label(frame_top, text="Buscar:", font=("sans", 10, "bold"), bg="#DDE1E5", fg="#1E293B").place(x=15, y=14)
        self.ent_buscar = ttk.Entry(frame_top, font=("sans", 10))
        self.ent_buscar.place(x=70, y=11, width=240, height=28)
        self.ent_buscar.bind("<KeyRelease>", lambda e: self.cargar_datos())

        tk.Label(frame_top, text="Ordenar:", font=("sans", 10, "bold"), bg="#DDE1E5", fg="#1E293B").place(x=330, y=14)
        self.cmb_orden = ttk.Combobox(frame_top, values=["Mayor Facturación", "Más Compras", "Nombre A-Z"], font=("sans", 10), state="readonly")
        self.cmb_orden.set("Mayor Facturación")
        self.cmb_orden.place(x=395, y=11, width=170, height=28)
        self.cmb_orden.bind("<<ComboboxSelected>>", lambda e: self.cargar_datos())

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
        style.configure("VC.Treeview.Heading", font=("sans", 10, "bold"), background="#E0E6ED")
        style.configure("VC.Treeview", font=("sans", 9), rowheight=24)

        cols = ("ranking", "cliente", "facturas", "articulos", "total_comprado", "ultima_compra")
        self.tabla = ttk.Treeview(self, columns=cols, show="headings", style="VC.Treeview")
        self.tabla.place(x=20, y=125, width=940, height=370)

        self.tabla.heading("ranking", text="#", anchor="center")
        self.tabla.heading("cliente", text="Cliente / Taller Mecánico", anchor="w")
        self.tabla.heading("facturas", text="Facturas", anchor="center")
        self.tabla.heading("articulos", text="Repuestos Comprados", anchor="center")
        self.tabla.heading("total_comprado", text="Total Comprado (RD$)", anchor="e")
        self.tabla.heading("ultima_compra", text="Última Compra", anchor="center")

        self.tabla.column("ranking", width=40, anchor="center")
        self.tabla.column("cliente", width=340, anchor="w")
        self.tabla.column("facturas", width=110, anchor="center")
        self.tabla.column("articulos", width=150, anchor="center")
        self.tabla.column("total_comprado", width=170, anchor="e")
        self.tabla.column("ultima_compra", width=130, anchor="center")

        # Barra Inferior
        frame_bot = tk.Frame(self, bg="#CAD8E2", highlightbackground="#A9BFCE", highlightthickness=1)
        frame_bot.place(x=20, y=505, width=940, height=75)

        self.lbl_tot_clientes = tk.Label(frame_bot, text="Clientes Registrados: 0", font=("sans", 11, "bold"), bg="#CAD8E2", fg="#1E293B")
        self.lbl_tot_clientes.place(x=30, y=25)

        self.lbl_gran_total = tk.Label(frame_bot, text="TOTAL FACTURADO: RD$ 0.00", font=("sans", 13, "bold"), bg="#CAD8E2", fg="#166534")
        self.lbl_gran_total.place(x=580, y=25)

    def cargar_datos(self):
        for r in self.tabla.get_children():
            self.tabla.delete(r)

        filtro = self.ent_buscar.get().strip().lower()
        orden = self.cmb_orden.get()

        clientes_dict = {}
        try:
            for cli, fac, cant, tot, fec in ServicioReportes().ventas_cliente():
                    c_nom = cli or "Cliente General"
                    if c_nom not in clientes_dict:
                        clientes_dict[c_nom] = {"facturas": set(), "articulos": 0, "total": 0.0, "ultima": fec}
                    clientes_dict[c_nom]["facturas"].add(fac)
                    clientes_dict[c_nom]["articulos"] += int(cant or 1)
                    clientes_dict[c_nom]["total"] += float(tot or 0.0)
                    if fec > clientes_dict[c_nom]["ultima"]:
                        clientes_dict[c_nom]["ultima"] = fec
        except Exception as e:
            print("Error cargando ventas por cliente:", e)

        lista = []
        for c, d in clientes_dict.items():
            if filtro and filtro not in c.lower():
                continue
            lista.append({
                "cliente": c,
                "facturas": len(d["facturas"]),
                "articulos": d["articulos"],
                "total": d["total"],
                "ultima": d["ultima"]
            })

        if orden == "Mayor Facturación":
            lista.sort(key=lambda x: x["total"], reverse=True)
        elif orden == "Más Compras":
            lista.sort(key=lambda x: x["facturas"], reverse=True)
        elif orden == "Nombre A-Z":
            lista.sort(key=lambda x: x["cliente"].lower())

        gran_total = 0.0
        for i, item in enumerate(lista, 1):
            gran_total += item["total"]
            self.tabla.insert("", tk.END, values=(
                str(i),
                f"  {item['cliente']}",
                str(item["facturas"]),
                str(item["articulos"]),
                f"RD$ {item['total']:,.2f}",
                str(item["ultima"])
            ))

        self.lbl_tot_clientes.config(text=f"Clientes con Compras: {len(lista)}")
        self.lbl_gran_total.config(text=f"TOTAL FACTURADO: RD$ {gran_total:,.2f}")

    def exportar_csv(self):
        dest = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("Archivo CSV", "*.csv")],
            initialfile="Reporte_Ventas_Por_Cliente.csv"
        )
        if dest:
            try:
                with open(dest, mode="w", newline="", encoding="utf-8-sig") as f:
                    writer = csv.writer(f)
                    writer.writerow(["#", "Cliente / Taller Mecánico", "Facturas", "Repuestos Comprados", "Total Comprado (RD$)", "Última Compra"])
                    for child in self.tabla.get_children():
                        writer.writerow(self.tabla.item(child, "values"))
                messagebox.showinfo("Exportación", f"Reporte exportado exitosamente a:\n{dest}")
            except Exception as e:
                messagebox.showerror("Error", f"Error exportando reporte: {e}")
