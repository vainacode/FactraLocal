import datetime
import os
import sys
import tkinter as tk
from tkinter import messagebox, ttk, simpledialog
from PIL import Image, ImageTk
from window_utils import posicionar_ventana
from dominio.ventas.excepciones import ErrorNegocio
from dominio.ventas.modelos import ItemVenta, SolicitudVenta
from servicios.servicio_ventas import ServicioVentas
from servicios.servicio_caja import ServicioCaja

class Ventas(tk.Toplevel):
    def __init__(self, parent, usuario="", rol="Cajero"):
        super().__init__(parent)
        self.parent = parent
        self.usuario = usuario
        self.rol = rol
        self.title("Punto de Venta Versión 4.4.7")
        posicionar_ventana(self, 1100, 650, parent)
        self.resizable(False, False)
        self.configure(bg="#C6D9E3")
        self.transient(parent)
        self.grab_set()
        try:
            self.iconbitmap(self.rutas('icono.ico'))
        except Exception:
            pass

        self.db_name = "database.db"
        self.servicio_ventas = ServicioVentas()
        self.servicio_caja = ServicioCaja()
        self.images = {}
        self.items_carrito = []
        self.factura_pendiente_retomada = None
        self.caja_id = self.obtener_caja_abierta()
        self.estado_caja = "ABIERTA" if self.caja_id else "CERRADA"
        self.almacen_id = self.obtener_almacen_actual()
        self.numero_factura = self.obtener_siguiente_factura()

        self.widgets()
        self.actualizar_reloj()
        self.cargar_datos_iniciales()
        self.configurar_atajos()
        self.reintentar_pendientes_factrapi()
        self.actualizar_alerta_fiscal()

    def obtener_caja_abierta(self):
        try:
            caja, _ = self.servicio_ventas.obtener_contexto(self.usuario)
            return caja
        except Exception:
            return None

    def validar_caja_activa(self):
        self.caja_id = self.obtener_caja_abierta()
        if not self.caja_id:
            self.estado_caja = "CERRADA"
            self.lbl_estado_caja.config(text="CERRADA", fg="#DC2626")
            messagebox.showwarning(
                "Caja cerrada",
                "Debe abrir una caja para este usuario antes de registrar ventas."
            )
            return False
        self.estado_caja = "ABIERTA"
        return True

    def rutas(self, ruta):
        try:
            rutabase = sys.__MEIPASS
        except Exception:
            rutabase = os.path.abspath(".")
        return os.path.join(rutabase, ruta)

    def obtener_siguiente_factura(self):
        try:
            return self.servicio_ventas.obtener_siguiente_factura()
        except Exception:
            return 1

    def obtener_almacen_actual(self):
        try:
            _, almacen = self.servicio_ventas.obtener_contexto(self.usuario)
            return almacen
        except Exception as error:
            # No vender usando el stock global si no se pudo leer el almacén
            # operativo: eso permitiría saltarse el control multi-almacén.
            raise RuntimeError(f"No se pudo leer el almacén operativo: {error}") from error

    def reintentar_pendientes_factrapi(self):
        """Reintenta en segundo plano los comprobantes e-CF que quedaron
        encolados (sin conexión/sin configurar) en una venta anterior.
        No bloquea la interfaz ni molesta al cajero si sigue sin haber
        conexión — solo actualiza en silencio lo que sí se pudo sincronizar."""
        import threading

        def trabajo():
            try:
                import factrapi_cliente
                factrapi_cliente.reintentar_comprobantes_pendientes()
                factrapi_cliente.reconciliar_comprobantes_pendientes()
            except Exception:
                pass

        threading.Thread(target=trabajo, daemon=True).start()

    def actualizar_alerta_fiscal(self):
        """Refresca secuencias y muestra avisos sin bloquear la venta."""
        import threading

        def trabajo():
            alertas = []
            try:
                import factrapi_cliente
                factrapi_cliente.refrescar_cache_secuencias()
                alertas = factrapi_cliente.obtener_alertas_secuencias()
            except Exception:
                # Sin FactrAPI configurada el modo informal sigue funcionando.
                pass
            try:
                self.after(0, lambda: self._mostrar_alerta_fiscal(alertas))
            except tk.TclError:
                pass

        threading.Thread(target=trabajo, daemon=True).start()
        self.after(300000, self.actualizar_alerta_fiscal)

    def _mostrar_alerta_fiscal(self, alertas):
        if not hasattr(self, "lbl_alerta_fiscal") or not self.lbl_alerta_fiscal.winfo_exists():
            return
        self.lbl_alerta_fiscal.config(
            text="  |  ".join(alertas[:2]) if alertas else "",
            fg="#B45309"
        )

    def widgets(self):
