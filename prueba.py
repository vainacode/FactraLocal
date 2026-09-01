"""Punto de venta Factra con interfaz visual y flujo operativo real.

Puede abrirse como Toplevel desde la aplicación principal o ejecutarse
directamente; usa los servicios de aplicación para catálogo, caja y ventas.
"""

from __future__ import annotations

import datetime as dt
import os
import sys
import tkinter as tk
from tkinter import messagebox, ttk
from decimal import Decimal

try:
    from PIL import Image, ImageTk
except ImportError:  # PIL es opcional; los botones siguen funcionando sin iconos.
    Image = ImageTk = None

try:
    from window_utils import posicionar_ventana
except ImportError:
    def posicionar_ventana(ventana, ancho, alto, _padre=None):
        ventana.geometry(f"{ancho}x{alto}")

from dominio.ventas.modelos import ItemVenta, SolicitudVenta
from servicios.servicio_caja import ServicioCaja
from servicios.servicio_clientes import ServicioClientes
from servicios.servicio_inventario import ServicioInventario
from servicios.servicio_ventas import ServicioVentas


class Prueba(tk.Toplevel):
    """Punto de venta operativo con la misma apariencia de la maqueta."""

    AZUL = "#2d5d98"
    AZUL_OSCURO = "#1f477d"
    AZUL_PANEL = "#285995"
    FONDO = "#f2f4f7"
    BORDE = "#c9d0d8"
    TEXTO = "#263746"
    NARANJA = "#f0c47b"

    def __init__(self, parent=None, usuario="SUPERVISOR"):
        super().__init__(parent)
        self.parent = parent
        self.usuario = usuario or "SUPERVISOR"
        self.servicio_ventas = ServicioVentas()
        self.servicio_caja = ServicioCaja()
        self.servicio_clientes = ServicioClientes()
        self.servicio_inventario = ServicioInventario()
        self._ventanas_secundarias = []
        self.title("Factra POS | Prueba")
        # La prueba debe cubrir exactamente el contenedor desde el que se abre,
        # sin dejar visible la ventana anterior por los bordes.
        self.minsize(900, 500)
        self._ajustar_al_contenedor(parent)
        self.configure(bg=self.FONDO)
        # Se comporta como las demás ventanas del sistema: queda asociada al
        # contenedor y captura la interacción mientras está abierta, pero al
        # cerrarse solo se destruye esta ventana hija.
        try:
            self.transient(parent.winfo_toplevel() if parent is not None else None)
            self.grab_set()
        except tk.TclError:
            pass
        # Prueba es la ventana principal del flujo de venta, no un modal del
        # contenedor. Los modales se enlazan a esta ventana individualmente.

        self.productos = [
            {"id": 1, "codigo": "TG-01", "articulo": "Teclado gamer Bluetooth Redragon", "descripcion": "Teclado inalámbrico con iluminación RGB", "precio": 450000.0, "costo": 0, "stock": 99},
            {"id": 2, "codigo": "TG-02", "articulo": "Teclado gamer Scorpion K215", "descripcion": "Teclado mecánico para juegos", "precio": 200000.0, "costo": 0, "stock": 99},
            {"id": 3, "codigo": "MS-01", "articulo": "Mouse gamer inalámbrico", "descripcion": "Mouse óptico inalámbrico de alta precisión", "precio": 85000.0, "costo": 0, "stock": 99},
        ]
        self._cargar_catalogo_real()
        self.carrito = []
        self.ultimo_producto = "Ningún producto agregado"
        self.impuesto = 0.19
        self.iconos = {}
        self.resultados_mostrados = False
        self._crear_estilos()
        self._construir_interfaz()
        self._actualizar_resumen()
        self._actualizar_reloj()
        # La interfaz define su propia barra azul; ocultamos la barra nativa
        # cuando todos los widgets ya fueron creados para no bloquear el
        # Toplevel al abrirlo desde el menú principal.
        self.update_idletasks()
        # El encabezado azul de Factra reemplaza la barra nativa de Windows;
        # así se muestra un solo título y no un encabezado duplicado.
        self.overrideredirect(True)
        self.protocol("WM_DELETE_WINDOW", self._cerrar)
        self.after(120, self._enfocar_busqueda)

    def _ajustar_al_contenedor(self, parent):
        """Alinea la ventana con el área real del contenedor principal."""
        try:
            if parent is not None:
                parent.update_idletasks()
                ancho = parent.winfo_width()
                alto = parent.winfo_height()
                x = parent.winfo_rootx()
                y = parent.winfo_rooty()
                if ancho > 100 and alto > 100:
                    self.geometry(f"{ancho}x{alto}+{x}+{y}")
                    return
            self.geometry("1280x760")
        except tk.TclError:
            self.geometry("1280x760")

    def _cargar_catalogo_real(self):
        try:
            filas = self.servicio_inventario.listar_productos(activos=True)
            if filas:
                self.productos = [{
                    "id": fila[0], "codigo": fila[8] or str(fila[0]),
                    "articulo": fila[1], "descripcion": fila[1],
                    "precio": float(fila[3] or 0), "costo": float(fila[4] or 0),
                    "stock": int(fila[5] or 0),
                } for fila in filas]
        except Exception:
            # La maqueta conserva sus productos de demostración si la base
            # no está disponible al abrirla directamente.
            pass

    def _enfocar_busqueda(self):
        if self.winfo_exists():
            try:
                self.deiconify()
                self.lift()
                self.focus_force()
                self.ent_busqueda.tkraise()
                self.ent_busqueda.focus_force()
                self.ent_busqueda.icursor(tk.END)
            except tk.TclError:
                pass

    def _cerrar(self):
        if self.winfo_exists():
            try:
                self.grab_release()
            except tk.TclError:
                pass
            self.destroy()
            try:
                principal = self.parent.winfo_toplevel() if self.parent is not None else None
                if principal is not None and principal.winfo_exists():
                    principal.deiconify()
                    principal.lift()
                    principal.focus_force()
            except tk.TclError:
                pass

    def _guardar_ventana_secundaria(self, ventana):
        """Mantiene vivos los modales y los coloca sobre la venta actual."""
        self._ventanas_secundarias.append(ventana)
        ventana.lift()
        ventana.focus_force()

        def quitar_referencia(_evento=None, ventana=ventana):
            if ventana in self._ventanas_secundarias:
                self._ventanas_secundarias.remove(ventana)

        ventana.bind("<Destroy>", quitar_referencia, add="+")
        return ventana

    def _crear_estilos(self):
        estilo = ttk.Style(self)
        try:
            estilo.theme_use("clam")
        except tk.TclError:
            pass
        estilo.configure("POS.Treeview", background="white", fieldbackground="white", foreground=self.TEXTO,
                         font=("Segoe UI", 9), rowheight=23, borderwidth=0)
        estilo.configure("POS.Treeview.Heading", background=self.AZUL, foreground="white",
                         font=("Segoe UI", 9, "bold"), relief="flat", padding=(5, 3))
        estilo.map("POS.Treeview", background=[("selected", "#dceafb")], foreground=[("selected", self.TEXTO)])
        estilo.configure("POS.TEntry", padding=4, font=("Segoe UI", 10))

    def _ruta_recurso(self, nombre):
        base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
        return os.path.join(base, "icono", nombre)

    def _icono(self, nombre, tamano=(23, 23)):
        if Image is None or ImageTk is None:
            return None
        ruta = self._ruta_recurso(nombre)
        if not os.path.exists(ruta):
            return None
        try:
            imagen = Image.open(ruta).convert("RGBA").resize(tamano, Image.Resampling.LANCZOS)
            clave = f"{nombre}-{tamano}"
            self.iconos[clave] = ImageTk.PhotoImage(imagen)
            return self.iconos[clave]
        except Exception:
            return None

    def _construir_interfaz(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(4, weight=1)

        titulo = tk.Frame(self, bg=self.AZUL, height=27)
        titulo.grid(row=0, column=0, sticky="ew")
        titulo.grid_propagate(False)
        tk.Label(titulo, text="▰", bg=self.AZUL, fg="#f3c46b", font=("Segoe UI", 9, "bold")).pack(side="left", padx=(10, 4))
        tk.Label(titulo, text="Factra POS  |  Versión 1.0  |  ENTORNO DE PRUEBA", bg=self.AZUL,
                 fg="white", font=("Segoe UI", 8)).pack(side="left")
        for texto, comando in (("—", self.iconify), ("□", self._maximizar), ("×", self._cerrar)):
            tk.Button(titulo, text=texto, command=comando, bg=self.AZUL, fg="white", relief="flat", bd=0,
                      activebackground=self.AZUL_OSCURO, activeforeground="white", font=("Segoe UI", 10)).pack(side="right", padx=4)

        navegacion = tk.Frame(self, bg=self.AZUL, height=31)
        navegacion.grid(row=1, column=0, sticky="ew")
        navegacion.grid_propagate(False)
        for texto, activo in (("POS", False), ("PUNTO DE VENTA", True), ("TALLERES Y SERVICIOS", False), ("ESHOP (TIENDA VIRTUAL)", False)):
            tk.Label(navegacion, text=texto, bg=self.AZUL_OSCURO if activo else self.AZUL, fg="white",
                     font=("Segoe UI", 8, "bold"), padx=14).pack(side="left", fill="y")

        self._crear_barra_acciones()
        self._crear_informacion()
        self._crear_tabla()
        self._crear_panel_inferior()

    def _crear_barra_acciones(self):
        acciones = tk.Frame(self, bg="white", height=70, highlightbackground=self.BORDE, highlightthickness=1)
        acciones.grid(row=2, column=0, sticky="ew")
        acciones.grid_propagate(False)
        botones = [
            ("Agregar\n(F2)", "agregar.png", self.agregar),
            ("Remover\n(Supr)", "eliminar.png", self.remover),
            ("Limpiar\n(F3)", "limpiar.png", self.limpiar),
            ("Consultar\n(F4)", "buscar.png", self.buscar),
            ("Precio\n(F11)", "precio.png", self.mostrar_demo),
            ("Cantidad\n(F11 - Ctrl+C)", "editar.png", self.cambiar_cantidad),
            ("Guardar\n(F5)", "guardar.png", self.mostrar_demo),
            ("Cargar\n(F6)", "cargarfactura.png", self.mostrar_demo),
            ("Clientes\n(F7)", "btnclientes.png", self.buscar_cliente),
            ("Facturar\n(F9)", "factura.png", self.facturar),
            ("Abrir Cajón\n(F8)", "abrircaja.png", self.abrir_caja),
            ("Calculadora\n(F10)", "btncaja.png", self.mostrar_demo),
            ("Reimprimir Factura\n(Ctrl+F9)", "impresora.png", self.mostrar_demo),
            ("Devolución de Factura\n(Ctrl+D)", "anular.png", self.mostrar_demo),
            ("Vales\n(Ctrl+V)", "ticket.png", self.mostrar_demo),
            ("Crear Arqueo de Caja\n(Ctrl+A)", "btncaja.png", self.mostrar_demo),
            ("Apartados", "pedido.png", self.mostrar_demo),
            ("Bonos", "abonospagados.png", self.mostrar_demo),
            ("Operaciones\nEspeciales (F12)", "especial.png", self.mostrar_demo),
        ]
        for indice, (texto, archivo, comando) in enumerate(botones):
            boton = tk.Button(acciones, text=texto, image=self._icono(archivo), compound="top", command=comando,
                              bg="white", fg=self.TEXTO, activebackground="#e8f0f8", relief="flat", bd=0,
                              font=("Segoe UI", 6, "bold"), cursor="hand2", justify="center")
            boton.grid(row=0, column=indice, sticky="nsew", padx=1, pady=3)
            acciones.columnconfigure(indice, weight=1)

    def _crear_informacion(self):
        info = tk.Frame(self, bg=self.FONDO, height=92)
        info.grid(row=3, column=0, sticky="ew", padx=14, pady=(4, 3))
        info.grid_propagate(False)
        izquierda = tk.Frame(info, bg=self.FONDO)
        izquierda.place(x=0, y=0, relwidth=.76, height=92)

        tk.Label(izquierda, text="Cliente", bg=self.FONDO, fg=self.TEXTO,
                 font=("Segoe UI", 8, "bold")).place(x=0, y=6)
        self.codigo_cliente = ttk.Entry(izquierda, style="POS.TEntry")
        self.codigo_cliente.insert(0, "222222222222")
        self.codigo_cliente.place(x=56, y=2, width=175, height=27)
        tk.Button(izquierda, text="×", command=lambda: self.codigo_cliente.delete(0, tk.END), bg="white", fg="#6d7884",
                  relief="solid", bd=1, font=("Segoe UI", 8)).place(x=235, y=3, width=23, height=25)
        self.lbl_cliente_nombre = tk.Label(izquierda, text="CONSUMIDOR FINAL", bg=self.FONDO, fg="#526273",
                                           font=("Segoe UI", 8))
        self.lbl_cliente_nombre.place(x=266, y=6)

        x_datos = 430
        tk.Label(izquierda, text="Cajero", bg=self.FONDO, fg="#526273",
                 font=("Segoe UI", 7, "bold")).place(x=x_datos, y=4)
        tk.Label(izquierda, text=self.usuario.upper(), bg=self.FONDO, fg="#526273",
                 font=("Segoe UI", 7)).place(x=x_datos + 47, y=4)
        tk.Label(izquierda, text="Fecha", bg=self.FONDO, fg="#526273",
                 font=("Segoe UI", 7, "bold")).place(x=x_datos, y=23)
        tk.Label(izquierda, text="JUEVES, 1 DE SEPTIEMBRE DE 2026", bg=self.FONDO, fg="#526273",
                 font=("Segoe UI", 7)).place(x=x_datos + 47, y=23)
        tk.Label(izquierda, text="Hora", bg=self.FONDO, fg="#526273",
                 font=("Segoe UI", 7, "bold")).place(x=x_datos, y=42)
        self.lbl_hora = tk.Label(izquierda, text="", bg=self.FONDO, fg="#526273",
                                 font=("Segoe UI", 7))
        self.lbl_hora.place(x=x_datos + 47, y=42)

        secundarios = (
            ("Acumula 9014.66 puntos", 0, 174, self.NARANJA, 1),
            ("Info de cliente", 179, 104, "#e5e9ee", 0),
            ("Impuestos", 288, 76, "#e5e9ee", 0),
            ("Más", 369, 42, "#e5e9ee", 0),
        )
        for texto, x, ancho, color, borde in secundarios:
            tk.Button(izquierda, text=texto, bg=color, fg=self.TEXTO, relief="solid" if borde else "flat",
                      bd=borde, font=("Segoe UI", 7, "bold"), command=self.mostrar_demo).place(
                          x=x, y=66, width=ancho, height=22)

        resumen = tk.Frame(info, bg=self.FONDO)
        resumen.place(relx=1, x=-205, y=0, width=205, height=92)
        tk.Label(resumen, text="Documento", bg=self.FONDO, fg=self.TEXTO,
                 font=("Segoe UI", 8, "bold"), anchor="w").place(x=0, y=1, width=100)
        self.lbl_doc = tk.Label(resumen, text="365", bg=self.FONDO, fg="#d33b32",
                                font=("Segoe UI", 11, "bold"), anchor="e")
        self.lbl_doc.place(x=135, y=0, width=66)
        self.lbl_articulos = tk.Label(resumen, bg=self.FONDO, fg=self.TEXTO,
                                      font=("Segoe UI", 7), anchor="w")
        self.lbl_articulos.place(x=0, y=23, width=200)
        self.lbl_subtotal = tk.Label(resumen, bg=self.FONDO, fg=self.TEXTO,
                                     font=("Segoe UI", 7), anchor="w")
        self.lbl_subtotal.place(x=0, y=41, width=200)
        self.lbl_impuesto = tk.Label(resumen, bg=self.FONDO, fg=self.TEXTO,
                                     font=("Segoe UI", 7), anchor="w")
        self.lbl_impuesto.place(x=0, y=59, width=200)

    def _crear_tabla(self):
        cuerpo = tk.Frame(self, bg="white", highlightbackground=self.BORDE, highlightthickness=1)
        cuerpo.grid(row=4, column=0, sticky="nsew", padx=14)
        cuerpo.rowconfigure(0, weight=1)
        cuerpo.columnconfigure(0, weight=1)

        self.tabla = ttk.Treeview(cuerpo, columns=("codigo", "articulo", "precio", "cantidad", "total"), show="headings", style="POS.Treeview", selectmode="browse")
        columnas = (("codigo", "CÓDIGO", 110, "w"), ("articulo", "ARTÍCULO", 520, "w"), ("precio", "PRECIO", 150, "e"), ("cantidad", "CANTIDAD", 90, "center"), ("total", "TOTAL", 170, "e"))
        for clave, texto, ancho, ancla in columnas:
            self.tabla.heading(clave, text=texto, anchor=ancla)
            self.tabla.column(clave, width=ancho, minwidth=0, anchor=ancla, stretch=clave == "articulo")
        self.tabla.grid(row=0, column=0, sticky="nsew")
        self.tabla.bind("<Double-1>", lambda _evento: self.cambiar_cantidad())
        self.ent_busqueda = tk.Entry(cuerpo, bg="#e1e4e8", fg="#263746", insertbackground="#263746",
                                     relief="flat", bd=0, font=("Segoe UI", 9, "bold"), takefocus=True)
        # Fila gris limpia, inmediatamente debajo del encabezado de columnas.
        self.ent_busqueda.bind("<Return>", self._seleccionar_producto_encontrado)
        # Muestra coincidencias mientras se escribe; solo filtra el catálogo
        # ya cargado, sin consultar la base de datos por cada tecla.
        self.ent_busqueda.bind("<KeyRelease>", self._actualizar_resultados_busqueda)
        self.ent_busqueda.bind("<Down>", lambda _evento: self._mover_resultado(1))
        self.ent_busqueda.bind("<Up>", lambda _evento: self._mover_resultado(-1))
        self.ent_busqueda.bind("<FocusIn>", lambda _evento: self.ent_busqueda.tkraise())
        self.linea_busqueda = tk.Frame(cuerpo, bg="#cbd1d8", height=1)
        self.panel_resultados = tk.Frame(cuerpo, bg="#f8f8f8", bd=1, relief="solid")
        self.resultados_busqueda = ttk.Treeview(
            self.panel_resultados,
            columns=("codigo", "descripcion", "referencia", "existencia", "precio"),
            show="headings", height=4, style="POS.Search.Treeview", selectmode="browse")
        for clave, texto, ancho, ancla in (
            ("codigo", "CÓDIGO", 165, "w"), ("descripcion", "DESCRIPCIÓN", 520, "w"),
            ("referencia", "REFERENCIA", 150, "w"), ("existencia", "EXISTENCIA", 110, "e"),
            ("precio", "PRECIO", 150, "e")):
            self.resultados_busqueda.heading(clave, text=texto, anchor=ancla)
            self.resultados_busqueda.column(clave, width=ancho, minwidth=0, anchor=ancla, stretch=clave == "descripcion")
        self.resultados_busqueda.pack(fill="both", expand=True)
        self.resultados_busqueda.bind("<Double-1>", self._seleccionar_resultado)
        self.resultados_busqueda.bind("<Return>", self._seleccionar_resultado)
        self.panel_resultados.place_forget()
        tk.Label(cuerpo, text="FACTRA", bg="white", fg="#edf3f8", font=("Segoe UI", 50, "bold")).place(relx=.5, rely=.55, anchor="center")
        self.tabla.bind("<Configure>", lambda _evento: self.after_idle(self._alinear_busqueda))

    def _crear_panel_inferior(self):
        panel = tk.Frame(self, bg=self.FONDO, height=112)
        panel.grid(row=5, column=0, sticky="ew", padx=14, pady=(6, 0))
        panel.grid_propagate(False)
        fondo = tk.Canvas(panel, bg=self.FONDO, highlightthickness=0, bd=0)
        fondo.place(x=0, y=0, relwidth=1, relheight=1)

        def redibujar(evento):
            fondo.delete("panel")
            w, h, r = evento.width, evento.height, 17
            fondo.create_rectangle(r, 0, w - r, h, fill=self.AZUL_PANEL, outline=self.AZUL_PANEL, tags="panel")
            fondo.create_rectangle(0, r, w, h - r, fill=self.AZUL_PANEL, outline=self.AZUL_PANEL, tags="panel")
            for x, y in ((0, 0), (w - 2 * r, 0), (0, h - 2 * r), (w - 2 * r, h - 2 * r)):
                fondo.create_oval(x, y, x + 2 * r, y + 2 * r, fill=self.AZUL_PANEL,
                                  outline=self.AZUL_PANEL, tags="panel")

        fondo.bind("<Configure>", redibujar)
        datos = tk.Frame(panel, bg=self.AZUL_PANEL)
        datos.place(x=16, y=4, relwidth=.58, height=102)
        self.lbl_ultimo_nombre = tk.Label(datos, bg=self.AZUL_PANEL, fg="white", anchor="w",
                                          font=("Segoe UI", 22, "bold italic"))
        self.lbl_ultimo_nombre.place(x=0, y=2, relwidth=1, height=31)
        self.lbl_ultimo_detalle = tk.Label(datos, bg=self.AZUL_PANEL, fg="white", anchor="w",
                                           justify="left", font=("Segoe UI", 8, "italic"))
        self.lbl_ultimo_detalle.place(x=0, y=35, relwidth=1, height=31)
        self.lbl_ultimo_estado = tk.Label(datos, bg=self.AZUL_PANEL, fg="white", anchor="w",
                                          font=("Segoe UI", 7, "italic"))
        self.lbl_ultimo_estado.place(x=0, y=72, relwidth=1, height=18)
        self.lbl_total = tk.Label(panel, text="RD$ 0.00", bg=self.AZUL_PANEL, fg="white",
                                  font=("Segoe UI", 42, "bold"), padx=8)
        self.lbl_total.place(relx=1, x=-14, rely=.5, anchor="e")

    @staticmethod
    def dinero(valor):
        return f"RD$ {valor:,.2f}"

    def _maximizar(self):
        try:
            self.state("normal" if self.state() == "zoomed" else "zoomed")
        except tk.TclError:
            pass

    def _actualizar_reloj(self):
        if self.winfo_exists():
            self.lbl_hora.config(text=dt.datetime.now().strftime("%H:%M:%S"))
            self.after(1000, self._actualizar_reloj)

    def _actualizar_resumen(self):
        for item in self.tabla.get_children():
            self.tabla.delete(item)
        # Fila vacía de búsqueda antes de los productos.
        self.tabla.insert("", "end", iid="__busqueda__", values=("", "", "", "", ""), tags=("busqueda",))
        subtotal = impuesto = total = 0.0
        for indice, item in enumerate(self.carrito):
            importe = item["precio"] * item["cantidad"]
            base = importe / (1 + self.impuesto)
            impuesto += importe - base
            subtotal += base
            total += importe
            self.tabla.insert("", "end", iid=item["codigo"], values=(item["codigo"], item["articulo"].upper(), self.dinero(item["precio"]), f"{item['cantidad']:.2f}", self.dinero(importe)), tags=("par" if indice % 2 == 0 else "impar",))
        self.tabla.tag_configure("par", background="white")
        self.tabla.tag_configure("impar", background="#eef1f4")
        self.tabla.tag_configure("busqueda", background="white")
        self.lbl_articulos.config(text=f"Artículos: {sum(i['cantidad'] for i in self.carrito)}")
        self.lbl_subtotal.config(text=f"Subtotal: {subtotal:,.2f}")
        self.lbl_impuesto.config(text=f"Impuesto: {impuesto:,.2f}")
        self.lbl_total.config(text=self.dinero(total))
        ultimo = next((i for i in self.carrito if i["articulo"] == self.ultimo_producto), None)
        self.lbl_ultimo_nombre.config(text=self.ultimo_producto.upper())
        self.lbl_ultimo_detalle.config(text=f"Valor total producto\n{self.dinero(ultimo['precio']) if ultimo else 'RD$ 0.00'}")
        self.lbl_ultimo_estado.config(text="Facturas en espera: 0   |   Clientes atendidos: 0   |   Estación: PRUEBA")
        self.after_idle(self._alinear_busqueda)

    def _alinear_busqueda(self):
        """Coloca el buscador único sobre la fila vacía bajo el encabezado."""
        if not self.winfo_exists() or not self.tabla.exists("__busqueda__"):
            return
        caja = self.tabla.bbox("__busqueda__", "codigo")
        if not caja:
            return
        _x, y, _ancho, alto = caja
        ancho = self.tabla.winfo_width()
        self.linea_busqueda.place(x=0, y=max(0, y - 1), width=ancho, height=1)
        self.ent_busqueda.place(x=2, y=y + 1, width=max(100, ancho - 4), height=max(16, alto - 2))
        self.ent_busqueda.tkraise()
        self.ent_busqueda.icursor(tk.END)

    def _seleccionado(self):
        seleccion = self.tabla.selection()
        return seleccion[0] if seleccion and seleccion[0] != "__busqueda__" else None

    def _seleccionar_producto_encontrado(self, _evento=None):
        texto = self.ent_busqueda.get().strip().lower()
        if not texto or texto == "buscar producto por código, nombre o descripción":
            return "break"
        if not self.resultados_mostrados:
            self._actualizar_resultados_busqueda()
            if not self.resultados_busqueda.get_children():
                messagebox.showinfo("Búsqueda", "No se encontró ningún producto.", parent=self)
                return "break"
            primera = self.resultados_busqueda.get_children()[0]
            self.resultados_busqueda.selection_set(primera)
            self.resultados_busqueda.focus(primera)
            self.resultados_mostrados = True
            return "break"
        seleccion = self.resultados_busqueda.selection()
        if seleccion:
            self._agregar_producto_encontrado(seleccion[0])
            return "break"
        return "break"

    def _agregar_producto_encontrado(self, codigo):
        """Agrega únicamente el producto que el usuario seleccionó del resultado."""
        producto = next((p for p in self.productos if p["codigo"] == codigo), None)
        if not producto:
            return
        existente = next((i for i in self.carrito if i["codigo"] == codigo), None)
        if existente:
            existente["cantidad"] += 1
        else:
            self.carrito.append({**producto, "cantidad": 1})
        self.ultimo_producto = producto["articulo"]
        self._actualizar_resumen()
        self.tabla.selection_set(codigo)
        self.tabla.focus(codigo)
        self.tabla.see(codigo)
        self.ent_busqueda.delete(0, tk.END)
        self.panel_resultados.place_forget()
        self.resultados_mostrados = False
        self.after(80, self._enfocar_busqueda)

    def _marcar_busqueda_modificada(self, _evento=None):
        self.resultados_mostrados = False
        self.panel_resultados.place_forget()

    def _mover_resultado(self, desplazamiento):
        """Permite recorrer con flechas los resultados visibles."""
        filas = self.resultados_busqueda.get_children()
        if not filas:
            return "break"
        seleccion = self.resultados_busqueda.selection()
        if seleccion and seleccion[0] in filas:
            indice = filas.index(seleccion[0]) + desplazamiento
        else:
            indice = 0 if desplazamiento > 0 else len(filas) - 1
        indice = max(0, min(indice, len(filas) - 1))
        fila = filas[indice]
        self.resultados_busqueda.selection_set(fila)
        self.resultados_busqueda.focus(fila)
        self.resultados_busqueda.see(fila)
        self.resultados_busqueda.focus_set()
        self.resultados_mostrados = True
        return "break"

    def _actualizar_resultados_busqueda(self, _evento=None):
        self.resultados_mostrados = False
        texto = self.ent_busqueda.get().strip().lower()
        for fila in self.resultados_busqueda.get_children():
            self.resultados_busqueda.delete(fila)
        if not texto or texto == "buscar producto por código, nombre o descripción":
            self.panel_resultados.place_forget()
            return False
        encontrados = [p for p in self.productos if texto in p["codigo"].lower()
                       or texto in p["articulo"].lower()
                       or texto in p.get("descripcion", "").lower()]
        for producto in encontrados:
            self.resultados_busqueda.insert("", "end", iid=producto["codigo"], values=(
                producto["codigo"], producto.get("descripcion", producto["articulo"]),
                producto["codigo"], "1,00", self.dinero(producto["precio"])))
        if encontrados:
            caja = self.tabla.bbox("__busqueda__", "codigo")
            if caja:
                _x, y, _ancho, alto = caja
                self.panel_resultados.place(x=2, y=y + alto + 2,
                                             width=max(300, self.tabla.winfo_width() - 4),
                                             height=min(145, 28 + 22 * len(encontrados)))
                self.panel_resultados.lift()
        else:
            self.panel_resultados.place_forget()
        return bool(encontrados)

    def _seleccionar_resultado(self, _evento=None):
        seleccion = self.resultados_busqueda.selection()
        if seleccion:
            producto = next((p for p in self.productos if p["codigo"] == seleccion[0]), None)
            if producto:
                self.ent_busqueda.delete(0, tk.END)
                self._agregar_producto_encontrado(producto["codigo"])
                self.resultados_mostrados = False
        return "break"

    def agregar(self):
        producto = self.productos[0]
        existente = next((i for i in self.carrito if i["codigo"] == producto["codigo"]), None)
        if existente:
            existente["cantidad"] += 1
        else:
            self.carrito.append({**producto, "cantidad": 1})
        self.ultimo_producto = producto["articulo"]
        self._actualizar_resumen()
        self.tabla.selection_set(producto["codigo"])

    def remover(self):
        codigo = self._seleccionado()
        if codigo:
            self.carrito = [i for i in self.carrito if i["codigo"] != codigo]
            self._actualizar_resumen()

    def abrir_caja(self):
        from abrir_caja_modal import AbrirCajaModal
        self._guardar_ventana_secundaria(
            AbrirCajaModal(self, usuario=self.usuario, callback_exito=lambda *_args: self._actualizar_contexto())
        )

    def _actualizar_contexto(self):
        try:
            caja, almacen = self.servicio_ventas.obtener_contexto(self.usuario)
            self.caja_id, self.almacen_id = caja, almacen
        except Exception:
            self.caja_id = self.almacen_id = None

    def facturar(self):
        if not self.carrito:
            messagebox.showwarning("Venta", "Agregue al menos un producto antes de facturar.", parent=self)
            return
        self._actualizar_contexto()
        if not self.caja_id:
            messagebox.showwarning("Caja cerrada", "Debe abrir una caja antes de facturar.", parent=self)
            self.abrir_caja()
            return
        from pago_modal import RealizarPagoModal
        total = sum(item["precio"] * item["cantidad"] for item in self.carrito)
        self._guardar_ventana_secundaria(
            RealizarPagoModal(self, total_pagar=total, callback_confirm=self._confirmar_venta)
        )

    def _confirmar_venta(self, medio, monto_recibido, _cambio, total, cuenta):
        try:
            items = [ItemVenta(
                item["id"], item["articulo"], int(item["cantidad"]),
                Decimal(str(item["precio"])), Decimal(str(item.get("costo", 0))))
                for item in self.carrito
            ]
            solicitud = SolicitudVenta(
                cliente=self.codigo_cliente.get().strip() or "Consumidor Final",
                items=items,
                medio_pago=medio,
                usuario=self.usuario,
                caja_id=self.caja_id,
                almacen_id=getattr(self, "almacen_id", None),
                cuenta_destino=cuenta or None,
                total=Decimal(str(total)),
                monto_recibido=Decimal(str(monto_recibido)),
            )
            resultado = self.servicio_ventas.realizar_venta(solicitud)
            self.lbl_doc.config(text=str(resultado.numero_factura))
            messagebox.showinfo("Venta registrada", f"Factura #{resultado.numero_factura} registrada correctamente.", parent=self)
            self.carrito.clear()
            self.ultimo_producto = "Ningún producto agregado"
            self._actualizar_resumen()
        except Exception as error:
            messagebox.showerror("Error de venta", f"No se pudo registrar la venta:\n{error}", parent=self)

    def limpiar(self):
        self.carrito.clear()
        self.ultimo_producto = "Ningún producto agregado"
        self._actualizar_resumen()

    def cambiar_cantidad(self):
        codigo = self._seleccionado()
        item = next((i for i in self.carrito if i["codigo"] == codigo), None)
        if item:
            item["cantidad"] += 1
            self.ultimo_producto = item["articulo"]
            self._actualizar_resumen()

    def buscar(self):
        self.ent_busqueda.focus_set()
        self.ent_busqueda.tkraise()
        self.ent_busqueda.icursor(tk.END)

    def buscar_cliente(self):
        from buscar_cliente_modal import BuscarClienteModal
        self._guardar_ventana_secundaria(
            BuscarClienteModal(self, callback_select=self.seleccionar_cliente_desde_modal)
        )

    def seleccionar_cliente_desde_modal(self, cliente):
        """Coloca el cliente elegido en la venta actual."""
        nombre = str(cliente[1] or "Consumidor Final").strip()
        identificacion = str(cliente[3] or "").strip()
        self.codigo_cliente.delete(0, tk.END)
        self.codigo_cliente.insert(0, nombre)
        self.lbl_cliente_nombre.config(text=identificacion or nombre)
        # El siguiente paso natural en caja es agregar productos: devolver el
        # foco al buscador cuando el modal termina de liberar el teclado.
        self.after(150, self._enfocar_busqueda)

    def mostrar_demo(self):
        messagebox.showinfo("Prototipo visual", "Esta acción es solamente demostrativa y no realiza operaciones reales.", parent=self)


if __name__ == "__main__":
    raiz = tk.Tk()
    raiz.withdraw()
    ventana = Prueba(raiz)
    ventana.protocol("WM_DELETE_WINDOW", raiz.destroy)
    raiz.mainloop()
