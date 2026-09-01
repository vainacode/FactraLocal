import tkinter as tk
from tkinter import messagebox, ttk

import db_conexion as sqlite3
from window_utils import posicionar_ventana


class HistorialNotas(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Historial de notas de crédito y débito")
        posicionar_ventana(self, 900, 500, parent)
        self.resizable(False, False)
        self.configure(bg="#DDE1E5")
        self.transient(parent)
        self.grab_set()
        tk.Label(self, text="HISTORIAL DE NOTAS", font=("sans", 21, "bold"),
                 bg="#DDE1E5", fg="#1E293B").pack(pady=16)
        self.tabla = ttk.Treeview(self, columns=("tipo", "factura", "ncf", "motivo", "monto", "fecha", "estado"), show="headings")
        self.tabla.pack(fill="both", expand=True, padx=20, pady=10)
        for col, texto, ancho in (("tipo", "Tipo", 90), ("factura", "Factura", 90), ("ncf", "e-NCF", 150),
                                  ("motivo", "Motivo", 250), ("monto", "Monto", 100), ("fecha", "Fecha", 100), ("estado", "Estado", 100)):
            self.tabla.heading(col, text=texto)
            self.tabla.column(col, width=ancho, anchor="center")
        tk.Button(self, text="Cerrar", command=self.destroy, bg="#EBEFF2",
                  font=("sans", 10, "bold")).pack(pady=(0, 14), ipadx=20, ipady=4)
        self.cargar()

    def cargar(self):
        try:
            with sqlite3.connect("database.db") as conn:
                filas = conn.execute("""
                    SELECT tipo, factura_afectada, NULL, motivo, monto, fecha, 'Local'
                    FROM notas_credito_debito_locales
                    UNION ALL
                    SELECT CASE WHEN c.tipo_ecf = 34 THEN 'Credito' ELSE 'Debito' END,
                           c.factura_local, c.e_ncf, COALESCE(c.ultimo_error, ''), NULL,
                           TO_CHAR(c.fecha_creacion, 'YYYY-MM-DD'), c.estado_actual
                    FROM comprobantes_fiscales c WHERE c.tipo_ecf IN (33, 34)
                    ORDER BY fecha DESC
                """).fetchall()
            for fila in filas:
                self.tabla.insert("", tk.END, values=fila)
        except sqlite3.Error as error:
            messagebox.showerror("Error", f"No se pudo cargar el historial: {error}")