#============== 1. FRAME SUPERIOR (HEADER) =========================================================#
        frame_header = tk.Frame(self, bg="#DDE1E5", highlightbackground="#B8C4CE", highlightthickness=1)
        frame_header.pack()
        frame_header.place(x=0, y=0, width=1100, height=65)

        # Avatar y Cajero
        ruta_cajero = self.rutas("icono/cajero.png")
        if not os.path.exists(ruta_cajero):
            ruta_cajero = self.rutas("icono/user_icon.png")

        if os.path.exists(ruta_cajero):
            img_caj = Image.open(ruta_cajero).resize((36, 36), Image.Resampling.LANCZOS)
            self.images["cajero"] = ImageTk.PhotoImage(img_caj)
            lbl_caj_img = tk.Label(frame_header, image=self.images["cajero"], bg="#DDE1E5")
            lbl_caj_img.place(x=20, y=14)

        lbl_cajero_txt = tk.Label(
            frame_header,
            text=f"Cajero: {self.usuario}",
            font=("sans", 13, "bold"),
            bg="#DDE1E5",
            fg="#1E293B"
        )
        lbl_cajero_txt.place(x=62, y=20)

        # Título Central
        lbl_titulo = tk.Label(
            frame_header,
            text="VENTA DE PRODUCTOS",
            font=("sans", 24, "bold"),
            bg="#DDE1E5",
            fg="#1E293B"
        )
        lbl_titulo.place(relx=0.5, y=32, anchor="center")

        self.lbl_alerta_fiscal = tk.Label(
            frame_header, text="", font=("sans", 8, "bold"),
            bg="#DDE1E5", fg="#B45309", anchor="center"
        )
        self.lbl_alerta_fiscal.place(x=350, y=51, width=540, height=13)

        # Botón Abrir Caja
        ruta_abrir = self.rutas("icono/abrircaja.png")
        if os.path.exists(ruta_abrir):
            img_ab = Image.open(ruta_abrir).resize((22, 22), Image.Resampling.LANCZOS)
            self.images["abrircaja"] = ImageTk.PhotoImage(img_ab)
            ico_ab = self.images["abrircaja"]
        else:
            ico_ab = None

        btn_abrir_caja = tk.Button(
            frame_header,
            text="  Abrir Caja",
            image=ico_ab,
            compound=tk.LEFT,
            font=("sans", 10, "bold"),
            bg="#DDE1E5",
            fg="#1E293B",
            activebackground="#DDE1E5",
            bd=0,
            cursor="hand2",
            command=self.abrir_caja_flujo
        )
        btn_abrir_caja.place(x=920, y=6, width=150, height=24)

        # Botón Cerrar Caja
        ruta_cerrar = self.rutas("icono/cerrarcaja.png")
        if os.path.exists(ruta_cerrar):
            img_ce = Image.open(ruta_cerrar).resize((22, 22), Image.Resampling.LANCZOS)
            self.images["cerrarcaja"] = ImageTk.PhotoImage(img_ce)
            ico_ce = self.images["cerrarcaja"]
        else:
            ico_ce = None

        btn_cerrar_caja = tk.Button(
            frame_header,
            text="  Cerrar Caja",
            image=ico_ce,
            compound=tk.LEFT,
            font=("sans", 10, "bold"),
            bg="#DDE1E5",
            fg="#1E293B",
            activebackground="#DDE1E5",
            bd=0,
            cursor="hand2",
            command=self.cerrar_caja_flujo
        )
        btn_cerrar_caja.place(x=920, y=34, width=150, height=24)

#============== 2. BARRA DE CLIENTE, BOTONES RÁPIDOS Y RELOJ =======================================#
        lbl_cli = tk.Label(self, text="Cliente:", font=("sans", 13, "bold"), bg="#C6D9E3", fg="#1E293B")
        lbl_cli.place(x=35, y=77)

        self.cmb_cliente = ttk.Combobox(self, font=("sans", 11), state="readonly")
        self.cmb_cliente.place(x=130, y=76, width=310, height=28)

        # 6 Botones rápidos al lado del combo de cliente
        iconos_cli = [
            ("agregarcliente.png", self.nuevo_cliente),
            ("clientedefecto.png", self.cliente_defecto),
            ("buscarproducto.png", self.buscar_cliente),
            ("impresora.png", self.config_impresora),
            ("factura.png", self.ver_facturas_abiertas),
            ("descuento.png", self.aplicar_descuento),
        ]

        x_btn = 450
        for ico_file, cmd in iconos_cli:
            ruta_i = self.rutas(f"icono/{ico_file}")
            if not os.path.exists(ruta_i):
                ruta_i = self.rutas("icono/buscar.png")

            if os.path.exists(ruta_i):
                img_i = Image.open(ruta_i).resize((24, 24), Image.Resampling.LANCZOS)
                self.images[ico_file] = ImageTk.PhotoImage(img_i)
                ico_btn = self.images[ico_file]
            else:
                ico_btn = None

            btn_i = tk.Button(
                self,
                image=ico_btn,
                bg="#EBEFF2",
                relief="raised",
                bd=1,
                cursor="hand2",
                command=cmd
            )
            btn_i.place(x=x_btn, y=73, width=34, height=34)
            x_btn += 38

        # Fecha (Calendario)
        ruta_cal = self.rutas("icono/calendario.png")
        if os.path.exists(ruta_cal):
            img_cal = Image.open(ruta_cal).resize((22, 22), Image.Resampling.LANCZOS)
            self.images["cal_v"] = ImageTk.PhotoImage(img_cal)
            lbl_cal = tk.Label(self, image=self.images["cal_v"], bg="#C6D9E3")
            lbl_cal.place(x=730, y=78)

        self.lbl_fecha = tk.Label(self, text="", font=("sans", 11, "bold"), bg="#C6D9E3", fg="#1E293B")
        self.lbl_fecha.place(x=756, y=80)

        # Hora (Reloj)
        ruta_clk = self.rutas("icono/hora.png")
        if os.path.exists(ruta_clk):
            img_clk = Image.open(ruta_clk).resize((22, 22), Image.Resampling.LANCZOS)
            self.images["clk_v"] = ImageTk.PhotoImage(img_clk)
            lbl_clk = tk.Label(self, image=self.images["clk_v"], bg="#C6D9E3")
            lbl_clk.place(x=875, y=78)

        self.lbl_hora = tk.Label(self, text="", font=("sans", 11, "bold"), bg="#C6D9E3", fg="#1E293B")
        self.lbl_hora.place(x=902, y=80)

