# agregar_datos.py

from PySide6.QtWidgets import (
    QWidget, QLabel, QLineEdit, QPushButton, QMessageBox, QVBoxLayout, QHBoxLayout,
    QComboBox, QGridLayout, QTabWidget, QFileDialog, QDialog, QTableWidget, QTableWidgetItem, QTextEdit, QScrollArea
)
from PySide6.QtCore import Qt
import pandas as pd
import os
from datetime import datetime
import sys
import subprocess
import ROOT
ROOT.gROOT.SetBatch(True)
from utils import (
    get_existing_campaigns, get_num_detectors, save_detector_data, process_root_file, save_results_to_csv, get_campaign_info
)

class AgregarDatos(QWidget):
    def __init__(self, back_callback=None):
        super().__init__()
        self.back_callback = back_callback
        self.root_file_path = ""
        self.detector_entries = []
        self.detector_map = {}
        self.detector_histogram_map = {}  # Almacenar el mapeo aquí
        self.histograms = {}
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Agregar Datos a Campaña Existente")
        # self.setFixedSize(900, 700)  # Ventana de tamaño fijo (eliminado para ajustar al espacio disponible)

        main_layout = QVBoxLayout(self)
        self.setLayout(main_layout)

        title = QLabel("Agregar Datos a Campaña Existente", self)
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 24px; font-weight: bold;")
        main_layout.addWidget(title)

        subtitle = QLabel(
            "Selecciona una campaña existente y agrega datos manualmente o desde un archivo ROOT.",
            self)
        subtitle.setWordWrap(True)
        subtitle.setStyleSheet("font-size: 14px;")
        main_layout.addWidget(subtitle)

        # Mensaje o instrucciones adicionales
        instructions = QTextEdit()
        instructions.setReadOnly(True)
        instructions.setText("Por favor, selecciona una campaña y el método para agregar datos.")
        instructions.setMaximumHeight(50)
        main_layout.addWidget(instructions)

        content_stack = QTabWidget(self)
        main_layout.addWidget(content_stack)

        # Pestaña Manual
        manual_tab = QWidget()
        manual_layout = QVBoxLayout(manual_tab)
        content_stack.addTab(manual_tab, "Datos Manuales")

        manual_form_layout = QGridLayout()
        manual_layout.addLayout(manual_form_layout)

        manual_form_layout.addWidget(QLabel("Seleccionar Campaña:", self), 0, 0)
        self.campaign_combo = QComboBox(self)
        self.campaign_combo.currentIndexChanged.connect(self.update_detector_entries)
        manual_form_layout.addWidget(self.campaign_combo, 0, 1)

        # Scroll Area for Detector Entries
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        detector_entries_widget = QWidget()
        self.detector_entries_layout = QGridLayout(detector_entries_widget)
        scroll_area.setWidget(detector_entries_widget)
        manual_layout.addWidget(scroll_area)

        self.observations_manual = QLineEdit(self)
        self.observations_manual.setPlaceholderText("Observaciones")
        self.observations_manual.setMaximumWidth(400)
        manual_layout.addWidget(self.observations_manual)

        buttons_layout = QHBoxLayout()
        save_button_manual = QPushButton("Agregar Datos")
        save_button_manual.setMaximumWidth(150)
        save_button_manual.clicked.connect(self.save_manual_data)
        save_button_manual.setStyleSheet("background-color: #4CAF50; color: white;")  # Botón verde
        buttons_layout.addWidget(save_button_manual)

        manual_back_button = QPushButton("Regresar")
        manual_back_button.setMaximumWidth(150)
        manual_back_button.clicked.connect(self.back)
        manual_back_button.setStyleSheet("background-color: #f44336; color: white;")  # Botón rojo
        buttons_layout.addWidget(manual_back_button)
        manual_layout.addLayout(buttons_layout)

        # Pestaña ROOT
        root_tab = QWidget()
        root_layout = QVBoxLayout(root_tab)
        content_stack.addTab(root_tab, "Datos desde ROOT")

        root_form_layout = QGridLayout()
        root_layout.addLayout(root_form_layout)

        root_form_layout.addWidget(QLabel("Seleccionar Campaña:", self), 0, 0)
        self.campaign_combo_root = QComboBox(self)
        campaigns = get_existing_campaigns()
        if campaigns:
            campaigns.reverse()
            self.campaign_combo_root.addItems(campaigns)
            self.campaign_combo_root.setCurrentIndex(0)
        else:
            self.campaign_como_root.addItem("No hay campañas disponibles")

        root_form_layout.addWidget(self.campaign_combo_root, 0, 1)

        accept_campaign_button = QPushButton("Aceptar Campaña", self)
        accept_campaign_button.setMaximumWidth(200)
        accept_campaign_button.clicked.connect(self.accept_campaign)
        root_form_layout.addWidget(accept_campaign_button, 1, 0)

        self.selected_file_label = QLabel("", self)
        root_form_layout.addWidget(self.selected_file_label, 1, 1)

        self.observations_root = QLineEdit(self)
        self.observations_root.setPlaceholderText("Observaciones")
        self.observations_root.setMaximumWidth(400)
        root_layout.addWidget(self.observations_root)

        root_buttons_layout = QHBoxLayout()
        save_button_root = QPushButton("Agregar Datos")
        save_button_root.setMaximumWidth(150)
        save_button_root.clicked.connect(self.save_root_data)
        save_button_root.setStyleSheet("background-color: #4CAF50; color: white;")  # Botón verde
        root_buttons_layout.addWidget(save_button_root)

        root_back_button = QPushButton("Regresar")
        root_back_button.setMaximumWidth(150)
        root_back_button.clicked.connect(self.back)
        root_back_button.setStyleSheet("background-color: #f44336; color: white;")  # Botón rojo
        root_buttons_layout.addWidget(root_back_button)
        root_layout.addLayout(root_buttons_layout)

        self.refresh_campaigns()

        # Estilos
        self.setStyleSheet("""
            QPushButton {
                min-width: 150px;
                min-height: 30px;
                font-size: 14px;
            }
            QLabel {
                font-size: 14px;
            }
            QLineEdit, QComboBox {
                font-size: 14px;
            }
            QTableWidget {
                font-size: 14px;
            }
        """)

    def refresh_campaigns(self):
        campaigns = get_existing_campaigns()
        self.campaign_combo.clear()
        self.campaign_combo.addItems(campaigns)
        self.campaign_combo_root.clear()
        self.campaign_combo_root.addItems(campaigns)
        self.update_detector_entries()

    def update_detector_entries(self):
        short_name = self.campaign_combo.currentText()
        if not short_name:
            return
        num_detectors = get_num_detectors(short_name)
        self.detector_entries.clear()

        # Eliminar entradas anteriores
        for i in reversed(range(self.detector_entries_layout.count())):
            item = self.detector_entries_layout.itemAt(i)
            if item and item.widget():
                item.widget().setParent(None)

        # Create headers
        header_labels = ["Detector", "Entries", "Neutrons in Region [140, 820] keV"]
        for col, header in enumerate(header_labels):
            label = QLabel(header)
            label.setStyleSheet("font-weight: bold;")
            self.detector_entries_layout.addWidget(label, 0, col)

        for i in range(num_detectors):
            detector_label = QLabel(f"Detector {i+1}", self)
            total_counts = QLineEdit(self)
            total_counts.setMaximumWidth(150)
            neutron_counts = QLineEdit(self)
            neutron_counts.setMaximumWidth(150)

            self.detector_entries_layout.addWidget(detector_label, i+1, 0)
            self.detector_entries_layout.addWidget(total_counts, i+1, 1)
            self.detector_entries_layout.addWidget(neutron_counts, i+1, 2)
            self.detector_entries.append((total_counts, neutron_counts))

    def save_manual_data(self):
        short_name = self.campaign_combo.currentText()
        detector_entries = []
        for total_entry, neutron_entry in self.detector_entries:
            total_text = total_entry.text().strip()
            neutron_text = neutron_entry.text().strip()
            if not total_text or not neutron_text:
                QMessageBox.critical(self, "Error", "Todos los campos de detectores deben estar completos.")
                return
            try:
                total = float(total_text)
                neutron = float(neutron_text)
                detector_entries.append((total, neutron))
            except ValueError:
                QMessageBox.critical(self, "Error", "Las entradas deben ser números válidos.")
                return

        observations = self.observations_manual.text().strip()
        if not observations:
            observations = "Sin observaciones"

        # No se solicita 'Nuevo Archivo DLT' en la entrada manual
        new_dlt = "N/A"

        # Usar el timestamp actual para la entrada manual
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # Verificar si el timestamp ya existe en el archivo CSV
        campaign_file = f"./data/{short_name}-CountingRate.csv"
        if os.path.exists(campaign_file):
            df_existing = pd.read_csv(campaign_file)
            if timestamp in df_existing['timestamp'].values:
                QMessageBox.critical(self, "Error", "Ya existe una entrada con el mismo timestamp.")
                return

        # Guardar los datos en el CSV
        success = self.save_results_manual(short_name, detector_entries, new_dlt, observations, timestamp)
        if success:
            QMessageBox.information(self, "Éxito", "Datos de la campaña guardados con éxito.")
            self.show_dataframe(short_name)
            self.back()
        else:
            QMessageBox.critical(self, "Error", "No se pudieron guardar los datos.")

    def save_results_manual(self, short_name, data_entries, new_dlt, observations, timestamp):
        campaign_file = f"./data/{short_name}-CountingRate.csv"
        os.makedirs("./data", exist_ok=True)

        if os.path.exists(campaign_file):
            existing_df = pd.read_csv(campaign_file)
        else:
            existing_df = pd.DataFrame()

        new_data = {
            "timestamp": timestamp,
            "dlt_file": new_dlt,
            "observations": observations
        }

        for i, (total_counts, neutron_counts) in enumerate(data_entries):
            new_data[f"detector_{i+1}_histogram_name"] = "Manual Entry"
            new_data[f"detector_{i+1}_total_counts"] = total_counts
            new_data[f"detector_{i+1}_neutron_counts"] = neutron_counts

        new_df = pd.DataFrame([new_data])
        combined_df = pd.concat([existing_df, new_df], ignore_index=True)

        # Ordenar por timestamp
        combined_df['timestamp'] = pd.to_datetime(combined_df['timestamp'])
        combined_df = combined_df.sort_values('timestamp')

        combined_df.to_csv(campaign_file, index=False)
        return True

    def accept_campaign(self):
        short_name = self.campaign_combo_root.currentText()
        if not short_name:
            QMessageBox.critical(self, "Error", "Debe seleccionar una campaña.")
            return

        self.selected_campaign_name = short_name
        # Mostrar interfaz de mapeo
        self.show_mapping_interface()

    def show_mapping_interface(self):
        # Crear una ventana de diálogo para el mapeo
        mapping_dialog = QDialog(self)
        mapping_dialog.setWindowTitle("Mapeo de Histogramas a Detectores")
        mapping_dialog.resize(600, 400)
        layout = QVBoxLayout(mapping_dialog)

        # Obtener los histogramas del archivo ROOT
        self.select_root_file()

        if not self.root_file_path:
            return

        root_file = ROOT.TFile(self.root_file_path)
        self.histograms = {}
        for key in root_file.GetListOfKeys():
            hist_name = key.GetName()
            cycle = key.GetCycle()
            if cycle == 1:
                obj = key.ReadObj()
                if isinstance(obj, ROOT.TH1) and any(suffix in hist_name for suffix in ['_cal', '_CAL', '_Cal']):
                    self.histograms[hist_name] = obj  # Guardar sin el ciclo en el nombre

        if not self.histograms:
            QMessageBox.critical(self, "Error", "No se encontraron histogramas con '_cal', '_CAL' o '_Cal' en el archivo ROOT.")
            return

        # Cargar mapeo existente o crear uno nuevo
        self.detector_map = {}
        mapping_layout = QGridLayout()
        num_detectors = get_num_detectors(self.selected_campaign_name)

        # Botón para cargar mapeo existente
        load_mapping_button = QPushButton("Cargar Mapeo")
        load_mapping_button.clicked.connect(self.load_mapping)
        layout.addWidget(load_mapping_button)

        for i in range(num_detectors):
            detector_label = QLabel(f"Detector {i + 1}")
            hist_name_combo = QComboBox()
            hist_name_combo.addItems(self.histograms.keys())
            mapping_layout.addWidget(detector_label, i, 0)
            mapping_layout.addWidget(hist_name_combo, i, 1)
            self.detector_map[i] = hist_name_combo

        # Cargar mapeo si existe
        mapping_file = f"./mapeo_calibrados/{self.selected_campaign_name}/Mapeo_histogramas_{self.selected_campaign_name}_calibrados.csv"
        if os.path.exists(mapping_file):
            self.load_mapping_from_file(mapping_file)

        layout.addLayout(mapping_layout)

        # Botones
        buttons_layout = QHBoxLayout()
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
            hist_name = self.detector_map[i].currentText()
            self.detector_histogram_map[i] = hist_name

        # Después de cerrar el diálogo, actualizar la etiqueta del archivo seleccionado
        self.selected_file_label.setText(os.path.basename(self.root_file_path))

    def load_mapping(self):
        mapping_file, _ = QFileDialog.getOpenFileName(self, "Seleccionar archivo de mapeo", f"./mapeo_calibrados/{self.selected_campaign_name}", "CSV Files (*.csv)")
        if mapping_file:
            self.load_mapping_from_file(mapping_file)

    def load_mapping_from_file(self, mapping_file):
        df_mapping = pd.read_csv(mapping_file)
        num_detectors = get_num_detectors(self.selected_campaign_name)
        for i in range(num_detectors):
            hist_name = df_mapping.loc[df_mapping['Detector'] == f'Detector_{i+1}', 'Histograma'].values[0]
            if hist_name in self.histograms:
                self.detector_map[i].setCurrentText(hist_name)
            else:
                QMessageBox.warning(self, "Advertencia", f"El histograma '{hist_name}' no se encontró en el archivo ROOT.")

    def select_root_file(self):
        short_name = self.selected_campaign_name
        if not short_name:
            QMessageBox.critical(self, "Error", "Debe seleccionar una campaña.")
            return

        # Open file dialog from ./rootonline/{short_name}
        initial_dir = os.path.abspath(os.path.join(".", "rootonline", short_name))
        if not os.path.exists(initial_dir):
            os.makedirs(initial_dir, exist_ok=True)
        file_name, _ = QFileDialog.getOpenFileName(self, "Seleccionar archivo ROOT", initial_dir, "ROOT Files (*.root)")
        if file_name:
            self.root_file_path = file_name
        else:
            self.root_file_path = ""

    def save_mapping(self):
        # Guardar el mapeo en un archivo CSV
        mapping_data = []
        for i in range(len(self.detector_map)):
            hist_name = self.detector_map[i].currentText()
            mapping_data.append({
                'Detector': f'Detector_{i+1}',
                'Histograma': hist_name
            })

        df_mapping = pd.DataFrame(mapping_data)
        save_dir = f"./mapeo_calibrados/{self.selected_campaign_name}"
        os.makedirs(save_dir, exist_ok=True)
        mapping_file = f"{save_dir}/Mapeo_histogramas_{self.selected_campaign_name}_calibrados.csv"
        df_mapping.to_csv(mapping_file, index=False)
        QMessageBox.information(self, "Éxito", f"Mapeo guardado en {mapping_file}")

    def save_root_data(self):
        short_name = self.campaign_combo_root.currentText()
        root_file_path = self.root_file_path

        if not root_file_path:
            QMessageBox.critical(self, "Error", "Debe seleccionar un archivo ROOT.")
            return

        observations = self.observations_root.text().strip()
        if not observations:
            observations = "Sin observaciones"

        new_dlt = "N/A"

        try:
            modification_time = os.path.getmtime(root_file_path)
            timestamp = datetime.fromtimestamp(modification_time).strftime('%Y-%m-%d %H:%M:%S')
        except Exception as e:
            QMessageBox.warning(self, "Advertencia", f"No se pudo obtener la fecha de modificación del archivo ROOT: {e}")
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        campaign_file = f"./data/{short_name}-CountingRate.csv"
        if os.path.exists(campaign_file):
            df_existing = pd.read_csv(campaign_file)
            if timestamp in df_existing['timestamp'].values:
                QMessageBox.critical(self, "Error", "Ya existe una entrada con el mismo timestamp.")
                return
        else:
            # Crear el archivo CSV si no existe
            df_existing = pd.DataFrame()

        root_file = ROOT.TFile(root_file_path)

        # Procesar los histogramas según el mapeo
        data_entries = []
        hist_names = []
        for i in range(len(self.detector_histogram_map)):
            hist_name = self.detector_histogram_map[i]
            hist = root_file.Get(f"{hist_name};1")
            if hist:
                integral_total = hist.Integral(0, 15000)
                integral_region = hist.Integral(140, 820)
                data_entries.append((integral_total, integral_region))
                hist_names.append(hist_name)
            else:
                QMessageBox.critical(self, "Error", f"No se pudo encontrar el histograma {hist_name} en el archivo ROOT.")
                root_file.Close()
                return

        root_file.Close()

        success = self.save_results_with_hist_names(short_name, data_entries, new_dlt, observations, timestamp, hist_names)
        if success:
            QMessageBox.information(self, "Éxito", "Datos desde archivo ROOT guardados con éxito.")
            self.show_dataframe(short_name)
            self.back()
        else:
            QMessageBox.critical(self, "Error", "No se pudieron guardar los datos.")

    def save_results_with_hist_names(self, short_name, data_entries, new_dlt, observations, timestamp, hist_names):
        campaign_file = f"./data/{short_name}-CountingRate.csv"
        os.makedirs("./data", exist_ok=True)

        if os.path.exists(campaign_file):
            existing_df = pd.read_csv(campaign_file)
        else:
            existing_df = pd.DataFrame()

        new_data = {
            "timestamp": timestamp,
            "dlt_file": new_dlt,
            "observations": observations
        }

        for i, (total_counts, neutron_counts) in enumerate(data_entries):
            new_data[f"detector_{i+1}_histogram_name"] = hist_names[i]
            new_data[f"detector_{i+1}_total_counts"] = total_counts
            new_data[f"detector_{i+1}_neutron_counts"] = neutron_counts

        new_df = pd.DataFrame([new_data])
        combined_df = pd.concat([existing_df, new_df], ignore_index=True)

        # Ordenar por timestamp
        combined_df['timestamp'] = pd.to_datetime(combined_df['timestamp'])
        combined_df = combined_df.sort_values('timestamp')

        combined_df.to_csv(campaign_file, index=False)
        return True

    def show_dataframe(self, short_name):
        campaign_file = f"./data/{short_name}-CountingRate.csv"
        if os.path.exists(campaign_file):
            df = pd.read_csv(campaign_file)
            self.show_dataframe_dialog(df)
        else:
            QMessageBox.warning(self, "Advertencia", "No se encontró el archivo de campaña.")

    def show_dataframe_dialog(self, df):
        dialog = QDialog(self)
        dialog.setWindowTitle("Datos de la Campaña")
        layout = QVBoxLayout()
        table = QTableWidget()
        table.setRowCount(df.shape[0])
        table.setColumnCount(df.shape[1])
        table.setHorizontalHeaderLabels(df.columns.tolist())
        for i in range(df.shape[0]):
            for j in range(df.shape[1]):
                table.setItem(i, j, QTableWidgetItem(str(df.iat[i, j])))
        table.resizeColumnsToContents()
        layout.addWidget(table)
        dialog.setLayout(layout)
        dialog.exec()

    def back(self):
        if callable(self.back_callback):
            self.back_callback()
        else:
            print("Error: back_callback no es callable")
