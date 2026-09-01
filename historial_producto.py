import csv
import datetime
import os
import db_conexion as sqlite3
import sys
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageTk
from window_utils import posicionar_ventana

class HistorialProducto(tk.Toplevel):
    def __init__(self, parent, producto_nombre=None):
        super().__init__(parent)
        self.parent = parent
        self.title("Historial de Producto")
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
        self.producto_actual = producto_nombre or ""
        self.movimientos = []

        self.widgets()
        self.cargar_productos_combo()
        self.cargar_historial()

    def rutas(self, ruta):
        try:
            rutabase = sys.__MEIPASS
        except Exception:
            rutabase = os.path.abspath(".")
        return os.path.join(rutabase, ruta)

    def widgets(self):
#============== 1. HEADER ==========================================================================#
        ruta_hist_ico = self.rutas("icono/historialprecios.png")
        if not os.path.exists(ruta_hist_ico):
            ruta_hist_ico = self.rutas("icono/historial.png")

        if os.path.exists(ruta_hist_ico):
            img_h = Image.open(ruta_hist_ico).resize((42, 42), Image.Resampling.LANCZOS)
            self.images["hist_title"] = ImageTk.PhotoImage(img_h)
            lbl_ico = tk.Label(self, image=self.images["hist_title"], bg="#C6D9E3")
            lbl_ico.place(x=20, y=12)

        lbl_title = tk.Label(
            self,
            text="Historial de Producto",
            font=("sans", 20, "bold"),
            bg="#C6D9E3",
            fg="#1E293B"
        )
        lbl_title.place(x=70, y=10)

        self.lbl_subtitle = tk.Label(
            self,
            text=f"Producto: {self.producto_actual}",
            font=("sans", 11, "italic"),
            bg="#C6D9E3",
            fg="#2563EB"
        )
        self.lbl_subtitle.place(x=72, y=40)

#============== 2. SELECCIÓN DE PRODUCTO ===========================================================#
        frame_sel = tk.LabelFrame(
            self,
            text="Seleccionar Producto",
            font=("sans", 11, "bold"),
            bg="#C6D9E3",
            fg="#1E293B",
            padx=10,
            pady=4
        )
        frame_sel.place(x=20, y=70, width=940, height=65)

        lbl_p = tk.Label(frame_sel, text="Producto:", font=("sans", 11, "bold"), bg="#C6D9E3", fg="#1E293B")
        lbl_p.place(x=10, y=5)

        self.cmb_producto = ttk.Combobox(frame_sel, font=("sans", 11))
        self.cmb_producto.place(x=95, y=4, width=775, height=28)
        self.cmb_producto.bind("<<ComboboxSelected>>", self.al_cambiar_producto)

        ruta_reload = self.rutas("icono/actualizar1.png")
        if not os.path.exists(ruta_reload):
            ruta_reload = self.rutas("icono/actualizar.png")

        if os.path.exists(ruta_reload):
            img_rel = Image.open(ruta_reload).resize((22, 22), Image.Resampling.LANCZOS)
            self.images["btn_rel"] = ImageTk.PhotoImage(img_rel)
            btn_rel = tk.Button(
                frame_sel,
                image=self.images["btn_rel"],
                bg="#EBEFF2",
                relief="raised",
                bd=1,
                cursor="hand2",
                command=self.cargar_historial
            )
            btn_rel.place(x=880, y=4, width=32, height=28)

