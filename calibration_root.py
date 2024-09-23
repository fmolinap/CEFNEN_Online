from PySide6.QtWidgets import (
    QWidget, QLabel, QPushButton, QLineEdit, QVBoxLayout, QHBoxLayout,
    QApplication, QMessageBox, QComboBox, QTextEdit, QGridLayout, QFileDialog,
    QDialog, QDialogButtonBox, QFormLayout
)
from PySide6.QtCore import Qt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.widgets import Cursor  # Asegúrate de importar Cursor
import pandas as pd
import os
from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib.widgets import Cursor  # Repetido, puedes eliminar uno de ellos
import ROOT
ROOT.gROOT.SetBatch(True)
from utils import get_existing_campaigns, get_num_detectors


class MplCanvas(FigureCanvas):
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111)
        super().__init__(fig)


class CalibrationRoot(QWidget):
    def __init__(self, back_callback=None):
        super().__init__()
        self.back_callback = back_callback
        self.histograms = {}
        self.results = []
        self.detector_index = 0
        self.detector_map = {}
        self.hist = None
        self.selected_channels = []
        self.energy_labels = [191, 764]  # Energías conocidas
        self.current_energy_index = 0
        self.selected_campaign_name = ""  # Inicializar la variable
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Calibración utilizando ROOT")
        self.resize(1000, 800)  # Aumentar el tamaño para acomodar gráficos

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

        # Selección de archivo ROOT
        file_layout = QHBoxLayout()
        file_label = QLabel("Seleccionar Archivo ROOT:")
        self.root_path = QLineEdit()
        browse_button = QPushButton("Examinar")
        browse_button.clicked.connect(self.browse_root_file)
        file_layout.addWidget(file_label)
        file_layout.addWidget(self.root_path)
        file_layout.addWidget(browse_button)
        self.main_layout.addLayout(file_layout)

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

    def browse_root_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Seleccionar archivo ROOT", "", "ROOT files (*.root)")
        if file_path:
            self.root_path.setText(file_path)

    def load_histograms(self):
        file_path = self.root_path.text()
        if not os.path.exists(file_path):
            QMessageBox.critical(self, "Error", "El archivo ROOT seleccionado no existe.")
            return

        self.root_file = ROOT.TFile(file_path)
        self.histograms = {key.GetName(): self.root_file.Get(key.GetName()) for key in self.root_file.GetListOfKeys() if key.GetName().endswith("_EFIR")}

        if not self.histograms:
            QMessageBox.critical(self, "Error", "No se encontraron histogramas con terminación '_EFIR' en el archivo ROOT.")
            return

        self.show_mapping_interface()

    def show_mapping_interface(self):
        # Almacenar el nombre de la campaña seleccionada antes de limpiar el layout
        self.selected_campaign_name = self.selected_campaign.currentText()

        self.clear_layout(self.main_layout)

        mapping_label = QLabel("Mapeo de Histogramas a Detectores")
        mapping_label.setAlignment(Qt.AlignCenter)
        mapping_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        self.main_layout.addWidget(mapping_label)

        mapping_layout = QGridLayout()
        num_detectors = get_num_detectors(self.selected_campaign_name)
        self.detector_map = {}

        for i in range(num_detectors):
            detector_label = QLabel(f"Detector {i + 1}")
            hist_name_combo = QComboBox()
            hist_name_combo.addItems(self.histograms.keys())
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
        if hist_name not in self.histograms:
            QMessageBox.critical(self, "Error", f"No se pudo cargar el histograma para el Detector {self.detector_index + 1}")
            return

        self.hist = self.histograms[hist_name]
        self.selected_channels = []
        self.current_energy_index = 0
        self.show_histogram(self.hist, hist_name)

    def show_histogram(self, hist, hist_name):
        if not hist:
            QMessageBox.critical(self, "Error", f"El histograma {hist_name} no se pudo cargar correctamente.")
            return

        # Crear una ventana de diálogo para el histograma
        hist_dialog = QDialog(self)
        hist_dialog.setWindowTitle(f"Histograma {hist_name}")
        hist_dialog.resize(800, 600)
        layout = QVBoxLayout(hist_dialog)

        # Crear el canvas de Matplotlib
        canvas = MplCanvas(self, width=5, height=4, dpi=100)
        x = [hist.GetBinCenter(i) for i in range(1, hist.GetNbinsX() + 1)]
        y = [hist.GetBinContent(i) for i in range(1, hist.GetNbinsX() + 1)]
        canvas.axes.plot(x, y, label=f"{hist_name}")
        canvas.axes.set_title(f"Histograma {hist_name}")
        canvas.axes.set_xlabel('Canal')
        canvas.axes.set_ylabel('Cuentas')
        canvas.axes.legend()
        cursor = Cursor(canvas.axes, useblit=True, color='red', linewidth=1)  # Asegúrate de que 'Cursor' está importado
        layout.addWidget(canvas)

        # Botones de Zoom
        zoom_layout = QHBoxLayout()
        zoom_lower_label = QLabel("Límite inferior del zoom:")
        self.zoom_lower = QLineEdit()
        zoom_upper_label = QLabel("Límite superior del zoom:")
        self.zoom_upper = QLineEdit()
        apply_zoom_button = QPushButton("Aplicar Zoom")
        apply_zoom_button.clicked.connect(lambda: self.apply_zoom(canvas, hist, hist_name))
        zoom_layout.addWidget(zoom_lower_label)
        zoom_layout.addWidget(self.zoom_lower)
        zoom_layout.addWidget(zoom_upper_label)
        zoom_layout.addWidget(self.zoom_upper)
        zoom_layout.addWidget(apply_zoom_button)
        layout.addLayout(zoom_layout)

        # Conectar el evento de clic
        canvas.mpl_connect('button_press_event', lambda event: self.on_click(event, hist_name, canvas, hist_dialog))

        hist_dialog.exec()

    def apply_zoom(self, canvas, hist, hist_name):
        try:
            lower = float(self.zoom_lower.text())
            upper = float(self.zoom_upper.text())
            if lower >= upper:
                raise ValueError("El límite inferior debe ser menor que el superior.")
        except ValueError as ve:
            QMessageBox.critical(self, "Error", f"Valores de zoom inválidos: {ve}")
            return

        canvas.axes.set_xlim(lower, upper)
        canvas.axes.figure.canvas.draw()

    def on_click(self, event, hist_name, canvas, hist_dialog):
        if event.inaxes:
            channel = event.xdata
            energy = self.energy_labels[self.current_energy_index]
            accept = self.confirm_channel_assignment(channel, energy)
            if accept:
                self.selected_channels.append(channel)
                # Dibujar una línea vertical en la posición seleccionada
                canvas.axes.axvline(x=channel, color='green', linestyle='--')
                canvas.axes.figure.canvas.draw()
                self.current_energy_index += 1
                if self.current_energy_index >= len(self.energy_labels):
                    hist_dialog.accept()
                    self.calculate_calibration(hist_name, *self.selected_channels)
            else:
                # Permitir que el usuario vuelva a seleccionar
                pass

    def confirm_channel_assignment(self, channel, energy):
        msg_box = QMessageBox(self)
        msg_box.setIcon(QMessageBox.Question)
        msg_box.setWindowTitle("Confirmar asignación")
        msg_box.setText(f"¿Deseas asignar el canal {channel:.2f} a la energía {energy} keV?")
        msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        result = msg_box.exec()

        if result == QMessageBox.Yes:
            return True
        else:
            return False

    def calculate_calibration(self, hist_name, channel1, channel2):
        energy1 = self.energy_labels[0]
        energy2 = self.energy_labels[1]
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
        self.result_text.append(f"  Canal {energy1} keV: {channel1:.2f}")
        self.result_text.append(f"  Canal {energy2} keV: {channel2:.2f}")
        self.result_text.append(f"  Offset: {offset:.4f}")
        self.result_text.append(f"  Slope: {slope:.4f}\n")

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
            result_text.append(f"  Canal {self.energy_labels[0]} keV: {res['Channel_191']:.2f}")
            result_text.append(f"  Canal {self.energy_labels[1]} keV: {res['Channel_764']:.2f}")
            result_text.append(f"  Offset: {res['Offset']:.4f}")
            result_text.append(f"  Slope: {res['Slope']:.4f}\n")

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
        try:
            directory = f"./calibration/{self.selected_campaign_name}"
            if not os.path.exists(directory):
                os.makedirs(directory)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            campaign_name = self.selected_campaign_name
            file_name = f"{directory}/{timestamp}_{campaign_name}_calibracion.csv"

            df = pd.DataFrame(self.results)
            df.to_csv(file_name, index=False)

            QMessageBox.information(self, "Éxito", f"Calibración guardada como {file_name}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al guardar la calibración: {str(e)}")

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
    window = CalibrationRoot()
    window.show()
    sys.exit(app.exec())
