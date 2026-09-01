import os
import shutil
import db_conexion as sqlite3
import sys
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageTk
from window_utils import posicionar_ventana
from servicios.servicio_inventario import ServicioInventario

class ProductoModal(tk.Toplevel):
    def __init__(self, parent, callback_refresh=None, producto_id=None):
        super().__init__(parent)
        self.parent = parent
        self.callback_refresh = callback_refresh
        self.producto_id = producto_id
        self.db_name = "database.db"
        self.servicio_inventario = ServicioInventario()
        self.images = {}
        self.image_path_selected = None

        if self.producto_id:
            self.title("Editar Producto")
        else:
            self.title("Agregar Producto")

        posicionar_ventana(self, 900, 530, parent)
        self.resizable(False, False)
        self.configure(bg="#C6D9E3")
        self.transient(parent)
        self.grab_set()
        try:
            self.iconbitmap(self.rutas('icono.ico'))
        except Exception:
            pass

        self.widgets()
        self.cargar_datos_combos()

        if self.producto_id:
            self.cargar_datos_producto()

    def rutas(self, ruta):
        try:
            rutabase = sys.__MEIPASS
        except Exception:
            rutabase = os.path.abspath(".")
        return os.path.join(rutabase, ruta)

    def widgets(self):
#============== GRUPO 1: INFORMACIÓN DEL PRODUCTO ==================================================#
        frame_info = tk.LabelFrame(
            self,
            text="Información del Producto",
            font=("sans", 12, "bold"),
            bg="#C6D9E3",
            fg="#1E293B",
            padx=12,
            pady=8
        )
        frame_info.place(x=15, y=10, width=410, height=380)

        # 1. Producto
        lbl_nom = tk.Label(frame_info, text="Producto:", font=("sans", 11, "bold"), bg="#C6D9E3", fg="#1E293B")
        lbl_nom.place(x=5, y=5)
        self.ent_nombre = ttk.Entry(frame_info, font=("sans", 10))
        self.ent_nombre.place(x=120, y=5, width=255, height=30)

        # 2. Código + icono barcode
        lbl_cod = tk.Label(frame_info, text="Código:", font=("sans", 11, "bold"), bg="#C6D9E3", fg="#1E293B")
        lbl_cod.place(x=5, y=40)
        self.ent_codigo = ttk.Entry(frame_info, font=("sans", 10))
        self.ent_codigo.place(x=120, y=40, width=220, height=30)

        ruta_barcode = self.rutas("icono/barcode.png")
        if os.path.exists(ruta_barcode):
            img_bar = Image.open(ruta_barcode).resize((24, 22), Image.Resampling.LANCZOS)
            self.images["barcode"] = ImageTk.PhotoImage(img_bar)
            btn_barcode = tk.Button(
                frame_info,
                image=self.images["barcode"],
                bg="white",
                relief="solid",
                bd=1,
                cursor="hand2",
                command=self.generar_codigo
            )
            btn_barcode.place(x=345, y=40, width=30, height=26)

        # 3. Proveedor
        lbl_prov = tk.Label(frame_info, text="Proveedor:", font=("sans", 11, "bold"), bg="#C6D9E3", fg="#1E293B")
        lbl_prov.place(x=5, y=75)
        self.cmb_proveedor = ttk.Combobox(frame_info, font=("sans", 10), state="readonly")
        self.cmb_proveedor.place(x=120, y=75, width=255, height=26)

        # 4. Costo
        lbl_costo = tk.Label(frame_info, text="Costo:", font=("sans", 11, "bold"), bg="#C6D9E3", fg="#1E293B")
        lbl_costo.place(x=5, y=110)
        self.ent_costo = ttk.Entry(frame_info, font=("sans", 10))
        self.ent_costo.place(x=120, y=110, width=255, height=30)
        self.ent_costo.bind("<KeyRelease>", self.calcular_precio_por_utilidad)

        # 5. Stock
        lbl_stock = tk.Label(frame_info, text="Stock:", font=("sans", 11, "bold"), bg="#C6D9E3", fg="#1E293B")
        lbl_stock.place(x=5, y=145)
        self.ent_stock = ttk.Entry(frame_info, font=("sans", 10))
        self.ent_stock.place(x=120, y=145, width=255, height=30)

        # 6. Categoria
        lbl_cat = tk.Label(frame_info, text="Categoria:", font=("sans", 11, "bold"), bg="#C6D9E3", fg="#1E293B")
        lbl_cat.place(x=5, y=180)
        self.cmb_categoria = ttk.Combobox(frame_info, font=("sans", 10), state="readonly")
        self.cmb_categoria.place(x=120, y=180, width=255, height=26)

        # 7. Sucursal
        lbl_suc = tk.Label(frame_info, text="Sucursal:", font=("sans", 11, "bold"), bg="#C6D9E3", fg="#1E293B")
        lbl_suc.place(x=5, y=215)
        self.cmb_sucursal = ttk.Combobox(frame_info, font=("sans", 10), state="readonly")
        self.cmb_sucursal.place(x=120, y=215, width=255, height=26)

        # 8. Estado
        lbl_est = tk.Label(frame_info, text="Estado:", font=("sans", 11, "bold"), bg="#C6D9E3", fg="#1E293B")
        lbl_est.place(x=5, y=250)
        self.cmb_estado = ttk.Combobox(frame_info, values=["Activo", "Inactivo"], font=("sans", 10), state="readonly")
        self.cmb_estado.current(0)
        self.cmb_estado.place(x=120, y=250, width=255, height=26)

        # 9. Impuesto
        lbl_imp = tk.Label(frame_info, text="Impuesto:", font=("sans", 11, "bold"), bg="#C6D9E3", fg="#1E293B")
        lbl_imp.place(x=5, y=285)
        self.cmb_impuesto = ttk.Combobox(frame_info, values=["Exento", "IVA 19%", "IVA 5%", "ICO 8%"], font=("sans", 10), state="readonly")
        self.cmb_impuesto.current(0)
        self.cmb_impuesto.place(x=120, y=285, width=255, height=26)

