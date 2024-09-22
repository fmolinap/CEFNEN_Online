from PySide6.QtWidgets import (
    QWidget, QLabel, QPushButton, QLineEdit, QVBoxLayout, QHBoxLayout,
    QApplication, QMessageBox, QComboBox, QTextEdit, QGridLayout, QFileDialog,
    QCheckBox, QDialog, QDialogButtonBox, QSpinBox, QGroupBox, QFormLayout
)
from PySide6.QtCore import Qt
import pandas as pd
import os
from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib.widgets import Cursor
import ROOT
ROOT.gROOT.SetBatch(True)
from utils import get_existing_campaigns, get_num_detectors


class RecalibrateRoot(QWidget):
    def __init__(self, back_callback=None):
        super().__init__()
        self.back_callback = back_callback
        self.histograms1 = {}
        self.histograms2 = {}
        self.results = []
        self.detector_index = 0
        self.channels_191 = []
        self.channels_764 = []
        self.detector_map = {}
        self.hist1 = None
        self.hist2 = None
        self.previous_calibration = None
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Recalibración utilizando ROOT")
        self.resize(800, 600)

        # Layout principal
        self.main_layout = QVBoxLayout(self)
        self.setLayout(self.main_layout)

        # Selección de campaña
        campaign_layout = QHBoxLayout()
        campaign_label = QLabel("Seleccionar Campaña:")
        self.selected_campaign = QComboBox()
        self.campaigns = get_existing_campaigns()
        if self.campaigns:
            self.selected_campaign.addItems(self.campaigns)
        else:
            self.selected_campaign.addItem("No hay campañas disponibles")
        campaign_layout.addWidget(campaign_label)
        campaign_layout.addWidget(self.selected_campaign)
        self.main_layout.addLayout(campaign_layout)

        # Selección de archivos ROOT
        file_layout1 = QHBoxLayout()
        file_label1 = QLabel("Seleccionar Archivo ROOT 1 (más antiguo):")
        self.root_path1 = QLineEdit()
        browse_button1 = QPushButton("Examinar")
        browse_button1.clicked.connect(lambda: self.browse_root_file(self.root_path1))
        file_layout1.addWidget(file_label1)
        file_layout1.addWidget(self.root_path1)
        file_layout1.addWidget(browse_button1)
        self.main_layout.addLayout(file_layout1)

        file_layout2 = QHBoxLayout()
        file_label2 = QLabel("Seleccionar Archivo ROOT 2 (más reciente):")
        self.root_path2 = QLineEdit()
        browse_button2 = QPushButton("Examinar")
        browse_button2.clicked.connect(lambda: self.browse_root_file(self.root_path2))
        file_layout2.addWidget(file_label2)
        file_layout2.addWidget(self.root_path2)
        file_layout2.addWidget(browse_button2)
        self.main_layout.addLayout(file_layout2)

        # Botones de acción
        buttons_layout = QHBoxLayout()
        load_button = QPushButton("Cargar Histogramas")
        load_button.clicked.connect(self.load_histograms)
        back_button = QPushButton("Regresar")
        back_button.clicked.connect(self.back)
        buttons_layout.addWidget(load_button)
        buttons_layout.addWidget(back_button)
        self.main_layout.addLayout(buttons_layout)

        # Área de resultados
        self.result_text = QTextEdit()
        self.result_text.setReadOnly(True)
        self.main_layout.addWidget(self.result_text)

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

    def browse_root_file(self, root_path_var):
        file_path, _ = QFileDialog.getOpenFileName(self, "Seleccionar archivo ROOT", "", "ROOT files (*.root)")
        if file_path:
            root_path_var.setText(file_path)

    def load_histograms(self):
        file_path1 = self.root_path1.text()
        file_path2 = self.root_path2.text()
        if not os.path.exists(file_path1) or not os.path.exists(file_path2):
            QMessageBox.critical(self, "Error", "Uno o ambos archivos ROOT seleccionados no existen.")
            return

        self.root_file1 = ROOT.TFile(file_path1)
        self.root_file2 = ROOT.TFile(file_path2)
        self.histograms1 = {key.GetName(): self.root_file1.Get(key.GetName()) for key in self.root_file1.GetListOfKeys() if key.GetName().endswith("_EFIR")}
        self.histograms2 = {key.GetName(): self.root_file2.Get(key.GetName()) for key in self.root_file2.GetListOfKeys() if key.GetName().endswith("_EFIR")}

        if not self.histograms1 or not self.histograms2:
            QMessageBox.critical(self, "Error", "No se encontraron histogramas con terminación '_EFIR' en uno o ambos archivos ROOT.")
            return

        self.load_previous_calibration()
        self.show_mapping_interface()

    def load_previous_calibration(self):
        calibration_dir = f"./calibration/{self.selected_campaign.currentText()}"
        if not os.path.exists(calibration_dir):
            return

        calibration_files = sorted([f for f in os.listdir(calibration_dir) if f.endswith('.csv')])
        if calibration_files:
            latest_calibration_file = os.path.join(calibration_dir, calibration_files[-1])
            self.previous_calibration = pd.read_csv(latest_calibration_file)

    def show_mapping_interface(self):
        self.clear_layout(self.main_layout)

        mapping_label = QLabel("Mapeo de Histogramas a Detectores")
        mapping_label.setAlignment(Qt.AlignCenter)
        mapping_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        self.main_layout.addWidget(mapping_label)

        mapping_layout = QGridLayout()
        num_detectors = get_num_detectors(self.selected_campaign.currentText())
        self.detector_map = {}

        for i in range(num_detectors):
            detector_label = QLabel(f"Detector {i + 1}")
            hist_name_combo = QComboBox()
            hist_name_combo.addItems(self.histograms1.keys())
            mapping_layout.addWidget(detector_label, i, 0)
            mapping_layout.addWidget(hist_name_combo, i, 1)
            self.detector_map[i] = hist_name_combo

        self.main_layout.addLayout(mapping_layout)

        # Botones
        buttons_layout = QHBoxLayout()
        accept_button = QPushButton("Aceptar Mapeo")
        accept_button.clicked.connect(self.start_calibration_sequence)
        back_button = QPushButton("Regresar")
        back_button.clicked.connect(self.back)
        buttons_layout.addWidget(accept_button)
        buttons_layout.addWidget(back_button)
        self.main_layout.addLayout(buttons_layout)

        # Área de resultados
        self.result_text = QTextEdit()
        self.result_text.setReadOnly(True)
        self.main_layout.addWidget(self.result_text)

    def start_calibration_sequence(self):
        self.detector_index = 0
        self.results = []
        self.calibrate_next_detector()

    def calibrate_next_detector(self):
        if self.detector_index >= len(self.detector_map):
            self.display_results()
            return

        hist_name = self.detector_map[self.detector_index].currentText()
        if hist_name not in self.histograms1 or hist_name not in self.histograms2:
            QMessageBox.critical(self, "Error", f"No se pudo cargar el histograma para el Detector {self.detector_index + 1}")
            return

        self.hist1 = self.histograms1[hist_name]
        self.hist2 = self.histograms2[hist_name]
        self.show_histogram(self.hist1, self.hist2, hist_name)

    def show_histogram(self, hist1, hist2, hist_name):
        if not hist1 or not hist2:
            QMessageBox.critical(self, "Error", f"El histograma {hist_name} no se pudo cargar correctamente.")
            return

        x = [hist1.GetBinCenter(i) for i in range(1, hist1.GetNbinsX() + 1)]
        y = [hist2.GetBinContent(i) - hist1.GetBinContent(i) for i in range(1, hist1.GetNbinsX() + 1)]

        fig, ax = plt.subplots()
        ax.plot(x, y, label=f"Diferencia {hist_name}")
        cursor = Cursor(ax, useblit=True, color='red', linewidth=1)
        ax.set_title(f"Diferencia {hist_name}")
        ax.set_xlabel('Canal')
        ax.set_ylabel('Cuentas')
        ax.legend()
        plt.show()

        self.show_zoom_interface(hist1, hist2, hist_name)

    def show_zoom_interface(self, hist1, hist2, hist_name):
        zoom_dialog = QDialog(self)
        zoom_dialog.setWindowTitle(f"Zoom para {hist_name}")
        layout = QVBoxLayout(zoom_dialog)

        instructions = QLabel(f"Espectro para {hist_name}")
        instructions.setAlignment(Qt.AlignCenter)
        layout.addWidget(instructions)

        show_spectrum_button = QPushButton("Mostrar Espectro")
        show_spectrum_button.clicked.connect(lambda: self.plot_histogram(hist1, hist2, hist_name))
        layout.addWidget(show_spectrum_button)

        form_layout = QFormLayout()
        self.zoom_lower = QLineEdit()
        self.zoom_upper = QLineEdit()
        form_layout.addRow("Límite inferior del zoom:", self.zoom_lower)
        form_layout.addRow("Límite superior del zoom:", self.zoom_upper)
        layout.addLayout(form_layout)

        apply_zoom_button = QPushButton("Aplicar Zoom")
        apply_zoom_button.clicked.connect(lambda: self.apply_zoom(zoom_dialog, hist1, hist2, hist_name))
        layout.addWidget(apply_zoom_button)

        zoom_dialog.exec()

    def plot_histogram(self, hist1, hist2, hist_name):
        x = [hist1.GetBinCenter(i) for i in range(1, hist1.GetNbinsX() + 1)]
        y1 = [hist1.GetBinContent(i) for i in range(1, hist1.GetNbinsX() + 1)]
        y2 = [hist2.GetBinContent(i) for i in range(1, hist2.GetNbinsX() + 1)]

        fig, ax = plt.subplots()
        ax.plot(x, y1, label=f"Histograma 1 - {hist_name}")
        ax.plot(x, y2, label=f"Histograma 2 - {hist_name}")
        cursor = Cursor(ax, useblit=True, color='red', linewidth=1)
        ax.set_title(f"Espectros {hist_name}")
        ax.set_xlabel('Canal')
        ax.set_ylabel('Cuentas')
        ax.legend()
        plt.show()

    def apply_zoom(self, zoom_dialog, hist1, hist2, hist_name):
        try:
            lower = int(self.zoom_lower.text())
            upper = int(self.zoom_upper.text())
        except ValueError:
            QMessageBox.critical(self, "Error", "Por favor, ingrese valores numéricos válidos para los límites de zoom.")
            return
        plt.close('all')
        zoom_dialog.close()

        self.show_zoomed_histogram(hist1, hist2, hist_name, lower, upper)

    def show_zoomed_histogram(self, hist1, hist2, hist_name, lower, upper):
        x = [hist1.GetBinCenter(i) for i in range(1, hist1.GetNbinsX() + 1)]
        y = [hist2.GetBinContent(i) - hist1.GetBinContent(i) for i in range(1, hist1.GetNbinsX() + 1)]

        fig, ax = plt.subplots()
        ax.plot(x, y, label=f"Diferencia {hist_name}")
        ax.set_xlim(lower, upper)

        # Plot previous calibration lines if available
        if self.previous_calibration is not None:
            prev_calib = self.previous_calibration[self.previous_calibration['Histograma'] == hist_name]
            if not prev_calib.empty:
                channel_191 = prev_calib['Channel_191'].values[0]
                channel_764 = prev_calib['Channel_764'].values[0]
                ax.axvline(x=channel_191, color='blue', linestyle='--', label='Prev 191 keV')
                ax.axvline(x=channel_764, color='green', linestyle='--', label='Prev 764 keV')

        cursor = Cursor(ax, useblit=True, color='red', linewidth=1)
        ax.set_title(f"Diferencia {hist_name}")
        ax.set_xlabel('Canal')
        ax.set_ylabel('Cuentas')
        ax.legend()
        plt.show()

        self.ask_for_channel_positions(hist_name)

    def ask_for_channel_positions(self, hist_name):
        position_dialog = QDialog(self)
        position_dialog.setWindowTitle(f"Seleccionar canales para {hist_name}")
        layout = QVBoxLayout(position_dialog)

        instructions = QLabel(f"Canales para {hist_name}:")
        instructions.setAlignment(Qt.AlignCenter)
        layout.addWidget(instructions)

        form_layout = QFormLayout()
        self.channel_191_entry = QLineEdit()
        self.channel_764_entry = QLineEdit()
        form_layout.addRow("Canal para 191 keV:", self.channel_191_entry)
        form_layout.addRow("Canal para 764 keV:", self.channel_764_entry)
        layout.addLayout(form_layout)

        self.keep_prev_calibration = QCheckBox("Mantener Calibración Anterior")
        if self.previous_calibration is not None:
            prev_calib = self.previous_calibration[self.previous_calibration['Histograma'] == hist_name]
            if not prev_calib.empty:
                self.keep_prev_calibration.setEnabled(True)
            else:
                self.keep_prev_calibration.setEnabled(False)
        else:
            self.keep_prev_calibration.setEnabled(False)
        layout.addWidget(self.keep_prev_calibration)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(lambda: self.accept_channels(position_dialog, hist_name))
        buttons.rejected.connect(position_dialog.reject)
        layout.addWidget(buttons)

        position_dialog.exec()

    def accept_channels(self, position_dialog, hist_name):
        try:
            if self.keep_prev_calibration.isChecked() and self.previous_calibration is not None:
                prev_calib = self.previous_calibration[self.previous_calibration['Histograma'] == hist_name]
                if not prev_calib.empty:
                    channel1 = prev_calib['Channel_191'].values[0]
                    channel2 = prev_calib['Channel_764'].values[0]
                else:
                    raise ValueError("No previous calibration data found.")
            else:
                channel1 = float(self.channel_191_entry.text())
                channel2 = float(self.channel_764_entry.text())

            energy1 = 191
            energy2 = 764
            slope = (energy2 - energy1) / (channel2 - channel1)
            offset = energy1 - slope * channel1

            detector = self.detector_index + 1
            self.results.append({
                "Detector": detector,
                "Histograma": hist_name,
                "Channel_191": channel1,
                "Channel_764": channel2,
                "Offset": offset,
                "Slope": slope
            })

            self.result_text.append(f"Detector {detector} ({hist_name}):")
            self.result_text.append(f"  Canal 191 keV: {channel1}")
            self.result_text.append(f"  Canal 764 keV: {channel2}")
            self.result_text.append(f"  Offset: {offset}")
            self.result_text.append(f"  Slope: {slope}\n")

        except ValueError:
            QMessageBox.critical(self, "Error", "Por favor, ingrese valores numéricos válidos para los canales.")
            return

        plt.close('all')
        position_dialog.accept()

        self.detector_index += 1
        self.calibrate_next_detector()

    def display_results(self):
        self.clear_layout(self.main_layout)

        result_label = QLabel("Resultados de Calibración")
        result_label.setAlignment(Qt.AlignCenter)
        result_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        self.main_layout.addWidget(result_label)

        result_text = QTextEdit()
        result_text.setReadOnly(True)
        self.main_layout.addWidget(result_text)

        for res in self.results:
            result_text.append(f"Detector {res['Detector']} ({res['Histograma']}):")
            result_text.append(f"  Canal 191 keV: {res['Channel_191']}")
            result_text.append(f"  Canal 764 keV: {res['Channel_764']}")
            result_text.append(f"  Offset: {res['Offset']}")
            result_text.append(f"  Slope: {res['Slope']}\n")

        # Botones
        buttons_layout = QHBoxLayout()
        save_button = QPushButton("Guardar Calibración")
        save_button.clicked.connect(self.save_results)
        back_button = QPushButton("Regresar")
        back_button.clicked.connect(self.back)
        buttons_layout.addWidget(save_button)
        buttons_layout.addWidget(back_button)
        self.main_layout.addLayout(buttons_layout)

    def save_results(self):
        directory = f"./calibration/{self.selected_campaign.currentText()}"
        if not os.path.exists(directory):
            os.makedirs(directory)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        campaign_name = self.selected_campaign.currentText()
        file_name = f"{directory}/{timestamp}_{campaign_name}_calibracion.csv"

        df = pd.DataFrame(self.results)
        df.to_csv(file_name, index=False)

        QMessageBox.information(self, "Éxito", f"Calibración guardada como {file_name}")

    def clear_layout(self, layout):
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
            elif child.layout():
                self.clear_layout(child.layout())

    def back(self):
        if callable(self.back_callback):
            self.back_callback()
        else:
            self.close()


if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    window = RecalibrateRoot()
    window.show()
    sys.exit(app.exec())
