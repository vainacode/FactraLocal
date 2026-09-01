import tkinter as tk
from PIL import ImageGrab
from prueba import Prueba

raiz = tk.Tk()
raiz.geometry("1x1+0+0")
ventana = Prueba(raiz)
ventana.attributes("-topmost", True)

def escribir():
    ventana.ent_busqueda.insert(0, "TG")
    ventana.ent_busqueda.focus_set()
    raiz.update_idletasks()
    raiz.update()
    x, y = ventana.winfo_rootx(), ventana.winfo_rooty()
    ImageGrab.grab(bbox=(x, y, x + ventana.winfo_width(), y + ventana.winfo_height())).save(r"C:\Users\monte\AppData\Local\Temp\factra_busqueda_check.png")
    ventana.destroy()
    raiz.destroy()

raiz.after(800, escribir)
raiz.mainloop()
