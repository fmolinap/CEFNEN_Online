# analisis_estadistico_descriptivo.py

from PySide6.QtWidgets import (
    QWidget, QLabel, QPushButton, QComboBox, QVBoxLayout, QHBoxLayout,
    QMessageBox, QPlainTextEdit, QTabWidget
)
from PySide6.QtCore import Qt
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
from utils import get_existing_campaigns, get_num_detectors
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas

class AnalisisEstadisticoDescriptivo(QWidget):
    def __init__(self, back_callback=None):
        super().__init__()
        self.back_callback = back_callback
        self.init_ui()
    
    def init_ui(self):
        self.setWindowTitle("Análisis Estadístico Descriptivo")
        self.resize(800, 600)
        
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)
        
        # Selección de campaña
        campaign_layout = QHBoxLayout()
        campaign_label = QLabel("Seleccionar Campaña:")
        self.campaign_combo = QComboBox()
        self.campaigns = get_existing_campaigns()
        if self.campaigns:
            self.campaign_combo.addItems(self.campaigns)
        else:
            self.campaign_combo.addItem("No hay campañas disponibles")
        campaign_layout.addWidget(campaign_label)
        campaign_layout.addWidget(self.campaign_combo)
        main_layout.addLayout(campaign_layout)
        
        # Botones
        buttons_layout = QHBoxLayout()
        generate_report_button = QPushButton("Reporte Estadístico")
        generate_report_button.clicked.connect(self.generate_report)
        buttons_layout.addWidget(generate_report_button)
        
        plot_histograms_button = QPushButton("Histo Distribución CR")
        plot_histograms_button.clicked.connect(self.plot_histograms)
        buttons_layout.addWidget(plot_histograms_button)
        
        plot_boxplots_button = QPushButton("Generar Boxplots")
        plot_boxplots_button.clicked.connect(self.plot_boxplots)
        buttons_layout.addWidget(plot_boxplots_button)
        
        back_button = QPushButton("Regresar")
        back_button.setStyleSheet("background-color: #f44336; color: white;")
        back_button.clicked.connect(self.back)
        buttons_layout.addWidget(back_button)
        
        main_layout.addLayout(buttons_layout)
        
        # Tabs para mostrar los reportes
        self.tabs = QTabWidget()
        
        # Tab para reporte estadístico
        self.report_display = QPlainTextEdit()
        self.report_display.setReadOnly(True)
        self.report_display.setMinimumHeight(200)
        self.tabs.addTab(self.report_display, "Reporte Estadístico")
        
        # Tab para reporte de outliers
        self.outliers_display = QPlainTextEdit()
        self.outliers_display.setReadOnly(True)
        self.outliers_display.setMinimumHeight(200)
        self.tabs.addTab(self.outliers_display, "Reporte de Outliers")
        
        main_layout.addWidget(self.tabs)
        
        # Mensaje de estado
        self.message_label = QLabel("")
        main_layout.addWidget(self.message_label)
        
        # Variables de datos
        self.df = None
        self.df_rates = None
        self.num_detectors = 0
        self.short_name = ""
        
        # Estilos
        self.setStyleSheet("""
            QPushButton {
                min-width: 180px;
                min-height: 40px;
                font-size: 14px;
            }
            QLabel {
                font-size: 14px;
            }
            QLineEdit, QComboBox {
                font-size: 14px;
            }
        """)
    
    def load_data(self):
        campaign_name = self.campaign_combo.currentText()
        if not campaign_name or campaign_name == "No hay campañas disponibles":
            QMessageBox.critical(self, "Error", "Debe seleccionar una campaña.")
            return False
        self.short_name = campaign_name
        csv_file = f"./data/{campaign_name}-CountingRate.csv"
        if not os.path.exists(csv_file):
            QMessageBox.critical(self, "Error", f"No se encontró el archivo {csv_file}.")
            return False
        self.df = pd.read_csv(csv_file)
        if self.df.empty:
            QMessageBox.critical(self, "Error", f"El archivo {csv_file} está vacío.")
            return False
        self.df['timestamp'] = pd.to_datetime(self.df['timestamp'])
        self.num_detectors = get_num_detectors(campaign_name)
        if self.num_detectors == 0:
            QMessageBox.critical(self, "Error", f"El número de detectores para la campaña {campaign_name} es 0.")
            return False
        return True
    
    def calculate_counting_rates(self):
        if self.df is None:
            return False
        self.df_rates = self.df.copy()
        for i in range(1, self.num_detectors +1):
            neutron_counts = self.df[f"detector_{i}_neutron_counts"].values
            timestamps = self.df['timestamp'].values
            counting_rates = []
            for j in range(1, len(neutron_counts)):
                delta_counts = neutron_counts[j] - neutron_counts[j-1]
                delta_time = (timestamps[j] - timestamps[j-1]) / np.timedelta64(1, 's')
                # Modificación para ignorar delta_counts negativos
                if delta_counts < 0 or delta_time <= 0:
                    rate = np.nan  # Ignorar este punto
                else:
                    rate = delta_counts / delta_time
                counting_rates.append(rate)
            # Para el primer dato, asignar NaN
            counting_rates.insert(0, np.nan)
            self.df_rates[f"detector_{i}_counting_rate"] = counting_rates
        return True
    
    def generate_report(self):
        if not self.load_data():
            return
        if not self.calculate_counting_rates():
            return
        # Calcular tiempo total de experimento
        total_time = (self.df['timestamp'].iloc[-1] - self.df['timestamp'].iloc[0])
        total_time_str = str(total_time)
        
        # Preparar reporte por detector
        report_lines = []
        report_lines.append(f"Análisis Estadístico Descriptivo de la Campaña {self.campaign_combo.currentText()}")
        report_lines.append(f"Tiempo total de experimento: {total_time_str}")
        report_lines.append("\n")
        for i in range(1, self.num_detectors +1):
            rates = self.df_rates[f"detector_{i}_counting_rate"]
            # Excluir counting rates negativos o NaN
            rates = rates[rates > 0].dropna()
            if len(rates) == 0:
                report_lines.append(f"Detector {i}: No hay datos válidos para calcular estadísticas.\n")
                continue
            mean = np.mean(rates)
            std = np.std(rates)
            median = np.median(rates)
            percentile_25 = np.percentile(rates, 25)
            percentile_75 = np.percentile(rates, 75)
            report_lines.append(f"Detector {i}:")
            report_lines.append(f"  Promedio del counting rate: {mean:.4f} cps")
            report_lines.append(f"  Desviación estándar: {std:.4f} cps")
            report_lines.append(f"  Mediana: {median:.4f} cps")
            report_lines.append(f"  Percentil 25: {percentile_25:.4f} cps")
            report_lines.append(f"  Percentil 75: {percentile_75:.4f} cps")
            report_lines.append("\n")
        report_text = '\n'.join(report_lines)
        # Guardar reporte en archivo .txt
        report_dir = f"./Reportes/Analisis_Estadistico_Descriptivo/{self.short_name}"
        os.makedirs(report_dir, exist_ok=True)
        report_file = os.path.join(report_dir, "AED_counting_rates.txt")
        with open(report_file, 'w') as f:
            f.write(report_text)
        # Mostrar reporte en el área de texto con scrollbar
        self.report_display.setPlainText(report_text)
        # Mostrar mensaje de éxito
        QMessageBox.information(self, "Éxito", f"Reporte generado y guardado en {report_file}")
        # Cambiar a la pestaña del reporte estadístico
        self.tabs.setCurrentWidget(self.report_display)
    
    def plot_histograms(self):
        if not self.load_data():
            return
        if not self.calculate_counting_rates():
            return
        # Preparar datos para graficar
        num_detectors = self.num_detectors
        num_histograms = num_detectors
        grid_size = int(np.ceil(np.sqrt(num_histograms)))
        # Crear figura y ejes
        fig, ax_arr = plt.subplots(grid_size, grid_size, figsize=(16, 9))
        plt.subplots_adjust(wspace=0.4, hspace=0.6)
        # Aplanar arreglo de ejes
        if num_histograms == 1:
            ax_arr = [ax_arr]
        else:
            ax_arr = ax_arr.flatten()
        # Graficar histogramas
        for idx in range(num_detectors):
            detector_num = idx + 1
            rates = self.df_rates[f"detector_{detector_num}_counting_rate"]
            # Excluir counting rates negativos o NaN
            rates = rates[rates > 0].dropna()
            if len(rates) == 0:
                continue
            # Determinar automáticamente el número de bins
            ax_arr[idx].hist(rates, bins='auto', color='blue', alpha=0.7)
            # Calcular estadísticas
            mean = np.mean(rates)
            std = np.std(rates)
            median = np.median(rates)
            percentile_25 = np.percentile(rates, 25)
            percentile_75 = np.percentile(rates, 75)
            # Graficar líneas verticales
            ax_arr[idx].axvline(mean, color='red', linestyle='-', label='Promedio')
            ax_arr[idx].axvline(mean - std, color='green', linestyle='--', label='Desv. Estándar')
            ax_arr[idx].axvline(mean + std, color='green', linestyle='--')
            ax_arr[idx].axvline(median, color='orange', linestyle='-.', label='Mediana')
            ax_arr[idx].axvline(percentile_25, color='purple', linestyle=':', label='Percentil 25')
            ax_arr[idx].axvline(percentile_75, color='purple', linestyle=':')
            ax_arr[idx].set_title(f"Detector {detector_num}")
            ax_arr[idx].set_xlabel("Counting Rate (cps)")
            ax_arr[idx].set_ylabel("Frecuencia")
            if idx == 0:
                ax_arr[idx].legend()
        # Ocultar subplots no utilizados
        for idx in range(num_detectors, len(ax_arr)):
            fig.delaxes(ax_arr[idx])
        # Guardar figura
        graphics_dir = f"./Graficos/AnalisisEstadisticoDescriptivo/{self.short_name}/Histogramas"
        os.makedirs(graphics_dir, exist_ok=True)
        histogram_file = os.path.join(graphics_dir, f"Histogramas_CR_{self.short_name}.png")
        fig.savefig(histogram_file)
        QMessageBox.information(self, "Éxito", f"Histogramas guardados en {histogram_file}")
        # Mostrar figura
        plt.show()
    
    def plot_boxplots(self):
        if not self.load_data():
            return
        if not self.calculate_counting_rates():
            return
        # Preparar datos
        data = []
        labels = []
        outliers_info = {}
        for i in range(1, self.num_detectors +1):
            rates = self.df_rates[f"detector_{i}_counting_rate"]
            timestamps = self.df_rates['timestamp']
            # Excluir counting rates negativos o NaN
            valid_indices = (rates > 0) & (~rates.isna())
            rates = rates[valid_indices]
            timestamps = timestamps[valid_indices]
            if len(rates) == 0:
                continue
            data.append(rates)
            labels.append(f"Detector {i}")
            # Identificar outliers
            q1 = np.percentile(rates, 25)
            q3 = np.percentile(rates, 75)
            iqr = q3 - q1
            lower_bound = q1 - 1.5 * iqr
            upper_bound = q3 + 1.5 * iqr
            outlier_indices = (rates < lower_bound) | (rates > upper_bound)
            outliers = rates[outlier_indices]
            outlier_timestamps = timestamps[outlier_indices]
            outliers_info[f"Detector {i}"] = list(zip(outliers, outlier_timestamps))
        # Verificar si hay datos para graficar
        if not data:
            QMessageBox.information(self, "Información", "No hay datos válidos para generar los boxplots.")
            return
        # Crear boxplot
        fig, ax = plt.subplots(figsize=(12, 8))
        ax.boxplot(data, labels=labels, showfliers=True)
        ax.set_title("Boxplots de Counting Rates de Neutrones por Detector")
        ax.set_ylabel("Counting Rate (cps)")
        # Guardar figura
        graphics_dir = f"./Graficos/AnalisisEstadisticoDescriptivo/{self.short_name}/Boxplots"
        os.makedirs(graphics_dir, exist_ok=True)
        boxplot_file = os.path.join(graphics_dir, f"BoxPlot_CR_{self.short_name}.png")
        fig.savefig(boxplot_file)
        QMessageBox.information(self, "Éxito", f"Boxplots guardados en {boxplot_file}")
        # Mostrar figura
        plt.show()
        # Generar reporte de outliers
        outliers_report = []
        for detector, outliers_list in outliers_info.items():
            if outliers_list:
                outliers_report.append(f"{detector} tiene outliers en los siguientes timestamps:")
                for value, timestamp in outliers_list:
                    outliers_report.append(f"  Timestamp: {timestamp}, Counting Rate: {value:.4f} cps")
            else:
                outliers_report.append(f"{detector} no tiene outliers.")
            outliers_report.append("\n")
        outliers_text = '\n'.join(outliers_report)
        # Guardar reporte de outliers
        outliers_dir = f"./Reportes/Outliers/{self.short_name}"
        os.makedirs(outliers_dir, exist_ok=True)
        outliers_file = os.path.join(outliers_dir, "Analysis_outliers.txt")
        with open(outliers_file, 'w') as f:
            f.write(outliers_text)
        # Mostrar reporte de outliers en el área de texto
        self.outliers_display.setPlainText(outliers_text)
        # Cambiar a la pestaña de reporte de outliers
        self.tabs.setCurrentWidget(self.outliers_display)
        # Mostrar mensaje de éxito
        QMessageBox.information(self, "Éxito", f"Análisis de outliers guardado en {outliers_file}")
    
    def back(self):
        if callable(self.back_callback):
            self.back_callback()
        else:
            self.close()
