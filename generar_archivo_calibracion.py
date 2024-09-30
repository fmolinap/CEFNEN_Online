# generar_archivo_calibracion.py

import pandas as pd
import os
import math
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
            self.global_data = pd.read_excel(file_path, sheet_name='Global', header=1, index_col=None)

            # Eliminar columnas 'Unnamed' si existen
            self.global_data = self.global_data.loc[:, ~self.global_data.columns.str.contains('^Unnamed')]

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
            self.hard_data = pd.read_excel(file_path, sheet_name=hard_sheet_name, header=2, index_col=None)

            # Eliminar columnas 'Unnamed' si existen
            self.hard_data = self.hard_data.loc[:, ~self.hard_data.columns.str.contains('^Unnamed')]

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

            # Crear un diccionario para mapear nombres de canales a Slope y Offset
            self.calibration_mapping = {}
            for index, row in self.calibration_file.iterrows():
                hist_name = row['Histograma']
                # Remover '_EFIR' si está presente
                if hist_name.endswith('_EFIR'):
                    channel_name = hist_name[:-5]
                else:
                    channel_name = hist_name
                self.calibration_mapping[channel_name] = {
                    'Slope': row['Slope'],
                    'Offset': row['Offset']
                }

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
            # Configurar XlsxWriter para manejar NaN/Inf
            writer = pd.ExcelWriter(output_file_path, engine='xlsxwriter',
                                    engine_kwargs={'options': {'nan_inf_to_errors': True}})

            # Copiar la hoja Global con formato
            self.write_global_sheet(writer)

            # Copiar la hoja Hard_{Name} con formato
            hard_sheet_name = f"Hard_{self.digitalizador_name}"
            self.write_hard_sheet(writer, hard_sheet_name)

            # Crear la hoja de Calibración Cal_{Name} con formato
            cal_sheet_name = f"Cal_{self.digitalizador_name}"
            self.create_calibration_sheet(writer, cal_sheet_name)

            # Crear la hoja de Condition con formato
            self.create_condition_sheet(writer)

            # Crear la hoja de Groups con formato
            self.create_groups_sheet(writer)

            # Cerrar y guardar el archivo Excel
            writer.close()

            self.result_text.setText(f"Archivo de calibración generado en: {output_file_path}")
            QMessageBox.information(self, "Éxito", f"Archivo de calibración guardado como: {output_file_path}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo generar el archivo de calibración: {e}")

    def write_global_sheet(self, writer):
        """Escribe la hoja Global con el formato especificado."""
        workbook = writer.book
        worksheet = workbook.add_worksheet('Global')

        # Formatos
        red_bold_format = workbook.add_format({'font_color': 'red', 'bold': True})
        yellow_bg_format = workbook.add_format({'bg_color': '#FFFF00', 'bold': True, 'border': 1})

        # Escribir "Modules" en A1 en rojo
        worksheet.write('A1', 'Modules', red_bold_format)

        # Escribir encabezados desde B2 con fondo amarillo
        headers = self.global_data.columns.tolist()
        worksheet.write_row('B2', headers, yellow_bg_format)

        # Escribir valores correspondientes en B3
        worksheet.write_row('B3', self.global_data.iloc[0].values)

    def write_hard_sheet(self, writer, sheet_name):
        """Escribe la hoja Hard_{Name} con el formato especificado."""
        workbook = writer.book
        worksheet = workbook.add_worksheet(sheet_name)

        # Formatos
        yellow_bg_format = workbook.add_format({'bg_color': '#FFFF00', 'bold': True})
        light_blue_bg_format = workbook.add_format({'bg_color': '#ADD8E6', 'bold': True, 'align': 'center'})
        green_bg_format = workbook.add_format({'bg_color': '#90EE90', 'bold': True, 'align': 'center'})
        black_bold_format = workbook.add_format({'bold': True})

        # Escribir "Channels" en A1 con fondo amarillo
        worksheet.write('A1', 'Channels', yellow_bg_format)

        # Escribir encabezados desde B3 en adelante
        headers = self.hard_data.columns.tolist()
        worksheet.write_row('B3', headers)

        # Escribir datos debajo de los encabezados
        for idx, row in enumerate(self.hard_data.values):
            worksheet.write_row(f'B{idx + 4}', row)

        # Aplicar formatos y fusiones
        # Fusionar celdas y aplicar formato según especificaciones
        worksheet.merge_range('E2:I2', 'Trigger Parameters', light_blue_bg_format)
        worksheet.merge_range('J2:M2', 'Energy Filter Parameters', green_bg_format)
        worksheet.merge_range('N2:O2', '', light_blue_bg_format)
        worksheet.merge_range('P2:W2', 'Samples Parameters', green_bg_format)
        worksheet.merge_range('X2:Z2', '', light_blue_bg_format)
        worksheet.merge_range('AA2:AF2', '', green_bg_format)
        worksheet.merge_range('AG2:AJ2', '', light_blue_bg_format)
        worksheet.merge_range('AK2:BH2', '', green_bg_format)

    def create_calibration_sheet(self, writer, cal_sheet_name):
        """Crea la hoja de calibración Cal_{Name B3} en el archivo Excel."""
        workbook = writer.book
        worksheet = workbook.add_worksheet(cal_sheet_name)

        # Formatos
        red_bold_format = workbook.add_format({'font_color': 'red', 'bold': True})
        yellow_bg_format = workbook.add_format({'bg_color': '#FFFF00', 'bold': True})

        # Incluir en la celda A1 la palabra "Calibration" en rojo
        worksheet.write('A1', 'Calibration', red_bold_format)

        # Crear el encabezado según especificaciones
        headers = [
            "Name", "Type", "Hard Source", "Par Source", "Range Min", "Range Max", "Bins",
            "Cal Factor", "Cal Offset", "Units", "Make Hist"
        ]

        # Escribir encabezados desde B2 a L2 con fondo amarillo
        worksheet.write_row('B2', headers, yellow_bg_format)

        # Rellenar los datos a partir de la fila 3
        for idx, channel_name in enumerate(self.channel_names):
            # Obtener los valores de calibración desde el diccionario
            calibration_data = self.calibration_mapping.get(channel_name)
            if calibration_data is None:
                QMessageBox.critical(self, "Error",
                                     f"No se encontraron valores de calibración para el canal {channel_name}.")
                return

            cal_factor = calibration_data['Slope']
            cal_offset = calibration_data['Offset']

            # Validar que cal_factor y cal_offset no sean None o NaN
            if cal_factor is None or cal_offset is None or math.isnan(cal_factor) or math.isnan(cal_offset):
                QMessageBox.critical(self, "Error",
                                     f"Los valores de calibración para el canal {channel_name} no son válidos.")
                return

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
            # Escribir los datos desde la fila 3, columna B
            worksheet.write_row(f'B{idx + 3}', calibration_entry)

    def create_condition_sheet(self, writer):
        """Crea la hoja Condition en el archivo Excel."""
        workbook = writer.book
        worksheet = workbook.add_worksheet('Condition')

        # Formatos
        red_bold_format = workbook.add_format({'font_color': 'red', 'bold': True})
        yellow_bg_format = workbook.add_format({'bg_color': '#FFFF00', 'bold': True})

        row_num = 0

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

        # Encabezados
        headers = ["Name", "Type", "Source", "Energy Min", "Energy Max", "Time source",
                   "Time Range Min", "Time Range Max", "Hist Bins", "Calibration Factor",
                   "Units", "Hist Enable", "Rate calibration factor", "Rate units"]

        for channel_name in self.channel_names:
            for unit, suffix, den, time_max in conditions:
                # Añadir línea con "Time Plots" en columna C
                worksheet.write(row_num, 2, 'Time Plots', red_bold_format)
                row_num += 1

                # Añadir línea de títulos desde B a O con fondo amarillo
                worksheet.write_row(row_num, 1, headers, yellow_bg_format)
                row_num += 1

                calibration_factor = base_factor / den

                # Validar que calibration_factor no sea NaN o Inf
                if math.isnan(calibration_factor) or math.isinf(calibration_factor):
                    QMessageBox.critical(self, "Error",
                                         f"El Calibration Factor para el canal {channel_name} es inválido.")
                    return

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
                # Escribir los datos desde columna B
                worksheet.write_row(row_num, 1, condition_entry)
                row_num += 1

    def create_groups_sheet(self, writer):
        """Crea la hoja Groups en el archivo Excel."""
        workbook = writer.book
        worksheet = workbook.add_worksheet('Groups')

        # Formatos
        red_bold_format = workbook.add_format({'font_color': 'red', 'bold': True})

        # Escribir "Groups" en la celda C1 en rojo
        worksheet.write('C1', 'Groups', red_bold_format)

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