#============== 3. RESUMEN DE ESTADÍSTICAS (3 TARJETAS) =============================================#
        # Tarjeta 1: Total Movimientos
        card1 = tk.Frame(self, bg="#DDE1E5", highlightbackground="#B8C4CE", highlightthickness=1)
        card1.place(x=20, y=145, width=300, height=70)

        tk.Label(card1, text="TOTAL MOVIMIENTOS", font=("sans", 8, "bold"), bg="#DDE1E5", fg="#64748B").place(x=12, y=8)
        self.lbl_card_tot = tk.Label(card1, text="0", font=("sans", 20, "bold"), bg="#DDE1E5", fg="#1E293B")
        self.lbl_card_tot.place(x=12, y=28)

        # Tarjeta 2: Último Cambio Precio
        card2 = tk.Frame(self, bg="#DDE1E5", highlightbackground="#B8C4CE", highlightthickness=1)
        card2.place(x=340, y=145, width=300, height=70)

        tk.Label(card2, text="ÚLTIMO CAMBIO PRECIO", font=("sans", 8, "bold"), bg="#DDE1E5", fg="#64748B").place(x=12, y=8)
        self.lbl_card_pre = tk.Label(card2, text="Sin cambios", font=("sans", 13, "bold"), bg="#DDE1E5", fg="#1E293B")
        self.lbl_card_pre.place(x=12, y=32)

        # Tarjeta 3: Último Cambio Stock
        card3 = tk.Frame(self, bg="#DDE1E5", highlightbackground="#B8C4CE", highlightthickness=1)
        card3.place(x=660, y=145, width=300, height=70)

        tk.Label(card3, text="ÚLTIMO CAMBIO STOCK", font=("sans", 8, "bold"), bg="#DDE1E5", fg="#64748B").place(x=12, y=8)
        self.lbl_card_stk = tk.Label(card3, text="Sin cambios", font=("sans", 13, "bold"), bg="#DDE1E5", fg="#1E293B")
        self.lbl_card_stk.place(x=12, y=32)

#============== 4. BARRA DE FILTRO Y CONTEO ========================================================#
        lbl_mot = tk.Label(self, text="Filtrar por motivo:", font=("sans", 10, "bold"), bg="#C6D9E3", fg="#1E293B")
        lbl_mot.place(x=25, y=228)

        self.cmb_motivo = ttk.Combobox(self, values=["Todos", "Venta", "Compra", "Ajuste manual", "Registro inicial"], font=("sans", 10), state="readonly")
        self.cmb_motivo.current(0)
        self.cmb_motivo.place(x=155, y=226, width=190, height=26)
        self.cmb_motivo.bind("<<ComboboxSelected>>", lambda e: self.filtrar_por_motivo())

        self.lbl_conteo = tk.Label(self, text="Mostrando 0 de 0 registros", font=("sans", 9, "bold"), bg="#C6D9E3", fg="#475569")
        self.lbl_conteo.place(x=790, y=228)

#============== 5. TABLA DE HISTORIAL ===============================================================#
        style = ttk.Style()
        style.configure("Historial.Treeview.Heading", font=("sans", 8, "bold"), background="#E0E6ED")
        style.configure("Historial.Treeview", font=("sans", 8), rowheight=24)

        columnas = ("id", "fecha", "hora", "pre_ant", "pre_nvo", "cos_ant", "cos_nvo", "stk_ant", "stk_nvo", "prov_ant", "prov_nvo", "usuario")
        self.tabla = ttk.Treeview(self, columns=columnas, show="headings", style="Historial.Treeview")
        self.tabla.place(x=20, y=260, width=940, height=260)

        titulos = [
            ("id", "ID", 35),
            ("fecha", "Fecha", 85),
            ("hora", "Hora", 70),
            ("pre_ant", "Precio Ant.", 80),
            ("pre_nvo", "Precio Nvo.", 80),
            ("cos_ant", "Costo Ant.", 80),
            ("cos_nvo", "Costo Nvo.", 80),
            ("stk_ant", "Stock Ant.", 65),
            ("stk_nvo", "Stock Nvo.", 65),
            ("prov_ant", "Prov. Ant.", 100),
            ("prov_nvo", "Prov. Nvo.", 100),
            ("usuario", "Usuario", 70),
        ]

        for col, txt, w in titulos:
            self.tabla.heading(col, text=txt, anchor="center")
            self.tabla.column(col, width=w, anchor="center")

        scroll_y = ttk.Scrollbar(self, orient="vertical", command=self.tabla.yview)
        self.tabla.configure(yscrollcommand=scroll_y.set)
        scroll_y.place(x=950, y=260, height=260)

