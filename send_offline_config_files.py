from PySide6.QtWidgets import (
    QWidget, QLabel, QLineEdit, QPushButton, QMessageBox, QVBoxLayout, QHBoxLayout,
    QComboBox, QTextEdit, QInputDialog, QApplication, QProgressBar
)
from PySide6.QtCore import Qt, QThread, Signal
import os
import subprocess
import pandas as pd
from utils import get_existing_campaigns
from rsync_thread import RsyncThread  # Importar RsyncThread desde el nuevo módulo

class SendOfflineConfigFiles(QWidget):
    def __init__(self, back_callback=None):
        super().__init__()
        self.back_callback = back_callback
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Enviar archivos de configuración offline a PC de Adquisición")
        self.resize(800, 600)
        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignTop)

        # Título
        title_label = QLabel("Enviar archivos de configuración offline a PC de Adquisición")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("font-size: 20px; font-weight: bold;")
        main_layout.addWidget(title_label)

        # Formulario de conexión
        form_layout = QVBoxLayout()
        main_layout.addLayout(form_layout)

        self.ip_entry = QLineEdit("192.168.0.107")
        self.port_entry = QLineEdit("22")
        self.user_entry = QLineEdit("lin")

        form_layout.addWidget(self.create_form_row("IP del PC de Adquisición:", self.ip_entry))
        form_layout.addWidget(self.create_form_row("Puerto:", self.port_entry))
        form_layout.addWidget(self.create_form_row("Usuario:", self.user_entry))

        # Selección de campaña
        self.selected_campaign = QComboBox()
        self.campaigns = get_existing_campaigns()
        self.selected_campaign.addItems(self.campaigns)
        form_layout.addWidget(self.create_form_row("Seleccionar Campaña:", self.selected_campaign))

        # Botones de acción
        buttons_layout = QHBoxLayout()
        main_layout.addLayout(buttons_layout)

        self.send_button = QPushButton("Enviar Archivos de Configuración Offline")
        self.send_button.setStyleSheet("background-color: #4CAF50; color: white;")
        self.send_button.clicked.connect(self.send_offline_config_files)
        buttons_layout.addWidget(self.send_button)

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

    def send_offline_config_files(self):
        ip = self.ip_entry.text()
        port = self.port_entry.text()
        user = self.user_entry.text()
        campaign = self.selected_campaign.currentText()

        if not ip or not port or not user or not campaign:
            QMessageBox.critical(self, "Error", "Todos los campos son obligatorios.")
            return

        password, ok = QInputDialog.getText(self, "Contraseña", "Ingrese la contraseña:", echo=QLineEdit.Password)
        if not ok or not password:
            QMessageBox.critical(self, "Error", "Contraseña no ingresada.")
            return

        local_path = f"./calibration/{campaign}/"
        if not os.path.exists(local_path):
            QMessageBox.critical(self, "Error", f"No se encontró la ruta local: {local_path}")
            return

        # Ruta remota donde se enviarán los archivos
        remote_path = "/home/lin/data/ROOTFILES/ConfFilesOffline/"

        # Comando rsync para enviar los archivos .csv
        rsync_command = (
            f"sshpass -p '{password}' rsync -avz -e 'ssh -p {port}' "
            f"{local_path}*.csv {user}@{ip}:{remote_path}"
        )

        self.progress_text.append("Iniciando envío de archivos de configuración offline...\n")

        # Deshabilitar botones durante la transferencia
        self.send_button.setEnabled(False)
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

    def transfer_finished(self, success):
        if success:
            self.progress_text.append("\nArchivos de configuración offline enviados correctamente.\n")
            QMessageBox.information(self, "Éxito", "Envío completado con éxito.")
        else:
            self.progress_text.append("\nFallo en el envío de archivos.\n")
            QMessageBox.critical(self, "Error", "El envío de archivos ha fallado.")

        # Habilitar botones después de la transferencia
        self.send_button.setEnabled(True)
        self.back_button.setEnabled(True)
        self.progress_bar.setValue(0)

    def back(self):
        if callable(self.back_callback):
            self.back_callback()
        else:
            print("Error: back_callback no es callable")

if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    window = SendOfflineConfigFiles()
    window.show()
    sys.exit(app.exec())
