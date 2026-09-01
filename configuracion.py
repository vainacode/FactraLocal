import glob
import os
import shutil
import subprocess
import db_conexion as sqlite3
import sys
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
from window_utils import posicionar_ventana
from servicios.servicio_configuracion import ServicioConfiguracion


def _herramienta_postgres(nombre):
    """Devuelve la ruta de una herramienta PostgreSQL instalada en el equipo."""
    encontrada = shutil.which(nombre)
    if encontrada:
        return encontrada
    candidatos = []
    for raiz in (r"C:\Program Files\PostgreSQL", r"C:\Program Files (x86)\PostgreSQL"):
        candidatos.extend(glob.glob(os.path.join(raiz, "*", "bin", f"{nombre}.exe")))
    return sorted(candidatos, reverse=True)[0] if candidatos else None


class Configuracion(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.servicio_configuracion = ServicioConfiguracion()
        self.title("Punto de Venta Versión 4.4.7 - Configuración")
        posicionar_ventana(self, 1100, 650, parent)
        self.resizable(False, False)
        self.configure(bg="#DDE1E5")
        self.transient(parent)
        self.grab_set()
        try:
            self.iconbitmap(self.rutas('icono.ico'))
        except Exception:
            pass

        self.images = {}
        self.widgets()

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
            text="CONFIGURACIÓN",
            font=("sans", 28, "bold"),
            bg="#DDE1E5",
            fg="#1E293B"
        )
        lbl_titulo.place(relx=0.5, y=35, anchor="center")

