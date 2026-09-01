import csv
import os
import db_conexion as sqlite3
import sys
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageTk
from window_utils import posicionar_ventana
from servicios.servicio_inventario import ServicioInventario

class Servicios(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.title("Gestión de Servicios")
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
        self.images = {}
        self.servicios = []
        self.servicio_sel_id = None
        self.pagina_actual = 1
        self.por_pagina = 10
        self.servicio_inventario = ServicioInventario()

        self.widgets()
        self.cargar_servicios()

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
            text="GESTIÓN DE SERVICIOS",
            font=("sans", 24, "bold"),
            bg="#C6D9E3",
            fg="#1E293B"
        )
        lbl_title.place(relx=0.5, y=25, anchor="center")

#============== 2. PANEL IZQUIERDO: INFORMACIÓN DEL SERVICIO =======================================#
        frame_form = tk.LabelFrame(
            self,
            text="Información del Servicio",
            font=("sans", 13, "bold"),
            bg="#C6D9E3",
            fg="#1E293B",
            padx=12,
            pady=10
        )
        frame_form.place(x=20, y=60, width=410, height=480)

        # Nombre
        lbl_nom = tk.Label(frame_form, text="Nombre:", font=("sans", 11, "bold"), bg="#C6D9E3", fg="#1E293B")
        lbl_nom.place(x=10, y=10)
        self.ent_nombre = ttk.Entry(frame_form, font=("sans", 11))
        self.ent_nombre.place(x=120, y=8, width=250, height=30)

        # Precio
        lbl_pre = tk.Label(frame_form, text="Precio:", font=("sans", 11, "bold"), bg="#C6D9E3", fg="#1E293B")
        lbl_pre.place(x=10, y=55)
        self.ent_precio = ttk.Entry(frame_form, font=("sans", 11))
        self.ent_precio.place(x=120, y=53, width=250, height=30)
        self.ent_precio.bind("<KeyRelease>", self.calcular_precio_final)

        # Costo
        lbl_cos = tk.Label(frame_form, text="Costo:", font=("sans", 11, "bold"), bg="#C6D9E3", fg="#1E293B")
        lbl_cos.place(x=10, y=100)
        self.ent_costo = ttk.Entry(frame_form, font=("sans", 11))
        self.ent_costo.place(x=120, y=98, width=250, height=30)

        # Impuesto
        lbl_imp = tk.Label(frame_form, text="Impuesto:", font=("sans", 11, "bold"), bg="#C6D9E3", fg="#1E293B")
        lbl_imp.place(x=10, y=145)
        self.cmb_impuesto = ttk.Combobox(frame_form, values=["Exento", "IVA 19%", "IVA 5%"], font=("sans", 11), state="readonly")
        self.cmb_impuesto.current(0)
        self.cmb_impuesto.place(x=120, y=143, width=250, height=30)
        self.cmb_impuesto.bind("<<ComboboxSelected>>", self.calcular_precio_final)

        # Descripción
        lbl_des = tk.Label(frame_form, text="Descripción:", font=("sans", 11, "bold"), bg="#C6D9E3", fg="#1E293B")
        lbl_des.place(x=10, y=190)
        self.txt_descripcion = tk.Text(frame_form, font=("sans", 10), height=4, width=30)
        self.txt_descripcion.place(x=120, y=188, width=250, height=80)

        # Estado
        lbl_est = tk.Label(frame_form, text="Estado:", font=("sans", 11, "bold"), bg="#C6D9E3", fg="#1E293B")
        lbl_est.place(x=10, y=285)
        self.cmb_estado = ttk.Combobox(frame_form, values=["Activo", "Inactivo"], font=("sans", 11), state="readonly")
        self.cmb_estado.current(0)
        self.cmb_estado.place(x=120, y=283, width=250, height=30)

        # Precio Final
        lbl_pf = tk.Label(frame_form, text="Precio Final:", font=("sans", 11, "bold"), bg="#C6D9E3", fg="#1E293B")
        lbl_pf.place(x=10, y=330)
        self.lbl_precio_final = tk.Label(frame_form, text="-", font=("sans", 12, "bold"), bg="#C6D9E3", fg="#16A34A")
        self.lbl_precio_final.place(x=120, y=330)

