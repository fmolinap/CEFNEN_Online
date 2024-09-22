import os
import pandas as pd
from PySide6.QtWidgets import QMessageBox

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

def get_last_timestamp(short_name):
    campaign_file = f"./data/{short_name}-CountingRate.csv"
    if not os.path.exists(campaign_file):
        return None
    df = pd.read_csv(campaign_file)
    if df.empty:
        return None
    return df["timestamp"].iloc[-1]

def get_current_dlt(short_name):
    campaign_file = f"./data/{short_name}-CountingRate.csv"
    if not os.path.exists(campaign_file):
        return None
    df = pd.read_csv(campaign_file)
    if df.empty:
        return None
    return df["dlt_file"].iloc[-1]

def save_detector_data(short_name, data_entries, new_dlt, observations, back_callback=None):
    campaign_file = f"./data/{short_name}-CountingRate.csv"
    os.makedirs("./data", exist_ok=True)

    # Verificar si el archivo existe y cargar los datos existentes
    if os.path.exists(campaign_file):
        df = pd.read_csv(campaign_file)
    else:
        df = pd.DataFrame()

    new_data = {
        "timestamp": pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S'),
        "dlt_file": new_dlt,
        "observations": observations
    }

    for i, (total_counts, neutron_counts) in enumerate(data_entries):
        total_counts = int(total_counts)
        neutron_counts = int(neutron_counts)

        if total_counts < neutron_counts:
            QMessageBox.critical(None, "Error", f"Las cuentas totales deben ser mayores o iguales a las cuentas de neutrones para el Detector {i+1}")
            return

        # Comprobar si el DataFrame no está vacío antes de acceder a sus elementos
        if not df.empty and new_dlt == df["dlt_file"].iloc[-1]:
            if total_counts <= df[f"detector_{i+1}_total_counts"].iloc[-1] or neutron_counts <= df[f"detector_{i+1}_neutron_counts"].iloc[-1]:
                QMessageBox.critical(None, "Error", f"Las nuevas cuentas deben ser mayores que las cuentas anteriores para el Detector {i+1} cuando el archivo DLT es el mismo")
                return

        new_data[f"detector_{i+1}_total_counts"] = total_counts
        new_data[f"detector_{i+1}_neutron_counts"] = neutron_counts

    # Concatenar el nuevo registro con el DataFrame existente
    df = pd.concat([df, pd.DataFrame([new_data])], ignore_index=True)
    df.to_csv(campaign_file, index=False)
    QMessageBox.information(None, "Info", "Datos de la campaña guardados con éxito.")
    if back_callback:
        back_callback()
