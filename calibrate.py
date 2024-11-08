from PySide6.QtWidgets import (
    QWidget, QLabel, QLineEdit, QPushButton, QMessageBox,
    QVBoxLayout, QHBoxLayout, QGridLayout, QComboBox, QTextEdit
)
from PySide6.QtCore import Qt
import pandas as pd
import os
from datetime import datetime
from utils import get_existing_campaigns, get_num_detectors

class Calibrate(QWidget):
    def __init__(self, parent=None, back_callback=None):
        super().__init__(parent)
        self.back_callback = back_callback
        self.channels_191 = []
        self.channels_764 = []
        self.selected_campaign = ""
        self.num_detectors = 0

        self.create_calibrate_window()

    def create_calibrate_window(self):
        self.setWindowTitle("Calibrate")
        self.resize(800, 600)

        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        # Título
        title = QLabel("Calibrate")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet(
            "font-size: 20px; font-weight: bold; background-color: #4CAF50; color: white; padding: 10px;"
        )
        main_layout.addWidget(title)

        # Selección de campaña
        campaigns_layout = QHBoxLayout()
        main_layout.addLayout(campaigns_layout)

        label_campaign = QLabel("Seleccionar Campaña:")
        campaigns_layout.addWidget(label_campaign)

        self.campaigns = get_existing_campaigns()
        self.campaign_combo = QComboBox()
        self.campaign_combo.addItems(self.campaigns)
        self.campaign_combo.setCurrentIndex(len(self.campaigns) - 1)
        if self.campaigns:
            self.selected_campaign = self.campaigns[0]
        campaigns_layout.addWidget(self.campaign_combo)
        self.campaign_combo.currentTextChanged.connect(self.update_detectors)

        # Marco de entradas
        self.input_frame = QWidget()
        self.input_layout = QGridLayout()
        self.input_frame.setLayout(self.input_layout)
        main_layout.addWidget(self.input_frame)

        # Área de resultados
        self.results_text = QTextEdit()
        self.results_text.setReadOnly(True)
        main_layout.addWidget(self.results_text)

        # Botones
        buttons_layout = QHBoxLayout()
        main_layout.addLayout(buttons_layout)

        calibrate_button = QPushButton("Calibrate")
        calibrate_button.setStyleSheet("background-color: #4CAF50; color: white;")
        calibrate_button.clicked.connect(self.calibrate)
        buttons_layout.addWidget(calibrate_button)

        back_button = QPushButton("Regresar")
        back_button.setStyleSheet("background-color: #f44336; color: white;")
        back_button.clicked.connect(self.back)
        buttons_layout.addWidget(back_button)

        self.update_detectors(self.selected_campaign)

    def update_detectors(self, campaign_name):
        self.clear_detectors()
        self.num_detectors = get_num_detectors(campaign_name)

        self.input_layout.addWidget(QLabel("Detector"), 0, 0)
        self.input_layout.addWidget(QLabel("Channel for 191 keV"), 0, 1)
        self.input_layout.addWidget(QLabel("Channel for 764 keV"), 0, 2)

        for i in range(self.num_detectors):
            detector_label = QLabel(f"Detector {i+1}")
            self.input_layout.addWidget(detector_label, i+1, 0)

            channel_191 = QLineEdit()
            self.input_layout.addWidget(channel_191, i+1, 1)
            self.channels_191.append(channel_191)

            channel_764 = QLineEdit()
            self.input_layout.addWidget(channel_764, i+1, 2)
            self.channels_764.append(channel_764)

    def clear_detectors(self):
        # Limpiar el layout de entradas
        while self.input_layout.count():
            item = self.input_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        self.channels_191 = []
        self.channels_764 = []

    def calibrate(self):
        energy1 = 191
        energy2 = 764
        results = []
        for i in range(self.num_detectors):
            try:
                channel1 = float(self.channels_191[i].text())
                channel2 = float(self.channels_764[i].text())
                slope = (energy2 - energy1) / (channel2 - channel1)
                offset = energy1 - slope * channel1
                results.append((i+1, channel1, channel2, offset, slope))
            except ValueError:
                QMessageBox.critical(
                    self, "Error",
                    f"Por favor, ingrese valores numéricos válidos para el Detector {i+1}."
                )
                return

        self.display_results(results)
        self.save_results(results)

    def display_results(self, results):
        self.results_text.clear()
        for detector, channel1, channel2, offset, slope in results:
            self.results_text.append(
                f"Detector {detector}: Offset = {offset:.2f}, Slope = {slope:.4f}"
            )

    def save_results(self, results):
        directory = "./calibration"
        if not os.path.exists(directory):
            os.makedirs(directory)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_name = f"{directory}/{timestamp}_energy_calibration.csv"

        df = pd.DataFrame(
            results,
            columns=["Detector", "Channel_191", "Channel_764", "Offset", "Slope"]
        )
        df.to_csv(file_name, index=False)

        QMessageBox.information(self, "Info", f"Calibración guardada como {file_name}")

    def back(self):
        if self.back_callback:
            self.back_callback()
