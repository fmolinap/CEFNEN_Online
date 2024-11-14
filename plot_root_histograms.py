# plot_root_histograms.py

from PySide6.QtWidgets import (
    QWidget, QLabel, QPushButton, QComboBox, QVBoxLayout, QHBoxLayout,
    QFileDialog, QMessageBox, QLineEdit, QScrollArea, QGridLayout, QDialog, QCheckBox
)
from PySide6.QtCore import Qt
import os
import ROOT
ROOT.gROOT.SetBatch(True)
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from datetime import datetime
from utils import get_existing_campaigns, get_num_detectors
import numpy as np
import pandas as pd

class PlotRootHistograms(QWidget):
    def __init__(self, back_callback=None):
        super().__init__()
        self.back_callback = back_callback
        self.histograms = {}
        self.canvas = None
        self.fig = None
        self.ax_arr = None
        self.zoom_applied = False
        self.detector_map = {}
        self.detector_histogram_map = {}
        self.root_file_path = ""
        self.selected_campaign_name = ""
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Visualización de Histogramas desde Archivo ROOT")
        # self.resize(1000, 800)  # Comentado para permitir ajuste automático

        self.main_layout = QVBoxLayout(self)
        self.setLayout(self.main_layout)

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
        campaign_layout.addWidget(campaign_label)
        campaign_layout.addWidget(self.selected_campaign)
        self.main_layout.addLayout(campaign_layout)

        # Checkbox para activar mapeo de histograma ChXX
        self.chxx_checkbox = QCheckBox("Medida en campaña (Histogramas llamados ChXX)")
        self.main_layout.addWidget(self.chxx_checkbox)

        # Botón para aceptar la campaña y cargar el mapeo
        accept_campaign_button = QPushButton("Aceptar Campaña")
        accept_campaign_button.clicked.connect(self.accept_campaign)
        self.main_layout.addWidget(accept_campaign_button)

        # Etiqueta para mostrar el archivo ROOT seleccionado
        self.selected_file_label = QLabel("")
        self.main_layout.addWidget(self.selected_file_label)

        # Selección de tipo de histograma (se actualizará después de cargar el archivo ROOT)
        hist_layout = QHBoxLayout()
        hist_label = QLabel("Seleccionar Sufijo (YY):")
        self.hist_type_combo = QComboBox()
        hist_layout.addWidget(hist_label)
        hist_layout.addWidget(self.hist_type_combo)
        self.main_layout.addLayout(hist_layout)

        # Botones de acción
        buttons_layout = QHBoxLayout()
        load_button = QPushButton("Cargar y Mostrar Histogramas")
        load_button.clicked.connect(self.load_and_show_histograms)
        back_button = QPushButton("Regresar")
        back_button.setStyleSheet("background-color: #f44336; color: white;")
        back_button.clicked.connect(self.back)
        buttons_layout.addWidget(load_button)
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
        """)

    def accept_campaign(self):
        short_name = self.selected_campaign.currentText()
        if not short_name or short_name == "No hay campañas disponibles":
            QMessageBox.critical(self, "Error", "Debe seleccionar una campaña.")
            return
        self.selected_campaign_name = short_name
        self.show_mapping_interface()

    def show_mapping_interface(self):
        # Seleccionar archivo ROOT
        initial_dir = os.path.abspath(os.path.join(".", "rootonline", self.selected_campaign_name))
        if not os.path.exists(initial_dir):
            os.makedirs(initial_dir, exist_ok=True)
        file_name, _ = QFileDialog.getOpenFileName(self, "Seleccionar archivo ROOT", initial_dir, "ROOT Files (*.root)")
        if file_name:
            self.root_file_path = file_name
            self.selected_file_label.setText(os.path.basename(self.root_file_path))
        else:
            self.root_file_path = ""
            return

        # Abrir el archivo ROOT
        root_file = ROOT.TFile(self.root_file_path)
        if root_file.IsZombie():
            QMessageBox.critical(self, "Error", "No se pudo abrir el archivo ROOT.")
            return

        # Obtener los histogramas y extraer nombres base y sufijos
        self.histograms = {}
        self.base_names = set()
        self.suffixes = set()
        for key in root_file.GetListOfKeys():
            hist_name = key.GetName()
            cycle = key.GetCycle()
            if cycle == 1:
                obj = key.ReadObj()
                if isinstance(obj, ROOT.TH1):
                    # Dividir el nombre del histograma en base_name y suffix
                    if self.chxx_checkbox.isChecked():
                        # Histograma nombrado como ChXX_YY
                        if '_' in hist_name:
                            base_name = hist_name.split('_')[0]
                            suffix = '_'.join(hist_name.split('_')[1:])
                        else:
                            base_name = hist_name
                            suffix = ''
                    else:
                        # Histograma con formato estándar
                        if '_' in hist_name:
                            base_name = '_'.join(hist_name.split('_')[:-1])
                            suffix = hist_name.split('_')[-1]
                        else:
                            base_name = hist_name
                            suffix = ''
                    # Guardar el histograma en un diccionario con clave (base_name, suffix)
                    self.histograms[(base_name, suffix)] = obj
                    # Añadir el base_name y suffix a los conjuntos
                    self.base_names.add(base_name)
                    self.suffixes.add(suffix)
        if not self.histograms:
            QMessageBox.critical(self, "Error", "No se encontraron histogramas en el archivo ROOT.")
            return

        # Actualizar la lista de sufijos
        self.hist_type_combo.clear()
        sorted_suffixes = sorted(self.suffixes)
        self.hist_type_combo.addItems(sorted_suffixes)

        # Crear interfaz de mapeo
        mapping_dialog = QDialog(self)
        mapping_dialog.setWindowTitle("Mapeo de Histogramas a Detectores")
        # mapping_dialog.resize(600, 400)  # Comentado para permitir ajuste automático
        layout = QVBoxLayout(mapping_dialog)

        # Cargar mapeo existente o crear uno nuevo
        self.detector_map = {}
        mapping_layout = QGridLayout()
        num_detectors = get_num_detectors(self.selected_campaign_name)

        # Base names disponibles
        base_name_list = sorted(self.base_names)

        for i in range(num_detectors):
            detector_label = QLabel(f"Detector {i + 1}")
            base_name_combo = QComboBox()
            base_name_combo.addItems(base_name_list)
            # Autoselección basada en ChXX
            if self.chxx_checkbox.isChecked():
                detector_number = i + 1
                if detector_number < 10:
                    expected_base = f"Ch0{detector_number}"
                else:
                    expected_base = f"Ch{detector_number}"
                if expected_base in base_name_list:
                    base_name_combo.setCurrentText(expected_base)
            mapping_layout.addWidget(detector_label, i, 0)
            mapping_layout.addWidget(base_name_combo, i, 1)
            self.detector_map[i] = base_name_combo

        # Cargar mapeo si existe
        mapping_file = f"./mapeo_calibrados/{self.selected_campaign_name}/Mapeo_histogramas_{self.selected_campaign_name}_plot_histograms_root.csv"
        if os.path.exists(mapping_file):
            self.load_mapping_from_file(mapping_file)

        layout.addLayout(mapping_layout)

        # Botones
        buttons_layout = QHBoxLayout()
        load_mapping_button = QPushButton("Cargar Mapeo")
        load_mapping_button.clicked.connect(self.load_mapping)
        buttons_layout.addWidget(load_mapping_button)

        save_mapping_button = QPushButton("Guardar Mapeo")
        save_mapping_button.clicked.connect(self.save_mapping)
        buttons_layout.addWidget(save_mapping_button)

        accept_button = QPushButton("Aceptar Mapeo")
        accept_button.clicked.connect(mapping_dialog.accept)
        buttons_layout.addWidget(accept_button)

        layout.addLayout(buttons_layout)

        mapping_dialog.exec()

        # Extraer el mapeo seleccionado antes de que los widgets sean eliminados
        self.detector_histogram_map = {}
        for i in range(len(self.detector_map)):
            base_name = self.detector_map[i].currentText()
            self.detector_histogram_map[i] = base_name

    def load_mapping(self):
        mapping_file, _ = QFileDialog.getOpenFileName(
            self,
            "Seleccionar archivo de mapeo",
            f"./mapeo_calibrados/{self.selected_campaign_name}",
            "CSV Files (*.csv)"
        )
        if mapping_file:
            self.load_mapping_from_file(mapping_file)

    def load_mapping_from_file(self, mapping_file):
        df_mapping = pd.read_csv(mapping_file)
        num_detectors = get_num_detectors(self.selected_campaign_name)
        for i in range(num_detectors):
            detector_key = f'Detector_{i+1}'
            if detector_key in df_mapping['Detector'].values:
                base_name = df_mapping.loc[df_mapping['Detector'] == detector_key, 'Histograma'].values[0]
                if base_name in self.base_names:
                    self.detector_map[i].setCurrentText(base_name)
                else:
                    QMessageBox.warning(self, "Advertencia", f"El histograma base '{base_name}' no se encontró en el archivo ROOT.")
            else:
                QMessageBox.warning(self, "Advertencia", f"No se encontró el mapeo para el {detector_key} en el archivo de mapeo.")

    def save_mapping(self):
        # Guardar el mapeo en un archivo CSV
        mapping_data = []
        for i in range(len(self.detector_map)):
            base_name = self.detector_map[i].currentText()
            mapping_data.append({
                'Detector': f'Detector_{i+1}',
                'Histograma': base_name
            })

        df_mapping = pd.DataFrame(mapping_data)
        save_dir = f"./mapeo_calibrados/{self.selected_campaign_name}"
        os.makedirs(save_dir, exist_ok=True)
        # Crear un archivo de mapeo especial para plot_histograms_root
        mapping_file = f"{save_dir}/Mapeo_histogramas_{self.selected_campaign_name}_plot_histograms_root.csv"
        # Verificar si el archivo ya existe
        if os.path.exists(mapping_file):
            QMessageBox.information(self, "Información", f"El archivo {mapping_file} ya existe y no será sobreescrito.")
            return
        df_mapping.to_csv(mapping_file, index=False)
        QMessageBox.information(self, "Éxito", f"Mapeo guardado en {mapping_file}")

    def load_and_show_histograms(self):
        if not self.root_file_path:
            QMessageBox.critical(self, "Error", "Debe seleccionar un archivo ROOT y cargar el mapeo.")
            return
        if not self.detector_histogram_map:
            QMessageBox.critical(self, "Error", "Debe cargar el mapeo de histogramas a detectores.")
            return

        self.hist_type = self.hist_type_combo.currentText()
        self.short_name = self.selected_campaign_name
        num_detectors = get_num_detectors(self.short_name)

        if num_detectors == 0:
            QMessageBox.critical(self, "Error", "El número de detectores para esta campaña es 0.")
            return

        # Abrir el archivo ROOT
        root_file = ROOT.TFile(self.root_file_path)
        if root_file.IsZombie():
            QMessageBox.critical(self, "Error", "No se pudo abrir el archivo ROOT.")
            return

        # Cargar histogramas usando el mapeo
        self.histograms_to_plot = []
        for i in range(num_detectors):
            base_name = self.detector_histogram_map.get(i)
            if not base_name:
                QMessageBox.warning(self, "Advertencia", f"No se encontró histograma para el Detector {i+1}.")
                continue
            # Construir el nombre del histograma según el sufijo seleccionado
            if self.hist_type:
                hist_name = f"{base_name}_{self.hist_type}"
            else:
                hist_name = base_name  # En caso de que no haya sufijo
            # Obtener el histograma
            hist = root_file.Get(hist_name)
            if not hist:
                QMessageBox.warning(self, "Advertencia", f"No se encontró el histograma {hist_name}.")
                continue
            self.histograms_to_plot.append((i+1, hist))

        if not self.histograms_to_plot:
            QMessageBox.critical(self, "Error", "No se encontraron histogramas para mostrar.")
            return

        # Preparar el canvas
        self.create_canvas()

    def create_canvas(self):
        num_histograms = len(self.histograms_to_plot)
        grid_size = int(np.ceil(np.sqrt(num_histograms)))

        # Crear una nueva ventana para el canvas
        self.canvas_window = QDialog(self)
        self.canvas_window.setWindowTitle("Visualización de Histogramas")
        # self.canvas_window.showFullScreen()  # Comentado para evitar pantalla completa

        # Ajustar el tamaño de la ventana al tamaño principal
        self.canvas_window.resize(self.width(), self.height())

        # Crear figura y ejes con mayor espacio entre subplots
        self.fig, self.ax_arr = plt.subplots(grid_size, grid_size, figsize=(16, 9))
        plt.subplots_adjust(wspace=0.4, hspace=0.6)  # Aumentar espacio entre subplots

        # Aplanar el arreglo de ejes para facilitar el acceso
        if num_histograms == 1:
            self.ax_arr = [self.ax_arr]
        else:
            self.ax_arr = self.ax_arr.flatten()

        for ax in self.ax_arr:
            ax.clear()

        # Graficar histogramas
        for idx, (detector_num, hist) in enumerate(self.histograms_to_plot):
            x = []
            y = []
            nbins = hist.GetNbinsX()
            for bin_num in range(1, nbins + 1):
                x.append(hist.GetBinCenter(bin_num))
                y.append(hist.GetBinContent(bin_num))
            self.ax_arr[idx].plot(x, y)
            self.ax_arr[idx].set_title(f"Detector {detector_num}", fontsize=14)
            self.ax_arr[idx].set_xlabel("Canal", fontsize=12)
            self.ax_arr[idx].set_ylabel("Cuentas", fontsize=12)

        # Ocultar subplots no utilizados
        for idx in range(len(self.histograms_to_plot), len(self.ax_arr)):
            self.fig.delaxes(self.ax_arr[idx])

        # Crear el widget del canvas
        self.canvas = FigureCanvas(self.fig)
        canvas_layout = QVBoxLayout()
        canvas_layout.addWidget(self.canvas)

        # Controles adicionales en el canvas_window
        controls_layout = QHBoxLayout()

        # Controles de Zoom
        zoom_layout = QHBoxLayout()
        zoom_label = QLabel("Zoom:")
        self.zoom_lower_in_canvas = QLineEdit()
        self.zoom_upper_in_canvas = QLineEdit()
        apply_zoom_button_in_canvas = QPushButton("Aplicar Zoom")
        apply_zoom_button_in_canvas.clicked.connect(self.apply_zoom_in_canvas)
        zoom_layout.addWidget(zoom_label)
        zoom_layout.addWidget(QLabel("Límite Inferior"))
        zoom_layout.addWidget(self.zoom_lower_in_canvas)
        zoom_layout.addWidget(QLabel("Límite Superior"))
        zoom_layout.addWidget(self.zoom_upper_in_canvas)
        zoom_layout.addWidget(apply_zoom_button_in_canvas)

        controls_layout.addLayout(zoom_layout)

        # Botón para guardar el canvas
        save_canvas_button_in_canvas = QPushButton("Guardar Canvas")
        save_canvas_button_in_canvas.clicked.connect(self.save_canvas_from_canvas_window)
        controls_layout.addWidget(save_canvas_button_in_canvas)

        # Botón para cerrar la ventana
        close_button = QPushButton("Cerrar")
        close_button.setFixedSize(100, 40)
        close_button.clicked.connect(self.canvas_window.close)
        controls_layout.addWidget(close_button)

        # Añadir los controles al layout del canvas
        canvas_layout.addLayout(controls_layout)

        self.canvas_window.setLayout(canvas_layout)
        self.zoom_applied = False

        self.canvas_window.exec()

    def apply_zoom_in_canvas(self):
        if not hasattr(self, 'canvas_window') or not self.canvas_window.isVisible():
            QMessageBox.critical(self.canvas_window, "Error", "No hay histogramas cargados o la ventana de canvas está cerrada.")
            return
        try:
            lower = float(self.zoom_lower_in_canvas.text())
            upper = float(self.zoom_upper_in_canvas.text())
            if lower >= upper:
                raise ValueError("El límite inferior debe ser menor que el superior.")
        except ValueError as ve:
            QMessageBox.critical(self.canvas_window, "Error", f"Valores de zoom inválidos: {ve}")
            return

        for ax in self.ax_arr[:len(self.histograms_to_plot)]:
            ax.set_xlim(lower, upper)
        self.canvas.draw()
        self.zoom_applied = True

    def save_canvas_from_canvas_window(self):
        if not hasattr(self, 'canvas'):
            QMessageBox.critical(self.canvas_window, "Error", "No hay canvas para guardar.")
            return
        directory = f"./Graficos/Canvas/{self.short_name}"
        os.makedirs(directory, exist_ok=True)
        # No incluir timestamp ni información de zoom en el nombre del archivo
        file_name = f"Canvas_{self.hist_type}.png"
        full_path = os.path.join(directory, file_name)
        self.fig.savefig(full_path)
        QMessageBox.information(self.canvas_window, "Éxito", f"Canvas guardado como {full_path}")

    def back(self):
        if callable(self.back_callback):
            self.back_callback()
        else:
            self.close()
