# crear_nueva_campagna.py

from PySide6.QtWidgets import (
    QWidget, QLabel, QLineEdit, QPushButton, QMessageBox, QVBoxLayout, QHBoxLayout,
    QRadioButton, QButtonGroup, QGridLayout
)
from PySide6.QtCore import Qt
import pandas as pd
import os
from utils import get_existing_campaigns

class CrearNuevaCampagna(QWidget):
    def __init__(self, back_callback=None):
        super().__init__()
        self.back_callback = back_callback
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Creando Nueva Campaña Experimental CEFNEN")
        self.resize(900, 700)

        # Layout principal
        self.main_layout = QVBoxLayout(self)
        self.setLayout(self.main_layout)

        # Título y subtítulo
        title = QLabel("Creando Nueva Campaña Experimental CEFNEN")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 24px; font-weight: bold;")
        self.main_layout.addWidget(title)

        subtitle = QLabel(
            "Ingresa los datos correspondientes a la nueva campaña experimental CEFNEN. "
            "Esta información será utilizada en todo el programa de análisis online y se encontrará "
            "en el archivo ./data/info_campaigns.csv que se recomienda no editar. Asegúrate de que el "
            "nombre corto sea representativo y único para esta campaña ya que es la base de todo el análisis."
        )
        subtitle.setWordWrap(True)
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("font-size: 14px;")
        self.main_layout.addWidget(subtitle)

        # Formulario
        form_layout = QGridLayout()
        self.main_layout.addLayout(form_layout)

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
        form_layout.addLayout(num_layout, 0, 0, 1, 2)

        # Campo para "otra" campaña
        self.other_entry = QLineEdit()
        self.other_entry.setPlaceholderText("Especifique otro número de campaña")
        self.other_entry.setVisible(False)
        form_layout.addWidget(self.other_entry, 1, 0, 1, 2)

        # Campos de entrada
        self.location = QLineEdit()
        self.latitude = QLineEdit()
        self.longitude = QLineEdit()
        self.geomagnetic_cutoff = QLineEdit()
        self.start_date = QLineEdit()
        self.end_date = QLineEdit()
        self.short_name = QLineEdit()
        self.num_detectors = QLineEdit()
        self.dlt_path = QLineEdit()
        self.root_path = QLineEdit()

        form_layout.addWidget(QLabel("Lugar:"), 2, 0)
        form_layout.addWidget(self.location, 2, 1)

        form_layout.addWidget(QLabel("Latitud:"), 3, 0)
        form_layout.addWidget(self.latitude, 3, 1)

        form_layout.addWidget(QLabel("Longitud:"), 4, 0)
        form_layout.addWidget(self.longitude, 4, 1)

        form_layout.addWidget(QLabel("Corte de Rigidez Geomagnética:"), 5, 0)
        form_layout.addWidget(self.geomagnetic_cutoff, 5, 1)

        form_layout.addWidget(QLabel("Fecha de Inicio (AA/MM/DD):"), 6, 0)
        form_layout.addWidget(self.start_date, 6, 1)

        form_layout.addWidget(QLabel("Fecha de Término (AA/MM/DD):"), 7, 0)
        form_layout.addWidget(self.end_date, 7, 1)

        form_layout.addWidget(QLabel("Nombre Corto:"), 8, 0)
        form_layout.addWidget(self.short_name, 8, 1)

        form_layout.addWidget(QLabel("Número de Detectores:"), 9, 0)
        form_layout.addWidget(self.num_detectors, 9, 1)

        form_layout.addWidget(QLabel("Path Completo a los Archivos .dlt:"), 10, 0)
        form_layout.addWidget(self.dlt_path, 10, 1)

        form_layout.addWidget(QLabel("Path Completo a los Archivos .root:"), 11, 0)
        form_layout.addWidget(self.root_path, 11, 1)

        # Botones
        buttons_layout = QHBoxLayout()
        save_button = QPushButton("Guardar")
        save_button.clicked.connect(self.save_new_campaign)
        save_button.setStyleSheet("background-color: #4CAF50; color: white;")  # Botón verde
        buttons_layout.addWidget(save_button)

        back_button = QPushButton("Regresar")
        back_button.clicked.connect(self.back)
        back_button.setStyleSheet("background-color: #f44336; color: white;")  # Botón rojo
        buttons_layout.addWidget(back_button)

        self.main_layout.addLayout(buttons_layout)

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
            QLineEdit {
                font-size: 14px;
            }
        """)

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
            "Latitud": self.latitude.text().strip(),
            "Longitud": self.longitude.text().strip(),
            "Corte de Rigidez Geomagnética": self.geomagnetic_cutoff.text().strip(),
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
                "Numero", "Lugar", "Latitud", "Longitud", "Corte de Rigidez Geomagnética",
                "Fecha de Inicio", "Fecha de Termino", "Nombre Corto",
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
        header = ["timestamp", "dlt_file"]
        for i in range(campaign_info['Número de Detectores']):
            header.extend([
                f"detector_{i+1}_total_counts",
                f"detector_{i+1}_neutron_counts"
            ])
        header.extend(["observations"])
        df_counts = pd.DataFrame(columns=header)
        df_counts.to_csv(file_name, index=False)

        QMessageBox.information(self, "Éxito", "Campaña creada y guardada con éxito.")
        self.back()

    def back(self):
        if callable(self.back_callback):
            self.back_callback()
        else:
            print("Error: back_callback no es callable")
