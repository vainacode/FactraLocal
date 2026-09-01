import tkinter as tk

def posicionar_ventana(window, width, height, parent=None):
    """
    Posiciona y centra una ventana de Tkinter:
    - Si se proporciona 'parent', posiciona la ventana sobre la ventana padre:
      - Si tiene el mismo tamaño o mayor que el padre (ej. módulos de 1100x650),
        se superpone exactamente en las coordenadas (x, y) del marco de la ventana padre para cubrirla por completo.
      - Si es más pequeña (como un modal o diálogo secundario), se centra directamente
        sobre el área visible de la ventana padre.
    - Si no se proporciona 'parent', centra la ventana 'mitad a mitad' en la pantalla del monitor.
    - Asegura que la nueva ventana quede al frente y con el foco activo.
    """
    try:
        window.update_idletasks()
    except Exception:
        pass
    
    colocado = False
    if parent is not None:
        try:
            top_parent = parent.winfo_toplevel() if hasattr(parent, 'winfo_toplevel') else parent
            top_parent.update_idletasks()
            pw = top_parent.winfo_width()
            ph = top_parent.winfo_height()
            px = top_parent.winfo_rootx()
            py = top_parent.winfo_rooty()
            wx = top_parent.winfo_x()
            wy = top_parent.winfo_y()
            
            if pw > 100 and ph > 100:
                if width >= pw and height >= ph:
                    # Cubrir exactamente la ventana de atrás píxel a píxel
                    x = wx if wx >= 0 else px
                    y = wy if wy >= 0 else py
                else:
                    # Centrar el modal sobre la ventana padre
                    x = px + max(0, (pw - width) // 2)
                    y = py + max(0, (ph - height) // 2)
                
                window.geometry(f"{width}x{height}+{x}+{y}")
                colocado = True
        except Exception:
            pass
            
    if not colocado:
        # Centrar 'mitad a mitad' en la pantalla
        try:
            sw = window.winfo_screenwidth()
            sh = window.winfo_screenheight()
            x = max(0, (sw - width) // 2)
            y = max(0, (sh - height) // 2)
            window.geometry(f"{width}x{height}+{x}+{y}")
        except Exception:
            window.geometry(f"{width}x{height}")

    try:
        window.lift()
        window.focus_force()
    except Exception:
        pass
