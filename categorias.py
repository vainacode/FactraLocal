import csv
import os
import db_conexion as sqlite3
import sys
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageTk
from window_utils import posicionar_ventana
from servicios.servicio_inventario import ServicioInventario

class Categorias(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.title("Gestión de Categorías")
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
        self.categorias = []
        self.categoria_seleccionada = None

        self.widgets()
        self.cargar_categorias()

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
            text="GESTIÓN DE CATEGORÍAS",
            font=("sans", 24, "bold"),
            bg="#DDE1E5",
            fg="#1E293B"
        )
        lbl_title.place(relx=0.5, y=25, anchor="center")

#============== 2. PANEL IZQUIERDO: FORMULARIO =====================================================#
        frame_form = tk.LabelFrame(
            self,
            text="Datos de la Categoría",
            font=("sans", 13, "bold"),
            bg="#C6D9E3",
            fg="#1E293B",
            padx=15,
            pady=10
        )
        frame_form.place(x=20, y=60, width=390, height=515)

        # Nombre
        lbl_nom = tk.Label(frame_form, text="Nombre de la Categoría:", font=("sans", 11, "bold"), bg="#C6D9E3", fg="#1E293B")
        lbl_nom.place(x=10, y=10)

        self.ent_nombre = ttk.Entry(frame_form, font=("sans", 11))
        self.ent_nombre.place(x=10, y=38, width=335, height=32)

        # Descripción
        lbl_desc = tk.Label(frame_form, text="Descripción:", font=("sans", 11, "bold"), bg="#C6D9E3", fg="#1E293B")
        lbl_desc.place(x=10, y=85)

        self.txt_desc = tk.Text(frame_form, font=("sans", 10), wrap="word", relief="solid", bd=1)
        self.txt_desc.place(x=10, y=110, width=335, height=100)

        # Estado
        lbl_est = tk.Label(frame_form, text="Estado:", font=("sans", 11, "bold"), bg="#C6D9E3", fg="#1E293B")
        lbl_est.place(x=10, y=225)

        self.cmb_estado = ttk.Combobox(frame_form, values=["Activo", "Inactivo"], font=("sans", 10), state="readonly")
        self.cmb_estado.current(0)
        self.cmb_estado.place(x=10, y=250, width=335, height=30)

        # Botones de Acción
        acciones = [
            ("Registrar", "agregar.png", self.registrar_categoria, 0, 0),
            ("Editar", "editar.png", self.modificar_categoria, 0, 1),
            ("Eliminar", "eliminar.png", self.eliminar_categoria, 1, 0),
            ("Limpiar", "limpiar.png", self.limpiar_formulario, 1, 1),
        ]

        frame_btns = tk.Frame(frame_form, bg="#C6D9E3")
        frame_btns.place(x=10, y=330, width=340, height=130)

        for txt, ico_file, cmd, r, c in acciones:
            ruta_i = self.rutas(f"icono/{ico_file}")
            if os.path.exists(ruta_i):
                img_i = Image.open(ruta_i).resize((22, 22), Image.Resampling.LANCZOS)
                self.images[f"cat_btn_{ico_file}"] = ImageTk.PhotoImage(img_i)
                ico_btn = self.images[f"cat_btn_{ico_file}"]
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
            btn.place(x=c * 170, y=r * 58, width=155, height=48)

