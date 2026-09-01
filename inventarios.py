import csv
import datetime
import os
import db_conexion as sqlite3
import sys
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageTk
from producto_modal import ProductoModal
from window_utils import posicionar_ventana
from servicios.servicio_inventario import ServicioInventario

class Inventarios(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.title("Punto de Venta Versión 4.4.7 - Inventarios")
        posicionar_ventana(self, 1100, 650, parent)
        self.resizable(False, False)
        self.configure(bg="#DCE1E6")
        self.transient(parent)
        self.grab_set()
        try:
            self.iconbitmap(self.rutas('icono.ico'))
        except Exception:
            pass

        self.db_name = "database.db"
        self.servicio_inventario = ServicioInventario()
        self.images = {}
        self.productos = []
        self.producto_seleccionado = None
        self.pagina_actual = 1
        self.productos_por_pagina = 8

        self.widgets()
        self.actualizar_reloj()
        self.cargar_productos()

    def rutas(self, ruta):
        try:
            rutabase = sys.__MEIPASS
        except Exception:
            rutabase = os.path.abspath(".")
        return os.path.join(rutabase, ruta)

    def widgets(self):
#============== 1. HEADER ==========================================================================#
        frame_header = tk.Frame(self, bg="#DCE1E6", highlightbackground="#B8C4CE", highlightthickness=1)
        frame_header.pack()
        frame_header.place(x=0, y=0, width=1100, height=75)

        # Total productos
        ruta_stock_icon = self.rutas("icono/totalinv.png")
        if not os.path.exists(ruta_stock_icon):
            ruta_stock_icon = self.rutas("icono/btninventario.png")

        if os.path.exists(ruta_stock_icon):
            img_stk = Image.open(ruta_stock_icon).resize((32, 32), Image.Resampling.LANCZOS)
            self.images["stk_ico"] = ImageTk.PhotoImage(img_stk)
            lbl_stk_img = tk.Label(frame_header, image=self.images["stk_ico"], bg="#DCE1E6")
            lbl_stk_img.place(x=20, y=20)

        self.lbl_total_prod = tk.Label(
            frame_header,
            text="Total productos: 0",
            font=("sans", 16, "bold"),
            bg="#DCE1E6",
            fg="#1E293B"
        )
        self.lbl_total_prod.place(x=60, y=22)

        # Título Central
        lbl_titulo = tk.Label(
            frame_header,
            text="INVENTARIOS",
            font=("sans", 28, "bold"),
            bg="#DCE1E6",
            fg="#1E293B"
        )
        lbl_titulo.place(relx=0.5, rely=0.5, anchor="center")

        # Fecha y Hora en tiempo real
        ruta_cal = self.rutas("icono/calendario.png")
        if os.path.exists(ruta_cal):
            img_cal = Image.open(ruta_cal).resize((26, 26), Image.Resampling.LANCZOS)
            self.images["cal"] = ImageTk.PhotoImage(img_cal)
            lbl_cal_ico = tk.Label(frame_header, image=self.images["cal"], bg="#DCE1E6")
            lbl_cal_ico.place(x=780, y=24)

        self.lbl_fecha = tk.Label(
            frame_header,
            text="",
            font=("sans", 13, "bold"),
            bg="#DCE1E6",
            fg="#1E293B"
        )
        self.lbl_fecha.place(x=812, y=26)

        ruta_clock = self.rutas("icono/hora.png")
        if os.path.exists(ruta_clock):
            img_clk = Image.open(ruta_clock).resize((26, 26), Image.Resampling.LANCZOS)
            self.images["clock"] = ImageTk.PhotoImage(img_clk)
            lbl_clk_ico = tk.Label(frame_header, image=self.images["clock"], bg="#DCE1E6")
            lbl_clk_ico.place(x=940, y=24)

        self.lbl_hora = tk.Label(
            frame_header,
            text="",
            font=("sans", 13, "bold"),
            bg="#DCE1E6",
            fg="#1E293B"
        )
        self.lbl_hora.place(x=972, y=26)

#============== 2. PANEL IZQUIERDO ==================================================================#
        # Grupo Buscar
        frame_buscar = tk.LabelFrame(
            self,
            text="Buscar",
            font=("sans", 12, "bold"),
            bg="#C6D9E3",
            fg="#1E293B",
            padx=8,
            pady=6
        )
        frame_buscar.place(x=15, y=85, width=280, height=85)

        self.ent_buscar = ttk.Entry(frame_buscar, font=("sans", 11))
        self.ent_buscar.place(x=5, y=8, width=215, height=32)
        self.ent_buscar.bind("<KeyRelease>", lambda e: self.filtrar_productos())

        ruta_barcode = self.rutas("icono/barcode.png")
        if os.path.exists(ruta_barcode):
            img_bar = Image.open(ruta_barcode).resize((28, 28), Image.Resampling.LANCZOS)
            self.images["barcode_search"] = ImageTk.PhotoImage(img_bar)
            btn_barcode = tk.Button(
                frame_buscar,
                image=self.images["barcode_search"],
                bg="white",
                relief="solid",
                bd=1,
                cursor="hand2",
                command=self.buscar_por_codigo
            )
            btn_barcode.place(x=225, y=8, width=32, height=32)

        # Grupo Selección
        frame_sel = tk.LabelFrame(
            self,
            text="Selección",
            font=("sans", 12, "bold"),
            bg="#C6D9E3",
            fg="#1E293B",
            padx=10,
            pady=8
        )
        frame_sel.place(x=15, y=175, width=280, height=195)

        self.lbl_sel_nom = tk.Label(frame_sel, text="Producto: -", font=("sans", 10, "bold"), bg="#C6D9E3", fg="#334155", anchor="w", wraplength=250, justify="left")
        self.lbl_sel_nom.place(x=5, y=5, width=260)

        self.lbl_sel_pre = tk.Label(frame_sel, text="Precio: -", font=("sans", 10, "bold"), bg="#C6D9E3", fg="#334155", anchor="w")
        self.lbl_sel_pre.place(x=5, y=42, width=260)

        self.lbl_sel_costo = tk.Label(frame_sel, text="Costo: -", font=("sans", 10, "bold"), bg="#C6D9E3", fg="#334155", anchor="w")
        self.lbl_sel_costo.place(x=5, y=75, width=260)

        self.lbl_sel_stock = tk.Label(frame_sel, text="Stock: -", font=("sans", 10, "bold"), bg="#C6D9E3", fg="#334155", anchor="w")
        self.lbl_sel_stock.place(x=5, y=108, width=260)

        self.lbl_sel_imp = tk.Label(frame_sel, text="Impuesto: Exento", font=("sans", 10, "bold"), bg="#C6D9E3", fg="#334155", anchor="w")
        self.lbl_sel_imp.place(x=5, y=140, width=260)

        # Grupo Opciones
        frame_opc = tk.LabelFrame(
            self,
            text="Opciones",
            font=("sans", 12, "bold"),
            bg="#C6D9E3",
            fg="#1E293B",
            padx=6,
            pady=4
        )
        frame_opc.place(x=15, y=375, width=280, height=265)

        lbl_ord = tk.Label(frame_opc, text="Ordenar por:", font=("sans", 10, "bold"), bg="#C6D9E3", fg="#334155")
        lbl_ord.place(x=5, y=2)

        self.cmb_orden = ttk.Combobox(
            frame_opc,
            values=["Más antiguo", "Más reciente", "Mayor precio", "Menor precio", "Mayor stock", "Menor stock", "A-Z"],
            font=("sans", 10),
            state="readonly"
        )
        self.cmb_orden.current(0)
        self.cmb_orden.place(x=5, y=24, width=255, height=26)
        self.cmb_orden.bind("<<ComboboxSelected>>", lambda e: self.ordenar_productos())

        # Botones de Acción (Grid)
        acciones = [
            ("Agregar", "agregar.png", self.abrir_agregar, 0, 0),
            ("Editar", "editar.png", self.abrir_editar, 0, 1),
            ("Inactivar", "eliminar.png", self.inactivar_producto, 0, 2),
            ("Exportar", "excel.png", self.exportar_excel, 0, 3),
            ("Stock", "bajastock.png", self.filtrar_bajo_stock, 1, 0),
            ("Precios", "historialprecios.png", self.mostrar_historial_precios, 1, 1),
            ("Servicios", "servicios.png", self.mostrar_servicios, 1, 2),
            ("Mín Stock", "guardar.png", self.mostrar_stock_min_ind, 1, 3),
        ]

        frame_btns = tk.Frame(frame_opc, bg="#C6D9E3")
        frame_btns.place(x=3, y=60, width=265, height=175)

        for txt, ico_file, cmd, r, c in acciones:
            ruta_i = self.rutas(f"icono/{ico_file}")
            if os.path.exists(ruta_i):
                img_a = Image.open(ruta_i).resize((26, 26), Image.Resampling.LANCZOS)
                self.images[ico_file] = ImageTk.PhotoImage(img_a)
                ico_btn = self.images[ico_file]
            else:
                ico_btn = None

            btn_act = tk.Button(
                frame_btns,
                text=txt,
                image=ico_btn,
                compound=tk.TOP,
                font=("sans", 8, "bold"),
                bg="#EBEFF2",
                fg="#1E293B",
                relief="raised",
                bd=2,
                cursor="hand2",
                command=cmd
            )
            btn_act.place(x=c * 66, y=r * 78, width=62, height=68)

#============== 3. PANEL DERECHO (PRODUCTOS) =======================================================#
        self.frame_prods = tk.LabelFrame(
            self,
            text="Productos",
            font=("sans", 12, "bold"),
            bg="#C6D9E3",
            fg="#1E293B",
            padx=8,
            pady=4
        )
        self.frame_prods.place(x=305, y=85, width=780, height=555)

        # Barra de paginación superior derecha
        ruta_izq = self.rutas("icono/izquierda.png")
        if os.path.exists(ruta_izq):
            img_izq = Image.open(ruta_izq).resize((18, 18), Image.Resampling.LANCZOS)
            self.images["izq"] = ImageTk.PhotoImage(img_izq)
            btn_izq = tk.Button(
                self.frame_prods,
                image=self.images["izq"],
                bg="#EBEFF2",
                relief="raised",
                bd=1,
                cursor="hand2",
                command=self.pagina_anterior
            )
            btn_izq.place(x=620, y=0, width=24, height=24)

        ruta_der = self.rutas("icono/derecha.png")
        if os.path.exists(ruta_der):
            img_der = Image.open(ruta_der).resize((18, 18), Image.Resampling.LANCZOS)
            self.images["der"] = ImageTk.PhotoImage(img_der)
            btn_der = tk.Button(
                self.frame_prods,
                image=self.images["der"],
                bg="#EBEFF2",
                relief="raised",
                bd=1,
                cursor="hand2",
                command=self.pagina_siguiente
            )
            btn_der.place(x=648, y=0, width=24, height=24)

        self.lbl_pag = tk.Label(
            self.frame_prods,
            text="Página 1 de 1",
            font=("sans", 10, "bold"),
            bg="#C6D9E3",
            fg="#1E293B"
        )
        self.lbl_pag.place(x=680, y=2)

        # Contenedor de las tarjetas de producto
        self.grid_cards = tk.Frame(self.frame_prods, bg="#C6D9E3")
        self.grid_cards.place(x=5, y=30, width=755, height=490)

    def actualizar_reloj(self):
        ahora = datetime.datetime.now()
        self.lbl_fecha.config(text=ahora.strftime("%d-%m-%Y"))
        self.lbl_hora.config(text=ahora.strftime("%H:%M:%S"))
        self.after(1000, self.actualizar_reloj)

    def cargar_productos(self):
        try:
            self.productos = self.servicio_inventario.listar_productos()

            self.lbl_total_prod.config(text=f"Total productos: {len(self.productos)}")
            self.renderizar_pagina()
        except Exception as e:
            print("Error cargando productos:", e)

    def insertar_productos_muestra(self, conn):
        # Se conserva el método por compatibilidad con instalaciones antiguas,
        # pero no realiza ninguna siembra automática de datos ficticios.
        return None

    def renderizar_pagina(self):
        # Limpiar tarjetas anteriores
        for widget in self.grid_cards.winfo_children():
            widget.destroy()

        total = len(self.productos)
        total_paginas = max(1, (total + self.productos_por_pagina - 1) // self.productos_por_pagina)
        if self.pagina_actual > total_paginas:
            self.pagina_actual = total_paginas
        if self.pagina_actual < 1:
            self.pagina_actual = 1

        self.lbl_pag.config(text=f"Página {self.pagina_actual} de {total_paginas}")

        inicio = (self.pagina_actual - 1) * self.productos_por_pagina
        fin = inicio + self.productos_por_pagina
        prods_pagina = self.productos[inicio:fin]

        for i, prod in enumerate(prods_pagina):
            col = i % 4
            fila = i // 4
            self.crear_tarjeta_producto(prod, col, fila)

    def crear_tarjeta_producto(self, prod, col, fila):
        # prod: (id, nombre, proveedor, precio, costo, stock, categoria, sucursal, image_path, estado)
        prod_id = prod[0]
        nombre = prod[1] or "Producto"
        precio = prod[3] or 0.0
        stock = prod[5] or 0
        img_path = prod[8] if len(prod) > 8 else ""

        card = tk.Frame(
            self.grid_cards,
            bg="white",
            highlightbackground="#B0C4DE",
            highlightthickness=1,
            cursor="hand2"
        )
        card.place(x=col * 188 + 5, y=fila * 240 + 5, width=180, height=230)

        # Imagen del producto
        lbl_img = tk.Label(card, bg="white")
        lbl_img.place(x=15, y=10, width=150, height=120)

        img_key = f"prod_img_{prod_id}"
        if img_path and os.path.exists(img_path):
            try:
                img_raw = Image.open(img_path).resize((130, 110), Image.Resampling.LANCZOS)
                self.images[img_key] = ImageTk.PhotoImage(img_raw)
                lbl_img.config(image=self.images[img_key])
            except Exception:
                lbl_img.config(text="📦", font=("sans", 32))
        else:
            # Icono representativo por defecto
            lbl_img.config(text="📦", font=("sans", 32))

        # Nombre del producto
        lbl_nom = tk.Label(
            card,
            text=nombre,
            font=("sans", 9, "bold"),
            bg="white",
            fg="#1E293B",
            wraplength=170,
            justify="center"
        )
        lbl_nom.place(x=5, y=135, width=170, height=42)

        # Precio
        lbl_pre = tk.Label(
            card,
            text=f"Precio: $ {precio:,.2f}",
            font=("sans", 9, "bold"),
            bg="white",
            fg="#334155",
            anchor="w"
        )
        lbl_pre.place(x=10, y=182, width=160)

        # Stock
        lbl_stk = tk.Label(
            card,
            text=f"Stock: {stock}",
            font=("sans", 9, "bold"),
            bg="white",
            fg="#166534" if stock > 10 else "#DC2626",
            anchor="w"
        )
        lbl_stk.place(x=10, y=204, width=160)

        # Evento de selección en toda la tarjeta
        for w in (card, lbl_img, lbl_nom, lbl_pre, lbl_stk):
            w.bind("<Button-1>", lambda e, p=prod, c=card: self.seleccionar_producto(p, c))
            w.bind("<Double-Button-1>", lambda e, p_id=prod_id: self.abrir_editar(p_id))

    def seleccionar_producto(self, prod, card_widget):
        self.producto_seleccionado = prod
        # Highlight seleccionado
        for c in self.grid_cards.winfo_children():
            c.config(highlightbackground="#B0C4DE", highlightthickness=1)
        card_widget.config(highlightbackground="#2563EB", highlightthickness=2)

        # Actualizar sección Selección
        self.lbl_sel_nom.config(text=f"Producto: {prod[1]}")
        self.lbl_sel_pre.config(text=f"Precio: $ {prod[3]:,.2f}")
        self.lbl_sel_costo.config(text=f"Costo: $ {prod[4]:,.2f}")
        self.lbl_sel_stock.config(text=f"Stock: {prod[5]}")
        self.lbl_sel_imp.config(text="Impuesto: Exento")

    def pagina_anterior(self):
        if self.pagina_actual > 1:
            self.pagina_actual -= 1
            self.renderizar_pagina()

    def pagina_siguiente(self):
        total = len(self.productos)
        total_paginas = max(1, (total + self.productos_por_pagina - 1) // self.productos_por_pagina)
        if self.pagina_actual < total_paginas:
            self.pagina_actual += 1
            self.renderizar_pagina()

    def filtrar_productos(self):
        query = self.ent_buscar.get().strip().lower()
        if not query:
            self.cargar_productos()
            return

        try:
            self.productos = self.servicio_inventario.filtrar_productos(query)
            self.pagina_actual = 1
            self.renderizar_pagina()
        except Exception as e:
            print("Error filtrando:", e)

    def buscar_por_codigo(self):
        from gestor_codigos_barra import GestorCodigosBarra
        GestorCodigosBarra(self)

    def mostrar_historial_precios(self):
        from kardex_inventario import KardexInventario
        prod_nom = self.producto_seleccionado[1] if self.producto_seleccionado else None
        prod_id = self.producto_seleccionado[0] if self.producto_seleccionado else None
        KardexInventario(self, producto_id=prod_id)

    def ordenar_productos(self):
        criterio = self.cmb_orden.get()
        if criterio == "Más antiguo":
            self.productos.sort(key=lambda x: x[0])
        elif criterio == "Más reciente":
            self.productos.sort(key=lambda x: x[0], reverse=True)
        elif criterio == "Mayor precio":
            self.productos.sort(key=lambda x: x[3] or 0, reverse=True)
        elif criterio == "Menor precio":
            self.productos.sort(key=lambda x: x[3] or 0)
        elif criterio == "Mayor stock":
            self.productos.sort(key=lambda x: x[5] or 0, reverse=True)
        elif criterio == "Menor stock":
            self.productos.sort(key=lambda x: x[5] or 0)
        elif criterio == "A-Z":
            self.productos.sort(key=lambda x: (x[1] or "").lower())
        self.renderizar_pagina()

    def abrir_agregar(self):
        ProductoModal(self, callback_refresh=self.cargar_productos)

    def abrir_editar(self, prod_id=None):
        if prod_id is None:
            if not self.producto_seleccionado:
                messagebox.showwarning("Atención", "Por favor seleccione un producto para editar.")
                return
            prod_id = self.producto_seleccionado[0]
        ProductoModal(self, callback_refresh=self.cargar_productos, producto_id=prod_id)

    def inactivar_producto(self):
        if not self.producto_seleccionado:
            messagebox.showwarning("Atención", "Por favor seleccione un producto para inactivar.")
            return

        prod_id = self.producto_seleccionado[0]
        prod_nom = self.producto_seleccionado[1]

        if messagebox.askyesno("Confirmar", f"¿Desea inactivar el producto '{prod_nom}'?"):
            try:
                self.servicio_inventario.desactivar(prod_id)
                messagebox.showinfo("Éxito", "Producto inactivado correctamente.")
                self.cargar_productos()
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo inactivar el producto: {e}")

    def filtrar_bajo_stock(self):
        from alerta_stock_bajo import AlertaStockBajo
        AlertaStockBajo(self)

    def mostrar_servicios(self):
        from servicios import Servicios
        Servicios(self)

    def mostrar_stock_min_ind(self):
        from stock_minimo_individual import StockMinimoIndividual
        StockMinimoIndividual(self)

    def exportar_excel(self):
        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("Archivo CSV", "*.csv")],
            initialfile="Inventario_Productos.csv"
        )
        if file_path:
            try:
                with open(file_path, mode="w", newline="", encoding="utf-8-sig") as f:
                    writer = csv.writer(f)
                    writer.writerow(["ID", "Producto", "Proveedor", "Precio", "Costo", "Stock", "Categoría", "Sucursal", "Estado"])
                    for p in self.productos:
                        writer.writerow([p[0], p[1], p[2], p[3], p[4], p[5], p[6], p[7], p[9] if len(p) > 9 else "Activo"])
                messagebox.showinfo("Exportación", "Inventario exportado exitosamente a CSV.")
            except Exception as e:
                messagebox.showerror("Error", f"Error al exportar inventario: {e}")
