from PySide6.QtWidgets import (
    QWidget, QLabel, QPushButton, QComboBox, QVBoxLayout, QHBoxLayout,
    QCheckBox, QRadioButton, QSlider, QTextEdit, QApplication, QMessageBox, QGroupBox,
    QGridLayout, QFileDialog
)
from PySide6.QtCore import Qt, QDateTime, QTimer
import pandas as pd
import os
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from utils import get_existing_campaigns, get_num_detectors

class NoiseAnalysis(QWidget):
    def __init__(self, back_callback=None):
        super().__init__()
        self.back_callback = back_callback
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Análisis de Ruido Online")
        self.resize(1000, 800)

        # Layout principal
        self.main_layout = QVBoxLayout(self)
        self.setLayout(self.main_layout)

        # Título
        title = QLabel("Análisis de Ruido Online")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 24px; font-weight: bold;")
        self.main_layout.addWidget(title)

        # Selección de campaña
        campaign_layout = QHBoxLayout()
        campaign_label = QLabel("Seleccionar Campaña:")
        self.selected_campaign = QComboBox()
        self.campaigns = get_existing_campaigns()
        if self.campaigns:
            self.selected_campaign.addItems(self.campaigns)
        else:
            self.selected_campaign.addItem("No hay campañas disponibles")
        self.selected_campaign.currentTextChanged.connect(self.update_detectors)
        campaign_layout.addWidget(campaign_label)
        campaign_layout.addWidget(self.selected_campaign)
        self.main_layout.addLayout(campaign_layout)

        # Selección de detectores
        self.detectors_group = QGroupBox("Selecciona los detectores para analizar:")
        self.detectors_layout = QGridLayout()
        self.detectors_group.setLayout(self.detectors_layout)
        self.main_layout.addWidget(self.detectors_group)

        # Selección de tiempo promedio de acumulación
        accumulation_layout = QHBoxLayout()
        accumulation_label = QLabel("Selecciona tiempo promedio de acumulación:")
        self.accumulation_time = QComboBox()
        accumulation_times = ["15 min", "30 min", "1 h", "2 h"]
        self.accumulation_time.addItems(accumulation_times)
        accumulation_layout.addWidget(accumulation_label)
        accumulation_layout.addWidget(self.accumulation_time)
        self.main_layout.addLayout(accumulation_layout)

        # Tolerancia de incremento de ruido
        noise_layout = QHBoxLayout()
        noise_label = QLabel("Tolerancia de incremento de ruido (%):")
        self.noise_tolerance = QSlider(Qt.Horizontal)
        self.noise_tolerance.setRange(0, 100)
        self.noise_tolerance.setValue(10)
        self.noise_value_label = QLabel(f"{self.noise_tolerance.value()}%")
        self.noise_tolerance.valueChanged.connect(self.update_noise_label)
        noise_layout.addWidget(noise_label)
        noise_layout.addWidget(self.noise_tolerance)
        noise_layout.addWidget(self.noise_value_label)
        self.main_layout.addLayout(noise_layout)

        # Botones de acción
        buttons_layout = QHBoxLayout()
        plot_button = QPushButton("Graficar Selección")
        plot_button.clicked.connect(self.plot_noise_analysis)
        buttons_layout.addWidget(plot_button)

        save_button = QPushButton("Guardar Selección")
        save_button.clicked.connect(self.save_plot)
        buttons_layout.addWidget(save_button)

        analyze_all_button = QPushButton("Analizar Todos los Detectores")
        analyze_all_button.clicked.connect(self.analyze_all_detectors)
        buttons_layout.addWidget(analyze_all_button)

        self.main_layout.addLayout(buttons_layout)

        # Área de reporte
        self.report_text = QTextEdit()
        self.report_text.setReadOnly(True)
        self.main_layout.addWidget(self.report_text)

        # Botones de navegación
        nav_buttons_layout = QHBoxLayout()
        back_button = QPushButton("Regresar")
        back_button.clicked.connect(self.back)
        nav_buttons_layout.addWidget(back_button)

        save_report_button = QPushButton("Guardar Reporte")
        save_report_button.clicked.connect(self.save_report)
        nav_buttons_layout.addWidget(save_report_button)

        self.main_layout.addLayout(nav_buttons_layout)

        # Estilos
        self.setStyleSheet("""
            QPushButton {
                min-width: 180px;
                min-height: 40px;
                font-size: 16px;
            }
            QLabel {
                font-size: 16px;
            }
            QComboBox, QSlider {
                font-size: 16px;
            }
            QTextEdit {
                font-size: 14px;
            }
        """)

        # Cargar detectores iniciales
        self.update_detectors(self.selected_campaign.currentText())

    def update_noise_label(self, value):
        self.noise_value_label.setText(f"{value}%")

    def update_detectors(self, campaign_name):
        # Limpiar layout de detectores
        for i in reversed(range(self.detectors_layout.count())):
            widget = self.detectors_layout.itemAt(i).widget()
            if widget is not None:
                widget.setParent(None)

        num_detectors = get_num_detectors(campaign_name)
        self.detectors = []
        row = 0
        col = 0
        for i in range(num_detectors):
            checkbox = QCheckBox(f"Detector {i + 1}")
            self.detectors.append(checkbox)
            self.detectors_layout.addWidget(checkbox, row, col)
            col += 1
            if col > 3:
                col = 0
                row += 1

    def plot_noise_analysis(self):
        campaign_file = f"./data/{self.selected_campaign.currentText()}-CountingRate.csv"
        if not os.path.exists(campaign_file):
            QMessageBox.critical(self, "Error", f"No se encontró el archivo para la campaña {self.selected_campaign.currentText()}")
            return

        try:
            df = pd.read_csv(campaign_file)
            df['timestamp'] = pd.to_datetime(df['timestamp'], format="%Y-%m-%d %H:%M:%S")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al leer los datos de la campaña: {e}")
            return

        selected_detectors = [i + 1 for i, checkbox in enumerate(self.detectors) if checkbox.isChecked()]
        if not selected_detectors:
            QMessageBox.critical(self, "Error", "Debe seleccionar al menos un detector.")
            return

        accumulation_time = self.accumulation_time.currentText()
        noise_tolerance = self.noise_tolerance.value()

        time_deltas = {
            "15 min": timedelta(minutes=15),
            "30 min": timedelta(minutes=30),
            "1 h": timedelta(hours=1),
            "2 h": timedelta(hours=2)
        }
        accumulation_delta = time_deltas[accumulation_time]

        plt.figure(figsize=(10, 6))
        for detector in selected_detectors:
            total_col = f"detector_{detector}_total_counts"
            neutron_col = f"detector_{detector}_neutron_counts"
            if total_col not in df.columns or neutron_col not in df.columns:
                QMessageBox.critical(self, "Error", f"El archivo no contiene las columnas necesarias para el Detector {detector}.")
                return

            df[f'ratio_{detector}'] = df[total_col] / df[neutron_col]

            df_resampled = df.set_index('timestamp').resample(accumulation_delta).mean(numeric_only=True).reset_index()
            df_resampled[f'ratio_{detector}'] = df_resampled[f'ratio_{detector}'].interpolate()

            average_ratio = df_resampled[f'ratio_{detector}'].mean()
            upper_band = average_ratio * (1 + noise_tolerance / 100)
            lower_band = average_ratio * (1 - noise_tolerance / 100)

            plt.plot(df_resampled['timestamp'], df_resampled[f'ratio_{detector}'], label=f'Detector {detector}')
            plt.fill_between(df_resampled['timestamp'], lower_band, upper_band, color='gray', alpha=0.2)

        plt.xlabel('Tiempo')
        plt.ylabel('Relación de Ruido (Entries / Neutron Region)')
        plt.legend()
        plt.title(f"Análisis de Ruido para Campaña {self.selected_campaign.currentText()} cada {accumulation_time}")
        plt.grid(True)
        plt.tight_layout()

        # Mostrar la figura en una ventana nueva
        self.show_plot()

    def show_plot(self):
        self.plot_window = QWidget()
        self.plot_window.setWindowTitle("Resultado del Análisis de Ruido")
        plot_layout = QVBoxLayout()
        self.plot_window.setLayout(plot_layout)

        canvas = FigureCanvas(plt.gcf())
        plot_layout.addWidget(canvas)

        self.plot_window.resize(800, 600)
        self.plot_window.show()

    def save_plot(self):
        campaign_file = f"./data/{self.selected_campaign.currentText()}-CountingRate.csv"
        if not os.path.exists(campaign_file):
            QMessageBox.critical(self, "Error", f"No se encontró el archivo para la campaña {self.selected_campaign.currentText()}")
            return

        try:
            df = pd.read_csv(campaign_file)
            df['timestamp'] = pd.to_datetime(df['timestamp'], format="%Y-%m-%d %H:%M:%S")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al leer los datos de la campaña: {e}")
            return

        selected_detectors = [i + 1 for i, checkbox in enumerate(self.detectors) if checkbox.isChecked()]
        if not selected_detectors:
            QMessageBox.critical(self, "Error", "Debe seleccionar al menos un detector.")
            return

        accumulation_time = self.accumulation_time.currentText()
        noise_tolerance = self.noise_tolerance.value()

        time_deltas = {
            "15 min": timedelta(minutes=15),
            "30 min": timedelta(minutes=30),
            "1 h": timedelta(hours=1),
            "2 h": timedelta(hours=2)
        }
        accumulation_delta = time_deltas[accumulation_time]

        plt.figure(figsize=(10, 6))
        for detector in selected_detectors:
            total_col = f"detector_{detector}_total_counts"
            neutron_col = f"detector_{detector}_neutron_counts"
            if total_col not in df.columns or neutron_col not in df.columns:
                QMessageBox.critical(self, "Error", f"El archivo no contiene las columnas necesarias para el Detector {detector}.")
                return

            df[f'ratio_{detector}'] = df[total_col] / df[neutron_col]

            df_resampled = df.set_index('timestamp').resample(accumulation_delta).mean(numeric_only=True).reset_index()
            df_resampled[f'ratio_{detector}'] = df_resampled[f'ratio_{detector}'].interpolate()

            average_ratio = df_resampled[f'ratio_{detector}'].mean()
            upper_band = average_ratio * (1 + noise_tolerance / 100)
            lower_band = average_ratio * (1 - noise_tolerance / 100)

            plt.plot(df_resampled['timestamp'], df_resampled[f'ratio_{detector}'], label=f'Detector {detector}')
            plt.fill_between(df_resampled['timestamp'], lower_band, upper_band, color='gray', alpha=0.2)

        plt.xlabel('Tiempo')
        plt.ylabel('Relación de Ruido (Entries / Neutron Region)')
        plt.legend()
        plt.title(f"Análisis de Ruido para Campaña {self.selected_campaign.currentText()} cada {accumulation_time}")
        plt.grid(True)
        plt.tight_layout()

        directory = "./Graficos/Noise_analysis"
        if not os.path.exists(directory):
            os.makedirs(directory)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        detectors_str = "_".join([f"Detector{detector}" for detector in selected_detectors])
        file_name = f"{directory}/{timestamp}_NoiseAnalysis_{self.selected_campaign.currentText()}_{detectors_str}.png"
        plt.savefig(file_name)

        QMessageBox.information(self, "Éxito", f"Gráfico guardado como {file_name}")

    def analyze_all_detectors(self):
        campaign_file = f"./data/{self.selected_campaign.currentText()}-CountingRate.csv"
        if not os.path.exists(campaign_file):
            QMessageBox.critical(self, "Error", f"No se encontró el archivo para la campaña {self.selected_campaign.currentText()}")
            return

        try:
            df = pd.read_csv(campaign_file)
            df['timestamp'] = pd.to_datetime(df['timestamp'], format="%Y-%m-%d %H:%M:%S")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al leer los datos de la campaña: {e}")
            return

        accumulation_time = self.accumulation_time.currentText()
        noise_tolerance = self.noise_tolerance.value()

        time_deltas = {
            "15 min": timedelta(minutes=15),
            "30 min": timedelta(minutes=30),
            "1 h": timedelta(hours=1),
            "2 h": timedelta(hours=2)
        }
        accumulation_delta = time_deltas[accumulation_time]

        report_lines = []

        num_detectors = get_num_detectors(self.selected_campaign.currentText())
        for detector in range(1, num_detectors + 1):
            total_col = f"detector_{detector}_total_counts"
            neutron_col = f"detector_{detector}_neutron_counts"
            if total_col not in df.columns or neutron_col not in df.columns:
                QMessageBox.critical(self, "Error", f"El archivo no contiene las columnas necesarias para el Detector {detector}.")
                return

            df[f'ratio_{detector}'] = df[total_col] / df[neutron_col]

            df_resampled = df.set_index('timestamp').resample(accumulation_delta).mean(numeric_only=True).reset_index()
            df_resampled[f'ratio_{detector}'] = df_resampled[f'ratio_{detector}'].interpolate()

            average_ratio = df_resampled[f'ratio_{detector}'].mean()
            current_ratio = df_resampled[f'ratio_{detector}'].iloc[-1]
            variation = (current_ratio - average_ratio) / average_ratio * 100

            line = f"Detector {detector}: Variación de {variation:.2f}%"
            if abs(variation) > noise_tolerance:
                line = f"**{line} (Fuera de tolerancia)**"

            report_lines.append(line)

        report = "\n".join(report_lines)

        self.report_text.setPlainText(report)

    def save_report(self):
        report = self.report_text.toPlainText()
        if not report.strip():
            QMessageBox.critical(self, "Error", "No hay reporte para guardar.")
            return

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_directory = "./reports/noise"
        if not os.path.exists(report_directory):
            os.makedirs(report_directory)

        report_file = f"{report_directory}/{timestamp}_{self.selected_campaign.currentText()}.txt"
        with open(report_file, 'w') as file:
            file.write(report)

        QMessageBox.information(self, "Éxito", f"Reporte de análisis de ruido guardado como {report_file}")

    def back(self):
        if callable(self.back_callback):
            self.back_callback()
        else:
            self.close()

if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    window = NoiseAnalysis()
    window.show()
    sys.exit(app.exec())