#============== 3. PANEL DERECHO: SERVICIOS REGISTRADOS ============================================#
        frame_tabla = tk.LabelFrame(
            self,
            text="Servicios Registrados",
            font=("sans", 13, "bold"),
            bg="#C6D9E3",
            fg="#1E293B",
            padx=10,
            pady=8
        )
        frame_tabla.place(x=450, y=60, width=630, height=480)

        # Búsqueda
        lbl_b = tk.Label(frame_tabla, text="Buscar:", font=("sans", 11, "bold"), bg="#C6D9E3", fg="#1E293B")
        lbl_b.place(x=10, y=8)

        self.ent_buscar = ttk.Entry(frame_tabla, font=("sans", 10))
        self.ent_buscar.place(x=75, y=6, width=250, height=28)
        self.ent_buscar.bind("<KeyRelease>", lambda e: self.filtrar_servicios())

        ruta_b = self.rutas("icono/buscar.png")
        if os.path.exists(ruta_b):
            img_b = Image.open(ruta_b).resize((20, 20), Image.Resampling.LANCZOS)
            self.images["b_srv"] = ImageTk.PhotoImage(img_b)
            btn_b = tk.Button(frame_tabla, image=self.images["b_srv"], bg="white", relief="solid", bd=1, cursor="hand2", command=self.filtrar_servicios)
            btn_b.place(x=330, y=6, width=30, height=28)

        # Paginador
        ruta_izq = self.rutas("icono/izquierda.png")
        if os.path.exists(ruta_izq):
            img_izq = Image.open(ruta_izq).resize((18, 18), Image.Resampling.LANCZOS)
            self.images["izq_srv"] = ImageTk.PhotoImage(img_izq)
            btn_izq = tk.Button(frame_tabla, image=self.images["izq_srv"], bg="#EBEFF2", relief="raised", bd=1, cursor="hand2", command=self.pag_ant)
            btn_izq.place(x=475, y=8, width=24, height=24)

        ruta_der = self.rutas("icono/derecha.png")
        if os.path.exists(ruta_der):
            img_der = Image.open(ruta_der).resize((18, 18), Image.Resampling.LANCZOS)
            self.images["der_srv"] = ImageTk.PhotoImage(img_der)
            btn_der = tk.Button(frame_tabla, image=self.images["der_srv"], bg="#EBEFF2", relief="raised", bd=1, cursor="hand2", command=self.pag_sig)
            btn_der.place(x=503, y=8, width=24, height=24)

        self.lbl_pag = tk.Label(frame_tabla, text="Página 1 de 1", font=("sans", 9, "bold"), bg="#C6D9E3", fg="#1E293B")
        self.lbl_pag.place(x=532, y=10)

        # Tabla
        style = ttk.Style()
        style.configure("Srv.Treeview.Heading", font=("sans", 9, "bold"), background="#E0E6ED")
        style.configure("Srv.Treeview", font=("sans", 9), rowheight=24)

        cols = ("id", "nombre", "precio", "costo", "impuesto")
        self.tabla = ttk.Treeview(frame_tabla, columns=cols, show="headings", style="Srv.Treeview")
        self.tabla.place(x=10, y=45, width=590, height=395)

        titulos = [
            ("id", "ID", 40),
            ("nombre", "Nombre", 250),
            ("precio", "Precio", 110),
            ("costo", "Costo", 90),
            ("impuesto", "Impuesto", 90),
        ]

        for c, t, w in titulos:
            self.tabla.heading(c, text=t, anchor="center")
            self.tabla.column(c, width=w, anchor="center" if c in ("id", "impuesto") else "w" if c == "nombre" else "e")

        scroll_y = ttk.Scrollbar(frame_tabla, orient="vertical", command=self.tabla.yview)
        self.tabla.configure(yscrollcommand=scroll_y.set)
        scroll_y.place(x=595, y=45, height=395)

        self.tabla.bind("<<TreeviewSelect>>", self.al_seleccionar_servicio)

