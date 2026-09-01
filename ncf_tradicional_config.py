import tkinter as tk
from tkinter import messagebox, ttk

import db_conexion as sqlite3
from ncf_tradicional import TIPOS_NCF
from window_utils import posicionar_ventana
from servicios.servicio_configuracion import ServicioConfiguracion


class NCFTradicionalConfig(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.title("Rangos NCF tradicionales")
        posicionar_ventana(self, 760, 520, parent)
        self.resizable(False, False)
        self.configure(bg="#DDE1E5")
        self.transient(parent)
        self.grab_set()
        self.tipo = tk.StringVar(value=TIPOS_NCF[0][0])
        self.servicio_configuracion = ServicioConfiguracion()
        self.crear_interfaz()
        self.cargar_rangos()

    def crear_interfaz(self):
        tk.Label(self, text="RANGOS NCF TRADICIONALES", font=("sans", 22, "bold"),
                 bg="#DDE1E5", fg="#1E293B").pack(pady=(18, 12))
        marco = tk.LabelFrame(self, text="Agregar rango autorizado por DGII",
                              font=("sans", 11, "bold"), bg="#C6D9E3", fg="#1E293B",
                              padx=12, pady=8)
        marco.pack(fill="x", padx=20)
        tk.Label(marco, text="Tipo:", bg="#C6D9E3", font=("sans", 10, "bold")).grid(row=0, column=0, padx=5, pady=4)
        ttk.Combobox(marco, textvariable=self.tipo, values=[t[0] for t in TIPOS_NCF],
                     state="readonly", width=10).grid(row=0, column=1, padx=5)
        self.desde = ttk.Entry(marco, width=15)
        self.hasta = ttk.Entry(marco, width=15)
        self.vencimiento = ttk.Entry(marco, width=15)
        for col, texto, widget in ((2, "Desde", self.desde), (4, "Hasta", self.hasta), (6, "Vence (AAAA-MM-DD)", self.vencimiento)):
            tk.Label(marco, text=texto, bg="#C6D9E3", font=("sans", 9, "bold")).grid(row=0, column=col, padx=4)
            widget.grid(row=0, column=col + 1, padx=4)
        tk.Button(marco, text="Agregar", command=self.agregar, bg="#15803D", fg="white",
                  font=("sans", 10, "bold"), relief="raised", bd=2).grid(row=0, column=8, padx=8)

        self.tabla = ttk.Treeview(self, columns=("tipo", "desde", "hasta", "actual", "vence", "estado"), show="headings")
        self.tabla.pack(fill="both", expand=True, padx=20, pady=16)
        for col, texto, ancho in (("tipo", "Tipo", 100), ("desde", "Desde", 120), ("hasta", "Hasta", 120),
                                  ("actual", "Próximo", 120), ("vence", "Vencimiento", 150), ("estado", "Estado", 100)):
            self.tabla.heading(col, text=texto)
            self.tabla.column(col, width=ancho, anchor="center")
        tk.Button(self, text="Cerrar", command=self.destroy, bg="#EBEFF2",
                  font=("sans", 10, "bold")).pack(pady=(0, 14), ipadx=20, ipady=4)

    def cargar_rangos(self):
        for item in self.tabla.get_children():
            self.tabla.delete(item)
        try:
            with sqlite3.connect("database.db") as conn:
                filas = conn.execute("""
                    SELECT tipo_ncf, secuencia_desde, secuencia_hasta, secuencia_actual,
                           fecha_vencimiento, CASE WHEN activa THEN 'Activo' ELSE 'Inactivo' END
                    FROM secuencias_ncf_tradicional ORDER BY tipo_ncf, id
                """).fetchall()
            for fila in filas:
                self.tabla.insert("", tk.END, values=fila)
        except sqlite3.Error as error:
            messagebox.showerror("Error", f"No se pudieron cargar los rangos: {error}")

    def agregar(self):
        try:
            desde = int(self.desde.get().strip())
            hasta = int(self.hasta.get().strip())
            if desde <= 0 or hasta < desde:
                raise ValueError
            vencimiento = self.vencimiento.get().strip() or None
            if vencimiento:
                import datetime
                datetime.date.fromisoformat(vencimiento)
            self.servicio_configuracion.crear_secuencia_ncf((self.tipo.get(), desde, hasta, desde, vencimiento))
            self.desde.delete(0, tk.END); self.hasta.delete(0, tk.END); self.vencimiento.delete(0, tk.END)
            self.cargar_rangos()
        except (ValueError, TypeError):
            messagebox.showwarning("Datos inválidos", "Revise el rango y la fecha de vencimiento.")
        except sqlite3.Error as error:
            messagebox.showerror("Error", f"No se pudo guardar el rango: {error}")
