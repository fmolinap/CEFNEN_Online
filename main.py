# main.py

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout,
    QFrame, QGroupBox, QSizePolicy, QGridLayout, QMessageBox, QLineEdit, QDialog,
    QStackedWidget, QScrollArea
)
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt
from PIL import Image, ImageQt
from crear_nueva_campagna import CrearNuevaCampagna
from agregar_datos import AgregarDatos
from calibrate import Calibrate
from plot_cr_evo import PlotCREvo
from plot_comparison import PlotComparison
from noise_analysis import NoiseAnalysis
from calibration_root import CalibrationRoot
from recalibrate_root import RecalibrateRoot
from fetch_root_files import FetchRootFiles
from fetch_dlt_files import FetchDLTFiles
from fetch_config_files import FetchConfigFiles
from send_config_files_to_remote import SendConfigFilesToRemote
from send_offline_config_files import SendOfflineConfigFiles
from lookuptable_setup import LookUpTableSetup
from incident_report import IncidentReport
from reporte_fin_de_campagna import ReporteFinCampagnaWindow
from generar_archivo_calibracion import GenerarArchivoCalibracionGASIFIC

# Importar funciones y clases adicionales
from monitoreo_archivos_remotos import MonitoringThread, MonitoringDialog
from utils import get_campaign_info

class MainApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CEFNEN Online Analysis Experimental Campaigns")
        self.resize(800, 600)

        # Cargar y redimensionar la imagen
        original_image = Image.open("Logo_CEFNEN.png")
        desired_width = 150
        aspect_ratio = original_image.height / original_image.width
        desired_height = int(desired_width * aspect_ratio)
        resized_image = original_image.resize(
            (desired_width, desired_height),
            Image.LANCZOS
        )
        self.logo_image = ImageQt.ImageQt(resized_image)
        self.logo_pixmap = QPixmap.fromImage(self.logo_image)

        self.monitoring_thread = None

        self.init_ui()

    def init_ui(self):
        # Crear el widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Crear el layout principal
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)

        # Sección superior: Controles de monitoreo y título
        top_layout = QVBoxLayout()
        main_layout.addLayout(top_layout)

        # Logo y Título
        header_layout = QVBoxLayout()
        top_layout.addLayout(header_layout)

        logo_label = QLabel()
        logo_label.setPixmap(self.logo_pixmap)
        logo_label.setAlignment(Qt.AlignCenter)
        header_layout.addWidget(logo_label)

        title_label = QLabel("CEFNEN Online Analysis \nExperimental Campaigns")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("font-size: 24px; font-weight: bold;")
        header_layout.addWidget(title_label)

        # Subtítulo
        subtitle_label = QLabel(
            "Este es el programa de análisis online de las campañas experimentales de CEFNEN. "
            "Ha sido desarrollado en 2024 para facilitar el análisis online de los datos "
            "de las Campañas en terreno."
        )
        subtitle_label.setWordWrap(True)
        subtitle_label.setAlignment(Qt.AlignCenter)
        subtitle_label.setStyleSheet("font-size: 14px;")
        header_layout.addWidget(subtitle_label)

        # Controles de monitoreo
        self.create_monitoring_controls(top_layout)

        # Separador
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        top_layout.addWidget(separator)

        # Sección central: Área de contenido cambiante con scroll
        content_scroll_area = QScrollArea()
        content_scroll_area.setWidgetResizable(True)
        main_layout.addWidget(content_scroll_area)

        self.content_widget = QStackedWidget()
        content_scroll_area.setWidget(self.content_widget)

        # Añadir la ventana principal al QStackedWidget
        self.main_window_widget = QWidget()
        self.create_main_window_ui(self.main_window_widget)
        self.content_widget.addWidget(self.main_window_widget)

        # Mostrar la ventana principal
        self.content_widget.setCurrentWidget(self.main_window_widget)

    def create_main_window_ui(self, parent_widget):
        # Crear el layout principal
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        parent_widget.setLayout(main_layout)

        # Layout para las secciones
        sections_layout = QGridLayout()
        sections_layout.setContentsMargins(10, 10, 10, 10)
        sections_layout.setSpacing(10)
        main_layout.addLayout(sections_layout)

        # Crear los marcos de sección en una cuadrícula
        self.create_section_frame("Campañas", self.create_campaign_buttons, sections_layout, 0, 0)
        self.create_section_frame("Gráficos", self.create_graphics_buttons, sections_layout, 0, 1)
        self.create_section_frame("Calibraciones", self.create_calibration_buttons, sections_layout, 1, 0)
        self.create_section_frame("Análisis", self.create_analysis_buttons, sections_layout, 1, 1)
        self.create_section_frame("Gestión de Archivos", self.create_file_management_buttons, sections_layout, 2, 0, 1, 2)

        main_layout.addStretch()

    def create_section_frame(self, title, create_buttons_func, parent_layout, row, col, rowspan=1, colspan=1):
        group_box = QGroupBox(title)
        layout = QVBoxLayout()
        group_box.setLayout(layout)
        create_buttons_func(layout)
        group_box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        parent_layout.addWidget(group_box, row, col, rowspan, colspan)

    def create_campaign_buttons(self, layout):
        btn_new_campaign = QPushButton("Crear Nueva Campaña")
        btn_new_campaign.clicked.connect(self.open_create_campaign)
        btn_new_campaign.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        layout.addWidget(btn_new_campaign)

        btn_add_data = QPushButton("Agregar Datos a Campaña en Curso")
        btn_add_data.clicked.connect(self.open_add_data)
        btn_add_data.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        layout.addWidget(btn_add_data)

        btn_incident_report = QPushButton("Bitácora de Campaña")
        btn_incident_report.clicked.connect(self.open_incident_report)
        btn_incident_report.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        layout.addWidget(btn_incident_report)

        btn_lookup_table = QPushButton("LookUpTable Setup")
        btn_lookup_table.clicked.connect(self.open_lookup_table_setup)
        btn_lookup_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        layout.addWidget(btn_lookup_table)

        btn_generate_report = QPushButton("Generar Reporte Fin de Campaña")
        btn_generate_report.clicked.connect(self.open_generate_report)
        btn_generate_report.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        layout.addWidget(btn_generate_report)

        layout.addStretch()

    def create_graphics_buttons(self, layout):
        btn_plot_cr_evo = QPushButton("Plot Neutron Counting Rates")
        btn_plot_cr_evo.clicked.connect(self.open_plot_cr_evo)
        btn_plot_cr_evo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        layout.addWidget(btn_plot_cr_evo)

        btn_plot_comparison = QPushButton("Plot Campaigns Comparison")
        btn_plot_comparison.clicked.connect(self.open_plot_comparison)
        btn_plot_comparison.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        layout.addWidget(btn_plot_comparison)

        layout.addStretch()

    def create_calibration_buttons(self, layout):
        btn_calibrate = QPushButton("Calibrate")
        btn_calibrate.clicked.connect(self.open_calibrate)
        btn_calibrate.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        layout.addWidget(btn_calibrate)

        btn_calibration_root = QPushButton("Calibrar desde ROOT")
        btn_calibration_root.clicked.connect(self.open_calibration_from_root)
        btn_calibration_root.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        layout.addWidget(btn_calibration_root)

        btn_recalibrate_root = QPushButton("Recalibrar desde ROOT")
        btn_recalibrate_root.clicked.connect(self.open_recalibrate_root)
        btn_recalibrate_root.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        layout.addWidget(btn_recalibrate_root)

        btn_generate_calibration_gasific = QPushButton("Generar Archivo de Calibración GASIFIC")
        btn_generate_calibration_gasific.clicked.connect(self.open_generate_calibration_gasific)
        btn_generate_calibration_gasific.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        layout.addWidget(btn_generate_calibration_gasific)

        layout.addStretch()

    def create_analysis_buttons(self, layout):
        btn_noise_analysis = QPushButton("Online Noise Analysis")
        btn_noise_analysis.clicked.connect(self.open_noise_analysis)
        btn_noise_analysis.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        layout.addWidget(btn_noise_analysis)

        layout.addStretch()

    def create_file_management_buttons(self, layout):
        btn_fetch_root = QPushButton("Traer archivos ROOT desde PC Adquisición")
        btn_fetch_root.clicked.connect(self.open_fetch_root_files)
        btn_fetch_root.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        layout.addWidget(btn_fetch_root)

        btn_fetch_dlt = QPushButton("Traer archivos DLT desde PC Adquisición")
        btn_fetch_dlt.clicked.connect(self.open_fetch_dlt_files)
        btn_fetch_dlt.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        layout.addWidget(btn_fetch_dlt)

        btn_fetch_config = QPushButton("Traer archivos XLSX de configuración de GASIFIC")
        btn_fetch_config.clicked.connect(self.open_fetch_config_files)
        btn_fetch_config.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        layout.addWidget(btn_fetch_config)

        btn_send_config = QPushButton("Enviar archivos XLSX de configuración de GASIFIC al PC de Adquisición")
        btn_send_config.clicked.connect(self.open_send_config_files_to_remote)
        btn_send_config.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        layout.addWidget(btn_send_config)

        btn_send_offline_config = QPushButton("Enviar archivos de configuración CSV Offline")
        btn_send_offline_config.clicked.connect(self.open_send_offline_config_files)
        btn_send_offline_config.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        layout.addWidget(btn_send_offline_config)

        layout.addStretch()

    def create_monitoring_controls(self, layout):
        monitor_layout = QHBoxLayout()

        self.start_monitor_button = QPushButton("Iniciar Monitoreo")
        self.start_monitor_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.start_monitor_button.clicked.connect(self.start_monitoring)
        monitor_layout.addWidget(self.start_monitor_button)

        self.stop_monitor_button = QPushButton("Terminar Monitoreo")
        self.stop_monitor_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.stop_monitor_button.clicked.connect(self.stop_monitoring)
        self.stop_monitor_button.setEnabled(False)  # Deshabilitado inicialmente
        monitor_layout.addWidget(self.stop_monitor_button)

        self.monitor_status_label = QLabel("Monitoreo: <font color='red'>OFF</font>")
        self.monitor_status_label.setAlignment(Qt.AlignCenter)
        monitor_layout.addWidget(self.monitor_status_label)

        layout.addLayout(monitor_layout)

        # Etiquetas para mostrar los últimos archivos
        self.last_root_label = QLabel("Último archivo ROOT: N/A")
        self.last_root_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.last_root_label)

        self.last_dlt_label = QLabel("Último archivo DLT: N/A")
        self.last_dlt_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.last_dlt_label)

    def start_monitoring(self):
        dialog = MonitoringDialog(self)
        if dialog.exec() == QDialog.Accepted:
            campaign, ip, username, password = dialog.get_monitoring_info()

            campaign_info = get_campaign_info(campaign)
            if campaign_info is None:
                QMessageBox.critical(self, "Error", f"No se pudo obtener la información para la campaña '{campaign}'.")
                return

            root_path = campaign_info.get('ROOT Path')
            dlt_path = campaign_info.get('DLT Path')

            # Iniciar el hilo de monitoreo
            self.monitoring_thread = MonitoringThread(ip, username, password, root_path, dlt_path)
            self.monitoring_thread.monitoring_status_changed.connect(self.update_monitor_status)
            self.monitoring_thread.error_signal.connect(self.handle_monitoring_error)
            self.monitoring_thread.new_files_detected.connect(self.update_last_files)
            self.monitoring_thread.start()
            self.update_monitor_status(True)
        else:
            pass  # El usuario canceló el diálogo

    def stop_monitoring(self):
        if hasattr(self, 'monitoring_thread') and self.monitoring_thread is not None and self.monitoring_thread.isRunning():
            self.monitoring_thread.stop()
            self.monitoring_thread.wait()
        self.update_monitor_status(False)

    def update_monitor_status(self, status):
        if status:
            self.monitor_status_label.setText("Monitoreo: <font color='green'>ON</font>")
            self.start_monitor_button.setEnabled(False)
            self.stop_monitor_button.setEnabled(True)
        else:
            self.monitor_status_label.setText("Monitoreo: <font color='red'>OFF</font>")
            self.start_monitor_button.setEnabled(True)
            self.stop_monitor_button.setEnabled(False)
            self.last_root_label.setText("Último archivo ROOT: N/A")
            self.last_dlt_label.setText("Último archivo DLT: N/A")

    def handle_monitoring_error(self, error_message):
        QMessageBox.critical(self, "Error en el Monitoreo", f"Ocurrió un error durante el monitoreo:\n{error_message}")
        self.update_monitor_status(False)

    def update_last_files(self, last_root_file, last_dlt_file):
        self.last_root_label.setText(f"Último archivo ROOT: {last_root_file}")
        self.last_dlt_label.setText(f"Último archivo DLT: {last_dlt_file}")

    # Métodos para abrir las diferentes ventanas
    def open_create_campaign(self):
        widget = CrearNuevaCampagna(back_callback=self.return_to_main_window)
        self.show_new_widget(widget)

    def open_add_data(self):
        widget = AgregarDatos(back_callback=self.return_to_main_window)
        self.show_new_widget(widget)

    def open_fetch_root_files(self):
        widget = FetchRootFiles(back_callback=self.return_to_main_window)
        self.show_new_widget(widget)

    def open_fetch_dlt_files(self):
        widget = FetchDLTFiles(back_callback=self.return_to_main_window)
        self.show_new_widget(widget)

    def open_fetch_config_files(self):
        widget = FetchConfigFiles(back_callback=self.return_to_main_window)
        self.show_new_widget(widget)

    def open_send_config_files_to_remote(self):
        widget = SendConfigFilesToRemote(back_callback=self.return_to_main_window)
        self.show_new_widget(widget)

    def open_send_offline_config_files(self):
        widget = SendOfflineConfigFiles(back_callback=self.return_to_main_window)
        self.show_new_widget(widget)

    def open_incident_report(self):
        # Obtener el último archivo DLT desde la etiqueta
        last_dlt_file = self.last_dlt_label.text().replace("Último archivo DLT: ", "")
        if last_dlt_file == "N/A":
            last_dlt_file = ""
        widget = IncidentReport(back_callback=self.return_to_main_window, last_dlt_file=last_dlt_file)
        self.show_new_widget(widget)

    def open_lookup_table_setup(self):
        widget = LookUpTableSetup(back_callback=self.return_to_main_window)
        self.show_new_widget(widget)

    def open_plot_cr_evo(self):
        widget = PlotCREvo(back_callback=self.return_to_main_window)
        self.show_new_widget(widget)

    def open_plot_comparison(self):
        widget = PlotComparison(back_callback=self.return_to_main_window)
        self.show_new_widget(widget)

    def open_calibrate(self):
        widget = Calibrate(back_callback=self.return_to_main_window)
        self.show_new_widget(widget)

    def open_calibration_from_root(self):
        widget = CalibrationRoot(back_callback=self.return_to_main_window)
        self.show_new_widget(widget)

    def open_recalibrate_root(self):
        widget = RecalibrateRoot(back_callback=self.return_to_main_window)
        self.show_new_widget(widget)

    def open_generate_calibration_gasific(self):
        widget = GenerarArchivoCalibracionGASIFIC(back_callback=self.return_to_main_window)
        self.show_new_widget(widget)

    def open_noise_analysis(self):
        widget = NoiseAnalysis(back_callback=self.return_to_main_window)
        self.show_new_widget(widget)

    def open_generate_report(self):
        widget = ReporteFinCampagnaWindow(back_callback=self.return_to_main_window)
        self.show_new_widget(widget)

    def show_new_widget(self, widget):
        self.content_widget.addWidget(widget)
        self.content_widget.setCurrentWidget(widget)

    def return_to_main_window(self):
        self.content_widget.setCurrentWidget(self.main_window_widget)

def main():
    import sys
    app = QApplication(sys.argv)
    window = MainApp()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
