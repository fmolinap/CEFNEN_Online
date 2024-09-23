from PySide6.QtWidgets import (
    QWidget, QLabel, QPushButton, QComboBox, QVBoxLayout, QHBoxLayout,
    QTableWidget, QTableWidgetItem, QApplication, QMessageBox, QHeaderView,
    QDialog, QDialogButtonBox, QFormLayout, QLineEdit, QFileDialog, QScrollArea
)
from PySide6.QtCore import Qt
from functools import partial
import pandas as pd
from datetime import datetime
import os
import utils  # Asegúrate de tener este módulo con las funciones necesarias
from PySide6.QtGui import QPixmap

class AddMaterialDialog(QDialog):
    """
    Diálogo para añadir un nuevo material a un componente específico.
    """
    def __init__(self, headers, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Agregar Nuevo Material")
        self.setModal(True)
        self.selected_header = None
        self.new_material = None
        self.headers = headers
        self.init_ui()

    def init_ui(self):
        layout = QFormLayout(self)

        # Seleccionar Componente
        self.header_combo = QComboBox()
        self.header_combo.addItems(self.headers)
        layout.addRow("Componente:", self.header_combo)

        # Ingresar Nuevo Material
        self.material_input = QLineEdit()
        layout.addRow("Nuevo Material:", self.material_input)

        # Botones
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.validate)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def validate(self):
        header = self.header_combo.currentText()
        material = self.material_input.text().strip()

        if not material:
            QMessageBox.critical(self, "Error", "El campo 'Nuevo Material' no puede estar vacío.")
            return

        self.selected_header = header
        self.new_material = material
        self.accept()

