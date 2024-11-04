# incident_report.py

from PySide6.QtWidgets import (
    QWidget, QLabel, QLineEdit, QPushButton, QMessageBox, QVBoxLayout, QHBoxLayout,
    QComboBox, QTextEdit, QFileDialog, QListWidget, QInputDialog, QListWidgetItem, QApplication
)
from PySide6.QtCore import Qt
import os
import pandas as pd
from datetime import datetime

class IncidentReport(QWidget):
    def __init__(self, back_callback=None, last_dlt_file=""):
        super().__init__()
        self.back_callback = back_callback
        self.graph_options = []
        self.last_dlt_file = last_dlt_file  # Almacenar el último archivo DLT
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Reporte de Incidencias")
        self.resize(800, 600)
        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignTop)

        # Título
        title_label = QLabel("Bitácora de Campaña y Reporte de Incidencias")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("font-size: 24px; font-weight: bold;")
        main_layout.addWidget(title_label)

        # Formulario principal
        form_layout = QVBoxLayout()
        main_layout.addLayout(form_layout)

        # Fecha y Hora
        timestamp_layout = QHBoxLayout()
        timestamp_label = QLabel("Fecha y Hora:")
        self.timestamp_value = QLabel(datetime.now().strftime("%Y-%m-%d %H:%M"))
        timestamp_layout.addWidget(timestamp_label)
        timestamp_layout.addWidget(self.timestamp_value)
        form_layout.addLayout(timestamp_layout)

        # Seleccionar Campaña
        campaign_layout = QHBoxLayout()
        campaign_label = QLabel("Seleccionar Campaña:")
        self.selected_campaign = QComboBox()
        self.campaigns = self.get_existing_campaigns()
        self.selected_campaign.addItems(self.campaigns)
        campaign_layout.addWidget(campaign_label)
        campaign_layout.addWidget(self.selected_campaign)
        form_layout.addLayout(campaign_layout)

        # Tipo de Incidencia
        incident_type_layout = QHBoxLayout()
        incident_type_label = QLabel("Tipo de Incidencia:")
        self.incident_type = QComboBox()
        incident_types = [
            "Inicio de Turno", "Monitoreo Regular durante Turno", "Término de Turno", "Inicio de Campaña", "Término de Campaña",
            "Detención Adquisición", "Reinicio Adquisición", "Problemas de Calibración",
            "Problemas de Ruido", "Problemas Eléctricos", "Mejoras siguiente campaña",
            "Problemas de Adquisición Hardware", "Problemas de Adquisición Software",
            "Cambio en Lookup Table", "Problema no identificado", "Otra"
        ]
        self.incident_type.addItems(incident_types)
        incident_type_layout.addWidget(incident_type_label)
        incident_type_layout.addWidget(self.incident_type)
        form_layout.addLayout(incident_type_layout)

        # Archivo DLT Actual
        dlt_layout = QHBoxLayout()
        dlt_label = QLabel("Archivo DLT Actual:")
        self.dlt_file = QLineEdit()
        self.dlt_file.setText(self.last_dlt_file)  # Establecer el último archivo DLT
        dlt_layout.addWidget(dlt_label)
        dlt_layout.addWidget(self.dlt_file)
        form_layout.addLayout(dlt_layout)

        # Responsable de Turno
        responsible_layout = QHBoxLayout()
        responsible_label = QLabel("Responsable de Turno:")
        self.responsible_person = QComboBox()
        responsible_persons = ["Francisco Molina", "Marcelo Zambra", "Jaime Romero", "Franco Lopez", "Javier Ruiz", "Otro"]
        self.responsible_person.addItems(responsible_persons)
        responsible_layout.addWidget(responsible_label)
        responsible_layout.addWidget(self.responsible_person)
        form_layout.addLayout(responsible_layout)

        # Descripción de la Incidencia
        description_label = QLabel("Escribir texto aquí:")
        form_layout.addWidget(description_label)
        self.incident_description = QTextEdit()
        form_layout.addWidget(self.incident_description)

        # Agregar Gráficos
        self.graph_files = []
        add_graph_button = QPushButton("Agregar Gráficos")
        add_graph_button.clicked.connect(self.add_graph)
        form_layout.addWidget(add_graph_button)

        self.graph_list = QListWidget()
        form_layout.addWidget(self.graph_list)

        # Botones de acción
        buttons_layout = QHBoxLayout()
        save_button = QPushButton("Guardar en Bitácora")
        save_button.setStyleSheet("background-color: #4CAF50; color: white;")
        save_button.clicked.connect(self.save_incident)
        buttons_layout.addWidget(save_button)

        edit_button = QPushButton("Editar una Entrada Anterior")
        edit_button.setStyleSheet("background-color: #2196F3; color: white;")
        edit_button.clicked.connect(self.edit_incident)
        buttons_layout.addWidget(edit_button)

        back_button = QPushButton("Regresar")
        back_button.setStyleSheet("background-color: #f44336; color: white;")
        back_button.clicked.connect(self.back)
        buttons_layout.addWidget(back_button)

        form_layout.addLayout(buttons_layout)

        # Últimas Incidencias
        incidents_label = QLabel("Últimas Entradas en Bitácora:")
        incidents_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        main_layout.addWidget(incidents_label)

        self.incident_list = QListWidget()
        main_layout.addWidget(self.incident_list)

        # Cargar incidencias iniciales
        self.load_incidents()

        # Estilos
        self.setStyleSheet("""
            QLabel {
                font-size: 14px;
            }
            QLineEdit, QComboBox, QTextEdit {
                font-size: 14px;
            }
            QPushButton {
                min-width: 150px;
                padding: 10px;
                font-size: 14px;
            }
            QListWidget {
                font-size: 13px;
            }
        """)

        # Conexiones
        self.selected_campaign.currentIndexChanged.connect(self.load_incidents)

    def add_graph(self):
        graph_type, ok = QInputDialog.getItem(
            self, "Seleccionar Tipo de Gráfico", "Tipo de Gráfico:",
            ["Plot Counting Rate", "Plot Comparison", "Análisis de Ruido", "Nueva LookUpTable"], 0, False
        )
        if not ok:
            return

        campaign = self.selected_campaign.currentText()
        if graph_type == "Plot Counting Rate":
            directory = f"./Graficos/{campaign}"
        elif graph_type == "Plot Comparison":
            directory = f"./Graficos/Comparison/{campaign}"
        elif graph_type == "Nueva LookUpTable":
            directory = f"./Graficos/Lookuptable/{campaign}"
        else:
            directory = f"./Graficos/NoiseAnalysis/{campaign}"

        file_path, _ = QFileDialog.getOpenFileName(
            self, "Seleccionar Archivo Gráfico", directory, "PNG files (*.png)"
        )
        if file_path:
            self.graph_files.append((graph_type, file_path))
            item_text = f"{graph_type}: {os.path.basename(file_path)}"
            self.graph_list.addItem(item_text)

    def save_incident(self):
        campaign = self.selected_campaign.currentText()
        directory = f"./incidencias/{campaign}"
        os.makedirs(directory, exist_ok=True)
        file_name = f"{directory}/Incidencias_{campaign}.csv"

        new_incident = {
            "Fecha y Hora": self.timestamp_value.text(),
            "Campaña": campaign,
            "Tipo de Incidencia": self.incident_type.currentText(),
            "Archivo DLT": self.dlt_file.text(),
            "Responsable de Turno": self.responsible_person.currentText(),
            "Descripcion de Incidencia": self.incident_description.toPlainText().strip()
        }

        for i, (graph_type, graph_path) in enumerate(self.graph_files):
            new_incident[f"Archivo Grafico {i + 1}"] = graph_path

        columns = [
            "Fecha y Hora", "Campaña", "Tipo de Incidencia", "Archivo DLT",
            "Responsable de Turno", "Descripcion de Incidencia",
            "Archivo Grafico 1", "Archivo Grafico 2", "Archivo Grafico 3", "Archivo Grafico 4"
        ]

        if os.path.exists(file_name):
            df_incidents = pd.read_csv(file_name)
        else:
            df_incidents = pd.DataFrame(columns=columns)

        df_incidents = pd.concat([df_incidents, pd.DataFrame([new_incident])], ignore_index=True)
        df_incidents.to_csv(file_name, index=False)
        QMessageBox.information(self, "Información", "Entrada en Bitácora guardada correctamente.")
        self.load_incidents()
        self.clear_form()

    def edit_incident(self):
        campaign = self.selected_campaign.currentText()
        directory = f"./incidencias/{campaign}"
        file_name = f"{directory}/Incidencias_{campaign}.csv"

        if not os.path.exists(file_name):
            QMessageBox.critical(self, "Error", "No hay entradas para editar.")
            return

        df_incidents = pd.read_csv(file_name)
        df_incidents = df_incidents.sort_values(by="Fecha y Hora", ascending=False)

        incident_list = df_incidents["Fecha y Hora"] + " - " + df_incidents["Tipo de Incidencia"]

        item, ok = QInputDialog.getItem(
            self, "Editar Incidencia", "Seleccionar Incidencia para Editar:", incident_list.tolist(), 0, False
        )
        if not ok or not item:
            return

        selected_datetime = item.split(" - ")[0]
        incident_data = df_incidents[df_incidents["Fecha y Hora"] == selected_datetime].iloc[0]

        # Cargar datos en el formulario
        self.timestamp_value.setText(incident_data["Fecha y Hora"])
        self.incident_type.setCurrentText(incident_data["Tipo de Incidencia"])

        # Convertir Archivo DLT a cadena si es necesario
        dlt_value = incident_data["Archivo DLT"]
        if not isinstance(dlt_value, str):
            dlt_value = str(dlt_value)
        self.dlt_file.setText(dlt_value)

        self.responsible_person.setCurrentText(incident_data["Responsable de Turno"])
        self.incident_description.setText(incident_data["Descripcion de Incidencia"])
        self.graph_files = []
        self.graph_list.clear()
        for i in range(1, 5):
            graph_col = f"Archivo Grafico {i}"
            if graph_col in incident_data and pd.notna(incident_data[graph_col]):
                graph_path = incident_data[graph_col]
                graph_type = "Desconocido"  # Podrías almacenar el tipo si lo deseas
                self.graph_files.append((graph_type, graph_path))
                item_text = f"{graph_type}: {os.path.basename(graph_path)}"
                self.graph_list.addItem(item_text)

    def load_incidents(self):
        self.incident_list.clear()
        campaign = self.selected_campaign.currentText()
        file_name = f"./incidencias/{campaign}/Incidencias_{campaign}.csv"

        if os.path.exists(file_name):
            df_incidents = pd.read_csv(file_name)
            df_incidents = df_incidents.sort_values(by="Fecha y Hora", ascending=False)
            for _, row in df_incidents.iterrows():
                item_text = f"{row['Fecha y Hora']} - {row['Tipo de Incidencia']}\n{row['Descripcion de Incidencia']}"
                list_item = QListWidgetItem(item_text)
                self.incident_list.addItem(list_item)

    def clear_form(self):
        self.timestamp_value.setText(datetime.now().strftime("%Y-%m-%d %H:%M"))
        self.incident_type.setCurrentIndex(0)
        self.dlt_file.setText(self.last_dlt_file)  # Restablecer el último archivo DLT
        self.responsible_person.setCurrentIndex(0)
        self.incident_description.clear()
        self.graph_files = []
        self.graph_list.clear()

    def get_existing_campaigns(self):
        info_file = "./data/info_campaigns.csv"
        if not os.path.exists(info_file):
            return []
        df_info = pd.read_csv(info_file)
        return df_info["Nombre Corto"].tolist()

    def back(self):
        if callable(self.back_callback):
            self.back_callback()
        else:
            print("Error: back_callback no es callable")

if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    window = IncidentReport()
    window.show()
    sys.exit(app.exec())
