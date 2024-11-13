# monitoreo_archivos_remotos.py

import paramiko
from PySide6.QtCore import QThread, Signal
from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QComboBox, QLineEdit, QPushButton, QHBoxLayout
import time
import os
from utils import get_existing_campaigns

# Importar pysmb
from smb.SMBConnection import SMBConnection

class MonitoringThread(QThread):
    monitoring_status_changed = Signal(bool)
    error_signal = Signal(str)
    new_files_detected = Signal(str, str, int, int)  # Señal para emitir los nombres de los últimos archivos, tamaño del archivo de la estación y tiempo total de medida

    def __init__(self, ip, username, password, root_path, dlt_path, smb_username, smb_password, smb_ip, smb_hostname):
        super().__init__()
        self.ip = ip
        self.username = username
        self.password = password
        self.root_path = root_path
        self.dlt_path = dlt_path
        self.smb_username = smb_username
        self.smb_password = smb_password
        self.smb_ip = smb_ip
        self.smb_hostname = smb_hostname
        self._running = True

    def run(self):
        try:
            # Establecer conexión SSH para archivos ROOT y DLT
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(hostname=self.ip, username=self.username, password=self.password)
            sftp = ssh.open_sftp()

            # Establecer conexión SMB para el archivo de la estación meteorológica
            smb_conn = SMBConnection(
                self.smb_username,
                self.smb_password,
                'python_client',
                self.smb_hostname,
                use_ntlm_v2=True
            )
            assert smb_conn.connect(self.smb_ip, 139)

            self.monitoring_status_changed.emit(True)

            while self._running:
                # Listar archivos en las rutas remotas
                root_files = sftp.listdir(self.root_path)
                dlt_files = sftp.listdir(self.dlt_path)

                # Obtener el último archivo ROOT y DLT
                last_root_file = self.get_latest_file(root_files, self.root_path, sftp)
                last_dlt_file = self.get_latest_file(dlt_files, self.dlt_path, sftp)

                # Obtener el tamaño del archivo de la estación meteorológica
                meteor_file_size = self.get_meteor_file_size(smb_conn)

                # Obtener el tiempo total de medida
                total_measurement_time = self.get_total_measurement_time(dlt_files, self.dlt_path, sftp)

                # Emitir señal con los nombres de los archivos, el tamaño del archivo de la estación y el tiempo total de medida
                self.new_files_detected.emit(last_root_file, last_dlt_file, meteor_file_size, total_measurement_time)

                # Esperar 120 segundos (2 minutos)
                time.sleep(120)

            sftp.close()
            ssh.close()
            smb_conn.close()

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

    def get_total_measurement_time(self, files, path, sftp):
        mod_times = []
        for file in files:
            try:
                attr = sftp.stat(os.path.join(path, file))
                mod_times.append(attr.st_mtime)
            except:
                continue
        if not mod_times:
            return 0
        total_time = max(mod_times) - min(mod_times)
        return int(total_time)

    def get_meteor_file_size(self, smb_conn):
        try:
            share_name = 'pc400'  # Nombre del recurso compartido en Windows (asegúrate de usar el nombre correcto)
            file_path = 'CR1000_Promedios_pm.dat'  # Nombre del archivo dentro del recurso compartido

            # Obtener información del archivo
            files = smb_conn.listPath(share_name, '/')

            # Buscar el archivo y obtener su tamaño
            for file in files:
                if file.filename.lower() == file_path.lower():
                    return file.file_size

            return -1  # Si no se encuentra el archivo
        except Exception as e:
            return -1  # En caso de error

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
        self.combo_campaign.setCurrentIndex(len(campaigns) - 1)
        layout.addWidget(label_campaign)
        layout.addWidget(self.combo_campaign)

        # SSH IP
        label_ip = QLabel("IP del PC de Adquisición (SSH):")
        self.edit_ip = QLineEdit()
        self.edit_ip.setText("192.168.0.107")
        layout.addWidget(label_ip)
        layout.addWidget(self.edit_ip)

        # SSH Username
        label_username = QLabel("Nombre de Usuario (SSH):")
        self.edit_username = QLineEdit()
        self.edit_username.setText("lin")
        layout.addWidget(label_username)
        layout.addWidget(self.edit_username)

        # SSH Password
        label_password = QLabel("Contraseña (SSH):")
        self.edit_password = QLineEdit()
        self.edit_password.setEchoMode(QLineEdit.Password)
        self.edit_password.setText("linrulez")
        layout.addWidget(label_password)
        layout.addWidget(self.edit_password)

        # SMB IP
        label_smb_ip = QLabel("IP del PC Windows (SMB):")
        self.edit_smb_ip = QLineEdit()
        self.edit_smb_ip.setText("192.168.0.123")
        layout.addWidget(label_smb_ip)
        layout.addWidget(self.edit_smb_ip)

        # SMB Hostname
        label_smb_hostname = QLabel("Nombre del Equipo Windows (SMB):")
        self.edit_smb_hostname = QLineEdit()
        self.edit_smb_hostname.setText("Portatilin4")
        layout.addWidget(label_smb_hostname)
        layout.addWidget(self.edit_smb_hostname)

        # SMB Username
        label_smb_username = QLabel("Nombre de Usuario (SMB):")
        self.edit_smb_username = QLineEdit()
        self.edit_smb_username.setText("lin")
        layout.addWidget(label_smb_username)
        layout.addWidget(self.edit_smb_username)

        # SMB Password
        label_smb_password = QLabel("Contraseña (SMB):")
        self.edit_smb_password = QLineEdit()
        self.edit_smb_password.setEchoMode(QLineEdit.Password)
        self.edit_smb_password.setText("linrulez")
        layout.addWidget(label_smb_password)
        layout.addWidget(self.edit_smb_password)

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
        smb_ip = self.edit_smb_ip.text()
        smb_hostname = self.edit_smb_hostname.text()
        smb_username = self.edit_smb_username.text()
        smb_password = self.edit_smb_password.text()
        return campaign, ip, username, password, smb_username, smb_password, smb_ip, smb_hostname
