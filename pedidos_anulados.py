import csv
import os
import db_conexion as sqlite3
import sys
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageTk
from window_utils import posicionar_ventana

class PedidosAnulados(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.title("Pedidos Anulados a Proveedores")
        posicionar_ventana(self, 980, 600, parent)
        self.resizable(False, False)
        self.configure(bg="#DDE1E5")
        self.transient(parent)
        self.grab_set()
        try:
            self.iconbitmap(self.rutas('icono.ico'))
        except Exception:
            pass

        self.db_name = "database.db"
        self.images = {}
        self.pedidos_anulados = []

        self.widgets()
        self.cargar_anulados()

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
            text="HISTORIAL DE PEDIDOS ANULADOS",
            font=("sans", 24, "bold"),
            bg="#DDE1E5",
            fg="#1E293B"
        )
        lbl_title.place(relx=0.5, y=25, anchor="center")

#============== 2. FILTROS =========================================================================#
        lbl_b = tk.Label(self, text="Buscar:", font=("sans", 12, "bold"), bg="#DDE1E5", fg="#1E293B")
        lbl_b.place(x=25, y=65)

        self.ent_buscar = ttk.Entry(self, font=("sans", 11))
        self.ent_buscar.place(x=95, y=63, width=280, height=30)
        self.ent_buscar.bind("<KeyRelease>", lambda e: self.filtrar())

        ruta_ex = self.rutas("icono/excel.png")
        if os.path.exists(ruta_ex):
            self.images["ex_pa_ico"] = ImageTk.PhotoImage(Image.open(ruta_ex).resize((20, 20), Image.Resampling.LANCZOS))
            ico_ex = self.images["ex_pa_ico"]
        else:
            ico_ex = None

        btn_ex = tk.Button(self, text="  Exportar Excel", image=ico_ex, compound=tk.LEFT, font=("sans", 10, "bold"), bg="#15803D", fg="white", relief="raised", bd=2, cursor="hand2", command=self.exportar_excel)
        btn_ex.place(x=795, y=60, width=160, height=36)

#============== 3. TABLA ===========================================================================#
        style = ttk.Style()
        style.configure("PAN.Treeview.Heading", font=("sans", 9, "bold"), background="#E0E6ED")
        style.configure("PAN.Treeview", font=("sans", 9), rowheight=24)

        cols = ("id", "pedido", "proveedor", "producto", "cantidad", "fecha", "usuario", "motivo")
        self.tabla = ttk.Treeview(self, columns=cols, show="headings", style="PAN.Treeview")
        self.tabla.place(x=20, y=105, width=940, height=425)

        titulos = [
            ("id", "ID", 40),
            ("pedido", "Nº Pedido", 80),
            ("proveedor", "Proveedor", 180),
            ("producto", "Producto", 220),
            ("cantidad", "Cant", 50),
            ("fecha", "Fecha", 100),
            ("usuario", "Usuario", 100),
            ("motivo", "Motivo", 150),
        ]

        for c, t, w in titulos:
            self.tabla.heading(c, text=t, anchor="center")
            self.tabla.column(c, width=w, anchor="center" if c in ("id", "pedido", "cantidad", "fecha", "usuario") else "w")

        scroll_y = ttk.Scrollbar(self, orient="vertical", command=self.tabla.yview)
        self.tabla.configure(yscrollcommand=scroll_y.set)
        scroll_y.place(x=950, y=105, height=425)

#============== 4. BARRA INFERIOR ==================================================================#
        btn_cerrar = tk.Button(self, text="Cerrar", font=("sans", 11, "bold"), bg="#EF4444", fg="white", relief="raised", bd=2, cursor="hand2", command=self.destroy)
        btn_cerrar.place(relx=0.5, y=550, width=160, height=38, anchor="center")

    def cargar_anulados(self):
        for r in self.tabla.get_children():
            self.tabla.delete(r)

        try:
            with sqlite3.connect(self.db_name) as conn:
                cur = conn.cursor()
                cur.execute("SELECT id, numero_pedido, proveedor, producto, cantidad, fecha, usuario, motivo FROM pedidos_anulados")
                self.pedidos_anulados = cur.fetchall()
        except Exception as error:
            self.pedidos_anulados = []
            messagebox.showerror("Error", f"No se pudo cargar el historial: {error}")

        for p in self.pedidos_anulados:
            self.tabla.insert("", tk.END, values=p)

    def filtrar(self):
        q = self.ent_buscar.get().strip().lower()
        for r in self.tabla.get_children():
            self.tabla.delete(r)

        for p in self.pedidos_anulados:
            if not q or q in str(p[1]).lower() or q in str(p[2]).lower() or q in str(p[3]).lower():
                self.tabla.insert("", tk.END, values=p)

    def exportar_excel(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("Archivo CSV", "*.csv")], initialfile="Pedidos_Anulados.csv")
        if file_path:
            try:
                with open(file_path, mode="w", newline="", encoding="utf-8-sig") as f:
                    w = csv.writer(f)
                    w.writerow(["ID", "Nº Pedido", "Proveedor", "Producto", "Cantidad", "Fecha", "Usuario", "Motivo"])
                    for p in self.pedidos_anulados:
                        w.writerow(p)
                messagebox.showinfo("Exportar", "Reporte exportado correctamente a CSV.")
            except Exception as e:
                messagebox.showerror("Error", f"Error exportando: {e}")
