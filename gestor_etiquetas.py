import os
import barcode
import db_conexion as sqlite3
import sys
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from barcode.writer import ImageWriter
from PIL import Image, ImageDraw, ImageTk
from window_utils import posicionar_ventana

class GestorEtiquetas(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.title("Gestor de Etiquetas de Productos")
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
        self.images = {}
        self.productos = []
        self.producto_seleccionado = None

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
            text="GESTOR DE ETIQUETAS DE PRODUCTOS",
            font=("sans", 20, "bold"),
            bg="#C6D9E3",
            fg="#1E293B"
        )
        lbl_title.place(relx=0.5, y=25, anchor="center")

#============== 2. PANEL IZQUIERDO: PRODUCTOS DEL INVENTARIO =======================================#
        frame_izq = tk.LabelFrame(
            self,
            text="Productos del Inventario",
            font=("sans", 12, "bold"),
            bg="#C6D9E3",
            fg="#1E293B",
            padx=10,
            pady=8
        )
        frame_izq.place(x=15, y=55, width=470, height=525)

        lbl_b = tk.Label(frame_izq, text="Buscar:", font=("sans", 11, "bold"), bg="#C6D9E3", fg="#1E293B")
        lbl_b.place(x=5, y=8)

        self.ent_buscar = ttk.Entry(frame_izq, font=("sans", 10))
        self.ent_buscar.place(x=70, y=6, width=325, height=28)
        self.ent_buscar.bind("<KeyRelease>", lambda e: self.filtrar_productos())

        ruta_rel = self.rutas("icono/actualizar1.png")
        if not os.path.exists(ruta_rel):
            ruta_rel = self.rutas("icono/actualizar.png")

        if os.path.exists(ruta_rel):
            img_r = Image.open(ruta_rel).resize((22, 22), Image.Resampling.LANCZOS)
            self.images["rel_etiq"] = ImageTk.PhotoImage(img_r)
            btn_r = tk.Button(frame_izq, image=self.images["rel_etiq"], bg="#22C55E", relief="solid", bd=1, cursor="hand2", command=self.cargar_productos)
            btn_r.place(x=405, y=6, width=32, height=28)

        # Tabla de productos
        style = ttk.Style()
        style.configure("Etiq.Treeview.Heading", font=("sans", 8, "bold"), background="#E0E6ED")
        style.configure("Etiq.Treeview", font=("sans", 8), rowheight=22)

        cols = ("id", "nombre", "codigo", "precio")
        self.tabla = ttk.Treeview(frame_izq, columns=cols, show="headings", style="Etiq.Treeview")
        self.tabla.place(x=5, y=42, width=425, height=445)

        self.tabla.heading("id", text="ID")
        self.tabla.heading("nombre", text="Nombre")
        self.tabla.heading("codigo", text="Código")
        self.tabla.heading("precio", text="Precio")

        self.tabla.column("id", width=35, anchor="center")
        self.tabla.column("nombre", width=210, anchor="w")
        self.tabla.column("codigo", width=95, anchor="center")
        self.tabla.column("precio", width=80, anchor="e")

        scroll_y = ttk.Scrollbar(frame_izq, orient="vertical", command=self.tabla.yview)
        self.tabla.configure(yscrollcommand=scroll_y.set)
        scroll_y.place(x=432, y=42, height=445)

        self.tabla.bind("<<TreeviewSelect>>", self.al_seleccionar_producto)

