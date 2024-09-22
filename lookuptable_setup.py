from PySide6.QtWidgets import (
    QWidget, QLabel, QPushButton, QComboBox, QVBoxLayout, QHBoxLayout,
    QTableWidget, QTableWidgetItem, QApplication, QMessageBox, QHeaderView
)
from PySide6.QtCore import Qt
from functools import partial
import pandas as pd
from datetime import datetime
import os
import utils

class LookUpTableSetup(QWidget):
    def __init__(self, back_callback=None):
        super().__init__()
        self.back_callback = back_callback
        self.material_data = self.load_materials_data()
        self.accepted_values = {}
        self.entries = []
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("LookUpTable de la Configuración de Detectores")
        self.resize(1200, 800)

        # Layout principal
        self.main_layout = QVBoxLayout(self)
        self.setLayout(self.main_layout)

        # Título
        title = QLabel("LookUpTable de la Configuración de Detectores")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 24px; font-weight: bold;")
        self.main_layout.addWidget(title)

        # Selección de campaña
        campaign_layout = QHBoxLayout()
        campaign_label = QLabel("Seleccionar Campaña:")
        campaign_label.setStyleSheet("font-size: 16px;")
        self.selected_campaign = QComboBox()
        self.campaigns = utils.get_existing_campaigns()
        if self.campaigns:
            self.selected_campaign.addItems(self.campaigns)
        else:
            self.selected_campaign.addItem("No hay campañas disponibles")
        self.selected_campaign.currentTextChanged.connect(self.load_campaign_data)
        campaign_layout.addWidget(campaign_label)
        campaign_layout.addWidget(self.selected_campaign)
        self.main_layout.addLayout(campaign_layout)

        # Tabla
        self.table = QTableWidget()
        self.main_layout.addWidget(self.table)

        # Botones
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch(1)
        save_button = QPushButton("Guardar LookUpTable")
        save_button.clicked.connect(self.save_lookuptable)
        buttons_layout.addWidget(save_button)

        generate_button = QPushButton("Generar Distribución de Detectores")
        generate_button.clicked.connect(self.generate_detector_distribution)
        buttons_layout.addWidget(generate_button)

        back_button = QPushButton("Regresar")
        back_button.clicked.connect(self.back)
        buttons_layout.addWidget(back_button)
        buttons_layout.addStretch(1)

        self.main_layout.addLayout(buttons_layout)

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
            QComboBox {
                font-size: 16px;
            }
            QTableWidget {
                font-size: 14px;
            }
        """)

        # Cargar datos iniciales
        self.load_campaign_data()

    def load_materials_data(self):
        materials_file = "./data/materiales.csv"
        if os.path.exists(materials_file):
            df = pd.read_csv(materials_file)
            return df
        else:
            return pd.DataFrame(columns=[
                "Contador Proporcional (Numero/tipo/diametro/largo/marca)",
                "Preamplificador (Numero/modelo)",
                "Alto Voltaje (Modulo/Canal)",
                "Digitalizador (Modelo/Canal)",
                "Moderador (Geometria/Material/diametro-lado)",
                "Set Cables (numero o detalle)"
            ])

    def load_campaign_data(self):
        campaign_name = self.selected_campaign.currentText()
        self.num_detectors = utils.get_num_detectors(campaign_name)
        self.create_table()

    def create_table(self):
        headers = [
            "Contador Proporcional (Numero/tipo/diametro/largo/marca)",
            "Preamplificador (Numero/modelo)",
            "Alto Voltaje (Modulo/Canal)",
            "Digitalizador (Modelo/Canal)",
            "Moderador (Geometria/Material/diametro-lado)",
            "Set Cables (numero o detalle)",
            "Posición"
        ]
        self.accepted_values = {header: [] for header in headers}
        self.entries = []

        self.table.clear()
        self.table.setRowCount(self.num_detectors)
        self.table.setColumnCount(len(headers) + 2)  # +2 para "Detector" y "Aceptar"
        self.table.setHorizontalHeaderLabels(["Detector"] + headers + ["Aceptar"])
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        for row in range(self.num_detectors):
            # Detector label
            item = QTableWidgetItem(f"Detector {row + 1}")
            item.setFlags(Qt.ItemIsEnabled)
            self.table.setItem(row, 0, item)

            entry_row = []
            for col, header in enumerate(headers, start=1):
                combo = QComboBox()
                options = self.get_available_options(header)
                combo.addItems(options)
                self.table.setCellWidget(row, col, combo)
                entry_row.append((header, combo))
            self.entries.append(entry_row)

            # Botón "Aceptar"
            accept_button = QPushButton("Aceptar")
            accept_button.clicked.connect(partial(self.accept_row, row))
            self.table.setCellWidget(row, len(headers) + 1, accept_button)

    def get_available_options(self, header):
        if header not in self.material_data.columns:
            return []
        if header != "Posición":
            options = self.material_data[header].dropna().unique().tolist()
        else:
            options = [f"({i},{j})" for i in range(1, 6) for j in range(1, 5)]
        options = [option for option in options if option not in self.accepted_values[header]]
        return options

    def accept_row(self, row):
        headers = [
            "Contador Proporcional (Numero/tipo/diametro/largo/marca)",
            "Preamplificador (Numero/modelo)",
            "Alto Voltaje (Modulo/Canal)",
            "Digitalizador (Modelo/Canal)",
            "Moderador (Geometria/Material/diametro-lado)",
            "Set Cables (numero o detalle)",
            "Posición"
        ]
        for col, (header, combo) in enumerate(self.entries[row]):
            value = combo.currentText()
            if not value:
                QMessageBox.critical(self, "Error", f"Por favor, seleccione un valor para {header} en el Detector {row + 1}")
                return
            self.accepted_values[header].append(value)
            combo.setEnabled(False)

        # Deshabilitar el botón "Aceptar"
        accept_button = self.table.cellWidget(row, len(headers) + 1)
        accept_button.setEnabled(False)

        # Actualizar opciones en otros combos
        for r in range(self.num_detectors):
            if r != row:
                for col, (header, combo) in enumerate(self.entries[r]):
                    if combo.isEnabled():
                        options = self.get_available_options(header)
                        current_value = combo.currentText()
                        combo.clear()
                        combo.addItems(options)
                        if current_value in options:
                            combo.setCurrentText(current_value)
                        else:
                            if options:
                                combo.setCurrentText(options[0])
                            else:
                                combo.setCurrentText("")
                                combo.setEnabled(False)

    def save_lookuptable(self):
        campaign_name = self.selected_campaign.currentText()
        save_dir = f"./lookuptable/{campaign_name}"
        os.makedirs(save_dir, exist_ok=True)
        file_name = f"{save_dir}/LookUpTable_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{campaign_name}.csv"

        data = []
        headers = [
            "Contador Proporcional (Numero/tipo/diametro/largo/marca)",
            "Preamplificador (Numero/modelo)",
            "Alto Voltaje (Modulo/Canal)",
            "Digitalizador (Modelo/Canal)",
            "Moderador (Geometria/Material/diametro-lado)",
            "Set Cables (numero o detalle)",
            "Posición"
        ]
        for row in range(self.num_detectors):
            row_data = {}
            for col, (header, combo) in enumerate(self.entries[row]):
                value = combo.currentText()
                if not value:
                    QMessageBox.critical(self, "Error", f"Faltan valores en el Detector {row + 1}. Por favor, completa todos los campos.")
                    return
                row_data[header] = value
            data.append(row_data)

        df = pd.DataFrame(data)
        df.to_csv(file_name, index=False)
        QMessageBox.information(self, "Éxito", f"LookUpTable guardada en {file_name}")

    def generate_detector_distribution(self):
        campaign_name = self.selected_campaign.currentText()
        save_dir = f"./Graficos/Lookuptable/{campaign_name}"
        os.makedirs(save_dir, exist_ok=True)
        file_name = f"{save_dir}/Distribucion_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{campaign_name}.png"

        # Aquí puedes agregar el código para generar la distribución de detectores y guardarla como imagen

        QMessageBox.information(self, "Éxito", f"Distribución de detectores guardada en {file_name}")

    def back(self):
        if callable(self.back_callback):
            self.back_callback()
        else:
            self.close()

if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    window = LookUpTableSetup()
    window.show()
    sys.exit(app.exec())
