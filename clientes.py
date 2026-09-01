import csv
import datetime
import os
import db_conexion as sqlite3
import sys
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageTk
from window_utils import posicionar_ventana
from servicios.servicio_clientes import ServicioClientes

class Clientes(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.title("Punto de Venta Versión 4.4.7 - Clientes")
        posicionar_ventana(self, 1100, 650, parent)
        self.resizable(False, False)
        self.configure(bg="#DDE1E5")
        self.transient(parent)
        self.grab_set()
        try:
            self.iconbitmap(self.rutas('icono.ico'))
        except Exception:
            pass

        self.db_name = "database.db"
        self.servicio_clientes = ServicioClientes()
        self.images = {}
        self.clientes = []
        self.cliente_seleccionado_id = None
        self.pagina_actual = 1
        self.por_pagina = 12

        self.widgets()
        self.actualizar_reloj()
        self.cargar_clientes()

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
            text="CLIENTES",
            font=("sans", 28, "bold"),
            bg="#DDE1E5",
            fg="#1E293B"
        )
        lbl_titulo.place(relx=0.5, rely=0.5, anchor="center")

        # Fecha y Hora
        ruta_cal = self.rutas("icono/calendario.png")
        if os.path.exists(ruta_cal):
            img_cal = Image.open(ruta_cal).resize((24, 24), Image.Resampling.LANCZOS)
            self.images["cal_cli"] = ImageTk.PhotoImage(img_cal)
            lbl_cal = tk.Label(frame_header, image=self.images["cal_cli"], bg="#DDE1E5")
            lbl_cal.place(x=770, y=24)

        self.lbl_fecha = tk.Label(frame_header, text="", font=("sans", 12, "bold"), bg="#DDE1E5", fg="#1E293B")
        self.lbl_fecha.place(x=800, y=26)

        ruta_clk = self.rutas("icono/hora.png")
        if os.path.exists(ruta_clk):
            img_clk = Image.open(ruta_clk).resize((24, 24), Image.Resampling.LANCZOS)
            self.images["clk_cli"] = ImageTk.PhotoImage(img_clk)
            lbl_clk = tk.Label(frame_header, image=self.images["clk_cli"], bg="#DDE1E5")
            lbl_clk.place(x=925, y=24)

        self.lbl_hora = tk.Label(frame_header, text="", font=("sans", 12, "bold"), bg="#DDE1E5", fg="#1E293B")
        self.lbl_hora.place(x=955, y=26)

