from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QFrame, QGroupBox
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt
from PIL import Image, ImageQt
from logbook import Logbook
from calibrate import Calibrate
from plot_cr_evo import PlotCREvo
from plot_comparison import PlotComparison
from noise_analysis import NoiseAnalysis
from calibration_root import Calibration
from recalibrate_root import RecalibrateRoot
from fetch_root_files import FetchRootFiles
from fetch_dlt_files import FetchDLTFiles
from lookuptable_setup import LookUpTableSetup
from edit_materials import EditMaterials
from incident_report import IncidentReport

class MainApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CEFNEN Online Analysis Experimental Campaigns")
        self.resize(1200, 800)

        # Cargar y redimensionar la imagen
        original_image = Image.open("Logo_CEFNEN.png")
        resized_image = original_image.resize(
            (int(original_image.width / 2), int(original_image.height / 2)),
            Image.LANCZOS
        )
        self.logo_image = ImageQt.ImageQt(resized_image)
        self.logo_pixmap = QPixmap.fromImage(self.logo_image)

        self.create_main_window()

    def create_main_window(self):
        # Crear el widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Crear el layout principal
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)

        # Logo y Título
        header_layout = QHBoxLayout()
        main_layout.addLayout(header_layout)

        logo_label = QLabel()
        logo_label.setPixmap(self.logo_pixmap)
        header_layout.addWidget(logo_label)

        title_label = QLabel("CEFNEN Online Analysis \nExperimental Campaigns")
        title_label.setAlignment(Qt.AlignCenter)
        header_layout.addWidget(title_label)

        # Subtítulo
        subtitle_label = QLabel(
            "Este es el programa de análisis online de las campañas experimentales de CEFNEN. "
            "Ha sido desarrollado en Julio de 2024 para facilitar el análisis online de los datos "
            "de la 5ta Campaña."
        )
        subtitle_label.setWordWrap(True)
        main_layout.addWidget(subtitle_label)

        # Separador
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        main_layout.addWidget(separator)

        # Layout para las secciones
        sections_layout = QHBoxLayout()
        main_layout.addLayout(sections_layout)

        # Crear los marcos de sección
        self.create_section_frame("Campañas", self.create_campaign_buttons, sections_layout)
        self.create_section_frame("Gráficos", self.create_graphics_buttons, sections_layout)
        self.create_section_frame("Calibraciones", self.create_calibration_buttons, sections_layout)
        self.create_section_frame("Análisis", self.create_analysis_buttons, sections_layout)

    def create_section_frame(self, title, create_buttons_func, parent_layout):
        group_box = QGroupBox(title)
        layout = QVBoxLayout()
        group_box.setLayout(layout)
        create_buttons_func(layout)
        parent_layout.addWidget(group_box)

    def create_campaign_buttons(self, layout):
        btn_new_campaign = QPushButton("Crear Nueva Campaña")
        btn_new_campaign.clicked.connect(self.open_create_campaign)
        layout.addWidget(btn_new_campaign)

        btn_add_data = QPushButton("Agregar Datos a Campaña en Curso")
        btn_add_data.clicked.connect(self.open_add_data)
        layout.addWidget(btn_add_data)

        btn_fetch_root = QPushButton("Traer archivos ROOT desde PC Adquisición")
        btn_fetch_root.clicked.connect(self.open_fetch_root_files)
        layout.addWidget(btn_fetch_root)

        btn_fetch_dlt = QPushButton("Traer archivos DLT desde PC Adquisición")
        btn_fetch_dlt.clicked.connect(self.open_fetch_dlt_files)
        layout.addWidget(btn_fetch_dlt)

        btn_incident_report = QPushButton("Reporte de Incidencias")
        btn_incident_report.clicked.connect(self.open_incident_report)
        layout.addWidget(btn_incident_report)

        btn_lookup_table = QPushButton("LookUpTable Setup")
        btn_lookup_table.clicked.connect(self.open_lookup_table_setup)
        layout.addWidget(btn_lookup_table)

        btn_edit_materials = QPushButton("Editar Materiales en Campaña")
        btn_edit_materials.clicked.connect(self.open_edit_materials)
        layout.addWidget(btn_edit_materials)

    def create_graphics_buttons(self, layout):
        btn_plot_cr_evo = QPushButton("Plot Neutron Counting Rates")
        btn_plot_cr_evo.clicked.connect(self.open_plot_cr_evo)
        layout.addWidget(btn_plot_cr_evo)

        btn_plot_comparison = QPushButton("Plot Campaigns Comparison")
        btn_plot_comparison.clicked.connect(self.open_plot_comparison)
        layout.addWidget(btn_plot_comparison)

    def create_calibration_buttons(self, layout):
        btn_calibrate = QPushButton("Calibrate")
        btn_calibrate.clicked.connect(self.open_calibrate)
        layout.addWidget(btn_calibrate)

        btn_calibration_root = QPushButton("Calibrar desde ROOT")
        btn_calibration_root.clicked.connect(self.open_calibration_from_root)
        layout.addWidget(btn_calibration_root)

        btn_recalibrate_root = QPushButton("Recalibrar desde ROOT")
        btn_recalibrate_root.clicked.connect(self.open_recalibrate_root)
        layout.addWidget(btn_recalibrate_root)

    def create_analysis_buttons(self, layout):
        btn_noise_analysis = QPushButton("Online Noise Analysis")
        btn_noise_analysis.clicked.connect(self.open_noise_analysis)
        layout.addWidget(btn_noise_analysis)

    # Métodos para abrir las diferentes ventanas
    def open_create_campaign(self):
        self.clear_central_widget()
        logbook = Logbook(back_callback=self.create_main_window)
        self.setCentralWidget(logbook)

    def open_add_data(self):
        self.clear_central_widget()
        logbook = Logbook(back_callback=self.create_main_window)
        self.setCentralWidget(logbook)

    def open_fetch_root_files(self):
        self.clear_central_widget()
        fetch_root_files = FetchRootFiles(back_callback=self.create_main_window)
        self.setCentralWidget(fetch_root_files)

    def open_fetch_dlt_files(self):
        self.clear_central_widget()
        fetch_dlt_files = FetchDLTFiles(back_callback=self.create_main_window)
        self.setCentralWidget(fetch_dlt_files)

    def open_incident_report(self):
        self.clear_central_widget()
        incident_report = IncidentReport(back_callback=self.create_main_window)
        self.setCentralWidget(incident_report)

    def open_lookup_table_setup(self):
        self.clear_central_widget()
        lookup_table_setup = LookUpTableSetup(back_callback=self.create_main_window)
        self.setCentralWidget(lookup_table_setup)

    def open_edit_materials(self):
        self.clear_central_widget()
        edit_materials = EditMaterials(back_callback=self.create_main_window)
        self.setCentralWidget(edit_materials)

    def open_plot_cr_evo(self):
        self.clear_central_widget()
        plot_cr_evo = PlotCREvo(back_callback=self.create_main_window)
        self.setCentralWidget(plot_cr_evo)

    def open_plot_comparison(self):
        self.clear_central_widget()
        plot_comparison = PlotComparison(back_callback=self.create_main_window)
        self.setCentralWidget(plot_comparison)

    def open_calibrate(self):
        self.clear_central_widget()
        calibrate_widget = Calibrate(back_callback=self.create_main_window)
        self.setCentralWidget(calibrate_widget)

    def open_calibration_from_root(self):
        self.clear_central_widget()
        calibration_widget = Calibration(back_callback=self.create_main_window)
        self.setCentralWidget(calibration_widget)

    def open_recalibrate_root(self):
        self.clear_central_widget()
        recalibrate_root = RecalibrateRoot(back_callback=self.create_main_window)
        self.setCentralWidget(recalibrate_root)

    def open_noise_analysis(self):
        self.clear_central_widget()
        noise_analysis = NoiseAnalysis(back_callback=self.create_main_window)
        self.setCentralWidget(noise_analysis)

    def clear_central_widget(self):
        # Elimina el widget central actual
        current_widget = self.centralWidget()
        if current_widget is not None:
            current_widget.deleteLater()
        # Establece un nuevo central_widget vacío
        self.setCentralWidget(QWidget())

if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    window = MainApp()
    window.show()
    sys.exit(app.exec())
