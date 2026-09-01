import tkinter as tk
from tkinter import messagebox, ttk

from permisos import MODULOS, ROLES, obtener_permisos, guardar_permisos
from window_utils import posicionar_ventana


class RolesPermisos(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.title("Roles y Permisos")
        posicionar_ventana(self, 520, 520, parent)
        self.resizable(False, False)
        self.configure(bg="#DDE1E5")
        self.transient(parent)
        self.grab_set()
        self.variables = {}
        self.rol = tk.StringVar(value=ROLES[0])
        self.crear_interfaz()
        self.cargar_rol()

    def crear_interfaz(self):
        tk.Label(
            self, text="ROLES Y PERMISOS", font=("sans", 22, "bold"),
            bg="#DDE1E5", fg="#1E293B"
        ).pack(pady=(18, 10))

        marco_roles = tk.LabelFrame(
            self, text="Seleccionar rol", font=("sans", 11, "bold"),
            bg="#C6D9E3", fg="#1E293B", padx=10, pady=5
        )
        marco_roles.pack(fill="x", padx=22)
        for rol in ROLES:
            ttk.Radiobutton(
                marco_roles, text=rol, value=rol, variable=self.rol,
                command=self.cargar_rol
            ).pack(side="left", padx=18, pady=5)

        marco_permisos = tk.LabelFrame(
            self, text="Módulos permitidos", font=("sans", 11, "bold"),
            bg="#C6D9E3", fg="#1E293B", padx=16, pady=8
        )
        marco_permisos.pack(fill="both", expand=True, padx=22, pady=14)
        for indice, modulo in enumerate(MODULOS):
            variable = tk.BooleanVar()
            self.variables[modulo] = variable
            tk.Checkbutton(
                marco_permisos, text=modulo, variable=variable,
                bg="#C6D9E3", activebackground="#C6D9E3",
                font=("sans", 10), anchor="w"
            ).grid(row=indice // 2, column=indice % 2, sticky="w", padx=8, pady=4)

        self.btn_guardar = tk.Button(
            self, text="Guardar permisos", font=("sans", 11, "bold"),
            bg="#15803D", fg="white", activebackground="#166534",
            relief="raised", bd=2, cursor="hand2", command=self.guardar
        )
        self.btn_guardar.pack(pady=(0, 18), ipadx=18, ipady=5)

    def cargar_rol(self):
        permitidos = obtener_permisos(self.rol.get())
        for modulo, variable in self.variables.items():
            variable.set(modulo in permitidos)
        es_admin = self.rol.get() == "Administrador"
        estado = "disabled" if es_admin else "normal"
        for child in self.winfo_children():
            if isinstance(child, tk.LabelFrame):
                for widget in child.winfo_children():
                    if isinstance(widget, tk.Checkbutton):
                        widget.configure(state=estado)

    def guardar(self):
        try:
            seleccionados = {m for m, v in self.variables.items() if v.get()}
            guardar_permisos(self.rol.get(), seleccionados)
            messagebox.showinfo("Permisos guardados", f"Los permisos de {self.rol.get()} fueron actualizados.")
            self.destroy()
        except Exception as error:
            messagebox.showerror("Error", f"No se pudieron guardar los permisos: {error}")
