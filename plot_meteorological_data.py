# plot_meteorological_data.py

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QComboBox, QLineEdit,
    QHBoxLayout, QMessageBox, QCheckBox, QScrollArea, QDateTimeEdit, QGroupBox
)
from PySide6.QtCore import Qt
import os
from datetime import datetime
import matplotlib.pyplot as plt

from smb.SMBConnection import SMBConnection
import pandas as pd
import io

from utils import get_existing_campaigns, get_campaign_info

class PlotMeteorologicalData(QWidget):
    def __init__(self, back_callback=None):
        super().__init__()
        self.back_callback = back_callback
        self.setWindowTitle("Graficar Datos de Estación Meteorológica")
        self.resize(800, 600)

        # Definir los grupos de variables
        self.variable_groups = {
            "Variables_locales_Meteorológicas": {
                "variables": [
                    ("WS_ms_Avg", "Velocidad del viento en m/s"),
                    ("BP_mbar_Avg", "Presión Atmosférica en mbar"),
                    ("AirTC_Avg", "Temperatura del Aire en °C"),
                    ("RH_Min", "Humedad Relativa del Ambiente"),
                    ("Rain_mm_Tot", "Precipitaciones en mm"),
                    ("SlrW_Avg", "Intensidad Solar medida en Watts")
                ]
            },
            "Humedad_de_Suelo": {
                "variables": [
                    ("VWC_5cm", "Humedad del suelo a 5 cm"),
                    ("VWC_10cm", "Humedad del suelo a 10 cm"),
                    ("VWC_20cm", "Humedad del suelo a 20 cm"),
                    ("VWC_30cm", "Humedad del suelo a 30 cm"),
                    ("VWC_40cm", "Humedad del suelo a 40 cm"),
                    ("VWC_50cm", "Humedad del suelo a 50 cm")
                ]
            },
            "Temperatura_del_Suelo": {
                "variables": [
                    ("TC_5cm", "Temperatura del suelo a 5 cm"),
                    ("TC_10cm", "Temperatura del suelo a 10 cm"),
                    ("TC_20cm", "Temperatura del suelo a 20 cm"),
                    ("TC_30cm", "Temperatura del suelo a 30 cm"),
                    ("TC_40cm", "Temperatura del suelo a 40 cm"),
                    ("TC_50cm", "Temperatura del suelo a 50 cm")
                ]
            },
            "Permitividad_Eléctrica_del_Suelo": {
                "variables": [
                    ("Perm_5cm", "Permitividad del suelo a 5 cm"),
                    ("Perm_10cm", "Permitividad del suelo a 10 cm"),
                    ("Perm_20cm", "Permitividad del suelo a 20 cm"),
                    ("Perm_30cm", "Permitividad del suelo a 30 cm"),
                    ("Perm_40cm", "Permitividad del suelo a 40 cm"),
                    ("Perm_50cm", "Permitividad del suelo a 50 cm")
                ]
            },
            "Conductividad_Eléctrica_del_Suelo": {
                "variables": [
                    ("EC_5cm", "Conductividad Eléctrica del suelo a 5 cm"),
                    ("EC_10cm", "Conductividad Eléctrica del suelo a 10 cm"),
                    ("EC_20cm", "Conductividad Eléctrica del suelo a 20 cm"),
                    ("EC_30cm", "Conductividad Eléctrica del suelo a 30 cm"),
                    ("EC_40cm", "Conductividad Eléctrica del suelo a 40 cm"),
                    ("EC_50cm", "Conductividad Eléctrica del suelo a 50 cm")
                ]
            }
        }

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Selección de campaña
        campaign_layout = QHBoxLayout()
        campaign_label = QLabel("Seleccionar Campaña:")
        self.campaign_combo = QComboBox()
        campaigns = get_existing_campaigns()
        self.campaign_combo.addItems(campaigns)
        campaign_layout.addWidget(campaign_label)
        campaign_layout.addWidget(self.campaign_combo)
        layout.addLayout(campaign_layout)

        # Botón para obtener rango de fechas
        self.date_range_button = QPushButton("Obtener Rango de Fechas")
        self.date_range_button.clicked.connect(self.get_campaign_date_range)
        layout.addWidget(self.date_range_button)

        # Mostrar rango de fechas
        self.date_range_label = QLabel("Rango de Fechas: N/A")
        layout.addWidget(self.date_range_label)

        # Credenciales SMB
        smb_layout = QHBoxLayout()
        smb_label = QLabel("Credenciales SMB:")
        smb_layout.addWidget(smb_label)

        self.smb_username = QLineEdit()
        self.smb_username.setPlaceholderText("Usuario")
        self.smb_username.setText("lin")
        smb_layout.addWidget(self.smb_username)

        self.smb_password = QLineEdit()
        self.smb_password.setPlaceholderText("Contraseña")
        self.smb_password.setEchoMode(QLineEdit.Password)
        self.smb_password.setText("linrulez")
        smb_layout.addWidget(self.smb_password)

        self.smb_ip = QLineEdit()
        self.smb_ip.setPlaceholderText("IP SMB")
        self.smb_ip.setText("192.168.0.123")
        smb_layout.addWidget(self.smb_ip)

        self.smb_hostname = QLineEdit()
        self.smb_hostname.setPlaceholderText("Nombre del Equipo SMB")
        self.smb_hostname.setText("Portatilin4")
        smb_layout.addWidget(self.smb_hostname)

        layout.addLayout(smb_layout)

        # Botón para obtener datos de estación meteorológica
        self.connect_button = QPushButton("Obtener Datos de Estación Meteorológica")
        self.connect_button.clicked.connect(self.obtain_meteorological_data)
        layout.addWidget(self.connect_button)

        # Selección de rango de fechas para graficar
        date_range_layout = QHBoxLayout()
        start_date_label = QLabel("Fecha Inicio:")
        self.plot_start_date = QDateTimeEdit()
        self.plot_start_date.setCalendarPopup(True)
        self.plot_start_date.setEnabled(False)
        date_range_layout.addWidget(start_date_label)
        date_range_layout.addWidget(self.plot_start_date)

        end_date_label = QLabel("Fecha Fin:")
        self.plot_end_date = QDateTimeEdit()
        self.plot_end_date.setCalendarPopup(True)
        self.plot_end_date.setEnabled(False)
        date_range_layout.addWidget(end_date_label)
        date_range_layout.addWidget(self.plot_end_date)

        layout.addLayout(date_range_layout)

        # Selección de grupos
        self.groups_layout = QVBoxLayout()
        self.group_checkboxes = []

        self.groups_groupbox = QGroupBox("Seleccionar Grupos a Graficar")
        self.groups_groupbox.setLayout(self.groups_layout)
        self.groups_groupbox.setEnabled(False)
        layout.addWidget(self.groups_groupbox)

        for group_name in self.variable_groups.keys():
            checkbox = QCheckBox(group_name.replace('_', ' '))
            self.groups_layout.addWidget(checkbox)
            self.group_checkboxes.append(checkbox)

        # Botón para graficar
        self.plot_button = QPushButton("Graficar Datos")
        self.plot_button.clicked.connect(self.plot_data)
        self.plot_button.setEnabled(False)
        layout.addWidget(self.plot_button)

        # Botón para regresar
        self.back_button = QPushButton("Regresar")
        self.back_button.clicked.connect(self.back)
        layout.addWidget(self.back_button)

    def get_campaign_date_range(self):
        short_name = self.campaign_combo.currentText()
        campaign_info = get_campaign_info(short_name)
        if not campaign_info:
            QMessageBox.critical(self, "Error", "No se pudo obtener información de la campaña.")
            return

        # Suponiendo que tienes un archivo CSV con timestamps de la campaña
        data_file = f"./data/{short_name}-CountingRate.csv"
        if not os.path.exists(data_file):
            QMessageBox.critical(self, "Error", f"No se encontró el archivo {data_file}")
            return

        df = pd.read_csv(data_file)
        if 'timestamp' not in df.columns:
            QMessageBox.critical(self, "Error", "El archivo de datos no contiene la columna 'timestamp'.")
            return

        df['timestamp'] = pd.to_datetime(df['timestamp'])
        self.start_date = df['timestamp'].min()
        self.end_date = df['timestamp'].max()

        self.date_range_label.setText(f"Rango de Fechas: {self.start_date} - {self.end_date}")

        # Establecer fechas en los selectores de fecha
        self.plot_start_date.setDateTime(self.start_date)
        self.plot_end_date.setDateTime(self.end_date)

    def obtain_meteorological_data(self):
        smb_username = self.smb_username.text()
        smb_password = self.smb_password.text()
        smb_ip = self.smb_ip.text()
        smb_hostname = self.smb_hostname.text()
        short_name = self.campaign_combo.currentText()

        try:
            # Conectar al recurso compartido SMB
            smb_conn = SMBConnection(
                smb_username,
                smb_password,
                'python_client',
                smb_hostname,
                use_ntlm_v2=True
            )
            assert smb_conn.connect(smb_ip, 139)

            share_name = 'pc400'  # Nombre del recurso compartido
            file_path = 'CR1000_Promedios_pm.dat'

            # Descargar el archivo temporalmente
            with open('temp.dat', 'wb') as temp_file:
                smb_conn.retrieveFile(share_name, file_path, temp_file)
            smb_conn.close()

            # Leer el archivo y filtrar por rango de fechas de la campaña
            df = pd.read_csv('temp.dat', skiprows=[0, 2], parse_dates=['TIMESTAMP'], na_values=['NAN'])
            os.remove('temp.dat')

            # Filtrar datos por rango de fechas de la campaña
            df = df[(df['TIMESTAMP'] >= self.start_date) & (df['TIMESTAMP'] <= self.end_date)]

            if df.empty:
                QMessageBox.information(self, "Información", "No hay datos en el rango de fechas de la campaña.")
                return

            # Guardar datos en CSV
            csv_filename = f'./data/variables_locales_1m_{short_name}.csv'
            if os.path.exists(csv_filename):
                # Leer datos existentes
                df_existing = pd.read_csv(csv_filename, parse_dates=['TIMESTAMP'])
                # Combinar y eliminar duplicados
                df_combined = pd.concat([df_existing, df]).drop_duplicates(subset='TIMESTAMP').sort_values('TIMESTAMP')
            else:
                df_combined = df

            # Guardar datos combinados
            df_combined.to_csv(csv_filename, index=False)

            # Actualizar selectores de fecha
            self.plot_start_date.setDateTime(df_combined['TIMESTAMP'].min())
            self.plot_end_date.setDateTime(df_combined['TIMESTAMP'].max())

            # Habilitar controles
            self.plot_start_date.setEnabled(True)
            self.plot_end_date.setEnabled(True)
            self.groups_groupbox.setEnabled(True)
            self.plot_button.setEnabled(True)

            QMessageBox.information(self, "Éxito", "Datos obtenidos y guardados correctamente.")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo obtener los datos: {e}")
            return

    def plot_data(self):
        selected_groups = [cb.text().replace(' ', '_') for cb in self.group_checkboxes if cb.isChecked()]
        if not selected_groups:
            QMessageBox.warning(self, "Advertencia", "Debe seleccionar al menos un grupo para graficar.")
            return

        short_name = self.campaign_combo.currentText()
        csv_filename = f'./data/variables_locales_1m_{short_name}.csv'
        if not os.path.exists(csv_filename):
            QMessageBox.critical(self, "Error", f"No se encontró el archivo {csv_filename}")
            return

        df = pd.read_csv(csv_filename, parse_dates=['TIMESTAMP'])

        # Filtrar por rango de fechas
        start_date = self.plot_start_date.dateTime().toPython()
        end_date = self.plot_end_date.dateTime().toPython()
        df = df[(df['TIMESTAMP'] >= start_date) & (df['TIMESTAMP'] <= end_date)]

        if df.empty:
            QMessageBox.information(self, "Información", "No hay datos en el rango de fechas seleccionado.")
            return

        for group_name in selected_groups:
            group_info = self.variable_groups[group_name]
            variables = group_info['variables']
            num_vars = len(variables)

            # Determinar tamaño de la cuadrícula
            n_cols = 2
            n_rows = (num_vars + 1) // n_cols

            fig, axes = plt.subplots(n_rows, n_cols, figsize=(15, 5 * n_rows))
            axes = axes.flatten()

            colors = plt.rcParams['axes.prop_cycle'].by_key()['color']
            for idx, (var_name, var_label) in enumerate(variables):
                ax = axes[idx]
                if var_name in df.columns:
                    color = colors[idx % len(colors)]
                    ax.plot(df['TIMESTAMP'], df[var_name], label=var_label, color=color)
                    ax.set_title(var_label)
                    ax.set_xlabel('Fecha y Hora')
                    ax.set_ylabel(var_label)
                    ax.legend()
                else:
                    ax.text(0.5, 0.5, f'Variable {var_name} no encontrada en los datos', ha='center', va='center')
                    ax.axis('off')

            # Ocultar subplots no utilizados
            for idx in range(len(variables), len(axes)):
                fig.delaxes(axes[idx])

            fig.suptitle(f'{group_name.replace("_", " ")} - {short_name}')
            fig.tight_layout(rect=[0, 0.03, 1, 0.95])

            # Guardar el gráfico sin fecha y hora en el nombre del archivo
            output_dir = f'./Graficos/EstacionMeteorologica/{short_name}'
            os.makedirs(output_dir, exist_ok=True)
            filename = f'{group_name}_{short_name}.png'
            filepath = os.path.join(output_dir, filename)
            fig.savefig(filepath)

            # Mostrar el gráfico
            plt.show()

    def back(self):
        if callable(self.back_callback):
            self.back_callback()
        else:
            self.close()