#============== 3. RECUADRO DE ENTRADA DE PRODUCTOS ================================================#
        frame_input = tk.Frame(self, bg="#DDE1E5", highlightbackground="#B8C4CE", highlightthickness=1)
        frame_input.place(x=20, y=115, width=910, height=115)

        # Fila 1: Código (F1), Cantidad (F2), Factura: #
        lbl_f1 = tk.Label(
            frame_input,
            text="Código:\n(F1)",
            font=("sans", 11, "bold"),
            bg="#DDE1E5",
            fg="#1E293B",
            justify="center"
        )
        lbl_f1.place(x=15, y=6)

        self.ent_codigo = ttk.Entry(frame_input, font=("sans", 12))
        self.ent_codigo.place(x=110, y=10, width=360, height=32)
        self.ent_codigo.bind("<Return>", lambda e: self.buscar_y_agregar_por_codigo())

        lbl_f2 = tk.Label(
            frame_input,
            text="Cantidad:\n(F2)",
            font=("sans", 11, "bold"),
            bg="#DDE1E5",
            fg="#1E293B",
            justify="center"
        )
        lbl_f2.place(x=485, y=6)

        self.ent_cantidad = ttk.Entry(frame_input, font=("sans", 12), justify="center")
        self.ent_cantidad.place(x=580, y=10, width=80, height=32)
        self.ent_cantidad.insert(0, "1")
        self.ent_cantidad.bind("<Return>", lambda e: self.buscar_y_agregar_por_codigo())

        # Badge Factura
        ruta_fac_ico = self.rutas("icono/factura.png")
        if os.path.exists(ruta_fac_ico):
            img_fac = Image.open(ruta_fac_ico).resize((24, 24), Image.Resampling.LANCZOS)
            self.images["fac_ico"] = ImageTk.PhotoImage(img_fac)
            lbl_fac_img = tk.Label(frame_input, image=self.images["fac_ico"], bg="#DDE1E5")
            lbl_fac_img.place(x=710, y=14)

        self.lbl_num_factura = tk.Label(
            frame_input,
            text=f"Factura:   {self.numero_factura}",
            font=("sans", 12, "bold"),
            bg="#DDE1E5",
            fg="#1E293B"
        )
        self.lbl_num_factura.place(x=745, y=16)

        # Fila 2: Producto: Combobox, Stock:
        lbl_prod_tag = tk.Label(
            frame_input,
            text="Producto:",
            font=("sans", 12, "bold"),
            bg="#DDE1E5",
            fg="#1E293B"
        )
        lbl_prod_tag.place(x=15, y=62)

        self.cmb_producto = ttk.Combobox(frame_input, font=("sans", 11), state="normal")
        self.cmb_producto.place(x=110, y=60, width=550, height=30)
        self.cmb_producto.bind("<<ComboboxSelected>>", self.al_seleccionar_producto_combo)
        self.cmb_producto.bind("<KeyRelease>", self.filtrar_productos)
        self.cmb_producto.bind("<Return>", lambda e: self.buscar_producto_en_lista())

        self.btn_buscar_producto = tk.Button(
            frame_input, text="Buscar", font=("sans", 10, "bold"),
            bg="#EBEFF2", fg="#1E293B", relief="raised", bd=1,
            command=self.buscar_producto_en_lista, cursor="hand2"
        )
        self.btn_buscar_producto.place(x=665, y=60, width=88, height=30)

        self.lbl_stock_disp = tk.Label(
            frame_input,
            text="Stock:",
            font=("sans", 12, "bold"),
            bg="#DDE1E5",
            fg="#1E293B"
        )
        self.lbl_stock_disp.place(x=765, y=62)

#============== 4. BARRA DE BOTONES DE ACCIÓN (F3 - F7) ============================================#
        frame_barra_btns = tk.Frame(self, bg="#B8C4CE", height=38)
        frame_barra_btns.place(x=20, y=235, width=910, height=38)

        acciones_tabla = [
            ("Agregar (F3)", "agregar.png", self.agregar_producto_seleccionado),
            ("Editar (F4)", "editar.png", self.editar_item_carrito),
            ("Eliminar (F5)", "eliminar.png", self.eliminar_item_carrito),
            ("Limpiar (F6)", "limpiar.png", self.limpiar_carrito),
            ("Precio (F7)", "especial.png", self.precio_especial),
        ]

        x_act = 0
        w_act = 182
        for txt, ico_f, cmd in acciones_tabla:
            ruta_i = self.rutas(f"icono/{ico_f}")
            if not os.path.exists(ruta_i):
                ruta_i = self.rutas("icono/precio.png")

            if os.path.exists(ruta_i):
                img_i = Image.open(ruta_i).resize((22, 22), Image.Resampling.LANCZOS)
                self.images[f"act_{txt}"] = ImageTk.PhotoImage(img_i)
                ico_btn = self.images[f"act_{txt}"]
            else:
                ico_btn = None

            btn_t = tk.Button(
                frame_barra_btns,
                text=f"  {txt}",
                image=ico_btn,
                compound=tk.LEFT,
                font=("sans", 9, "bold"),
                bg="#EBEFF2",
                fg="#1E293B",
                activebackground="#D5E0E8",
                relief="raised",
                bd=1,
                cursor="hand2",
                command=cmd
            )
            btn_t.place(x=x_act, y=0, width=w_act, height=38)
            x_act += w_act

