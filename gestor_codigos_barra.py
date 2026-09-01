import os
import random
from io import BytesIO
import barcode
import db_conexion as sqlite3
import sys
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from barcode.writer import ImageWriter
from PIL import Image, ImageTk
from window_utils import posicionar_ventana
from servicios.servicio_inventario import ServicioInventario

class GestorCodigosBarra(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.title("Gestor de Códigos de Barra - Inventario")
        posicionar_ventana(self, 980, 600, parent)
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
        self.productos = []
        self.producto_seleccionado = None
        self.barcode_image = None

        self.widgets()
        self.cargar_productos()

    def rutas(self, ruta):
        try:
            rutabase = sys.__MEIPASS
        except Exception:
            rutabase = os.path.abspath(".")
        return os.path.join(rutabase, ruta)

    def widgets(self):
#============== 1. HEADER ==========================================================================#
        lbl_title = tk.Label(
            self,
            text="GESTOR DE CÓDIGOS DE BARRA",
            font=("sans", 20, "bold"),
            bg="#C6D9E3",
            fg="#1E293B"
        )
        lbl_title.place(relx=0.5, y=25, anchor="center")

#============== 2. PANEL IZQUIERDO ==================================================================#
        frame_izq = tk.LabelFrame(
            self,
            text="Productos del Inventario",
            font=("sans", 12, "bold"),
            bg="#C6D9E3",
            fg="#1E293B",
            padx=10,
            pady=8
        )
        frame_izq.place(x=15, y=55, width=460, height=525)

        lbl_b = tk.Label(frame_izq, text="Buscar:", font=("sans", 11, "bold"), bg="#C6D9E3", fg="#1E293B")
        lbl_b.place(x=5, y=8)

        self.ent_buscar = ttk.Entry(frame_izq, font=("sans", 10))
        self.ent_buscar.place(x=70, y=6, width=315, height=28)
        self.ent_buscar.bind("<KeyRelease>", lambda e: self.filtrar_productos())

        ruta_rel = self.rutas("icono/actualizar1.png")
        if not os.path.exists(ruta_rel):
            ruta_rel = self.rutas("icono/actualizar.png")

        if os.path.exists(ruta_rel):
            img_r = Image.open(ruta_rel).resize((22, 22), Image.Resampling.LANCZOS)
            self.images["rel_bar"] = ImageTk.PhotoImage(img_r)
            btn_r = tk.Button(frame_izq, image=self.images["rel_bar"], bg="#22C55E", relief="solid", bd=1, cursor="hand2", command=self.cargar_productos)
            btn_r.place(x=395, y=6, width=32, height=28)

        # Tabla de productos
        style = ttk.Style()
        style.configure("Bar.Treeview.Heading", font=("sans", 8, "bold"), background="#E0E6ED")
        style.configure("Bar.Treeview", font=("sans", 8), rowheight=22)

        cols = ("id", "nombre", "codigo")
        self.tabla = ttk.Treeview(frame_izq, columns=cols, show="headings", style="Bar.Treeview")
        self.tabla.place(x=5, y=42, width=415, height=445)

        self.tabla.heading("id", text="ID")
        self.tabla.heading("nombre", text="Nombre")
        self.tabla.heading("codigo", text="Código Actual")

        self.tabla.column("id", width=35, anchor="center")
        self.tabla.column("nombre", width=250, anchor="w")
        self.tabla.column("codigo", width=130, anchor="center")

        scroll_y = ttk.Scrollbar(frame_izq, orient="vertical", command=self.tabla.yview)
        self.tabla.configure(yscrollcommand=scroll_y.set)
        scroll_y.place(x=422, y=42, height=445)

        self.tabla.bind("<<TreeviewSelect>>", self.al_seleccionar_producto)

#============== 3. PANEL DERECHO: GENERADOR DE CÓDIGO ===============================================#
        frame_der = tk.LabelFrame(
            self,
            text="Generador de Código de Barra",
            font=("sans", 12, "bold"),
            bg="#C6D9E3",
            fg="#1E293B",
            padx=10,
            pady=8
        )
        frame_der.place(x=495, y=55, width=470, height=525)

        self.lbl_info_prod = tk.Label(
            frame_der,
            text="Seleccione un producto para administrar su código de barras",
            font=("sans", 9, "bold"),
            bg="#C6D9E3",
            fg="#1E293B",
            justify="left"
        )
        self.lbl_info_prod.place(x=10, y=5)

        # Tipo
        lbl_tipo = tk.Label(frame_der, text="Tipo:", font=("sans", 12, "bold"), bg="#C6D9E3", fg="#1E293B")
        lbl_tipo.place(x=15, y=55)

        self.cmb_tipo = ttk.Combobox(frame_der, values=["EAN-13", "CODE-128", "UPC-A"], font=("sans", 11), state="readonly")
        self.cmb_tipo.current(0)
        self.cmb_tipo.place(x=85, y=55, width=170, height=30)

        # Código + Botón Aleatorio
        lbl_cod = tk.Label(frame_der, text="Código:", font=("sans", 12, "bold"), bg="#C6D9E3", fg="#1E293B")
        lbl_cod.place(x=15, y=100)

        self.ent_cod = ttk.Entry(frame_der, font=("sans", 12), justify="center")
        self.ent_cod.place(x=110, y=98, width=195, height=32)

        btn_rand = tk.Button(
            frame_der,
            text="  Aleatorio",
            image=self.images.get("rel_bar"),
            compound=tk.LEFT,
            font=("sans", 10, "bold"),
            bg="#22C55E",
            fg="white",
            relief="raised",
            bd=2,
            cursor="hand2",
            command=self.generar_aleatorio
        )
        btn_rand.place(x=315, y=98, width=125, height=32)

        # Botón Vista Previa
        ruta_eye = self.rutas("icono/mostrar.png")
        if os.path.exists(ruta_eye):
            img_e = Image.open(ruta_eye).resize((18, 18), Image.Resampling.LANCZOS)
            self.images["eye_bar"] = ImageTk.PhotoImage(img_e)
            ico_e = self.images["eye_bar"]
        else:
            ico_e = None

        btn_vp = tk.Button(
            frame_der,
            text="  Vista Previa",
            image=ico_e,
            compound=tk.LEFT,
            font=("sans", 10, "bold"),
            bg="#EBEFF2",
            fg="#1E293B",
            relief="raised",
            bd=2,
            cursor="hand2",
            command=self.dibujar_codigo_barras
        )
        btn_vp.place(relx=0.5, y=160, width=150, height=32, anchor="center")

        # Tarjeta Visual del Código de Barras
        self.card_barcode = tk.Frame(frame_der, bg="white", highlightbackground="#94A3B8", highlightthickness=1)
        self.card_barcode.place(x=20, y=185, width=410, height=140)

        self.canvas_barcode = tk.Canvas(self.card_barcode, bg="white", highlightthickness=0)
        self.canvas_barcode.pack(fill="both", expand=True)

        self.lbl_cod_sub = tk.Label(frame_der, text="Sin código asignado", font=("sans", 10, "bold"), bg="#C6D9E3", fg="#1E293B")
        self.lbl_cod_sub.place(relx=0.5, y=340, anchor="center")

        # Botón Guardar en Producto
        ruta_save = self.rutas("icono/guardar.png")
        if os.path.exists(ruta_save):
            img_s = Image.open(ruta_save).resize((22, 22), Image.Resampling.LANCZOS)
            self.images["save_bar_ico"] = ImageTk.PhotoImage(img_s)
            ico_s = self.images["save_bar_ico"]
        else:
            ico_s = None

        btn_save = tk.Button(
            frame_der,
            text="  Guardar en Producto",
            image=ico_s,
            compound=tk.LEFT,
            font=("sans", 11, "bold"),
            bg="#EBEFF2",
            fg="#1E293B",
            relief="raised",
            bd=2,
            cursor="hand2",
            command=self.guardar_en_producto
        )
        btn_save.place(relx=0.5, y=385, width=230, height=40, anchor="center")

        # Botones Copiar e Imagen
        ruta_cop = self.rutas("icono/codigo.png")
        if not os.path.exists(ruta_cop):
            ruta_cop = self.rutas("icono/barcode.png")

        if os.path.exists(ruta_cop):
            img_cp = Image.open(ruta_cop).resize((20, 20), Image.Resampling.LANCZOS)
            self.images["cop_ico"] = ImageTk.PhotoImage(img_cp)
            ico_cp = self.images["cop_ico"]
        else:
            ico_cp = None

        btn_cop = tk.Button(
            frame_der,
            text="  Copiar",
            image=ico_cp,
            compound=tk.LEFT,
            font=("sans", 10, "bold"),
            bg="#EBEFF2",
            fg="#1E293B",
            relief="raised",
            bd=2,
            cursor="hand2",
            command=self.copiar_codigo
        )
        btn_cop.place(x=105, y=425, width=115, height=36)

        ruta_fot = self.rutas("icono/foto.png")
        if os.path.exists(ruta_fot):
            img_ft = Image.open(ruta_fot).resize((20, 20), Image.Resampling.LANCZOS)
            self.images["fot_ico"] = ImageTk.PhotoImage(img_ft)
            ico_ft = self.images["fot_ico"]
        else:
            ico_ft = None

        btn_fot = tk.Button(
            frame_der,
            text="  Imagen",
            image=ico_ft,
            compound=tk.LEFT,
            font=("sans", 10, "bold"),
            bg="#EBEFF2",
            fg="#1E293B",
            relief="raised",
            bd=2,
            cursor="hand2",
            command=self.guardar_imagen_barcode
        )
        btn_fot.place(x=235, y=425, width=115, height=36)

    def cargar_productos(self):
        try:
            with sqlite3.connect(self.db_name) as conn:
                cur = conn.cursor()
                cur.execute("SELECT id, nombre, precio, codigo_barra FROM inventario WHERE estado != 'Inactivo' OR estado IS NULL")
                self.productos = cur.fetchall()
            self.renderizar_tabla()
        except Exception as e:
            print("Error cargando productos:", e)

    def renderizar_tabla(self):
        for r in self.tabla.get_children():
            self.tabla.delete(r)

        for p in self.productos:
            cod = p[3] or "-"
            self.tabla.insert("", tk.END, values=(p[0], p[1], cod))

        self.dibujar_codigo_barras()

    def al_seleccionar_producto(self, event=None):
        sel = self.tabla.selection()
        if not sel:
            return
        vals = self.tabla.item(sel[0], "values")
        if vals:
            self.producto_seleccionado = vals
            self.lbl_info_prod.config(text=f"Producto: {vals[1]}\nCódigo actual: {vals[2]}")
            self.ent_cod.delete(0, tk.END)
            if vals[2] != "-":
                self.ent_cod.insert(0, vals[2])
            self.dibujar_codigo_barras()

    def generar_aleatorio(self):
        tipo = self.cmb_tipo.get()
        if tipo == "EAN-13":
            cod = "".join(random.choice("0123456789") for _ in range(12))
        elif tipo == "UPC-A":
            cod = "".join(random.choice("0123456789") for _ in range(11))
        else:
            cod = "".join(random.choice("0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ") for _ in range(10))
        self.ent_cod.delete(0, tk.END)
        self.ent_cod.insert(0, cod)
        self.dibujar_codigo_barras()

    def _generar_imagen_barcode(self, codigo):
        """Valida y genera una imagen de barras real, no una textura decorativa."""
        tipo = self.cmb_tipo.get() or "CODE-128"
        nombre = {"EAN-13": "ean13", "UPC-A": "upca", "CODE-128": "code128"}[tipo]
        valor = codigo.strip()
        if tipo in ("EAN-13", "UPC-A") and not valor.isdigit():
            raise ValueError(f"{tipo} solo admite dígitos.")
        if tipo == "EAN-13" and len(valor) not in (12, 13):
            raise ValueError("EAN-13 requiere 12 dígitos (el sistema calcula el verificador) o 13 válidos.")
        if tipo == "UPC-A" and len(valor) not in (11, 12):
            raise ValueError("UPC-A requiere 11 dígitos (el sistema calcula el verificador) o 12 válidos.")
        if tipo == "CODE-128" and len(valor) > 80:
            raise ValueError("CODE-128 no puede superar 80 caracteres.")
        clase = barcode.get_barcode_class(nombre)
        objeto = clase(valor, writer=ImageWriter())
        imagen = objeto.render({"write_text": True, "module_height": 15, "font_size": 9, "text_distance": 2, "quiet_zone": 4})
        return objeto.get_fullcode(), imagen.convert("RGB")

    def dibujar_codigo_barras(self):
        self.canvas_barcode.delete("all")
        cod = self.ent_cod.get().strip()
        if not cod:
            self.lbl_cod_sub.config(text="Sin código asignado")
            self.canvas_barcode.create_text(200, 60, text="Sin código asignado", font=("sans", 14), fill="#64748B")
            return
        try:
            codigo_completo, imagen = self._generar_imagen_barcode(cod)
            self.lbl_cod_sub.config(text=f"Código: {codigo_completo}")
            imagen.thumbnail((380, 120), Image.Resampling.LANCZOS)
            self.barcode_image = ImageTk.PhotoImage(imagen)
            self.canvas_barcode.create_image(205, 68, image=self.barcode_image, anchor="center")
        except Exception as error:
            self.lbl_cod_sub.config(text="Código inválido")
            self.canvas_barcode.create_text(200, 60, text=str(error), width=360, font=("sans", 10), fill="#B42318")

    def guardar_en_producto(self):
        if not self.producto_seleccionado:
            messagebox.showwarning("Atención", "Seleccione un producto para guardar el código.")
            return
        cod = self.ent_cod.get().strip()
        if not cod or len(cod) > 80:
            messagebox.showerror("Error", "Indique un código de barras válido de hasta 80 caracteres.")
            return
        try:
            cod, _ = self._generar_imagen_barcode(cod)
        except Exception as error:
            messagebox.showerror("Código inválido", str(error))
            return
        self.ent_cod.delete(0, tk.END)
        self.ent_cod.insert(0, cod)
        producto_id = self.producto_seleccionado[0]
        try:
            self.servicio_inventario.actualizar_codigo_barra(producto_id, cod)
            self.cargar_productos()
            messagebox.showinfo("Éxito", f"Código '{cod}' asignado al producto correctamente.")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar el código: {e}")

    def copiar_codigo(self):
        cod = self.ent_cod.get().strip()
        self.clipboard_clear()
        self.clipboard_append(cod)
        messagebox.showinfo("Copiado", f"Código '{cod}' copiado al portapapeles.")

    def guardar_imagen_barcode(self):
        file_path = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("Imagen PNG", "*.png")],
            initialfile="Codigo_Barra.png"
        )
        if file_path:
            cod = self.ent_cod.get().strip()
            if not cod:
                messagebox.showwarning("Atención", "No hay un código asignado para exportar.")
                return
            try:
                cod, img = self._generar_imagen_barcode(cod)
            except Exception as error:
                messagebox.showerror("Código inválido", str(error))
                return
            img.save(file_path)
            messagebox.showinfo("Guardado", "Imagen del código de barras exportada exitosamente.")

    def filtrar_productos(self):
        q = self.ent_buscar.get().strip().lower()
        for r in self.tabla.get_children():
            self.tabla.delete(r)
        for p in self.productos:
            if not q or q in p[1].lower() or q in str(p[0]):
                cod = p[3] or "-"
                self.tabla.insert("", tk.END, values=(p[0], p[1], cod))
