import tkinter as tk


def mostrar_dialogo(parent, titulo, mensaje, tipo="info"):
    """Muestra un aviso modal con el estilo propio de la aplicación."""
    colores = {
        "info": ("#0E5A45", "#E3F0EC", "✓"),
        "error": ("#B42318", "#FCE8E6", "!"),
        "warning": ("#9A6700", "#FFF4CE", "⚠"),
    }
    color, fondo_icono, icono = colores.get(tipo, colores["info"])
    dialog = tk.Toplevel(parent)
    dialog.overrideredirect(True)
    dialog.geometry("430x235")
    dialog.resizable(False, False)
    dialog.configure(bg="#F1F5F8")
    dialog.transient(parent)
    dialog.grab_set()
    dialog.focus_force()
    dialog.lift()
    dialog.attributes("-topmost", True)
    dialog.update_idletasks()
    parent.update_idletasks()
    x = parent.winfo_rootx() + max(0, (parent.winfo_width() - dialog.winfo_width()) // 2)
    y = parent.winfo_rooty() + max(0, (parent.winfo_height() - dialog.winfo_height()) // 2)
    dialog.geometry(f"430x235+{x}+{y}")
    dialog.after(250, lambda: dialog.attributes("-topmost", False) if dialog.winfo_exists() else None)

    def cerrar_dialogo(event=None):
        """Libera el grab modal antes de cerrar para no bloquear la ventana principal."""
        if not dialog.winfo_exists():
            return
        try:
            if dialog.grab_current() == str(dialog):
                dialog.grab_release()
        except tk.TclError:
            # El diálogo puede estar cerrándose al mismo tiempo que se procesa
            # otro evento del sistema.
            pass
        dialog.destroy()
        try:
            parent.focus_force()
        except tk.TclError:
            pass

    tk.Frame(dialog, bg=color, height=7).pack(fill="x")
    tk.Label(dialog, text=icono, font=("Segoe UI", 26, "bold"), fg=color,
             bg=fondo_icono, width=3, height=1).pack(pady=(18, 9))
    tk.Label(dialog, text=titulo, font=("Segoe UI", 15, "bold"),
             fg="#1A1F2B", bg="#F1F5F8").pack()
    tk.Label(dialog, text=mensaje, font=("Segoe UI", 10), fg="#4A5266",
             bg="#F1F5F8", justify="center", wraplength=370).pack(pady=(9, 17))
    tk.Button(dialog, text="Continuar", font=("Segoe UI", 10, "bold"),
              bg=color, fg="white", activebackground=color, activeforeground="white",
              relief="flat", bd=0, padx=25, pady=7, cursor="hand2",
              command=cerrar_dialogo).pack()
    dialog.bind("<Return>", cerrar_dialogo)
    dialog.bind("<Escape>", cerrar_dialogo)
    dialog.protocol("WM_DELETE_WINDOW", cerrar_dialogo)
    return dialog
