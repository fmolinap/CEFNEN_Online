# reporte_fin_de_campagna.py

from PySide6.QtWidgets import (
    QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout,
    QMessageBox, QTextEdit, QProgressBar, QComboBox
)
from PySide6.QtCore import Qt, QThread, Signal
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak
from reportlab.lib.units import inch
from reportlab.lib.utils import ImageReader
import pandas as pd
import os
import re
from datetime import datetime
import math
import utils  # Asegúrate de que utils.py esté en el mismo directorio o en el PYTHONPATH

def add_page_number(canvas, doc):
    """
    Dibuja el número de página en la parte inferior derecha de cada página.
    """
    page_num = canvas.getPageNumber()
    text = f"Página {page_num}"
    canvas.saveState()
    canvas.setFont('Helvetica', 9)
    canvas.setFillColor(colors.black)
    # Coordenadas para dibujar el texto (ajusta según tus necesidades)
    canvas.drawRightString(doc.pagesize[0] - inch, 0.75 * inch, text)
    canvas.restoreState()

class ReporteFinCampagnaWindow(QWidget):
    def __init__(self, back_callback=None, parent=None):
        super().__init__(parent)
        self.back_callback = back_callback
        self.setWindowTitle("Generar Reporte Fin de Campaña")
        # self.resize(600, 400)  # Comentado para permitir ajuste automático al tamaño de la ventana principal
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # Selección de campaña
        campaign_layout = QHBoxLayout()
        campaign_label = QLabel("Seleccionar Campaña:")
        self.campaign_combo = QComboBox()
        self.campaigns = utils.get_existing_campaigns()
        if self.campaigns:
            self.campaign_combo.addItems(self.campaigns)
            self.campaign_combo.setCurrentIndex(len(self.campaigns) - 1)
        else:
            self.campaign_combo.addItem("No hay campañas disponibles")
        campaign_layout.addWidget(campaign_label)
        campaign_layout.addWidget(self.campaign_combo)
        layout.addLayout(campaign_layout)

        # Botón para generar el reporte
        generate_button = QPushButton("Generar Reporte")
        generate_button.setStyleSheet("background-color: #4CAF50; color: white; font-size: 16px;")
        generate_button.clicked.connect(self.generate_report)
        layout.addWidget(generate_button)

        # Área de texto para mensajes
        self.message_area = QTextEdit()
        self.message_area.setReadOnly(True)
        layout.addWidget(self.message_area)

        # Barra de progreso
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)

        # Botón "Regresar"
        back_button = QPushButton("Regresar")
        back_button.setStyleSheet("background-color: #f44336; color: white;")
        back_button.clicked.connect(self.back)
        layout.addWidget(back_button)

    def generate_report(self):
        campaign_name = self.campaign_combo.currentText()
        if not campaign_name or campaign_name == "No hay campañas disponibles":
            QMessageBox.critical(self, "Error", "Por favor, selecciona una campaña válida.")
            return

        # Iniciar el hilo de generación de reporte
        self.thread = ReportGenerationThread(campaign_name)
        self.thread.progress.connect(self.update_progress)
        self.thread.message.connect(self.append_message)
        self.thread.finished.connect(self.report_finished)
        self.thread.error.connect(self.report_error)
        self.thread.start()

    def update_progress(self, value):
        self.progress_bar.setValue(value)

    def append_message(self, text):
        self.message_area.append(text)

    def report_finished(self, report_file):
        self.message_area.append(f"Reporte generado exitosamente: {report_file}")
        QMessageBox.information(self, "Éxito", f"Reporte generado exitosamente en {report_file}")
        self.progress_bar.setValue(100)
        self.thread = None  # Liberar el hilo

    def report_error(self, error_message):
        self.message_area.append(f"Error al generar el reporte: {error_message}")
        QMessageBox.critical(self, "Error", f"Ocurrió un error: {error_message}")
        self.progress_bar.setValue(0)
        self.thread = None  # Liberar el hilo

    def back(self):
        """
        Maneja la acción de regresar a la ventana anterior.
        """
        if callable(self.back_callback):
            self.back_callback()
        else:
            self.close()

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

    def generar_reporte_fin_campagna(self, nombre_corto):
        self.progress.emit(5)
        
        # Obtener la ruta absoluta al directorio actual
        base_dir = os.path.dirname(os.path.abspath(__file__))

        # Cargar información general de la campaña
        campaign_info = utils.get_campaign_info(nombre_corto)
        if not campaign_info:
            raise ValueError(f"No se encontró información para la campaña '{nombre_corto}'")

        # Formatear fechas y otros valores
        fecha_inicio = campaign_info.get('Fecha de Inicio', '')
        fecha_termino = campaign_info.get('Fecha de Termino', '')
        lugar = campaign_info.get('Lugar', '')
        num_detectores = campaign_info.get('Número de Detectores', '')
        dlt_path = campaign_info.get('DLT Path', '')
        root_path = campaign_info.get('ROOT Path', '')

        # Nuevos campos solicitados
        latitud = campaign_info.get('Latitud', '')
        longitud = campaign_info.get('Longitud', '')
        altura = campaign_info.get('Altitud', '')
        corte_rigidez = campaign_info.get('Corte de Rigidez Geomagnética', '')
        b_n = campaign_info.get('B_N', '')
        b_e = campaign_info.get('B_E', '')
        b_d = campaign_info.get('B_D', '')

        # Cálculo de |B| [nT]
        try:
            b_n_val = float(b_n)
            b_e_val = float(b_e)
            b_d_val = float(b_d)
            b_magnitude = math.sqrt(b_n_val**2 + b_e_val**2 + b_d_val**2)
            b_magnitude_str = f"{b_magnitude:.2f}"
        except (ValueError, TypeError):
            b_magnitude_str = "No disponible"

        # Generar enlace a Google Maps
        if latitud and longitud:
            google_maps_link = f"https://www.google.com/maps/search/?api=1&query={latitud},{longitud}"
            mapa_html = f'<a href="{google_maps_link}" color="blue">Ver ubicación en Google Maps</a>'
        else:
            mapa_html = 'No disponible'

        self.progress.emit(10)

        # Crear el directorio para los reportes si no existe
        report_dir = os.path.join(base_dir, "reportes_fin_de_campagna")
        os.makedirs(report_dir, exist_ok=True)
        report_file = os.path.join(report_dir, f"Reporte_Fin_Campagna_{nombre_corto}.pdf")

        # Crear el documento PDF
        doc = SimpleDocTemplate(report_file, pagesize=A4,
                                rightMargin=inch, leftMargin=inch,
                                topMargin=inch, bottomMargin=inch)
        elementos = []
        styles = getSampleStyleSheet()
        # Definición de estilos personalizados
        styles.add(ParagraphStyle(
            name='TituloPortada',
            fontSize=24,
            leading=28,
            alignment=TA_CENTER,
            spaceAfter=20,
            fontName='Helvetica-Bold'
        ))
        styles.add(ParagraphStyle(
            name='SubtituloPortada',
            fontSize=14,
            leading=18,
            alignment=TA_CENTER,
            spaceAfter=30,
            fontName='Helvetica-Bold'
        ))
        styles.add(ParagraphStyle(
            name='Capitulo',
            fontSize=16,
            leading=20,
            alignment=TA_LEFT,
            spaceAfter=12,
            fontName='Helvetica-Bold',
            textColor=colors.darkblue  # Color azul oscuro
        ))
        styles.add(ParagraphStyle(
            name='Subtitulo',
            fontSize=12,
            leading=14,
            alignment=TA_LEFT,
            spaceAfter=6,
            fontName='Helvetica-Bold',
            textColor=colors.maroon  # Rojo oscuro
        ))
        styles.add(ParagraphStyle(
            name='Texto',
            fontSize=10,
            leading=12,
            alignment=TA_LEFT,
            spaceAfter=10
        ))
        styles.add(ParagraphStyle(
            name='TablaTexto',
            fontSize=6,
            leading=8,
            alignment=TA_CENTER
        ))

        available_width = doc.width  # Ancho disponible para contenido

        # Portada
        # Logo en la portada
        logo_path = os.path.join(base_dir, "Logo_CEFNEN.png")
        if not os.path.exists(logo_path):
            raise FileNotFoundError(f"No se encontró el archivo de logo en {logo_path}")
        logo = Image(logo_path, width=4*inch, height=1*inch)  # Aumentar ancho y disminuir alto
        logo.hAlign = 'CENTER'
        elementos.append(logo)
        elementos.append(Spacer(1, 12))  # Espaciado
        elementos.append(Spacer(1, 12))
        elementos.append(Spacer(1, 12))
        elementos.append(Spacer(1, 12))
        # Título detallado del reporte
        titulo_reporte = f"Reporte de Fin de Campaña {nombre_corto},\ndesde {fecha_inicio} hasta {fecha_termino} desarrollada en {lugar}"
        elementos.append(Paragraph(titulo_reporte, styles['TituloPortada']))

        # Fecha de generación del reporte
        fecha_generacion = datetime.now().strftime("%d/%m/%Y %H:%M")
        elementos.append(Paragraph(f"Fecha de Generación: {fecha_generacion}", styles['SubtituloPortada']))

        elementos.append(PageBreak())  # Salto de página después de la portada

        self.progress.emit(15)

        # Capítulo 1: Información General de la Campaña
        elementos.append(Paragraph("Capítulo 1: Información General de la Campaña", styles['Capitulo']))
        info_general = f"""
        <b>Fecha de Inicio:</b> {fecha_inicio}<br/>
        <b>Fecha de Término:</b> {fecha_termino}<br/>
        <b>Lugar:</b> {lugar}<br/>
        <b>Número de Detectores:</b> {num_detectores}<br/>
        <b>DLT Path:</b> {dlt_path}<br/>
        <b>ROOT Path:</b> {root_path}<br/>
        <b>Latitud Geográfica [º]:</b> {latitud}<br/>
        <b>Longitud Geográfica [º]:</b> {longitud}<br/>
        <b>Altura [msnm]:</b> {altura}<br/>
        <b>Corte Vertical de Rigidez Geomagnética [GV]:</b> {corte_rigidez}<br/>
        <b>B_N [nT]:</b> {b_n}<br/>
        <b>B_E [nT]:</b> {b_e}<br/>
        <b>B_D [nT]:</b> {b_d}<br/>
        <b>|B| [nT]:</b> {b_magnitude_str}<br/>
        <b>Mapa:</b> {mapa_html}
        """
        elementos.append(Paragraph(info_general, styles['Texto']))
        elementos.append(PageBreak())  # Salto de página después del capítulo

        self.progress.emit(25)

        # Capítulo 2: LookUpTable y Distribución de Detectores
        elementos.append(Paragraph("Capítulo 2: LookUpTable y Distribución de Detectores", styles['Capitulo']))

        # Definir el diccionario de mapeo de columnas
        column_mapping = {
            "Contador Proporcional (Numero/tipo/diametro/largo/marca)": "Contador",
            "Preamplificador (Numero/modelo)": "Preamp",
            "Alto Voltaje (Modulo/Canal)": "HV",
            "Digitalizador (Modelo/Canal)": "Digitalizador",
            "Moderador (Geometria/Material/diametro-lado)": "Moderador",
            "Set Cables (numero o detalle)": "Set Cables"
        }

        # Agregar la LookUpTable
        lookuptable_dir = os.path.join(base_dir, "lookuptable", nombre_corto)
        lookuptable_file = None
        if os.path.exists(lookuptable_dir):
            archivos = sorted([f for f in os.listdir(lookuptable_dir) if f.startswith("LookUpTable") and f.endswith(".csv")])
            if archivos:
                lookuptable_file = os.path.join(lookuptable_dir, archivos[0])
                df_lookuptable = pd.read_csv(lookuptable_file)

                # Añadir columna 'Detector' identificando cada fila
                df_lookuptable.insert(0, 'Detector', range(1, len(df_lookuptable) + 1))

                # Renombrar las columnas según el diccionario de mapeo
                df_lookuptable.rename(columns=column_mapping, inplace=True)

                # Reordenar las columnas según la sugerencia
                column_order = ['Detector', 'Contador', 'Preamp', 'HV', 'Digitalizador', 'Moderador', 'Set Cables']
                # Asegurarse de que todas las columnas en column_order existan en el DataFrame
                column_order = [col for col in column_order if col in df_lookuptable.columns]
                df_lookuptable = df_lookuptable[column_order]

                data = [df_lookuptable.columns.tolist()] + df_lookuptable.values.tolist()

                # Calcular el ancho de cada columna proporcionalmente
                num_cols = len(data[0])
                col_width = available_width / num_cols
                col_widths = [col_width] * num_cols

                # Crear la tabla con tamaños ajustados y fuente de 6pt
                tabla = Table(data, colWidths=col_widths, repeatRows=1)
                tabla.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 6),  # Fuente ajustada a 6pt
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 4),
                    ('GRID', (0, 0), (-1, -1), 0.25, colors.black),
                ]))
                elementos.append(tabla)
            else:
                elementos.append(Paragraph("No se encontró ningún archivo LookUpTable.", styles['Texto']))
        else:
            elementos.append(Paragraph("No se encontró el directorio de LookUpTable.", styles['Texto']))

        self.progress.emit(35)

        # Agregar la imagen de distribución de detectores
        distribucion_dir = os.path.join(base_dir, "Graficos", "Lookuptable", nombre_corto)
        distribucion_file = None
        if os.path.exists(distribucion_dir):
            imagenes = sorted([f for f in os.listdir(distribucion_dir) if f.startswith("Distribucion") and f.endswith(".png")])
            if imagenes:
                distribucion_file = os.path.join(distribucion_dir, imagenes[0])

                # Escalar la imagen al ancho disponible manteniendo la relación de aspecto
                img = ImageReader(distribucion_file)
                original_width, original_height = img.getSize()
                aspect = original_height / original_width
                scaled_width = available_width
                scaled_height = scaled_width * aspect

                imagen = Image(distribucion_file, width=scaled_width, height=scaled_height)
                imagen.hAlign = 'CENTER'
                elementos.append(Spacer(1, 12))
                elementos.append(Paragraph("Distribución de Detectores:", styles['Subtitulo']))
                elementos.append(Spacer(1, 12))
                elementos.append(imagen)
            else:
                elementos.append(Paragraph("No se encontró ninguna imagen de distribución de detectores.", styles['Texto']))
        else:
            elementos.append(Paragraph("No se encontró el directorio de distribución de detectores.", styles['Texto']))

        elementos.append(PageBreak())  # Salto de página después del capítulo

        self.progress.emit(45)

        # Capítulo 3: Incidencias
        elementos.append(Paragraph("Capítulo 3: Incidencias", styles['Capitulo']))

        incidencias_dir = os.path.join(base_dir, "incidencias", nombre_corto)
        incidencias_file = os.path.join(incidencias_dir, f"Incidencias_{nombre_corto}.csv")

        if os.path.exists(incidencias_file):
            df_incidencias = pd.read_csv(incidencias_file)
            df_incidencias.sort_values(by=['Fecha y Hora'], inplace=True)

            for idx, row in df_incidencias.iterrows():
                fecha = row.get('Fecha y Hora', 'Fecha no disponible')
                tipo = row.get('Tipo de Incidencia', 'Tipo no disponible')
                titulo_incidencia = f"- {fecha}: {tipo}"
                elementos.append(Paragraph(titulo_incidencia, styles['Subtitulo']))

                # Obtener la descripción, responsable de turno y archivo DLT
                descripcion_incidencia = row.get('Descripción de Incidencia') or row.get('Descripcion de Incidencia') or 'Descripción no disponible'
                responsable_turno = row.get('Responsable de Turno') or row.get('Responsable') or 'Desconocido'
                archivo_dlt = row.get('Archivo DLT', 'No disponible')

                descripcion = f"{descripcion_incidencia}<br/><b>Responsable de Turno:</b> {responsable_turno}<br/><b>Archivo DLT:</b> {archivo_dlt}"
                elementos.append(Paragraph(descripcion, styles['Texto']))

                # Agregar gráficos si existen
                for i in range(1, 50):
                    archivo_grafico = row.get(f'Archivo Grafico {i}')
                    if pd.notna(archivo_grafico) and os.path.exists(archivo_grafico):
                        # Escalar la imagen al ancho disponible manteniendo la relación de aspecto
                        img = ImageReader(archivo_grafico)
                        original_width, original_height = img.getSize()
                        aspect = original_height / original_width
                        scaled_width = available_width
                        scaled_height = scaled_width * aspect

                        imagen = Image(archivo_grafico, width=scaled_width, height=scaled_height)
                        imagen.hAlign = 'CENTER'
                        elementos.append(imagen)
                        elementos.append(Spacer(1, 6))  # Espaciado reducido

                # Agregar un espacio después de cada incidencia en lugar de un salto de página
                elementos.append(Spacer(1, 12))  # Doble salto de línea
        else:
            elementos.append(Paragraph("No se encontró el archivo de incidencias.", styles['Texto']))

        elementos.append(PageBreak())  # Salto de página después del capítulo

        self.progress.emit(55)

        # Capítulo 4: Reportes de Ruido
        elementos.append(Paragraph("Capítulo 4: Reportes de Ruido", styles['Capitulo']))

        noise_reports_dir = os.path.join(base_dir, "reports", "noise")
        if os.path.exists(noise_reports_dir):
            noise_report_files = [f for f in os.listdir(noise_reports_dir) if f.endswith('.txt') and nombre_corto in f]
            if noise_report_files:
                # Ordenar los archivos por fecha de modificación
                noise_report_files.sort(key=lambda f: os.path.getmtime(os.path.join(noise_reports_dir, f)), reverse=True)
                latest_noise_file = noise_report_files[0]
                reporte_titulo = f"- Reporte: {latest_noise_file}"
                elementos.append(Paragraph(reporte_titulo, styles['Subtitulo']))
                with open(os.path.join(noise_reports_dir, latest_noise_file), 'r', encoding='utf-8') as f:
                    contenido_reporte = f.read()
                elementos.append(Paragraph(contenido_reporte.replace('\n', '<br/>'), styles['Texto']))
            else:
                elementos.append(Paragraph("No se encontraron reportes de ruido.", styles['Texto']))
        else:
            elementos.append(Paragraph("No se encontró el directorio de reportes de ruido.", styles['Texto']))

        elementos.append(PageBreak())  # Salto de página después del capítulo

        self.progress.emit(65)

        # Capítulo 5: Calibraciones
        elementos.append(Paragraph("Capítulo 5: Calibraciones", styles['Capitulo']))

        calibration_dir = os.path.join(base_dir, "calibration", nombre_corto)
        if os.path.exists(calibration_dir):
            calibration_files = [f for f in os.listdir(calibration_dir) if f.endswith('.csv')]
            if calibration_files:
                # Ordenar los archivos por fecha de modificación
                calibration_files.sort(key=lambda f: os.path.getmtime(os.path.join(calibration_dir, f)), reverse=True)
                
                for calibration_file_name in calibration_files:
                    calibration_file = os.path.join(calibration_dir, calibration_file_name)
                    df_calibration = pd.read_csv(calibration_file)
                    data = [df_calibration.columns.tolist()] + df_calibration.values.tolist()

                    # Calcular el ancho de cada columna proporcionalmente
                    num_cols = len(data[0])
                    col_width = available_width / num_cols
                    col_widths = [col_width] * num_cols

                    # Crear la tabla con tamaños ajustados y fuente de 6pt
                    tabla_calibracion = Table(data, colWidths=col_widths, repeatRows=1)
                    tabla_calibracion.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('FONTSIZE', (0, 0), (-1, -1), 6),  # Fuente ajustada a 6pt
                        ('BOTTOMPADDING', (0, 0), (-1, 0), 4),
                        ('GRID', (0, 0), (-1, -1), 0.25, colors.black),
                    ]))
                    elementos.append(Paragraph(f"Archivo de Calibración: {os.path.basename(calibration_file)}", styles['Subtitulo']))
                    elementos.append(tabla_calibracion)
                    elementos.append(Spacer(1,12))  # Espacio entre tablas
            else:
                elementos.append(Paragraph("No se encontraron archivos de calibración.", styles['Texto']))
        else:
            elementos.append(Paragraph("No se encontró el directorio de calibraciones.", styles['Texto']))

        self.progress.emit(75)

        # Capítulo 6: Análisis Estadístico Descriptivo
        elementos.append(Paragraph("Capítulo 6: Análisis Estadístico Descriptivo", styles['Capitulo']))

        # Subcapítulo 6.1: Neutron Counting Rates
        elementos.append(Paragraph("6.1 Neutron Counting Rates", styles['Subtitulo']))
        aed_counting_rates_file = os.path.join(base_dir, "Reportes", "Analisis_Estadistico_Descriptivo", nombre_corto, "AED_counting_rates.txt")
        if os.path.exists(aed_counting_rates_file):
            with open(aed_counting_rates_file, 'r', encoding='utf-8') as f:
                aed_content = f.read()
            elementos.append(Paragraph(aed_content.replace('\n', '<br/>'), styles['Texto']))
        else:
            elementos.append(Paragraph("No se encontró el archivo de Neutron Counting Rates.", styles['Texto']))

        # Subcapítulo 6.2: Distribución de Counting rates por detector
        elementos.append(Paragraph("6.2 Distribución de Counting Rates por Detector", styles['Subtitulo']))
        histogram_image_path = os.path.join(base_dir, "Graficos", "AnalisisEstadisticoDescriptivo", nombre_corto, "Histogramas", f"Histogramas_CR_{nombre_corto}.png")
        if os.path.exists(histogram_image_path):
            # Escalar la imagen al ancho disponible manteniendo la relación de aspecto
            img = ImageReader(histogram_image_path)
            original_width, original_height = img.getSize()
            aspect = original_height / original_width
            scaled_width = available_width
            scaled_height = scaled_width * aspect

            imagen = Image(histogram_image_path, width=scaled_width, height=scaled_height)
            imagen.hAlign = 'CENTER'
            elementos.append(imagen)
        else:
            elementos.append(Paragraph("No se encontró la imagen de Distribución de Counting Rates.", styles['Texto']))

        # Subcapítulo 6.3: Boxplots de Counting Rates de Campaña
        elementos.append(Paragraph("6.3 Boxplots de Counting Rates de Campaña", styles['Subtitulo']))
        boxplot_image_path = os.path.join(base_dir, "Graficos", "AnalisisEstadisticoDescriptivo", nombre_corto, "Boxplots", f"BoxPlot_CR_{nombre_corto}.png")
        if os.path.exists(boxplot_image_path):
            # Escalar la imagen al ancho disponible manteniendo la relación de aspecto
            img = ImageReader(boxplot_image_path)
            original_width, original_height = img.getSize()
            aspect = original_height / original_width
            scaled_width = available_width
            scaled_height = scaled_width * aspect

            imagen = Image(boxplot_image_path, width=scaled_width, height=scaled_height)
            imagen.hAlign = 'CENTER'
            elementos.append(imagen)
        else:
            elementos.append(Paragraph("No se encontró la imagen de Boxplots de Counting Rates.", styles['Texto']))

        # Subcapítulo 6.4: Reporte de Outliers
        elementos.append(Paragraph("6.4 Reporte de Outliers", styles['Subtitulo']))
        outliers_report_file = os.path.join(base_dir, "Reportes", "Outliers", nombre_corto, "Analysis_outliers.txt")
        if os.path.exists(outliers_report_file):
            with open(outliers_report_file, 'r', encoding='utf-8') as f:
                outliers_content = f.read()
            elementos.append(Paragraph(outliers_content.replace('\n', '<br/>'), styles['Texto']))
        else:
            elementos.append(Paragraph("No se encontró el reporte de outliers.", styles['Texto']))

        elementos.append(PageBreak())

        self.progress.emit(80)

        # Capítulo 7: Gráficos de Adquisición GASIFIC
        elementos.append(Paragraph("Capítulo 7: Gráficos de Adquisición GASIFIC", styles['Capitulo']))

        canvas_dir = os.path.join(base_dir, "Graficos", "Canvas", nombre_corto)
        if os.path.exists(canvas_dir):
            canvas_images = [f for f in os.listdir(canvas_dir) if f.startswith('Canvas_') and f.endswith('.png')]
            if canvas_images:
                canvas_files_by_type = {}
                for filename in canvas_images:
                    # Ajuste de expresión regular para coincidir con el formato 'Canvas_{hist_type}_{timestamp}.png'
                    match = re.match(r'Canvas_(.+?)_(\d{8}_\d{4}).png', filename)
                    if match:
                        hist_type = match.group(1)
                        timestamp_str = match.group(2)
                        # Convertir el timestamp a datetime para comparación
                        timestamp_dt = datetime.strptime(timestamp_str, '%Y%m%d_%H%M')
                        # Si el hist_type no está en el diccionario o el timestamp es más reciente, actualizar
                        if hist_type not in canvas_files_by_type or canvas_files_by_type[hist_type][1] < timestamp_dt:
                            canvas_files_by_type[hist_type] = (filename, timestamp_dt)
                # Incluir el último archivo para cada hist_type
                for hist_type, (filename, _) in canvas_files_by_type.items():
                    image_path = os.path.join(canvas_dir, filename)
                    # Escalar la imagen al ancho disponible manteniendo la relación de aspecto
                    img = ImageReader(image_path)
                    original_width, original_height = img.getSize()
                    aspect = original_height / original_width
                    scaled_width = available_width
                    scaled_height = scaled_width * aspect

                    imagen = Image(image_path, width=scaled_width, height=scaled_height)
                    imagen.hAlign = 'CENTER'
                    elementos.append(Paragraph(f"Histograma Tipo: {hist_type}", styles['Subtitulo']))
                    elementos.append(imagen)
                    elementos.append(Spacer(1, 12))
            else:
                elementos.append(Paragraph("No se encontraron imágenes en la carpeta de Gráficos de Adquisición GASIFIC.", styles['Texto']))
        else:
            elementos.append(Paragraph("No se encontró el directorio de Gráficos de Adquisición GASIFIC.", styles['Texto']))

        elementos.append(PageBreak())

        self.progress.emit(85)

        # Capítulo 8: Variables Locales
        elementos.append(Paragraph("Capítulo 8: Variables Locales", styles['Capitulo']))

        variables_dir = os.path.join(base_dir, "Graficos", "EstacionMeteorologica", nombre_corto)
        if os.path.exists(variables_dir):
            variable_images = [f for f in os.listdir(variables_dir) if f.endswith('.png')]
            if variable_images:
                variable_files_by_type = {}
                for filename in variable_images:
                    var_type = os.path.splitext(filename)[0]  # Obtener el nombre sin extensión como tipo de variable
                    image_path = os.path.join(variables_dir, filename)
                    # Obtener la fecha de modificación del archivo
                    timestamp_dt = datetime.fromtimestamp(os.path.getmtime(image_path))
                    # Si el var_type no está en el diccionario o el timestamp es más reciente, actualizar
                    if var_type not in variable_files_by_type or variable_files_by_type[var_type][1] < timestamp_dt:
                        variable_files_by_type[var_type] = (filename, timestamp_dt)
                # Incluir el último archivo para cada var_type
                for var_type, (filename, _) in variable_files_by_type.items():
                    image_path = os.path.join(variables_dir, filename)
                    # Escalar la imagen al ancho disponible manteniendo la relación de aspecto
                    img = ImageReader(image_path)
                    original_width, original_height = img.getSize()
                    aspect = original_height / original_width
                    scaled_width = available_width
                    scaled_height = scaled_width * aspect

                    imagen = Image(image_path, width=scaled_width, height=scaled_height)
                    imagen.hAlign = 'CENTER'
                    elementos.append(Paragraph(f"Variable: {var_type}", styles['Subtitulo']))
                    elementos.append(imagen)
                    elementos.append(Spacer(1, 12))
            else:
                elementos.append(Paragraph("No se encontraron imágenes en la carpeta de Variables Locales.", styles['Texto']))
        else:
            elementos.append(Paragraph("No se encontró el directorio de Variables Locales.", styles['Texto']))

        elementos.append(PageBreak())

        self.progress.emit(95)

        # Construir el PDF con numeración de páginas
        doc.build(elementos, onFirstPage=add_page_number, onLaterPages=add_page_number)
        self.progress.emit(100)

        return report_file

if __name__ == "__main__":
    import sys
    from PySide6.QtWidgets import QApplication
    app = QApplication(sys.argv)
    window = ReporteFinCampagnaWindow()
    window.show()
    sys.exit(app.exec())