#============== 5. TABLA DE PRODUCTOS EN VENTA =====================================================#
        style = ttk.Style()
        style.configure("Ventas.Treeview.Heading", font=("sans", 9, "bold"), background="#E0E6ED")
        style.configure("Ventas.Treeview", font=("sans", 10), rowheight=24)

        self.tabla = ttk.Treeview(
            self,
            columns=("producto", "precio", "cantidad", "impuesto", "total"),
            show="headings",
            style="Ventas.Treeview"
        )
        self.tabla.place(x=20, y=273, width=895, height=245)

        self.tabla.heading("producto", text="Producto", anchor="center")
        self.tabla.heading("precio", text="Precio c/u", anchor="center")
        self.tabla.heading("cantidad", text="Cantidad", anchor="center")
        self.tabla.heading("impuesto", text="Impuesto", anchor="center")
        self.tabla.heading("total", text="Total", anchor="center")

        self.tabla.column("producto", width=420, anchor="w")
        self.tabla.column("precio", width=120, anchor="center")
        self.tabla.column("cantidad", width=95, anchor="center")
        self.tabla.column("impuesto", width=120, anchor="center")
        self.tabla.column("total", width=140, anchor="center")

        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.tabla.yview)
        self.tabla.configure(yscrollcommand=scrollbar.set)
        scrollbar.place(x=915, y=273, height=245)

#============== 6. PANELES INFERIORES: RESUMEN, INFORMACIÓN Y TOTAL A PAGAR =========================#
        # Resumen de la compra
        frame_resumen = tk.LabelFrame(
            self,
            text="RESUMEN DE LA COMPRA",
            font=("sans", 9, "bold"),
            bg="#C6D9E3",
            fg="#1E293B"
        )
        frame_resumen.place(x=20, y=528, width=225, height=110)

        lbl_sub = tk.Label(frame_resumen, text="Subtotal:", font=("sans", 10, "bold"), bg="#C6D9E3", fg="#334155")
        lbl_sub.place(x=10, y=10)
        self.lbl_subtotal_val = tk.Label(frame_resumen, text="RD$ 0.00", font=("sans", 10, "bold"), bg="#C6D9E3", fg="#1E293B")
        self.lbl_subtotal_val.place(x=85, y=10)

        lbl_imp = tk.Label(frame_resumen, text="Impuesto:", font=("sans", 10, "bold"), bg="#C6D9E3", fg="#334155")
        lbl_imp.place(x=10, y=45)
        self.lbl_impuesto_val = tk.Label(frame_resumen, text="RD$ 0.00", font=("sans", 10, "bold"), bg="#C6D9E3", fg="#1E293B")
        self.lbl_impuesto_val.place(x=85, y=45)

        # Información
        frame_info = tk.LabelFrame(
            self,
            text="INFORMACIÓN",
            font=("sans", 9, "bold"),
            bg="#C6D9E3",
            fg="#1E293B"
        )
        frame_info.place(x=255, y=528, width=210, height=110)

        lbl_art = tk.Label(frame_info, text="Total Artículos:", font=("sans", 10, "bold"), bg="#C6D9E3", fg="#334155")
        lbl_art.place(x=10, y=10)
        self.lbl_articulos_val = tk.Label(frame_info, text="0", font=("sans", 10, "bold"), bg="#C6D9E3", fg="#1E293B")
        self.lbl_articulos_val.place(x=120, y=10)

        lbl_caj_tag = tk.Label(frame_info, text="Estado Caja:", font=("sans", 10, "bold"), bg="#C6D9E3", fg="#334155")
        lbl_caj_tag.place(x=10, y=45)
        self.lbl_estado_caja = tk.Label(frame_info, text="ABIERTA", font=("sans", 10, "bold"), bg="#C6D9E3", fg="#166534")
        self.lbl_estado_caja.place(x=105, y=45)

        # TOTAL A PAGAR (Recuadro Grande Gris)
        frame_total = tk.Frame(
            self,
            bg="#DDE1E5",
            highlightbackground="#B8C4CE",
            highlightthickness=1
        )
        frame_total.place(x=475, y=528, width=455, height=110)

        lbl_total_banner = tk.Label(
            frame_total,
            text="TOTAL A PAGAR",
            font=("sans", 11, "bold"),
            bg="#DDE1E5",
            fg="#1E293B"
        )
        lbl_total_banner.place(relx=0.5, y=16, anchor="center")

        # Moneda dorada (moneda.png)
        ruta_coin = self.rutas("icono/moneda.png")
        if not os.path.exists(ruta_coin):
            ruta_coin = self.rutas("icono/precio.png")

        if os.path.exists(ruta_coin):
            img_c = Image.open(ruta_coin).resize((46, 46), Image.Resampling.LANCZOS)
            self.images["coin_tot"] = ImageTk.PhotoImage(img_c)
            lbl_coin_img = tk.Label(frame_total, image=self.images["coin_tot"], bg="#DDE1E5")
            lbl_coin_img.place(x=45, y=40)
        else:
            lbl_coin_img = tk.Label(frame_total, text="💰", font=("sans", 24), bg="#DDE1E5")
            lbl_coin_img.place(x=45, y=40)

        self.lbl_gran_total = tk.Label(
            frame_total,
            text="RD$ 0.00",
            font=("sans", 26, "bold"),
            bg="#DDE1E5",
            fg="#1E293B"
        )
        self.lbl_gran_total.place(x=105, y=42)

