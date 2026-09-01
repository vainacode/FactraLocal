import os
import datetime
import db_conexion as sqlite3
import sys
import tkinter as tk
from tkinter import messagebox, ttk
from PIL import Image, ImageTk
from window_utils import posicionar_ventana
from servicios.servicio_inventario import ServicioInventario

class Promociones(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.title("Gestión de Promociones y Descuentos")
        posicionar_ventana(self, 980, 600, parent)
        self.resizable(False, False)
        self.configure(bg="#DDE1E5")
        self.transient(parent)
        self.grab_set()
        try:
            self.iconbitmap(self.rutas('icono.ico'))
        except Exception:
            pass

        self.db_name = "database.db"
        self.servicio_inventario = ServicioInventario()
        self.images = {}
        self.promociones = []
        self.promocion_seleccionada = None

        self.widgets()
        self.cargar_promociones()

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
            text="GESTIÓN DE PROMOCIONES",
            font=("sans", 24, "bold"),
            bg="#DDE1E5",
            fg="#1E293B"
        )
        lbl_title.place(relx=0.5, y=25, anchor="center")

#============== 2. PANEL IZQUIERDO: FORMULARIO =====================================================#
        frame_form = tk.LabelFrame(
            self,
            text="Datos de la Promoción",
            font=("sans", 13, "bold"),
            bg="#C6D9E3",
            fg="#1E293B",
            padx=15,
            pady=10
        )
        frame_form.place(x=20, y=60, width=390, height=515)

        # Nombre
        lbl_nom = tk.Label(frame_form, text="Nombre de la Promoción:", font=("sans", 10, "bold"), bg="#C6D9E3", fg="#1E293B")
        lbl_nom.place(x=10, y=5)

        self.ent_nombre = ttk.Entry(frame_form, font=("sans", 11))
        self.ent_nombre.place(x=10, y=28, width=335, height=28)

        # Tipo
        lbl_tip = tk.Label(frame_form, text="Tipo de Descuento:", font=("sans", 10, "bold"), bg="#C6D9E3", fg="#1E293B")
        lbl_tip.place(x=10, y=65)

        self.cmb_tipo = ttk.Combobox(frame_form, values=["Porcentaje (%)", "Valor Fijo ($)"], font=("sans", 10), state="readonly")
        self.cmb_tipo.current(0)
        self.cmb_tipo.place(x=10, y=88, width=335, height=28)

        # Descuento Valor
        lbl_desc = tk.Label(frame_form, text="Valor / Porcentaje:", font=("sans", 10, "bold"), bg="#C6D9E3", fg="#1E293B")
        lbl_desc.place(x=10, y=125)

        self.ent_descuento = ttk.Entry(frame_form, font=("sans", 11), justify="center")
        self.ent_descuento.place(x=10, y=148, width=335, height=28)

        # Fecha Inicio & Fin
        lbl_ini = tk.Label(frame_form, text="Fecha Inicio (AAAA-MM-DD):", font=("sans", 10, "bold"), bg="#C6D9E3", fg="#1E293B")
        lbl_ini.place(x=10, y=185)

        self.ent_inicio = ttk.Entry(frame_form, font=("sans", 11), justify="center")
        self.ent_inicio.place(x=10, y=208, width=335, height=28)
        hoy = datetime.date.today()
        self.ent_inicio.insert(0, hoy.strftime("%Y-%m-%d"))

        lbl_fin = tk.Label(frame_form, text="Fecha Fin (AAAA-MM-DD):", font=("sans", 10, "bold"), bg="#C6D9E3", fg="#1E293B")
        lbl_fin.place(x=10, y=245)

        self.ent_fin = ttk.Entry(frame_form, font=("sans", 11), justify="center")
        self.ent_fin.place(x=10, y=268, width=335, height=28)
        self.ent_fin.insert(0, (hoy + datetime.timedelta(days=30)).strftime("%Y-%m-%d"))

        # Estado
        lbl_est = tk.Label(frame_form, text="Estado:", font=("sans", 10, "bold"), bg="#C6D9E3", fg="#1E293B")
        lbl_est.place(x=10, y=305)

        self.cmb_estado = ttk.Combobox(frame_form, values=["Activa", "Inactiva"], font=("sans", 10), state="readonly")
        self.cmb_estado.current(0)
        self.cmb_estado.place(x=10, y=328, width=335, height=28)

        # Botones
        acciones = [
            ("Registrar", "agregar.png", self.registrar, 0, 0),
            ("Editar", "editar.png", self.modificar, 0, 1),
            ("Eliminar", "eliminar.png", self.eliminar, 1, 0),
            ("Limpiar", "limpiar.png", self.limpiar, 1, 1),
        ]

        frame_btns = tk.Frame(frame_form, bg="#C6D9E3")
        frame_btns.place(x=10, y=375, width=340, height=110)

        for txt, ico_file, cmd, r, c in acciones:
            ruta_i = self.rutas(f"icono/{ico_file}")
            if os.path.exists(ruta_i):
                img_i = Image.open(ruta_i).resize((22, 22), Image.Resampling.LANCZOS)
                self.images[f"promo_btn_{ico_file}"] = ImageTk.PhotoImage(img_i)
                ico_btn = self.images[f"promo_btn_{ico_file}"]
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
            btn.place(x=c * 170, y=r * 52, width=155, height=44)