#============== 3. PANEL DERECHO: GENERADOR DE ETIQUETA ============================================#
        frame_der = tk.LabelFrame(
            self,
            text="Generador de Etiqueta",
            font=("sans", 12, "bold"),
            bg="#C6D9E3",
            fg="#1E293B",
            padx=10,
            pady=8
        )
        frame_der.place(x=505, y=55, width=460, height=525)

        self.lbl_info_prod = tk.Label(
            frame_der,
            text="Seleccione un producto para generar su etiqueta",
            font=("sans", 9, "bold"),
            bg="#C6D9E3",
            fg="#1E293B",
            justify="left"
        )
        self.lbl_info_prod.place(x=10, y=5)

        # Botón Vista Previa
        ruta_eye = self.rutas("icono/mostrar.png")
        if os.path.exists(ruta_eye):
            img_e = Image.open(ruta_eye).resize((18, 18), Image.Resampling.LANCZOS)
            self.images["eye_etiq"] = ImageTk.PhotoImage(img_e)
            ico_e = self.images["eye_etiq"]
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
            command=self.generar_etiqueta_visual
        )
        btn_vp.place(relx=0.5, y=70, width=150, height=34, anchor="center")

        # Contenedor de la Etiqueta (Tarjeta)
        self.card_etiqueta = tk.Frame(frame_der, bg="white", highlightbackground="#94A3B8", highlightthickness=1)
        self.card_etiqueta.place(x=20, y=105, width=400, height=250)

        # Banner Superior Azul Marino
        self.frame_et_banner = tk.Frame(self.card_etiqueta, bg="#1E293B")
        self.frame_et_banner.place(x=15, y=15, width=370, height=70)

        self.lbl_et_nombre = tk.Label(
            self.frame_et_banner,
            text="SIN PRODUCTO SELECCIONADO",
            font=("sans", 12, "bold"),
            bg="#1E293B",
            fg="white",
            wraplength=350,
            justify="center"
        )
        self.lbl_et_nombre.place(relx=0.5, rely=0.5, anchor="center")

        # Línea dorada divisoria
        tk.Frame(self.card_etiqueta, bg="#F59E0B", height=3).place(x=15, y=85, width=370)

        # Precio Gigante en Rojo
        self.lbl_et_precio = tk.Label(
            self.card_etiqueta,
            text="$ 0.00",
            font=("sans", 32, "bold"),
            bg="white",
            fg="#DC2626"
        )
        self.lbl_et_precio.place(relx=0.5, y=135, anchor="center")

        # Línea gris suave
        tk.Frame(self.card_etiqueta, bg="#E2E8F0", height=1).place(x=25, y=180, width=350)

        # Notas inferiores
        tk.Label(self.card_etiqueta, text="PRECIO DE VENTA", font=("sans", 8, "bold"), bg="white", fg="#64748B").place(relx=0.5, y=195, anchor="center")
        self.lbl_et_cod_sub = tk.Label(self.card_etiqueta, text="COD: -", font=("sans", 8, "bold"), bg="white", fg="#64748B")
        self.lbl_et_cod_sub.place(relx=0.5, y=215, anchor="center")

        # Código abajo
        self.lbl_et_codigo_bottom = tk.Label(frame_der, text="Código: -", font=("sans", 10, "bold"), bg="#C6D9E3", fg="#1E293B")
        self.lbl_et_codigo_bottom.place(relx=0.5, y=380, anchor="center")

        # Botón Guardar IMG
        ruta_save = self.rutas("icono/guardar.png")
        if os.path.exists(ruta_save):
            img_s = Image.open(ruta_save).resize((22, 22), Image.Resampling.LANCZOS)
            self.images["save_img_etiq"] = ImageTk.PhotoImage(img_s)
            ico_s = self.images["save_img_etiq"]
        else:
            ico_s = None

        btn_save = tk.Button(
            frame_der,
            text="  Guardar IMG",
            image=ico_s,
            compound=tk.LEFT,
            font=("sans", 11, "bold"),
            bg="#EBEFF2",
            fg="#1E293B",
            relief="raised",
            bd=2,
            cursor="hand2",
            command=self.guardar_imagen_etiqueta
        )
        btn_save.place(relx=0.5, y=430, width=170, height=44, anchor="center")

    def cargar_productos(self):
        try:
            with sqlite3.connect(self.db_name) as conn:
                cur = conn.cursor()
                cur.execute("SELECT id, nombre, precio, costo, stock, codigo_barra FROM inventario WHERE estado != 'Inactivo' OR estado IS NULL")
                self.productos = cur.fetchall()
            self.renderizar_tabla()
        except Exception as e:
            print("Error cargando productos:", e)

    def renderizar_tabla(self):
        for r in self.tabla.get_children():
            self.tabla.delete(r)

        for p in self.productos:
            cod = p[5] or "-"
            self.tabla.insert("", tk.END, values=(p[0], p[1], cod, f"${p[2]:,.2f}"))

    def al_seleccionar_producto(self, event=None):
        sel = self.tabla.selection()
        if not sel:
            return
        vals = self.tabla.item(sel[0], "values")
        if vals:
            self.producto_seleccionado = vals
            self.generar_etiqueta_visual()

    def generar_etiqueta_visual(self):
        if not self.producto_seleccionado:
            return
        # vals: id, nombre, codigo, precio
        p_id, nom, cod, pre = self.producto_seleccionado
        self.lbl_info_prod.config(text=f"Producto: {nom}\nCódigo: {cod} | Precio: {pre}")
        self.lbl_et_nombre.config(text=nom.upper())
        self.lbl_et_precio.config(text=pre.replace("$", "$ "))
        self.lbl_et_cod_sub.config(text=f"COD: {cod}")
        self.lbl_et_codigo_bottom.config(text=f"Código: {cod}")

    def filtrar_productos(self):
        q = self.ent_buscar.get().strip().lower()
        for r in self.tabla.get_children():
            self.tabla.delete(r)
        for p in self.productos:
            if not q or q in p[1].lower() or q in str(p[0]):
                cod = p[5] or "-"
                self.tabla.insert("", tk.END, values=(p[0], p[1], cod, f"${p[2]:,.2f}"))

    def guardar_imagen_etiqueta(self):
        if not self.producto_seleccionado:
            messagebox.showwarning("Atención", "Seleccione un producto para generar la etiqueta.")
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("Imagen PNG", "*.png")],
            initialfile=f"Etiqueta_{self.producto_seleccionado[0]}.png"
        )
        if file_path:
            # Crear imagen de etiqueta con PIL
            W, H = 600, 380
            img = Image.new("RGB", (W, H), (255, 255, 255))
            d = ImageDraw.Draw(img)
            # Header azul marino
            d.rectangle([20, 20, 580, 120], fill=(30, 41, 59))
            # Línea dorada
            d.rectangle([20, 120, 580, 126], fill=(245, 158, 11))
            # Textos básicos
            d.text((40, 50), self.producto_seleccionado[1].upper(), fill=(255, 255, 255))
            d.text((160, 180), f"PRECIO: {self.producto_seleccionado[3]}", fill=(220, 38, 38))
            codigo = str(self.producto_seleccionado[2] or "").strip()
            if codigo and codigo != "-":
                try:
                    if codigo.isdigit() and len(codigo) in (12, 13):
                        clase = barcode.get_barcode_class("ean13")
                    elif codigo.isdigit() and len(codigo) in (11, 12):
                        clase = barcode.get_barcode_class("upca")
                    else:
                        clase = barcode.get_barcode_class("code128")
                    imagen_barras = clase(codigo, writer=ImageWriter()).render({
                        "write_text": True, "module_height": 12, "font_size": 8,
                        "text_distance": 2, "quiet_zone": 3,
                    }).convert("RGB")
                    imagen_barras.thumbnail((500, 90), Image.Resampling.LANCZOS)
                    img.paste(imagen_barras, ((W - imagen_barras.width) // 2, 205))
                    d = ImageDraw.Draw(img)
                    d.text((180, 315), f"COD: {codigo}", fill=(100, 116, 139))
                except Exception as error:
                    messagebox.showerror("Código inválido", f"No se pudo generar el código de barras: {error}")
                    return
            else:
                d.text((230, 260), "SIN CÓDIGO", fill=(100, 116, 139))
            img.save(file_path)
            messagebox.showinfo("Éxito", "Imagen de etiqueta guardada correctamente.")
