# noise_analysis.py

from PySide6.QtWidgets import (
    QWidget, QLabel, QPushButton, QComboBox, QVBoxLayout, QHBoxLayout,
    QTextEdit, QApplication, QMessageBox, QGroupBox, QSlider, QCheckBox, QScrollArea
)
from PySide6.QtCore import Qt
import pandas as pd
import os
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from utils import get_existing_campaigns, get_num_detectors, create_detector_checkboxes

class NoiseAnalysis(QWidget):
    def __init__(self, back_callback=None):
        super().__init__()
        self.back_callback = back_callback
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Análisis de Ruido Online")
        self.resize(1000, 800)

        # Layout principal con scroll
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        main_widget = QWidget()
        scroll_area.setWidget(main_widget)
        self.main_layout = QVBoxLayout(main_widget)
        self.setLayout(QVBoxLayout())
        self.layout().addWidget(scroll_area)

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
            self.selected_campaign.setCurrentIndex(len(self.campaigns) - 1)
        else:
            self.selected_campaign.addItem("No hay campañas disponibles")
        self.selected_campaign.currentTextChanged.connect(self.update_detectors)
        campaign_layout.addWidget(campaign_label)
        campaign_layout.addWidget(self.selected_campaign)
        self.main_layout.addLayout(campaign_layout)

        # Selección de detectores
        detectors_label = QLabel("Selecciona los detectores para analizar:")
        self.main_layout.addWidget(detectors_label)

        # Aquí usaremos el método create_detector_checkboxes
        self.detectors_widget = QWidget()
        self.detectors_layout = QVBoxLayout(self.detectors_widget)
        self.main_layout.addWidget(self.detectors_widget)

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
        back_button.setStyleSheet("background-color: #f44336; color: white;")
        
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
            QCheckBox {
                font-size: 16px;
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
        if num_detectors == 0:
            QMessageBox.warning(self, "Advertencia", f"La campaña '{campaign_name}' no tiene detectores definidos.")
            return

        # Usar el método create_detector_checkboxes
        detectors_widget, self.detectors_checkboxes, self.select_all_checkbox = create_detector_checkboxes(num_detectors)
        self.detectors_layout.addWidget(detectors_widget)

    def plot_noise_analysis(self):
        campaign_file = f"./data/{self.selected_campaign.currentText()}-CountingRate.csv"
        if not os.path.exists(campaign_file):
            QMessageBox.critical(self, "Error", f"No se encontró el archivo para la campaña {self.selected_campaign.currentText()}")
            return

        try:
            df = pd.read_csv(campaign_file)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al leer los datos de la campaña: {e}")
            return

        # Obtener los detectores seleccionados
        selected_detectors = [i + 1 for i, checkbox in enumerate(self.detectors_checkboxes) if checkbox.isChecked()]
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
        data_plotted = False  # Variable para verificar si se graficaron datos

        for detector in selected_detectors:
            total_col = f"detector_{detector}_total_counts"
            neutron_col = f"detector_{detector}_neutron_counts"
            if total_col not in df.columns or neutron_col not in df.columns:
                QMessageBox.critical(self, "Error", f"El archivo no contiene las columnas necesarias para el Detector {detector}.")
                return

            # Calcular la relación Entries / Neutron Region
            df[f'ratio_{detector}'] = df[total_col] / df[neutron_col]

            # Calcular diferencias y filtrar valores iniciales
            df['diff_time'] = df['timestamp'].diff().dt.total_seconds()
            df_filtered = df[df['diff_time'] > 0]

            if df_filtered.empty:
                QMessageBox.warning(self, "Advertencia", f"No hay datos válidos para el Detector {detector} después del filtrado.")
                continue

            df_resampled = df_filtered.set_index('timestamp').resample(accumulation_delta).mean(numeric_only=True).reset_index()
            df_resampled[f'ratio_{detector}'] = df_resampled[f'ratio_{detector}'].interpolate()

            average_ratio = df_resampled[f'ratio_{detector}'].mean()
            upper_band = average_ratio * (1 + noise_tolerance / 100)
            lower_band = average_ratio * (1 - noise_tolerance / 100)

            plt.plot(df_resampled['timestamp'], df_resampled[f'ratio_{detector}'], label=f'Detector {detector}')
            plt.fill_between(df_resampled['timestamp'], lower_band, upper_band, color='gray', alpha=0.2)
            data_plotted = True

        if data_plotted:
            plt.xlabel('Tiempo')
            plt.ylabel('Relación de Ruido (Entries / Neutron Region)')
            plt.legend()
            plt.title(f"Análisis de Ruido para Campaña {self.selected_campaign.currentText()} cada {accumulation_time}")
            plt.grid(True)
            plt.tight_layout()

            # Mostrar la figura en una ventana nueva
            self.show_plot()
        else:
            QMessageBox.warning(self, "Advertencia", "No hay datos para mostrar después del filtrado.")

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
            df['timestamp'] = pd.to_datetime(df['timestamp'])
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al leer los datos de la campaña: {e}")
            return

        # Obtener los detectores seleccionados
        selected_detectors = [i + 1 for i, checkbox in enumerate(self.detectors_checkboxes) if checkbox.isChecked()]
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
        data_plotted = False  # Variable para verificar si se graficaron datos

        for detector in selected_detectors:
            total_col = f"detector_{detector}_total_counts"
            neutron_col = f"detector_{detector}_neutron_counts"
            if total_col not in df.columns or neutron_col not in df.columns:
                QMessageBox.critical(self, "Error", f"El archivo no contiene las columnas necesarias para el Detector {detector}.")
                return

            # Calcular la relación Entries / Neutron Region
            df[f'ratio_{detector}'] = df[total_col] / df[neutron_col]

            # Calcular diferencias y filtrar valores iniciales
            df['diff_time'] = df['timestamp'].diff().dt.total_seconds()
            df_filtered = df[df['diff_time'] > 0]

            if df_filtered.empty:
                QMessageBox.warning(self, "Advertencia", f"No hay datos válidos para el Detector {detector} después del filtrado.")
                continue

            df_resampled = df_filtered.set_index('timestamp').resample(accumulation_delta).mean(numeric_only=True).reset_index()
            df_resampled[f'ratio_{detector}'] = df_resampled[f'ratio_{detector}'].interpolate()

            average_ratio = df_resampled[f'ratio_{detector}'].mean()
            upper_band = average_ratio * (1 + noise_tolerance / 100)
            lower_band = average_ratio * (1 - noise_tolerance / 100)

            plt.plot(df_resampled['timestamp'], df_resampled[f'ratio_{detector}'], label=f'Detector {detector}')
            plt.fill_between(df_resampled['timestamp'], lower_band, upper_band, color='gray', alpha=0.2)
            data_plotted = True

        if data_plotted:
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
        else:
            QMessageBox.warning(self, "Advertencia", "No hay datos para guardar después del filtrado.")

    def analyze_all_detectors(self):
        campaign_file = f"./data/{self.selected_campaign.currentText()}-CountingRate.csv"
        if not os.path.exists(campaign_file):
            QMessageBox.critical(self, "Error", f"No se encontró el archivo para la campaña {self.selected_campaign.currentText()}")
            return

        try:
            df = pd.read_csv(campaign_file)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
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

            # Calcular la relación Entries / Neutron Region
            df[f'ratio_{detector}'] = df[total_col] / df[neutron_col]

            # Calcular diferencias y filtrar valores iniciales
            df['diff_time'] = df['timestamp'].diff().dt.total_seconds()
            df_filtered = df[df['diff_time'] > 0]

            if df_filtered.empty:
                report_lines.append(f"Detector {detector}: No hay datos válidos después del filtrado.")
                continue

            df_resampled = df_filtered.set_index('timestamp').resample(accumulation_delta).mean(numeric_only=True).reset_index()
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
