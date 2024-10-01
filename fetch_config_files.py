from PySide6.QtWidgets import (
    QWidget, QLabel, QLineEdit, QPushButton, QMessageBox, QVBoxLayout, QHBoxLayout,
    QTextEdit, QInputDialog, QApplication, QProgressBar
)
from PySide6.QtCore import Qt, QThread, Signal
import os
import subprocess
from rsync_thread import RsyncThread  # Importar RsyncThread desde el nuevo módulo

class FetchConfigFiles(QWidget):
    def __init__(self, back_callback=None):
        super().__init__()
        self.back_callback = back_callback
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Traer archivos de configuración desde PC de Adquisición")
        self.resize(800, 600)
        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignTop)

        # Título
        title_label = QLabel("Traer archivos de configuración desde PC de Adquisición")
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

        # Botones de acción
        buttons_layout = QHBoxLayout()
        main_layout.addLayout(buttons_layout)

        self.fetch_button = QPushButton("Traer Archivos de Configuración")
        self.fetch_button.setStyleSheet("background-color: #4CAF50; color: white;")
        self.fetch_button.clicked.connect(self.fetch_config_files)
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
            QLineEdit {
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

    def fetch_config_files(self):
        ip = self.ip_entry.text()
        port = self.port_entry.text()
        user = self.user_entry.text()

        if not ip or not port or not user:
            QMessageBox.critical(self, "Error", "Todos los campos son obligatorios.")
            return

        password, ok = QInputDialog.getText(self, "Contraseña", "Ingrese la contraseña:", echo=QLineEdit.Password)
        if not ok or not password:
            QMessageBox.critical(self, "Error", "Contraseña no ingresada.")
            return

        remote_path = "/home/lin/data/EXPERIMENTS_RAW_DATA/2024/ConfigFiles2024"
        local_path = "./calibration/ConfigFiles2024"
        os.makedirs(local_path, exist_ok=True)

        # Comando rsync para archivos de configuración
        rsync_command = (
            f"sshpass -p '{password}' rsync -avz --times -e 'ssh -p {port}' "
            f"{user}@{ip}:{remote_path}/ {local_path}"
        )

        self.progress_text.append("Iniciando transferencia de archivos de configuración...\n")

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

    def transfer_finished(self, success):
        if success:
            self.progress_text.append("\nArchivos de configuración transferidos correctamente.\n")
            QMessageBox.information(self, "Éxito", "Transferencia completada con éxito.")
        else:
            self.progress_text.append("\nFallo en la transferencia de archivos.\n")
            QMessageBox.critical(self, "Error", "La transferencia de archivos ha fallado.")

        # Habilitar botones después de la transferencia
        self.fetch_button.setEnabled(True)
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
    window = FetchConfigFiles()
    window.show()
    sys.exit(app.exec())
