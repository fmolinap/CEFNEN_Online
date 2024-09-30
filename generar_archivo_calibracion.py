# generar_archivo_calibracion.py

import pandas as pd
import os
from PySide6.QtWidgets import (
    QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QFileDialog, QComboBox,
    QMessageBox, QApplication, QSpinBox, QGridLayout
)
from PySide6.QtCore import Qt
from utils import get_existing_campaigns


class GenerarArchivoCalibracionGASIFIC(QWidget):
    def __init__(self, back_callback=None):
        super().__init__()
        self.back_callback = back_callback
        self.global_data = None
        self.hard_data = None
        self.calibration_file = None
        self.digitalizador_name = None
        self.sampling_freq = None
        self.channel_names = []
        self.range_max = 15000  # Valor por defecto
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

        # Campo para Rango máximo
        range_layout = QHBoxLayout()
        range_label = QLabel("Rango máximo histogramas calibrados [keV]:")
        self.range_max_input = QSpinBox()
        self.range_max_input.setRange(1, 100000)
        self.range_max_input.setValue(self.range_max)
        range_layout.addWidget(range_label)
        range_layout.addWidget(self.range_max_input)
        self.main_layout.addLayout(range_layout)

        # Layout para los botones en una cuadrícula
        buttons_layout = QGridLayout()
        self.main_layout.addLayout(buttons_layout)

        # Botón para cargar el archivo base de calibración
        load_base_button = QPushButton("Cargar Archivo Base Excel")
        load_base_button.clicked.connect(self.load_base_file)
        load_base_button.setStyleSheet("background-color: #FFD700; color: black;")  # Amarillo
        buttons_layout.addWidget(load_base_button, 0, 0)

        # Etiqueta para mostrar el archivo base cargado
        self.base_file_label = QLabel("Archivo base no cargado")
        buttons_layout.addWidget(self.base_file_label, 0, 1)

        # Botón para cargar el archivo de calibración
        load_calibration_button = QPushButton("Cargar Archivo de Calibración")
        load_calibration_button.clicked.connect(self.load_calibration_file)
        load_calibration_button.setStyleSheet("background-color: #800080; color: white;")  # Morado
        buttons_layout.addWidget(load_calibration_button, 1, 0)

        # Etiqueta para mostrar el archivo de calibración cargado
        self.calibration_file_label = QLabel("Archivo de calibración no cargado")
        buttons_layout.addWidget(self.calibration_file_label, 1, 1)

        # Botón para generar el archivo de calibración
        generate_button = QPushButton("Generar archivo .xlsx para calibración Gasific")
        generate_button.clicked.connect(self.generate_calibration_file)
        generate_button.setStyleSheet("background-color: #4CAF50; color: white;")  # Verde
        buttons_layout.addWidget(generate_button, 2, 0, 1, 2)

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
                min-width: 200px;
                min-height: 40px;
                font-size: 14px;
            }
            QLabel {
                font-size: 14px;
            }
        """)

    def load_base_file(self):
        """Carga el archivo base que contiene las hojas Global y Hard_{Name}."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Seleccionar archivo base de calibración", "", "Excel Files (*.xlsx *.xls)"
        )
        if not file_path:
            return

        try:
            # Leer el archivo Excel con las hojas Global y Hard_{Name}
            # Especificamos header=1 para que pandas reconozca los encabezados en la fila 2
            self.global_data = pd.read_excel(file_path, sheet_name='Global', header=1)

            # Obtener el nombre del digitalizador de la celda B3 (columna 'Name')
            self.digitalizador_name = self.global_data.at[0, 'Name']
            if not self.digitalizador_name:
                raise ValueError("No se pudo encontrar el nombre del digitalizador en la celda B3 de la hoja 'Global'.")

            # Obtener la frecuencia de muestreo de la celda H3 (columna 'Clock Freq')
            self.sampling_freq = self.global_data.at[0, 'Clock Freq']
            if not self.sampling_freq:
                raise ValueError("No se pudo encontrar la frecuencia de muestreo en la celda H3 de la hoja 'Global'.")

            # Leer la hoja Hard_{Name} con el encabezado en la fila 3 (header=2)
            hard_sheet_name = f"Hard_{self.digitalizador_name}"
            self.hard_data = pd.read_excel(file_path, sheet_name=hard_sheet_name, header=2)

            # Verificar si la columna 'Name' existe
            if 'Name' not in self.hard_data.columns:
                raise ValueError(f"No se encontró la columna 'Name' en la hoja '{hard_sheet_name}'.")

            # Obtener los nombres de los canales desde la columna 'Name'
            self.channel_names = self.hard_data['Name'].dropna().tolist()

            # Mostrar el nombre del archivo cargado
            self.base_file_label.setText(f"Archivo base cargado: {os.path.basename(file_path)}")
            QMessageBox.information(self, "Éxito", f"Archivo base {file_path} cargado exitosamente.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo cargar el archivo base de calibración: {e}")
            return

    def load_calibration_file(self):
        """Carga el archivo de calibración con los factores y offsets para cada canal."""
        short_name = self.selected_campaign.currentText().strip()
        if not short_name:
            QMessageBox.critical(self, "Error", "Debe seleccionar una campaña válida.")
            return

        # Buscar el archivo CSV en la carpeta ./calibration/{short_name}/*.csv
        calibration_dir = f"./calibration/{short_name}"
        if not os.path.exists(calibration_dir):
            QMessageBox.critical(self, "Error", f"No se encontró la carpeta de calibración: {calibration_dir}")
            return

        file_path, _ = QFileDialog.getOpenFileName(
            self, "Seleccionar archivo de calibración CSV", calibration_dir, "CSV Files (*.csv)"
        )
        if not file_path:
            return

        try:
            # Leer el archivo CSV de calibración
            self.calibration_file = pd.read_csv(file_path)
            # Mostrar el nombre del archivo cargado
            self.calibration_file_label.setText(f"Archivo de calibración cargado: {os.path.basename(file_path)}")
            QMessageBox.information(self, "Éxito", f"Archivo de calibración {file_path} cargado exitosamente.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo cargar el archivo de calibración: {e}")
            return

    def generate_calibration_file(self):
        """Genera el archivo de calibración completo."""
        if self.global_data is None or self.hard_data is None or self.calibration_file is None:
            QMessageBox.critical(
                self, "Error", "Debe cargar el archivo base y el archivo de calibración antes de generar."
            )
            return

        short_name = self.selected_campaign.currentText().strip()
        if not short_name:
            QMessageBox.critical(self, "Error", "Debe seleccionar una campaña válida.")
            return

        try:
            # Crear un archivo Excel nuevo basado en las hojas cargadas
            output_file_path = f"./calibration/{short_name}/{short_name}_archivo_calibracion.xlsx"
            os.makedirs(os.path.dirname(output_file_path), exist_ok=True)
            writer = pd.ExcelWriter(output_file_path, engine='xlsxwriter')

            # Copiar la hoja Global
            self.global_data.to_excel(writer, sheet_name='Global', index=False)

            # Copiar la hoja Hard_{Name}
            hard_sheet_name = f"Hard_{self.digitalizador_name}"
            self.hard_data.to_excel(writer, sheet_name=hard_sheet_name, index=False)

            # Crear la hoja de Calibración Cal_{Name}
            cal_sheet_name = f"Cal_{self.digitalizador_name}"
            self.create_calibration_sheet(writer, cal_sheet_name)

            # Crear la hoja de Condition
            self.create_condition_sheet(writer)

            # Crear la hoja de Groups
            self.create_groups_sheet(writer)

            # Cerrar y guardar el archivo Excel
            writer.close()

            self.result_text.setText(f"Archivo de calibración generado en: {output_file_path}")
            QMessageBox.information(self, "Éxito", f"Archivo de calibración guardado como: {output_file_path}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo generar el archivo de calibración: {e}")

    def create_calibration_sheet(self, writer, cal_sheet_name):
        """Crea la hoja de calibración Cal_{Name B3} en el archivo Excel."""
        # Crear el encabezado según especificaciones
        headers = [
            "Name", "Type", "Hard Source", "Par Source", "Range Min", "Range Max", "Bins",
            "Cal Factor", "Cal Offset", "Units", "Make Hist"
        ]

        # Inicializar lista para almacenar todas las filas
        data_rows = []

        # Incluir en la celda A1 la palabra "Calibration"
        data_rows.append(["Calibration"] + [""] * (len(headers) - 1))

        # Añadir los títulos en la fila 2
        data_rows.append(headers)

        # Rellenar los datos a partir de la fila 3
        for channel_name in self.channel_names:
            cal_factor = self.get_calibration_value(channel_name, "Slope")
            cal_offset = self.get_calibration_value(channel_name, "Offset")

            calibration_entry = [
                f"{channel_name}_Cal",
                "CalSpec",
                channel_name,
                "EFIR",
                0,
                self.range_max_input.value(),
                self.range_max_input.value(),
                cal_factor,
                cal_offset,
                "Energy [keV]",
                1
            ]
            data_rows.append(calibration_entry)

        # Convertir las filas en un DataFrame
        calibration_df = pd.DataFrame(data_rows)

        # Escribir el DataFrame en la hoja correspondiente sin índices y sin encabezados
        calibration_df.to_excel(writer, sheet_name=cal_sheet_name, index=False, header=False)

        # Aplicar formato de letra roja a la celda A1
        workbook = writer.book
        worksheet = writer.sheets[cal_sheet_name]
        red_format = workbook.add_format({'font_color': 'red'})
        worksheet.write('A1', 'Calibration', red_format)

    def create_condition_sheet(self, writer):
        """Crea la hoja Condition en el archivo Excel."""
        condition_sheet_name = "Condition"

        # Inicializar listas para almacenar las filas
        data_rows = []

        # Definir los tiempos y denominadores
        conditions = [
            ("15 min", "_CR_15min", 60*15, 10000),
            ("30 min", "_CR_30min", 60*30, 5000),
            ("1 hour", "_CR_1h", 60*60, 2500)
        ]

        # Calcular Calibration Factor según frecuencia de muestreo
        sampling_freq = self.sampling_freq
        factor_mapping = {
            250: 4e-9,
            125: 8e-9,
            62.5: 16e-8,
            62: 16e-8,
            25: 4e-8
        }
        base_factor = factor_mapping.get(sampling_freq, 4e-9)

        for unit, suffix, den, time_max in conditions:
            # Añadir línea con "Time Plots" en columna C
            data_rows.append(["", "", "Time Plots"] + [""] * 11)
            # Añadir línea de títulos
            headers = ["Name", "Type", "Source", "Energy Min", "Energy Max", "Time source",
                       "Time Range Min", "Time Range Max", "Hist Bins", "Calibration Factor",
                       "Units", "Hist Enable", "Rate calibration factor", "Rate units"]
            data_rows.append(headers)

            for channel_name in self.channel_names:
                calibration_factor = base_factor / den
                condition_entry = [
                    f"{channel_name}{suffix}",
                    "TimeEL",
                    f"{channel_name}_Cal",
                    140,
                    820,
                    "Timestamp",
                    0,
                    time_max,
                    time_max,
                    calibration_factor,
                    unit,
                    1,
                    1,
                    f"Counts per {unit}"
                ]
                data_rows.append(condition_entry)

        # Convertir las filas en un DataFrame
        condition_df = pd.DataFrame(data_rows)

        # Escribir en el Excel sin índices y sin encabezados
        condition_df.to_excel(writer, sheet_name=condition_sheet_name, index=False, header=False)

    def create_groups_sheet(self, writer):
        """Crea la hoja Groups en el archivo Excel."""
        group_df = pd.DataFrame({"A": ["", "", "Groups"]})
        group_df.to_excel(writer, sheet_name="Groups", index=False, header=False, startrow=0)

    def get_calibration_value(self, channel_name, value_type):
        """Obtiene el valor de calibración para un canal específico desde el archivo CSV cargado."""
        if self.calibration_file is None:
            return None
        hist_name = f"{channel_name}_EFIR"
        row = self.calibration_file[self.calibration_file['Histograma'] == hist_name]
        return row[value_type].values[0] if not row.empty else None

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
