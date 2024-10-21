# utils.py

import os
import pandas as pd
from PySide6.QtWidgets import QMessageBox, QWidget, QVBoxLayout, QCheckBox
from PySide6.QtCore import Qt
import paramiko
from datetime import datetime
import ROOT
ROOT.gROOT.SetBatch(True)

def get_existing_campaigns():
    info_file = "./data/info_campaigns.csv"
    if not os.path.exists(info_file):
        return []
    df_info = pd.read_csv(info_file)
    return df_info["Nombre Corto"].tolist()

def get_num_detectors(short_name):
    info_file = "./data/info_campaigns.csv"
    if not os.path.exists(info_file):
        return 0

    df = pd.read_csv(info_file)
    if 'Nombre Corto' not in df.columns or 'Número de Detectores' not in df.columns:
        return 0

    row = df[df['Nombre Corto'] == short_name]
    if row.empty:
        return 0

    return int(row['Número de Detectores'].values[0])

def get_campaign_info(short_name):
    info_file = "./data/info_campaigns.csv"
    if not os.path.exists(info_file):
        return None
    df_info = pd.read_csv(info_file)
    campaign_info = df_info[df_info["Nombre Corto"] == short_name]
    if campaign_info.empty:
        return None
    return campaign_info.iloc[0].to_dict()

def get_remote_path(campaign, file_type="ROOT"):
    info_file = "./data/info_campaigns.csv"
    df_info = pd.read_csv(info_file)
    campaign_info = df_info[df_info["Nombre Corto"] == campaign]

    if campaign_info.empty:
        raise ValueError(f"No se encontró información para la campaña '{campaign}'.")

    column_name = f"{file_type} Path"
    if column_name not in campaign_info.columns:
        raise KeyError(f"La columna '{column_name}' no existe en el archivo info_campaigns.csv.")

    remote_path = campaign_info.iloc[0][column_name]
    if not remote_path:
        raise ValueError(f"La ruta remota de {file_type} no está definida para esta campaña.")

    return remote_path

def save_detector_data(short_name, data_entries, new_dlt, observations):
    campaign_file = f"./data/{short_name}-CountingRate.csv"
    os.makedirs("./data", exist_ok=True)

    # Verificar si el archivo existe y cargar los datos existentes
    if os.path.exists(campaign_file):
        df = pd.read_csv(campaign_file)
    else:
        df = pd.DataFrame()

    new_data = {
        "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "dlt_file": new_dlt,
        "observations": observations
    }

    for i, (total_counts, neutron_counts) in enumerate(data_entries):
        total_counts = float(total_counts)
        neutron_counts = float(neutron_counts)

        if total_counts < neutron_counts:
            QMessageBox.critical(None, "Error", f"Las cuentas totales deben ser mayores o iguales a las cuentas de neutrones para el Detector {i+1}")
            return False

        if not df.empty and new_dlt == df["dlt_file"].iloc[-1]:
            if total_counts <= df[f"detector_{i+1}_total_counts"].iloc[-1] or neutron_counts <= df[f"detector_{i+1}_neutron_counts"].iloc[-1]:
                QMessageBox.critical(None, "Error", f"Las nuevas cuentas deben ser mayores que las cuentas anteriores para el Detector {i+1} cuando el archivo DLT es el mismo")
                return False

        new_data[f"detector_{i+1}_total_counts"] = total_counts
        new_data[f"detector_{i+1}_neutron_counts"] = neutron_counts

    df = pd.concat([df, pd.DataFrame([new_data])], ignore_index=True)
    df.to_csv(campaign_file, index=False)
    return True

def process_root_file(root_file_path):
    """
    Procesa un archivo ROOT y extrae los histogramas necesarios.
    """
    try:
        root_file = ROOT.TFile(root_file_path)
        if root_file.IsZombie():
            QMessageBox.critical(None, "Error", "No se pudo abrir el archivo ROOT.")
            return None

        hist_names = list({key.GetName().split(';')[0] for key in root_file.GetListOfKeys() if key.GetName().endswith(('_cal', '_CAL', '_Cal'))})
        if not hist_names:
            QMessageBox.critical(None, "Error", "No se encontraron histogramas con terminación '_cal', '_CAL' o '_Cal' en el archivo ROOT.")
            return None

        results = []
        for hist_name in hist_names:
            obj = root_file.Get(f"{hist_name};1")
            if isinstance(obj, ROOT.TH1):
                integral_total = obj.Integral(0, 15000)
                integral_region = obj.Integral(140, 820)
                results.append((hist_name, integral_total, integral_region))

        df = pd.DataFrame(results, columns=['Nombre del Histograma', 'Total Counts', 'Neutron Counts'])
        return df

    except Exception as e:
        QMessageBox.critical(None, "Error", f"No se pudo procesar el archivo ROOT: {e}")
        return None

