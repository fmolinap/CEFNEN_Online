# logbook.py

from PySide6.QtWidgets import (
    QWidget, QLabel, QLineEdit, QPushButton, QMessageBox, QVBoxLayout, QHBoxLayout,
    QComboBox, QRadioButton, QButtonGroup, QGridLayout, QFrame, QApplication,
    QGroupBox, QTableWidget, QTableWidgetItem, QHeaderView, QTextEdit,
    QStackedWidget, QDateEdit, QSpinBox, QFileDialog, QTabWidget, QDialog, QTableView
)
from PySide6.QtCore import Qt, QDate
import pandas as pd
import os
from datetime import datetime
import paramiko
import ROOT
import sys
import subprocess  # Para abrir carpetas
ROOT.gROOT.SetBatch(True)
from utils import (
    get_existing_campaigns, get_campaign_info, get_last_timestamp,
    get_current_dlt, save_detector_data, get_num_detectors, get_remote_root_files
)

class Logbook(QWidget):
    def __init__(self, back_callback=None):
        super().__init__()
        self.back_callback = back_callback
        self.init_ui_once = False  # Indicador para saber si ya se ha inicializado la UI
        self.init_ui()

    def init_ui(self):
        if not self.init_ui_once:
            self.setWindowTitle("Registro de Campañas")
            self.resize(900, 700)

            # Establecer layout principal
            self.main_layout = QVBoxLayout(self)
            self.setLayout(self.main_layout)

            # Botones principales
            buttons_layout = QHBoxLayout()
            self.main_layout.addLayout(buttons_layout)

            new_campaign_button = QPushButton("Crear Campaña Nueva")
            new_campaign_button.clicked.connect(self.create_new_campaign)
            buttons_layout.addWidget(new_campaign_button)

            add_data_campaign_button = QPushButton("Agregar Datos a Campaña Antigua")
            add_data_campaign_button.clicked.connect(self.add_data_to_campaign)
            buttons_layout.addWidget(add_data_campaign_button)

            back_button = QPushButton("Regresar")
            back_button.clicked.connect(self.back)
            buttons_layout.addWidget(back_button)

            # Contenedor dinámico
            self.content_frame = QFrame()
            self.main_layout.addWidget(self.content_frame)
            self.content_layout = QVBoxLayout(self.content_frame)

            # Área de mensajes
            self.message_area = QTextEdit()
            self.message_area.setReadOnly(True)
            self.main_layout.addWidget(self.message_area)  # Agregar debajo de los botones principales

            # Estilos (Actualizados para compatibilidad)
            self.setStyleSheet("""
                QPushButton {
                    min-width: 200px;
                    min-height: 40px;
                    font-size: 16px;
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
                QTextEdit {
                    font-size: 12px;
                    background-color: #ffffff;  /* Cambiado a blanco para compatibilidad */
                    color: #000000;  /* Texto negro */
                }
                QTabWidget::pane {
                    border: 1px solid #cccccc;  /* Borde claro */
                }
                QTabBar::tab {
                    background: #f0f0f0;  /* Fondo claro */
                    color: #000000;  /* Texto negro */
                    padding: 10px;
                }
                QTabBar::tab:selected {
                    background: #e0e0e0;  /* Fondo ligeramente más oscuro para la pestaña seleccionada */
                }
            """)

            self.init_ui_once = True  # Marcar que la UI ha sido inicializada
        else:
            # Si la UI ya ha sido inicializada, simplemente limpiamos el contenido dinámico
            self.clear_content()

    def clear_content(self):
        # Eliminar widgets anteriores del contenedor dinámico
        for i in reversed(range(self.content_layout.count())):
            widget = self.content_layout.itemAt(i).widget()
            if widget is not None:
                widget.setParent(None)

    def create_new_campaign(self):
        self.clear_content()
        campaign_frame = QFrame()
        self.content_layout.addWidget(campaign_frame)
        layout = QGridLayout()
        campaign_frame.setLayout(layout)

        # Título y subtítulo
        title = QLabel("Creando Nueva Campaña Experimental CEFNEN")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 20px; font-weight: bold;")
        layout.addWidget(title, 0, 0, 1, 2)

        subtitle = QLabel(
            "Ingresa los datos correspondientes a la nueva campaña experimental CEFNEN. "
            "Esta información será utilizada en todo el programa de análisis online y se encontrará "
            "en el archivo ./data/info_campaigns.csv que se recomienda no editar. Asegúrate de que el "
            "nombre corto sea representativo y único para esta campaña ya que es la base de todo el análisis."
        )
        subtitle.setWordWrap(True)
        layout.addWidget(subtitle, 1, 0, 1, 2)

        # Selección de número de campaña
        campaign_nums = ["1ra", "2da", "3ra", "4ta", "5ta", "6ta", "7ma", "8va", "9na", "test", "Lab", "otra"]
        self.campaign_num_group = QButtonGroup()
        num_layout = QHBoxLayout()
        for num in campaign_nums:
            radio = QRadioButton(num)
            self.campaign_num_group.addButton(radio)
            num_layout.addWidget(radio)
            if num == "otra":
                radio.toggled.connect(self.check_other)
        layout.addLayout(num_layout, 2, 0, 1, 2)

        # Campo para "otra" campaña
        self.other_entry = QLineEdit()
        self.other_entry.setPlaceholderText("Especifique otro número de campaña")
        self.other_entry.setVisible(False)
        layout.addWidget(self.other_entry, 3, 0, 1, 2)

        # Campos de entrada
        self.location = QLineEdit()
        self.start_date = QLineEdit()
        self.end_date = QLineEdit()
        self.short_name = QLineEdit()
        self.num_detectors = QLineEdit()
        self.dlt_path = QLineEdit()
        self.root_path = QLineEdit()

        layout.addWidget(QLabel("Lugar:"), 4, 0)
        layout.addWidget(self.location, 4, 1)

        layout.addWidget(QLabel("Fecha de Inicio (AA/MM/DD):"), 5, 0)
        layout.addWidget(self.start_date, 5, 1)

        layout.addWidget(QLabel("Fecha de Término (AA/MM/DD):"), 6, 0)
        layout.addWidget(self.end_date, 6, 1)

        layout.addWidget(QLabel("Nombre Corto:"), 7, 0)
        layout.addWidget(self.short_name, 7, 1)

        layout.addWidget(QLabel("Número de Detectores:"), 8, 0)
        layout.addWidget(self.num_detectors, 8, 1)

        layout.addWidget(QLabel("Path Completo a los Archivos .dlt:"), 9, 0)
        layout.addWidget(self.dlt_path, 9, 1)

        layout.addWidget(QLabel("Path Completo a los Archivos .root:"), 10, 0)
        layout.addWidget(self.root_path, 10, 1)

        # Botones
        buttons_layout = QHBoxLayout()
        save_button = QPushButton("Guardar")
        save_button.clicked.connect(self.save_new_campaign)
        buttons_layout.addWidget(save_button)

        back_button = QPushButton("Regresar")
        back_button.clicked.connect(self.init_ui)
        buttons_layout.addWidget(back_button)

        layout.addLayout(buttons_layout, 11, 0, 1, 2)

    def check_other(self):
        if self.campaign_num_group.checkedButton() and self.campaign_num_group.checkedButton().text() == "otra":
            self.other_entry.setVisible(True)
        else:
            self.other_entry.setVisible(False)

    def save_new_campaign(self):
        selected_button = self.campaign_num_group.checkedButton()
        if not selected_button:
            QMessageBox.critical(self, "Error", "Debe seleccionar un número de campaña.")
            return
        campaign_num = self.other_entry.text().strip() if selected_button.text() == "otra" else selected_button.text().strip()

        if not campaign_num:
            QMessageBox.critical(self, "Error", "Debe especificar el número de campaña.")
            return

        try:
            num_detectors = int(self.num_detectors.text())
            if num_detectors <= 0:
                raise ValueError
        except ValueError:
            QMessageBox.critical(self, "Error", "El número de detectores debe ser un número entero positivo.")
            return

        campaign_info = {
            "Numero": campaign_num,
            "Lugar": self.location.text().strip(),
            "Fecha de Inicio": self.start_date.text().strip(),
            "Fecha de Termino": self.end_date.text().strip(),
            "Nombre Corto": self.short_name.text().strip(),
            "Número de Detectores": num_detectors,
            "DLT Path": self.dlt_path.text().strip(),
            "ROOT Path": self.root_path.text().strip()
        }

        # Validaciones adicionales
        if not all(campaign_info.values()):
            QMessageBox.critical(self, "Error", "Todos los campos deben estar completos.")
            return

        info_file = "./data/info_campaigns.csv"
        os.makedirs("./data", exist_ok=True)
        if not os.path.exists(info_file):
            df_info = pd.DataFrame(columns=[
                "Numero", "Lugar", "Fecha de Inicio", "Fecha de Termino", "Nombre Corto",
                "Número de Detectores", "DLT Path", "ROOT Path"
            ])
        else:
            df_info = pd.read_csv(info_file)

        # Verificar si el nombre corto ya existe
        if campaign_info['Nombre Corto'] in df_info['Nombre Corto'].values:
            QMessageBox.critical(self, "Error", "El nombre corto ya existe. Por favor, elija otro.")
            return

        df_info = pd.concat([df_info, pd.DataFrame([campaign_info])], ignore_index=True)
        df_info.to_csv(info_file, index=False)

        file_name = f"./data/{campaign_info['Nombre Corto']}-CountingRate.csv"
        header = ["timestamp"]
        for i in range(campaign_info['Número de Detectores']):
            header.extend([
                f"detector_{i+1}_total_counts",
                f"detector_{i+1}_neutron_counts"
            ])
        header.extend(["observations"])  # Eliminado 'dlt_file'
        df_counts = pd.DataFrame(columns=header)
        df_counts.to_csv(file_name, index=False)

        QMessageBox.information(self, "Éxito", "Campaña creada y guardada con éxito.")
        self.init_ui()

    def add_data_to_campaign(self):
        self.clear_content()
        add_data_widget = AddDataToCampaign(
            back_callback=self.back,
            main_stack=self.content_layout,
            refresh_callback=self.refresh_campaigns,
            show_dataframe_dialog=self.show_dataframe_dialog
        )
        self.content_layout.addWidget(add_data_widget)

    def show_dataframe_dialog(self, df):
        # Implementación de un diálogo para mostrar el DataFrame
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
        self.refresh_callback()

    def refresh_campaigns(self):
        # Implementa la lógica para refrescar las campañas si es necesario
        # Por ejemplo, podrías actualizar los desplegables si hay cambios
        pass