#============== 4. PANEL INFERIOR DE OPCIONES =======================================================#
        frame_opc = tk.LabelFrame(
            self,
            text="Opciones",
            font=("sans", 11, "bold"),
            bg="#C6D9E3",
            fg="#1E293B",
            padx=10,
            pady=4
        )
        frame_opc.place(x=20, y=545, width=1060, height=85)

        opciones_srv = [
            ("Registrar", "ingresarc.png", self.registrar_servicio),
            ("Editar", "editar.png", self.modificar_servicio),
            ("Eliminar", "eliminar.png", self.eliminar_servicio),
            ("Exportar", "excel.png", self.exportar_excel),
        ]

        x_op = 20
        for txt, ico_f, cmd in opciones_srv:
            ruta_i = self.rutas(f"icono/{ico_f}")
            if not os.path.exists(ruta_i):
                ruta_i = self.rutas("icono/agregar.png")

            if os.path.exists(ruta_i):
                img_i = Image.open(ruta_i).resize((22, 22), Image.Resampling.LANCZOS)
                self.images[f"op_srv_{ico_f}"] = ImageTk.PhotoImage(img_i)
                ico_btn = self.images[f"op_srv_{ico_f}"]
            else:
                ico_btn = None

            btn = tk.Button(
                frame_opc,
                text=f"  {txt}",
                image=ico_btn,
                compound=tk.LEFT,
                font=("sans", 11, "bold"),
                bg="#EBEFF2",
                fg="#1E293B",
                relief="raised",
                bd=2,
                cursor="hand2",
                command=cmd
            )
            btn.place(x=x_op, y=8, width=225, height=44)
            x_op += 260

    def calcular_precio_final(self, event=None):
        try:
            pre = float(self.ent_precio.get().strip() or 0)
            imp = self.cmb_impuesto.get()
            tasa = 0.19 if "19" in imp else 0.05 if "5" in imp else 0.0
            tot = pre * (1 + tasa)
            self.lbl_precio_final.config(text=f"$ {tot:,.2f}")
        except ValueError:
            self.lbl_precio_final.config(text="-")

    def cargar_servicios(self):
        self.servicios = []
        try:
            with sqlite3.connect(self.db_name) as conn:
                self.servicios = conn.execute("""
                    SELECT id, nombre, precio, costo, COALESCE(tipo_impuesto, 'Exento')
                    FROM servicios WHERE estado = 'Activo' OR estado IS NULL ORDER BY nombre
                """).fetchall()
        except Exception:
            self.servicios = []
        self.renderizar_tabla()

    def renderizar_tabla(self):
        for r in self.tabla.get_children():
            self.tabla.delete(r)

        total_pags = max(1, (len(self.servicios) + self.por_pagina - 1) // self.por_pagina)
        self.lbl_pag.config(text=f"Página {self.pagina_actual} de {total_pags}")

        inicio = (self.pagina_actual - 1) * self.por_pagina
        fin = inicio + self.por_pagina
        for s in self.servicios[inicio:fin]:
            self.tabla.insert("", tk.END, values=s)

    def al_seleccionar_servicio(self, event=None):
        sel = self.tabla.selection()
        if not sel:
            return
        vals = self.tabla.item(sel[0], "values")
        if vals:
            self.servicio_sel_id = vals[0]
            self.ent_nombre.delete(0, tk.END)
            self.ent_nombre.insert(0, vals[1])
            self.ent_precio.delete(0, tk.END)
            self.ent_precio.insert(0, vals[2].replace("$", "").replace(",", "").strip())
            self.ent_costo.delete(0, tk.END)
            self.ent_costo.insert(0, vals[3].replace("$", "").replace(",", "").strip())
            self.cmb_impuesto.set(vals[4])
            self.calcular_precio_final()

    def registrar_servicio(self):
        nom = self.ent_nombre.get().strip()
        pre = self.ent_precio.get().strip()
        if not nom or not pre:
            messagebox.showwarning("Atención", "Ingrese al menos el nombre y precio del servicio.")
            return

        try:
            precio_val = float(pre)
            cos_val = float(self.ent_costo.get().strip() or 0)
            imp_val = self.cmb_impuesto.get()

            descripcion = self.txt_descripcion.get("1.0", tk.END).strip()
            self.servicio_inventario.crear_servicio_catalogo((nom, precio_val, cos_val, descripcion, imp_val))
            self.cargar_servicios()
            messagebox.showinfo("Éxito", "Servicio registrado correctamente.")
            self.limpiar_form()
        except (ValueError, sqlite3.Error) as error:
            messagebox.showerror("Error", f"No se pudo registrar el servicio: {error}")

    def modificar_servicio(self):
        if not self.servicio_sel_id:
            messagebox.showwarning("Atención", "Seleccione un servicio para editar.")
            return
        nom = self.ent_nombre.get().strip()
        try:
            precio = float(self.ent_precio.get().strip())
            costo = float(self.ent_costo.get().strip() or 0)
            descripcion = self.txt_descripcion.get("1.0", tk.END).strip()
            self.servicio_inventario.actualizar_servicio_catalogo(self.servicio_sel_id, (nom, precio, costo, descripcion, self.cmb_impuesto.get()))
            self.cargar_servicios()
            self.limpiar_form()
            messagebox.showinfo("Éxito", "Servicio modificado correctamente.")
        except (ValueError, sqlite3.Error) as error:
            messagebox.showerror("Error", f"No se pudo modificar el servicio: {error}")

    def eliminar_servicio(self):
        sel = self.tabla.selection()
        if not sel:
            messagebox.showwarning("Atención", "Seleccione un servicio para eliminar.")
            return
        if messagebox.askyesno("Confirmar", "¿Desea eliminar el servicio seleccionado?"):
            try:
                servicio_id = self.tabla.item(sel[0], "values")[0]
                self.servicio_inventario.desactivar_servicio_catalogo(servicio_id)
                self.cargar_servicios()
                self.limpiar_form()
                messagebox.showinfo("Éxito", "Servicio desactivado correctamente.")
            except sqlite3.Error as error:
                messagebox.showerror("Error", f"No se pudo desactivar el servicio: {error}")

    def limpiar_form(self):
        self.servicio_sel_id = None
        self.ent_nombre.delete(0, tk.END)
        self.ent_precio.delete(0, tk.END)
        self.ent_costo.delete(0, tk.END)
        self.txt_descripcion.delete("1.0", tk.END)
        self.lbl_precio_final.config(text="-")

    def filtrar_servicios(self):
        q = self.ent_buscar.get().strip().lower()
        for r in self.tabla.get_children():
            self.tabla.delete(r)
        for s in self.servicios:
            if not q or q in s[1].lower():
                self.tabla.insert("", tk.END, values=s)

    def pag_ant(self):
        if self.pagina_actual > 1:
            self.pagina_actual -= 1
            self.renderizar_tabla()

    def pag_sig(self):
        total_pags = max(1, (len(self.servicios) + self.por_pagina - 1) // self.por_pagina)
        if self.pagina_actual < total_pags:
            self.pagina_actual += 1
            self.renderizar_tabla()

    def exportar_excel(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("Archivo CSV", "*.csv")], initialfile="Servicios.csv")
        if file_path:
            try:
                with open(file_path, mode="w", newline="", encoding="utf-8-sig") as f:
                    w = csv.writer(f)
                    w.writerow(["ID", "Nombre", "Precio", "Costo", "Impuesto"])
                    for s in self.servicios:
                        w.writerow(s)
                messagebox.showinfo("Exportar", "Servicios exportados exitosamente.")
            except Exception as e:
                messagebox.showerror("Error", f"Error exportando: {e}")
