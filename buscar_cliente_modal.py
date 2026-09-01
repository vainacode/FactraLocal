import tkinter as tk
from tkinter import messagebox, ttk

from servicios.servicio_clientes import ServicioClientes


class BuscarClienteModal(tk.Toplevel):
    """Selector de clientes para el punto de venta."""

    AZUL = "#2d5d98"
    AZUL_OSCURO = "#1f477d"
    FONDO = "#f2f4f7"

    def __init__(self, parent, callback_select=None):
        super().__init__(parent)
        self.parent = parent
        self.callback_select = callback_select
        self.servicio_clientes = ServicioClientes()
        self.clientes = []
        self.resultados_mostrados = False

        self.title("Seleccionar cliente")
        self.geometry("680x470")
        self.minsize(560, 380)
        self.configure(bg=self.FONDO)
        self.transient(parent)
        self.grab_set()
        self._construir_interfaz()
        self._cargar_clientes()
        self.after(100, self.ent_busqueda.focus_set)

        # La ventana usa el encabezado propio de la aplicación.
        self.update_idletasks()
        self.overrideredirect(True)
        self.deiconify()
        self.lift()
        self.focus_force()

    def _construir_interfaz(self):
        encabezado = tk.Frame(self, bg=self.AZUL, height=34)
        encabezado.pack(fill="x")
        encabezado.pack_propagate(False)
        tk.Label(encabezado, text="▰  SELECCIONAR CLIENTE", bg=self.AZUL, fg="white",
                 font=("Segoe UI", 10, "bold")).pack(side="left", padx=12)
        tk.Button(encabezado, text="×", command=self.destroy, bg=self.AZUL, fg="white",
                  activebackground=self.AZUL_OSCURO, activeforeground="white",
                  relief="flat", bd=0, font=("Segoe UI", 15, "bold"),
                  width=3).pack(side="right")

        cuerpo = tk.Frame(self, bg=self.FONDO)
        cuerpo.pack(fill="both", expand=True, padx=14, pady=14)
        tk.Label(cuerpo, text="Buscar por nombre o identificación", bg=self.FONDO,
                 fg="#263746", font=("Segoe UI", 10, "bold")).pack(anchor="w")
        self.ent_busqueda = tk.Entry(cuerpo, bg="white", fg="#263746",
                                     insertbackground="#263746", relief="solid", bd=1,
                                     font=("Segoe UI", 11))
        fila_busqueda = tk.Frame(cuerpo, bg=self.FONDO)
        fila_busqueda.pack(fill="x", pady=(5, 12))
        fila_busqueda.columnconfigure(0, weight=1)
        self.ent_busqueda.pack(in_=fila_busqueda, side="left", fill="x", expand=True, ipady=5)
        self.ent_busqueda.bind("<Return>", self._buscar_o_seleccionar)
        self.ent_busqueda.bind("<KeyRelease>", self._marcar_busqueda_modificada)
        tk.Button(fila_busqueda, text="Buscar", command=self._buscar_o_seleccionar,
                  bg=self.AZUL, fg="white", activebackground=self.AZUL_OSCURO,
                  activeforeground="white", relief="flat", bd=0,
                  font=("Segoe UI", 9, "bold"), width=11).pack(side="right", padx=(8, 0), ipady=3)

        self.tabla = ttk.Treeview(cuerpo, columns=("id", "nombre", "tipo", "identificacion", "celular"),
                                  show="headings", selectmode="browse")
        for clave, texto, ancho, ancla in (
            ("id", "ID", 55, "center"), ("nombre", "Nombre", 245, "w"),
            ("tipo", "Tipo", 70, "center"), ("identificacion", "Identificación", 145, "center"),
            ("celular", "Celular", 120, "center"),
        ):
            self.tabla.heading(clave, text=texto, anchor=ancla)
            self.tabla.column(clave, width=ancho, anchor=ancla, stretch=clave == "nombre")
        self.tabla.pack(fill="both", expand=True)
        self.tabla.bind("<Double-1>", self._seleccionar)
        self.tabla.bind("<Return>", self._seleccionar)

        pie = tk.Frame(cuerpo, bg=self.FONDO)
        pie.pack(fill="x", pady=(12, 0))
        tk.Button(pie, text="Seleccionar", command=self._seleccionar, bg="#d9f2df",
                  fg="#166534", relief="solid", bd=1, font=("Segoe UI", 9, "bold"),
                  width=15).pack(side="left")
        tk.Button(pie, text="Cerrar", command=self.destroy, bg="white", fg="#263746",
                  relief="solid", bd=1, font=("Segoe UI", 9, "bold"),
                  width=12).pack(side="right")
        self.lbl_estado = tk.Label(cuerpo, text="Escriba un nombre o identificación y presione Enter.",
                                   bg=self.FONDO, fg="#64748b", anchor="w",
                                   font=("Segoe UI", 8))
        self.lbl_estado.pack(fill="x", pady=(5, 0))

    def _cargar_clientes(self):
        try:
            self.clientes = list(self.servicio_clientes.listar())
            self._renderizar(self.clientes)
            self.lbl_estado.config(text=f"{len(self.clientes)} clientes disponibles. Escriba y presione Enter.")
        except Exception as exc:
            messagebox.showerror("Clientes", f"No se pudieron cargar los clientes: {exc}", parent=self)

    def _renderizar(self, clientes):
        for fila in self.tabla.get_children():
            self.tabla.delete(fila)
        for cliente in clientes:
            self.tabla.insert("", "end", iid=str(cliente[0]), values=(
                cliente[0], cliente[1] or "", cliente[2] or "CC",
                cliente[3] or "-", cliente[4] or "-"))

    def _buscar_o_seleccionar(self, _evento=None):
        texto = self.ent_busqueda.get().strip().lower()
        if not texto:
            self._renderizar(self.clientes)
            self.resultados_mostrados = True
            self.lbl_estado.config(text=f"{len(self.clientes)} clientes disponibles.")
            return "break"
        if not self.resultados_mostrados:
            resultados = [c for c in self.clientes if texto in str(c[1] or "").lower()
                          or texto in str(c[3] or "").lower()]
            self._renderizar(resultados)
            if not resultados:
                self.lbl_estado.config(text="No se encontraron coincidencias.")
                messagebox.showinfo("Clientes", "No se encontró ningún cliente.", parent=self)
                return "break"
            self.tabla.selection_set(str(resultados[0][0]))
            self.tabla.focus(str(resultados[0][0]))
            self.resultados_mostrados = True
            self.lbl_estado.config(text=f"{len(resultados)} resultado(s). Seleccione uno y presione Enter.")
            return "break"
        self._seleccionar()
        return "break"

    def _marcar_busqueda_modificada(self, _evento=None):
        self.resultados_mostrados = False

    def _seleccionar(self, _evento=None):
        seleccion = self.tabla.selection()
        if not seleccion:
            return "break"
        cliente = next((c for c in self.clientes if str(c[0]) == str(seleccion[0])), None)
        if cliente and self.callback_select:
            try:
                self.grab_release()
            except tk.TclError:
                pass
            self.callback_select(cliente)
        if cliente:
            self.destroy()
        return "break"