class ImageDisplayDialog(QDialog):
    """
    Diálogo para mostrar la imagen generada de la distribución de detectores.
    """
    def __init__(self, image_path, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Distribución de Detectores")
        self.resize(1200, 800)
        layout = QVBoxLayout(self)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        self.label = QLabel()
        self.label.setAlignment(Qt.AlignCenter)
        pixmap = QPixmap(image_path)
        self.label.setPixmap(pixmap)
        scroll.setWidget(self.label)
        layout.addWidget(scroll)

        # Botón para cerrar
        close_button = QPushButton("Cerrar")
        close_button.clicked.connect(self.close)
        layout.addWidget(close_button)

class LookUpTableSetup(QWidget):
    def __init__(self, back_callback=None):
        super().__init__()
        self.back_callback = back_callback
        self.material_data = self.load_materials_data()
        self.accepted_values = {}
        self.accepted_positions = []  # Separar posiciones aceptadas
        self.entries = []
        self.posiciones_disponibles = [f"({i},{j})" for i in range(1, 6) for j in range(1, 5)]
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("LookUpTable de la Configuración de Detectores")
        self.resize(1600, 1200)  # Aumentar tamaño para acomodar nuevos elementos

        # Layout principal
        self.main_layout = QVBoxLayout(self)
        self.setLayout(self.main_layout)

        # Título
        title = QLabel("LookUpTable de la Configuración de Detectores")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 24px; font-weight: bold;")
        self.main_layout.addWidget(title)

        # Selección de campaña y gestión de materiales
        top_layout = QHBoxLayout()
        self.setup_campaign_selection(top_layout)
        self.setup_manage_materials_button(top_layout)
        self.setup_load_lookuptable_button(top_layout)  # Nuevo botón para cargar LookUpTable
        self.main_layout.addLayout(top_layout)

        # Tabla
        self.table = QTableWidget()
        self.main_layout.addWidget(self.table)

        # Botones de acción
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch(1)
        save_button = QPushButton("Guardar LookUpTable")
        save_button.setStyleSheet("background-color: #4CAF50; color: white;")
        save_button.clicked.connect(self.save_lookuptable)
        buttons_layout.addWidget(save_button)

        generate_button = QPushButton("Generar Distribución de Detectores")
        generate_button.setStyleSheet("background-color: #2196F3; color: white;")
        generate_button.clicked.connect(self.generate_detector_distribution)
        buttons_layout.addWidget(generate_button)

        back_button = QPushButton("Regresar")
        back_button.setStyleSheet("background-color: #f44336; color: white;")
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

    def setup_campaign_selection(self, layout):
        """
        Configura la selección de campaña.
        """
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
        layout.addLayout(campaign_layout)

    def setup_manage_materials_button(self, layout):
        """
        Configura el botón para gestionar materiales.
        """
        manage_button = QPushButton("Agregar Nuevo Material")
        manage_button.setStyleSheet("background-color: #FF9800; color: white;")
        manage_button.clicked.connect(self.open_add_material_dialog)
        layout.addWidget(manage_button)

    def setup_load_lookuptable_button(self, layout):
        """
        Configura el botón para cargar una LookUpTable existente.
        """
        load_button = QPushButton("Cargar LookUpTable")
        load_button.setStyleSheet("background-color: #9C27B0; color: white;")
        load_button.clicked.connect(self.load_existing_lookuptable)
        layout.addWidget(load_button)

    def load_materials_data(self):
        materiales_file = "./data/materiales.csv"  # Usar 'materiales.csv' como se indicó
        if os.path.exists(materiales_file):
            try:
                df = pd.read_csv(materiales_file, dtype=str)
                df = df.where(pd.notnull(df), '')  # Reemplazar NaN con cadenas vacías
                return df
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo cargar 'materiales.csv': {str(e)}")
                # Retornar DataFrame vacío si hay error
                return pd.DataFrame(columns=[
                    "Contador Proporcional (Numero/tipo/diametro/largo/marca)",
                    "Preamplificador (Numero/modelo)",
                    "Alto Voltaje (Modulo/Canal)",
                    "Digitalizador (Modelo/Canal)",
                    "Moderador (Geometria/Material/diametro-lado)",
                    "Set Cables (numero o detalle)"
                ])
        else:
            # Crear DataFrame vacío si el archivo no existe
            return pd.DataFrame(columns=[
                "Contador Proporcional (Numero/tipo/diametro/largo/marca)",
                "Preamplificador (Numero/modelo)",
                "Alto Voltaje (Modulo/Canal)",
                "Digitalizador (Modelo/Canal)",
                "Moderador (Geometria/Material/diametro-lado)",
                "Set Cables (numero o detalle)"
            ])

    def load_campaign_data(self):
        """
        Carga los datos de la campaña seleccionada y crea la tabla.
        """
        campaign_name = self.selected_campaign.currentText()
        self.num_detectors = utils.get_num_detectors(campaign_name)
        print(f"Campaña seleccionada: {campaign_name}")
        print(f"Número de detectores: {self.num_detectors}")
        self.create_table()

    def create_table(self):
        """
        Crea y configura la tabla con los detectores y sus componentes.
        """
        headers = [
            "Contador Proporcional (Numero/tipo/diametro/largo/marca)",
            "Preamplificador (Numero/modelo)",
            "Alto Voltaje (Modulo/Canal)",
            "Digitalizador (Modelo/Canal)",
            "Moderador (Geometria/Material/diametro-lado)",
            "Set Cables (numero o detalle)",
            "Posición"
        ]
        self.accepted_values = {header: [] for header in headers[:-1]}  # Excluir "Posición"
        self.accepted_positions = []  # Separar posiciones aceptadas

        self.entries = []

        self.table.clear()
        # +3 para "Detector", "Aceptar" y "Editar"
        self.table.setRowCount(self.num_detectors)
        self.table.setColumnCount(len(headers) + 3)
        self.table.setHorizontalHeaderLabels(["Detector"] + headers + ["Aceptar", "Editar"])
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
                if header != "Posición":
                    options = self.get_available_options(header)
                else:
                    options = self.get_available_posiciones()
                combo.addItems(options)
                combo.setEditable(False)
                self.table.setCellWidget(row, col, combo)
                entry_row.append((header, combo))
            self.entries.append(entry_row)

            # Botón "Aceptar"
            accept_button = QPushButton("Aceptar")
            accept_button.setStyleSheet("background-color: #2196F3; color: white;")
            accept_button.clicked.connect(partial(self.accept_row, row))
            self.table.setCellWidget(row, len(headers) + 1, accept_button)

            # Botón "Editar"
            edit_button = QPushButton("Editar")
            edit_button.setStyleSheet("background-color: #FFC107; color: white;")
            edit_button.clicked.connect(partial(self.edit_row, row))
            edit_button.setEnabled(False)  # Inicialmente deshabilitado
            self.table.setCellWidget(row, len(headers) + 2, edit_button)

    def get_available_options(self, header, current_value=None):
        """
        Obtiene las opciones disponibles para un componente específico, excluyendo las ya aceptadas,
        pero incluyendo el current_value si está presente.
        """
        if header not in self.material_data.columns:
            return []
        # Obtener las opciones únicas para el componente
        options = self.material_data[header].dropna().unique().tolist()
        # Excluir aceptadas, pero incluir current_value
        if current_value in options:
            options.remove(current_value)
        options = [option for option in options if option not in self.accepted_values.get(header, [])]
        if current_value:
            options.append(current_value)
        return options

    def get_available_posiciones(self):
        """
        Obtiene las opciones disponibles para "Posición", excluyendo las ya aceptadas.
        """
        options = [pos for pos in self.posiciones_disponibles if pos not in self.accepted_positions]
        return options

    def accept_row(self, row):
        """
        Acepta y registra las selecciones realizadas para un detector específico.
        Además, verifica que no existan valores duplicados entre las filas aceptadas.
        """
        headers = [
            "Contador Proporcional (Numero/tipo/diametro/largo/marca)",
            "Preamplificador (Numero/modelo)",
            "Alto Voltaje (Modulo/Canal)",
            "Digitalizador (Modelo/Canal)",
            "Moderador (Geometria/Material/diametro-lado)",
            "Set Cables (numero o detalle)",
            "Posición"
        ]
        new_values = {}
        for col, (header, combo) in enumerate(self.entries[row]):
            value = combo.currentText()
            if not value:
                QMessageBox.critical(self, "Error", f"Por favor, seleccione un valor para {header} en el Detector {row + 1}")
                return
            new_values[header] = value

        # Verificar duplicados para cada componente
        for header in headers[:-1]:  # Excluir "Posición"
            value = new_values[header]
            if value in self.accepted_values.get(header, []):
                QMessageBox.critical(self, "Error", f"El valor '{value}' para '{header}' ya está asignado en otro detector.")
                return

        # Verificar duplicado para "Posición" si no es "DAQ"
        pos_value = new_values["Posición"]
        if pos_value != "DAQ" and pos_value in self.accepted_positions:
            QMessageBox.critical(self, "Error", f"La posición '{pos_value}' ya está asignada a otro detector.")
            return

        # Verificar que "DAQ" no esté duplicado
        if pos_value == "DAQ" and "DAQ" in self.accepted_positions:
            QMessageBox.critical(self, "Error", f"La posición 'DAQ' ya está asignada a otro detector.")
            return

        # Si todas las verificaciones pasan, actualizar accepted_values y accepted_positions
        for header in headers[:-1]:
            self.accepted_values[header].append(new_values[header])

        if pos_value != "DAQ":
            self.accepted_positions.append(pos_value)

        # Deshabilitar los ComboBoxes después de aceptar
        for col, (header, combo) in enumerate(self.entries[row]):
            combo.setEnabled(False)

        # Deshabilitar el botón "Aceptar" y habilitar "Editar"
        accept_button = self.table.cellWidget(row, len(headers) + 1)
        accept_button.setEnabled(False)

        edit_button = self.table.cellWidget(row, len(headers) + 2)
        edit_button.setEnabled(True)

    def edit_row(self, row):
        """
        Permite editar las selecciones de una fila específica.
        """
        headers = [
            "Contador Proporcional (Numero/tipo/diametro/largo/marca)",
            "Preamplificador (Numero/modelo)",
            "Alto Voltaje (Modulo/Canal)",
            "Digitalizador (Modelo/Canal)",
            "Moderador (Geometria/Material/diametro-lado)",
            "Set Cables (numero o detalle)",
            "Posición"
        ]

        # Recuperar valores actuales
        current_values = {}
        for col, (header, combo) in enumerate(self.entries[row]):
            current_values[header] = combo.currentText()

        # Restablecer las opciones aceptadas para reponer las opciones disponibles
        for header, value in current_values.items():
            if header != "Posición":
                if header in self.accepted_values and value in self.accepted_values[header]:
                    self.accepted_values[header].remove(value)
            else:
                if value != "DAQ" and value in self.accepted_positions:
                    self.accepted_positions.remove(value)

        # Habilitar los ComboBoxes para edición
        for col, (header, combo) in enumerate(self.entries[row]):
            combo.setEnabled(True)
            if header != "Posición":
                options = self.get_available_options(header, current_value=current_values[header])
            else:
                options = self.get_available_posiciones() + ([current_values[header]] if current_values[header] else [])
                options = list(dict.fromkeys(options))  # Eliminar duplicados preservando el orden
            combo.blockSignals(True)  # Evitar emitir señales mientras actualizamos
            combo.clear()
            combo.addItems(options)
            combo.setCurrentText(current_values[header])
            # No deshabilitar el ComboBox después de establecer el texto
            # Para permitir que el usuario lo edite
            combo.blockSignals(False)

        # Habilitar el botón "Aceptar" nuevamente
        accept_button = self.table.cellWidget(row, len(headers) + 1)
        accept_button.setEnabled(True)

        # Deshabilitar el botón "Editar" hasta que se acepte nuevamente
        edit_button = self.table.cellWidget(row, len(headers) + 2)
        edit_button.setEnabled(False)

    def save_lookuptable(self):
        """
        Guarda la LookUpTable actual en un archivo CSV.
        """
        campaign_name = self.selected_campaign.currentText()
        if not campaign_name or campaign_name == "No hay campañas disponibles":
            QMessageBox.critical(self, "Error", "Por favor, selecciona una campaña válida antes de guardar.")
            return

        # Verificar que todas las filas hayan sido aceptadas
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
            for col, (header, combo) in enumerate(self.entries[row]):
                value = combo.currentText()
                if not value:
                    QMessageBox.critical(self, "Error", f"Faltan valores en el Detector {row + 1}. Por favor, completa todos los campos.")
                    return

        save_dir = f"./lookuptable/{campaign_name}"
        os.makedirs(save_dir, exist_ok=True)
        file_name = f"{save_dir}/LookUpTable_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{campaign_name}.csv"

        data = []
        for row in range(self.num_detectors):
            row_data = {}
            for col, (header, combo) in enumerate(self.entries[row]):
                value = combo.currentText()
                row_data[header] = value
            data.append(row_data)

        df = pd.DataFrame(data)
        try:
            df.to_csv(file_name, index=False)
            QMessageBox.information(self, "Éxito", f"LookUpTable guardada en {file_name}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo guardar la LookUpTable: {str(e)}")

    def generate_detector_distribution(self):
        """
        Genera una distribución gráfica de los detectores.
        """
        campaign_name = self.selected_campaign.currentText()
        if not campaign_name or campaign_name == "No hay campañas disponibles":
            QMessageBox.critical(self, "Error", "Por favor, selecciona una campaña válida antes de generar la distribución.")
            return

        save_dir = f"./Graficos/Lookuptable/{campaign_name}"
        os.makedirs(save_dir, exist_ok=True)
        file_name = f"{save_dir}/Distribucion_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{campaign_name}.png"

        # Importar matplotlib
        try:
            import matplotlib.pyplot as plt
        except ImportError:
            QMessageBox.critical(self, "Error", "Matplotlib no está instalado. Por favor, instala matplotlib para generar gráficos.")
            return

        # Crear una figura de tamaño A4 horizontal
        fig, ax = plt.subplots(figsize=(11.69, 8.27))  # Tamaño en pulgadas para A4 horizontal

        # Configurar el título con fecha y hora
        title = f"Distribución de Detectores - {campaign_name}\nGenerado el {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        plt.title(title, fontsize=16, fontweight='bold', pad=20)

        # Definir márgenes y dimensiones de la cuadrícula
        margin = 0.05  # Margen como proporción del tamaño de la figura
        grid_rows = 5
        grid_cols = 4

        # Calcular el ancho y alto de cada celda
        total_width = 1 - 2 * margin
        total_height = 1 - 2 * margin - 0.1  # Reservar espacio para el título
        cell_width = total_width / grid_cols
        cell_height = total_height / grid_rows

        # Dibujar las líneas horizontales
        for i in range(grid_rows + 1):
            y = margin + i * cell_height + 0.05  # Ajuste vertical por el título
            ax.plot([margin, 1 - margin], [y, y], color='black')

        # Dibujar las líneas verticales
        for j in range(grid_cols + 1):
            x = margin + j * cell_width
            ax.plot([x, x], [margin + 0.05, margin + 0.05 + total_height], color='black')

        # Rellenar cada celda con la información del detector
        for row in range(self.num_detectors):
            for col, (header, combo) in enumerate(self.entries[row]):
                if header == "Posición":
                    pos_text = combo.currentText()
                    if pos_text:
                        # Extraer números de la posición (i,j)
                        pos_numbers = pos_text.strip("()").split(",")
                        if len(pos_numbers) == 2:
                            try:
                                i = int(pos_numbers[0]) - 1  # Índices 0-based
                                j = int(pos_numbers[1]) - 1
                                if 0 <= i < grid_rows and 0 <= j < grid_cols:
                                    # Calcular la posición del texto dentro de la celda
                                    x = margin + j * cell_width + cell_width / 2
                                    y = margin + 0.05 + (grid_rows - i - 0.5) * cell_height + 0.05

                                    # Ajustar la posición del texto hacia abajo dos líneas
                                    y_shift = cell_height * 0.2  # Ajuste hacia abajo (aproximadamente dos líneas)
                                    y -= y_shift

                                    # Recopilar toda la información del detector
                                    detector_info = []
                                    for h, cmb in self.entries[row]:
                                        # Cambiar "Contador Proporcional" a "Contador"
                                        if h.startswith("Contador Proporcional"):
                                            header_short = "Contador"
                                        else:
                                            header_short = h.split(' (')[0]
                                        detector_info.append(f"{header_short}: {cmb.currentText()}")
                                    cell_text = "\n".join(detector_info)

                                    # Añadir el texto a la figura
                                    ax.text(x, y, cell_text, ha='center', va='center', fontsize=6, fontweight='bold')
                            except ValueError:
                                continue

        # Establecer valor predeterminado "DAQ" en posición (5,3) si no está asignada
        self.set_default_position_daq()

        # Ajustar los límites de la figura
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)

        # Ocultar los ejes
        ax.axis('off')

        # Guardar el gráfico
        try:
            plt.savefig(file_name, bbox_inches='tight')
            plt.close()
            QMessageBox.information(self, "Éxito", f"Distribución de detectores guardada en {file_name}")
            self.display_generated_image(file_name)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo generar la distribución: {str(e)}")

    def set_default_position_daq(self):
        """
        Establece la posición (5,3) como "DAQ" por defecto si no está asignada.
        """
        default_pos = "(5,3)"
        daq_assigned = False

        # Verificar si "DAQ" ya está asignado a alguna posición
        for row in range(self.num_detectors):
            pos_combo = self.entries[row][6][1]  # Índice 6 para "Posición"
            if pos_combo.currentText() == "DAQ":
                daq_assigned = True
                break

        print(f"Verificando si 'DAQ' está asignado: {daq_assigned}")

        if not daq_assigned:
            # Buscar la posición (5,3)
            for row in range(self.num_detectors):
                pos_combo = self.entries[row][6][1]
                if pos_combo.currentText() == default_pos:
                    pos_combo.setCurrentText("DAQ")
                    self.accepted_positions.append("DAQ")
                    print(f"'DAQ' asignado a la posición (5,3) en el Detector {row + 1}")
                    # Deshabilitar "DAQ" en otros ComboBoxes
                    for r in range(self.num_detectors):
                        if r != row:
                            other_combo = self.entries[r][6][1]
                            index = other_combo.findText("DAQ")
                            if index != -1:
                                other_combo.removeItem(index)
                                print(f"'DAQ' removido de la posición (Fila {r + 1})")
                    break
        else:
            # Si "DAQ" ya está asignado, asegurarse de que no se pueda reasignar
            print("'DAQ' ya está asignado a una posición.")

    def display_generated_image(self, image_path):
        """
        Muestra la imagen generada en una ventana emergente.
        """
        if not os.path.exists(image_path):
            QMessageBox.critical(self, "Error", f"No se encontró el archivo de imagen: {image_path}")
            return

        dialog = ImageDisplayDialog(image_path, self)
        dialog.exec()

    def back(self):
        """
        Maneja la acción de regresar a la ventana anterior.
        """
        if callable(self.back_callback):
            self.back_callback()
        else:
            self.close()

    def open_add_material_dialog(self):
        """
        Abre un diálogo para agregar un nuevo material a un componente específico.
        """
        headers = [
            "Contador Proporcional (Numero/tipo/diametro/largo/marca)",
            "Preamplificador (Numero/modelo)",
            "Alto Voltaje (Modulo/Canal)",
            "Digitalizador (Modelo/Canal)",
            "Moderador (Geometria/Material/diametro-lado)",
            "Set Cables (numero o detalle)"
            # "Posición" excluida
        ]

        dialog = AddMaterialDialog(headers, self)
        if dialog.exec():
            selected_header = dialog.selected_header
            new_material = dialog.new_material

            # Crear un nuevo DataFrame con el nuevo material
            new_entry = {selected_header: new_material}
            new_df = pd.DataFrame([new_entry])

            # Concatenar el nuevo material al DataFrame existente
            self.material_data = pd.concat([self.material_data, new_df], ignore_index=True)

            # Guardar los cambios en 'materiales.csv'
            try:
                self.material_data.to_csv("./data/materiales.csv", index=False)
                QMessageBox.information(self, "Éxito", f"Nuevo material '{new_material}' añadido a '{selected_header}'.")
                self.refresh_table_options()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo guardar el nuevo material: {str(e)}")

    def refresh_table_options(self):
        """
        Actualiza las opciones de los QComboBox en la tabla después de agregar un nuevo material.
        """
        headers = [
            "Contador Proporcional (Numero/tipo/diametro/largo/marca)",
            "Preamplificador (Numero/modelo)",
            "Alto Voltaje (Modulo/Canal)",
            "Digitalizador (Modelo/Canal)",
            "Moderador (Geometria/Material/diametro-lado)",
            "Set Cables (numero o detalle)",
            "Posición"
        ]

        component_headers = headers[:-1]
        position_header = headers[-1]

        for row in range(self.num_detectors):
            for col, (header, combo) in enumerate(self.entries[row]):
                current_value = combo.currentText()
                print(f"Actualizando opciones para Fila {row + 1}, Columna '{header}': Valor Actual '{current_value}'")
                combo.blockSignals(True)  # Evitar emitir señales mientras actualizamos
                combo.clear()
                if header != position_header:
                    options = self.get_available_options(header, current_value)
                else:
                    # Manejar "Posición" por separado
                    options = [pos for pos in self.posiciones_disponibles if pos not in self.accepted_positions]
                    if current_value:
                        options.append(current_value)
                        options = list(dict.fromkeys(options))  # Eliminar duplicados preservando el orden
                combo.addItems(options)
                if current_value in options or (header == position_header and current_value == "DAQ"):
                    combo.setCurrentText(current_value)
                    if header != position_header or (header == position_header and current_value == "DAQ"):
                        combo.setEnabled(False)  # Deshabilitar si ya está asignado
                        print(f"Fila {row + 1}, Columna '{header}': QComboBox deshabilitado")
                else:
                    if options:
                        combo.setCurrentText(options[0])
                        print(f"Fila {row + 1}, Columna '{header}': Seleccionado valor por defecto '{options[0]}'")
                    else:
                        combo.setCurrentText("")
                        combo.setEnabled(False)
                        print(f"Fila {row + 1}, Columna '{header}': Sin opciones disponibles, QComboBox deshabilitado")
                combo.blockSignals(False)

    def load_existing_lookuptable(self):
        """
        Abre un diálogo para seleccionar y cargar una LookUpTable existente.
        """
        file_dialog = QFileDialog(self)
        file_dialog.setNameFilter("CSV Files (*.csv)")
        if file_dialog.exec():
            selected_files = file_dialog.selectedFiles()
            if selected_files:
                file_path = selected_files[0]
                try:
                    df_loaded = pd.read_csv(file_path, dtype=str)
                    df_loaded = df_loaded.where(pd.notnull(df_loaded), '')  # Reemplazar NaN con cadenas vacías

                    # Verificar que el número de detectores coincida
                    if len(df_loaded) != self.num_detectors:
                        QMessageBox.critical(self, "Error", "El número de detectores en el archivo no coincide con la campaña seleccionada.")
                        return

                    # Limpiar los valores aceptados actuales
                    headers = [
                        "Contador Proporcional (Numero/tipo/diametro/largo/marca)",
                        "Preamplificador (Numero/modelo)",
                        "Alto Voltaje (Modulo/Canal)",
                        "Digitalizador (Modelo/Canal)",
                        "Moderador (Geometria/Material/diametro-lado)",
                        "Set Cables (numero o detalle)",
                        "Posición"
                    ]
                    component_headers = headers[:-1]
                    position_header = headers[-1]

                    self.accepted_values = {header: [] for header in component_headers}
                    self.accepted_positions = []

                    # Asignar los valores cargados a la tabla y actualizar accepted_values
                    for row in range(self.num_detectors):
                        for col, header in enumerate(headers, start=1):
                            # Verificar que el encabezado exista en el CSV
                            if header not in df_loaded.columns:
                                QMessageBox.critical(self, "Error", f"El encabezado '{header}' no se encuentra en el archivo CSV.")
                                return

                            # Usar iloc para acceso basado en posición
                            value = df_loaded.iloc[row][header]
                            combo = self.entries[row][col - 1][1]
                            combo.blockSignals(True)
                            combo.setCurrentText(value)
                            combo.blockSignals(False)
                            # Actualizar accepted_values
                            if header != position_header and value:
                                self.accepted_values[header].append(value)
                            elif header == position_header and value and value != "DAQ":
                                self.accepted_positions.append(value)
                            # Mensaje de depuración
                            print(f"Fila {row + 1}, Columna '{header}': Asignado valor '{value}'")

                    # Manejar "Posición" por separado
                    for row in range(self.num_detectors):
                        combo = self.entries[row][6][1]  # Índice 6 para "Posición"
                        value = combo.currentText()
                        if value != "DAQ":
                            combo.setEnabled(False)
                        else:
                            combo.setEnabled(True)

                    # Deshabilitar el botón "Aceptar" y habilitar "Editar"
                    for row in range(self.num_detectors):
                        accept_button = self.table.cellWidget(row, len(headers) + 1)
                        accept_button.setEnabled(False)

                        edit_button = self.table.cellWidget(row, len(headers) + 2)
                        edit_button.setEnabled(True)
                    
                    # Establecer "DAQ" en posición (5,3) si no está asignada
                    self.set_default_position_daq()

                    # Actualizar las opciones de los ComboBoxes para reflejar las selecciones cargadas
                    self.refresh_table_options()

                    # Informar al usuario
                    QMessageBox.information(self, "Éxito", f"LookUpTable cargada exitosamente desde {file_path}")
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"No se pudo cargar la LookUpTable: {str(e)}")
