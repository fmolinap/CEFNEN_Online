from PySide6.QtWidgets import (
    QWidget, QLabel, QPushButton, QLineEdit, QVBoxLayout, QHBoxLayout,
    QApplication, QMessageBox, QComboBox, QTextEdit, QGridLayout, QGroupBox
)
from PySide6.QtCore import Qt
import pandas as pd
import os
from datetime import datetime
from utils import get_existing_campaigns, get_num_detectors


class Recalibrate(QWidget):
    def __init__(self, back_callback=None):
        super().__init__()
        self.back_callback = back_callback
        self.channels_191 = []
        self.channels_764 = []
        self.selected_campaign = None
        self.num_detectors = 0
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Recalibración de Detectores")
        self.resize(800, 600)

        # Layout principal
        self.main_layout = QVBoxLayout(self)
        self.setLayout(self.main_layout)

        # Título
        title = QLabel("Recalibración de Detectores")
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
            self.selected_campaign.currentTextChanged.connect(self.update_detectors)
            self.selected_campaign.setCurrentIndex(0)
            self.update_detectors(self.selected_campaign.currentText())
        else:
            self.selected_campaign.addItem("No hay campañas disponibles")
        campaign_layout.addWidget(campaign_label)
        campaign_layout.addWidget(self.selected_campaign)
        self.main_layout.addLayout(campaign_layout)

        # Cuadro de entrada de datos
        self.input_group = QGroupBox("Valores Actuales para la Recalibración")
        self.input_layout = QGridLayout()
        self.input_group.setLayout(self.input_layout)
        self.main_layout.addWidget(self.input_group)

        # Área de resultados
        self.results_text = QTextEdit()
        self.results_text.setReadOnly(True)
        self.main_layout.addWidget(self.results_text)

        # Botones de acción
        buttons_layout = QHBoxLayout()
        recalibrate_button = QPushButton("Recalibrar")
        recalibrate_button.clicked.connect(self.recalibrate)
        back_button = QPushButton("Regresar")
        back_button.clicked.connect(self.back)
        buttons_layout.addWidget(recalibrate_button)
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
            QLineEdit, QComboBox {
                font-size: 16px;
            }
            QTextEdit {
                font-size: 14px;
            }
        """)

    def update_detectors(self, campaign_name):
        # Limpiar el layout de entrada
        for i in reversed(range(self.input_layout.count())):
            widget = self.input_layout.itemAt(i).widget()
            if widget is not None:
                widget.setParent(None)

        self.channels_191 = []
        self.channels_764 = []
        self.num_detectors = get_num_detectors(campaign_name)

        # Etiquetas de encabezado
        self.input_layout.addWidget(QLabel("Detector"), 0, 0)
        self.input_layout.addWidget(QLabel("Valor Actual para 191 keV"), 0, 1)
        self.input_layout.addWidget(QLabel("Valor Actual para 764 keV"), 0, 2)

        # Campos de entrada para cada detector
        for i in range(self.num_detectors):
            detector_label = QLabel(f"Detector {i + 1}")
            detector_label.setAlignment(Qt.AlignCenter)
            channel_191 = QLineEdit()
            channel_764 = QLineEdit()
            self.channels_191.append(channel_191)
            self.channels_764.append(channel_764)

            self.input_layout.addWidget(detector_label, i + 1, 0)
            self.input_layout.addWidget(channel_191, i + 1, 1)
            self.input_layout.addWidget(channel_764, i + 1, 2)

    def recalibrate(self):
        energy1 = 191
        energy2 = 764
        results = []
        try:
            calibration_files = [f for f in os.listdir('./calibration') if f.endswith('_energy_calibration.csv')]
            if not calibration_files:
                QMessageBox.critical(self, "Error", "No se encontraron archivos de calibración previos.")
                return
            latest_calibration_file = max(calibration_files, key=lambda f: os.path.getctime(os.path.join('./calibration', f)))
            df_calibration = pd.read_csv(f'./calibration/{latest_calibration_file}')
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo encontrar el archivo de calibración más reciente: {e}")
            return

        for i in range(self.num_detectors):
            try:
                actual_value_191 = float(self.channels_191[i].text())
                actual_value_764 = float(self.channels_764[i].text())
                original_channel_191 = df_calibration.loc[i, 'Channel_191']
                original_channel_764 = df_calibration.loc[i, 'Channel_764']
                slope = (actual_value_764 - actual_value_191) / (original_channel_764 - original_channel_191)
                offset = actual_value_191 - slope * original_channel_191
                results.append({
                    "Detector": i + 1,
                    "Actual_191": actual_value_191,
                    "Actual_764": actual_value_764,
                    "Offset": offset,
                    "Slope": slope
                })
            except ValueError:
                QMessageBox.critical(self, "Error", f"Por favor, ingrese valores numéricos válidos para el Detector {i + 1}.")
                return
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Ocurrió un error con el Detector {i + 1}: {e}")
                return

        self.display_results(results)
        self.save_results(results)

    def display_results(self, results):
        self.results_text.clear()
        for res in results:
            self.results_text.append(
                f"Detector {res['Detector']}: Offset = {res['Offset']:.2f}, Slope = {res['Slope']:.4f}"
            )

    def save_results(self, results):
        directory = "./calibration"
        if not os.path.exists(directory):
            os.makedirs(directory)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_name = f"{directory}/{timestamp}_recalibration.csv"

        df = pd.DataFrame(results)
        df.to_csv(file_name, index=False)

        QMessageBox.information(self, "Éxito", f"Recalibración guardada como {file_name}")

    def back(self):
        if callable(self.back_callback):
            self.back_callback()
        else:
            self.close()


if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    window = Recalibrate()
    window.show()
    sys.exit(app.exec())