#============== 3. PANEL DERECHO: BÚSQUEDA Y TABLA ==================================================#
        lbl_b = tk.Label(self, text="Buscar:", font=("sans", 12, "bold"), bg="#DDE1E5", fg="#1E293B")
        lbl_b.place(x=430, y=68)

        self.ent_buscar = ttk.Entry(self, font=("sans", 11))
        self.ent_buscar.place(x=505, y=66, width=200, height=30)
        self.ent_buscar.bind("<KeyRelease>", lambda e: self.filtrar())

        ruta_ex = self.rutas("icono/excel.png")
        if os.path.exists(ruta_ex):
            self.images["ex_cat_ico"] = ImageTk.PhotoImage(Image.open(ruta_ex).resize((20, 20), Image.Resampling.LANCZOS))
            ico_ex = self.images["ex_cat_ico"]
        else:
            ico_ex = None

        btn_ex = tk.Button(self, text="  Exportar Excel", image=ico_ex, compound=tk.LEFT, font=("sans", 10, "bold"), bg="#15803D", fg="white", relief="raised", bd=2, cursor="hand2", command=self.exportar_excel)
        btn_ex.place(x=805, y=63, width=160, height=36)

        # Tabla
        style = ttk.Style()
        style.configure("CAT.Treeview.Heading", font=("sans", 9, "bold"), background="#E0E6ED")
        style.configure("CAT.Treeview", font=("sans", 9), rowheight=24)

        cols = ("id", "nombre", "descripcion", "total_prods", "estado")
        self.tabla = ttk.Treeview(self, columns=cols, show="headings", style="CAT.Treeview")
        self.tabla.place(x=430, y=110, width=535, height=465)

        titulos = [
            ("id", "ID", 40),
            ("nombre", "Categoría", 140),
            ("descripcion", "Descripción", 180),
            ("total_prods", "Total Prods", 85),
            ("estado", "Estado", 70),
        ]

        for c, t, w in titulos:
            self.tabla.heading(c, text=t, anchor="center")
            self.tabla.column(c, width=w, anchor="center" if c in ("id", "total_prods", "estado") else "w")

        scroll_y = ttk.Scrollbar(self, orient="vertical", command=self.tabla.yview)
        self.tabla.configure(yscrollcommand=scroll_y.set)
        scroll_y.place(x=950, y=110, height=465)

        self.tabla.bind("<<TreeviewSelect>>", self.al_seleccionar)

    def cargar_categorias(self):
        for r in self.tabla.get_children():
            self.tabla.delete(r)

        try:
            with sqlite3.connect(self.db_name) as conn:
                cur = conn.cursor()
                cur.execute('''
                    SELECT c.id, c.nombre, c.descripcion, COUNT(i.id), 'Activo'
                    FROM categorias c
                    LEFT JOIN inventario i ON i.categoria = c.nombre
                    GROUP BY c.id, c.nombre, c.descripcion
                ''')
                self.categorias = cur.fetchall()
        except Exception:
            self.categorias = []

        for c in self.categorias:
            self.tabla.insert("", tk.END, values=c)

    def al_seleccionar(self, event=None):
        sel = self.tabla.selection()
        if not sel:
            return
        vals = self.tabla.item(sel[0], "values")
        self.categoria_seleccionada = vals
        self.ent_nombre.delete(0, tk.END)
        self.ent_nombre.insert(0, vals[1])
        self.txt_desc.delete("1.0", tk.END)
        self.txt_desc.insert("1.0", vals[2] if len(vals) > 2 else "")
        self.cmb_estado.set(vals[4] if len(vals) > 4 else "Activo")

    def registrar_categoria(self):
        nom = self.ent_nombre.get().strip()
        desc = self.txt_desc.get("1.0", tk.END).strip()

        if not nom:
            messagebox.showwarning("Atención", "Ingrese el nombre de la categoría.")
            return

        try:
            self.servicio_inventario.crear_categoria(nom, desc)
            messagebox.showinfo("Éxito", f"Categoría '{nom}' registrada exitosamente.")
            self.limpiar_formulario()
            self.cargar_categorias()
        except Exception as e:
            messagebox.showerror("Error", f"Error registrando categoría: {e}")

    def modificar_categoria(self):
        if not self.categoria_seleccionada:
            messagebox.showwarning("Atención", "Seleccione una categoría para modificar.")
            return

        nom = self.ent_nombre.get().strip()
        desc = self.txt_desc.get("1.0", tk.END).strip()

        try:
            self.servicio_inventario.actualizar_categoria(self.categoria_seleccionada[0], nom, desc)
            messagebox.showinfo("Éxito", "Categoría modificada correctamente.")
            self.limpiar_formulario()
            self.cargar_categorias()
        except Exception as e:
            messagebox.showerror("Error", f"Error modificando categoría: {e}")

    def eliminar_categoria(self):
        if not self.categoria_seleccionada:
            messagebox.showwarning("Atención", "Seleccione una categoría para eliminar.")
            return

        resp = messagebox.askyesno("Confirmar", f"¿Está seguro de eliminar la categoría '{self.categoria_seleccionada[1]}'?")
        if resp:
            try:
                self.servicio_inventario.eliminar_categoria(self.categoria_seleccionada[0])
                messagebox.showinfo("Éxito", "Categoría eliminada.")
                self.limpiar_formulario()
                self.cargar_categorias()
            except Exception as e:
                messagebox.showerror("Error", f"Error eliminando: {e}")

    def limpiar_formulario(self):
        self.categoria_seleccionada = None
        self.ent_nombre.delete(0, tk.END)
        self.txt_desc.delete("1.0", tk.END)
        self.cmb_estado.current(0)

    def filtrar(self):
        q = self.ent_buscar.get().strip().lower()
        for r in self.tabla.get_children():
            self.tabla.delete(r)

        for c in self.categorias:
            if not q or q in str(c[1]).lower() or q in str(c[2]).lower():
                self.tabla.insert("", tk.END, values=c)

    def exportar_excel(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("Archivo CSV", "*.csv")], initialfile="Categorias.csv")
        if file_path:
            try:
                with open(file_path, mode="w", newline="", encoding="utf-8-sig") as f:
                    w = csv.writer(f)
                    w.writerow(["ID", "Categoría", "Descripción", "Total Productos", "Estado"])
                    for c in self.categorias:
                        w.writerow(c)
                messagebox.showinfo("Exportar", "Categorías exportadas correctamente a CSV.")
            except Exception as e:
                messagebox.showerror("Error", f"Error exportando: {e}")