def save_results_to_csv(short_name, df, new_dlt, observations):
    """
    Guarda los resultados procesados desde un archivo ROOT al archivo CSV de la campaña.
    """
    campaign_file = f"./data/{short_name}-CountingRate.csv"
    os.makedirs("./data", exist_ok=True)

    if os.path.exists(campaign_file):
        existing_df = pd.read_csv(campaign_file)
    else:
        existing_df = pd.DataFrame()

    new_data = {
        "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "dlt_file": new_dlt,
        "observations": observations
    }

    for i, row in df.iterrows():
        new_data[f"detector_{i+1}_total_counts"] = row['Total Counts']
        new_data[f"detector_{i+1}_neutron_counts"] = row['Neutron Counts']

    new_df = pd.concat([existing_df, pd.DataFrame([new_data])], ignore_index=True)
    new_df.to_csv(campaign_file, index=False)
    return True

def get_remote_root_files(ip, remote_path, username, password):
    """
    Conecta al PC remoto vía SSH, lista los archivos .root en la ruta especificada y devuelve la lista.
    """
    try:
        # Establecer conexión SSH
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname=ip, username=username, password=password)

        # Abrir una sesión SFTP
        sftp = ssh.open_sftp()

        # Listar archivos en la ruta remota
        files = sftp.listdir(remote_path)
        root_files = [f for f in files if f.endswith('.root')]

        # Cerrar conexiones
        sftp.close()
        ssh.close()

        return root_files

    except paramiko.AuthenticationException:
        raise Exception("Autenticación fallida. Verifica tu usuario y contraseña.")
    except paramiko.SSHException as sshException:
        raise Exception(f"Error al establecer conexión SSH: {sshException}")
    except FileNotFoundError:
        raise Exception(f"La ruta remota '{remote_path}' no existe.")
    except Exception as e:
        raise Exception(f"Ocurrió un error inesperado: {e}")

# --- Método actualizado para crear las casillas de verificación de detectores con opción "Seleccionar Todos" ---

def create_detector_checkboxes(num_detectors):
    """
    Crea un widget que contiene las casillas de verificación para los detectores,
    incluyendo una casilla para seleccionar todos.

    Args:
        num_detectors (int): Número total de detectores disponibles.

    Returns:
        QWidget: Un widget que contiene las casillas de verificación.
        list: Una lista con las casillas de verificación de los detectores.
        QCheckBox: La casilla de verificación "Seleccionar Todos".
    """
    # Widget contenedor
    container_widget = QWidget()
    layout = QVBoxLayout(container_widget)

    # Casilla de verificación "Seleccionar Todos"
    select_all_checkbox = QCheckBox("Seleccionar Todos")
    layout.addWidget(select_all_checkbox)

    # Contenedor para las casillas de los detectores
    detectors_layout = QVBoxLayout()
    detectors_checkboxes = []

    for i in range(num_detectors):
        checkbox = QCheckBox(f"Detector {i + 1}")
        detectors_layout.addWidget(checkbox)
        detectors_checkboxes.append(checkbox)

    # Conectar la casilla "Seleccionar Todos" con las casillas de detectores
    def toggle_select_all(checked):
        for checkbox in detectors_checkboxes:
            checkbox.blockSignals(True)
            checkbox.setChecked(checked)
            checkbox.blockSignals(False)
        # No es necesario llamar a update_select_all_state aquí

    def update_select_all_state():
        all_checked = all(cb.isChecked() for cb in detectors_checkboxes)
        select_all_checkbox.blockSignals(True)
        select_all_checkbox.setChecked(all_checked)
        select_all_checkbox.blockSignals(False)

    select_all_checkbox.toggled.connect(toggle_select_all)

    for checkbox in detectors_checkboxes:
        checkbox.stateChanged.connect(update_select_all_state)

    # Agregar las casillas de detectores al layout principal
    layout.addLayout(detectors_layout)

    return container_widget, detectors_checkboxes, select_all_checkbox
