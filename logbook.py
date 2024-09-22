from PySide6.QtWidgets import (
    QWidget, QLabel, QLineEdit, QPushButton, QMessageBox, QVBoxLayout, QHBoxLayout,
    QComboBox, QRadioButton, QButtonGroup, QGridLayout, QFrame, QApplication,
    QGroupBox, QTableWidget, QTableWidgetItem, QHeaderView
)
from PySide6.QtCore import Qt
import pandas as pd
import os
from datetime import datetime
import paramiko
import ROOT
ROOT.gROOT.SetBatch(True)
from utils import (
    get_existing_campaigns, get_campaign_info, get_last_timestamp,
    get_current_dlt, save_detector_data
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

            old_campaign_button = QPushButton("Agregar Datos a Campaña Antigua")
            old_campaign_button.clicked.connect(self.add_to_old_campaign)
            buttons_layout.addWidget(old_campaign_button)

            back_button = QPushButton("Regresar")
            back_button.clicked.connect(self.back)
            buttons_layout.addWidget(back_button)

            # Contenedor dinámico
            self.content_frame = QFrame()
            self.main_layout.addWidget(self.content_frame)
            self.content_layout = QVBoxLayout(self.content_frame)

            # Estilos
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
        if self.campaign_num_group.checkedButton().text() == "otra":
            self.other_entry.setVisible(True)
        else:
            self.other_entry.setVisible(False)

    def save_new_campaign(self):
        selected_button = self.campaign_num_group.checkedButton()
        if not selected_button:
            QMessageBox.critical(self, "Error", "Debe seleccionar un número de campaña.")
            return
        campaign_num = self.other_entry.text() if selected_button.text() == "otra" else selected_button.text()

        try:
            num_detectors = int(self.num_detectors.text())
        except ValueError:
            QMessageBox.critical(self, "Error", "El número de detectores debe ser un número entero.")
            return

        campaign_info = {
            "Numero": campaign_num,
            "Lugar": self.location.text(),
            "Fecha de Inicio": self.start_date.text(),
            "Fecha de Termino": self.end_date.text(),
            "Nombre Corto": self.short_name.text(),
            "Número de Detectores": num_detectors,
            "DLT Path": self.dlt_path.text(),
            "ROOT Path": self.root_path.text()
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
        header.extend(["dlt_file", "observations"])
        df_counts = pd.DataFrame(columns=header)
        df_counts.to_csv(file_name, index=False)

        QMessageBox.information(self, "Éxito", "Campaña creada y guardada con éxito.")
        self.init_ui()

    def add_to_old_campaign(self):
        self.clear_content()
        old_campaign_frame = QFrame()
        self.content_layout.addWidget(old_campaign_frame)
        layout = QVBoxLayout()
        old_campaign_frame.setLayout(layout)

        # Título y subtítulo
        title = QLabel("Agregar Datos a Campaña en Curso")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 20px; font-weight: bold;")
        layout.addWidget(title)

        subtitle = QLabel(
            "En esta sección podrás agregar datos durante tu turno de experimento tanto de forma manual, es decir mirando las Entries y la Integral [140,820]keV de los Espectros de Altura de pulso de la pantalla de control del Sistema de Adquisición de Datos GASIFIC, como de forma semiautomática obteniendo un archivo .root generado en la adquisición 'Save Online Histograms' del PC de adquisición guardándolo en este PC Local y leyendo la lista de histogramas calibrados en energía, seleccionando la correspondencia 'número de detector-nombre del histograma'. Además se solicita siempre que haya un evento que notificar escribir en la casilla de Observaciones ya que nos permitirá llevar un control de lo sucedido durante el experimento a la hora de hacer el análisis offline. También es importante registrar correctamente el nombre del archivo .dlt ya que un nuevo archivo permite relajar condiciones impuestas a los gráficos generados."
        )
        subtitle.setWordWrap(True)
        layout.addWidget(subtitle)

        # Seleccionar campaña
        campaign_layout = QHBoxLayout()
        campaign_label = QLabel("Seleccionar Campaña:")
        self.selected_campaign = QComboBox()
        self.campaigns = get_existing_campaigns()
        self.selected_campaign.addItems(self.campaigns)
        campaign_layout.addWidget(campaign_label)
        campaign_layout.addWidget(self.selected_campaign)
        layout.addLayout(campaign_layout)

        # Botones de acción
        buttons_layout = QHBoxLayout()
        manual_button = QPushButton("Agregar Datos Manualmente")
        manual_button.clicked.connect(self.load_manual_entry)
        buttons_layout.addWidget(manual_button)

        root_file_button = QPushButton("Agregar Datos de un archivo ROOT")
        root_file_button.clicked.connect(self.load_root_entry)
        buttons_layout.addWidget(root_file_button)

        back_button = QPushButton("Regresar")
        back_button.clicked.connect(self.init_ui)
        buttons_layout.addWidget(back_button)

        layout.addLayout(buttons_layout)

    def load_manual_entry(self):
        # Obtener el texto seleccionado antes de limpiar el contenido
        selected_campaign_text = self.selected_campaign.currentText()
        campaign_info = get_campaign_info(selected_campaign_text)
        if not campaign_info:
            QMessageBox.critical(self, "Error", "No se pudo cargar la información de la campaña.")
            return

        self.clear_content()
        data_entry_frame = QFrame()
        self.content_layout.addWidget(data_entry_frame)
        layout = QVBoxLayout()
        data_entry_frame.setLayout(layout)

        title = QLabel(f"Agregando datos manualmente a la {campaign_info['Numero']} Campaña en {campaign_info['Lugar']}")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 20px; font-weight: bold;")
        layout.addWidget(title)

        last_timestamp = get_last_timestamp(selected_campaign_text)
        if last_timestamp:
            last_data_label = QLabel(f"Últimos datos guardados: {last_timestamp}")
            layout.addWidget(last_data_label)

        # Tabla de entrada de datos
        num_detectors = int(campaign_info['Número de Detectores'])
        grid_layout = QGridLayout()
        grid_layout.addWidget(QLabel("Detector"), 0, 0)
        grid_layout.addWidget(QLabel("Entries"), 0, 1)
        grid_layout.addWidget(QLabel("Neutrons in Region [140, 820] keV"), 0, 2)

        self.detector_entries = []
        for i in range(num_detectors):
            grid_layout.addWidget(QLabel(f"Detector {i+1}"), i+1, 0)
            total_counts = QLineEdit()
            neutron_counts = QLineEdit()
            grid_layout.addWidget(total_counts, i+1, 1)
            grid_layout.addWidget(neutron_counts, i+1, 2)
            self.detector_entries.append((total_counts, neutron_counts))

        layout.addLayout(grid_layout)

        # Archivo DLT y observaciones
        self.new_dlt = QLineEdit()
        current_dlt = get_current_dlt(selected_campaign_text)
        if current_dlt:
            self.new_dlt.setText(current_dlt)
        else:
            self.new_dlt.setPlaceholderText("Ingrese el nombre del archivo DLT actual")

        self.observations = QLineEdit("Sin Observaciones")

        dlt_layout = QHBoxLayout()
        dlt_layout.addWidget(QLabel("Nuevo Archivo DLT:"))
        dlt_layout.addWidget(self.new_dlt)
        layout.addLayout(dlt_layout)

        obs_layout = QHBoxLayout()
        obs_layout.addWidget(QLabel("Observaciones:"))
        obs_layout.addWidget(self.observations)
        layout.addLayout(obs_layout)

        # Botones
        buttons_layout = QHBoxLayout()
        save_button = QPushButton("Guardar Datos")
        save_button.clicked.connect(lambda: self.save_detector_data_manual(selected_campaign_text))
        buttons_layout.addWidget(save_button)

        back_button = QPushButton("Regresar")
        back_button.clicked.connect(self.init_ui)
        buttons_layout.addWidget(back_button)
        layout.addLayout(buttons_layout)

    def save_detector_data_manual(self, campaign_name):
        data_entries = []
        for total_counts, neutron_counts in self.detector_entries:
            try:
                total = float(total_counts.text())
                neutron = float(neutron_counts.text())
                data_entries.append((total, neutron))
            except ValueError:
                QMessageBox.critical(self, "Error", "Todos los recuentos deben ser números.")
                return

        new_dlt = self.new_dlt.text()
        observations = self.observations.text()
        # Llamamos a la función importada y pasamos self.init_ui como back_callback
        save_detector_data(campaign_name, data_entries, new_dlt, observations, self.init_ui)
        # No es necesario mostrar el QMessageBox aquí, ya se muestra en la función
        # self.init_ui()  # Esto ya se ejecuta en el back_callback

    def load_root_entry(self):
        # Obtener el texto seleccionado antes de limpiar el contenido
        selected_campaign_text = self.selected_campaign.currentText()
        campaign_info = get_campaign_info(selected_campaign_text)
        if not campaign_info:
            QMessageBox.critical(self, "Error", "No se pudo cargar la información de la campaña.")
            return

        self.clear_content()
        root_frame = QFrame()
        self.content_layout.addWidget(root_frame)
        layout = QVBoxLayout()
        root_frame.setLayout(layout)

        title = QLabel(f"Agregando datos a la {campaign_info['Numero']} Campaña en {campaign_info['Lugar']} desde un archivo ROOT")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 20px; font-weight: bold;")
        layout.addWidget(title)

        # Cuadro 1: Obtener archivos ROOT desde PC Adquisición Remoto
        remote_group = QGroupBox("Obtener archivos ROOT desde PC Adquisición Remoto")
        remote_layout = QVBoxLayout()
        remote_group.setLayout(remote_layout)
        layout.addWidget(remote_group)

        self.remote_ip = QLineEdit("192.168.0.107")
        self.remote_path = QLineEdit("/path/to/root/files/")
        self.remote_username = QLineEdit()
        self.remote_password = QLineEdit()
        self.remote_password.setEchoMode(QLineEdit.Password)

        remote_form_layout = QGridLayout()
        remote_form_layout.addWidget(QLabel("IP del PC Remoto:"), 0, 0)
        remote_form_layout.addWidget(self.remote_ip, 0, 1)
        remote_form_layout.addWidget(QLabel("Path Remoto:"), 1, 0)
        remote_form_layout.addWidget(self.remote_path, 1, 1)
        remote_form_layout.addWidget(QLabel("Usuario:"), 2, 0)
        remote_form_layout.addWidget(self.remote_username, 2, 1)
        remote_form_layout.addWidget(QLabel("Contraseña:"), 3, 0)
        remote_form_layout.addWidget(self.remote_password, 3, 1)
        remote_layout.addLayout(remote_form_layout)

        get_remote_files_button = QPushButton("Obtener Archivos Remotos")
        get_remote_files_button.clicked.connect(self.get_remote_files)
        remote_layout.addWidget(get_remote_files_button)

        # Cuadro 2: Cargar Histogramas desde PC Local
        local_group = QGroupBox("Cargar Histogramas desde PC Local")
        local_layout = QVBoxLayout()
        local_group.setLayout(local_layout)
        layout.addWidget(local_group)

        self.local_path = QLineEdit(f"./rootonline/{selected_campaign_text}/")

        local_form_layout = QGridLayout()
        local_form_layout.addWidget(QLabel("Path Local:"), 0, 0)
        local_form_layout.addWidget(self.local_path, 0, 1)
        local_layout.addLayout(local_form_layout)

        load_files_button = QPushButton("Mostrar archivos ROOT")
        load_files_button.clicked.connect(self.load_local_file)
        local_layout.addWidget(load_files_button)

        self.local_files_list = QComboBox()
        local_layout.addWidget(self.local_files_list)

        load_local_file_button = QPushButton("Cargar")
        load_local_file_button.clicked.connect(lambda: self.select_root_file(selected_campaign_text))
        local_layout.addWidget(load_local_file_button)

        # Botón de regresar
        back_button = QPushButton("Regresar")
        back_button.clicked.connect(self.init_ui)
        layout.addWidget(back_button)

    # Resto de métodos...
    # Asegúrate de incluir los métodos get_remote_files, load_local_file, select_root_file,
    # process_root_file, analyze_histograms, show_analysis_results, save_analysis_results, etc.

    def back(self):
        if callable(self.back_callback):
            self.back_callback()
        else:
            print("Error: back_callback no es callable")

    def clear_frame(self):
        self.clear_content()

    def back_to_main(self):
        self.init_ui()

if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    window = Logbook()
    window.show()
    sys.exit(app.exec())