#============== 2. PANEL IZQUIERDO: FORMULARIO CLIENTES ============================================#
        frame_form = tk.LabelFrame(
            self,
            text="Clientes",
            font=("sans", 14, "bold"),
            bg="#C6D9E3",
            fg="#1E293B",
            padx=12,
            pady=10
        )
        frame_form.place(x=20, y=85, width=400, height=545)

        # Nombre
        lbl_nom = tk.Label(frame_form, text="Nombre:", font=("sans", 12, "bold"), bg="#C6D9E3", fg="#1E293B")
        lbl_nom.place(x=5, y=10)
        self.ent_nombre = ttk.Entry(frame_form, font=("sans", 11))
        self.ent_nombre.place(x=130, y=10, width=235, height=30)

        # Tipo de ID + Número ID
        lbl_tid = tk.Label(frame_form, text="Tipo de ID:", font=("sans", 12, "bold"), bg="#C6D9E3", fg="#1E293B")
        lbl_tid.place(x=5, y=55)

        self.cmb_tipo_id = ttk.Combobox(frame_form, values=["CC", "NIT", "CE", "PAS"], font=("sans", 11), state="readonly")
        self.cmb_tipo_id.current(0)
        self.cmb_tipo_id.place(x=130, y=55, width=65, height=30)

        self.ent_numero_id = ttk.Entry(frame_form, font=("sans", 11))
        self.ent_numero_id.place(x=205, y=55, width=160, height=30)

        # Celular
        lbl_cel = tk.Label(frame_form, text="Celular:", font=("sans", 12, "bold"), bg="#C6D9E3", fg="#1E293B")
        lbl_cel.place(x=5, y=100)
        self.ent_celular = ttk.Entry(frame_form, font=("sans", 11))
        self.ent_celular.place(x=130, y=100, width=235, height=30)

        # Dirección
        lbl_dir = tk.Label(frame_form, text="Dirección:", font=("sans", 12, "bold"), bg="#C6D9E3", fg="#1E293B")
        lbl_dir.place(x=5, y=145)
        self.ent_direccion = ttk.Entry(frame_form, font=("sans", 11))
        self.ent_direccion.place(x=130, y=145, width=235, height=30)

        # Correo
        lbl_cor = tk.Label(frame_form, text="Correo:", font=("sans", 12, "bold"), bg="#C6D9E3", fg="#1E293B")
        lbl_cor.place(x=5, y=190)
        self.ent_correo = ttk.Entry(frame_form, font=("sans", 11))
        self.ent_correo.place(x=130, y=190, width=235, height=30)

        # 6 Botones de acción en cuadrícula 2x3
        botones_cli = [
            ("Ingresar", "ingresarc.png", self.ingresar_cliente, 0, 0),
            ("Inactivar", "eliminar.png", self.inactivar_cliente, 0, 1),
            ("Modificar", "modificar.png", self.modificar_cliente, 0, 2),
            ("Exportar", "excel.png", self.exportar_excel, 1, 0),
            ("Historial", "historialcp.png", self.historial_cliente, 1, 1),
            ("Pago Gen.", "btncobros.png", self.pago_general, 1, 2),
        ]

        frame_btns = tk.Frame(frame_form, bg="#C6D9E3")
        frame_btns.place(x=5, y=260, width=365, height=230)

        for txt, ico_f, cmd, r, c in botones_cli:
            ruta_i = self.rutas(f"icono/{ico_f}")
            if not os.path.exists(ruta_i):
                ruta_i = self.rutas("icono/agregar.png")

            if os.path.exists(ruta_i):
                img_i = Image.open(ruta_i).resize((32, 32), Image.Resampling.LANCZOS)
                self.images[f"btn_cli_{ico_f}"] = ImageTk.PhotoImage(img_i)
                ico_btn = self.images[f"btn_cli_{ico_f}"]
            else:
                ico_btn = None

            btn = tk.Button(
                frame_btns,
                text=txt,
                image=ico_btn,
                compound=tk.TOP,
                font=("sans", 9, "bold"),
                bg="#EBEFF2",
                fg="#1E293B",
                relief="raised",
                bd=2,
                cursor="hand2",
                command=cmd
            )
            btn.place(x=c * 122 + 5, y=r * 110 + 5, width=110, height=95)