#============== 7. COLUMNA LATERAL DERECHA (5 BOTONES) =============================================#
        frame_col_der = tk.Frame(
            self,
            bg="#C6D9E3",
            highlightbackground="#A9BFCE",
            highlightthickness=1
        )
        frame_col_der.place(x=945, y=115, width=135, height=523)

        botones_lateral = [
            ("Pagar", "pagar.png", self.procesar_pago),
            ("Ver\nVentas", "ver.png", self.ver_ventas_historial),
            ("Anular\nFactura", "anular.png", self.anular_factura),
            ("Guardar\nFactura", "facturaguardar.png", self.guardar_factura_pendiente),
            ("Facturas\nAbiertas", "facturapendiente.png", self.ver_facturas_abiertas),
        ]

        y_lat = 8
        for txt, ico_f, cmd in botones_lateral:
            ruta_i = self.rutas(f"icono/{ico_f}")
            if os.path.exists(ruta_i):
                img_i = Image.open(ruta_i).resize((32, 32), Image.Resampling.LANCZOS)
                self.images[f"lat_{ico_f}"] = ImageTk.PhotoImage(img_i)
                ico_btn = self.images[f"lat_{ico_f}"]
            else:
                ico_btn = None

            btn_lat = tk.Button(
                frame_col_der,
                text=txt,
                image=ico_btn,
                compound=tk.TOP,
                font=("sans", 9, "bold"),
                bg="#EBEFF2",
                fg="#1E293B",
                activebackground="#D5E0E8",
                relief="raised",
                bd=2,
                cursor="hand2",
                command=cmd
            )
            btn_lat.place(x=7, y=y_lat, width=119, height=94)
            y_lat += 103

    def configurar_atajos(self):
        self.bind("<F1>", lambda e: self.ent_codigo.focus_set())
        self.bind("<F2>", lambda e: self.ent_cantidad.focus_set())
        self.bind("<F3>", lambda e: self.agregar_producto_seleccionado())
        self.bind("<F4>", lambda e: self.editar_item_carrito())
        self.bind("<F5>", lambda e: self.eliminar_item_carrito())
        self.bind("<F6>", lambda e: self.limpiar_carrito())
        self.bind("<F7>", lambda e: self.precio_especial())
        self.bind("<F12>", lambda e: self.procesar_pago())

    def actualizar_reloj(self):
        ahora = datetime.datetime.now()
        self.lbl_fecha.config(text=ahora.strftime("%d-%m-%Y"))
        self.lbl_hora.config(text=ahora.strftime("%H:%M:%S"))
        self.after(1000, self.actualizar_reloj)

    def cargar_datos_iniciales(self):
        try:
            clis, defecto = self.servicio_ventas.listar_clientes()
            if not clis:
                clis = ["Cliente General", "Consumidor Final"]
            if "Cliente General" not in clis:
                clis.insert(0, "Cliente General")
            self.cmb_cliente["values"] = clis
            if defecto and defecto in clis:
                self.cmb_cliente.set(defecto)
            else:
                self.cmb_cliente.current(0)
            self.lista_productos_db = self.servicio_ventas.listar_productos_disponibles(self.almacen_id)
            self._actualizar_lista_productos()
        except Exception as e:
            print("Error cargando datos de ventas:", e)

    def _texto_producto(self, producto):
        return f"{producto[0]} - {producto[1]} ($ {producto[2]:,.2f})"

    def _actualizar_lista_productos(self, filtro=""):
        filtro = (filtro or "").strip().lower()
        productos = self.lista_productos_db
        if filtro:
            productos = [
                p for p in productos
                if filtro in str(p[0]).lower()
                or filtro in str(p[1]).lower()
                or (len(p) > 5 and p[5] and filtro in str(p[5]).lower())
            ]
        self.cmb_producto["values"] = [self._texto_producto(p) for p in productos]

    def filtrar_productos(self, event=None):
        """Permite encontrar un producto escribiendo nombre, código o barra."""
        if event and event.keysym in ("Return", "Tab", "Up", "Down", "Escape"):
            return
        self._actualizar_lista_productos(self.cmb_producto.get())

    def buscar_producto_en_lista(self):
        """Agrega la selección escrita en el buscador, aunque no se use QR."""
        texto = self.cmb_producto.get().strip()
        if not texto:
            self.ent_codigo.focus_set()
            return
        try:
            prod_id = int(texto.split(" - ", 1)[0])
            producto = next((p for p in self.lista_productos_db if int(p[0]) == prod_id), None)
        except (TypeError, ValueError):
            candidatos = [
                p for p in self.lista_productos_db
                if texto.lower() in str(p[1]).lower()
                or (len(p) > 5 and p[5] and texto.lower() in str(p[5]).lower())
            ]
            producto = candidatos[0] if len(candidatos) == 1 else None
        if producto:
            try:
                cantidad = int(self.ent_cantidad.get().strip() or 1)
            except ValueError:
                cantidad = 1
            self.agregar_a_carrito(producto, cantidad)
            self.cmb_producto.set("")
            self._actualizar_lista_productos()
            self.ent_cantidad.delete(0, tk.END)
            self.ent_cantidad.insert(0, "1")
            self.cmb_producto.focus_set()
        elif len(self.cmb_producto["values"]) > 1:
            messagebox.showwarning("Producto", "Hay varios productos. Seleccione uno de la lista.")
        else:
            messagebox.showerror("Producto no encontrado", f"No se encontró un producto con: {texto}")

    def al_seleccionar_producto_combo(self, event=None):
        sel = self.cmb_producto.get()
        if sel:
            try:
                prod_id = int(sel.split(" - ")[0])
                for p in self.lista_productos_db:
                    if p[0] == prod_id:
                        self.lbl_stock_disp.config(text=f"Stock: {p[3]}")
                        self.ent_codigo.delete(0, tk.END)
                        self.ent_codigo.insert(0, str(p[0]))
                        break
            except Exception:
                pass

    def buscar_y_agregar_por_codigo(self):
        codigo = self.ent_codigo.get().strip()
        if not codigo:
            return

        prod_encontrado = None
        for p in self.lista_productos_db:
            if str(p[0]) == codigo or (len(p) > 5 and p[5] and str(p[5]).lower() == codigo.lower()) or codigo.lower() in p[1].lower():
                prod_encontrado = p
                break

        if not prod_encontrado:
            try:
                prod_encontrado = self.servicio_ventas.buscar_producto(codigo, self.almacen_id)
            except Exception:
                pass

        if prod_encontrado:
            try:
                cant = int(self.ent_cantidad.get().strip() or 1)
            except ValueError:
                cant = 1
            self.agregar_a_carrito(prod_encontrado, cant)
            self.ent_codigo.delete(0, tk.END)
            self.ent_cantidad.delete(0, tk.END)
            self.ent_cantidad.insert(0, "1")
            self.ent_codigo.focus_set()
        else:
            messagebox.showerror("Error", f"No se encontró ningún producto con el código/nombre '{codigo}'.")

    def agregar_producto_seleccionado(self):
        sel = self.cmb_producto.get()
        if sel:
            try:
                prod_id = int(sel.split(" - ")[0])
                for p in self.lista_productos_db:
                    if p[0] == prod_id:
                        try:
                            cant = int(self.ent_cantidad.get().strip() or 1)
                        except ValueError:
                            cant = 1
                        self.agregar_a_carrito(p, cant)
                        return
            except Exception:
                pass
        self.buscar_y_agregar_por_codigo()

    def agregar_a_carrito(self, prod, cantidad):
        if self.estado_caja == "CERRADA":
            messagebox.showwarning("Caja Cerrada", "La caja está cerrada. Debe abrirla para registrar ventas.")
            return

        prod_id, nombre, precio, stock, costo = prod[0], prod[1], prod[2], prod[3], prod[4]

        if cantidad <= 0:
            messagebox.showwarning("Cantidad", "La cantidad debe ser mayor a cero.")
            return

        for item in self.items_carrito:
            if item["id"] == prod_id:
                if item["cantidad"] + cantidad > stock:
                    messagebox.showwarning("Stock Insuficiente", f"Stock disponible: {stock}. Ya tiene {item['cantidad']} en el carrito.")
                    return
                item["cantidad"] += cantidad
                item["total"] = item["cantidad"] * item["precio"]
                self.actualizar_tabla_carrito()
                return

        if cantidad > stock:
            messagebox.showwarning("Stock Insuficiente", f"Stock disponible para {nombre}: {stock}.")
            return

        item = {
            "id": prod_id,
            "producto": nombre,
            "precio": precio,
            "costo": costo,
            "cantidad": cantidad,
            "impuesto": 0.00,
            "total": cantidad * precio
        }
        self.items_carrito.append(item)
        self.actualizar_tabla_carrito()

    def actualizar_tabla_carrito(self):
        for row in self.tabla.get_children():
            self.tabla.delete(row)

        subtotal = 0.0
        total_arts = 0

        for item in self.items_carrito:
            subtotal += item["total"]
            total_arts += item["cantidad"]
            self.tabla.insert("", tk.END, values=(
                f"  {item['producto']}",
                f"{item['precio']:,.2f}",
                item["cantidad"],
                f"{item['impuesto']:,.2f}",
                f"{item['total']:,.2f}"
            ))

        self.lbl_subtotal_val.config(text=f"RD$ {subtotal:,.2f}")
        self.lbl_impuesto_val.config(text="RD$ 0.00")
        self.lbl_articulos_val.config(text=str(total_arts))
        self.lbl_gran_total.config(text=f"RD$ {subtotal:,.2f}")

    def editar_item_carrito(self):
        sel = self.tabla.selection()
        if not sel:
            messagebox.showwarning("Atención", "Seleccione un producto de la tabla para editar.")
            return

        idx = self.tabla.index(sel[0])
        item = self.items_carrito[idx]

        dialog = tk.Toplevel(self)
        dialog.title("Modificar Cantidad")
        posicionar_ventana(dialog, 300, 150, self)
        dialog.resizable(False, False)
        dialog.configure(bg="#C6D9E3")
        dialog.transient(self)
        dialog.grab_set()

        tk.Label(dialog, text=f"Producto: {item['producto']}", font=("sans", 10, "bold"), bg="#C6D9E3").pack(pady=8)
        tk.Label(dialog, text="Nueva cantidad:", font=("sans", 10), bg="#C6D9E3").pack()
        ent = ttk.Entry(dialog, font=("sans", 11), justify="center")
        ent.insert(0, str(item["cantidad"]))
        ent.pack(pady=5)
        ent.focus_set()

        def guardar_cant():
            try:
                nc = int(ent.get().strip())
                if nc > 0:
                    item["cantidad"] = nc
                    item["total"] = nc * item["precio"]
                    self.actualizar_tabla_carrito()
                    dialog.destroy()
                else:
                    messagebox.showerror("Error", "La cantidad debe ser mayor a 0.")
            except ValueError:
                messagebox.showerror("Error", "Ingrese un número válido.")

        tk.Button(dialog, text="Aceptar", command=guardar_cant, bg="#EBEFF2", font=("sans", 10, "bold")).pack(pady=5)

    def eliminar_item_carrito(self):
        sel = self.tabla.selection()
        if not sel:
            messagebox.showwarning("Atención", "Seleccione un producto de la tabla para eliminar.")
            return

        idx = self.tabla.index(sel[0])
        del self.items_carrito[idx]
        self.actualizar_tabla_carrito()

    def limpiar_carrito(self):
        if self.items_carrito:
            if messagebox.askyesno("Limpiar", "¿Desea vaciar el carrito actual?"):
                self.items_carrito.clear()
                self.factura_pendiente_retomada = None
                self.actualizar_tabla_carrito()

    def precio_especial(self):
        sel = self.tabla.selection()
        if not sel:
            messagebox.showwarning("Atención", "Seleccione un producto de la tabla para cambiar el precio.")
            return

        idx = self.tabla.index(sel[0])
        item = self.items_carrito[idx]

        dialog = tk.Toplevel(self)
        dialog.title("Precio Especial")
        posicionar_ventana(dialog, 300, 150, self)
        dialog.resizable(False, False)
        dialog.configure(bg="#C6D9E3")
        dialog.transient(self)
        dialog.grab_set()

        tk.Label(dialog, text=f"{item['producto']}", font=("sans", 10, "bold"), bg="#C6D9E3").pack(pady=8)
        tk.Label(dialog, text="Nuevo Precio:", font=("sans", 10), bg="#C6D9E3").pack()
        ent = ttk.Entry(dialog, font=("sans", 11), justify="center")
        ent.insert(0, str(item["precio"]))
        ent.pack(pady=5)
        ent.focus_set()

        def guardar_precio():
            try:
                np = float(ent.get().strip())
                if np >= 0:
                    item["precio"] = np
                    item["total"] = item["cantidad"] * np
                    self.actualizar_tabla_carrito()
                    dialog.destroy()
            except ValueError:
                messagebox.showerror("Error", "Ingrese un precio numérico válido.")

        tk.Button(dialog, text="Aplicar", command=guardar_precio, bg="#EBEFF2", font=("sans", 10, "bold")).pack(pady=5)

    def procesar_pago(self):
        if not self.validar_caja_activa():
            return
        if not self.items_carrito:
            messagebox.showwarning("Venta Vacía", "No hay productos en la tabla para cobrar.")
            return

        total_a_pagar = sum(item["total"] for item in self.items_carrito)
        from pago_modal import RealizarPagoModal

        def finalizar(medio="Efectivo", monto_rec=0.0, cambio=0.0, total_final=None, cuenta_destino=None):
            try:
                cliente_nom = self.cmb_cliente.get() or "Cliente General"
                items = [ItemVenta(
                    producto_id=item["id"], producto=item["producto"], cantidad=item["cantidad"],
                    precio=item["precio"], costo=item["costo"],
                ) for item in self.items_carrito]
                solicitud = SolicitudVenta(
                    cliente=cliente_nom, items=items, medio_pago=medio,
                    usuario=self.usuario, caja_id=self.caja_id, almacen_id=self.almacen_id,
                    cuenta_destino=cuenta_destino, total=total_final, monto_recibido=monto_rec,
                    factura_pendiente_retomada=self.factura_pendiente_retomada,
                )
                resultado = self.servicio_ventas.realizar_venta(solicitud)
                self.numero_factura = self.servicio_ventas.obtener_siguiente_factura()
                self.lbl_num_factura.config(text=f"Factura:   {self.numero_factura}")

                if resultado.fiscal_pendiente:
                    messagebox.showwarning(
                        "Facturación Electrónica Pendiente",
                        f"La venta #{resultado.numero_factura} se guardó correctamente, pero el e-CF "
                        f"no se pudo emitir todavía:\n\n{resultado.motivo_fiscal}\n\n"
                        "Quedó en cola para reintentarse automáticamente."
                    )
                elif resultado.estado_fiscal:
                    messagebox.showinfo(
                        "Factura Electrónica",
                        f"Venta #{resultado.numero_factura} emitida con e-NCF: {resultado.ncf_electronico}"
                    )
                elif resultado.ncf_tradicional:
                    messagebox.showinfo(
                        "NCF tradicional",
                        f"Venta #{resultado.numero_factura} registrada con NCF: {resultado.ncf_tradicional}"
                    )

                self.items_carrito.clear()
                self.factura_pendiente_retomada = None
                self.actualizar_tabla_carrito()
                self.cargar_datos_iniciales()
            except ErrorNegocio as e:
                messagebox.showerror("Error guardando venta", str(e))
            except Exception as e:
                messagebox.showerror("Error guardando venta", f"La venta no se guardó y la operación fue revertida:\n{e}")

        RealizarPagoModal(self, total_pagar=total_a_pagar, callback_confirm=finalizar)

    def abrir_caja_flujo(self):
        from abrir_caja_modal import AbrirCajaModal
        def al_abrir(estado, monto):
            self.caja_id = self.obtener_caja_abierta()
            self.estado_caja = "ABIERTA"
            self.lbl_estado_caja.config(text="ABIERTA", fg="#166534")
        AbrirCajaModal(self, usuario=self.usuario, callback_exito=al_abrir)

    def cerrar_caja_flujo(self):
        from reporte_caja import ReporteCajaUsuario
        if not self.validar_caja_activa():
            return
        if messagebox.askyesno("Cerrar Caja", f"¿Desea cerrar el turno actual de caja de {self.usuario}?\n\nAl confirmar se cerrará la caja y se generará el Reporte de Caja."):
            try:
                resumen = self.servicio_caja.resumen_cierre(self.caja_id)
                contado = simpledialog.askfloat("Cuadre de caja", f"Efectivo contado físicamente (esperado RD$ {resumen['esperado']:,.2f}):", parent=self, minvalue=0)
                if contado is None:
                    return
                cierre = self.servicio_caja.cerrar(self.caja_id, contado)
                esperado, diferencia, tot_ventas = cierre["esperado"], cierre["diferencia"], cierre["total_ventas"]
            except Exception as e:
                messagebox.showerror("Error cerrando caja", f"La caja no se cerró:\n{e}")
                return

            self.estado_caja = "CERRADA"
            self.lbl_estado_caja.config(text="CERRADA", fg="#DC2626")
            if diferencia < 0:
                resultado = f"FALTANTE: RD$ {abs(diferencia):,.2f}"
            elif diferencia > 0:
                resultado = f"SOBRANTE: RD$ {diferencia:,.2f}"
            else:
                resultado = "CUADRE EXACTO"
            messagebox.showinfo("Caja Cerrada", f"La caja se cerró correctamente.\n\nEsperado: RD$ {esperado:,.2f}\nContado: RD$ {float(contado):,.2f}\n{resultado}\n\nA continuación se mostrará el reporte.")
            ReporteCajaUsuario(self)

    def cambiar_estado_caja(self, estado):
        if estado == "ABIERTA":
            self.abrir_caja_flujo()
        else:
            self.cerrar_caja_flujo()

    def ver_ventas_historial(self):
        from ventas_realizadas import VentasRealizadas
        VentasRealizadas(self)

    def anular_factura(self):
        if self.rol not in ("Administrador", "Supervisor"):
            messagebox.showwarning("Acceso restringido", "Un cajero no puede anular facturas. Solicite autorización a un supervisor.")
            return
        from anular_factura_modal import AnularFacturaModal
        AnularFacturaModal(self)

    def guardar_factura_pendiente(self):
        if not self.validar_caja_activa():
            return
        if not self.items_carrito:
            messagebox.showwarning("Atención", "No hay productos en la venta para guardar.")
            return

        cliente_nom = self.cmb_cliente.get() or "Cliente General"
        try:
            items = [ItemVenta(
                producto_id=item["id"], producto=item["producto"], cantidad=item["cantidad"],
                precio=item["precio"], costo=item["costo"],
            ) for item in self.items_carrito]
            resultado = self.servicio_ventas.guardar_factura_pendiente(
                cliente_nom, items, self.usuario, self.caja_id, self.almacen_id,
            )
            messagebox.showinfo("Guardar", f"Factura #{resultado.numero_factura} guardada como pendiente exitosamente.")
            self.numero_factura = self.servicio_ventas.obtener_siguiente_factura()
            self.lbl_num_factura.config(text=f"Factura:   {self.numero_factura}")
            self.items_carrito.clear()
            self.actualizar_tabla_carrito()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar la factura pendiente: {e}")

    def ver_facturas_abiertas(self):
        from facturas_pendientes import FacturasPendientes
        FacturasPendientes(self, callback_retomar=self.retomar_factura_pendiente)

    def retomar_factura_pendiente(self, numero_factura):
        try:
            filas = self.servicio_ventas.obtener_factura_pendiente(numero_factura)
            if not filas:
                return
            # Se conserva hasta que el cobro confirme la venta. Si el
            # usuario cancela o falla el guardado, puede retomarla otra vez.
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo retomar la factura pendiente: {e}")
            return

        for producto, precio, cantidad, total, costo in filas:
            prod_id = None
            for p in self.lista_productos_db:
                if p[1] == producto:
                    prod_id = p[0]
                    break
            self.items_carrito.append({
                "id": prod_id,
                "producto": producto,
                "precio": precio,
                "costo": costo,
                "cantidad": cantidad,
                "impuesto": 0.00,
                "total": total
            })
        self.factura_pendiente_retomada = numero_factura
        self.actualizar_tabla_carrito()

    def nuevo_cliente(self):
        from clientes import Clientes
        Clientes(self)

    def cliente_defecto(self):
        from cliente_defecto_modal import ClienteDefectoModal
        ClienteDefectoModal(self, callback_guardar=lambda c: self.cmb_cliente.set(c))

    def buscar_cliente(self):
        from buscar_producto import BuscarProductoModal
        BuscarProductoModal(self, callback_select=self.seleccionar_producto_desde_modal)

    def seleccionar_producto_desde_modal(self, producto):
        """Recibe la selección del listado detallado y la deja lista para agregar."""
        prod_id = producto[0]
        disponible = next((p for p in self.lista_productos_db if int(p[0]) == int(prod_id)), None)
        if not disponible:
            messagebox.showwarning(
                "Producto sin existencia",
                f"{producto[1]} no tiene existencia disponible en el almacén operativo."
            )
            return
        self.cmb_producto.set(self._texto_producto(disponible))
        self.al_seleccionar_producto_combo()
        self.ent_cantidad.focus_set()

    def config_impresora(self):
        from factura_config import FacturaConfig
        FacturaConfig(self)

    def aplicar_descuento(self):
        # El descuento se solicita dentro del cobro para que se valide junto
        # al medio de pago y quede reflejado en el total final.
        self.procesar_pago()