#============== 3. PANEL DERECHO: TABLA =============================================================#
        style = ttk.Style()
        style.configure("PRM.Treeview.Heading", font=("sans", 9, "bold"), background="#E0E6ED")
        style.configure("PRM.Treeview", font=("sans", 9), rowheight=24)

        cols = ("id", "nombre", "tipo", "descuento", "vigencia", "estado")
        self.tabla = ttk.Treeview(self, columns=cols, show="headings", style="PRM.Treeview")
        self.tabla.place(x=430, y=65, width=530, height=510)

        titulos = [
            ("id", "ID", 40),
            ("nombre", "Promoción", 160),
            ("tipo", "Tipo", 100),
            ("descuento", "Descuento", 90),
            ("vigencia", "Vigencia", 120),
            ("estado", "Estado", 70),
        ]

        for c, t, w in titulos:
            self.tabla.heading(c, text=t, anchor="center")
            self.tabla.column(c, width=w, anchor="center" if c in ("id", "tipo", "descuento", "vigencia", "estado") else "w")

        scroll_y = ttk.Scrollbar(self, orient="vertical", command=self.tabla.yview)
        self.tabla.configure(yscrollcommand=scroll_y.set)
        scroll_y.place(x=945, y=65, height=510)

        self.tabla.bind("<<TreeviewSelect>>", self.al_seleccionar)

    def cargar_promociones(self):
        for r in self.tabla.get_children():
            self.tabla.delete(r)

        try:
            with sqlite3.connect(self.db_name) as conn:
                cur = conn.cursor()
                cur.execute("SELECT id, nombre, tipo, descuento, fecha_inicio || ' al ' || fecha_fin, estado FROM promociones")
                self.promociones = cur.fetchall()
        except Exception:
            self.promociones = []

        for p in self.promociones:
            self.tabla.insert("", tk.END, values=p)

    def al_seleccionar(self, event=None):
        sel = self.tabla.selection()
        if not sel:
            return
        vals = self.tabla.item(sel[0], "values")
        self.promocion_seleccionada = vals
        self.ent_nombre.delete(0, tk.END)
        self.ent_nombre.insert(0, vals[1])
        self.cmb_tipo.set(vals[2])
        self.ent_descuento.delete(0, tk.END)
        self.ent_descuento.insert(0, vals[3].replace("%", "").replace("$", "").strip())
        self.cmb_estado.set(vals[5] if len(vals) > 5 else "Activa")

    def registrar(self):
        nom = self.ent_nombre.get().strip()
        desc = self.ent_descuento.get().strip()
        tip = self.cmb_tipo.get()
        f_ini = self.ent_inicio.get().strip()
        f_fin = self.ent_fin.get().strip()
        est = self.cmb_estado.get()

        if not nom or not desc:
            messagebox.showwarning("Atención", "Nombre y valor del descuento son requeridos.")
            return

        try:
            self.servicio_inventario.crear_promocion((nom, tip, float(desc), f_ini, f_fin, est))
            messagebox.showinfo("Éxito", f"Promoción '{nom}' registrada exitosamente.")
            self.limpiar()
            self.cargar_promociones()
        except Exception as e:
            messagebox.showerror("Error", f"Error registrando promoción: {e}")

    def modificar(self):
        if not self.promocion_seleccionada:
            messagebox.showwarning("Atención", "Seleccione una promoción para editar.")
            return

        nom = self.ent_nombre.get().strip()
        desc = self.ent_descuento.get().strip()
        tip = self.cmb_tipo.get()
        est = self.cmb_estado.get()

        try:
            self.servicio_inventario.actualizar_promocion(self.promocion_seleccionada[0], (nom, tip, float(desc), est))
            messagebox.showinfo("Éxito", "Promoción modificada exitosamente.")
            self.limpiar()
            self.cargar_promociones()
        except Exception as e:
            messagebox.showerror("Error", f"Error modificando: {e}")

    def eliminar(self):
        if not self.promocion_seleccionada:
            messagebox.showwarning("Atención", "Seleccione una promoción para eliminar.")
            return

        resp = messagebox.askyesno("Confirmar", f"¿Está seguro de eliminar la promoción '{self.promocion_seleccionada[1]}'?")
        if resp:
            try:
                self.servicio_inventario.eliminar_promocion(self.promocion_seleccionada[0])
                messagebox.showinfo("Éxito", "Promoción eliminada.")
                self.limpiar()
                self.cargar_promociones()
            except Exception as e:
                messagebox.showerror("Error", f"Error eliminando: {e}")

    def limpiar(self):
        self.promocion_seleccionada = None
        self.ent_nombre.delete(0, tk.END)
        self.ent_descuento.delete(0, tk.END)
        self.cmb_tipo.current(0)
        self.cmb_estado.current(0)
