from PySide6.QtWidgets import (
    QWidget, QLabel, QPushButton, QComboBox, QVBoxLayout, QHBoxLayout,
    QCheckBox, QRadioButton, QApplication, QMessageBox, QGroupBox,
    QGridLayout
)
from PySide6.QtCore import Qt
import pandas as pd
import os
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from utils import get_existing_campaigns, get_num_detectors


class PlotCREvo(QWidget):
    def __init__(self, back_callback=None):
        super().__init__()
        self.back_callback = back_callback
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Gráficos de Evolución Temporal de Campañas Experimentales")
        self.resize(1000, 800)

        # Layout principal
        self.main_layout = QVBoxLayout(self)
        self.setLayout(self.main_layout)

        # Título
        title = QLabel("Gráficos de Evolución Temporal de Campañas Experimentales")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 24px; font-weight: bold;")
        self.main_layout.addWidget(title)

        # Selección de campaña
        campaign_layout = QHBoxLayout()
        campaign_label = QLabel("Seleccionar Campaña:")
        self.selected_campaign_plot = QComboBox()
        self.campaigns = get_existing_campaigns()
        if self.campaigns:
            self.selected_campaign_plot.addItems(self.campaigns)
        else:
            self.selected_campaign_plot.addItem("No hay campañas disponibles")
        self.selected_campaign_plot.currentTextChanged.connect(self.update_detectors)
        campaign_layout.addWidget(campaign_label)
        campaign_layout.addWidget(self.selected_campaign_plot)
        self.main_layout.addLayout(campaign_layout)

        # Selección de datos a graficar
        data_type_layout = QHBoxLayout()
        data_type_label = QLabel("Seleccionar Datos a Graficar:")
        self.entries_radio = QRadioButton("Entries")
        self.entries_radio.setChecked(True)
        self.neutron_radio = QRadioButton("Neutron Regions")
        data_type_layout.addWidget(data_type_label)
        data_type_layout.addWidget(self.entries_radio)
        data_type_layout.addWidget(self.neutron_radio)
        self.main_layout.addLayout(data_type_layout)

        # Selección de detectores
        detectors_label = QLabel("Selecciona los detectores para graficar:")
        self.main_layout.addWidget(detectors_label)
        self.detectors_group = QGroupBox()
        self.detectors_layout = QGridLayout()
        self.detectors_group.setLayout(self.detectors_layout)
        self.main_layout.addWidget(self.detectors_group)

        # Selección de tiempo de acumulación
        accumulation_layout = QHBoxLayout()
        accumulation_label = QLabel("Selecciona tiempo promedio de acumulación:")
        self.accumulation_time = QComboBox()
        accumulation_times = ["15 min", "30 min", "1 h", "2 h"]
        self.accumulation_time.addItems(accumulation_times)
        accumulation_layout.addWidget(accumulation_label)
        accumulation_layout.addWidget(self.accumulation_time)
        self.main_layout.addLayout(accumulation_layout)

        # Botones de acción
        buttons_layout = QHBoxLayout()
        plot_button = QPushButton("Graficar selección")
        plot_button.clicked.connect(self.plot_data)
        save_button = QPushButton("Guardar Selección")
        save_button.clicked.connect(self.save_plot)
        buttons_layout.addWidget(plot_button)
        buttons_layout.addWidget(save_button)
        self.main_layout.addLayout(buttons_layout)

        # Botón de regresar
        back_button = QPushButton("Regresar")
        back_button.clicked.connect(self.back)
        self.main_layout.addWidget(back_button)

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
            QComboBox, QRadioButton {
                font-size: 16px;
            }
            QCheckBox {
                font-size: 16px;
            }
        """)

        # Actualizar detectores iniciales
        self.update_detectors(self.selected_campaign_plot.currentText())

    def update_detectors(self, campaign_name):
        # Limpiar layout de detectores
        for i in reversed(range(self.detectors_layout.count())):
            widget = self.detectors_layout.itemAt(i).widget()
            if widget is not None:
                widget.setParent(None)

        num_detectors = get_num_detectors(campaign_name)
        self.detector_checkboxes = []
        row = 0
        col = 0
        for i in range(num_detectors):
            checkbox = QCheckBox(f"Detector {i + 1}")
            self.detector_checkboxes.append(checkbox)
            self.detectors_layout.addWidget(checkbox, row, col)
            col += 1
            if col > 3:
                col = 0
                row += 1

    def plot_data(self):
        campaign_file = f"./data/{self.selected_campaign_plot.currentText()}-CountingRate.csv"
        if not os.path.exists(campaign_file):
            QMessageBox.critical(self, "Error", f"No se encontró el archivo para la campaña {self.selected_campaign_plot.currentText()}")
            return

        try:
            df = pd.read_csv(campaign_file)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al leer los datos de la campaña: {e}")
            return

        selected_detectors = [i + 1 for i, cb in enumerate(self.detector_checkboxes) if cb.isChecked()]
        if not selected_detectors:
            QMessageBox.critical(self, "Error", "Debe seleccionar al menos un detector.")
            return

        data_type = "Neutron Regions" if self.neutron_radio.isChecked() else "Entries"
        accumulation_time = self.accumulation_time.currentText()

        time_deltas = {
            "15 min": timedelta(minutes=15),
            "30 min": timedelta(minutes=30),
            "1 h": timedelta(hours=1),
            "2 h": timedelta(hours=2)
        }
        accumulation_delta = time_deltas[accumulation_time]

        plt.figure(figsize=(10, 6))
        for detector in selected_detectors:
            col_name = f"detector_{detector}_neutron_counts" if data_type == "Neutron Regions" else f"detector_{detector}_total_counts"
            if col_name not in df.columns:
                QMessageBox.critical(self, "Error", f"El archivo no contiene la columna {col_name}.")
                return

            df['diff_counts'] = df[col_name].diff().fillna(0)
            df['diff_time'] = df['timestamp'].diff().dt.total_seconds().fillna(1)
            df['rate'] = df['diff_counts'] / df['diff_time']

            # Resamplear los datos en intervalos de acumulación y calcular la media
            df_resampled = df.set_index('timestamp').resample(accumulation_delta).mean(numeric_only=True).reset_index()

            # Interpolar valores faltantes
            df_resampled['rate'] = df_resampled['rate'].interpolate()

            plt.plot(df_resampled['timestamp'], df_resampled['rate'], label=f'Detector {detector}')

        plt.xlabel('Tiempo')
        plt.ylabel('Average Counting Rate s$^{-1}$')
        plt.legend()
        plt.title(f"Counting Rate ({data_type}) para la Campaña {self.selected_campaign_plot.currentText()} cada {accumulation_time}")
        plt.grid(True)
        plt.tight_layout()

        # Mostrar el gráfico en una ventana nueva
        self.show_plot()

    def show_plot(self):
        self.plot_window = QWidget()
        self.plot_window.setWindowTitle("Resultado del Gráfico")
        plot_layout = QVBoxLayout()
        self.plot_window.setLayout(plot_layout)

        canvas = FigureCanvas(plt.gcf())
        plot_layout.addWidget(canvas)

        self.plot_window.resize(800, 600)
        self.plot_window.show()

    def save_plot(self):
        campaign_file = f"./data/{self.selected_campaign_plot.currentText()}-CountingRate.csv"
        if not os.path.exists(campaign_file):
            QMessageBox.critical(self, "Error", f"No se encontró el archivo para la campaña {self.selected_campaign_plot.currentText()}")
            return

        try:
            df = pd.read_csv(campaign_file)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al leer los datos de la campaña: {e}")
            return

        selected_detectors = [i + 1 for i, cb in enumerate(self.detector_checkboxes) if cb.isChecked()]
        if not selected_detectors:
            QMessageBox.critical(self, "Error", "Debe seleccionar al menos un detector.")
            return

        data_type = "Neutron Regions" if self.neutron_radio.isChecked() else "Entries"
        accumulation_time = self.accumulation_time.currentText()

        time_deltas = {
            "15 min": timedelta(minutes=15),
            "30 min": timedelta(minutes=30),
            "1 h": timedelta(hours=1),
            "2 h": timedelta(hours=2)
        }
        accumulation_delta = time_deltas[accumulation_time]

        plt.figure(figsize=(10, 6))
        for detector in selected_detectors:
            col_name = f"detector_{detector}_neutron_counts" if data_type == "Neutron Regions" else f"detector_{detector}_total_counts"
            if col_name not in df.columns:
                QMessageBox.critical(self, "Error", f"El archivo no contiene la columna {col_name}.")
                return

            df['diff_counts'] = df[col_name].diff().fillna(0)
            df['diff_time'] = df['timestamp'].diff().dt.total_seconds().fillna(1)
            df['rate'] = df['diff_counts'] / df['diff_time']

            # Resamplear los datos en intervalos de acumulación y calcular la media
            df_resampled = df.set_index('timestamp').resample(accumulation_delta).mean(numeric_only=True).reset_index()

            # Interpolar valores faltantes
            df_resampled['rate'] = df_resampled['rate'].interpolate()

            plt.plot(df_resampled['timestamp'], df_resampled['rate'], label=f'Detector {detector}')

        plt.xlabel('Tiempo')
        plt.ylabel('Average Counting Rate s$^{-1}$')
        plt.legend()
        plt.title(f"Counting Rate ({data_type}) para la Campaña {self.selected_campaign_plot.currentText()} cada {accumulation_time}")
        plt.grid(True)
        plt.tight_layout()

        # Crear carpeta si no existe
        directory = f"./Graficos/{self.selected_campaign_plot.currentText()}"
        if not os.path.exists(directory):
            os.makedirs(directory)

        # Guardar el gráfico
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        detectors_str = "_".join([f"Detector{detector}" for detector in selected_detectors])
        file_name = f"{directory}/{timestamp}_CountingRate_{self.selected_campaign_plot.currentText()}_{accumulation_time}_{detectors_str}.png"
        plt.savefig(file_name)

        QMessageBox.information(self, "Éxito", f"Gráfico guardado como {file_name}")

    def back(self):
        if callable(self.back_callback):
            self.back_callback()
        else:
            self.close()


if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    window = PlotCREvo()
    window.show()
    sys.exit(app.exec())
