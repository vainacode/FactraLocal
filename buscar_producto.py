import os
import db_conexion as sqlite3
import sys
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
from window_utils import posicionar_ventana
from servicios.servicio_inventario import ServicioInventario

class BuscarProductoModal(tk.Toplevel):
    def __init__(self, parent, callback_select=None):
        super().__init__(parent)
        self.parent = parent
        self.callback_select = callback_select
        self.title("Buscar Producto")
        posicionar_ventana(self, 820, 600, parent)
        self.resizable(False, False)
        self.configure(bg="#C6D9E3")
        self.transient(parent)
        self.grab_set()
        try:
            self.iconbitmap(self.rutas('icono.ico'))
        except Exception:
            pass

        self.db_name = "database.db"
        self.servicio_inventario = ServicioInventario()
        self.images = {}
        self.productos_db = []
        self.producto_actual = None

        self.widgets()
        self.cargar_productos_combo()

    def rutas(self, ruta):
        try:
            rutabase = sys.__MEIPASS
        except Exception:
            rutabase = os.path.abspath(".")
        return os.path.join(rutabase, ruta)

    def widgets(self):
#============== 1. GRUPO BUSCAR PRODUCTO ============================================================#
        frame_bus = tk.LabelFrame(
            self,
            text="Buscar Producto",
            font=("sans", 14, "bold"),
            bg="#C6D9E3",
            fg="#1E293B",
            padx=12,
            pady=10
        )
        frame_bus.place(x=20, y=10, width=480, height=110)

        lbl_bp = tk.Label(frame_bus, text="Buscar producto:", font=("sans", 12, "bold"), bg="#C6D9E3", fg="#1E293B")
        lbl_bp.place(x=10, y=10)

        self.cmb_buscar = ttk.Combobox(frame_bus, font=("sans", 11))
        self.cmb_buscar.place(x=10, y=38, width=440, height=30)
        self.cmb_buscar.bind("<<ComboboxSelected>>", self.al_seleccionar_producto)
        self.cmb_buscar.bind("<KeyRelease>", self.al_escribir_filtro)

#============== 2. GRUPO INFORMACIÓN DEL PRODUCTO ===================================================#
        frame_info = tk.LabelFrame(
            self,
            text="Información del Producto",
            font=("sans", 14, "bold"),
            bg="#C6D9E3",
            fg="#1E293B",
            padx=12,
            pady=8
        )
        frame_info.place(x=20, y=130, width=480, height=395)

        campos = [
            ("Nombre:", "lbl_nombre", "#1E293B", 10),
            ("Precio:", "lbl_precio", "#1E293B", 42),
            ("Proveedor:", "lbl_proveedor", "#1E293B", 74),
            ("Stock:", "lbl_stock", "#1E293B", 106),
            ("Categoria:", "lbl_categoria", "#1E293B", 138),
            ("Sucursal:", "lbl_sucursal", "#1E293B", 170),
            ("Impuesto:", "lbl_impuesto", "#1E293B", 202),
            ("P. Mayorista:", "lbl_p_mayor", "#1E293B", 234),
            ("Cant. Mínima:", "lbl_cant_min", "#1E293B", 266),
            ("Precio Venta:", "lbl_precio_venta", "#16A34A", 305),
        ]

        self.labels_val = {}
        for tag, key, color, y_pos in campos:
            f_size = 12 if key == "lbl_precio_venta" else 11
            lbl_t = tk.Label(frame_info, text=tag, font=("sans", f_size, "bold"), bg="#C6D9E3", fg="#1E293B")
            lbl_t.place(x=10, y=y_pos)

            lbl_v = tk.Label(frame_info, text="-", font=("sans", f_size, "bold" if key == "lbl_precio_venta" else "normal"), bg="#C6D9E3", fg=color)
            lbl_v.place(x=150, y=y_pos)
            self.labels_val[key] = lbl_v

#============== 3. PANEL DERECHO: IMAGEN DEL PRODUCTO ===============================================#
        frame_img_card = tk.Frame(self, bg="white", highlightbackground="#B8C4CE", highlightthickness=1)
        frame_img_card.place(x=525, y=25, width=270, height=300)

        self.lbl_img = tk.Label(frame_img_card, text="📦\nSin imagen", font=("sans", 13), bg="white", fg="#64748B")
        self.lbl_img.pack(fill="both", expand=True, padx=10, pady=10)

        lbl_cap = tk.Label(self, text="Imagen del producto", font=("sans", 10, "italic"), bg="#C6D9E3", fg="#64748B")
        lbl_cap.place(x=590, y=335)

        frame_lista = tk.LabelFrame(
            self, text="Productos disponibles", font=("sans", 11, "bold"),
            bg="#C6D9E3", fg="#1E293B"
        )
        frame_lista.place(x=525, y=355, width=270, height=170)
        self.tabla_productos = ttk.Treeview(
            frame_lista, columns=("codigo", "nombre", "precio", "stock"),
            show="headings", selectmode="browse", height=6
        )
        for col, title, width in (("codigo", "Código", 48), ("nombre", "Producto", 110), ("precio", "Precio", 62), ("stock", "Stock", 45)):
            self.tabla_productos.heading(col, text=title)
            self.tabla_productos.column(col, width=width, anchor="center")
        self.tabla_productos.pack(fill="both", expand=True, padx=5, pady=5)
        self.tabla_productos.bind("<<TreeviewSelect>>", self.al_seleccionar_fila)
        self.tabla_productos.bind("<Double-1>", lambda e: self.seleccionar())