class AddDataToCampaign(QWidget):
    def __init__(self, back_callback, main_stack, refresh_callback, show_dataframe_dialog):
        super().__init__()
        self.back_callback = back_callback
        self.main_stack = main_stack
        self.refresh_callback = refresh_callback
        self.show_dataframe_dialog = show_dataframe_dialog
        self.root_file_path = ""
        self.detector_entries = []
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)

        title_stack = QStackedWidget(self)
        # Removed background-color to match main app's color scheme
        title_stack.setStyleSheet("")
        title_widget = QWidget(self)
        title_layout = QVBoxLayout(title_widget)
        title_stack.addWidget(title_widget)
        main_layout.addWidget(title_stack)

        title = QLabel("Agregar Datos a Campaña Existente", self)
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 20px; font-weight: bold;")
        title_layout.addWidget(title)

        subtitle = QLabel(
            "Selecciona una campaña existente y agrega datos manualmente o desde un archivo ROOT.",
            self)
        subtitle.setWordWrap(True)
        subtitle.setStyleSheet("font-size: 14px;")
        title_layout.addWidget(subtitle)

        content_stack = QTabWidget(self)
        # Removed background-color to match main app's color scheme
        content_stack.setStyleSheet("")
        main_layout.addWidget(content_stack)

        # Manual Tab
        manual_tab = QWidget()
        manual_content = QWidget()
        self.manual_layout = QGridLayout(manual_content)
        manual_tab_layout = QVBoxLayout(manual_tab)
        manual_tab_layout.addWidget(manual_content)
        content_stack.addTab(manual_tab, "Datos Manuales")

        self.manual_layout.addWidget(QLabel("Seleccionar Campaña:", self), 0, 0)
        self.campaign_combo = QComboBox(self)
        self.campaign_combo.currentIndexChanged.connect(self.update_detector_entries)
        self.manual_layout.addWidget(self.campaign_combo, 0, 1, 1, 2)

        # ROOT Tab
        root_tab = QWidget()
        root_content = QWidget()
        self.root_layout = QVBoxLayout(root_content)
        root_tab_layout = QVBoxLayout(root_tab)
        root_tab_layout.addWidget(root_content)
        content_stack.addTab(root_tab, "Datos desde ROOT")

        self.root_layout.addWidget(QLabel("Seleccionar Campaña:", self))
        self.campaign_combo_root = QComboBox(self)
        self.campaign_combo_root.currentIndexChanged.connect(self.update_root_entries)
        self.root_layout.addWidget(self.campaign_combo_root)

        select_file_button = QPushButton("Seleccionar archivo ROOT", self)
        select_file_button.setMaximumWidth(200)
        select_file_button.clicked.connect(self.select_root_file)
        self.root_layout.addWidget(select_file_button)
        self.selected_file_label = QLabel("", self)
        self.root_layout.addWidget(self.selected_file_label)

        self.new_dlt_root = QLineEdit(self)
        self.new_dlt_root.setPlaceholderText("Nuevo Archivo DLT")
        self.new_dlt_root.setMaximumWidth(200)
        self.root_layout.addWidget(self.new_dlt_root)

        self.observations_root = QLineEdit(self)
        self.observations_root.setPlaceholderText("Observaciones")
        self.observations_root.setMaximumWidth(200)
        self.root_layout.addWidget(self.observations_root)

        save_button_root = QPushButton("Guardar Datos desde ROOT", self)
        save_button_root.setMaximumWidth(200)
        save_button_root.clicked.connect(self.save_root_data)
        self.root_layout.addWidget(save_button_root)

        root_back_button = QPushButton("Regresar", self)
        root_back_button.setMaximumWidth(200)
        root_back_button.clicked.connect(self.back_callback)  # Cambiado a back_callback
        self.root_layout.addWidget(root_back_button)

        # Manual "Regresar" Button
        manual_back_button = QPushButton("Regresar", self)
        manual_back_button.setMaximumWidth(200)
        manual_back_button.clicked.connect(self.back_callback)  # Cambiado a back_callback
        self.manual_layout.addWidget(manual_back_button, 20, 2)

        self.refresh_campaigns()

    def refresh_campaigns(self):
        self.campaign_combo.clear()
        self.campaign_combo_root.clear()
        campaigns = get_existing_campaigns()
        self.campaign_combo.addItems(campaigns)
        self.campaign_combo_root.addItems(campaigns)

    def update_detector_entries(self):
        short_name = self.campaign_combo.currentText()
        if not short_name:
            return
        num_detectors = get_num_detectors(short_name)
        self.detector_entries.clear()

        # Eliminar entradas anteriores (excepto los labels de campaña)
        for i in reversed(range(self.manual_layout.count())):
            item = self.manual_layout.itemAt(i)
            if item and item.widget() and not isinstance(item.widget(), QLabel) and not isinstance(item.widget(), QPushButton):
                item.widget().setParent(None)

        left_entries = QVBoxLayout()
        right_entries = QVBoxLayout()

        for i in range(num_detectors):
            detector_label = QLabel(f"Detector {i+1}", self)
            total_counts = QLineEdit(self)
            total_counts.setMaximumWidth(200)
            neutron_counts = QLineEdit(self)
            neutron_counts.setMaximumWidth(200)
            if (i + 1) % 2 == 1:  # Impares
                left_entries.addWidget(detector_label)
                left_entries.addWidget(QLabel("Entries", self))
                left_entries.addWidget(total_counts)
                left_entries.addWidget(QLabel("Neutrons in Region [140, 820] keV", self))
                left_entries.addWidget(neutron_counts)
            else:  # Pares
                right_entries.addWidget(detector_label)
                right_entries.addWidget(QLabel("Entries", self))
                right_entries.addWidget(total_counts)
                right_entries.addWidget(QLabel("Neutrons in Region [140, 820] keV", self))
                right_entries.addWidget(neutron_counts)
            self.detector_entries.append((total_counts, neutron_counts))

        detector_layout = QHBoxLayout()
        detector_layout.addLayout(left_entries)
        detector_layout.addLayout(right_entries)
        self.manual_layout.addLayout(detector_layout, 1, 0, 1, 3)

        self.new_dlt_manual = QLineEdit(self)
        self.new_dlt_manual.setPlaceholderText("Nuevo Archivo DLT")
        self.new_dlt_manual.setMaximumWidth(200)
        self.manual_layout.addWidget(self.new_dlt_manual, 18, 1, 1, 2)

        self.observations_manual = QLineEdit(self)
        self.observations_manual.setPlaceholderText("Observaciones")
        self.observations_manual.setMaximumWidth(200)
        self.manual_layout.addWidget(self.observations_manual, 19, 1, 1, 2)

        save_button_manual = QPushButton("Guardar Datos Manuales", self)
        save_button_manual.setMaximumWidth(200)
        save_button_manual.clicked.connect(self.save_manual_data)
        self.manual_layout.addWidget(save_button_manual, 20, 1)

    def update_root_entries(self):
        short_name = self.campaign_combo_root.currentText()
        if not short_name:
            return
        # No es necesario volver a crear los widgets de campaña, se asume que ya están creados
        # Por lo tanto, evitamos limpiar y re-agregar widgets que ya existen
        # Esto previene la pérdida de la lista de campañas en el ComboBox

    def select_root_file(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Seleccionar archivo ROOT", "", "ROOT Files (*.root)")
        if file_name:
            self.selected_file_label.setText(file_name)
            self.root_file_path = file_name

            # Obtener la carpeta ./rootonline/{Nombre de campaña seleccionada}
            short_name = self.campaign_combo_root.currentText()
            target_folder = os.path.join(".", "rootonline", short_name)
            if not os.path.exists(target_folder):
                os.makedirs(target_folder, exist_ok=True)

            # Abrir la carpeta en el explorador de archivos
            try:
                if sys.platform.startswith('darwin'):  # macOS
                    subprocess.call(['open', os.path.abspath(target_folder)])
                elif sys.platform.startswith('linux'):  # Linux
                    subprocess.call(['xdg-open', os.path.abspath(target_folder)])
                elif sys.platform.startswith('win'):  # Windows
                    os.startfile(os.path.abspath(target_folder))
                else:
                    QMessageBox.warning(self, "Advertencia", "Sistema operativo no soportado para abrir la carpeta automáticamente.")
            except Exception as e:
                QMessageBox.warning(self, "Advertencia", f"No se pudo abrir la carpeta: {e}")

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

        new_dlt = self.new_dlt_manual.text().strip()
        observations = self.observations_manual.text().strip()

        if not new_dlt:
            QMessageBox.critical(self, "Error", "El campo 'Nuevo Archivo DLT' no puede estar vacío.")
            return

        if not observations:
            QMessageBox.critical(self, "Error", "El campo 'Observaciones' no puede estar vacío.")
            return

        # Obtener el timestamp basado en la última modificación del archivo ROOT
        try:
            modification_time = os.path.getmtime(self.root_file_path)
            timestamp = datetime.fromtimestamp(modification_time).strftime('%Y-%m-%d %H:%M:%S')
        except Exception as e:
            QMessageBox.warning(self, "Advertencia", f"No se pudo obtener la fecha de modificación del archivo ROOT: {e}")
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # Guardar los datos sin verificar el archivo .dlt y comentarios
        campaign_file = f"./data/{short_name}-CountingRate.csv"
        os.makedirs("./data", exist_ok=True)

        if os.path.exists(campaign_file):
            existing_df = pd.read_csv(campaign_file)
        else:
            existing_df = pd.DataFrame()

        new_data = {
            "timestamp": timestamp,
            "observations": observations
        }

        for i, (total, neutron) in enumerate(detector_entries, start=1):
            new_data[f"detector_{i}_total_counts"] = total
            new_data[f"detector_{i}_neutron_counts"] = neutron

        new_df = pd.concat([existing_df, pd.DataFrame([new_data])], ignore_index=True)
        new_df.to_csv(campaign_file, index=False)

        QMessageBox.information(self, "Éxito", "Datos de la campaña guardados con éxito.")
        self.show_dataframe(short_name)
        self.back_callback()  # Cambiado a back_callback

    def save_root_data(self):
        short_name = self.campaign_combo_root.currentText()
        root_file_path = self.root_file_path
        new_dlt = self.new_dlt_root.text().strip()
        observations = self.observations_root.text().strip()

        if not root_file_path:
            QMessageBox.critical(self, "Error", "Debe seleccionar un archivo ROOT.")
            return

        if not new_dlt:
            QMessageBox.critical(self, "Error", "El campo 'Nuevo Archivo DLT' no puede estar vacío.")
            return

        if not observations:
            QMessageBox.critical(self, "Error", "El campo 'Observaciones' no puede estar vacío.")
            return

        try:
            root_file = ROOT.TFile(root_file_path)
            if root_file.IsZombie():
                QMessageBox.critical(self, "Error", "No se pudo abrir el archivo ROOT.")
                return

            hist_names = list({key.GetName().split(';')[0] for key in root_file.GetListOfKeys() if key.GetName().endswith(('_cal', '_CAL', '_Cal'))})
            if not hist_names:
                QMessageBox.critical(self, "Error", "No se encontraron histogramas con terminación '_cal', '_CAL' o '_Cal' en el archivo ROOT.")
                return

            results = []
            for hist_name in hist_names:
                obj = root_file.Get(f"{hist_name};1")
                if isinstance(obj, ROOT.TH1):
                    integral_total = obj.Integral(0, 15000)
                    integral_region = obj.Integral(140, 820)
                    results.append((hist_name, integral_total, integral_region))

            df = pd.DataFrame(results, columns=['Nombre del Histograma', 'Total Counts', 'Neutron Counts'])
            self.save_results_to_csv(short_name, df, new_dlt, observations)
            self.show_dataframe(short_name)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo procesar el archivo ROOT: {e}")
            return

        QMessageBox.information(self, "Éxito", "Datos desde archivo ROOT guardados con éxito.")
        self.back_callback()  # Cambiado a back_callback

    def save_results_to_csv(self, short_name, df, new_dlt, observations):
        campaign_file = f"./data/{short_name}-CountingRate.csv"
        os.makedirs("./data", exist_ok=True)

        if os.path.exists(campaign_file):
            existing_df = pd.read_csv(campaign_file)
        else:
            existing_df = pd.DataFrame()

        # Obtener el timestamp basado en la última modificación del archivo ROOT
        try:
            modification_time = os.path.getmtime(self.root_file_path)
            timestamp = datetime.fromtimestamp(modification_time).strftime('%Y-%m-%d %H:%M:%S')
        except Exception as e:
            QMessageBox.warning(self, "Advertencia", f"No se pudo obtener la fecha de modificación del archivo ROOT: {e}")
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        new_data = {
            "timestamp": timestamp,
            "observations": observations
        }

        for i, row in df.iterrows():
            new_data[f"detector_{i+1}_total_counts"] = row['Total Counts']
            new_data[f"detector_{i+1}_neutron_counts"] = row['Neutron Counts']

        new_df = pd.concat([existing_df, pd.DataFrame([new_data])], ignore_index=True)
        new_df.to_csv(campaign_file, index=False)

    def show_dataframe(self, short_name):
        campaign_file = f"./data/{short_name}-CountingRate.csv"
        if os.path.exists(campaign_file):
            df = pd.read_csv(campaign_file)
            self.show_dataframe_dialog(df)
        else:
            QMessageBox.warning(self, "Advertencia", "No se encontró el archivo de campaña.")

    def show_dataframe_dialog(self, df):
        # Implementación de un diálogo para mostrar el DataFrame
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
        self.refresh_callback()