#============== SECCIÓN SUPERIOR DERECHA: IMAGEN ===================================================#
        self.frame_img_preview = tk.Frame(self, bg="white", highlightbackground="#9FB8C7", highlightthickness=1)
        self.frame_img_preview.place(x=450, y=20, width=170, height=170)

        self.lbl_preview = tk.Label(self.frame_img_preview, bg="white", text="Sin Imagen\n(PNG/JPG)", fg="#94A3B8", font=("sans", 10, "italic"))
        self.lbl_preview.pack(fill="both", expand=True)

        lbl_formatos = tk.Label(
            self,
            text="Formatos aceptados: PNG, JPG, JPEG\nIdealmente sin fondo (PNG)",
            font=("sans", 9, "italic"),
            bg="#C6D9E3",
            fg="#475569",
            justify="center"
        )
        lbl_formatos.place(x=435, y=195, width=200)

        lbl_nota_mayorista = tk.Label(
            self,
            text="Si no utiliza precio al por mayor,\ndeje vacías las casillas de\nPrecio Mayorista y Cantidad Mínima",
            font=("sans", 9, "italic"),
            bg="#C6D9E3",
            fg="#475569",
            justify="center"
        )
        lbl_nota_mayorista.place(x=650, y=80, width=230)

#============== GRUPO 2: CONFIGURACIÓN DEL PRECIO ==================================================#
        frame_precio = tk.LabelFrame(
            self,
            text="Configuración del Precio",
            font=("sans", 11, "bold"),
            bg="#C6D9E3",
            fg="#1E293B",
            padx=10,
            pady=8
        )
        frame_precio.place(x=435, y=240, width=225, height=150)

        lbl_util = tk.Label(frame_precio, text="% Utilidad:", font=("sans", 10, "bold"), bg="#C6D9E3", fg="#1E293B")
        lbl_util.place(x=5, y=5)
        self.ent_utilidad = ttk.Entry(frame_precio, font=("sans", 10), width=6)
        self.ent_utilidad.place(x=90, y=5)
        self.ent_utilidad.bind("<KeyRelease>", self.calcular_precio_por_utilidad)

        self.var_usa_utilidad = tk.BooleanVar(value=False)
        self.chk_utilidad = tk.Checkbutton(
            frame_precio,
            text="Si",
            variable=self.var_usa_utilidad,
            bg="#C6D9E3",
            font=("sans", 9, "bold"),
            command=self.calcular_precio_por_utilidad
        )
        self.chk_utilidad.place(x=155, y=5)

        lbl_pre = tk.Label(frame_precio, text="Precio:", font=("sans", 10, "bold"), bg="#C6D9E3", fg="#1E293B")
        lbl_pre.place(x=5, y=40)
        self.ent_precio = ttk.Entry(frame_precio, font=("sans", 10), width=12)
        self.ent_precio.place(x=90, y=40)
        self.ent_precio.bind("<KeyRelease>", self.actualizar_precio_final)

        lbl_final_tag = tk.Label(frame_precio, text="Precio Final:", font=("sans", 10, "bold"), bg="#C6D9E3", fg="#1E293B")
        lbl_final_tag.place(x=5, y=80)
        self.lbl_precio_final = tk.Label(frame_precio, text="$ 0.00", font=("sans", 11, "bold"), bg="#C6D9E3", fg="#166534")
        self.lbl_precio_final.place(x=95, y=79)

