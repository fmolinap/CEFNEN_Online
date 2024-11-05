# fetch_root_files.py

from PySide6.QtWidgets import (
    QWidget, QLabel, QLineEdit, QPushButton, QMessageBox, QVBoxLayout, QHBoxLayout,
    QComboBox, QTextEdit, QInputDialog, QApplication, QProgressBar
)
from PySide6.QtCore import Qt, QThread, Signal
import os
import subprocess
import pandas as pd
from rsync_thread import RsyncThread  # Importar RsyncThread desde el nuevo módulo

class FetchRootFiles(QWidget):
    def __init__(self, back_callback=None):
        super().__init__()
        self.back_callback = back_callback
        self.DEFAULT_IP = "192.168.0.107"
        self.DEFAULT_USER = "lin"
        self.DEFAULT_PASSWORD = "linrulez"  # Aquí puedes poner la contraseña por defecto
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Traer archivos ROOT desde PC de Adquisición")
        self.resize(800, 600)
        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignTop)

        # Título
        title_label = QLabel("Traer archivos ROOT desde PC de Adquisición")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("font-size: 20px; font-weight: bold;")
        main_layout.addWidget(title_label)

        # Formulario de conexión
        form_layout = QVBoxLayout()
        main_layout.addLayout(form_layout)

        self.ip_entry = QLineEdit(self.DEFAULT_IP)
        self.port_entry = QLineEdit("22")
        self.user_entry = QLineEdit(self.DEFAULT_USER)

        form_layout.addWidget(self.create_form_row("IP del PC de Adquisición:", self.ip_entry))
        form_layout.addWidget(self.create_form_row("Puerto:", self.port_entry))
        form_layout.addWidget(self.create_form_row("Usuario:", self.user_entry))

        # Selección de campaña
        self.selected_campaign = QComboBox()
        self.campaigns = self.get_existing_campaigns()
        if self.campaigns:
            self.selected_campaign.addItems(self.campaigns)
        else:
            self.selected_campaign.addItem("No hay campañas disponibles")
        form_layout.addWidget(self.create_form_row("Seleccionar Campaña:", self.selected_campaign))

        # Botones de acción
        buttons_layout = QHBoxLayout()
        main_layout.addLayout(buttons_layout)

        # Asignar los botones a atributos de la clase
        self.fetch_button = QPushButton("Traer Archivos ROOT")
        self.fetch_button.setStyleSheet("background-color: #4CAF50; color: white;")
        self.fetch_button.clicked.connect(self.fetch_root_files)
        buttons_layout.addWidget(self.fetch_button)

        self.back_button = QPushButton("Regresar")
        self.back_button.setStyleSheet("background-color: #f44336; color: white;")
        self.back_button.clicked.connect(self.back)
        buttons_layout.addWidget(self.back_button)

        # Área de progreso
        progress_label = QLabel("Progreso de la transferencia:")
        main_layout.addWidget(progress_label)

        self.progress_text = QTextEdit()
        self.progress_text.setReadOnly(True)
        main_layout.addWidget(self.progress_text)

        # Barra de progreso
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        main_layout.addWidget(self.progress_bar)

        # Estilos
        self.setStyleSheet("""
            QLabel {
                font-size: 14px;
            }
            QLineEdit, QComboBox {
                font-size: 14px;
                padding: 5px;
            }
            QPushButton {
                min-width: 150px;
                padding: 10px;
                font-size: 14px;
            }
            QTextEdit {
                font-size: 13px;
            }
            QProgressBar {
                height: 25px;
            }
        """)

    def create_form_row(self, label_text, widget):
        row_widget = QWidget()
        row_layout = QHBoxLayout()
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setSpacing(10)
        row_widget.setLayout(row_layout)
        label = QLabel(label_text)
        label.setFixedWidth(200)
        row_layout.addWidget(label)
        row_layout.addWidget(widget)
        return row_widget

    def get_existing_campaigns(self):
        info_file = "./data/info_campaigns.csv"
        if not os.path.exists(info_file):
            return []
        df_info = pd.read_csv(info_file)
        return df_info["Nombre Corto"].tolist()

    def fetch_root_files(self):
        ip = self.ip_entry.text()
        port = self.port_entry.text()
        user = self.user_entry.text()
        campaign = self.selected_campaign.currentText()

        if not ip or not port or not user or not campaign:
            QMessageBox.critical(self, "Error", "Todos los campos son obligatorios.")
            return

        # Si la IP y el usuario coinciden con los valores predeterminados, usar la contraseña por defecto
        if ip == self.DEFAULT_IP and user == self.DEFAULT_USER:
            password = self.DEFAULT_PASSWORD
        else:
            password, ok = QInputDialog.getText(self, "Contraseña", "Ingrese la contraseña:", echo=QLineEdit.Password)
            if not ok or not password:
                QMessageBox.critical(self, "Error", "Contraseña no ingresada.")
                return

        try:
            remote_path = self.get_remote_path(campaign)
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))
            return

        local_path = f"./rootonline/{campaign}"
        os.makedirs(local_path, exist_ok=True)

        # Comando rsync sin comodines y con preservación de timestamps
        rsync_command = (
            f"sshpass -p '{password}' rsync -avz -e 'ssh -p {port}' "
            f"{user}@{ip}:{remote_path}/ {local_path}"
        )

        self.progress_text.append("Iniciando transferencia de archivos ROOT...\n")

        # Deshabilitar botones durante la transferencia
        self.fetch_button.setEnabled(False)
        self.back_button.setEnabled(False)

        # Crear y ejecutar el hilo de rsync
        self.rsync_thread = RsyncThread(rsync_command)
        self.rsync_thread.progress_signal.connect(self.update_progress)
        self.rsync_thread.error_signal.connect(self.show_error)
        self.rsync_thread.finished_signal.connect(self.transfer_finished)
        self.rsync_thread.start()

    def update_progress(self, text):
        self.progress_text.append(text)
        self.progress_text.ensureCursorVisible()
        # Actualizar la barra de progreso (esto es una simplificación)
        if "%" in text:
            try:
                percent = int(text.strip().split('%')[0])
                self.progress_bar.setValue(percent)
            except ValueError:
                pass  # Ignorar líneas que no contienen un porcentaje válido

    def show_error(self, error_text):
        self.progress_text.append(f"\nError: {error_text}\n")
        QMessageBox.critical(self, "Error", f"Ocurrió un error durante la transferencia:\n{error_text}")

    def transfer_finished(self, success):
        if success:
            self.progress_text.append("\nArchivos ROOT transferidos correctamente.\n")
            QMessageBox.information(self, "Éxito", "Transferencia completada con éxito.")
        else:
            self.progress_text.append("\nFallo en la transferencia de archivos.\n")
            QMessageBox.critical(self, "Error", "La transferencia de archivos ha fallado.")

        # Habilitar botones después de la transferencia
        self.fetch_button.setEnabled(True)
        self.back_button.setEnabled(True)
        self.progress_bar.setValue(0)

    def get_remote_path(self, campaign):
        info_file = "./data/info_campaigns.csv"
        df_info = pd.read_csv(info_file)
        campaign_info = df_info[df_info["Nombre Corto"] == campaign]

        if campaign_info.empty:
            raise ValueError(f"No se encontró información para la campaña '{campaign}'.")

        if "ROOT Path" not in campaign_info.columns:
            raise KeyError("La columna 'ROOT Path' no existe en el archivo info_campaigns.csv.")

        remote_path = campaign_info.iloc[0]["ROOT Path"]
        if not remote_path:
            raise ValueError("La ruta remota de ROOT no está definida para esta campaña.")

        return remote_path

    def back(self):
        if callable(self.back_callback):
            self.back_callback()
        else:
            self.close()

if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    window = FetchRootFiles()
    window.show()
    sys.exit(app.exec())