#============== 2. COLUMNAS DE CONFIGURACIÓN (4 COLUMNAS) ==========================================#
        columnas = [
            # Columna 1 (x=25)
            [
                ("Mi Empresa", "btnproveedor.png", self.abrir_empresa),
                ("Sucursales", "sucursal.png", self.abrir_sucursales),
                ("Categorias", "categorias.png", self.abrir_categorias),
                ("Impresora", "impresora.png", self.abrir_impresora),
                ("Generar Barcode", "barcode.png", self.abrir_barcode),
                ("Bancos", "btnbanco.png", self.abrir_bancos),
            ],
            # Columna 2 (x=295)
            [
                ("Moneda", "moneda.png", self.abrir_moneda),
                ("Impuestos", "impuesto.png", self.abrir_impuestos),
                ("Configurar\nStock Minimo", "stockminimo.png", self.abrir_stock_minimo),
                ("Baja de\nProductos", "bajaproducto.png", self.abrir_bajas_productos),
                ("Cliente por\nDefecto", "clientes.png", self.abrir_cliente_defecto),
                ("Combos", "combos.png", self.abrir_combos),
            ],
            # Columna 3 (x=565)
            [
                ("Editar Factura", "factura.png", self.abrir_factura_config),
                ("Descargar\nPlantilla", "plantilla.png", self.descargar_plantilla),
                ("Importar\nProductos", "excel.png", self.abrir_importar_productos),
                ("Promociones", "promociones.png", self.abrir_promociones),
                ("Generar\nCatálogo PDF", "pdf.png", self.abrir_catalogo_pdf),
                ("Generar\nEtiquetas", "etiqueta.png", self.abrir_etiquetas),
            ],
            # Columna 4 (x=835) - Base de datos
            [
                ("Copia de\nseguridad DB", "basedatos.png", self.backup_db),
                ("Restaurar DB", "actualizar1.png", self.restaurar_db),
                ("Eliminar\nregistros DB", "eliminar.png", self.limpiar_db),
                ("Rangos NCF\ntradicional", "factura.png", self.abrir_ncf_tradicional),
                ("Almacenes", "btninventario.png", self.abrir_almacenes),
                ("Numeración y\nFacturación Electrónica", "factura.png", self.abrir_numeracion_fiscal),
            ]
        ]

        x_col = 25
        for col in columnas:
            frame_col = tk.Frame(self, bg="#C6D9E3", highlightbackground="#B8C4CE", highlightthickness=1)
            frame_col.place(x=x_col, y=70, width=245, height=550)

            y_item = 10
            for txt, ico_file, cmd in col:
                ruta_i = self.rutas(f"icono/{ico_file}")
                if not os.path.exists(ruta_i):
                    ruta_i = self.rutas("icono/guardar.png")

                if os.path.exists(ruta_i):
                    img_i = Image.open(ruta_i).resize((32, 32), Image.Resampling.LANCZOS)
                    self.images[f"cfg_{txt}_{ico_file}"] = ImageTk.PhotoImage(img_i)
                    ico_btn = self.images[f"cfg_{txt}_{ico_file}"]
                else:
                    ico_btn = None

                btn_item = tk.Button(
                    frame_col,
                    text=f"  {txt}",
                    image=ico_btn,
                    compound=tk.LEFT,
                    font=("sans", 11, "bold"),
                    bg="#EBEFF2",
                    fg="#1E293B",
                    activebackground="#D5E0E8",
                    relief="raised",
                    bd=2,
                    anchor="w",
                    padx=12,
                    cursor="hand2",
                    command=cmd
                )
                btn_item.place(x=8, y=y_item, width=227, height=76)
                y_item += 86

            x_col += 270

    def abrir_numeracion_fiscal(self):
        from numeracion_fiscal_config import NumeracionFiscalConfig
        NumeracionFiscalConfig(self)

    def abrir_importar_productos(self):
        from importar_productos import ImportarProductosModal
        ImportarProductosModal(self)

    def descargar_plantilla(self):
        from importar_productos import ImportarProductosModal
        modal = ImportarProductosModal(self)
        modal.descargar_plantilla()
        modal.destroy()

    def abrir_impresora(self):
        from factura_config import FacturaConfig
        FacturaConfig(self)

    def abrir_empresa(self):
        from empresa_config import EmpresaConfig
        EmpresaConfig(self)

    def abrir_sucursales(self):
        from sucursales import Sucursales
        Sucursales(self)

    def abrir_categorias(self):
        from categorias import Categorias
        Categorias(self)

    def abrir_moneda(self):
        from moneda_config import MonedaConfig
        MonedaConfig(self)

    def abrir_impuestos(self):
        from impuestos_config import ImpuestosConfig
        ImpuestosConfig(self)

    def abrir_promociones(self):
        from promociones import Promociones
        Promociones(self)

    def abrir_bajas_productos(self):
        from bajas_productos import BajasProductos
        BajasProductos(self)

    def abrir_cliente_defecto(self):
        from cliente_defecto_modal import ClienteDefectoModal
        ClienteDefectoModal(self)

    def abrir_barcode(self):
        from gestor_codigos_barra import GestorCodigosBarra
        GestorCodigosBarra(self)

    def abrir_bancos(self):
        from gestion_banco import GestionBanco
        GestionBanco(self)

    def abrir_etiquetas(self):
        from gestor_etiquetas import GestorEtiquetas
        GestorEtiquetas(self)

    def abrir_stock_minimo(self):
        from stock_minimo_modal import StockMinimoModal
        StockMinimoModal(self)

    def abrir_baja_stock(self):
        from alerta_stock_bajo import AlertaStockBajo
        AlertaStockBajo(self)

    def abrir_clientes(self):
        from clientes import Clientes
        Clientes(self)

    def abrir_combos(self):
        from combos import Combos
        Combos(self)

    def abrir_factura_config(self):
        from factura_config import FacturaConfig
        FacturaConfig(self)

    def abrir_ncf_tradicional(self):
        from ncf_tradicional_config import NCFTradicionalConfig
        NCFTradicionalConfig(self)

    def abrir_almacenes(self):
        from almacenes import Almacenes
        Almacenes(self)

    def abrir_catalogo_pdf(self):
        from catalogo_pdf_modal import CatalogoPdfModal
        CatalogoPdfModal(self)

    def backup_db(self):
        import datetime
        os.makedirs("backups", exist_ok=True)
        ahora = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = os.path.abspath(os.path.join("backups", f"factra_db_backup_{ahora}.sql"))
        try:
            import db_conexion
            dsn = db_conexion.DSN
            if os.getenv("POS_ENV", "development").lower() == "production" and not dsn.get("password"):
                raise RuntimeError("Falta POS_DB_PASSWORD en el entorno de producción.")
            pg_dump = _herramienta_postgres("pg_dump")
            if not pg_dump:
                raise FileNotFoundError("pg_dump")
            subprocess.run([
                pg_dump, "-h", dsn["host"], "-p", str(dsn["port"]), "-U", dsn["user"],
                "-d", dsn["dbname"], "-F", "p", "-f", backup_path
            ], check=True, env={**os.environ, "PGPASSWORD": dsn["password"], "PGSSLMODE": dsn.get("sslmode", "prefer")}, capture_output=True, text=True)
            if not os.path.isfile(backup_path) or os.path.getsize(backup_path) < 256:
                raise RuntimeError("pg_dump terminó, pero el archivo generado está vacío o incompleto.")
            with open(backup_path, "r", encoding="utf-8", errors="replace") as respaldo:
                contenido = respaldo.read(4096)
            if "PostgreSQL database dump" not in contenido and "CREATE " not in contenido:
                raise RuntimeError("El archivo no tiene la estructura esperada de un respaldo PostgreSQL.")
            messagebox.showinfo("Copia de Seguridad Exitosa", f"Respaldo PostgreSQL guardado en:\n{backup_path}")
        except FileNotFoundError:
            messagebox.showerror("Respaldo no disponible", "No se encontró pg_dump. Instale las herramientas de PostgreSQL para crear respaldos.")
        except Exception as e:
            messagebox.showerror("Error de Respaldo", f"No se pudo crear la copia de seguridad: {e}")

    def restaurar_db(self):
        import shutil
        from tkinter import filedialog
        archivo = filedialog.askopenfilename(title="Seleccionar respaldo PostgreSQL", filetypes=[("Respaldo SQL", "*.sql"), ("Todos los archivos", "*.*")])
        if not archivo:
            return

        if messagebox.askyesno("Confirmar Restauración", f"¿Está seguro de que desea restaurar la base de datos desde:\n{archivo}?\n\nLos datos actuales serán reemplazados por los del archivo de respaldo."):
            try:
                if not os.path.isfile(archivo) or os.path.getsize(archivo) < 256:
                    raise ValueError("El archivo seleccionado está vacío o incompleto.")
                with open(archivo, "r", encoding="utf-8", errors="replace") as respaldo:
                    contenido = respaldo.read(4096)
                if "PostgreSQL database dump" not in contenido and "CREATE " not in contenido:
                    raise ValueError("El archivo no parece ser un respaldo SQL de PostgreSQL.")
                import db_conexion
                dsn = db_conexion.DSN
                if os.getenv("POS_ENV", "development").lower() == "production" and not dsn.get("password"):
                    raise RuntimeError("Falta POS_DB_PASSWORD en el entorno de producción.")
                psql = _herramienta_postgres("psql")
                if not psql:
                    raise FileNotFoundError("psql")
                subprocess.run([
                    psql, "-h", dsn["host"], "-p", str(dsn["port"]), "-U", dsn["user"],
                    "-d", dsn["dbname"], "-f", archivo
                ], check=True, env={**os.environ, "PGPASSWORD": dsn["password"], "PGSSLMODE": dsn.get("sslmode", "prefer")}, capture_output=True, text=True)
                messagebox.showinfo("Restauración Completada", "La base de datos PostgreSQL fue restaurada correctamente. Se recomienda reiniciar la aplicación.")
            except FileNotFoundError:
                messagebox.showerror("Restauración no disponible", "No se encontró psql. Instale las herramientas de PostgreSQL para restaurar respaldos.")
            except Exception as e:
                messagebox.showerror("Error al Restaurar", f"Error durante la restauración: {e}")

    def limpiar_db(self):
        if os.getenv("POS_ENV", "development").lower() == "production":
            messagebox.showwarning(
                "Operación bloqueada",
                "La eliminación masiva de ventas y movimientos está bloqueada en producción."
            )
            return
        if messagebox.askyesno("Depurar Registros", "¿Desea limpiar los registros de ventas, facturas y movimientos de prueba conservando todos los productos, categorías, proveedores y usuarios?"):
            try:
                self.servicio_configuracion.limpiar_registros_desarrollo()
                messagebox.showinfo("Éxito", "Registros de ventas y movimientos de prueba depurados correctamente.")
            except Exception as e:
                messagebox.showerror("Error", f"Error al limpiar registros: {e}")
