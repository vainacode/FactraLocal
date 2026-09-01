import datetime
import os
import db_conexion
import db_conexion as sqlite3
import sys
import tkinter as tk
from tkinter import messagebox, ttk
from PIL import Image, ImageTk
from window_utils import posicionar_ventana
from servicios.servicio_cotizaciones import ServicioCotizaciones

class Cotizaciones(tk.Toplevel):
    def __init__(self, parent, usuario=""):
        super().__init__(parent)
        self.parent = parent
        self.usuario = usuario
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
        self.servicio_cotizaciones = ServicioCotizaciones()
        self.images = {}
        self.items_carrito = []
        self.numero_cotizacion = self.obtener_siguiente_cotizacion()

        self.widgets()
        self.actualizar_reloj()
        self.cargar_datos_iniciales()
        self.configurar_atajos()

    def rutas(self, ruta):
        try:
            rutabase = sys.__MEIPASS
        except Exception:
            rutabase = os.path.abspath(".")
        return os.path.join(rutabase, ruta)

    def obtener_siguiente_cotizacion(self):
        try:
            return db_conexion.ver_siguiente_numero("cotizacion")
        except Exception:
            return 1

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
            self.images["cajero_cot"] = ImageTk.PhotoImage(img_caj)
            lbl_caj_img = tk.Label(frame_header, image=self.images["cajero_cot"], bg="#DDE1E5")
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
            text="COTIZACIONES DE PRODUCTOS",
            font=("sans", 24, "bold"),
            bg="#DDE1E5",
            fg="#1E293B"
        )
        lbl_titulo.place(relx=0.5, y=32, anchor="center")

#============== 2. BARRA DE CLIENTE Y RELOJ ========================================================#
        lbl_cli = tk.Label(self, text="Cliente:", font=("sans", 13, "bold"), bg="#C6D9E3", fg="#1E293B")
        lbl_cli.place(x=35, y=77)

        self.cmb_cliente = ttk.Combobox(self, font=("sans", 11))
        self.cmb_cliente.place(x=130, y=76, width=310, height=28)

        # 3 Botones rápidos de cliente
        iconos_cli = [
            ("agregarcliente.png", self.nuevo_cliente),
            ("clientedefecto.png", self.cliente_defecto),
            ("descuento.png", self.aplicar_descuento),
        ]

        x_btn = 450
        for ico_file, cmd in iconos_cli:
            ruta_i = self.rutas(f"icono/{ico_file}")
            if os.path.exists(ruta_i):
                img_i = Image.open(ruta_i).resize((24, 24), Image.Resampling.LANCZOS)
                self.images[f"cot_cli_{ico_file}"] = ImageTk.PhotoImage(img_i)
                ico_btn = self.images[f"cot_cli_{ico_file}"]
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

        # Fecha y Hora
        ruta_cal = self.rutas("icono/calendario.png")
        if os.path.exists(ruta_cal):
            img_cal = Image.open(ruta_cal).resize((22, 22), Image.Resampling.LANCZOS)
            self.images["cal_cot"] = ImageTk.PhotoImage(img_cal)
            lbl_cal = tk.Label(self, image=self.images["cal_cot"], bg="#C6D9E3")
            lbl_cal.place(x=710, y=78)

        self.lbl_fecha = tk.Label(self, text="", font=("sans", 11, "bold"), bg="#C6D9E3", fg="#1E293B")
        self.lbl_fecha.place(x=736, y=80)

        ruta_clk = self.rutas("icono/hora.png")
        if os.path.exists(ruta_clk):
            img_clk = Image.open(ruta_clk).resize((22, 22), Image.Resampling.LANCZOS)
            self.images["clk_cot"] = ImageTk.PhotoImage(img_clk)
            lbl_clk = tk.Label(self, image=self.images["clk_cot"], bg="#C6D9E3")
            lbl_clk.place(x=855, y=78)

        self.lbl_hora = tk.Label(self, text="", font=("sans", 11, "bold"), bg="#C6D9E3", fg="#1E293B")
        self.lbl_hora.place(x=882, y=80)