#============== 6. BOTONES INFERIORES ===============================================================#
        # Refrescar
        if "btn_rel" in self.images:
            btn_ref = tk.Button(self, text="  Refrescar", image=self.images["btn_rel"], compound=tk.LEFT, font=("sans", 10, "bold"), bg="#EBEFF2", fg="#1E293B", relief="raised", bd=2, cursor="hand2", command=self.cargar_historial)
            btn_ref.place(x=20, y=540, width=120, height=38)

        # Exportar
        ruta_ex = self.rutas("icono/excel.png")
        if os.path.exists(ruta_ex):
            self.images["excel_h"] = ImageTk.PhotoImage(Image.open(ruta_ex).resize((20, 20), Image.Resampling.LANCZOS))
            btn_ex = tk.Button(self, text="  Exportar", image=self.images["excel_h"], compound=tk.LEFT, font=("sans", 10, "bold"), bg="#EBEFF2", fg="#1E293B", relief="raised", bd=2, cursor="hand2", command=self.exportar_excel)
            btn_ex.place(x=390, y=540, width=120, height=38)

        # Exportar PDF
        ruta_pdf = self.rutas("icono/pdf.png")
        if os.path.exists(ruta_pdf):
            self.images["pdf_h"] = ImageTk.PhotoImage(Image.open(ruta_pdf).resize((20, 20), Image.Resampling.LANCZOS))
            btn_pdf = tk.Button(self, text="  Exportar PDF", image=self.images["pdf_h"], compound=tk.LEFT, font=("sans", 10, "bold"), bg="#EBEFF2", fg="#1E293B", relief="raised", bd=2, cursor="hand2", command=self.exportar_pdf)
            btn_pdf.place(x=525, y=540, width=135, height=38)

        # Cerrar
        ruta_close = self.rutas("icono/cancelar.png")
        if os.path.exists(ruta_close):
            self.images["close_h"] = ImageTk.PhotoImage(Image.open(ruta_close).resize((20, 20), Image.Resampling.LANCZOS))
            btn_close = tk.Button(self, text="  Cerrar", image=self.images["close_h"], compound=tk.LEFT, font=("sans", 10, "bold"), bg="#EBEFF2", fg="#1E293B", relief="raised", bd=2, cursor="hand2", command=self.destroy)
            btn_close.place(x=840, y=540, width=120, height=38)

    def cargar_productos_combo(self):
        try:
            with sqlite3.connect(self.db_name) as conn:
                cur = conn.cursor()
                cur.execute("SELECT nombre FROM inventario WHERE estado != 'Inactivo' OR estado IS NULL")
                prods = [r[0] for r in cur.fetchall()]
                if not prods:
                    prods = [self.producto_actual]
                self.cmb_producto["values"] = prods
                if self.producto_actual in prods:
                    self.cmb_producto.set(self.producto_actual)
                elif prods:
                    self.cmb_producto.current(0)
                    self.producto_actual = prods[0]
        except Exception as e:
            print("Error cargando productos:", e)

    def al_cambiar_producto(self, event=None):
        self.producto_actual = self.cmb_producto.get()
        self.lbl_subtitle.config(text=f"Producto: {self.producto_actual}")
        self.cargar_historial()

    def cargar_historial(self):
        for r in self.tabla.get_children():
            self.tabla.delete(r)

        # Cargar únicamente el historial persistido del producto.
        self.movimientos = []
        try:
            with sqlite3.connect(self.db_name) as conn:
                cur = conn.cursor()
                cur.execute("SELECT * FROM historial_precios WHERE nombre_producto = ?", (self.producto_actual,))
                rows = cur.fetchall()

                if rows:
                    for r in rows:
                        self.movimientos.append((
                            r[0], r[9], r[10], f"$ {r[3]:,.2f}", f"$ {r[4]:,.2f}",
                            f"$ {r[5]:,.2f}", f"$ {r[6]:,.2f}", r[7], r[8],
                            "-", "-", r[11] or ""
                        ))
        except Exception:
            pass

        for m in self.movimientos:
            self.tabla.insert("", tk.END, values=m)

        self.lbl_card_tot.config(text=str(len(self.movimientos)))
        if self.movimientos:
            p_nvo = self.movimientos[0][4]
            p_ant = self.movimientos[0][3]
            s_nvo = self.movimientos[0][8]
            s_ant = self.movimientos[0][7]
            self.lbl_card_pre.config(text=f"{p_ant} → {p_nvo} =")
            self.lbl_card_stk.config(text=f"{s_ant} → {s_nvo} =")
        else:
            self.lbl_card_pre.config(text="Sin cambios")
            self.lbl_card_stk.config(text="Sin cambios")
        self.lbl_conteo.config(text=f"Mostrando {len(self.movimientos)} de {len(self.movimientos)} registros")

    def filtrar_por_motivo(self):
        mot = self.cmb_motivo.get()
        if mot == "Todos":
            self.cargar_historial()
        else:
            self.cargar_historial()

    def exportar_excel(self):
        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("Archivo CSV", "*.csv")],
            initialfile=f"Historial_{self.producto_actual.replace(' ', '_')}.csv"
        )
        if file_path:
            try:
                with open(file_path, mode="w", newline="", encoding="utf-8-sig") as f:
                    w = csv.writer(f)
                    w.writerow(["ID", "Fecha", "Hora", "Precio Ant.", "Precio Nvo.", "Costo Ant.", "Costo Nvo.", "Stock Ant.", "Stock Nvo.", "Prov. Ant.", "Prov. Nvo.", "Usuario"])
                    for m in self.movimientos:
                        w.writerow(m)
                messagebox.showinfo("Exportar", "Historial exportado correctamente a CSV.")
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo exportar: {e}")

    def exportar_pdf(self):
        destino = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("Documento PDF", "*.pdf")],
            initialfile=f"Historial_{self.producto_actual.replace(' ', '_')}.pdf",
        )
        if not destino:
            return
        try:
            from reportlab.lib.pagesizes import landscape, letter
            from reportlab.pdfgen import canvas
            pagina = landscape(letter)
            pdf = canvas.Canvas(destino, pagesize=pagina)
            ancho, alto = pagina
            pdf.setFont("Helvetica-Bold", 14)
            pdf.drawString(36, alto - 36, f"Historial de producto: {self.producto_actual}")
            pdf.setFont("Helvetica", 8)
            y = alto - 60
            encabezados = ["ID", "Fecha", "Hora", "Precio ant.", "Precio nuevo", "Costo ant.", "Costo nuevo", "Stock ant.", "Stock nuevo", "Usuario"]
            posiciones = [36, 65, 135, 190, 260, 335, 405, 480, 545, 620]
            pdf.setFont("Helvetica-Bold", 8)
            for x, titulo in zip(posiciones, encabezados):
                pdf.drawString(x, y, titulo)
            y -= 14
            pdf.setFont("Helvetica", 8)
            for fila in self.movimientos:
                valores = [fila[0], fila[1], fila[2], fila[3], fila[4], fila[5], fila[6], fila[7], fila[8], fila[11]]
                for x, valor in zip(posiciones, valores):
                    pdf.drawString(x, y, str(valor or "")[:18])
                y -= 12
                if y < 30:
                    pdf.showPage()
                    y = alto - 36
            pdf.save()
            messagebox.showinfo("Exportar PDF", f"Historial exportado en:\n{destino}")
        except ImportError:
            messagebox.showerror("PDF no disponible", "Instale la dependencia reportlab para generar documentos PDF.")
        except Exception as error:
            messagebox.showerror("Error", f"No se pudo generar el PDF: {error}")
