"""Generación de documentos de venta con una identidad visual común."""
import html
import os
import db_conexion as sqlite3
import webbrowser
import tkinter as tk
from datetime import datetime


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SALIDA_DIR = os.path.join(BASE_DIR, "documentos_emitidos")


def dialogo_documento(parent, titulo, mensaje, ruta=None, error=False):
    """Diálogo visual propio para documentos, sin avisos estándar del sistema."""
    dialog = tk.Toplevel(parent)
    dialog.overrideredirect(True)
    dialog.geometry("520x285")
    dialog.resizable(False, False)
    dialog.configure(bg="#F1F5F8")
    dialog.transient(parent)
    dialog.grab_set()
    dialog.update_idletasks()
    parent.update_idletasks()
    x = parent.winfo_rootx() + max(0, (parent.winfo_width() - dialog.winfo_width()) // 2)
    y = parent.winfo_rooty() + max(0, (parent.winfo_height() - dialog.winfo_height()) // 2)
    dialog.geometry(f"520x285+{x}+{y}")
    color = "#B42318" if error else "#0E5A45"
    fondo = "#FCE8E6" if error else "#E3F0EC"
    tk.Frame(dialog, bg=color, height=7).pack(fill="x")
    tk.Label(dialog, text="!" if error else "✓", font=("Segoe UI", 27, "bold"), fg="white", bg=color, width=3).pack(pady=(18, 7))
    tk.Label(dialog, text=titulo, font=("Segoe UI", 16, "bold"), fg="#1A1F2B", bg="#F1F5F8").pack()
    tk.Label(dialog, text=mensaje, font=("Segoe UI", 10), fg="#4A5266", bg="#F1F5F8", justify="center", wraplength=455).pack(pady=(8, 10))
    if ruta:
        tk.Label(dialog, text=os.path.basename(ruta), font=("Consolas", 9), fg=color, bg=fondo, padx=12, pady=7).pack(fill="x", padx=28, pady=(0, 13))
    botones = tk.Frame(dialog, bg="#F1F5F8")
    botones.pack()
    if ruta and not error:
        tk.Button(botones, text="Abrir documento", font=("Segoe UI", 10, "bold"), bg=color, fg="white", activebackground="#084936", activeforeground="white", bd=0, padx=17, pady=8, cursor="hand2", command=lambda: webbrowser.open("file:///" + ruta.replace(os.sep, "/"))).pack(side="left", padx=5)
    tk.Button(botones, text="Cerrar", font=("Segoe UI", 10, "bold"), bg="white", fg="#1A1F2B", activebackground="#E4EAF0", bd=1, padx=20, pady=7, cursor="hand2", command=dialog.destroy).pack(side="left", padx=5)
    dialog.protocol("WM_DELETE_WINDOW", dialog.destroy)
    return dialog


def _esc(value):
    return html.escape(str(value or ""))


def _money(value):
    return f"RD$ {float(value or 0):,.2f}"


def _empresa(db_name="database.db"):
    fallback = {"nombre": "", "direccion": "", "telefono": "", "email": "", "website": "", "rnc": ""}
    try:
        with sqlite3.connect(os.path.join(BASE_DIR, db_name)) as conn:
            row = conn.execute("SELECT nombre, direccion, telefono, email, website, numero_id, nit FROM empresa LIMIT 1").fetchone()
            if row:
                fallback.update(dict(zip(("nombre", "direccion", "telefono", "email", "website", "rnc", "nit"), row)))
    except sqlite3.Error:
        pass
    return fallback


def cargar_factura(factura_id, db_name="database.db"):
    with sqlite3.connect(os.path.join(BASE_DIR, db_name)) as conn:
        rows = conn.execute(
            "SELECT factura, cliente, producto, precio, cantidad, total, fecha, hora, cajero, medio_pago "
            "FROM ventas WHERE factura=? "
            "UNION ALL "
            "SELECT factura, cliente, producto, precio, cantidad, total, fecha_creacion, hora_creacion, cajero, "
            "COALESCE(medio_pago, 'Crédito') FROM facturas_pendientes "
            "WHERE factura=? AND estado IN ('Crédito', 'Pagada') "
            "ORDER BY 1", (factura_id, factura_id)
        ).fetchall()
        comprobante = conn.execute(
            "SELECT e_ncf, tipo_ecf, estado_actual FROM comprobantes_fiscales "
            "WHERE factura_local=? AND factrapi_comprobante_id IS NOT NULL "
            "ORDER BY fecha_creacion DESC LIMIT 1", (factura_id,)
        ).fetchone()
    if not rows:
        raise ValueError(f"No existe la factura #{factura_id}.")
    return {
        "numero": rows[0][0], "cliente": rows[0][1], "cajero": rows[0][8] or "",
        "medio": rows[0][9] or "Efectivo", "fecha": rows[0][6], "hora": rows[0][7],
        "items": [{"producto": r[2], "precio": r[3], "cantidad": r[4], "total": r[5]} for r in rows],
        "e_ncf": comprobante[0] if comprobante else None,
        "estado_ecf": comprobante[2] if comprobante else None,
        "tipo_ecf": comprobante[1] if comprobante else None,
    }


def generar_factura(factura_id, formato="A4", db_name="database.db", abrir=False):
    """Genera un HTML listo para imprimir y lo abre en el navegador predeterminado."""
    empresa = _empresa(db_name)
    factura = cargar_factura(factura_id, db_name)
    subtotal = sum(float(i["total"] or 0) for i in factura["items"])
    impuesto = 0.0
    total = subtotal + impuesto
    filas = "".join(
        f"<tr><td class='center'>{_esc(i['cantidad'])}</td><td>{_esc(i['producto'])}</td>"
        f"<td class='num'>{_money(i['precio'])}</td><td class='num'>{_money(i['total'])}</td></tr>"
        for i in factura["items"]
    ) or "<tr><td colspan='4' class='empty'>No hay artículos registrados para esta factura.</td></tr>"
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    ticket = formato.lower() in ("80mm", "50mm", "ticket")
    width = "80mm" if formato.lower() != "50mm" else "50mm"
    body = f"""<!doctype html><html lang='es'><head><meta charset='utf-8'><title>Factura {_esc(factura['numero'])}</title>
<style>
:root{{--ink:#1a1f2b;--soft:#4a5266;--line:#d8dde6;--brand:#0e5a45;--brand-soft:#e3f0ec;--gold:#b8860b;--paper:#fff}}
*{{box-sizing:border-box}}body{{margin:0;background:#eef0f4;color:var(--ink);font-family:'Segoe UI',Arial,sans-serif}}
.sheet{{background:var(--paper);margin:28px auto;padding:34px;max-width:820px;box-shadow:0 4px 24px #1419282e;font-size:13px;line-height:1.45}}
.head{{display:flex;justify-content:space-between;gap:20px;border-bottom:3px solid var(--ink);padding-bottom:16px}}
.brand{{font-size:25px;font-weight:800;color:var(--brand);letter-spacing:.5px}}.brand span{{color:var(--gold)}}
.muted{{color:var(--soft);font-size:12px}}.ncf{{border:1.5px solid var(--ink);border-radius:8px;min-width:245px;text-align:center;overflow:hidden}}
.ncf b{{display:block;background:var(--ink);color:#fff;padding:8px;font-size:12px}}.ncf strong{{display:block;padding:10px 8px 2px;font:700 18px 'Courier New'}}.ncf small{{display:block;padding:0 8px 10px;color:var(--soft)}}
.grid{{display:grid;grid-template-columns:1fr 1fr;gap:14px;margin:16px 0}}.panel{{border:1px solid var(--line);border-radius:6px;overflow:hidden}}.panel h3{{margin:0;background:#f2f4f8;padding:7px 11px;font-size:10px;text-transform:uppercase;letter-spacing:.8px;color:var(--soft)}}.rows{{padding:9px 11px}}.row{{padding:2px 0}}.row b{{display:inline-block;width:92px;color:var(--soft)}}
table{{width:100%;border-collapse:collapse;margin-top:4px}}th{{background:var(--ink);color:#fff;padding:9px;text-align:left;font-size:11px;text-transform:uppercase;letter-spacing:.4px}}td{{padding:9px;border-bottom:1px solid var(--line);font-size:12px}}tr:nth-child(even){{background:#fafbfd}}.center{{text-align:center}}.num{{text-align:right}}.empty{{text-align:center;color:var(--soft);padding:28px}}
.bottom{{display:flex;justify-content:space-between;gap:22px;margin-top:18px}}.note{{flex:1;color:var(--soft);font-size:11px}}.totals{{min-width:260px}}.total-row{{display:flex;justify-content:space-between;padding:6px 10px;border-bottom:1px solid var(--line)}}.grand{{background:var(--brand);color:#fff;border-radius:6px;font-size:16px;font-weight:800;margin-top:6px;padding:10px}}
.seal{{border-top:1.5px dashed var(--line);margin-top:22px;padding-top:15px;display:flex;gap:18px;align-items:center}}.qr{{height:78px;width:78px;border:7px solid #111;background:repeating-linear-gradient(45deg,#111 0 3px,#fff 3px 7px)}}.code{{font:700 15px 'Courier New';letter-spacing:1.5px}}footer{{margin-top:24px;padding-top:7px;border-top:1px solid var(--line);text-align:center;color:#8a93a3;font-size:10px}}
@media print{{body{{background:#fff}}.sheet{{margin:0;box-shadow:none;max-width:none}}}}
.ticket{{width:{width};padding:16px 12px;font-family:'Courier New',monospace;font-size:11px;line-height:1.35}}.ticket .head{{display:block;text-align:center;border-bottom:0}}.ticket .brand{{font-size:18px}}.ticket .ncf{{min-width:0;margin-top:10px}}.ticket .grid{{display:block;margin:12px 0}}.ticket .panel{{border:0;border-radius:0;border-top:1px dashed #000}}.ticket .panel h3{{background:none;padding:5px 0;color:#000}}.ticket .rows{{padding:3px 0}}.ticket table th{{background:#fff;color:#000;border-bottom:1px solid #000;padding:4px 0}}.ticket td{{padding:4px 0}}.ticket .bottom{{display:block}}.ticket .totals{{margin-top:14px}}.ticket .seal{{justify-content:center;text-align:center}}.ticket footer{{font-size:9px}}
</style></head><body><main class='sheet {'ticket' if ticket else ''}'>
<section class='head'><div><div class='brand'>{_esc(empresa['nombre'])}</div><div class='muted'><b>RNC: {_esc(empresa['rnc'])}</b></div><div class='muted'>{_esc(empresa['direccion'])}</div><div class='muted'>{_esc(empresa['telefono'])} · {_esc(empresa['email'])}</div></div>
<div class='ncf'><b>{'COMPROBANTE FISCAL ELECTRÓNICO' if factura['e_ncf'] else 'FACTURA DE VENTA'}</b><strong>{_esc(factura['e_ncf'] or ('Pendiente de emisión' if factura['estado_ecf'] else 'Sin NCF electrónico'))}</strong><small>Factura local No. {_esc(factura['numero'])}</small></div></section>
<section class='grid'><div class='panel'><h3>Cliente</h3><div class='rows'><div class='row'><b>Nombre:</b>{_esc(factura['cliente'])}</div><div class='row'><b>Condición:</b>{_esc(factura['medio'])}</div></div></div><div class='panel'><h3>Información</h3><div class='rows'><div class='row'><b>Fecha:</b>{_esc(factura['fecha'])}</div><div class='row'><b>Cajero:</b>{_esc(factura['cajero'])}</div><div class='row'><b>Pago:</b>{_esc(factura['medio'])}</div></div></div></section>
<table><thead><tr><th style='width:58px'>Cant.</th><th>Descripción</th><th class='num' style='width:125px'>Precio unit.</th><th class='num' style='width:125px'>Importe</th></tr></thead><tbody>{filas}</tbody></table>
<section class='bottom'><div class='note'><div class='panel'><h3>Observaciones</h3><div class='rows'>Documento emitido por {_esc(empresa['nombre'])}. Conserve esta factura para cualquier reclamación o garantía.</div></div><p>Verifique los datos del comprobante antes de retirarse.</p></div><div class='totals'><div class='total-row'><span>Subtotal</span><span>{_money(subtotal)}</span></div><div class='total-row'><span>ITBIS</span><span>{_money(impuesto)}</span></div><div class='total-row grand'><span>TOTAL</span><span>{_money(total)}</span></div></div></section>
<section class='seal'><div class='qr'></div><div><div class='muted'>ESTADO FISCAL</div><div class='code'>{_esc(factura['estado_ecf'] or 'No aplica')}</div><div class='muted'>{_esc(factura['e_ncf'] or ('Sin e-NCF asignado todavía' if factura['estado_ecf'] else 'Documento informal'))}</div></div></section><footer>{_esc(empresa['nombre'])} · RNC {_esc(empresa['rnc'])} · {'Comprobante Fiscal Electrónico' if factura['e_ncf'] else 'Documento de venta'}</footer></main></body></html>"""
    os.makedirs(SALIDA_DIR, exist_ok=True)
    formato_salida = "50mm" if formato.lower() == "50mm" else ("80mm" if ticket else "a4")
    path = os.path.join(SALIDA_DIR, f"factura_{factura_id}_{stamp}_{formato_salida}.html")
    with open(path, "w", encoding="utf-8") as file:
        file.write(body)
    if abrir:
        webbrowser.open("file:///" + path.replace(os.sep, "/"))
    return path