#============== 3. RECUADRO DE ENTRADA =============================================================#
        frame_input = tk.Frame(self, bg="#DDE1E5", highlightbackground="#B8C4CE", highlightthickness=1)
        frame_input.place(x=20, y=115, width=910, height=115)

        # Fila 1
        lbl_f1 = tk.Label(frame_input, text="Código:\n(F1)", font=("sans", 11, "bold"), bg="#DDE1E5", fg="#1E293B", justify="center")
        lbl_f1.place(x=15, y=6)

        self.ent_codigo = ttk.Entry(frame_input, font=("sans", 12))
        self.ent_codigo.place(x=110, y=10, width=360, height=32)
        self.ent_codigo.bind("<Return>", lambda e: self.buscar_y_agregar_por_codigo())

        lbl_f2 = tk.Label(frame_input, text="Cantidad:\n(F2)", font=("sans", 11, "bold"), bg="#DDE1E5", fg="#1E293B", justify="center")
        lbl_f2.place(x=485, y=6)

        self.ent_cantidad = ttk.Entry(frame_input, font=("sans", 12), justify="center")
        self.ent_cantidad.place(x=580, y=10, width=80, height=32)
        self.ent_cantidad.insert(0, "1")
        self.ent_cantidad.bind("<Return>", lambda e: self.buscar_y_agregar_por_codigo())

        ruta_fac_ico = self.rutas("icono/factura.png")
        if os.path.exists(ruta_fac_ico):
            img_fac = Image.open(ruta_fac_ico).resize((24, 24), Image.Resampling.LANCZOS)
            self.images["cot_fac_ico"] = ImageTk.PhotoImage(img_fac)
            lbl_fac_img = tk.Label(frame_input, image=self.images["cot_fac_ico"], bg="#DDE1E5")
            lbl_fac_img.place(x=710, y=14)

        self.lbl_num_cot = tk.Label(
            frame_input,
            text=f"Cotización: {self.numero_cotizacion}",
            font=("sans", 12, "bold"),
            bg="#DDE1E5",
            fg="#1E293B"
        )
        self.lbl_num_cot.place(x=745, y=16)

        lbl_prod_tag = tk.Label(frame_input, text="Producto:", font=("sans", 12, "bold"), bg="#DDE1E5", fg="#1E293B")
        lbl_prod_tag.place(x=15, y=62)

        self.cmb_producto = ttk.Combobox(frame_input, font=("sans", 11))
        self.cmb_producto.place(x=110, y=60, width=550, height=30)
        self.cmb_producto.bind("<<ComboboxSelected>>", self.al_seleccionar_producto_combo)
        self.cmb_producto.bind("<Return>", lambda e: self.agregar_producto_seleccionado())

        self.lbl_stock_disp = tk.Label(frame_input, text="Stock:", font=("sans", 12, "bold"), bg="#DDE1E5", fg="#1E293B")
        self.lbl_stock_disp.place(x=680, y=62)

