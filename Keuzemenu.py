# -*- coding: utf-8 -*-
"""
Created on Thu Nov 13 15:40:55 2025

@author: nilsw
"""
def select_sport():
    import tkinter as tk
    from tkinter import ttk

    root = tk.Tk()
    root.withdraw()

    selected_sport = None
    selected_lactate = None

    def center_window(window, width, height):
        """Centreert een Tkinter-venster op het scherm."""
        window.update_idletasks()
        screen_w = window.winfo_screenwidth()
        screen_h = window.winfo_screenheight()
        x = (screen_w - width) // 2
        y = (screen_h - height) // 2
        window.geometry(f"{width}x{height}+{x}+{y}")

    def on_ok():
        nonlocal selected_sport, selected_lactate
        selected_sport = sport_dropdown.get()
        selected_lactate = lactate_dropdown.get()
        top.destroy()

    # Popup window
    top = tk.Toplevel(root)
    top.title("Selecteer een sport")
    window_width = 300
    window_height = 200
    center_window(top, window_width, window_height)
    top.grab_set()

    ttk.Label(top, text="Kies de sport die je wilt analyseren:").pack(pady=5)
    sport_dropdown = ttk.Combobox(top, state="readonly",
                                  values=("Wielrennen", "Hardlopen"))
    sport_dropdown.current(0)
    sport_dropdown.pack(pady=5)

    ttk.Label(top, text="Met lactaatmetingen?").pack(pady=5)
    lactate_dropdown = ttk.Combobox(top, state="readonly",
                                    values=("Ja", "Nee"))
    lactate_dropdown.current(1)
    lactate_dropdown.pack(pady=5)

    ttk.Button(top, text="OK", command=on_ok).pack(pady=10)

    root.wait_window(top)
    root.destroy()

    return selected_sport, selected_lactate
def kies_bestand() -> str:
    import tkinter as tk
    from tkinter import filedialog, messagebox, simpledialog, ttk
    import sys
    """Laat de gebruiker een Excelbestand kiezen en geeft het pad terug."""
    root = tk.Tk()
    root.withdraw()
    root.call('wm', 'attributes', '.', '-topmost', True)

    file_path = filedialog.askopenfilename()
    root.destroy()

    if not file_path:
        print("Geen bestand geselecteerd. Sluiten...")
        sys.exit()

    print(f"Geselecteerd bestand: {file_path}")
    return file_path