import tkinter as tk
from tkinter import StringVar, Label, Button, OptionMenu, Checkbutton, IntVar, Scale, HORIZONTAL, Toplevel, Text
import pandas as pd
import os
from datetime import datetime
from utils import get_existing_campaigns, get_campaign_info

class NoiseAnalysis:
    def __init__(self, root, back_callback):
        self.root = root
        self.back_callback = back_callback

    def create_noise_analysis_window(self):
        self.clear_frame()
        analysis_frame = tk.Frame(self.root)
        analysis_frame.pack(fill="both", expand=True)

        Label(analysis_frame, text="Online Noise Analysis", font=("Arial", 20, "bold")).pack(pady=10)

        self.selected_campaign = StringVar(analysis_frame)
        self.campaigns = get_existing_campaigns()
        if self.campaigns:
            self.selected_campaign.set(self.campaigns[0])

        Label(analysis_frame, text="Seleccionar Campaña:").pack()
        OptionMenu(analysis_frame, self.selected_campaign, *self.campaigns).pack()

        campaign_info = get_campaign_info(self.selected_campaign.get())
        self.num_detectors = campaign_info['Número de Detectores']
        
        Label(analysis_frame, text="Selecciona los detectores para graficar:").pack()
        self.detectors = {}
        detector_frame = tk.Frame(analysis_frame)
        detector_frame.pack()
        for i in range(self.num_detectors):
            self.detectors[i+1] = IntVar()
            Checkbutton(detector_frame, text=f"Detector {i+1}", variable=self.detectors[i+1]).grid(row=i//4, column=i%4)

        Label(analysis_frame, text="Selecciona tiempo promedio de acumulación:").pack()
        self.accumulation_time = StringVar()
        self.accumulation_time.set("15 min")
        OptionMenu(analysis_frame, self.accumulation_time, "15 min", "30 min", "1 h", "2 h").pack()

        Label(analysis_frame, text="Tolerancia de incremento de ruido (%):").pack()
        self.noise_tolerance = Scale(analysis_frame, from_=0, to=100, orient=HORIZONTAL)
        self.noise_tolerance.pack()

        button_frame = tk.Frame(analysis_frame)
        button_frame.pack(pady=10)

        plot_button = Button(button_frame, text="Graficar selección", command=self.plot_noise_data)
        plot_button.pack(side="left", padx=5)

        save_button = Button(button_frame, text="Guardar selección", command=self.save_plot)
        save_button.pack(side="left", padx=5)

        analyze_all_button = Button(button_frame, text="Analizar todos los detectores", command=self.analyze_all_detectors)
        analyze_all_button.pack(side="left", padx=5)

        self.report_text = Text(analysis_frame, width=60, height=20)
        self.report_text.pack(pady=10)

        back_button = Button(analysis_frame, text="Regresar", command=self.back_callback)
        back_button.pack(side="left", pady=10)

        save_report_button = Button(analysis_frame, text="Guardar Reporte", command=self.save_report)
        save_report_button.pack(side="right", pady=10)

    def plot_noise_data(self):
        # Implementar la lógica para graficar la relación de ruido
        pass

    def save_plot(self):
        campaign_short_name = self.selected_campaign.get()
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"./Graficos/Noise_analysis/{timestamp}_{campaign_short_name}_noise_plot.png"
        os.makedirs(os.path.dirname(filename), exist_ok=True)

        # Implementar la lógica para guardar el gráfico
        plt.savefig(filename)
        messagebox.showinfo("Info", f"Gráfico guardado en {filename}")

    def analyze_all_detectors(self):
        # Implementar la lógica para analizar todos los detectores y mostrar el reporte en self.report_text
        pass

    def save_report(self):
        campaign_short_name = self.selected_campaign.get()
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"./reports/noise/{timestamp}_{campaign_short_name}_report.txt"
        os.makedirs(os.path.dirname(filename), exist_ok=True)

        with open(filename, 'w') as report_file:
            report_file.write(self.report_text.get("1.0", tk.END))
        messagebox.showinfo("Info", f"Reporte guardado en {filename}")

    def clear_frame(self):
        for widget in self.root.winfo_children():
            widget.destroy()
