import datetime
import tkinter as tk
from tkinter import messagebox, ttk

import db_conexion as sqlite3
from window_utils import posicionar_ventana
from servicios.servicio_fiscal import ServicioFiscal


class NotaCreditoDebito(tk.Toplevel):
    def __init__(self, parent, factura=None):
        super().__init__(parent)
        self.parent = parent
        self.servicio_fiscal = ServicioFiscal()
        self.title("Nota de crédito / débito")
        posicionar_ventana(self, 500, 330, parent)
        self.resizable(False, False)
        self.configure(bg="#DDE1E5")
        self.transient(parent)
        self.grab_set()
        self.factura = tk.StringVar(value=str(factura or ""))
        self.tipo = tk.StringVar(value="Credito")
        self.crear_interfaz()

    def crear_interfaz(self):
        tk.Label(self, text="NOTA DE CRÉDITO / DÉBITO", font=("sans", 19, "bold"),
                 bg="#DDE1E5", fg="#1E293B").pack(pady=(18, 12))
        marco = tk.LabelFrame(self, text="Datos de la corrección", font=("sans", 11, "bold"),
                              bg="#C6D9E3", fg="#1E293B", padx=15, pady=10)
        marco.pack(fill="x", padx=20)
        tk.Label(marco, text="Factura afectada:", bg="#C6D9E3", font=("sans", 10, "bold")).grid(row=0, column=0, sticky="w", pady=5)
        ttk.Entry(marco, textvariable=self.factura, width=28).grid(row=0, column=1, pady=5)
        tk.Label(marco, text="Tipo:", bg="#C6D9E3", font=("sans", 10, "bold")).grid(row=1, column=0, sticky="w", pady=5)
        ttk.Combobox(marco, textvariable=self.tipo, values=("Credito", "Debito"), state="readonly", width=25).grid(row=1, column=1, pady=5)
        tk.Label(marco, text="Monto:", bg="#C6D9E3", font=("sans", 10, "bold")).grid(row=2, column=0, sticky="w", pady=5)
        self.monto = ttk.Entry(marco, width=28)
        self.monto.grid(row=2, column=1, pady=5)
        tk.Label(marco, text="Motivo:", bg="#C6D9E3", font=("sans", 10, "bold")).grid(row=3, column=0, sticky="w", pady=5)
        self.motivo = ttk.Entry(marco, width=28)
        self.motivo.grid(row=3, column=1, pady=5)
        tk.Button(self, text="Registrar nota", command=self.registrar, bg="#15803D", fg="white",
                  font=("sans", 11, "bold"), relief="raised", bd=2).pack(pady=16, ipadx=20, ipady=5)
        tk.Button(self, text="Ver historial", command=self.ver_historial, bg="#EBEFF2",
                  font=("sans", 9, "bold")).pack(pady=(0, 12), ipadx=12, ipady=3)

    def ver_historial(self):
        from historial_notas import HistorialNotas
        HistorialNotas(self)

    def registrar(self):
        try:
            factura = int(self.factura.get().strip())
            monto = float(self.monto.get().strip())
            if monto <= 0:
                raise ValueError
            motivo = self.motivo.get().strip() or "Corrección de factura"
            cajero = getattr(self.parent, "usuario", "")
            if not cajero:
                messagebox.showerror("Sesión requerida", "No se puede registrar una nota sin un usuario autenticado.")
                return
            with sqlite3.connect("database.db") as conn:
                original = conn.execute(
                    "SELECT factrapi_comprobante_id FROM comprobantes_fiscales WHERE factura_local = ? AND factrapi_comprobante_id IS NOT NULL LIMIT 1",
                    (factura,),
                ).fetchone()
            if original:
                import ecf_integracion
                respuesta = ecf_integracion.emitir_nota(factura, self.tipo.get(), motivo, monto, cajero)
                mensaje = f"Nota enviada a FactrAPI con e-NCF {respuesta.get('eNCF', 'pendiente')}"
            else:
                ahora = datetime.datetime.now()
                self.servicio_fiscal.guardar_nota_local((self.tipo.get(), factura, motivo, monto,
                    ahora.strftime("%Y-%m-%d"), ahora.strftime("%H:%M:%S"), cajero))
                mensaje = "Nota local registrada correctamente."
            messagebox.showinfo("Nota registrada", mensaje)
            self.destroy()
        except (ValueError, TypeError):
            messagebox.showwarning("Datos inválidos", "Ingrese una factura y un monto válidos.")
        except Exception as error:
            messagebox.showerror("Error", f"No se pudo registrar la nota: {error}")
