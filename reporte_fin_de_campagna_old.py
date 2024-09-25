# reporte_fin_de_campagna.py

from PySide6.QtWidgets import (
    QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout,
    QMessageBox, QTextEdit, QProgressBar, QComboBox
)
from PySide6.QtCore import Qt, QThread, Signal
import os
import subprocess
from jinja2 import Environment, FileSystemLoader
from datetime import datetime
import pandas as pd
import utils  # Asegúrate de que utils.py esté en el mismo directorio o en el PYTHONPATH

class ReportGenerationThread(QThread):
    progress = Signal(int)
    message = Signal(str)
    finished = Signal(str)
    error = Signal(str)

    def __init__(self, campaign_name):
        super().__init__()
        self.campaign_name = campaign_name

    def run(self):
        try:
            report_path = self.generar_reporte_fin_campagna(self.campaign_name)
            self.finished.emit(report_path)
        except Exception as e:
            self.error.emit(str(e))

def get_campaign_data(nombre_corto):
    # Implementa esta función para obtener los datos necesarios
    base_dir = os.path.dirname(os.path.abspath(__file__))
    campaign_info = utils.get_campaign_info(nombre_corto)
    if not campaign_info:
        raise ValueError(f"No se encontró información para la campaña '{nombre_corto}'")

    # LookUpTable
    lookuptable_dir = os.path.join(base_dir, "lookuptable", nombre_corto)
    lookuptable_file = next((f for f in os.listdir(lookuptable_dir) if f.startswith("LookUpTable") and f.endswith(".csv")), None)
    if lookuptable_file:
        df_lookup = pd.read_csv(os.path.join(lookuptable_dir, lookuptable_file))
        lookup_columns = df_lookup.columns.tolist()
        lookup_data = df_lookup.values.tolist()
    else:
        lookup_columns = []
        lookup_data = []

    # Distribución de Detectores
    distribucion_dir = os.path.join(base_dir, "Graficos", "Lookuptable", nombre_corto)
    distribucion_file = next((f for f in os.listdir(distribucion_dir) if f.startswith("Distribucion") and f.endswith(".png")), None)
    distribution_image_path = os.path.join(distribucion_dir, distribucion_file) if distribucion_file else ''

    # Incidencias
    incidencias_file = os.path.join(base_dir, "incidencias", nombre_corto, f"Incidencias_{nombre_corto}.csv")
    if os.path.exists(incidencias_file):
        df_incidencias = pd.read_csv(incidencias_file)
        incidencias = []
        for idx, row in df_incidencias.iterrows():
            graficos = [row.get(f'Archivo Grafico {i}') for i in range(1, 6) if pd.notna(row.get(f'Archivo Grafico {i}')) and os.path.exists(row.get(f'Archivo Grafico {i}'))]
            incidencias.append({
                'fecha': row.get('Fecha y Hora', 'Fecha no disponible'),
                'tipo': row.get('Tipo de Incidencia', 'Tipo no disponible'),
                'descripcion': row.get('Descripción de Incidencia', 'Descripción no disponible'),
                'responsable': row.get('Responsable de Turno', 'Desconocido'),
                'graficos': graficos
            })
    else:
        incidencias = []

    # Reportes de Ruido
    noise_reports_dir = os.path.join(base_dir, "reports", "noise")
    noise_report_files = [f for f in os.listdir(noise_reports_dir) if f.endswith('.txt') and nombre_corto in f] if os.path.exists(noise_reports_dir) else []
    reportes_ruido = []
    for noise_file in noise_report_files:
        with open(os.path.join(noise_reports_dir, noise_file), 'r', encoding='utf-8') as f:
            contenido = f.read()
        reportes_ruido.append({
            'nombre': noise_file,
            'contenido': contenido
        })

    # Calibraciones
    calibration_dir = os.path.join(base_dir, "calibration", nombre_corto)
    calibration_files = [f for f in os.listdir(calibration_dir) if f.endswith('.csv')] if os.path.exists(calibration_dir) else []
    calibraciones = []
    for calib_file in calibration_files:
        df_calib = pd.read_csv(os.path.join(calibration_dir, calib_file))
        calibraciones.append({
            'nombre': calib_file,
            'columns': df_calib.columns.tolist(),
            'data': df_calib.values.tolist()
        })

    return {
        'campaign_name': nombre_corto,
        'generation_date': datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        'campaign_info': {
            'fecha_inicio': campaign_info.get('Fecha de Inicio', ''),
            'fecha_termino': campaign_info.get('Fecha de Termino', ''),
            'lugar': campaign_info.get('Lugar', ''),
            'num_detectores': campaign_info.get('Número de Detectores', ''),
            'dlt_path': campaign_info.get('DLT Path', ''),
            'root_path': campaign_info.get('ROOT Path', '')
        },
        'lookup_columns': lookup_columns,
        'lookup_data': lookup_data,
        'distribution_image_path': distribution_image_path,
        'incidencias': incidencias,
        'reportes_ruido': reportes_ruido,
        'calibraciones': calibraciones
    }

