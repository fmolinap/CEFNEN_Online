from PySide6.QtWidgets import (
    QWidget, QLabel, QLineEdit, QPushButton, QMessageBox, QVBoxLayout, QHBoxLayout,
    QRadioButton, QButtonGroup, QGridLayout
)
from PySide6.QtCore import Qt
import pandas as pd
import os
from utils import get_existing_campaigns
from geopy.geocoders import Nominatim
import pyIGRF
import math
from datetime import datetime
import urllib.parse

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

        # Opciones de entrada de ubicación
        self.input_option_label = QLabel("Seleccione el método de entrada de ubicación:")
        self.address_radio = QRadioButton("Dirección o lugar")
        self.coords_radio = QRadioButton("Latitud y longitud")
        self.address_radio.setChecked(True)

        self.input_option_group = QButtonGroup()
        self.input_option_group.addButton(self.address_radio)
        self.input_option_group.addButton(self.coords_radio)
        self.input_option_group.buttonClicked.connect(self.toggle_input_method)

        form_layout.addWidget(self.input_option_label, 2, 0)
        location_options_layout = QHBoxLayout()
        location_options_layout.addWidget(self.address_radio)
        location_options_layout.addWidget(self.coords_radio)
        form_layout.addLayout(location_options_layout, 2, 1)

        # Campos para dirección
        self.location_label = QLabel("Dirección o lugar:")
        self.location_input = QLineEdit()
        self.location_input.setPlaceholderText("Ingrese una ciudad o dirección")
        form_layout.addWidget(self.location_label, 3, 0)
        form_layout.addWidget(self.location_input, 3, 1)

        # Campos de coordenadas
        self.lat_label = QLabel("Latitud:")
        self.lat_input = QLineEdit()
        self.lat_input.setPlaceholderText("Ejemplo: -23.65")
        self.lon_label = QLabel("Longitud:")
        self.lon_input = QLineEdit()
        self.lon_input.setPlaceholderText("Ejemplo: -70.40")
        coords_layout = QHBoxLayout()
        coords_layout.addWidget(self.lat_label)
        coords_layout.addWidget(self.lat_input)
        coords_layout.addWidget(self.lon_label)
        coords_layout.addWidget(self.lon_input)
        form_layout.addLayout(coords_layout, 4, 0, 1, 2)

        # Campo de altitud
        self.alt_label = QLabel("Altitud (msnm):")
        self.alt_input = QLineEdit()
        self.alt_input.setPlaceholderText("Ejemplo: 500 (metros sobre el nivel del mar)")
        form_layout.addWidget(self.alt_label, 5, 0)
        form_layout.addWidget(self.alt_input, 5, 1)

        # Campo de fecha
        self.date_label = QLabel("Fecha (AA/MM/DD):")
        self.date_input = QLineEdit()
        self.date_input.setPlaceholderText("AA/MM/DD")
        form_layout.addWidget(self.date_label, 6, 0)
        form_layout.addWidget(self.date_input, 6, 1)

        # Botón para calcular parámetros geomagnéticos
        self.calculate_geomag_button = QPushButton("Calcular Parámetros Geomagnéticos")
        self.calculate_geomag_button.clicked.connect(self.calculate_parameters)
        form_layout.addWidget(self.calculate_geomag_button, 7, 0, 1, 2)

        # Campos de latitud, longitud y Rc
        self.latitude = QLineEdit()
        self.longitude = QLineEdit()
        self.geomagnetic_cutoff = QLineEdit()

        form_layout.addWidget(QLabel("Latitud:"), 8, 0)
        form_layout.addWidget(self.latitude, 8, 1)

        form_layout.addWidget(QLabel("Longitud:"), 9, 0)
        form_layout.addWidget(self.longitude, 9, 1)

        form_layout.addWidget(QLabel("Corte de Rigidez Geomagnética (Rc):"), 10, 0)
        form_layout.addWidget(self.geomagnetic_cutoff, 10, 1)

        # Campos adicionales
        self.start_date = QLineEdit()
        self.end_date = QLineEdit()
        self.short_name = QLineEdit()
        self.num_detectors = QLineEdit()
        self.dlt_path = QLineEdit()
        self.root_path = QLineEdit()

        form_layout.addWidget(QLabel("Fecha de Inicio (AA/MM/DD):"), 11, 0)
        form_layout.addWidget(self.start_date, 11, 1)

        form_layout.addWidget(QLabel("Fecha de Término (AA/MM/DD):"), 12, 0)
        form_layout.addWidget(self.end_date, 12, 1)

        form_layout.addWidget(QLabel("Nombre Corto:"), 13, 0)
        form_layout.addWidget(self.short_name, 13, 1)

        form_layout.addWidget(QLabel("Número de Detectores:"), 14, 0)
        form_layout.addWidget(self.num_detectors, 14, 1)

        form_layout.addWidget(QLabel("Path Completo a los Archivos .dlt:"), 15, 0)
        form_layout.addWidget(self.dlt_path, 15, 1)

        form_layout.addWidget(QLabel("Path Completo a los Archivos .root:"), 16, 0)
        form_layout.addWidget(self.root_path, 16, 1)

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

        self.toggle_input_method()

    def toggle_input_method(self):
        if self.address_radio.isChecked():
            # Mostrar campos de dirección
            self.location_label.setVisible(True)
            self.location_input.setVisible(True)
            self.lat_label.setVisible(False)
            self.lat_input.setVisible(False)
            self.lon_label.setVisible(False)
            self.lon_input.setVisible(False)
        else:
            # Mostrar campos de coordenadas
            self.location_label.setVisible(False)
            self.location_input.setVisible(False)
            self.lat_label.setVisible(True)
            self.lat_input.setVisible(True)
            self.lon_label.setVisible(True)
            self.lon_input.setVisible(True)

    def check_other(self):
        if self.campaign_num_group.checkedButton() and self.campaign_num_group.checkedButton().text() == "otra":
            self.other_entry.setVisible(True)
        else:
            self.other_entry.setVisible(False)

    def calculate_parameters(self):
        try:
            if self.address_radio.isChecked():
                location_name = self.location_input.text().strip()
                if not location_name:
                    QMessageBox.warning(self, "Advertencia", "Por favor, ingrese una dirección o lugar.")
                    return

                # Geocodificación
                geolocator = Nominatim(user_agent="geomag_app")
                location = geolocator.geocode(location_name)

                if location is None:
                    QMessageBox.warning(self, "Advertencia", "No se pudo encontrar la ubicación. Intente con otra dirección.")
                    return

                latitude = location.latitude
                longitude = location.longitude
            else:
                lat_text = self.lat_input.text().strip()
                lon_text = self.lon_input.text().strip()
                if not lat_text or not lon_text:
                    QMessageBox.warning(self, "Advertencia", "Por favor, ingrese latitud y longitud.")
                    return
                try:
                    latitude = float(lat_text)
                    longitude = float(lon_text)
                except ValueError:
                    QMessageBox.warning(self, "Advertencia", "Latitud y longitud deben ser números.")
                    return

            # Obtener la altitud
            alt_text = self.alt_input.text().strip()
            if alt_text:
                try:
                    altitude = float(alt_text) / 1000  # Convertir de metros a kilómetros
                except ValueError:
                    QMessageBox.warning(self, "Advertencia", "La altitud debe ser un número.")
                    return
            else:
                altitude = 0  # Asumir nivel del mar si no se ingresa altitud

            # Obtener la fecha
            date_text = self.date_input.text().strip()
            if date_text:
                try:
                    date = datetime.strptime(date_text, "%y/%m/%d")
                except ValueError:
                    QMessageBox.warning(self, "Advertencia", "La fecha debe estar en formato AA/MM/DD.")
                    return
            else:
                date = datetime.now()

            # Calcular los parámetros geomagnéticos
            results = self.calculate_geomagnetic_parameters(latitude, longitude, altitude, date)

            if results is not None:
                # Rellenar los campos con los valores calculados
                self.latitude.setText(f"{latitude:.6f}")
                self.longitude.setText(f"{longitude:.6f}")
                self.geomagnetic_cutoff.setText(f"{results['Rc']:.2f}")
                # Almacenar B_N, B_E, B_D y altitud
                self.B_N = results['B_N']
                self.B_E = results['B_E']
                self.B_D = results['B_D']
                self.altitude = altitude * 1000  # Convertir de km a metros
            else:
                QMessageBox.critical(self, "Error", "Error en el cálculo de los parámetros geomagnéticos.")
        except Exception as e:
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, "Error", f"Error en el cálculo: {e}")

    def calculate_geomagnetic_parameters(self, lat, lon, alt, date):
        try:
            # Convertir fecha a decimal
            year = date.year + (date.timetuple().tm_yday - 1) / 365.25

            # Obtener los valores del campo geomagnético usando pyIGRF
            igrf_result = pyIGRF.igrf_value(lat, lon, alt, year)

            # Desempaquetar los primeros tres valores
            if len(igrf_result) >= 3:
                B_r, B_theta, B_phi = igrf_result[:3]
            else:
                raise ValueError(f"Resultado inesperado de pyIGRF.igrf_value: {igrf_result}")

            # Convertir de coordenadas esféricas a componentes geográficos
            B_N = -B_theta  # Componente norte en nT
            B_E = B_phi     # Componente este en nT
            B_D = -B_r      # Componente vertical hacia abajo en nT

            # Calcular la intensidad horizontal
            H = math.sqrt(B_N**2 + B_E**2)  # En nT

            # Calcular la inclinación magnética (I)
            inclination = math.degrees(math.atan2(B_D, H))  # En grados

            # Calcular la latitud geomagnética (aproximada)
            magnetic_lat = lat + inclination

            # Evitar división por cero
            cos_magnetic_lat = math.cos(math.radians(magnetic_lat))
            if cos_magnetic_lat == 0:
                raise ValueError("La latitud geomagnética resulta en una división por cero.")

            # Calcular el parámetro L de McIlwain (aproximado)
            L = 1 / (cos_magnetic_lat ** 2)

            # Calcular la rigidez de corte Rc (en GV)
            Rc = 14.9 / (L ** 2)

            # Crear un diccionario con los resultados
            results = {
                'latitude': lat,
                'longitude': lon,
                'Rc': Rc,
                'B_N': B_N,
                'B_E': B_E,
                'B_D': B_D
            }

            return results

        except Exception as e:
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, "Error", f"Error en el cálculo geomagnético: {e}")
            return None

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
            "Lugar": self.location_input.text().strip() if self.address_radio.isChecked() else "",
            "Latitud": self.latitude.text().strip(),
            "Longitud": self.longitude.text().strip(),
            "Altitud": self.altitude if hasattr(self, 'altitude') else '',
            "Corte de Rigidez Geomagnética": self.geomagnetic_cutoff.text().strip(),
            "Fecha de Inicio": self.start_date.text().strip(),
            "Fecha de Termino": self.end_date.text().strip(),
            "Nombre Corto": self.short_name.text().strip(),
            "Número de Detectores": num_detectors,
            "DLT Path": self.dlt_path.text().strip(),
            "ROOT Path": self.root_path.text().strip(),
            "B_N": self.B_N if hasattr(self, 'B_N') else '',
            "B_E": self.B_E if hasattr(self, 'B_E') else '',
            "B_D": self.B_D if hasattr(self, 'B_D') else ''
        }

        # Validaciones adicionales
        if not all(campaign_info.values()):
            QMessageBox.critical(self, "Error", "Todos los campos deben estar completos.")
            return

        # Convertir latitud, longitud, Rc y altitud a float
        try:
            campaign_info["Latitud"] = float(campaign_info["Latitud"])
            campaign_info["Longitud"] = float(campaign_info["Longitud"])
            campaign_info["Altitud"] = float(campaign_info["Altitud"])
            campaign_info["Corte de Rigidez Geomagnética"] = float(campaign_info["Corte de Rigidez Geomagnética"])
            campaign_info["B_N"] = float(campaign_info["B_N"])
            campaign_info["B_E"] = float(campaign_info["B_E"])
            campaign_info["B_D"] = float(campaign_info["B_D"])
        except ValueError:
            QMessageBox.critical(self, "Error", "Latitud, longitud, altitud, rigidez de corte y campos magnéticos deben ser números.")
            return

        # Generar enlace a Google Maps
        latitud = campaign_info["Latitud"]
        longitud = campaign_info["Longitud"]
        if latitud and longitud:
            google_maps_link = f"https://www.google.com/maps/search/?api=1&query={latitud},{longitud}"
            campaign_info["Google Maps Link"] = google_maps_link
        else:
            campaign_info["Google Maps Link"] = ''

        info_file = "./data/info_campaigns.csv"
        os.makedirs("./data", exist_ok=True)
        if not os.path.exists(info_file):
            df_info = pd.DataFrame(columns=[
                "Numero", "Lugar", "Latitud", "Longitud", "Altitud", "Corte de Rigidez Geomagnética",
                "Fecha de Inicio", "Fecha de Termino", "Nombre Corto",
                "Número de Detectores", "DLT Path", "ROOT Path",
                "B_N", "B_E", "B_D", "Google Maps Link"
            ])
        else:
            df_info = pd.read_csv(info_file)
            # Añadir la columna "Google Maps Link" si no existe
            if "Google Maps Link" not in df_info.columns:
                df_info["Google Maps Link"] = ''

        # Verificar si el nombre corto ya existe
        if campaign_info['Nombre Corto'] in df_info['Nombre Corto'].values:
            QMessageBox.critical(self, "Error", "El nombre corto ya existe. Por favor, elija otro.")
            return

        # Guardar la información de la campaña
        df_info = pd.concat([df_info, pd.DataFrame([campaign_info])], ignore_index=True)
        df_info.to_csv(info_file, index=False)

        # Ya no es necesario guardar la imagen del mapa
        # self.save_map_image(campaign_info["Latitud"], campaign_info["Longitud"], campaign_info["Nombre Corto"])

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

if __name__ == "__main__":
    import sys
    from PySide6.QtWidgets import QApplication
    app = QApplication(sys.argv)
    window = CrearNuevaCampagna()
    window.show()
    sys.exit(app.exec())
