"""Ventana de activación local de Factra."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import tkinter as tk
from tkinter import messagebox


class VentanaLicencia(tk.Toplevel):
    """Puerta de acceso de licencia mostrada antes del login."""

    ANCHO = 620
    ALTO = 410
    NARANJA = "#ff9d16"
    AZUL = "#243f78"

    def __init__(self, parent, on_activated=None):
        super().__init__(parent)
        self.parent = parent
        self.on_activated = on_activated
        self.overrideredirect(True)
        self.resizable(False, False)
        self.configure(bg="white")
        self._centrar()
        self._construir()
        self.protocol("WM_DELETE_WINDOW", self._cancelar)
        self.after(120, self._enfocar)

    def _centrar(self):
        self.update_idletasks()
        pantalla_x = self.winfo_screenwidth()
        pantalla_y = self.winfo_screenheight()
        x = max(0, (pantalla_x - self.ANCHO) // 2)
        y = max(0, (pantalla_y - self.ALTO) // 2)
        self.geometry(f"{self.ANCHO}x{self.ALTO}+{x}+{y}")

    def _construir(self):
        izquierda = tk.Frame(self, bg=self.NARANJA, width=305, height=self.ALTO)
        izquierda.pack(side="left", fill="y")
        izquierda.pack_propagate(False)

        lienzo = tk.Canvas(izquierda, bg=self.NARANJA, highlightthickness=0)
        lienzo.place(x=0, y=0, relwidth=1, relheight=1)
        # Decoración de la referencia: nubes/ondas y un monitor POS simple.
        for x, y, radio in ((70, 42, 105), (165, 90, 115), (88, 190, 120), (180, 295, 110)):
            lienzo.create_oval(x - radio, y - radio, x + radio, y + radio,
                               fill="#ff9d16", outline="#ff9d16")
        lienzo.create_rectangle(95, 125, 223, 214, fill="#5ca8e8", outline="")
        for fila in range(2):
            for columna in range(3):
                lienzo.create_rectangle(95 + columna * 43, 125 + fila * 45,
                                        137 + columna * 43, 169 + fila * 45,
                                        fill="#4a98df", outline="#4a98df")
        lienzo.create_rectangle(224, 125, 278, 214, fill="#d6d7dc", outline="")
        for y in (143, 163, 183, 203):
            lienzo.create_rectangle(235, y, 250, y + 6, fill="#a2a4ad", outline="")
            lienzo.create_rectangle(258, y, 273, y + 6, fill="#a2a4ad", outline="")
        lienzo.create_rectangle(145, 214, 183, 250, fill="#82828c", outline="")
        lienzo.create_rectangle(105, 250, 225, 276, fill="#a8a8b0", outline="")
        lienzo.create_rectangle(123, 250, 207, 263, fill="#c4c4ca", outline="")
        lienzo.create_rectangle(58, 265, 105, 310, fill="#777883", outline="")
        lienzo.create_rectangle(68, 278, 95, 286, fill="#4f5059", outline="")
        lienzo.create_text(30, 348, text="POS", anchor="w", fill="white",
                           font=("Segoe UI", 30, "bold"))
        lienzo.create_text(30, 382, text="POINT OF SALE", anchor="w", fill="white",
                           font=("Segoe UI", 9, "bold"))
        lienzo.create_text(30, 397, text="SYSTEM32", anchor="w", fill="white",
                           font=("Segoe UI", 15, "bold"))

        derecha = tk.Frame(self, bg="#fcfcfd", width=315, height=self.ALTO,
                           highlightbackground="#7f7f86", highlightthickness=1)
        derecha.pack(side="right", fill="both", expand=True)
        derecha.pack_propagate(False)

        tk.Label(derecha, text="Se autoriza el uso de este software a:",
                 bg="#fcfcfd", fg="#3e3e48", font=("Segoe UI", 9, "bold"),
                 anchor="w").place(x=28, y=10, width=260)
        tk.Label(derecha, text="SISTEMA DE FACTURACIÓN FACTRA", bg="#fcfcfd",
                 fg="#3e3e48", font=("Segoe UI", 8), anchor="w").place(x=28, y=28, width=260)
        tk.Label(derecha, text="Bajo licencia de uso", bg="#fcfcfd", fg="#3e3e48",
                 font=("Segoe UI", 9, "bold"), anchor="w").place(x=28, y=58, width=260)
        tk.Label(derecha, text="C0070923-15-1500-3001575-3\nFACTRA POS",
                 bg="#fcfcfd", fg="#3e3e48", font=("Segoe UI", 8), justify="left",
                 anchor="w").place(x=28, y=77, width=260, height=35)

        tk.Label(derecha, text="Ingrese la clave de acceso", bg="#fcfcfd",
                 fg="#626270", font=("Segoe UI", 11), anchor="w").place(x=28, y=178, width=245)
        self.clave = tk.Entry(derecha, bg="#e5e5ea", fg="#30303a", relief="flat",
                              font=("Segoe UI", 12), insertbackground="#30303a")
        self.clave.place(x=28, y=198, width=195, height=27)
        tk.Button(derecha, text="×", command=lambda: self.clave.delete(0, tk.END),
                  bg="#d8473e", fg="white", activebackground="#b93630",
                  relief="flat", bd=0, font=("Segoe UI", 12, "bold"),
                  cursor="hand2").place(x=223, y=198, width=37, height=27)
        tk.Button(derecha, text="ACTIVAR", command=self._activar, bg=self.AZUL,
                  fg="white", activebackground="#315696", relief="flat", bd=0,
                  font=("Segoe UI", 9, "bold"), cursor="hand2").place(x=28, y=244, width=232, height=32)
        self.clave.bind("<Return>", lambda _evento: self._activar())
        tk.Label(derecha, text="Versión 1.0\nCopyright © 2026 - Factra",
                 bg="#fcfcfd", fg="#777783", font=("Segoe UI", 8),
                 justify="right", anchor="e").place(x=120, y=365, width=140)

    def _enfocar(self):
        if self.winfo_exists():
            self.lift()
            self.focus_force()
            self.clave.focus_force()

    @staticmethod
    def _archivo_licencia():
        return Path(os.path.abspath(".factra_license"))

    def _clave_valida(self, clave):
        esperada = os.getenv("POS_LICENSE_KEY", "FACTRA-DEMO").strip()
        return bool(clave) and hashlib.sha256(clave.encode("utf-8")).hexdigest() == hashlib.sha256(esperada.encode("utf-8")).hexdigest()

    def _activar(self):
        clave = self.clave.get().strip()
        if not self._clave_valida(clave):
            messagebox.showerror("Licencia", "La clave de acceso no es válida.", parent=self)
            self.clave.focus_force()
            return
        try:
            self._archivo_licencia().write_text(json.dumps({"activa": True}), encoding="utf-8")
        except OSError:
            pass
        if callable(self.on_activated):
            self.on_activated()
        self.destroy()

    def _cancelar(self):
        if messagebox.askyesno("Salir", "¿Desea cerrar Factra?", parent=self):
            self.parent.destroy()