#============== 4. BOTONES INFERIORES ===============================================================#
        ruta_limp = self.rutas("icono/limpiar.png")
        if os.path.exists(ruta_limp):
            img_l = Image.open(ruta_limp).resize((22, 22), Image.Resampling.LANCZOS)
            self.images["limp_bp"] = ImageTk.PhotoImage(img_l)
            ico_l = self.images["limp_bp"]
        else:
            ico_l = None

        btn_limp = tk.Button(
            self,
            text="  Limpiar",
            image=ico_l,
            compound=tk.LEFT,
            font=("sans", 11, "bold"),
            bg="#EBEFF2",
            fg="#1E293B",
            relief="raised",
            bd=2,
            cursor="hand2",
            command=self.limpiar
        )
        btn_limp.place(x=130, y=540, width=130, height=40)

        btn_sel = tk.Button(
            self, text="  Seleccionar", font=("sans", 11, "bold"),
            bg="#DCFCE7", fg="#166534", relief="raised", bd=2,
            cursor="hand2", command=self.seleccionar
        )
        btn_sel.place(x=5, y=540, width=120, height=40)

        ruta_close = self.rutas("icono/cancelar.png")
        if os.path.exists(ruta_close):
            img_c = Image.open(ruta_close).resize((22, 22), Image.Resampling.LANCZOS)
            self.images["close_bp"] = ImageTk.PhotoImage(img_c)
            ico_c = self.images["close_bp"]
        else:
            ico_c = None

        btn_close = tk.Button(
            self,
            text="  Cerrar",
            image=ico_c,
            compound=tk.LEFT,
            font=("sans", 11, "bold"),
            bg="#EBEFF2",
            fg="#1E293B",
            relief="raised",
            bd=2,
            cursor="hand2",
            command=self.destroy
        )
        btn_close.place(x=340, y=540, width=130, height=40)

    def cargar_productos_combo(self):
        try:
            self.productos_db = self.servicio_inventario.listar_productos()

            nombres = [p[1] for p in self.productos_db]
            self.cmb_buscar["values"] = nombres
            self.refrescar_lista()
            if self.productos_db:
                self.mostrar_info_producto(self.productos_db[0])
        except Exception as e:
            print("Error cargando productos en modal de búsqueda:", e)

    def al_seleccionar_producto(self, event=None):
        nom = self.cmb_buscar.get().strip()
        for p in self.productos_db:
            if p[1] == nom:
                self.mostrar_info_producto(p)
                self.seleccionar_fila_producto(p)
                break

    def al_escribir_filtro(self, event=None):
        texto = self.cmb_buscar.get().strip().lower()
        self.refrescar_lista(texto)
        for p in self.productos_db:
            if not texto or texto in p[1].lower() or str(p[0]) == texto:
                self.mostrar_info_producto(p)
                break

    def refrescar_lista(self, filtro=""):
        filtro = (filtro or "").lower()
        for item in self.tabla_productos.get_children():
            self.tabla_productos.delete(item)
        for p in self.productos_db:
            if filtro and filtro not in str(p[0]).lower() and filtro not in str(p[1]).lower():
                continue
            self.tabla_productos.insert("", tk.END, iid=str(p[0]), values=(p[0], p[1], f"{float(p[2] or 0):,.2f}", p[4]))

    def seleccionar_fila_producto(self, producto):
        try:
            self.tabla_productos.selection_set(str(producto[0]))
            self.tabla_productos.focus(str(producto[0]))
        except Exception:
            pass

    def al_seleccionar_fila(self, event=None):
        seleccion = self.tabla_productos.selection()
        if not seleccion:
            return
        prod_id = int(seleccion[0])
        producto = next((p for p in self.productos_db if int(p[0]) == prod_id), None)
        if producto:
            self.mostrar_info_producto(producto)

    def seleccionar(self):
        if not self.producto_actual:
            return
        if self.callback_select:
            self.callback_select(self.producto_actual)
        self.destroy()

    def mostrar_info_producto(self, prod):
        self.producto_actual = prod
        # id, nombre, precio, costo, stock, categoria, sucursal, proveedor, image_path
        p_id, nom, precio, costo, stock, cat, suc, prov, img_path = prod

        self.labels_val["lbl_nombre"].config(text=nom)
        self.labels_val["lbl_precio"].config(text=f"{precio:,.2f}")
        self.labels_val["lbl_proveedor"].config(text=prov or "-")
        self.labels_val["lbl_stock"].config(text=str(stock))
        self.labels_val["lbl_categoria"].config(text=cat or "Despensa")
        self.labels_val["lbl_sucursal"].config(text=suc or "PRINCIPAL")
        self.labels_val["lbl_impuesto"].config(text="Exento")
        self.labels_val["lbl_p_mayor"].config(text="No aplica")
        self.labels_val["lbl_cant_min"].config(text="No aplica")
        self.labels_val["lbl_precio_venta"].config(text=f"{precio:,.2f}")

        # Cargar imagen si existe
        ruta_img = img_path if (img_path and os.path.exists(img_path)) else self.rutas(f"imagenes/{nom}.png")
        if not os.path.exists(ruta_img):
            ruta_img = self.rutas("imagenes/Cafe Juan Valdez 95 gr Chocolate.png")

        if os.path.exists(ruta_img):
            try:
                img_raw = Image.open(ruta_img).resize((220, 260), Image.Resampling.LANCZOS)
                self.images["prod_preview_bp"] = ImageTk.PhotoImage(img_raw)
                self.lbl_img.config(image=self.images["prod_preview_bp"], text="")
            except Exception:
                self.lbl_img.config(image="", text="📦\nSin imagen")
        else:
            self.lbl_img.config(image="", text="📦\nSin imagen")

    def limpiar(self):
        self.cmb_buscar.set("")
        for key in self.labels_val:
            self.labels_val[key].config(text="-")
        self.lbl_img.config(image="", text="📦\nSin imagen")