#============== GRUPO 3: PRECIO MAYORISTA ==========================================================#
        frame_mayorista = tk.LabelFrame(
            self,
            text="Precio Mayorista",
            font=("sans", 11, "bold"),
            bg="#C6D9E3",
            fg="#1E293B",
            padx=10,
            pady=8
        )
        frame_mayorista.place(x=670, y=240, width=215, height=150)

        lbl_pm = tk.Label(frame_mayorista, text="P. Mayorista:", font=("sans", 10, "bold"), bg="#C6D9E3", fg="#1E293B")
        lbl_pm.place(x=5, y=10)
        self.ent_pm = ttk.Entry(frame_mayorista, font=("sans", 10), width=10)
        self.ent_pm.place(x=105, y=10)

        lbl_cant_m = tk.Label(frame_mayorista, text="Cant. Mín.:", font=("sans", 10, "bold"), bg="#C6D9E3", fg="#1E293B")
        lbl_cant_m.place(x=5, y=50)
        self.ent_cant_m = ttk.Entry(frame_mayorista, font=("sans", 10), width=10)
        self.ent_cant_m.place(x=105, y=50)

#============== GRUPO 4: BOTONES DE ACCIÓN ========================================================#
        frame_opc = tk.LabelFrame(
            self,
            text="Opciones",
            font=("sans", 11, "bold"),
            bg="#C6D9E3",
            fg="#1E293B",
            padx=10,
            pady=6
        )
        frame_opc.place(x=15, y=410, width=870, height=95)

        # 1. Guardar
        ruta_guardar = self.rutas("icono/guardar.png")
        if os.path.exists(ruta_guardar):
            img_g = Image.open(ruta_guardar).resize((24, 24), Image.Resampling.LANCZOS)
            self.images["guardar"] = ImageTk.PhotoImage(img_g)
            ico_g = self.images["guardar"]
        else:
            ico_g = None

        btn_guardar = tk.Button(
            frame_opc,
            text="  Guardar",
            image=ico_g,
            compound=tk.LEFT,
            font=("sans", 12, "bold"),
            bg="#EBEFF2",
            fg="#1E293B",
            relief="raised",
            bd=2,
            cursor="hand2",
            command=self.guardar_producto
        )
        btn_guardar.place(x=50, y=10, width=150, height=42)

        # 2. Cancelar
        ruta_cancelar = self.rutas("icono/cancelar.png")
        if os.path.exists(ruta_cancelar):
            img_c = Image.open(ruta_cancelar).resize((24, 24), Image.Resampling.LANCZOS)
            self.images["cancelar"] = ImageTk.PhotoImage(img_c)
            ico_c = self.images["cancelar"]
        else:
            ico_c = None

        btn_cancelar = tk.Button(
            frame_opc,
            text="  Cancelar",
            image=ico_c,
            compound=tk.LEFT,
            font=("sans", 12, "bold"),
            bg="#EBEFF2",
            fg="#1E293B",
            relief="raised",
            bd=2,
            cursor="hand2",
            command=self.destroy
        )
        btn_cancelar.place(x=230, y=10, width=150, height=42)

        # 3. Cargar Imagen
        ruta_foto = self.rutas("icono/foto.png")
        if os.path.exists(ruta_foto):
            img_f = Image.open(ruta_foto).resize((24, 24), Image.Resampling.LANCZOS)
            self.images["foto"] = ImageTk.PhotoImage(img_f)
            ico_f = self.images["foto"]
        else:
            ico_f = None

        btn_foto = tk.Button(
            frame_opc,
            text="  Cargar Imagen",
            image=ico_f,
            compound=tk.LEFT,
            font=("sans", 12, "bold"),
            bg="#EBEFF2",
            fg="#1E293B",
            relief="raised",
            bd=2,
            cursor="hand2",
            command=self.seleccionar_imagen
        )
        btn_foto.place(x=420, y=10, width=180, height=42)

    def generar_codigo(self):
        import random
        codigo = "770" + str(random.randint(1000000000, 9999999999))
        self.ent_codigo.delete(0, tk.END)
        self.ent_codigo.insert(0, codigo)

    def calcular_precio_por_utilidad(self, event=None):
        if self.var_usa_utilidad.get():
            try:
                costo_val = float(self.ent_costo.get().strip() or 0)
                util_val = float(self.ent_utilidad.get().strip() or 0)
                if costo_val > 0 and util_val >= 0:
                    precio_calc = costo_val * (1 + (util_val / 100.0))
                    self.ent_precio.delete(0, tk.END)
                    self.ent_precio.insert(0, f"{precio_calc:.2f}")
                    self.actualizar_precio_final()
            except ValueError:
                pass
        else:
            self.actualizar_precio_final()

    def actualizar_precio_final(self, event=None):
        try:
            precio_val = float(self.ent_precio.get().strip() or 0)
            self.lbl_precio_final.config(text=f"$ {precio_val:,.2f}")
        except ValueError:
            self.lbl_precio_final.config(text="$ 0.00")

    def seleccionar_imagen(self):
        file_path = filedialog.askopenfilename(
            title="Seleccionar Imagen del Producto",
            filetypes=[("Archivos de Imagen", "*.png;*.jpg;*.jpeg;*.webp")]
        )
        if file_path:
            self.image_path_selected = file_path
            self.mostrar_preview_imagen(file_path)

    def mostrar_preview_imagen(self, ruta_img):
        try:
            if os.path.exists(ruta_img):
                img = Image.open(ruta_img)
                img.thumbnail((160, 160), Image.Resampling.LANCZOS)
                self.images["preview"] = ImageTk.PhotoImage(img)
                self.lbl_preview.config(image=self.images["preview"], text="")
        except Exception:
            self.lbl_preview.config(text="Error al cargar", image="")

    def cargar_datos_combos(self):
        os.makedirs("productos", exist_ok=True)
        try:
            provs, cats, sucs = self.servicio_inventario.catalogos_producto()
            self.cmb_proveedor["values"] = provs
            self.cmb_categoria["values"] = cats
            self.cmb_sucursal["values"] = sucs
            if provs:
                self.cmb_proveedor.current(0)
            if cats:
                self.cmb_categoria.current(0)
            if sucs:
                self.cmb_sucursal.current(0)
        except Exception as e:
            print("Error cargando combos:", e)

    def cargar_datos_producto(self):
        try:
            prod = self.servicio_inventario.obtener_producto(self.producto_id)
            if prod:
                    self.ent_nombre.insert(0, prod[1] or "")
                    self.ent_codigo.insert(0, prod[8] or "")
                    if prod[2] in self.cmb_proveedor["values"]:
                        self.cmb_proveedor.set(prod[2])
                    self.ent_precio.insert(0, str(prod[3] or 0))
                    self.ent_costo.insert(0, str(prod[4] or 0))
                    self.ent_stock.insert(0, str(prod[5] or 0))
                    if prod[6] in self.cmb_categoria["values"]:
                        self.cmb_categoria.set(prod[6])
                    if prod[7] in self.cmb_sucursal["values"]:
                        self.cmb_sucursal.set(prod[7])
                    if prod[10] in self.cmb_estado["values"]:
                        self.cmb_estado.set(prod[10])

                    self.actualizar_precio_final()

                    img_path = prod[9]
                    if img_path and os.path.exists(img_path):
                        self.image_path_selected = img_path
                        self.mostrar_preview_imagen(img_path)
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo cargar el producto: {e}")

    def guardar_producto(self):
        nombre = self.ent_nombre.get().strip()
        codigo = self.ent_codigo.get().strip()
        proveedor = self.cmb_proveedor.get().strip()
        categoria = self.cmb_categoria.get().strip()
        sucursal = self.cmb_sucursal.get().strip()
        estado = self.cmb_estado.get().strip()

        if not nombre:
            messagebox.showerror("Error", "El nombre del producto es obligatorio.")
            return

        if len(codigo) > 80:
            messagebox.showerror("Error", "El código de barras no puede superar 80 caracteres.")
            return

        try:
            costo = float(self.ent_costo.get().strip() or 0)
            precio = float(self.ent_precio.get().strip() or 0)
            stock = int(self.ent_stock.get().strip() or 0)
        except ValueError:
            messagebox.showerror("Error", "Costo, precio y stock deben ser valores numéricos válidos.")
            return

        # Guardar imagen en la carpeta productos/ si es nueva
        ruta_final_img = ""
        if self.image_path_selected:
            os.makedirs("productos", exist_ok=True)
            ext = os.path.splitext(self.image_path_selected)[1]
            nom_img = f"prod_{nombre.replace(' ', '_')[:20]}{ext}"
            ruta_destino = os.path.join("productos", nom_img)
            try:
                if os.path.abspath(self.image_path_selected) != os.path.abspath(ruta_destino):
                    shutil.copyfile(self.image_path_selected, ruta_destino)
                ruta_final_img = ruta_destino
            except Exception:
                ruta_final_img = self.image_path_selected

        try:
            self.servicio_inventario.guardar_producto(self.producto_id, nombre, proveedor, precio, costo, stock, categoria, sucursal, codigo, ruta_final_img, estado)
            messagebox.showinfo("Éxito", "Producto actualizado correctamente." if self.producto_id else "Producto registrado correctamente.")

            if self.callback_refresh:
                self.callback_refresh()

            self.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"Error al guardar en la base de datos: {e}")
