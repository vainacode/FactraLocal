import datetime
import os
import sys
import tkinter as tk
from tkinter import messagebox, ttk
from PIL import Image, ImageTk
from window_utils import posicionar_ventana
from servicios.servicio_caja import ServicioCaja

class ControlGastos(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.title("Punto de Venta Versión 4.4.7 - Control de Gastos")
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
        self.servicio_caja = ServicioCaja()
        self.images = {}
        self.gastos = []

        self.widgets()
        self.actualizar_reloj()

    def rutas(self, ruta):
        try:
            rutabase = sys.__MEIPASS
        except Exception:
            rutabase = os.path.abspath(".")
        return os.path.join(rutabase, ruta)

    def widgets(self):
#============== 1. HEADER CON FECHA Y HORA =========================================================#
        lbl_title = tk.Label(
            self,
            text="CONTROL DE GASTOS",
            font=("sans", 26, "bold"),
            bg="#DDE1E5",
            fg="#1E293B"
        )
        lbl_title.place(relx=0.5, y=30, anchor="center")

        # Calendario & Reloj Top Right
        frame_time = tk.Frame(self, bg="#DDE1E5")
        frame_time.place(x=770, y=20, width=310, height=35)

        ruta_cal = self.rutas("icono/calendario.png")
        if os.path.exists(ruta_cal):
            self.images["cal_cg_head"] = ImageTk.PhotoImage(Image.open(ruta_cal).resize((22, 22), Image.Resampling.LANCZOS))
            tk.Label(frame_time, image=self.images["cal_cg_head"], bg="#DDE1E5").place(x=0, y=5)

        ahora_inicial = datetime.datetime.now()
        self.lbl_fecha_h = tk.Label(frame_time, text=ahora_inicial.strftime("%d-%m-%Y"), font=("sans", 11, "bold"), bg="#DDE1E5", fg="#1E293B")
        self.lbl_fecha_h.place(x=30, y=6)

        ruta_reloj = self.rutas("icono/reloj.png")
        if not os.path.exists(ruta_reloj):
            ruta_reloj = self.rutas("icono/calendario.png")

        if os.path.exists(ruta_reloj):
            self.images["rel_cg_head"] = ImageTk.PhotoImage(Image.open(ruta_reloj).resize((22, 22), Image.Resampling.LANCZOS))
            tk.Label(frame_time, image=self.images["rel_cg_head"], bg="#DDE1E5").place(x=150, y=5)

        self.lbl_hora_h = tk.Label(frame_time, text=ahora_inicial.strftime("%H:%M:%S"), font=("sans", 11, "bold"), bg="#DDE1E5", fg="#1E293B")
        self.lbl_hora_h.place(x=180, y=6)

#============== 2. PANEL IZQUIERDO: REGISTRAR GASTO ================================================#
        frame_form = tk.LabelFrame(
            self,
            text="Registrar gasto",
            font=("sans", 14, "bold"),
            bg="#C6D9E3",
            fg="#1E293B",
            padx=15,
            pady=10
        )
        frame_form.place(x=20, y=65, width=390, height=550)

        # Concepto
        lbl_c = tk.Label(frame_form, text="Concepto:", font=("sans", 12, "bold"), bg="#C6D9E3", fg="#1E293B")
        lbl_c.place(x=10, y=10)

        self.ent_concepto = ttk.Entry(frame_form, font=("sans", 11))
        self.ent_concepto.place(x=10, y=35, width=335, height=32)

        # Valor
        lbl_v = tk.Label(frame_form, text="Valor:", font=("sans", 12, "bold"), bg="#C6D9E3", fg="#1E293B")
        lbl_v.place(x=10, y=85)

        self.ent_valor = ttk.Entry(frame_form, font=("sans", 11), justify="right")
        self.ent_valor.place(x=10, y=110, width=335, height=32)

        # Entidad
        lbl_e = tk.Label(frame_form, text="Entidad:", font=("sans", 12, "bold"), bg="#C6D9E3", fg="#1E293B")
        lbl_e.place(x=10, y=160)

        self.ent_entidad = ttk.Entry(frame_form, font=("sans", 11))
        self.ent_entidad.place(x=10, y=185, width=335, height=32)

        # Fecha
        lbl_f = tk.Label(frame_form, text="Fecha:", font=("sans", 12, "bold"), bg="#C6D9E3", fg="#1E293B")
        lbl_f.place(x=10, y=235)

        self.ent_fecha = ttk.Entry(frame_form, font=("sans", 11), justify="center")
        self.ent_fecha.place(x=10, y=260, width=280, height=32)
        self.ent_fecha.insert(0, datetime.datetime.now().strftime("%d-%m-%Y"))

        if "cal_cg_head" in self.images:
            btn_cal = tk.Button(frame_form, image=self.images["cal_cg_head"], bg="white", relief="solid", bd=1, cursor="hand2")
            btn_cal.place(x=300, y=260, width=32, height=32)

        # Botones de Acción (3 Grandes Cuadrados)
        ruta_ing = self.rutas("icono/agregar.png")
        if os.path.exists(ruta_ing):
            self.images["ing_cg"] = ImageTk.PhotoImage(Image.open(ruta_ing).resize((32, 32), Image.Resampling.LANCZOS))
            ico_ing = self.images["ing_cg"]
        else:
            ico_ing = None

        btn_ing = tk.Button(
            frame_form,
            text="Ingresar",
            image=ico_ing,
            compound=tk.TOP,
            font=("sans", 10, "bold"),
            bg="#EBEFF2",
            fg="#1E293B",
            relief="raised",
            bd=2,
            cursor="hand2",
            command=self.ingresar_gasto
        )
        btn_ing.place(x=20, y=360, width=95, height=85)

        ruta_elim = self.rutas("icono/eliminar.png")
        if os.path.exists(ruta_elim):
            self.images["elim_cg"] = ImageTk.PhotoImage(Image.open(ruta_elim).resize((32, 32), Image.Resampling.LANCZOS))
            ico_elim = self.images["elim_cg"]
        else:
            ico_elim = None

        btn_elim = tk.Button(
            frame_form,
            text="Eliminar",
            image=ico_elim,
            compound=tk.TOP,
            font=("sans", 10, "bold"),
            bg="#EBEFF2",
            fg="#1E293B",
            relief="raised",
            bd=2,
            cursor="hand2",
            command=self.eliminar_gasto
        )
        btn_elim.place(x=130, y=360, width=95, height=85)

        ruta_mod = self.rutas("icono/editar.png")
        if os.path.exists(ruta_mod):
            self.images["mod_cg"] = ImageTk.PhotoImage(Image.open(ruta_mod).resize((32, 32), Image.Resampling.LANCZOS))
            ico_mod = self.images["mod_cg"]
        else:
            ico_mod = None

        btn_mod = tk.Button(
            frame_form,
            text="Modificar",
            image=ico_mod,
            compound=tk.TOP,
            font=("sans", 10, "bold"),
            bg="#EBEFF2",
            fg="#1E293B",
            relief="raised",
            bd=2,
            cursor="hand2"
        )
        btn_mod.place(x=240, y=360, width=95, height=85)

#============== 3. PANEL DERECHO: BÚSQUEDA Y TABLA ==================================================#
        lbl_b = tk.Label(self, text="Buscar:", font=("sans", 12, "bold"), bg="#DDE1E5", fg="#1E293B")
        lbl_b.place(x=430, y=70)

        self.ent_buscar = ttk.Entry(self, font=("sans", 11))
        self.ent_buscar.place(x=505, y=68, width=220, height=30)

        ruta_busc = self.rutas("icono/buscar.png")
        if os.path.exists(ruta_busc):
            self.images["busc_cg_ico"] = ImageTk.PhotoImage(Image.open(ruta_busc).resize((22, 22), Image.Resampling.LANCZOS))
            btn_b_ico = tk.Button(self, image=self.images["busc_cg_ico"], bg="white", relief="solid", bd=1, cursor="hand2")
            btn_b_ico.place(x=730, y=68, width=32, height=30)

        # Paginador
        ruta_izq = self.rutas("icono/izquierda.png")
        if os.path.exists(ruta_izq):
            self.images["izq_cg"] = ImageTk.PhotoImage(Image.open(ruta_izq).resize((18, 18), Image.Resampling.LANCZOS))
            btn_izq = tk.Button(self, image=self.images["izq_cg"], bg="#EBEFF2", relief="raised", bd=1, cursor="hand2")
            btn_izq.place(x=880, y=70, width=24, height=24)

        ruta_der = self.rutas("icono/derecha.png")
        if os.path.exists(ruta_der):
            self.images["der_cg"] = ImageTk.PhotoImage(Image.open(ruta_der).resize((18, 18), Image.Resampling.LANCZOS))
            btn_der = tk.Button(self, image=self.images["der_cg"], bg="#EBEFF2", relief="raised", bd=1, cursor="hand2")
            btn_der.place(x=908, y=70, width=24, height=24)

        self.lbl_pag_info = tk.Label(self, text="Página 1 de 1", font=("sans", 10, "bold"), bg="#DDE1E5", fg="#1E293B")
        self.lbl_pag_info.place(x=940, y=72)

        # Tabla de Gastos
        style = ttk.Style()
        style.configure("CG.Treeview.Heading", font=("sans", 9, "bold"), background="#E0E6ED")
        style.configure("CG.Treeview", font=("sans", 9), rowheight=24)

        cols = ("id", "concepto", "valor", "entidad", "fecha", "origen")
        self.tabla = ttk.Treeview(self, columns=cols, show="headings", style="CG.Treeview")
        self.tabla.place(x=430, y=110, width=650, height=505)

        titulos = [
            ("id", "Id", 50),
            ("concepto", "Concepto", 180),
            ("valor", "Valor", 110),
            ("entidad", "Entidad", 120),
            ("fecha", "Fecha", 100),
            ("origen", "Origen", 80),
        ]

        for c, t, w in titulos:
            self.tabla.heading(c, text=t, anchor="center")
            self.tabla.column(c, width=w, anchor="center" if c in ("id", "fecha", "origen") else "e" if c == "valor" else "w")

        scroll_y = ttk.Scrollbar(self, orient="vertical", command=self.tabla.yview)
        self.tabla.configure(yscrollcommand=scroll_y.set)
        scroll_y.place(x=1065, y=110, height=505)

        self.cargar_gastos()

    def cargar_gastos(self):
        for r in self.tabla.get_children():
            self.tabla.delete(r)

        self.gastos = []
        try:
            for gid, conc, mnt, ent, fec, orig in self.servicio_caja.listar_gastos():
                    item = (gid, conc, f"RD$ {float(mnt or 0.0):,.2f}", ent or "General", fec, orig or "Caja")
                    self.gastos.append(item)
                    self.tabla.insert("", tk.END, values=item)
        except Exception as e:
            print("Error cargando gastos:", e)

    def actualizar_reloj(self):
        ahora = datetime.datetime.now()
        self.lbl_fecha_h.config(text=ahora.strftime("%d-%m-%Y"))
        self.lbl_hora_h.config(text=ahora.strftime("%H:%M:%S"))
        self.after(1000, self.actualizar_reloj)

    def ingresar_gasto(self):
        conc = self.ent_concepto.get().strip()
        val = self.ent_valor.get().strip()
        ent = self.ent_entidad.get().strip()
        fec = self.ent_fecha.get().strip()

        if not conc or not val:
            messagebox.showwarning("Atención", "Ingrese concepto y valor del gasto.")
            return

        from destino_gasto_modal import DestinoGastoModal
        from seleccionar_cuenta_banco import SeleccionarCuentaBanco

        def guardar_con_origen(origen_str):
            try:
                val_f = float(val.replace("RD$", "").replace("$", "").replace(",", ""))
                try:
                    ahora_fec = datetime.datetime.strptime(fec, "%d-%m-%Y").strftime("%Y-%m-%d")
                except ValueError:
                    ahora_fec = datetime.datetime.now().strftime("%Y-%m-%d")
                usuario = getattr(self.parent, "usuario", None)
                if not usuario:
                    user_info = getattr(getattr(self.parent, "controlador", None), "usuario_actual", {})
                    usuario = user_info.get("nombre") or user_info.get("username")
                self.servicio_caja.registrar_gasto(conc, val_f, ent or "General", ahora_fec, origen_str, usuario)

                messagebox.showinfo("Éxito", f"Gasto de RD$ {val_f:,.2f} registrado correctamente en {origen_str}.")
                self.ent_concepto.delete(0, tk.END)
                self.ent_valor.delete(0, tk.END)
                self.ent_entidad.delete(0, tk.END)
                self.cargar_gastos()
            except ValueError:
                messagebox.showerror("Error", "Ingrese un valor numérico válido.")
            except Exception as e:
                messagebox.showerror("Error", f"Error guardando gasto: {e}")

        def resolver_destino(dest):
            if dest == "Banco":
                SeleccionarCuentaBanco(self, callback_confirm=lambda b_nom, c_num: guardar_con_origen(f"Banco ({b_nom})"))
            elif dest == "Caja":
                guardar_con_origen("Caja")
            else:
                guardar_con_origen("Registro")

        DestinoGastoModal(self, callback_destino=resolver_destino)

    def eliminar_gasto(self):
        sel = self.tabla.selection()
        if not sel:
            messagebox.showwarning("Atención", "Seleccione un gasto para eliminar.")
            return
        vals = self.tabla.item(sel[0], "values")
        gid = vals[0]
        if messagebox.askyesno("Confirmar", f"¿Desea eliminar el gasto #{gid} ({vals[1]})?"):
            try:
                usuario = getattr(self.parent, "usuario", None)
                if not usuario:
                    user_info = getattr(getattr(self.parent, "controlador", None), "usuario_actual", {})
                    usuario = user_info.get("nombre") or user_info.get("username") or ""
                if not usuario:
                    raise ValueError("No hay un usuario autenticado para anular el gasto.")
                self.servicio_caja.anular_gasto(gid, usuario)
                self.cargar_gastos()
                messagebox.showinfo("Gasto anulado", "El gasto fue anulado y permanece en el historial de auditoría.")
            except Exception as e:
                messagebox.showerror("Error", f"Error eliminando gasto: {e}")
