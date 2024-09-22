import tkinter as tk
from tkinter import messagebox, simpledialog
import pandas as pd
import os
from datetime import datetime

class Calibrate:
    def __init__(self, root, back_callback):
        self.root = root
        self.back_callback = back_callback

    def create_calibrate_window(self):
        self.clear_frame()
        calibrate_frame = tk.Frame(self.root)
        calibrate_frame.pack(fill="both", expand=True)

        title = tk.Label(calibrate_frame, text="Calibrate", font=("Arial", 20, "bold"))
        title.pack()

        self.entries = []
        for i in range(self.num_detectors):
            tk.Label(calibrate_frame, text=f"Detector {i+1}").grid(row=i, column=0)
            channel1_entry = tk.Entry(calibrate_frame)
            channel1_entry.grid(row=i, column=1)
            channel2_entry = tk.Entry(calibrate_frame)
            channel2_entry.grid(row=i, column=2)
            self.entries.append((channel1_entry, channel2_entry))

        calibrate_button = tk.Button(calibrate_frame, text="Calibrate", command=self.calibrate)
        calibrate_button.grid(row=self.num_detectors, column=0, pady=10)

        back_button = tk.Button(calibrate_frame, text="Regresar", command=self.back_callback)
        back_button.pack(pady=10)

    def calibrate(self):
        results = []
        for i, (channel1_entry, channel2_entry) in enumerate(self.entries):
            try:
                channel1 = float(channel1_entry.get())
                channel2 = float(channel2_entry.get())
                energy1 = 191
                energy2 = 764

                slope = (energy2 - energy1) / (channel2 - channel1)
                offset = energy1 - slope * channel1

                results.append((offset, slope))
            except ValueError:
                messagebox.showerror("Error", f"Valores inválidos para el Detector {i+1}")
                return

        self.display_results(results)

    def display_results(self, results):
        results_window = tk.Toplevel(self.root)
        results_window.title("Calibration Results")

        for i, (offset, slope) in enumerate(results):
            tk.Label(results_window, text=f"Detector {i+1} - Offset: {offset:.3f}, Slope: {slope:.3f}").pack()

        save_button = tk.Button(results_window, text="Guardar Resultados", command=lambda: self.save_results(results))
        save_button.pack(pady=10)

    def save_results(self, results):
        calibration_data = {
            "Detector": [f"Detector {i+1}" for i in range(self.num_detectors)],
            "Offset": [offset for offset, _ in results],
            "Slope": [slope for _, slope in results]
        }
        df = pd.DataFrame(calibration_data)
        os.makedirs("./calibration", exist_ok=True)
        filename = f"./calibration/{datetime.now().strftime('%Y%m%d_%H%M%S')}_energy_calibration.csv"
        df.to_csv(filename, index=False)
        messagebox.showinfo("Info", f"Resultados guardados en {filename}")

    def clear_frame(self):
        for widget in self.root.winfo_children():
            widget.destroy()
