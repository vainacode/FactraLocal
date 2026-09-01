import os
import db_conexion
import db_conexion as sqlite3
import sys
import tkinter as tk
from tkinter import messagebox, ttk
from PIL import Image, ImageTk
from window_utils import posicionar_ventana
from seguridad import cifrar_secreto
from servicios.servicio_configuracion import ServicioConfiguracion

MODOS = [
    ("informal", "Informal (ticket sin valor fiscal)"),
    ("ncf_tradicional", "NCF tradicional (rangos autorizados por DGII, sin e-CF)"),
    ("ecf_factrapi", "Factura Electrónica e-CF (vía FactrAPI)"),
]
MODOS_POR_ETIQUETA = {etiqueta: clave for clave, etiqueta in MODOS}
ETIQUETAS_POR_MODO = {clave: etiqueta for clave, etiqueta in MODOS}

AMBIENTES = ["pruebas", "certificacion", "produccion"]


class NumeracionFiscalConfig(tk.Toplevel):
    """Configuración base de la Fase 1 del plan de facturación electrónica
    (ver PLAN_FACTURACION_ELECTRONICA.md): modo de facturación, punto de
    venta fijo de esta instalación, conexión con FactrAPI y estado de la
    numeración local."""

    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.title("Numeración y Facturación Electrónica")
        posicionar_ventana(self, 900, 620, parent)
        self.resizable(False, False)
        self.configure(bg="#DDE1E5")
        self.transient(parent)
        self.grab_set()
        try:
            self.iconbitmap(self.rutas('icono.ico'))
        except Exception:
            pass

        self.db_name = "database.db"
        self.images = {}
        self.punto_venta_actual = None
        self.api_key_guardada = None
        self.servicio_configuracion = ServicioConfiguracion()

        self.widgets()
        self.cargar_datos()

    def rutas(self, ruta):
        try:
            rutabase = sys.__MEIPASS
        except Exception:
            rutabase = os.path.abspath(".")
        return os.path.join(rutabase, ruta)

    def widgets(self):
        lbl_title = tk.Label(
            self, text="NUMERACIÓN Y FACTURACIÓN ELECTRÓNICA",
            font=("sans", 18, "bold"), bg="#DDE1E5", fg="#1E293B"
        )
        lbl_title.place(relx=0.5, y=25, anchor="center")

        # ============== 1. MODO DE FACTURACIÓN ==============
        frame_modo = tk.LabelFrame(
            self, text="Modo de Facturación", font=("sans", 12, "bold"),
            bg="#C6D9E3", fg="#1E293B", padx=15, pady=10
        )
        frame_modo.place(x=20, y=55, width=860, height=95)

        tk.Label(frame_modo, text="Modo actual:", font=("sans", 10, "bold"), bg="#C6D9E3", fg="#1E293B").place(x=10, y=8)

        self.cmb_modo = ttk.Combobox(
            frame_modo, values=[e for _, e in MODOS], font=("sans", 10), state="readonly"
        )
        self.cmb_modo.place(x=10, y=32, width=560, height=28)

        tk.Label(
            frame_modo,
            text="El modo informal (ticket) sigue funcionando siempre igual que hoy.\n"
                 "Los otros dos modos numeran con secuencias propias, separadas del ticket informal.",
            font=("sans", 8, "italic"), bg="#C6D9E3", fg="#475569", justify="left"
        ).place(x=580, y=8)

        # ============== 2. PUNTO DE VENTA DE ESTA INSTALACIÓN ==============
        frame_pv = tk.LabelFrame(
            self, text="Punto de Venta de esta instalación", font=("sans", 12, "bold"),
            bg="#C6D9E3", fg="#1E293B", padx=15, pady=10
        )
        frame_pv.place(x=20, y=160, width=860, height=140)

        tk.Label(
            frame_pv,
            text="Cada instalación del sistema opera siempre con el mismo Punto de Venta\n"
                 "(caja/terminal fija). Se configura una sola vez.",
            font=("sans", 9), bg="#C6D9E3", fg="#334155", justify="left"
        ).place(x=10, y=2)

        tk.Label(frame_pv, text="Código:", font=("sans", 10, "bold"), bg="#C6D9E3", fg="#1E293B").place(x=10, y=48)
        self.ent_pv_codigo = ttk.Entry(frame_pv, font=("sans", 10))
        self.ent_pv_codigo.place(x=10, y=70, width=180, height=28)

        tk.Label(frame_pv, text="Nombre:", font=("sans", 10, "bold"), bg="#C6D9E3", fg="#1E293B").place(x=210, y=48)
        self.ent_pv_nombre = ttk.Entry(frame_pv, font=("sans", 10))
        self.ent_pv_nombre.place(x=210, y=70, width=250, height=28)

        tk.Label(frame_pv, text="Sucursal:", font=("sans", 10, "bold"), bg="#C6D9E3", fg="#1E293B").place(x=480, y=48)
        self.cmb_pv_sucursal = ttk.Combobox(frame_pv, font=("sans", 10), state="readonly")
        self.cmb_pv_sucursal.place(x=480, y=70, width=200, height=28)

        self.lbl_pv_estado = tk.Label(frame_pv, text="", font=("sans", 9, "bold"), bg="#C6D9E3", fg="#16A34A")
        self.lbl_pv_estado.place(x=10, y=105)

        # ============== 3. CONEXIÓN FACTRAPI ==============
        frame_api = tk.LabelFrame(
            self, text="Conexión con FactrAPI (facturación electrónica DGII)", font=("sans", 12, "bold"),
            bg="#C6D9E3", fg="#1E293B", padx=15, pady=10
        )
        frame_api.place(x=20, y=310, width=860, height=170)

        tk.Label(
            frame_api,
            text="La conexión se usa para emitir e-CF, consultar secuencias y sincronizar\n"
                 "clientes y puntos de venta. Use credenciales del ambiente seleccionado.",
            font=("sans", 8, "italic"), bg="#C6D9E3", fg="#B45309", justify="left"
        ).place(x=10, y=2)

        tk.Label(frame_api, text="Ambiente:", font=("sans", 10, "bold"), bg="#C6D9E3", fg="#1E293B").place(x=10, y=45)
        self.cmb_ambiente = ttk.Combobox(frame_api, values=AMBIENTES, font=("sans", 10), state="readonly")
        self.cmb_ambiente.place(x=10, y=67, width=160, height=28)

        tk.Label(frame_api, text="URL base:", font=("sans", 10, "bold"), bg="#C6D9E3", fg="#1E293B").place(x=190, y=45)
        self.ent_url_base = ttk.Entry(frame_api, font=("sans", 10))
        self.ent_url_base.place(x=190, y=67, width=320, height=28)

        tk.Label(frame_api, text="API Key:", font=("sans", 10, "bold"), bg="#C6D9E3", fg="#1E293B").place(x=530, y=45)
        self.ent_api_key = ttk.Entry(frame_api, font=("sans", 10), show="*")
        self.ent_api_key.place(x=530, y=67, width=310, height=28)

        self.lbl_api_estado = tk.Label(
            frame_api, text="Sin verificar", font=("sans", 9, "bold"), bg="#C6D9E3", fg="#64748B"
        )
        self.lbl_api_estado.place(x=10, y=110)

        # ============== 4. NUMERACIÓN LOCAL (solo lectura) ==============
        frame_num = tk.LabelFrame(
            self, text="Numeración local actual", font=("sans", 12, "bold"),
            bg="#C6D9E3", fg="#1E293B", padx=15, pady=10
        )
        frame_num.place(x=20, y=490, width=860, height=70)

        self.lbl_num_venta = tk.Label(frame_num, text="Próximo ticket de venta: -", font=("sans", 10, "bold"), bg="#C6D9E3", fg="#1E293B")
        self.lbl_num_venta.place(x=10, y=8)

        self.lbl_num_cotizacion = tk.Label(frame_num, text="Próxima cotización: -", font=("sans", 10, "bold"), bg="#C6D9E3", fg="#1E293B")
        self.lbl_num_cotizacion.place(x=310, y=8)

        self.lbl_num_pedido = tk.Label(frame_num, text="Próximo pedido: -", font=("sans", 10, "bold"), bg="#C6D9E3", fg="#1E293B")
        self.lbl_num_pedido.place(x=600, y=8)

        # ============== BOTONES ==============
        ruta_save = self.rutas("icono/guardar.png")
        ico_save = None
        if os.path.exists(ruta_save):
            self.images["save_nfc"] = ImageTk.PhotoImage(Image.open(ruta_save).resize((22, 22), Image.Resampling.LANCZOS))
            ico_save = self.images["save_nfc"]

        btn_save = tk.Button(
            self, text="  Guardar Configuración", image=ico_save, compound=tk.LEFT,
            font=("sans", 11, "bold"), bg="#22C55E", fg="white",
            relief="raised", bd=2, cursor="hand2", command=self.guardar
        )
        btn_save.place(x=250, y=575, width=220, height=40)

        btn_cerrar = tk.Button(
            self, text="Cerrar", font=("sans", 11, "bold"), bg="#EBEFF2", fg="#1E293B",
            relief="raised", bd=2, cursor="hand2", command=self.destroy
        )
        btn_cerrar.place(x=490, y=575, width=140, height=40)

    def cargar_datos(self):
        try:
            with sqlite3.connect(self.db_name) as conn:
                cur = conn.cursor()

                cur.execute("SELECT nombre FROM sucursal WHERE estado != 'Inactivo' OR estado IS NULL")
                sucursales = [r[0] for r in cur.fetchall()]
                self.cmb_pv_sucursal["values"] = sucursales
                if sucursales:
                    self.cmb_pv_sucursal.current(0)

                cur.execute('''
                    SELECT modo_facturacion, punto_venta_id, factrapi_ambiente, factrapi_url_base, factrapi_api_key
                    FROM configuracion_general WHERE id = 1
                ''')
                fila = cur.fetchone()
                if fila:
                    modo, pv_id, ambiente, url_base, api_key = fila
                    self.cmb_modo.set(ETIQUETAS_POR_MODO.get(modo, ETIQUETAS_POR_MODO["informal"]))
                    self.cmb_ambiente.set(ambiente or "pruebas")
                    if url_base:
                        self.ent_url_base.insert(0, url_base)
                    if api_key:
                        self.api_key_guardada = api_key
                        self.lbl_api_estado.config(text="API Key guardada (oculta)", fg="#0284C7")

                    if pv_id:
                        cur.execute("SELECT id, codigo, nombre, sucursal_id FROM puntos_venta WHERE id = ?", (pv_id,))
                        pv = cur.fetchone()
                        if pv:
                            self.punto_venta_actual = pv[0]
                            self.ent_pv_codigo.insert(0, pv[1])
                            self.ent_pv_nombre.insert(0, pv[2])
                            self.lbl_pv_estado.config(text=f"Punto de venta configurado: {pv[1]}", fg="#16A34A")
                else:
                    self.cmb_modo.set(ETIQUETAS_POR_MODO["informal"])
                    self.cmb_ambiente.set("pruebas")

                if not self.punto_venta_actual:
                    self.lbl_pv_estado.config(text="Sin configurar todavía — complete código y nombre y guarde.", fg="#B45309")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo cargar la configuración: {e}")

        try:
            self.lbl_num_venta.config(text=f"Próximo ticket de venta: {db_conexion.ver_siguiente_numero('ticket_venta')}")
            self.lbl_num_cotizacion.config(text=f"Próxima cotización: {db_conexion.ver_siguiente_numero('cotizacion')}")
            self.lbl_num_pedido.config(text=f"Próximo pedido: {db_conexion.ver_siguiente_numero('pedido')}")
        except Exception:
            pass

    def guardar(self):
        etiqueta_modo = self.cmb_modo.get()
        modo = MODOS_POR_ETIQUETA.get(etiqueta_modo, "informal")
        ambiente = self.cmb_ambiente.get() or "pruebas"
        url_base = self.ent_url_base.get().strip()
        api_key = self.ent_api_key.get().strip()
        if modo == "ecf_factrapi" and os.getenv("POS_ENV", "development").lower() == "production" and not os.getenv("POS_FACTRAPI_ENCRYPTION_KEY"):
            messagebox.showerror("Configuración incompleta", "Configure POS_FACTRAPI_ENCRYPTION_KEY antes de activar e-CF en producción.")
            return
        if api_key:
            api_key_db = cifrar_secreto(api_key)
        elif self.api_key_guardada and not str(self.api_key_guardada).startswith("fernet$") and os.getenv("POS_FACTRAPI_ENCRYPTION_KEY"):
            # Migra una clave antigua en claro sin obligar al usuario a
            # volver a escribirla en la pantalla.
            api_key_db = cifrar_secreto(self.api_key_guardada)
        else:
            api_key_db = self.api_key_guardada

        codigo_pv = self.ent_pv_codigo.get().strip()
        nombre_pv = self.ent_pv_nombre.get().strip()
        sucursal_nom = self.cmb_pv_sucursal.get()

        try:
            punto_venta_id = self.servicio_configuracion.guardar_numeracion_fiscal(
                modo, self.punto_venta_actual, codigo_pv, nombre_pv, sucursal_nom,
                ambiente, url_base, api_key_db)
            self.punto_venta_actual = punto_venta_id

            messagebox.showinfo("Éxito", "Configuración guardada correctamente.")
            self.lbl_pv_estado.config(text=f"Punto de venta configurado: {codigo_pv}" if codigo_pv else "Sin configurar todavía.", fg="#16A34A" if codigo_pv else "#B45309")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar la configuración: {e}\n\nSi el código de punto de venta ya existe, use uno distinto.")
