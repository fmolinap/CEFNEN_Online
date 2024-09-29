# generar_archivo_calibracion.py

import pandas as pd
import os
from PySide6.QtWidgets import (
    QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QFileDialog, QComboBox,
    QMessageBox, QApplication
)
from PySide6.QtCore import Qt
from utils import get_existing_campaigns, get_campaign_info


class GenerarArchivoCalibracionGASIFIC(QWidget):
    def __init__(self, back_callback=None):
        super().__init__()
        self.back_callback = back_callback
        self.global_data = None
        self.hard_data = None
        self.calibration_file = None
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Generar Archivo de Calibración GASIFIC")
        self.resize(800, 600)

        # Layout principal
        self.main_layout = QVBoxLayout(self)
        self.setLayout(self.main_layout)

        # Título
        title = QLabel("Generar Archivo de Calibración GASIFIC")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 24px; font-weight: bold;")
        self.main_layout.addWidget(title)

        # Selección de campaña
        campaign_layout = QHBoxLayout()
        campaign_label = QLabel("Seleccionar Campaña:")
        self.selected_campaign = QComboBox()
        self.selected_campaign.addItems(get_existing_campaigns())
        campaign_layout.addWidget(campaign_label)
        campaign_layout.addWidget(self.selected_campaign)
        self.main_layout.addLayout(campaign_layout)

        # Botón para cargar el archivo base de calibración
        load_base_button = QPushButton("Cargar Archivo Base Excel")
        load_base_button.clicked.connect(self.load_base_file)
        load_base_button.setStyleSheet("background-color: #4CAF50; color: white;")
        self.main_layout.addWidget(load_base_button)

        # Botón para cargar el archivo de calibración
        load_calibration_button = QPushButton("Cargar Archivo de Calibración")
        load_calibration_button.clicked.connect(self.load_calibration_file)
        load_calibration_button.setStyleSheet("background-color: #4CAF50; color: white;")
        self.main_layout.addWidget(load_calibration_button)

        # Botón para generar el archivo de calibración
        generate_button = QPushButton("Generar Archivo de Calibración")
        generate_button.clicked.connect(self.generate_calibration_file)
        generate_button.setStyleSheet("background-color: #4CAF50; color: white;")
        self.main_layout.addWidget(generate_button)

        # Botón de regresar
        back_button = QPushButton("Regresar")
        back_button.clicked.connect(self.back)
        back_button.setStyleSheet("background-color: #f44336; color: white;")
        self.main_layout.addWidget(back_button)

        # Resultados
        self.result_text = QLabel()
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
        """)

    def load_base_file(self):
        """Carga el archivo base que contiene las hojas Global y Hard_{Name}."""
        file_path, _ = QFileDialog.getOpenFileName(self, "Seleccionar archivo base de calibración", "", "Excel Files (*.xlsx *.xls)")
        if not file_path:
            return

        try:
            # Leer el archivo Excel con las hojas Global y Hard_{Name}
            self.global_data = pd.read_excel(file_path, sheet_name='Global')
            
            # Obtener el nombre del digitalizador de la posición B3 (fila 1, columna 1 en iloc)
            digitalizador_name = self.global_data.iloc[1, 1]
            
            if not digitalizador_name:
                raise ValueError("No se pudo encontrar el nombre del digitalizador en la celda B3 de la hoja 'Global'.")
            
            # Obtener la hoja Hard correspondiente
            hard_sheet_name = f"Hard_{digitalizador_name}"
            self.hard_data = pd.read_excel(file_path, sheet_name=hard_sheet_name)

            QMessageBox.information(self, "Éxito", f"Archivo base {file_path} cargado exitosamente.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo cargar el archivo base de calibración: {e}")
            return

    def load_calibration_file(self):
        """Carga el archivo de calibración con los factores y offsets para cada canal."""
        file_path, _ = QFileDialog.getOpenFileName(self, "Seleccionar archivo de calibración CSV", "", "CSV Files (*.csv)")
        if not file_path:
            return

        try:
            # Leer el archivo CSV de calibración
            self.calibration_file = pd.read_csv(file_path)
            QMessageBox.information(self, "Éxito", f"Archivo de calibración {file_path} cargado exitosamente.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo cargar el archivo de calibración: {e}")
            return

    def generate_calibration_file(self):
        """Genera el archivo de calibración completo."""
        if self.global_data is None or self.hard_data is None or self.calibration_file is None:
            QMessageBox.critical(self, "Error", "Debe cargar el archivo base y el archivo de calibración antes de generar.")
            return

        short_name = self.selected_campaign.currentText().strip()
        if not short_name:
            QMessageBox.critical(self, "Error", "Debe seleccionar una campaña válida.")
            return

        try:
            # Crear un archivo Excel nuevo basado en las hojas cargadas
            output_file_path = f"./calibration/{short_name}_archivo_calibracion.xlsx"
            writer = pd.ExcelWriter(output_file_path, engine='xlsxwriter')

            # Copiar la hoja Global
            self.global_data.to_excel(writer, sheet_name='Global', index=False)

            # Copiar la hoja Hard_{Name}
            hard_sheet_name = f"Hard_{self.global_data.iloc[1, 1]}"
            self.hard_data.to_excel(writer, sheet_name=hard_sheet_name, index=False)

            # Crear la hoja de Calibración Cal_{Name}
            cal_sheet_name = f"Cal_{self.global_data.iloc[1, 1]}"
            self.create_calibration_sheet(writer, cal_sheet_name)

            # Crear la hoja de Condition
            self.create_condition_sheet(writer, short_name)

            # Crear la hoja de Groups
            self.create_groups_sheet(writer)

            writer.save()
            self.result_text.setText(f"Archivo de calibración generado en: {output_file_path}")
            QMessageBox.information(self, "Éxito", f"Archivo de calibración guardado como: {output_file_path}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo generar el archivo de calibración: {e}")

    def create_calibration_sheet(self, writer, cal_sheet_name):
        """Crea la hoja de calibración Cal_{Name} en el archivo Excel."""
        # Crear el encabezado
        headers = [
            "Name", "Type", "Hard Source", "Par Source", "Range Min", "Range Max", "Bins", 
            "Cal Factor", "Cal Offset", "Units", "Make Hist"
        ]
        calibration_df = pd.DataFrame(columns=headers)
        calibration_df.loc[0, 'Name'] = "Calibration"  # Agregar título en la primera fila
        for index, row in self.hard_data.iterrows():
            channel_name = row["Name"]
            calibration_entry = {
                "Name": f"{channel_name}_Cal",
                "Type": "CalSpec",
                "Hard Source": channel_name,
                "Par Source": "EFIR",
                "Range Min": 0,
                "Range Max": 15000,
                "Bins": 15000,
                "Cal Factor": self.get_calibration_value(channel_name, "Slope"),
                "Cal Offset": self.get_calibration_value(channel_name, "Offset"),
                "Units": "Energy [keV]",
                "Make Hist": 1
            }
            calibration_df = calibration_df.append(calibration_entry, ignore_index=True)

        calibration_df.to_excel(writer, sheet_name=cal_sheet_name, index=False, startrow=1)

    def create_condition_sheet(self, writer, short_name):
        """Crea la hoja Condition en el archivo Excel."""
        # Obtener la frecuencia de muestreo
        sampling_freq = self.global_data.iloc[1, 7]  # Acceder a la celda H3 con iloc
        den_15min = 60 * 15
        den_30min = 60 * 30
        den_1h = 60 * 60

        # Definir las condiciones para cada rango de tiempo
        conditions = [
            ("_CR_15min", den_15min, "15 min"),
            ("_CR_30min", den_30min, "30 min"),
            ("_CR_1h", den_1h, "1 hour")
        ]

        condition_data = []
        for suffix, den, unit in conditions:
            for _, row in self.hard_data.iterrows():
                channel_name = row["Name"]
                condition_data.append({
                    "Name": f"{channel_name}{suffix}",
                    "Type": "TimeEL",
                    "Source": f"{channel_name}_Cal",
                    "Energy Min": 140,
                    "Energy Max": 820,
                    "Time source": "Timestamp",
                    "Time Range Min": 0,
                    "Time Range Max": 10000 if unit == "15 min" else (5000 if unit == "30 min" else 2500),
                    "Hist Bins": 10000 if unit == "15 min" else (5000 if unit == "30 min" else 2500),
                    "Calibration Factor": self.get_calibration_factor(sampling_freq, den),
                    "Units": unit,
                    "Hist Enable": 1,
                    "Rate calibration factor": 1,
                    "Rate units": f"Counts per {unit}"
                })

        # Convertir la lista de condiciones en un DataFrame
        condition_df = pd.DataFrame(condition_data)
        condition_df.to_excel(writer, sheet_name="Condition", index=False, startrow=2)

    def create_groups_sheet(self, writer):
        """Crea la hoja Groups en el archivo Excel."""
        group_df = pd.DataFrame({"C": ["Groups"]})
        group_df.to_excel(writer, sheet_name="Groups", index=False, startrow=0)

    def get_calibration_value(self, channel_name, value_type):
        """Obtiene el valor de calibración para un canal específico desde el archivo CSV cargado."""
        if self.calibration_file is None:
            return None
        hist_name = f"{channel_name}_EFIR"
        row = self.calibration_file[self.calibration_file['Histograma'] == hist_name]
        return row[value_type].values[0] if not row.empty else None

    def get_calibration_factor(self, sampling_freq, den):
        """Calcula el factor de calibración basado en la frecuencia de muestreo y el denominador de tiempo."""
        factor_mapping = {
            250: 4e-9,
            125: 8e-9,
            62.5: 16e-8,
            25: 4e-8
        }
        return factor_mapping.get(sampling_freq, 4e-9) / den

    def back(self):
        """Regresa a la ventana principal."""
        if callable(self.back_callback):
            self.back_callback()
        else:
            self.close()


if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    window = GenerarArchivoCalibracionGASIFIC()
    window.show()
    sys.exit(app.exec())