#============== 3. PANEL DERECHO: BÚSQUEDA Y TABLA ==================================================#
        lbl_b = tk.Label(self, text="Buscar:", font=("sans", 13, "bold"), bg="#DDE1E5", fg="#1E293B")
        lbl_b.place(x=440, y=95)

        self.ent_buscar = ttk.Entry(self, font=("sans", 11))
        self.ent_buscar.place(x=515, y=93, width=200, height=30)
        self.ent_buscar.bind("<KeyRelease>", lambda e: self.filtrar_clientes())

        ruta_b = self.rutas("icono/buscar.png")
        if os.path.exists(ruta_b):
            img_b = Image.open(ruta_b).resize((22, 22), Image.Resampling.LANCZOS)
            self.images["buscar_ico_cli"] = ImageTk.PhotoImage(img_b)
            btn_b = tk.Button(self, image=self.images["buscar_ico_cli"], bg="white", relief="solid", bd=1, cursor="hand2", command=self.filtrar_clientes)
            btn_b.place(x=720, y=93, width=32, height=30)

        # Paginador
        ruta_izq = self.rutas("icono/izquierda.png")
        if os.path.exists(ruta_izq):
            img_izq = Image.open(ruta_izq).resize((18, 18), Image.Resampling.LANCZOS)
            self.images["izq_cli"] = ImageTk.PhotoImage(img_izq)
            btn_izq = tk.Button(self, image=self.images["izq_cli"], bg="#EBEFF2", relief="raised", bd=1, cursor="hand2", command=self.pag_ant)
            btn_izq.place(x=870, y=95, width=24, height=24)

        ruta_der = self.rutas("icono/derecha.png")
        if os.path.exists(ruta_der):
            img_der = Image.open(ruta_der).resize((18, 18), Image.Resampling.LANCZOS)
            self.images["der_cli"] = ImageTk.PhotoImage(img_der)
            btn_der = tk.Button(self, image=self.images["der_cli"], bg="#EBEFF2", relief="raised", bd=1, cursor="hand2", command=self.pag_sig)
            btn_der.place(x=898, y=95, width=24, height=24)

        self.lbl_pag = tk.Label(self, text="Página 1 de 1", font=("sans", 10, "bold"), bg="#DDE1E5", fg="#1E293B")
        self.lbl_pag.place(x=930, y=97)

        # Tabla de Clientes
        style = ttk.Style()
        style.configure("Clientes.Treeview.Heading", font=("sans", 9, "bold"), background="#E0E6ED")
        style.configure("Clientes.Treeview", font=("sans", 9), rowheight=24)

        cols = ("id", "nombre", "tipo_id", "numero_id", "celular")
        self.tabla = ttk.Treeview(self, columns=cols, show="headings", style="Clientes.Treeview")
        self.tabla.place(x=440, y=135, width=630, height=480)

        titulos = [
            ("id", "ID", 40),
            ("nombre", "Nombre", 230),
            ("tipo_id", "Tipo ID", 65),
            ("numero_id", "Número ID", 140),
            ("celular", "Celular", 140),
        ]

        for c, t, w in titulos:
            self.tabla.heading(c, text=t, anchor="center")
            self.tabla.column(c, width=w, anchor="center" if c in ("id", "tipo_id", "numero_id", "celular") else "w")

        scroll_y = ttk.Scrollbar(self, orient="vertical", command=self.tabla.yview)
        self.tabla.configure(yscrollcommand=scroll_y.set)
        scroll_y.place(x=1055, y=135, height=480)

        self.tabla.bind("<<TreeviewSelect>>", self.al_seleccionar_cliente)

    def actualizar_reloj(self):
        ahora = datetime.datetime.now()
        self.lbl_fecha.config(text=ahora.strftime("%d-%m-%Y"))
        self.lbl_hora.config(text=ahora.strftime("%H:%M:%S"))
        self.after(1000, self.actualizar_reloj)

    def cargar_clientes(self):
        try:
            self.clientes = self.servicio_clientes.listar()

            self.renderizar_tabla()
        except Exception as e:
            print("Error cargando clientes:", e)

    def renderizar_tabla(self):
        for r in self.tabla.get_children():
            self.tabla.delete(r)

        total = len(self.clientes)
        total_pags = max(1, (total + self.por_pagina - 1) // self.por_pagina)
        self.lbl_pag.config(text=f"Página {self.pagina_actual} de {total_pags}")

        inicio = (self.pagina_actual - 1) * self.por_pagina
        fin = inicio + self.por_pagina
        for c in self.clientes[inicio:fin]:
            self.tabla.insert("", tk.END, values=(c[0], c[1], c[2] or "CC", c[3] or "-", c[4] or "-"))

    def al_seleccionar_cliente(self, event=None):
        sel = self.tabla.selection()
        if not sel:
            return
        item_vals = self.tabla.item(sel[0], "values")
        if item_vals:
            self.cliente_seleccionado_id = item_vals[0]
            # Cargar en formulario
            try:
                c = self.servicio_clientes.obtener(self.cliente_seleccionado_id)
                if c:
                    self.ent_nombre.delete(0, tk.END)
                    self.ent_nombre.insert(0, c[0] or "")
                    if c[1] in self.cmb_tipo_id["values"]:
                        self.cmb_tipo_id.set(c[1])
                    self.ent_numero_id.delete(0, tk.END)
                    self.ent_numero_id.insert(0, str(c[2] or ""))
                    self.ent_celular.delete(0, tk.END)
                    self.ent_celular.insert(0, str(c[3] or ""))
                    self.ent_direccion.delete(0, tk.END)
                    self.ent_direccion.insert(0, c[4] or "")
                    self.ent_correo.delete(0, tk.END)
                    self.ent_correo.insert(0, c[5] or "")
            except Exception:
                pass

    def ingresar_cliente(self):
        nom = self.ent_nombre.get().strip()
        tid = self.cmb_tipo_id.get().strip()
        nid = self.ent_numero_id.get().strip()
        cel = self.ent_celular.get().strip()
        dire = self.ent_direccion.get().strip()
        cor = self.ent_correo.get().strip()

        if not nom:
            messagebox.showwarning("Atención", "Ingrese el nombre del cliente.")
            return

        try:
            self.servicio_clientes.crear(nom, tid, nid, cel, dire, cor)
            messagebox.showinfo("Éxito", "Cliente registrado correctamente.")
            self.limpiar_formulario()
            self.cargar_clientes()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo registrar cliente: {e}")

    def modificar_cliente(self):
        if not self.cliente_seleccionado_id:
            messagebox.showwarning("Atención", "Seleccione un cliente de la tabla para modificar.")
            return

        nom = self.ent_nombre.get().strip()
        tid = self.cmb_tipo_id.get().strip()
        nid = self.ent_numero_id.get().strip()
        cel = self.ent_celular.get().strip()
        dire = self.ent_direccion.get().strip()
        cor = self.ent_correo.get().strip()

        try:
            self.servicio_clientes.actualizar(self.cliente_seleccionado_id, nom, tid, nid, cel, dire, cor)
            messagebox.showinfo("Éxito", "Cliente modificado correctamente.")
            self.cargar_clientes()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo modificar: {e}")

    def inactivar_cliente(self):
        if not self.cliente_seleccionado_id:
            messagebox.showwarning("Atención", "Seleccione un cliente para inactivar.")
            return

        if messagebox.askyesno("Confirmar", "¿Desea inactivar el cliente seleccionado?"):
            try:
                self.servicio_clientes.desactivar(self.cliente_seleccionado_id)
                messagebox.showinfo("Éxito", "Cliente inactivado correctamente.")
                self.limpiar_formulario()
                self.cargar_clientes()
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo inactivar: {e}")

    def limpiar_formulario(self):
        self.cliente_seleccionado_id = None
        self.ent_nombre.delete(0, tk.END)
        self.ent_numero_id.delete(0, tk.END)
        self.ent_celular.delete(0, tk.END)
        self.ent_direccion.delete(0, tk.END)
        self.ent_correo.delete(0, tk.END)

    def filtrar_clientes(self):
        q = self.ent_buscar.get().strip().lower()
        if not q:
            self.cargar_clientes()
            return
        try:
            self.clientes = self.servicio_clientes.filtrar(q)
            self.pagina_actual = 1
            self.renderizar_tabla()
        except Exception as e:
            print("Error filtrando clientes:", e)

    def pag_ant(self):
        if self.pagina_actual > 1:
            self.pagina_actual -= 1
            self.renderizar_tabla()

    def pag_sig(self):
        total = len(self.clientes)
        total_pags = max(1, (total + self.por_pagina - 1) // self.por_pagina)
        if self.pagina_actual < total_pags:
            self.pagina_actual += 1
            self.renderizar_tabla()

    def exportar_excel(self):
        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("Archivo CSV", "*.csv")],
            initialfile="Clientes.csv"
        )
        if file_path:
            try:
                with open(file_path, mode="w", newline="", encoding="utf-8-sig") as f:
                    w = csv.writer(f)
                    w.writerow(["ID", "Nombre", "Tipo ID", "Número ID", "Celular", "Dirección", "Correo"])
                    for c in self.clientes:
                        w.writerow(c)
                messagebox.showinfo("Exportar", "Clientes exportados correctamente a CSV.")
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo exportar: {e}")

    def historial_cliente(self):
        from cliente_detalle import ClienteDetalle
        nom = self.ent_nombre.get().strip() or "CLIENTE GENERAL"
        ClienteDetalle(self, cliente_nom=nom)

    def pago_general(self):
        messagebox.showinfo("Pago General", "Registro de pagos y abonos de clientes.")
