from PySide6.QtWidgets import (
    QWidget, QLabel, QPushButton, QLineEdit, QVBoxLayout, QHBoxLayout,
    QApplication, QMessageBox, QComboBox, QTextEdit, QGridLayout,
    QFileDialog, QCheckBox, QDialog, QScrollArea
)
from PySide6.QtCore import Qt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.widgets import Cursor
import pandas as pd
import os
import re
from datetime import datetime
import matplotlib.pyplot as plt
import ROOT
ROOT.gROOT.SetBatch(True)
from utils import get_existing_campaigns, get_num_detectors


class MplCanvas(FigureCanvas):
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111)
        super().__init__(fig)


class RecalibrateRoot(QWidget):
    def __init__(self, back_callback=None):
        super().__init__()
        self.back_callback = back_callback
        self.histograms1 = {}
        self.histograms2 = {}
        self.results = []
        self.detector_index = 0
        self.detector_map = {}
        self.hist1 = None
        self.hist2 = None
        self.previous_calibration = None
        self.selected_detectors = []
        self.selected_campaign_name = ""
        self.selected_channels = []
        self.energy_labels = [191, 764]
        self.current_energy_index = 0
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
            self.selected_campaign_name = self.selected_campaign.currentText()
        else:
            self.selected_campaign.addItem("No hay campañas disponibles")
        self.selected_campaign.currentIndexChanged.connect(self.update_selected_campaign)
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

    def update_selected_campaign(self):
        self.selected_campaign_name = self.selected_campaign.currentText()

    def browse_root_file(self, root_path_var):
        # Obtener el nombre corto de la campaña seleccionada
        short_name = self.selected_campaign_name
        # Construir el directorio inicial
        initial_dir = os.path.abspath(os.path.join(".", "rootonline", short_name))
        # Crear el directorio si no existe
        if not os.path.exists(initial_dir):
            os.makedirs(initial_dir, exist_ok=True)
        file_path, _ = QFileDialog.getOpenFileName(self, "Seleccionar archivo ROOT", initial_dir, "ROOT files (*.root)")
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
        self.show_detector_selection()

    def load_previous_calibration(self):
        calibration_dir = f"./calibration/{self.selected_campaign_name}"
        if not os.path.exists(calibration_dir):
            self.previous_calibration = None
            return

        calibration_files = [f for f in os.listdir(calibration_dir) if f.endswith('.csv')]
        if calibration_files:
            # Expresión regular para extraer el timestamp del nombre del archivo
            pattern = re.compile(r'(\d{8}_\d{6})_' + re.escape(self.selected_campaign_name) + r'_calibracion\.csv$')
            files_with_timestamps = []
            for filename in calibration_files:
                match = pattern.match(filename)
                if match:
                    timestamp_str = match.group(1)
                    try:
                        timestamp = datetime.strptime(timestamp_str, '%Y%m%d_%H%M%S')
                        files_with_timestamps.append((timestamp, filename))
                    except ValueError:
                        pass  # Ignorar archivos con timestamp inválido
            if files_with_timestamps:
                # Ordenar los archivos por timestamp
                files_with_timestamps.sort(key=lambda x: x[0])
                latest_calibration_file = os.path.join(calibration_dir, files_with_timestamps[-1][1])
                # Leer el archivo CSV, eliminando espacios iniciales en los nombres de columnas
                self.previous_calibration = pd.read_csv(latest_calibration_file, skipinitialspace=True)
                # Eliminar espacios en los nombres de las columnas
                self.previous_calibration.columns = [col.strip() for col in self.previous_calibration.columns]
            else:
                self.previous_calibration = None
        else:
            self.previous_calibration = None

    def show_detector_selection(self):
        self.clear_layout(self.main_layout)

        selection_label = QLabel("Seleccione los Detectores a Recalibrar")
        selection_label.setAlignment(Qt.AlignCenter)
        selection_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        self.main_layout.addWidget(selection_label)

        detectors_layout = QVBoxLayout()
        self.detector_checkboxes = []
        num_detectors = get_num_detectors(self.selected_campaign_name)

        self.select_all_checkbox = QCheckBox("Seleccionar Todos")
        self.select_all_checkbox.toggled.connect(self.toggle_select_all)
        detectors_layout.addWidget(self.select_all_checkbox)

        for i in range(num_detectors):
            checkbox = QCheckBox(f"Detector {i + 1}")
            checkbox.toggled.connect(self.update_selected_detectors)
            detectors_layout.addWidget(checkbox)
            self.detector_checkboxes.append(checkbox)

        self.main_layout.addLayout(detectors_layout)

        # Botones
        buttons_layout = QHBoxLayout()
        accept_button = QPushButton("Aceptar Selección")
        accept_button.clicked.connect(self.show_mapping_interface)
        back_button = QPushButton("Regresar")
        back_button.clicked.connect(self.back)
        buttons_layout.addWidget(accept_button)
        buttons_layout.addWidget(back_button)
        self.main_layout.addLayout(buttons_layout)

        # Área de resultados
        self.result_text = QTextEdit()
        self.result_text.setReadOnly(True)
        self.main_layout.addWidget(self.result_text)

    def toggle_select_all(self, checked):
        for checkbox in self.detector_checkboxes:
            checkbox.setChecked(checked)
        # Actualizar la lista de detectores seleccionados
        self.update_selected_detectors()

    def update_selected_detectors(self):
        self.selected_detectors = [i for i, cb in enumerate(self.detector_checkboxes) if cb.isChecked()]
        # Actualizar el estado del checkbox "Seleccionar Todos"
        all_checked = all(cb.isChecked() for cb in self.detector_checkboxes) if self.detector_checkboxes else False
        self.select_all_checkbox.blockSignals(True)
        self.select_all_checkbox.setChecked(all_checked)
        self.select_all_checkbox.blockSignals(False)

    def show_mapping_interface(self):
        # Asegurarse de que la lista de detectores seleccionados está actualizada
        self.update_selected_detectors()
        if not self.selected_detectors:
            QMessageBox.warning(self, "Advertencia", "Debe seleccionar al menos un detector para recalibrar.")
            return

        self.clear_layout(self.main_layout)

        mapping_label = QLabel("Mapeo de Histogramas a Detectores")
        mapping_label.setAlignment(Qt.AlignCenter)
        mapping_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        self.main_layout.addWidget(mapping_label)

        # Crear un área de scroll para el mapeo
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        mapping_widget = QWidget()
        mapping_layout = QGridLayout(mapping_widget)
        scroll_area.setWidget(mapping_widget)
        self.main_layout.addWidget(scroll_area)

        self.detector_map = {}

        for idx, detector_num in enumerate(self.selected_detectors):
            detector_label = QLabel(f"Detector {detector_num + 1}")
            hist_name_combo = QComboBox()
            hist_name_combo.addItems(self.histograms1.keys())
            mapping_layout.addWidget(detector_label, idx, 0)
            mapping_layout.addWidget(hist_name_combo, idx, 1)
            self.detector_map[detector_num] = hist_name_combo

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
        if self.detector_index >= len(self.selected_detectors):
            self.display_results()
            return

        detector_num = self.selected_detectors[self.detector_index]
        hist_name = self.detector_map[detector_num].currentText()
        if hist_name not in self.histograms1 or hist_name not in self.histograms2:
            QMessageBox.critical(self, "Error", f"No se pudo cargar el histograma para el Detector {detector_num + 1}")
            return

        self.current_detector_num = detector_num
        self.hist1 = self.histograms1[hist_name]
        self.hist2 = self.histograms2[hist_name]
        self.current_hist_name = hist_name
        self.selected_channels = []
        self.current_energy_index = 0
        self.show_histogram(self.hist1, self.hist2, hist_name)

    def show_histogram(self, hist1, hist2, hist_name):
        if not hist1 or not hist2:
            QMessageBox.critical(self, "Error", f"El histograma {hist_name} no se pudo cargar correctamente.")
            return

        # Crear una ventana de diálogo para el histograma
        hist_dialog = QDialog(self)
        hist_dialog.setWindowTitle(f"Histograma {hist_name}")
        hist_dialog.resize(800, 600)
        layout = QVBoxLayout(hist_dialog)

        # Crear el canvas de Matplotlib
        canvas = MplCanvas(self, width=8, height=6, dpi=100)
        x = [hist1.GetBinCenter(i) for i in range(1, hist1.GetNbinsX() + 1)]
        y = [hist2.GetBinContent(i) - hist1.GetBinContent(i) for i in range(1, hist1.GetNbinsX() + 1)]
        canvas.axes.plot(x, y, label=f"Diferencia {hist_name}")
        canvas.axes.set_title(f"Diferencia {hist_name}")
        canvas.axes.set_xlabel('Canal')
        canvas.axes.set_ylabel('Cuentas')
        canvas.axes.legend()
        cursor = Cursor(canvas.axes, useblit=True, color='red', linewidth=1)
        layout.addWidget(canvas)

        # Botones de Zoom
        zoom_layout = QHBoxLayout()
        zoom_lower_label = QLabel("Límite inferior del zoom:")
        self.zoom_lower = QLineEdit()
        zoom_upper_label = QLabel("Límite superior del zoom:")
        self.zoom_upper = QLineEdit()
        apply_zoom_button = QPushButton("Aplicar Zoom")
        apply_zoom_button.clicked.connect(lambda: self.apply_zoom(canvas))
        zoom_layout.addWidget(zoom_lower_label)
        zoom_layout.addWidget(self.zoom_lower)
        zoom_layout.addWidget(zoom_upper_label)
        zoom_layout.addWidget(self.zoom_upper)
        zoom_layout.addWidget(apply_zoom_button)
        layout.addLayout(zoom_layout)

        # Conectar el evento de clic
        canvas.mpl_connect('button_press_event', lambda event: self.on_click(event, hist_name, canvas, hist_dialog))

        hist_dialog.exec()

    def apply_zoom(self, canvas):
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

        detector = self.current_detector_num + 1
        self.results.append({
            "Detector": detector,
            "Histograma": hist_name,
            "Channel_191": channel1,
            "Channel_764": channel2,
            "Offset": offset,
            "Slope": slope
        })

        self.result_text.append(f"Detector {detector} ({hist_name}):")
        self.result_text.append(f"  Canal 191 keV: {channel1:.2f}")
        self.result_text.append(f"  Canal 764 keV: {channel2:.2f}")
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
            result_text.append(f"  Canal 191 keV: {res['Channel_191']:.2f}")
            result_text.append(f"  Canal 764 keV: {res['Channel_764']:.2f}")
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
        directory = f"./calibration/{self.selected_campaign_name}"
        if not os.path.exists(directory):
            os.makedirs(directory)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        campaign_name = self.selected_campaign_name
        file_name = f"{directory}/{timestamp}_{campaign_name}_calibracion.csv"

        new_calibration_df = pd.DataFrame(self.results)

        # Si no se seleccionaron todos los detectores, combinar con la calibración anterior
        if self.previous_calibration is not None:
            # Verificar si 'Detector' y 'Histograma' existen en previous_calibration
            required_columns = ['Detector', 'Histograma', 'Channel_191', 'Channel_764', 'Offset', 'Slope']
            if all(column in self.previous_calibration.columns for column in required_columns):
                # Asegurarse de que 'Detector' es entero
                self.previous_calibration['Detector'] = self.previous_calibration['Detector'].astype(int)
                new_calibration_df['Detector'] = new_calibration_df['Detector'].astype(int)

                # Reemplazar las filas de los detectores recalibrados
                combined_df = self.previous_calibration.copy()
                combined_df.set_index('Detector', inplace=True)
                new_calibration_df.set_index('Detector', inplace=True)
                combined_df.update(new_calibration_df)
                combined_df.reset_index(inplace=True)
            else:
                QMessageBox.critical(self, "Error", "El archivo de calibración anterior no tiene las columnas necesarias para combinar.")
                return
        else:
            combined_df = new_calibration_df

        # Reordenar las columnas para mantener el formato
        combined_df = combined_df[['Detector', 'Histograma', 'Channel_191', 'Channel_764', 'Offset', 'Slope']]
        combined_df.sort_values(by='Detector', inplace=True)

        combined_df.to_csv(file_name, index=False)

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
