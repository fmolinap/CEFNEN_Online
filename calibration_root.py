from PySide6.QtWidgets import (
    QWidget, QLabel, QLineEdit, QPushButton, QMessageBox, QFileDialog, QTextEdit,
    QVBoxLayout, QHBoxLayout, QComboBox
)
from PySide6.QtCore import Qt
import ROOT
ROOT.gROOT.SetBatch(True)
import pandas as pd
import os
from datetime import datetime
import matplotlib
matplotlib.use('QtAgg')  # Asegurar el uso del backend adecuado
import matplotlib.pyplot as plt
from matplotlib.widgets import Cursor
from utils import get_existing_campaigns

class Calibration(QWidget):
    def __init__(self, back_callback=None):
        super().__init__()
        self.back_callback = back_callback
        self.histograms = {}
        self.results = []
        self.detector_index = 0
        self.channels_191 = []
        self.channels_764 = []
        self.detector_map = {}
        self.hist = None
        self.create_calibration_window()

    def create_calibration_window(self):
        self.setWindowTitle("Calibración desde Archivo ROOT")
        self.resize(800, 600)
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        title = QLabel("Calibración desde Archivo ROOT")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 20px; font-weight: bold;")
        main_layout.addWidget(title)

        # Selección de campaña
        campaign_layout = QHBoxLayout()
        campaign_label = QLabel("Seleccionar Campaña:")
        campaign_layout.addWidget(campaign_label)

        self.selected_campaign = QComboBox()
        self.campaigns = get_existing_campaigns()
        self.selected_campaign.addItems(self.campaigns)
        campaign_layout.addWidget(self.selected_campaign)
        main_layout.addLayout(campaign_layout)

        # Selección de archivo ROOT
        root_file_layout = QHBoxLayout()
        root_label = QLabel("Seleccionar Archivo ROOT:")
        root_file_layout.addWidget(root_label)

        self.root_path = QLineEdit()
        self.root_path.setReadOnly(True)
        root_file_layout.addWidget(self.root_path)

        browse_button = QPushButton("Browse")
        browse_button.clicked.connect(self.browse_root_file)
        root_file_layout.addWidget(browse_button)
        main_layout.addLayout(root_file_layout)

        # Botones de acción
        action_buttons_layout = QHBoxLayout()
        load_button = QPushButton("Cargar Histogramas")
        load_button.clicked.connect(self.load_histograms)
        action_buttons_layout.addWidget(load_button)

        back_button = QPushButton("Regresar")
        back_button.clicked.connect(self.back)
        action_buttons_layout.addWidget(back_button)
        main_layout.addLayout(action_buttons_layout)

        # Área de resultados
        self.result_text = QTextEdit()
        self.result_text.setReadOnly(True)
        main_layout.addWidget(self.result_text)

    def browse_root_file(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Seleccionar Archivo ROOT", "", "ROOT Files (*.root)")
        if file_name:
            self.root_path.setText(file_name)

    def load_histograms(self):
        file_path = self.root_path.text()
        if not file_path:
            QMessageBox.critical(self, "Error", "Por favor, seleccione un archivo ROOT.")
            return

        if not os.path.exists(file_path):
            QMessageBox.critical(self, "Error", "El archivo ROOT seleccionado no existe.")
            return

        self.histograms.clear()
        self.root_file = ROOT.TFile(file_path)
        keys = self.root_file.GetListOfKeys()
        for key in keys:
            obj = key.ReadObj()
            if obj.InheritsFrom("TH1"):
                self.histograms[key.GetName()] = obj

        if not self.histograms:
            QMessageBox.critical(self, "Error", "No se encontraron histogramas en el archivo ROOT seleccionado.")
            return

        self.result_text.clear()
        self.detector_map = {i+1: hist_name for i, hist_name in enumerate(self.histograms.keys())}
        self.detector_index = 0
        self.channels_191 = []
        self.channels_764 = []
        self.results = []
        self.calibrate_next_detector()

    def calibrate_next_detector(self):
        if self.detector_index >= len(self.detector_map):
            self.display_results()
            return

        detector_num = self.detector_index + 1
        hist_name = self.detector_map[detector_num]
        self.hist = self.histograms[hist_name]
        self.result_text.append(f"Calibrando Detector {detector_num}: {hist_name}")

        # Plot histogram
        fig, ax = plt.subplots()
        x = [self.hist.GetBinCenter(i) for i in range(1, self.hist.GetNbinsX() + 1)]
        y = [self.hist.GetBinContent(i) for i in range(1, self.hist.GetNbinsX() + 1)]
        ax.plot(x, y, label=hist_name)
        ax.set_title(f"Histogram for {hist_name}")
        ax.set_xlabel('Channel')
        ax.set_ylabel('Counts')
        cursor = Cursor(ax, useblit=True, color='red', linewidth=2)

        self.channel_clicks = []

        def onclick(event):
            if event.inaxes == ax:
                channel = int(event.xdata)
                self.channel_clicks.append(channel)
                if len(self.channel_clicks) == 1:
                    self.result_text.append(f"  Canal 191 keV: {channel}")
                    self.channels_191.append(channel)
                elif len(self.channel_clicks) == 2:
                    self.result_text.append(f"  Canal 764 keV: {channel}")
                    self.channels_764.append(channel)
                    fig.canvas.mpl_disconnect(cid)
                    plt.close(fig)
                    self.calculate_calibration()

        cid = fig.canvas.mpl_connect('button_press_event', onclick)
        plt.show()

    def calculate_calibration(self):
        energy1 = 191
        energy2 = 764
        channel1 = self.channels_191[self.detector_index]
        channel2 = self.channels_764[self.detector_index]
        slope = (energy2 - energy1) / (channel2 - channel1)
        offset = energy1 - slope * channel1
        detector_num = self.detector_index + 1
        hist_name = self.detector_map[detector_num]
        self.results.append((detector_num, hist_name, channel1, channel2, offset, slope))
        self.detector_index += 1
        self.channel_clicks = []
        self.calibrate_next_detector()

    def display_results(self):
        self.result_text.append("\nResultados de Calibración:")
        for detector, hist_name, channel1, channel2, offset, slope in self.results:
            self.result_text.append(f"Detector {detector} ({hist_name}):")
            self.result_text.append(f"  Canal 191 keV: {channel1}")
            self.result_text.append(f"  Canal 764 keV: {channel2}")
            self.result_text.append(f"  Offset: {offset}")
            self.result_text.append(f"  Slope: {slope}")
            self.result_text.append("")

        save_button = QPushButton("Guardar Calibración")
        save_button.clicked.connect(self.save_results)
        self.layout().addWidget(save_button)

    def save_results(self):
        campaign_name = self.selected_campaign.currentText()
        directory = f"./calibration/{campaign_name}"
        os.makedirs(directory, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_name = f"{directory}/{timestamp}_{campaign_name}_calibracion.csv"

        df = pd.DataFrame(self.results, columns=["Detector", "Histograma", "Channel_191", "Channel_764", "Offset", "Slope"])
        df.to_csv(file_name, index=False)

        QMessageBox.information(self, "Info", f"Calibración guardada como {file_name}")

    def back(self):
        if callable(self.back_callback):
            self.back_callback()
        else:
            print("Error: back_callback no es callable")
