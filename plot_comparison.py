from PySide6.QtWidgets import (
    QWidget, QLabel, QPushButton, QComboBox, QVBoxLayout, QHBoxLayout,
    QApplication, QMessageBox, QRadioButton, QGroupBox, QGridLayout
)
from PySide6.QtCore import Qt
import pandas as pd
import os
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from utils import get_existing_campaigns, get_num_detectors, create_detector_checkboxes

class PlotComparison(QWidget):
    def __init__(self, back_callback=None):
        super().__init__()
        self.back_callback = back_callback
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Comparación Gráfica entre Campañas")
        self.resize(1000, 800)

        # Layout principal
        self.main_layout = QVBoxLayout(self)
        self.setLayout(self.main_layout)

        # Título
        title = QLabel("Comparación Gráfica entre Campañas")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 24px; font-weight: bold;")
        self.main_layout.addWidget(title)

        # Selección de campañas
        campaigns_layout = QGridLayout()
        campaign_label1 = QLabel("Seleccionar Campaña 1:")
        self.selected_campaign_plot1 = QComboBox()
        self.campaigns = get_existing_campaigns()
        if self.campaigns:
            self.selected_campaign_plot1.addItems(self.campaigns)
        else:
            self.selected_campaign_plot1.addItem("No hay campañas disponibles")
        self.selected_campaign_plot1.currentTextChanged.connect(self.update_detectors1)

        campaign_label2 = QLabel("Seleccionar Campaña 2:")
        self.selected_campaign_plot2 = QComboBox()
        if self.campaigns:
            self.selected_campaign_plot2.addItems(self.campaigns)
        else:
            self.selected_campaign_plot2.addItem("No hay campañas disponibles")
        self.selected_campaign_plot2.currentTextChanged.connect(self.update_detectors2)

        campaigns_layout.addWidget(campaign_label1, 0, 0)
        campaigns_layout.addWidget(self.selected_campaign_plot1, 0, 1)
        campaigns_layout.addWidget(campaign_label2, 1, 0)
        campaigns_layout.addWidget(self.selected_campaign_plot2, 1, 1)

        self.main_layout.addLayout(campaigns_layout)

        # Selección de datos a graficar
        data_type_layout = QGridLayout()

        data_type_label1 = QLabel("Seleccionar Datos a Graficar para Campaña 1:")
        self.data_type1 = QGroupBox()
        data_type_options1 = QHBoxLayout()
        self.entries_radio1 = QRadioButton("Entries")
        self.entries_radio1.setChecked(True)
        self.neutron_radio1 = QRadioButton("Neutron Regions")
        data_type_options1.addWidget(self.entries_radio1)
        data_type_options1.addWidget(self.neutron_radio1)
        self.data_type1.setLayout(data_type_options1)

        data_type_label2 = QLabel("Seleccionar Datos a Graficar para Campaña 2:")
        self.data_type2 = QGroupBox()
        data_type_options2 = QHBoxLayout()
        self.entries_radio2 = QRadioButton("Entries")
        self.entries_radio2.setChecked(True)
        self.neutron_radio2 = QRadioButton("Neutron Regions")
        data_type_options2.addWidget(self.entries_radio2)
        data_type_options2.addWidget(self.neutron_radio2)
        self.data_type2.setLayout(data_type_options2)

        data_type_layout.addWidget(data_type_label1, 0, 0)
        data_type_layout.addWidget(self.data_type1, 0, 1)
        data_type_layout.addWidget(data_type_label2, 1, 0)
        data_type_layout.addWidget(self.data_type2, 1, 1)

        self.main_layout.addLayout(data_type_layout)

        # Selección de detectores
        detectors_label1 = QLabel("Selecciona los detectores para graficar en Campaña 1:")
        self.main_layout.addWidget(detectors_label1)

        self.detectors_widget1 = QWidget()
        self.detectors_layout1 = QVBoxLayout(self.detectors_widget1)
        self.main_layout.addWidget(self.detectors_widget1)

        detectors_label2 = QLabel("Selecciona los detectores para graficar en Campaña 2:")
        self.main_layout.addWidget(detectors_label2)

        self.detectors_widget2 = QWidget()
        self.detectors_layout2 = QVBoxLayout(self.detectors_widget2)
        self.main_layout.addWidget(self.detectors_widget2)

        self.update_detectors1(self.selected_campaign_plot1.currentText())
        self.update_detectors2(self.selected_campaign_plot2.currentText())

        # Selección de tiempo de acumulación
        accumulation_layout = QGridLayout()

        accumulation_label1 = QLabel("Selecciona tiempo promedio de acumulación para Campaña 1:")
        self.accumulation_time1 = QComboBox()
        accumulation_times = ["15 min", "30 min", "1 h", "2 h"]
        self.accumulation_time1.addItems(accumulation_times)

        accumulation_label2 = QLabel("Selecciona tiempo promedio de acumulación para Campaña 2:")
        self.accumulation_time2 = QComboBox()
        self.accumulation_time2.addItems(accumulation_times)

        accumulation_layout.addWidget(accumulation_label1, 0, 0)
        accumulation_layout.addWidget(self.accumulation_time1, 0, 1)
        accumulation_layout.addWidget(accumulation_label2, 1, 0)
        accumulation_layout.addWidget(self.accumulation_time2, 1, 1)

        self.main_layout.addLayout(accumulation_layout)

        # Botones de acción
        buttons_layout = QHBoxLayout()
        compare_plot_button = QPushButton("Graficar Selección")
        compare_plot_button.clicked.connect(self.compare_plot_data)
        save_compare_button = QPushButton("Guardar Selección")
        save_compare_button.clicked.connect(self.save_compare_plot)
        back_button = QPushButton("Regresar")
        back_button.setStyleSheet("background-color: #f44336; color: white;")
        back_button.clicked.connect(self.back)

        buttons_layout.addWidget(compare_plot_button)
        buttons_layout.addWidget(save_compare_button)
        buttons_layout.addWidget(back_button)

        self.main_layout.addLayout(buttons_layout)

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
            QComboBox {
                font-size: 16px;
            }
            QRadioButton {
                font-size: 16px;
            }
            QCheckBox {
                font-size: 16px;
            }
        """)

    def update_detectors1(self, campaign_name):
        # Limpiar layout de detectores
        for i in reversed(range(self.detectors_layout1.count())):
            widget = self.detectors_layout1.itemAt(i).widget()
            if widget is not None:
                widget.setParent(None)

        num_detectors = get_num_detectors(campaign_name)
        if num_detectors == 0:
            QMessageBox.warning(self, "Advertencia", f"La campaña '{campaign_name}' no tiene detectores definidos.")
            return

        # Usar el método create_detector_checkboxes
        detectors_widget, self.detector_checkboxes1, self.select_all_checkbox1 = create_detector_checkboxes(num_detectors)
        self.detectors_layout1.addWidget(detectors_widget)

    def update_detectors2(self, campaign_name):
        # Limpiar layout de detectores
        for i in reversed(range(self.detectors_layout2.count())):
            widget = self.detectors_layout2.itemAt(i).widget()
            if widget is not None:
                widget.setParent(None)

        num_detectors = get_num_detectors(campaign_name)
        if num_detectors == 0:
            QMessageBox.warning(self, "Advertencia", f"La campaña '{campaign_name}' no tiene detectores definidos.")
            return

        # Usar el método create_detector_checkboxes
        detectors_widget, self.detector_checkboxes2, self.select_all_checkbox2 = create_detector_checkboxes(num_detectors)
        self.detectors_layout2.addWidget(detectors_widget)

    def compare_plot_data(self):
        campaign_file1 = f"./data/{self.selected_campaign_plot1.currentText()}-CountingRate.csv"
        campaign_file2 = f"./data/{self.selected_campaign_plot2.currentText()}-CountingRate.csv"

        if not os.path.exists(campaign_file1):
            QMessageBox.critical(self, "Error", f"No se encontró el archivo para la campaña {self.selected_campaign_plot1.currentText()}")
            return
        if not os.path.exists(campaign_file2):
            QMessageBox.critical(self, "Error", f"No se encontró el archivo para la campaña {self.selected_campaign_plot2.currentText()}")
            return

        try:
            df1 = pd.read_csv(campaign_file1)
            df1['timestamp'] = pd.to_datetime(df1['timestamp'])
            df2 = pd.read_csv(campaign_file2)
            df2['timestamp'] = pd.to_datetime(df2['timestamp'])
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al leer los datos de las campañas: {e}")
            return

        selected_detectors1 = [i + 1 for i, cb in enumerate(self.detector_checkboxes1) if cb.isChecked()]
        selected_detectors2 = [i + 1 for i, cb in enumerate(self.detector_checkboxes2) if cb.isChecked()]

        if not selected_detectors1:
            QMessageBox.critical(self, "Error", "Debe seleccionar al menos un detector para la Campaña 1.")
            return
        if not selected_detectors2:
            QMessageBox.critical(self, "Error", "Debe seleccionar al menos un detector para la Campaña 2.")
            return

        data_type1 = "Neutron Regions" if self.neutron_radio1.isChecked() else "Entries"
        data_type2 = "Neutron Regions" if self.neutron_radio2.isChecked() else "Entries"
        accumulation_time1 = self.accumulation_time1.currentText()
        accumulation_time2 = self.accumulation_time2.currentText()

        time_deltas = {
            "15 min": timedelta(minutes=15),
            "30 min": timedelta(minutes=30),
            "1 h": timedelta(hours=1),
            "2 h": timedelta(hours=2)
        }
        accumulation_delta1 = time_deltas[accumulation_time1]
        accumulation_delta2 = time_deltas[accumulation_time2]

        plt.figure(figsize=(10, 6))
        # Procesar Campaña 1
        for detector in selected_detectors1:
            col_name = f"detector_{detector}_neutron_counts" if data_type1 == "Neutron Regions" else f"detector_{detector}_total_counts"
            if col_name not in df1.columns:
                QMessageBox.critical(self, "Error", f"El archivo de la Campaña 1 no contiene la columna {col_name}.")
                return

            df1['diff_counts'] = df1[col_name].diff().fillna(0)
            df1['diff_time'] = df1['timestamp'].diff().dt.total_seconds().fillna(1)
            df1['rate'] = df1['diff_counts'] / df1['diff_time']

            df_resampled1 = df1.set_index('timestamp').resample(accumulation_delta1).mean(numeric_only=True).reset_index()
            df_resampled1['rate'] = df_resampled1['rate'].interpolate()

            start_time = df_resampled1['timestamp'].iloc[0]
            df_resampled1['relative_time'] = (df_resampled1['timestamp'] - start_time).dt.total_seconds() / 3600  # En horas

            plt.plot(df_resampled1['relative_time'], df_resampled1['rate'], label=f'{self.selected_campaign_plot1.currentText()} - Detector {detector}')

        # Procesar Campaña 2
        for detector in selected_detectors2:
            col_name = f"detector_{detector}_neutron_counts" if data_type2 == "Neutron Regions" else f"detector_{detector}_total_counts"
            if col_name not in df2.columns:
                QMessageBox.critical(self, "Error", f"El archivo de la Campaña 2 no contiene la columna {col_name}.")
                return

            df2['diff_counts'] = df2[col_name].diff().fillna(0)
            df2['diff_time'] = df2['timestamp'].diff().dt.total_seconds().fillna(1)
            df2['rate'] = df2['diff_counts'] / df2['diff_time']

            df_resampled2 = df2.set_index('timestamp').resample(accumulation_delta2).mean(numeric_only=True).reset_index()
            df_resampled2['rate'] = df_resampled2['rate'].interpolate()

            start_time = df_resampled2['timestamp'].iloc[0]
            df_resampled2['relative_time'] = (df_resampled2['timestamp'] - start_time).dt.total_seconds() / 3600  # En horas

            plt.plot(df_resampled2['relative_time'], df_resampled2['rate'], label=f'{self.selected_campaign_plot2.currentText()} - Detector {detector}')

        plt.xlabel('Tiempo Relativo (horas)')
        plt.ylabel('Average Counting Rate s$^{-1}$')
        plt.legend()
        plt.title(f"Comparación de Counting Rate para {self.selected_campaign_plot1.currentText()} y {self.selected_campaign_plot2.currentText()}")
        plt.grid(True)
        plt.tight_layout()

        # Mostrar el gráfico en una ventana nueva
        self.show_plot()

    def show_plot(self):
        self.plot_window = QWidget()
        self.plot_window.setWindowTitle("Resultado del Gráfico de Comparación")
        plot_layout = QVBoxLayout()
        self.plot_window.setLayout(plot_layout)

        canvas = FigureCanvas(plt.gcf())
        plot_layout.addWidget(canvas)

        self.plot_window.resize(800, 600)
        self.plot_window.show()

    def save_compare_plot(self):
        # El código es similar a compare_plot_data, pero guarda el gráfico
        # y muestra un mensaje de confirmación
        self.compare_plot_data()  # Generamos el gráfico
        directory = "./Graficos/Comparacion"
        if not os.path.exists(directory):
            os.makedirs(directory)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        detectors_str1 = "_".join([f"Detector{detector}" for detector in [i + 1 for i, cb in enumerate(self.detector_checkboxes1) if cb.isChecked()]])
        detectors_str2 = "_".join([f"Detector{detector}" for detector in [i + 1 for i, cb in enumerate(self.detector_checkboxes2) if cb.isChecked()]])
        file_name = f"{directory}/{timestamp}_Comparacion_{self.selected_campaign_plot1.currentText()}_{self.selected_campaign_plot2.currentText()}_{detectors_str1}_{detectors_str2}.png"
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
    window = PlotComparison()
    window.show()
    sys.exit(app.exec())
