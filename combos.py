import os
import db_conexion as sqlite3
import sys
import tkinter as tk
from tkinter import messagebox, ttk
from PIL import Image, ImageTk
from window_utils import posicionar_ventana
from servicios.servicio_inventario import ServicioInventario

class Combos(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.title("Ver Combos")
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
        self.combos_lista = []
        self.combo_actual = ""
        self.servicio_inventario = ServicioInventario()

        self.widgets()
        self.cargar_combos()

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
            text="VER COMBOS",
            font=("sans", 22, "bold"),
            bg="#C6D9E3",
            fg="#1E293B"
        )
        lbl_title.place(relx=0.5, y=28, anchor="center")

#============== 2. GRUPO SELECCIONAR COMBO =========================================================#
        frame_sel = tk.LabelFrame(
            self,
            text="Seleccionar Combo",
            font=("sans", 11, "bold"),
            bg="#C6D9E3",
            fg="#1E293B",
            padx=12,
            pady=10
        )
        frame_sel.place(x=20, y=60, width=940, height=90)

        lbl_c = tk.Label(frame_sel, text="Combo:", font=("sans", 12, "bold"), bg="#C6D9E3", fg="#1E293B")
        lbl_c.place(x=10, y=10)

        self.cmb_combo = ttk.Combobox(frame_sel, font=("sans", 11), state="readonly")
        self.cmb_combo.place(x=90, y=8, width=320, height=30)
        self.cmb_combo.bind("<<ComboboxSelected>>", self.al_cambiar_combo)

        # Precio Venta
        lbl_pv = tk.Label(frame_sel, text="Precio Venta:", font=("sans", 12, "bold"), bg="#C6D9E3", fg="#1E293B")
        lbl_pv.place(x=430, y=10)

        self.ent_pv = ttk.Entry(frame_sel, font=("sans", 12, "bold"), justify="center")
        self.ent_pv.place(x=560, y=8, width=160, height=30)

        # Costo Total
        lbl_ct = tk.Label(frame_sel, text="Costo Total:", font=("sans", 12, "bold"), bg="#C6D9E3", fg="#1E293B")
        lbl_ct.place(x=430, y=48)

        self.ent_ct = ttk.Entry(frame_sel, font=("sans", 12, "bold"), justify="center")
        self.ent_ct.place(x=560, y=46, width=160, height=30)

#============== 3. GRUPO PRODUCTOS DEL COMBO =======================================================#
        frame_prods = tk.LabelFrame(
            self,
            text="Productos del Combo",
            font=("sans", 11, "bold"),
            bg="#C6D9E3",
            fg="#1E293B",
            padx=10,
            pady=8
        )
        frame_prods.place(x=20, y=160, width=940, height=360)

        style = ttk.Style()
        style.configure("Combos.Treeview.Heading", font=("sans", 9, "bold"), background="#E0E6ED")
        style.configure("Combos.Treeview", font=("sans", 10), rowheight=24)

        cols = ("codigo", "producto", "cantidad", "costo_u", "costo_t")
        self.tabla = ttk.Treeview(frame_prods, columns=cols, show="headings", style="Combos.Treeview")
        self.tabla.place(x=10, y=10, width=900, height=310)

        titulos = [
            ("codigo", "Código", 90),
            ("producto", "Producto", 440),
            ("cantidad", "Cantidad", 90),
            ("costo_u", "Costo Unitario", 140),
            ("costo_t", "Costo Total", 140),
        ]

        for c, t, w in titulos:
            self.tabla.heading(c, text=t, anchor="center")
            self.tabla.column(c, width=w, anchor="center" if c in ("codigo", "cantidad") else "w" if c == "producto" else "e")

        scroll_y = ttk.Scrollbar(frame_prods, orient="vertical", command=self.tabla.yview)
        self.tabla.configure(yscrollcommand=scroll_y.set)
        scroll_y.place(x=912, y=10, height=310)

#============== 4. BOTONES INFERIORES ===============================================================#
        acciones = [
            ("Editar", "editar.png", self.editar_combo),
            ("Eliminar", "eliminar.png", self.eliminar_combo),
            ("Activar", "agregar.png", self.activar_combo),
            ("Cerrar", "cancelar.png", self.destroy),
        ]

        x_btn = 60
        for txt, ico_f, cmd in acciones:
            ruta_i = self.rutas(f"icono/{ico_f}")
            if os.path.exists(ruta_i):
                img_i = Image.open(ruta_i).resize((22, 22), Image.Resampling.LANCZOS)
                self.images[f"btn_cmb_{ico_f}"] = ImageTk.PhotoImage(img_i)
                ico_btn = self.images[f"btn_cmb_{ico_f}"]
            else:
                ico_btn = None

            btn = tk.Button(
                self,
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
            btn.place(x=x_btn, y=535, width=170, height=44)
            x_btn += 225

    def cargar_combos(self):
        try:
            with sqlite3.connect(self.db_name) as conn:
                cur = conn.cursor()
                cur.execute("SELECT nombre FROM combos WHERE estado != 'Inactivo' OR estado IS NULL")
                cbs = [r[0] for r in cur.fetchall()]
                self.cmb_combo["values"] = cbs
                if cbs:
                    self.cmb_combo.current(0)
                    self.al_cambiar_combo()
        except Exception as e:
            print("Error cargando combos:", e)

    def al_cambiar_combo(self, event=None):
        nom = self.cmb_combo.get()
        for r in self.tabla.get_children():
            self.tabla.delete(r)

        if not nom:
            return
        try:
            with sqlite3.connect(self.db_name) as conn:
                fila = conn.execute(
                    "SELECT precio_venta, costo_total FROM combos WHERE nombre = ?", (nom,)
                ).fetchone()
            if fila:
                self.ent_pv.delete(0, tk.END)
                self.ent_pv.insert(0, f"$ {float(fila[0] or 0):,.2f}")
                self.ent_ct.delete(0, tk.END)
                self.ent_ct.insert(0, f"$ {float(fila[1] or 0):,.2f}")
        except Exception as error:
            messagebox.showerror("Error", f"No se pudo cargar el combo: {error}")

    def editar_combo(self):
        from combo_detalle import DetalleComboModal
        DetalleComboModal(self, combo_nombre=self.cmb_combo.get())

    def eliminar_combo(self):
        nombre = self.cmb_combo.get().strip()
        if not nombre:
            messagebox.showwarning("Combo", "Seleccione un combo.")
            return
        if messagebox.askyesno("Confirmar", f"¿Desea desactivar el combo '{nombre}'?"):
            try:
                self.servicio_inventario.cambiar_estado_combo(nombre, "Inactivo")
                self.cargar_combos()
                messagebox.showinfo("Éxito", "Combo desactivado correctamente.")
            except Exception as error:
                messagebox.showerror("Error", f"No se pudo desactivar el combo: {error}")

    def activar_combo(self):
        nombre = self.cmb_combo.get().strip()
        if not nombre:
            messagebox.showwarning("Combo", "Seleccione un combo.")
            return
        try:
            self.servicio_inventario.cambiar_estado_combo(nombre, "Activo")
            self.cargar_combos()
            messagebox.showinfo("Activar", f"Combo '{nombre}' activado para ventas.")
        except Exception as error:
            messagebox.showerror("Error", f"No se pudo activar el combo: {error}")
