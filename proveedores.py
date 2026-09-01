import csv
import datetime
import os
import db_conexion as sqlite3
import sys
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageTk
from window_utils import posicionar_ventana
from servicios.servicio_compras import ServicioCompras

class Proveedores(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.title("Punto de Venta Versión 4.4.7 - Gestión de Proveedores")
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
        self.servicio_compras = ServicioCompras()
        self.images = {}
        self.proveedores = []
        self.proveedor_seleccionado = None

        self.widgets()
        self.actualizar_reloj()
        self.cargar_proveedores()

    def rutas(self, ruta):
        try:
            rutabase = sys.__MEIPASS
        except Exception:
            rutabase = os.path.abspath(".")
        return os.path.join(rutabase, ruta)

    def widgets(self):
#============== 1. HEADER ==========================================================================#
        lbl_titulo = tk.Label(
            self,
            text="GESTIÓN DE PROVEEDORES",
            font=("sans", 28, "bold"),
            bg="#DDE1E5",
            fg="#1E293B"
        )
        lbl_titulo.place(relx=0.5, y=35, anchor="center")

        # Fecha y Hora Top-Right
        frame_time = tk.Frame(self, bg="#DDE1E5")
        frame_time.place(x=780, y=20, width=300, height=35)

        ruta_cal = self.rutas("icono/calendario.png")
        if os.path.exists(ruta_cal):
            self.images["cal_prov"] = ImageTk.PhotoImage(Image.open(ruta_cal).resize((22, 22), Image.Resampling.LANCZOS))
            tk.Label(frame_time, image=self.images["cal_prov"], bg="#DDE1E5").place(x=0, y=5)

        self.lbl_fecha = tk.Label(frame_time, text="", font=("sans", 11, "bold"), bg="#DDE1E5", fg="#1E293B")
        self.lbl_fecha.place(x=30, y=6)

        ruta_rel = self.rutas("icono/reloj.png")
        if not os.path.exists(ruta_rel):
            ruta_rel = self.rutas("icono/calendario.png")

        if os.path.exists(ruta_rel):
            self.images["rel_prov"] = ImageTk.PhotoImage(Image.open(ruta_rel).resize((22, 22), Image.Resampling.LANCZOS))
            tk.Label(frame_time, image=self.images["rel_prov"], bg="#DDE1E5").place(x=150, y=5)

        self.lbl_hora = tk.Label(frame_time, text="", font=("sans", 11, "bold"), bg="#DDE1E5", fg="#1E293B")
        self.lbl_hora.place(x=180, y=6)

#============== 2. PANEL IZQUIERDO: FORMULARIO =====================================================#
        frame_form = tk.LabelFrame(
            self,
            text="Datos del Proveedor",
            font=("sans", 13, "bold"),
            bg="#C6D9E3",
            fg="#1E293B",
            padx=15,
            pady=8
        )
        frame_form.place(x=20, y=70, width=420, height=550)

        # Nombre / Razón Social
        lbl_nom = tk.Label(frame_form, text="Razón Social / Nombre:", font=("sans", 10, "bold"), bg="#C6D9E3", fg="#1E293B")
        lbl_nom.place(x=10, y=5)

        self.ent_nombre = ttk.Entry(frame_form, font=("sans", 11))
        self.ent_nombre.place(x=10, y=28, width=365, height=28)

        # NIT / RUT
        lbl_nit = tk.Label(frame_form, text="NIT / Identificación:", font=("sans", 10, "bold"), bg="#C6D9E3", fg="#1E293B")
        lbl_nit.place(x=10, y=60)

        self.ent_nit = ttk.Entry(frame_form, font=("sans", 11))
        self.ent_nit.place(x=10, y=83, width=365, height=28)

        # Teléfono
        lbl_tel = tk.Label(frame_form, text="Teléfono / Celular:", font=("sans", 10, "bold"), bg="#C6D9E3", fg="#1E293B")
        lbl_tel.place(x=10, y=115)

        self.ent_tel = ttk.Entry(frame_form, font=("sans", 11))
        self.ent_tel.place(x=10, y=138, width=365, height=28)

        # Persona de Contacto
        lbl_con = tk.Label(frame_form, text="Persona de Contacto:", font=("sans", 10, "bold"), bg="#C6D9E3", fg="#1E293B")
        lbl_con.place(x=10, y=170)

        self.ent_contacto = ttk.Entry(frame_form, font=("sans", 11))
        self.ent_contacto.place(x=10, y=193, width=365, height=28)

        # Correo Electrónico
        lbl_mail = tk.Label(frame_form, text="Correo Electrónico:", font=("sans", 10, "bold"), bg="#C6D9E3", fg="#1E293B")
        lbl_mail.place(x=10, y=225)

        self.ent_email = ttk.Entry(frame_form, font=("sans", 11))
        self.ent_email.place(x=10, y=248, width=365, height=28)

        # Dirección
        lbl_dir = tk.Label(frame_form, text="Dirección:", font=("sans", 10, "bold"), bg="#C6D9E3", fg="#1E293B")
        lbl_dir.place(x=10, y=280)

        self.ent_direccion = ttk.Entry(frame_form, font=("sans", 11))
        self.ent_direccion.place(x=10, y=303, width=365, height=28)

        # Ciudad
        lbl_ciu = tk.Label(frame_form, text="Ciudad:", font=("sans", 10, "bold"), bg="#C6D9E3", fg="#1E293B")
        lbl_ciu.place(x=10, y=335)

        self.ent_ciudad = ttk.Entry(frame_form, font=("sans", 11))
        self.ent_ciudad.place(x=10, y=358, width=365, height=28)

        # Botones de Acción (4 Botones Cuadrados)
        acciones = [
            ("Registrar", "agregar.png", self.registrar_proveedor, 0, 0),
            ("Editar", "editar.png", self.modificar_proveedor, 0, 1),
            ("Eliminar", "eliminar.png", self.eliminar_proveedor, 1, 0),
            ("Limpiar", "limpiar.png", self.limpiar_formulario, 1, 1),
        ]

        frame_btns = tk.Frame(frame_form, bg="#C6D9E3")
        frame_btns.place(x=15, y=395, width=360, height=125)

        for txt, ico_file, cmd, r, c in acciones:
            ruta_i = self.rutas(f"icono/{ico_file}")
            if os.path.exists(ruta_i):
                img_i = Image.open(ruta_i).resize((22, 22), Image.Resampling.LANCZOS)
                self.images[f"prov_btn_{ico_file}"] = ImageTk.PhotoImage(img_i)
                ico_btn = self.images[f"prov_btn_{ico_file}"]
            else:
                ico_btn = None

            btn = tk.Button(
                frame_btns,
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
            btn.place(x=c * 180, y=r * 60, width=165, height=48)

#============== 3. PANEL DERECHO: BÚSQUEDA Y TABLA ==================================================#
        lbl_b = tk.Label(self, text="Buscar:", font=("sans", 12, "bold"), bg="#DDE1E5", fg="#1E293B")
        lbl_b.place(x=460, y=75)

        self.ent_buscar = ttk.Entry(self, font=("sans", 11))
        self.ent_buscar.place(x=530, y=73, width=220, height=30)
        self.ent_buscar.bind("<KeyRelease>", lambda e: self.filtrar_proveedores())

        ruta_b = self.rutas("icono/buscar.png")
        if os.path.exists(ruta_b):
            self.images["b_prov_ico"] = ImageTk.PhotoImage(Image.open(ruta_b).resize((22, 22), Image.Resampling.LANCZOS))
            btn_b = tk.Button(self, image=self.images["b_prov_ico"], bg="white", relief="solid", bd=1, cursor="hand2")
            btn_b.place(x=755, y=73, width=32, height=30)

        # Botón Exportar Excel
        ruta_ex = self.rutas("icono/excel.png")
        if os.path.exists(ruta_ex):
            self.images["ex_prov_ico"] = ImageTk.PhotoImage(Image.open(ruta_ex).resize((22, 22), Image.Resampling.LANCZOS))
            ico_ex = self.images["ex_prov_ico"]
        else:
            ico_ex = None

        btn_ex = tk.Button(
            self,
            text="  Exportar Excel",
            image=ico_ex,
            compound=tk.LEFT,
            font=("sans", 10, "bold"),
            bg="#15803D",
            fg="white",
            relief="raised",
            bd=2,
            cursor="hand2",
            command=self.exportar_excel
        )
        btn_ex.place(x=915, y=70, width=165, height=36)

        # Tabla
        style = ttk.Style()
        style.configure("PROV.Treeview.Heading", font=("sans", 9, "bold"), background="#E0E6ED")
        style.configure("PROV.Treeview", font=("sans", 9), rowheight=24)

        cols = ("id", "nombre", "nit", "telefono", "contacto", "ciudad")
        self.tabla = ttk.Treeview(self, columns=cols, show="headings", style="PROV.Treeview")
        self.tabla.place(x=460, y=115, width=620, height=500)

        titulos = [
            ("id", "ID", 40),
            ("nombre", "Razón Social / Nombre", 190),
            ("nit", "NIT / ID", 100),
            ("telefono", "Teléfono", 100),
            ("contacto", "Contacto", 110),
            ("ciudad", "Ciudad", 80),
        ]

        for c, t, w in titulos:
            self.tabla.heading(c, text=t, anchor="center")
            self.tabla.column(c, width=w, anchor="center" if c in ("id", "nit", "telefono", "ciudad") else "w")

        scroll_y = ttk.Scrollbar(self, orient="vertical", command=self.tabla.yview)
        self.tabla.configure(yscrollcommand=scroll_y.set)
        scroll_y.place(x=1082, y=115, height=500)

        self.tabla.bind("<<TreeviewSelect>>", self.al_seleccionar)

    def actualizar_reloj(self):
        ahora = datetime.datetime.now()
        self.lbl_fecha.config(text=ahora.strftime("%d-%m-%Y"))
        self.lbl_hora.config(text=ahora.strftime("%H:%M:%S"))
        self.after(1000, self.actualizar_reloj)

    def cargar_proveedores(self):
        for r in self.tabla.get_children():
            self.tabla.delete(r)

        try:
            self.proveedores = self.servicio_compras.listar_proveedores()
        except Exception as error:
            self.proveedores = []
            messagebox.showerror("Error", f"No se pudieron cargar los proveedores: {error}")

        for p in self.proveedores:
            self.tabla.insert("", tk.END, values=p)

    def al_seleccionar(self, event=None):
        sel = self.tabla.selection()
        if not sel:
            return
        vals = self.tabla.item(sel[0], "values")
        self.proveedor_seleccionado = vals
        self.ent_nombre.delete(0, tk.END)
        self.ent_nombre.insert(0, vals[1])
        self.ent_nit.delete(0, tk.END)
        self.ent_nit.insert(0, vals[2])
        self.ent_tel.delete(0, tk.END)
        self.ent_tel.insert(0, vals[3])
        self.ent_contacto.delete(0, tk.END)
        self.ent_contacto.insert(0, vals[4] if len(vals) > 4 else "")
        self.ent_ciudad.delete(0, tk.END)
        self.ent_ciudad.insert(0, vals[5] if len(vals) > 5 else "")

    def registrar_proveedor(self):
        nom = self.ent_nombre.get().strip()
        nit = self.ent_nit.get().strip()
        tel = self.ent_tel.get().strip()
        con = self.ent_contacto.get().strip()
        em = self.ent_email.get().strip()
        dir_p = self.ent_direccion.get().strip()
        ciu = self.ent_ciudad.get().strip()

        if not nom:
            messagebox.showwarning("Atención", "El nombre o razón social es obligatorio.")
            return

        try:
            self.servicio_compras.crear_proveedor((nom, nit, tel, con, em, dir_p, ciu))
            messagebox.showinfo("Éxito", f"Proveedor '{nom}' registrado exitosamente.")
            self.limpiar_formulario()
            self.cargar_proveedores()
        except Exception as e:
            messagebox.showerror("Error", f"Error registrando proveedor: {e}")

    def modificar_proveedor(self):
        if not self.proveedor_seleccionado:
            messagebox.showwarning("Atención", "Seleccione un proveedor de la tabla para editar.")
            return

        nom = self.ent_nombre.get().strip()
        nit = self.ent_nit.get().strip()
        tel = self.ent_tel.get().strip()
        con = self.ent_contacto.get().strip()
        em = self.ent_email.get().strip()
        dir_p = self.ent_direccion.get().strip()
        ciu = self.ent_ciudad.get().strip()

        try:
            self.servicio_compras.actualizar_proveedor(self.proveedor_seleccionado[0], (nom, nit, tel, con, em, dir_p, ciu))
            messagebox.showinfo("Éxito", "Proveedor actualizado correctamente.")
            self.limpiar_formulario()
            self.cargar_proveedores()
        except Exception as e:
            messagebox.showerror("Error", f"Error modificando proveedor: {e}")

    def eliminar_proveedor(self):
        if not self.proveedor_seleccionado:
            messagebox.showwarning("Atención", "Seleccione un proveedor de la tabla para eliminar.")
            return

        resp = messagebox.askyesno("Confirmar", f"¿Está seguro de eliminar al proveedor '{self.proveedor_seleccionado[1]}'?")
        if resp:
            try:
                self.servicio_compras.eliminar_proveedor(self.proveedor_seleccionado[0])
                messagebox.showinfo("Éxito", "Proveedor eliminado correctamente.")
                self.limpiar_formulario()
                self.cargar_proveedores()
            except Exception as e:
                messagebox.showerror("Error", f"Error eliminando proveedor: {e}")

    def limpiar_formulario(self):
        self.proveedor_seleccionado = None
        self.ent_nombre.delete(0, tk.END)
        self.ent_nit.delete(0, tk.END)
        self.ent_tel.delete(0, tk.END)
        self.ent_contacto.delete(0, tk.END)
        self.ent_email.delete(0, tk.END)
        self.ent_direccion.delete(0, tk.END)
        self.ent_ciudad.delete(0, tk.END)

    def filtrar_proveedores(self):
        q = self.ent_buscar.get().strip().lower()
        for r in self.tabla.get_children():
            self.tabla.delete(r)

        for p in self.proveedores:
            if not q or q in str(p[1]).lower() or q in str(p[2]).lower() or q in str(p[4]).lower():
                self.tabla.insert("", tk.END, values=p)

    def exportar_excel(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("Archivo CSV", "*.csv")], initialfile="Proveedores.csv")
        if file_path:
            try:
                with open(file_path, mode="w", newline="", encoding="utf-8-sig") as f:
                    w = csv.writer(f)
                    w.writerow(["ID", "Nombre", "NIT", "Teléfono", "Contacto", "Ciudad"])
                    for p in self.proveedores:
                        w.writerow(p)
                messagebox.showinfo("Exportar", "Proveedores exportados correctamente a CSV.")
            except Exception as e:
                messagebox.showerror("Error", f"Error exportando proveedores: {e}")
