import tkinter as tk
from tkinter import font as tkfont
from tkinter import ttk

def apply_styles(root):
    default_font = tkfont.nametofont("TkDefaultFont")
    default_font.config(size=12)

    style = ttk.Style()
    style.configure("TFrame", background="#F6F7EB")
    style.configure("TLabel", background="#F6F7EB", foreground="#0C120C", font=default_font)
    style.configure("TButton", background="#F6F7EB", foreground="#1C5D99", font=default_font)
    style.map("TButton", background=[("active", "#1C5D99")], foreground=[("active", "#F6F7EB")])

    # Definir un estilo específico para los títulos
    title_font = tkfont.Font(family="Helvetica", size=24, weight="bold")
    style.configure("Title.TLabel", font=title_font, background="#F6F7EB", foreground="#0C120C")
