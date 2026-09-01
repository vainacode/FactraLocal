import datetime
import json
import os
import db_conexion
import db_conexion as sqlite3
import sys
import tkinter as tk
from tkinter import messagebox, ttk
from PIL import Image, ImageTk
from window_utils import posicionar_ventana
from servicios.servicio_compras import ServicioCompras

class Compras(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
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
        self.servicio_compras = ServicioCompras()
        self.images = {}
        self.items_pedido = []
        try:
            self.numero_pedido = db_conexion.ver_siguiente_numero("pedido")
        except Exception:
            self.numero_pedido = 1

        self.widgets()
        self.actualizar_reloj()
        self.cargar_productos_combo()

    def rutas(self, ruta):
        try:
            rutabase = sys.__MEIPASS
        except Exception:
            rutabase = os.path.abspath(".")
        return os.path.join(rutabase, ruta)

    def widgets(self):
#============== 1. HEADER ==========================================================================#
        frame_header = tk.Frame(self, bg="#DDE1E5", highlightbackground="#B8C4CE", highlightthickness=1)
        frame_header.pack()
        frame_header.place(x=0, y=0, width=1100, height=75)

        lbl_titulo = tk.Label(
            frame_header,
            text="COMPRAS",
            font=("sans", 28, "bold"),
            bg="#DDE1E5",
            fg="#1E293B"
        )
        lbl_titulo.place(relx=0.5, rely=0.5, anchor="center")

        # Fecha y Hora
        ruta_cal = self.rutas("icono/calendario.png")
        if os.path.exists(ruta_cal):
            img_cal = Image.open(ruta_cal).resize((24, 24), Image.Resampling.LANCZOS)
            self.images["cal_comp"] = ImageTk.PhotoImage(img_cal)
            lbl_cal = tk.Label(frame_header, image=self.images["cal_comp"], bg="#DDE1E5")
            lbl_cal.place(x=770, y=24)

        self.lbl_fecha = tk.Label(frame_header, text="", font=("sans", 12, "bold"), bg="#DDE1E5", fg="#1E293B")
        self.lbl_fecha.place(x=800, y=26)

        ruta_clk = self.rutas("icono/hora.png")
        if os.path.exists(ruta_clk):
            img_clk = Image.open(ruta_clk).resize((24, 24), Image.Resampling.LANCZOS)
            self.images["clk_comp"] = ImageTk.PhotoImage(img_clk)
            lbl_clk = tk.Label(frame_header, image=self.images["clk_comp"], bg="#DDE1E5")
            lbl_clk.place(x=925, y=24)

        self.lbl_hora = tk.Label(frame_header, text="", font=("sans", 12, "bold"), bg="#DDE1E5", fg="#1E293B")
        self.lbl_hora.place(x=955, y=26)

#============== 2. PANEL IZQUIERDO: REGISTRAR PEDIDOS ===============================================#
        frame_form = tk.LabelFrame(
            self,
            text="Registrar pedidos",
            font=("sans", 14, "bold"),
            bg="#C6D9E3",
            fg="#1E293B",
            padx=12,
            pady=10
        )
        frame_form.place(x=20, y=85, width=390, height=545)

        # N° Pedido
        lbl_np = tk.Label(frame_form, text="N° Pedido:", font=("sans", 12, "bold"), bg="#C6D9E3", fg="#1E293B")
        lbl_np.place(x=5, y=10)

        self.ent_num_pedido = ttk.Entry(frame_form, font=("sans", 12, "bold"), justify="center")
        self.ent_num_pedido.place(x=130, y=8, width=225, height=30)
        self.ent_num_pedido.insert(0, str(self.numero_pedido))

        # Producto
        lbl_pr = tk.Label(frame_form, text="Producto:", font=("sans", 12, "bold"), bg="#C6D9E3", fg="#1E293B")
        lbl_pr.place(x=5, y=55)

        self.cmb_producto = ttk.Combobox(frame_form, font=("sans", 11))
        self.cmb_producto.place(x=130, y=53, width=225, height=30)
        self.cmb_producto.bind("<<ComboboxSelected>>", self.al_seleccionar_producto)

        # Proveedor + Botón Editar
        lbl_pv = tk.Label(frame_form, text="Proveedor:", font=("sans", 12, "bold"), bg="#C6D9E3", fg="#1E293B")
        lbl_pv.place(x=5, y=100)

        self.ent_proveedor = ttk.Entry(frame_form, font=("sans", 11))
        self.ent_proveedor.place(x=130, y=98, width=175, height=30)

        ruta_ed = self.rutas("icono/editar.png")
        if os.path.exists(ruta_ed):
            img_ed = Image.open(ruta_ed).resize((20, 20), Image.Resampling.LANCZOS)
            self.images["ed_prov"] = ImageTk.PhotoImage(img_ed)
            btn_ed = tk.Button(frame_form, image=self.images["ed_prov"], bg="#0284C7", relief="solid", bd=1, cursor="hand2", command=self.editar_proveedor)
            btn_ed.place(x=315, y=98, width=40, height=30)

        # Precio
        lbl_pre = tk.Label(frame_form, text="Precio:", font=("sans", 12, "bold"), bg="#C6D9E3", fg="#1E293B")
        lbl_pre.place(x=5, y=145)

        self.ent_precio = ttk.Entry(frame_form, font=("sans", 11))
        self.ent_precio.place(x=130, y=143, width=225, height=30)

        # Costo
        lbl_cos = tk.Label(frame_form, text="Costo:", font=("sans", 12, "bold"), bg="#C6D9E3", fg="#1E293B")
        lbl_cos.place(x=5, y=190)

        self.ent_costo = ttk.Entry(frame_form, font=("sans", 11))
        self.ent_costo.place(x=130, y=188, width=225, height=30)

        # Nueva Cant + Stock
        lbl_nc = tk.Label(frame_form, text="Nueva Cant:", font=("sans", 11, "bold"), bg="#C6D9E3", fg="#1E293B")
        lbl_nc.place(x=5, y=235)

        self.ent_nueva_cant = ttk.Entry(frame_form, font=("sans", 11), justify="center")
        self.ent_nueva_cant.place(x=130, y=233, width=90, height=30)
        self.ent_nueva_cant.insert(0, "1")

        lbl_st = tk.Label(frame_form, text="Stock:", font=("sans", 11, "bold"), bg="#C6D9E3", fg="#1E293B")
        lbl_st.place(x=230, y=235)

        self.ent_stock = ttk.Entry(frame_form, font=("sans", 11), justify="center")
        self.ent_stock.place(x=290, y=233, width=65, height=30)

        # 4 Botones de acción inferiores en formulario
        botones_form = [
            ("Agregar", "agregar1.png", self.agregar_item_pedido),
            ("Registrar", "registrar.png", self.registrar_pedido),
            ("Ver\nPedido", "ver.png", self.ver_pedidos),
            ("Anular\nPedido", "anular.png", self.anular_pedido),
        ]

        x_b = 5
        for txt, ico_f, cmd in botones_form:
            ruta_i = self.rutas(f"icono/{ico_f}")
            if not os.path.exists(ruta_i):
                ruta_i = self.rutas("icono/agregar.png")

            if os.path.exists(ruta_i):
                img_i = Image.open(ruta_i).resize((26, 26), Image.Resampling.LANCZOS)
                self.images[f"btn_comp_{ico_f}"] = ImageTk.PhotoImage(img_i)
                ico_btn = self.images[f"btn_comp_{ico_f}"]
            else:
                ico_btn = None

            btn = tk.Button(
                frame_form,
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
            btn.place(x=x_b, y=365, width=82, height=75)
            x_b += 88

#============== 3. PANEL DERECHO: TABLA Y OPCIONES ==================================================#
        # Tabla de pedidos
        style = ttk.Style()
        style.configure("Compras.Treeview.Heading", font=("sans", 9, "bold"), background="#E0E6ED")
        style.configure("Compras.Treeview", font=("sans", 10), rowheight=24)

        cols = ("num_pedido", "proveedor", "producto", "cantidad")
        self.tabla = ttk.Treeview(self, columns=cols, show="headings", style="Compras.Treeview")
        self.tabla.place(x=430, y=95, width=640, height=435)

        self.tabla.heading("num_pedido", text="N° Pedido")
        self.tabla.heading("proveedor", text="Proveedor")
        self.tabla.heading("producto", text="Producto")
        self.tabla.heading("cantidad", text="Cantidad")

        self.tabla.column("num_pedido", width=80, anchor="center")
        self.tabla.column("proveedor", width=180, anchor="w")
        self.tabla.column("producto", width=270, anchor="w")
        self.tabla.column("cantidad", width=80, anchor="center")

        scroll_y = ttk.Scrollbar(self, orient="vertical", command=self.tabla.yview)
        self.tabla.configure(yscrollcommand=scroll_y.set)
        scroll_y.place(x=1055, y=95, height=435)

        # Panel Opciones Inferior
        frame_opciones = tk.LabelFrame(
            self,
            text="Opciones",
            font=("sans", 11, "bold"),
            bg="#C6D9E3",
            fg="#1E293B",
            padx=10,
            pady=4
        )
        frame_opciones.place(x=430, y=540, width=640, height=85)

        opciones_btns = [
            ("Eliminar", "eliminar.png", self.eliminar_item),
            ("Limpiar", "cancelar.png", self.limpiar_tabla),
            ("Guardar", "guardar.png", self.guardar_borrador),
            ("Cargar", "cargarcotizacion.png", self.cargar_borrador),
        ]

        x_op = 15
        for txt, ico_f, cmd in opciones_btns:
            ruta_i = self.rutas(f"icono/{ico_f}")
            if not os.path.exists(ruta_i):
                ruta_i = self.rutas("icono/guardar.png")

            if os.path.exists(ruta_i):
                img_i = Image.open(ruta_i).resize((22, 22), Image.Resampling.LANCZOS)
                self.images[f"op_comp_{ico_f}"] = ImageTk.PhotoImage(img_i)
                ico_btn = self.images[f"op_comp_{ico_f}"]
            else:
                ico_btn = None

            btn_op = tk.Button(
                frame_opciones,
                text=f"  {txt}",
                image=ico_btn,
                compound=tk.LEFT,
                font=("sans", 10, "bold"),
                bg="#EBEFF2",
                fg="#1E293B",
                relief="raised",
                bd=2,
                cursor="hand2",
                command=cmd
            )
            btn_op.place(x=x_op, y=8, width=135, height=40)
            x_op += 150

    def actualizar_reloj(self):
        ahora = datetime.datetime.now()
        self.lbl_fecha.config(text=ahora.strftime("%d-%m-%Y"))
        self.lbl_hora.config(text=ahora.strftime("%H:%M:%S"))
        self.after(1000, self.actualizar_reloj)

    def cargar_productos_combo(self):
        try:
            self.productos_db = self.servicio_compras.listar_productos()
            self.cmb_producto["values"] = [p[1] for p in self.productos_db]
        except Exception as e:
            print("Error cargando productos en compras:", e)

    def al_seleccionar_producto(self, event=None):
        nom = self.cmb_producto.get().strip()
        for p in self.productos_db:
            if p[1] == nom:
                self.ent_proveedor.delete(0, tk.END)
                self.ent_proveedor.insert(0, p[5] or "")
                self.ent_precio.delete(0, tk.END)
                self.ent_precio.insert(0, f"{p[2]:,.2f}")
                self.ent_costo.delete(0, tk.END)
                self.ent_costo.insert(0, f"{p[3]:,.2f}")
                self.ent_stock.delete(0, tk.END)
                self.ent_stock.insert(0, str(p[4]))
                break

    def agregar_item_pedido(self):
        nom = self.cmb_producto.get().strip()
        prov = self.ent_proveedor.get().strip()
        cant = self.ent_nueva_cant.get().strip()
        num_p = self.ent_num_pedido.get().strip()

        if not nom:
            messagebox.showwarning("Atención", "Seleccione un producto para agregar al pedido.")
            return

        if not prov:
            messagebox.showwarning("Atención", "Ingrese el proveedor antes de agregar el producto.")
            return
        item = (num_p, prov, nom, cant or "1")
        self.items_pedido.append(item)
        self.tabla.insert("", tk.END, values=item)

    def registrar_pedido(self):
        if not self.items_pedido:
            messagebox.showwarning("Atención", "No hay productos en el pedido para registrar.")
            return

        from registrar_pedido_modal import RegistrarPedidoModal

        def al_confirmar():
            self.numero_pedido += 1
            self.ent_num_pedido.delete(0, tk.END)
            self.ent_num_pedido.insert(0, str(self.numero_pedido))
            self.limpiar_tabla()

        RegistrarPedidoModal(self, pedido_info=self.items_pedido, callback_success=al_confirmar)

    def ver_pedidos(self):
        ventana = tk.Toplevel(self)
        ventana.title("Pedidos registrados")
        ventana.geometry("850x420")
        ventana.transient(self)
        ventana.grab_set()
        tabla = ttk.Treeview(ventana, columns=("pedido", "proveedor", "producto", "cantidad", "fecha"), show="headings")
        for col, title, width in (("pedido", "Nº Pedido", 100), ("proveedor", "Proveedor", 190), ("producto", "Producto", 300), ("cantidad", "Cantidad", 90), ("fecha", "Fecha", 130)):
            tabla.heading(col, text=title)
            tabla.column(col, width=width, anchor="center" if col in ("pedido", "cantidad", "fecha") else "w")
        tabla.pack(fill="both", expand=True, padx=12, pady=12)
        try:
            filas = self.servicio_compras.listar_pedidos()
            for fila in filas:
                tabla.insert("", tk.END, values=fila)
        except Exception as error:
            ventana.destroy()
            messagebox.showerror("Error", f"No se pudieron cargar los pedidos: {error}")

    def anular_pedido(self):
        from pedidos_anulados import PedidosAnulados
        PedidosAnulados(self)

    def eliminar_item(self):
        sel = self.tabla.selection()
        if not sel:
            messagebox.showwarning("Atención", "Seleccione un producto de la tabla para eliminar.")
            return
        idx = self.tabla.index(sel[0])
        del self.items_pedido[idx]
        self.tabla.delete(sel[0])

    def limpiar_tabla(self):
        self.items_pedido.clear()
        for r in self.tabla.get_children():
            self.tabla.delete(r)

    def guardar_borrador(self):
        if not self.items_pedido:
            messagebox.showwarning("Borrador vacío", "Agregue productos antes de guardar.")
            return
        controlador = getattr(self.parent, "controlador", None)
        usuario_info = getattr(controlador, "usuario_actual", {}) or {}
        usuario = usuario_info.get("nombre") or usuario_info.get("username") or ""
        if not usuario:
            messagebox.showerror("Sesión requerida", "No se puede registrar un pedido sin un usuario autenticado.")
            return
        try:
            self.servicio_compras.guardar_borrador(usuario, self.items_pedido)
            messagebox.showinfo("Borrador guardado", "El pedido fue guardado como borrador.")
        except Exception as error:
            messagebox.showerror("Error", f"No se pudo guardar el borrador: {error}")

    def cargar_borrador(self):
        try:
            controlador = getattr(self.parent, "controlador", None)
            usuario_info = getattr(controlador, "usuario_actual", {}) or {}
            usuario = usuario_info.get("nombre") or usuario_info.get("username") or ""
            fila = self.servicio_compras.obtener_borrador(usuario)
            if not fila or not fila[1]:
                messagebox.showinfo("Borradores", "No hay borradores guardados.")
                return
            self.limpiar_tabla()
            self.items_pedido = [tuple(item) for item in fila[1]]
            for item in self.items_pedido:
                self.tabla.insert("", tk.END, values=item)
            messagebox.showinfo("Borrador cargado", f"Se cargó el borrador #{fila[0]}.")
        except Exception as error:
            messagebox.showerror("Error", f"No se pudo cargar el borrador: {error}")

    def editar_proveedor(self):
        # Abrir el mantenimiento real evita confirmar una operación que no
        # guardaba ningún cambio.
        from proveedores import Proveedores
        Proveedores(self)