#============== 4. BARRA DE BOTONES F3 - F6 =========================================================#
        frame_barra_btns = tk.Frame(self, bg="#B8C4CE", height=38)
        frame_barra_btns.place(x=20, y=235, width=910, height=38)

        acciones_tabla = [
            ("Agregar (F3)", "agregar.png", self.agregar_producto_seleccionado),
            ("Editar (F4)", "editar.png", self.editar_item_carrito),
            ("Eliminar (F5)", "eliminar.png", self.eliminar_item_carrito),
            ("Limpiar (F6)", "limpiar.png", self.limpiar_carrito),
        ]

        x_act = 0
        w_act = 227
        for txt, ico_f, cmd in acciones_tabla:
            ruta_i = self.rutas(f"icono/{ico_f}")
            if os.path.exists(ruta_i):
                img_i = Image.open(ruta_i).resize((22, 22), Image.Resampling.LANCZOS)
                self.images[f"act_cot_{txt}"] = ImageTk.PhotoImage(img_i)
                ico_btn = self.images[f"act_cot_{txt}"]
            else:
                ico_btn = None

            btn_t = tk.Button(
                frame_barra_btns,
                text=f"  {txt}",
                image=ico_btn,
                compound=tk.LEFT,
                font=("sans", 10, "bold"),
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

#============== 5. TABLA ===========================================================================#
        style = ttk.Style()
        style.configure("Cot.Treeview.Heading", font=("sans", 9, "bold"), background="#E0E6ED")
        style.configure("Cot.Treeview", font=("sans", 10), rowheight=24)

        self.tabla = ttk.Treeview(
            self,
            columns=("producto", "precio", "cantidad", "impuesto", "total"),
            show="headings",
            style="Cot.Treeview"
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

#============== 6. PANELES INFERIORES ===============================================================#
        frame_resumen = tk.LabelFrame(self, text="RESUMEN DE LA COMPRA", font=("sans", 9, "bold"), bg="#C6D9E3", fg="#1E293B")
        frame_resumen.place(x=20, y=528, width=225, height=110)

        lbl_sub = tk.Label(frame_resumen, text="Subtotal:", font=("sans", 10, "bold"), bg="#C6D9E3", fg="#334155")
        lbl_sub.place(x=10, y=10)
        self.lbl_subtotal_val = tk.Label(frame_resumen, text="RD$ 0.00", font=("sans", 10, "bold"), bg="#C6D9E3", fg="#1E293B")
        self.lbl_subtotal_val.place(x=85, y=10)

        lbl_imp = tk.Label(frame_resumen, text="Impuesto:", font=("sans", 10, "bold"), bg="#C6D9E3", fg="#334155")
        lbl_imp.place(x=10, y=45)
        self.lbl_impuesto_val = tk.Label(frame_resumen, text="RD$ 0.00", font=("sans", 10, "bold"), bg="#C6D9E3", fg="#1E293B")
        self.lbl_impuesto_val.place(x=85, y=45)

        frame_info = tk.LabelFrame(self, text="INFORMACIÓN", font=("sans", 9, "bold"), bg="#C6D9E3", fg="#1E293B")
        frame_info.place(x=255, y=528, width=210, height=110)

        lbl_art = tk.Label(frame_info, text="Total Artículos:", font=("sans", 10, "bold"), bg="#C6D9E3", fg="#334155")
        lbl_art.place(x=10, y=20)
        self.lbl_articulos_val = tk.Label(frame_info, text="0", font=("sans", 10, "bold"), bg="#C6D9E3", fg="#1E293B")
        self.lbl_articulos_val.place(x=120, y=20)

        frame_total = tk.Frame(self, bg="#DDE1E5", highlightbackground="#B8C4CE", highlightthickness=1)
        frame_total.place(x=475, y=528, width=455, height=110)

        lbl_total_banner = tk.Label(frame_total, text="TOTAL COTIZACIÓN", font=("sans", 11, "bold"), bg="#DDE1E5", fg="#1E293B")
        lbl_total_banner.place(relx=0.5, y=16, anchor="center")

        ruta_coin = self.rutas("icono/moneda.png")
        if os.path.exists(ruta_coin):
            img_c = Image.open(ruta_coin).resize((46, 46), Image.Resampling.LANCZOS)
            self.images["coin_cot"] = ImageTk.PhotoImage(img_c)
            lbl_coin_img = tk.Label(frame_total, image=self.images["coin_cot"], bg="#DDE1E5")
            lbl_coin_img.place(x=45, y=40)
        else:
            lbl_coin_img = tk.Label(frame_total, text="💰", font=("sans", 24), bg="#DDE1E5")
            lbl_coin_img.place(x=45, y=40)

        self.lbl_gran_total = tk.Label(frame_total, text="RD$ 0.00", font=("sans", 26, "bold"), bg="#DDE1E5", fg="#1E293B")
        self.lbl_gran_total.place(x=105, y=42)

#============== 7. COLUMNA LATERAL DERECHA =========================================================#
        frame_col_der = tk.Frame(self, bg="#C6D9E3", highlightbackground="#A9BFCE", highlightthickness=1)
        frame_col_der.place(x=945, y=115, width=135, height=523)

        botones_lateral = [
            ("Registrar", "pago.png", self.registrar_cotizacion),
            ("Ver\nCotiz.", "ver.png", self.ver_cotizaciones),
            ("Anular\nCotiz.", "anular.png", self.anular_cotizacion),
            ("Guardar\nCotiz.", "facturaguardar.png", self.guardar_cotizacion),
            ("Cotiz.\nAbiertas", "facturapendiente.png", self.cotizaciones_abiertas),
        ]

        y_lat = 8
        for txt, ico_f, cmd in botones_lateral:
            ruta_i = self.rutas(f"icono/{ico_f}")
            if os.path.exists(ruta_i):
                img_i = Image.open(ruta_i).resize((32, 32), Image.Resampling.LANCZOS)
                self.images[f"lat_cot_{ico_f}"] = ImageTk.PhotoImage(img_i)
                ico_btn = self.images[f"lat_cot_{ico_f}"]
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

    def actualizar_reloj(self):
        ahora = datetime.datetime.now()
        self.lbl_fecha.config(text=ahora.strftime("%d-%m-%Y"))
        self.lbl_hora.config(text=ahora.strftime("%H:%M:%S"))
        self.after(1000, self.actualizar_reloj)

    def cargar_datos_iniciales(self):
        try:
            clis = self.servicio_cotizaciones.listar_clientes()
            if not clis:
                clis = ["Cliente General"]
            self.cmb_cliente["values"] = clis
            self.cmb_cliente.current(0)
            self.lista_productos_db = self.servicio_cotizaciones.listar_productos()
            self.cmb_producto["values"] = [f"{p[0]} - {p[1]} ($ {p[2]:,.2f})" for p in self.lista_productos_db]
        except Exception as e:
            print("Error cargando cotizaciones:", e)

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
            if str(p[0]) == codigo or codigo.lower() in p[1].lower():
                prod_encontrado = p
                break

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
        prod_id, nombre, precio, stock, costo = prod[0], prod[1], prod[2], prod[3], prod[4]

        for item in self.items_carrito:
            if item["id"] == prod_id:
                item["cantidad"] += cantidad
                item["total"] = item["cantidad"] * item["precio"]
                self.actualizar_tabla_carrito()
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
            messagebox.showwarning("Atención", "Seleccione un producto para editar.")
            return
        idx = self.tabla.index(sel[0])
        item = self.items_carrito[idx]
        item["cantidad"] += 1
        item["total"] = item["cantidad"] * item["precio"]
        self.actualizar_tabla_carrito()

    def eliminar_item_carrito(self):
        sel = self.tabla.selection()
        if not sel:
            messagebox.showwarning("Atención", "Seleccione un producto para eliminar.")
            return
        idx = self.tabla.index(sel[0])
        del self.items_carrito[idx]
        self.actualizar_tabla_carrito()

    def limpiar_carrito(self):
        if self.items_carrito:
            self.items_carrito.clear()
            self.actualizar_tabla_carrito()

    def _guardar_cotizacion_bd(self, estado):
        cliente_nom = self.cmb_cliente.get() or "Cliente General"
        return self.servicio_cotizaciones.registrar(cliente_nom, self.items_carrito, self.usuario, estado)

    def registrar_cotizacion(self):
        if not self.items_carrito:
            messagebox.showwarning("Atención", "No hay productos en la cotización.")
            return
        try:
            numero_asignado = self._guardar_cotizacion_bd("Registrada")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo registrar la cotización: {e}")
            return
        messagebox.showinfo("Cotización", f"Cotización #{numero_asignado} registrada exitosamente.")
        self.numero_cotizacion = db_conexion.ver_siguiente_numero("cotizacion")
        self.lbl_num_cot.config(text=f"Cotización:  {self.numero_cotizacion}")
        self.limpiar_carrito()

    def ver_cotizaciones(self):
        from cargar_cotizacion import CargarCotizacion
        CargarCotizacion(self, callback_load=self.retomar_cotizacion)

    def anular_cotizacion(self):
        messagebox.showinfo("Anular", "Para anular una cotización, ábrala desde 'Cotizaciones Abiertas' y elimínela desde ahí.")

    def guardar_cotizacion(self):
        if not self.items_carrito:
            messagebox.showwarning("Atención", "No hay productos en la cotización para guardar.")
            return
        try:
            numero_asignado = self._guardar_cotizacion_bd("Pendiente")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar la cotización: {e}")
            return
        messagebox.showinfo("Guardar", f"Cotización #{numero_asignado} guardada exitosamente.")
        self.numero_cotizacion = db_conexion.ver_siguiente_numero("cotizacion")
        self.lbl_num_cot.config(text=f"Cotización:  {self.numero_cotizacion}")
        self.limpiar_carrito()

    def cotizaciones_abiertas(self):
        from cargar_cotizacion import CargarCotizacion
        CargarCotizacion(self, callback_load=self.retomar_cotizacion)

    def retomar_cotizacion(self, numero_cotizacion):
        try:
            filas = self.servicio_cotizaciones.eliminar(numero_cotizacion)
            if not filas:
                return
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo retomar la cotización: {e}")
            return

        for producto, precio, cantidad, total, costo in filas:
            self.items_carrito.append({
                "id": None,
                "producto": producto,
                "precio": precio,
                "costo": costo,
                "cantidad": cantidad,
                "impuesto": 0.00,
                "total": total
            })
        self.actualizar_tabla_carrito()

    def nuevo_cliente(self):
        from clientes import Clientes
        Clientes(self)

    def cliente_defecto(self):
        self.cmb_cliente.set("Cliente General")

    def aplicar_descuento(self):
        from cotizacion_nota_modal import CotizacionNotaModal
        CotizacionNotaModal(self)
