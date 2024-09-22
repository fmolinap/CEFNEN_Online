from PySide6.QtWidgets import (
    QWidget, QLabel, QLineEdit, QPushButton, QMessageBox, QVBoxLayout,
    QHBoxLayout, QFormLayout, QGroupBox, QApplication
)
from PySide6.QtGui import QIcon
from PySide6.QtCore import Qt
import os
import pandas as pd

class EditMaterials(QWidget):
    def __init__(self, back_callback=None):
        super().__init__()
        self.back_callback = back_callback
        self.material_fields = [
            "Contador Proporcional (Número/tipo/diámetro/largo/marca)",
            "Preamplificador (Número/modelo)",
            "Alto Voltaje (Módulo/Canal)",
            "Digitalizador (Modelo/Canal)",
            "Moderador (Geometría/Material/diámetro-lado)",
            "Set Cables (número o detalle)"
        ]
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Editar Materiales en Campaña")
        self.resize(600, 500)

        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignTop)

        # Título
        title_label = QLabel("Editar Materiales en Campaña")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("font-size: 24px; font-weight: bold; margin-bottom: 20px;")
        main_layout.addWidget(title_label)

        # Formulario de materiales
        form_group_box = QGroupBox("Materiales")
        form_layout = QFormLayout()
        form_group_box.setLayout(form_layout)
        main_layout.addWidget(form_group_box)

        self.material_entries = {}
        for field in self.material_fields:
            entry = QLineEdit()
            self.material_entries[field] = entry
            form_layout.addRow(QLabel(field + ":"), entry)

        # Botones de acción
        buttons_layout = QHBoxLayout()
        main_layout.addLayout(buttons_layout)

        save_button = QPushButton("Guardar Todos")
        save_button.setIcon(QIcon.fromTheme("document-save"))
        save_button.clicked.connect(self.save_all_materials)
        buttons_layout.addWidget(save_button)

        back_button = QPushButton("Regresar")
        back_button.setIcon(QIcon.fromTheme("go-previous"))
        back_button.clicked.connect(self.back)
        buttons_layout.addWidget(back_button)

        # Estilos
        self.setStyleSheet("""
            QWidget {
                font-size: 14px;
            }
            QGroupBox {
                font-size: 16px;
                font-weight: bold;
                margin-top: 20px;
            }
            QLabel {
                min-width: 200px;
            }
            QPushButton {
                min-width: 120px;
                padding: 8px;
            }
        """)

    def save_all_materials(self):
        materials_file = "./data/materiales.csv"
        df_materials = pd.read_csv(materials_file) if os.path.exists(materials_file) else pd.DataFrame(columns=self.material_fields)

        new_row = {}
        for field in self.material_fields:
            new_value = self.material_entries[field].text()
            if not new_value:
                QMessageBox.critical(self, "Error", f"El campo '{field}' no puede estar vacío.")
                return
            new_row[field] = new_value

        # Verificar duplicados
        for field in self.material_fields:
            if new_row[field] in df_materials[field].values:
                QMessageBox.warning(self, "Advertencia", f"El material en '{field}' ya existe y no será agregado de nuevo.")
                new_row[field] = None  # Evitar duplicados

        df_materials = df_materials.append(new_row, ignore_index=True)
        df_materials.to_csv(materials_file, index=False)
        QMessageBox.information(self, "Información", "Materiales guardados correctamente.")
        self.clear_fields()

    def clear_fields(self):
        for entry in self.material_entries.values():
            entry.clear()

    def back(self):
        if callable(self.back_callback):
            self.back_callback()

if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    window = EditMaterials()
    window.show()
    sys.exit(app.exec())
