# main.py

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout,
    QFrame, QGroupBox, QSizePolicy, QGridLayout, QMessageBox, QLineEdit, QDialog,
    QStackedWidget, QScrollArea
)
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt
from PIL import Image, ImageQt

# Importar los módulos de las diferentes ventanas
from crear_nueva_campagna import CrearNuevaCampagna
from agregar_datos import AgregarDatos
from calibrate import Calibrate
from plot_cr_evo import PlotCREvo
from plot_comparison import PlotComparison
from plot_meteorological_data import PlotMeteorologicalData  # Nuevo módulo
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
from plot_root_histograms import PlotRootHistograms
from analisis_estadistico_descriptivo import AnalisisEstadisticoDescriptivo

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

        title_label = QLabel("CEFNEN Online Analysis Experimental Campaigns")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("font-size: 24px; font-weight: bold;")
        header_layout.addWidget(title_label)

        # Subtítulo
        subtitle_label = QLabel(
            "Programa de análisis online de las campañas experimentales de CEFNEN. fmolinap2024"
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

        # Sección central: Área de contenido cambiante sin scroll
        self.content_widget = QStackedWidget()
        main_layout.addWidget(self.content_widget)

        # Añadir la ventana principal al QStackedWidget
        self.main_window_widget = QWidget()
        self.create_main_window_ui(self.main_window_widget)
        self.content_widget.addWidget(self.main_window_widget)

        # Añadir un placeholder para los subprogramas
        self.subprogram_scroll_area = QScrollArea()
        self.subprogram_scroll_area.setWidgetResizable(True)
        # No se establece ningún widget todavía
        self.content_widget.addWidget(self.subprogram_scroll_area)

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

        # Nuevo botón para graficar histogramas ROOT
        btn_plot_root_histograms = QPushButton("Plot ROOT Histograms")
        btn_plot_root_histograms.clicked.connect(self.open_plot_root_histograms)
        btn_plot_root_histograms.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        layout.addWidget(btn_plot_root_histograms)

        # Nuevo botón para graficar datos de estación meteorológica
        btn_plot_meteorological_data = QPushButton("Plot Meteorological Data")
        btn_plot_meteorological_data.clicked.connect(self.open_plot_meteorological_data)
        btn_plot_meteorological_data.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        layout.addWidget(btn_plot_meteorological_data)

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

        btn_statistical_analysis = QPushButton("Análisis Estadístico Descriptivo")
        btn_statistical_analysis.clicked.connect(self.open_statistical_analysis)
        btn_statistical_analysis.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        layout.addWidget(btn_statistical_analysis)

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
        self.start_monitor_button.setStyleSheet("background-color: green; color: white;")
        monitor_layout.addWidget(self.start_monitor_button)

        self.exit_button = QPushButton("Salir de CEFNEN Online")
        self.exit_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.exit_button.clicked.connect(self.exit_application)
        self.exit_button.setStyleSheet("background-color: red; color: white;")
        monitor_layout.addWidget(self.exit_button)

        self.monitor_status_label = QLabel("Monitoring: <font color='red'>OFF</font>")
        self.monitor_status_label.setAlignment(Qt.AlignCenter)
        monitor_layout.addWidget(self.monitor_status_label)

        layout.addLayout(monitor_layout)

        # Etiquetas para mostrar los últimos archivos y el tiempo total de medida
        info_layout = QGridLayout()
        info_layout.setContentsMargins(0, 0, 0, 0)
        info_layout.setSpacing(2)

        small_font_size = "font-size: 15px;"

        self.last_root_label = QLabel("Last ROOT file: N/A")
        self.last_root_label.setAlignment(Qt.AlignCenter)
        self.last_root_label.setStyleSheet(small_font_size)
        info_layout.addWidget(self.last_root_label, 0, 0)

        self.last_dlt_label = QLabel("Last DLT file: N/A")
        self.last_dlt_label.setAlignment(Qt.AlignCenter)
        self.last_dlt_label.setStyleSheet(small_font_size)
        info_layout.addWidget(self.last_dlt_label, 0, 1)

        self.meteor_file_size_label = QLabel("Size MS file: N/A")
        self.meteor_file_size_label.setAlignment(Qt.AlignCenter)
        self.meteor_file_size_label.setStyleSheet(small_font_size)
        info_layout.addWidget(self.meteor_file_size_label, 1, 0)

        self.total_measurement_time_label = QLabel("Total Measurement Time: N/A")
        self.total_measurement_time_label.setAlignment(Qt.AlignCenter)
        self.total_measurement_time_label.setStyleSheet(small_font_size)
        info_layout.addWidget(self.total_measurement_time_label, 1, 1)

        layout.addLayout(info_layout)

    def start_monitoring(self):
        dialog = MonitoringDialog(self)
        if dialog.exec() == QDialog.Accepted:
            campaign, ip, username, password, smb_username, smb_password, smb_ip, smb_hostname = dialog.get_monitoring_info()

            campaign_info = get_campaign_info(campaign)
            if campaign_info is None:
                QMessageBox.critical(self, "Error", f"No se pudo obtener la información para la campaña '{campaign}'.")
                return

            root_path = campaign_info.get('ROOT Path')
            dlt_path = campaign_info.get('DLT Path')

            # Iniciar el hilo de monitoreo
            self.monitoring_thread = MonitoringThread(
                ip,
                username,
                password,
                root_path,
                dlt_path,
                smb_username,
                smb_password,
                smb_ip,
                smb_hostname
            )
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

    def exit_application(self):
        self.stop_monitoring()
        self.close()

    def update_monitor_status(self, status):
        if status:
            self.monitor_status_label.setText("Monitoring: <font color='green'>ON</font>")
            self.start_monitor_button.setEnabled(False)
        else:
            self.monitor_status_label.setText("Monitoring: <font color='red'>OFF</font>")
            self.start_monitor_button.setEnabled(True)
            self.last_root_label.setText("Last ROOT file: N/A")
            self.last_dlt_label.setText("Last DLT file: N/A")
            self.meteor_file_size_label.setText("Size MS file: N/A")
            self.total_measurement_time_label.setText("Total Measurement Time: N/A")

    def handle_monitoring_error(self, error_message):
        QMessageBox.critical(self, "Error en el Monitoreo", f"Ocurrió un error durante el monitoreo:\n{error_message}")
        self.update_monitor_status(False)

    def update_last_files(self, last_root_file, last_dlt_file, meteor_file_size, total_measurement_time):
        self.last_root_label.setText(f"Last ROOT file: {last_root_file}")
        self.last_dlt_label.setText(f"Last DLT file: {last_dlt_file}")
        if meteor_file_size >= 0:
            size_kb = meteor_file_size / 1024
            self.meteor_file_size_label.setText(f"Size MS file: {size_kb:.2f} KB")
        else:
            self.meteor_file_size_label.setText("Size MS file: N/A")
        # Actualizar el tiempo total de medida
        days, remainder = divmod(total_measurement_time, 86400)
        hours, remainder = divmod(remainder, 3600)
        minutes, _ = divmod(remainder, 60)
        self.total_measurement_time_label.setText(f"Total Measurement Time: {int(days)}d {int(hours)}h {int(minutes)}m")

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
        last_dlt_file = self.last_dlt_label.text().replace("Last DLT file: ", "")
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

    def open_plot_root_histograms(self):
        widget = PlotRootHistograms(back_callback=self.return_to_main_window)
        self.show_new_widget(widget)

    def open_plot_meteorological_data(self):
        widget = PlotMeteorologicalData(back_callback=self.return_to_main_window)
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

    def open_statistical_analysis(self):
        widget = AnalisisEstadisticoDescriptivo(back_callback=self.return_to_main_window)
        self.show_new_widget(widget)

    def open_generate_report(self):
        widget = ReporteFinCampagnaWindow(back_callback=self.return_to_main_window)
        self.show_new_widget(widget)

    def show_new_widget(self, widget):
        # Establecer el widget dentro del scroll area
        self.subprogram_scroll_area.setWidget(widget)
        # Cambiar al scroll area que contiene el subprograma
        self.content_widget.setCurrentWidget(self.subprogram_scroll_area)

    def return_to_main_window(self):
        # Quitar el widget del scroll area
        self.subprogram_scroll_area.takeWidget()
        # Cambiar de vuelta a la ventana principal
        self.content_widget.setCurrentWidget(self.main_window_widget)

def main():
    import sys
    app = QApplication(sys.argv)
    window = MainApp()
    # Ajustar el tamaño de la ventana para que ocupe la mitad izquierda de la pantalla
    screen_geometry = app.primaryScreen().availableGeometry()
    screen_width = screen_geometry.width()
    screen_height = screen_geometry.height()
    window.setGeometry(0, 0, screen_width // 2, screen_height)
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
