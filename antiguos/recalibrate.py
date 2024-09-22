import tkinter as tk
from tkinter import messagebox, Label, Entry, Button, simpledialog
import pandas as pd
import os
from datetime import datetime

class Recalibrate:
    def __init__(self, root, back_callback, num_detectors):
        self.root = root
        self.back_callback = back_callback
        self.num_detectors = num_detectors

    def create_recalibrate_window(self):
        self.clear_frame()
        recalibrate_frame = tk.Frame(self.root)
        recalibrate_frame.pack(fill="both", expand=True)

        title = tk.Label(recalibrate_frame, text="Recalibrate", font=("Arial", 20, "bold"))
        title.pack()
        self.entries = []
        for i in range(self.num_detectors):
            tk.Label(recalibrate_frame, text=f"Detector {i+1}").grid(row=i, column=0)
            actual_value1_entry = tk.Entry(recalibrate_frame)
            actual_value1_entry.grid(row=i, column=1)
            actual_value2_entry = tk.Entry(recalibrate_frame)
            actual_value2_entry.grid(row=i, column=2)
            self.entries.append((actual_value1_entry, actual_value2_entry))

        recalibrate_button = tk.Button(recalibrate_frame, text="Recalibrate", command=self.recalibrate)
        recalibrate_button.grid(row=self.num_detectors, column=0, pady=10)

        back_button = tk.Button(recalibrate_frame, text="Regresar", command=self.back_callback)
        back_button.grid(row=self.num_detectors, column=1, pady=10)

    def recalibrate(self):
        results = []
        last_calibration_file = self.get_last_calibration_file()
        if not last_calibration_file:
            messagebox.showerror("Error", "No se encontró el archivo de calibración anterior.")
            return

        df = pd.read_csv(last_calibration_file)
        for i, (actual_value1_entry, actual_value2_entry) in enumerate(self.entries):
            try:
                actual_value1 = float(actual_value1_entry.get())
                actual_value2 = float(actual_value2_entry.get())
                original_channel1 = df.loc[i, 'Channel_191']
                original_channel2 = df.loc[i, 'Channel_764']

                slope = (actual_value2 - actual_value1) / (original_channel2 - original_channel1)
                offset = actual_value1 - slope * original_channel1

                results.append((offset, slope))
            except ValueError:
                messagebox.showerror("Error", f"Valores inválidos para el Detector {i+1}")
                return

        self.display_results(results)

    def get_last_calibration_file(self):
        calibration_dir = "./calibration"
        if not os.path.exists(calibration_dir):
            return None

        files = [os.path.join(calibration_dir, f) for f in os.listdir(calibration_dir) if f.endswith("_energy_calibration.csv")]
        if not files:
            return None

        latest_file = max(files, key=os.path.getctime)
        return latest_file

    def display_results(self, results):
        results_window = tk.Toplevel(self.root)
        results_window.title("Recalibration Results")

        for i, (offset, slope) in enumerate(results):
            tk.Label(results_window, text=f"Detector {i+1} - Offset: {offset:.3f}, Slope: {slope:.3f}").pack()

        save_button = tk.Button(results_window, text="Guardar Resultados", command=lambda: self.save_results(results))
        save_button.pack(pady=10)

    def save_results(self, results):
        recalibration_data = {
            "Detector": [f"Detector {i+1}" for i in range(self.num_detectors)],
            "Offset": [offset for offset, _ in results],
            "Slope": [slope for _, slope in results]
        }
        df = pd.DataFrame(recalibration_data)
        os.makedirs("./calibration", exist_ok=True)
        filename = f"./calibration/{datetime.now().strftime('%Y%m%d_%H%M%S')}_recalibration.csv"
        df.to_csv(filename, index=False)
        messagebox.showinfo("Info", f"Resultados guardados en {filename}")

    def clear_frame(self):
        for widget in self.root.winfo_children():
            widget.destroy()
