# monitoreo_archivos_remotos.py

import paramiko
from PySide6.QtCore import QThread, Signal
from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QComboBox, QLineEdit, QPushButton, QHBoxLayout
import time
import os
from utils import get_existing_campaigns

class MonitoringThread(QThread):
    monitoring_status_changed = Signal(bool)
    error_signal = Signal(str)
    new_files_detected = Signal(str, str)  # Señal para emitir los nombres de los últimos archivos

    def __init__(self, ip, username, password, root_path, dlt_path):
        super().__init__()
        self.ip = ip
        self.username = username
        self.password = password
        self.root_path = root_path
        self.dlt_path = dlt_path
        self._running = True

    def run(self):
        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(hostname=self.ip, username=self.username, password=self.password)
            sftp = ssh.open_sftp()

            self.monitoring_status_changed.emit(True)

            while self._running:
                # Listar archivos en las rutas remotas
                root_files = sftp.listdir(self.root_path)
                dlt_files = sftp.listdir(self.dlt_path)

                # Obtener el último archivo ROOT y DLT
                last_root_file = self.get_latest_file(root_files, self.root_path, sftp)
                last_dlt_file = self.get_latest_file(dlt_files, self.dlt_path, sftp)

                # Emitir señal con los nombres de los archivos
                self.new_files_detected.emit(last_root_file, last_dlt_file)

                # Esperar 120 segundos (2 minutos)
                time.sleep(120)

            sftp.close()
            ssh.close()

        except Exception as e:
            self.error_signal.emit(str(e))
            self.monitoring_status_changed.emit(False)

    def stop(self):
        self._running = False

    def get_latest_file(self, files, path, sftp):
        latest_time = 0
        latest_file = 'N/A'
        for file in files:
            filepath = os.path.join(path, file)
            try:
                attr = sftp.stat(os.path.join(path, file))
                if attr.st_mtime > latest_time:
                    latest_time = attr.st_mtime
                    latest_file = file
            except:
                continue
        return latest_file

class MonitoringDialog(QDialog):
    monitoring_started = Signal(object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Iniciar Monitoreo")
        self.setModal(True)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()

        # Seleccionar campaña
        label_campaign = QLabel("Selecciona la campaña:")
        self.combo_campaign = QComboBox()
        campaigns = get_existing_campaigns()
        self.combo_campaign.addItems(campaigns)
        layout.addWidget(label_campaign)
        layout.addWidget(self.combo_campaign)

        # IP
        label_ip = QLabel("IP del PC de Adquisición:")
        self.edit_ip = QLineEdit()
        self.edit_ip.setText("192.168.0.107")
        layout.addWidget(label_ip)
        layout.addWidget(self.edit_ip)

        # Username
        label_username = QLabel("Nombre de Usuario:")
        self.edit_username = QLineEdit()
        self.edit_username.setText("lin")
        layout.addWidget(label_username)
        layout.addWidget(self.edit_username)

        # Password
        label_password = QLabel("Contraseña:")
        self.edit_password = QLineEdit()
        self.edit_password.setEchoMode(QLineEdit.Password)
        layout.addWidget(label_password)
        layout.addWidget(self.edit_password)

        # Botones
        button_layout = QHBoxLayout()
        self.button_start = QPushButton("Iniciar Monitoreo")
        self.button_cancel = QPushButton("Cancelar")
        button_layout.addWidget(self.button_start)
        button_layout.addWidget(self.button_cancel)
        layout.addLayout(button_layout)

        self.setLayout(layout)

        self.button_start.clicked.connect(self.accept)
        self.button_cancel.clicked.connect(self.reject)

    def get_monitoring_info(self):
        campaign = self.combo_campaign.currentText()
        ip = self.edit_ip.text()
        username = self.edit_username.text()
        password = self.edit_password.text()
        return campaign, ip, username, password