def generate_tex(data, output_tex_path):
    # Configurar el entorno de Jinja2
    env = Environment(loader=FileSystemLoader('.'))
    template = env.get_template('template.tex')

    # Renderizar la plantilla con los datos
    rendered_tex = template.render(data)

    # Escribir el archivo .tex
    with open(output_tex_path, 'w', encoding='utf-8') as f:
        f.write(rendered_tex)

def compile_tex_to_pdf(tex_path, output_dir):
    # Cambia al directorio donde está el .tex
    cwd = os.path.dirname(tex_path)
    command = ['pdflatex', '-interaction=nonstopmode', tex_path]
    subprocess.run(command, cwd=cwd, check=True)
    
    # Obtener el nombre del archivo PDF
    tex_filename = os.path.basename(tex_path)
    pdf_filename = tex_filename.replace('.tex', '.pdf')
    pdf_path = os.path.join(cwd, pdf_filename)
    return pdf_path

def generar_reporte_fin_campagna(nombre_corto):
    # Definir las rutas
    base_dir = os.path.dirname(os.path.abspath(__file__))
    report_dir = os.path.join(base_dir, "reportes_fin_de_campagna")
    os.makedirs(report_dir, exist_ok=True)
    
    # Obtener los datos de la campaña
    data = get_campaign_data(nombre_corto)
    
    # Definir la ruta del archivo .tex
    tex_filename = f"Reporte_Fin_Campagna_{nombre_corto}.tex"
    tex_path = os.path.join(report_dir, tex_filename)
    
    # Generar el archivo .tex
    generate_tex(data, tex_path)
    
    # Compilar el archivo .tex en .pdf
    pdf_path = compile_tex_to_pdf(tex_path, report_dir)
    
    # Opcional: Eliminar archivos auxiliares
    aux_extensions = ['.aux', '.log', '.out']
    for ext in aux_extensions:
        aux_file = tex_path.replace('.tex', ext)
        if os.path.exists(aux_file):
            os.remove(aux_file)
    
    return pdf_path

class ReportGenerationThread(QThread):
    progress = Signal(int)
    message = Signal(str)
    finished = Signal(str)
    error = Signal(str)

    def __init__(self, campaign_name):
        super().__init__()
        self.campaign_name = campaign_name

    def run(self):
        try:
            self.progress.emit(10)
            self.message.emit("Iniciando la generación del reporte...")

            report_path = generar_reporte_fin_campagna(self.campaign_name)
            self.progress.emit(100)
            self.message.emit("Reporte generado exitosamente.")
            self.finished.emit(report_path)
        except subprocess.CalledProcessError as e:
            self.error.emit(f"Error durante la compilación de LaTeX: {e}")
        except Exception as e:
            self.error.emit(str(e))
