# CEFNEN_Online_v1

Este es el programa de análisis online de las campañas experimentales de **CEFNEN** (Centro de Estudios y Formación en Nuevas Energías Nucleares). Ha sido desarrollado en Julio de 2024 para facilitar el análisis online de los datos de la 5ta Campaña experimental.

## Descripción

La aplicación está diseñada para ayudar a investigadores y técnicos en el análisis y calibración de datos de detectores nucleares. Proporciona herramientas para:

- **Visualizar y comparar datos de campañas experimentales**: Permite generar gráficos de la evolución temporal de los recuentos de los detectores y comparar diferentes campañas.
- **Realizar análisis de ruido**: Proporciona herramientas para analizar el ruido en los detectores y generar reportes.
- **Calibrar y recalibrar detectores**: Ofrece funciones para calibrar y recalibrar los detectores utilizando archivos de datos y archivos ROOT.
- **Gestionar campañas experimentales**: Permite al usuario crear nuevas campañas, agregar datos, configurar tablas de búsqueda y editar materiales.
- **Generar reportes de incidencias**: Facilita el registro y seguimiento de incidencias durante las campañas.

## Características

- Interfaz gráfica moderna y fácil de usar gracias a **PySide6**.
- Integración con **ROOT** para el manejo de archivos de datos y histogramas.
- Generación de gráficos interactivos utilizando **Matplotlib**.
- Estructura modular y código limpio para facilitar el mantenimiento y la extensión.

## Requisitos del Sistema

- **Python 3.7** o superior.
- **Sistemas operativos compatibles**: Windows, macOS, Linux.

### Bibliotecas Python necesarias:

- PySide6
- pandas
- matplotlib
- numpy
- PIL (Pillow)
- ROOT (para funciones relacionadas con archivos ROOT)
- datetime

Puedes instalarlas usando `pip`:

bash
pip install PySide6 pandas matplotlib numpy pillow

Para ROOT, debes instalarlo siguiendo las instrucciones en root.cern.

### Instalacion


  1.	Clonar el repositorio o descargar los archivos del programa:

  'git clone https://github.com/tu_usuario/CEFNEN_Online_v1.git'


  2.	Instalar las dependencias utilizando pip:

   'pip install -r requirements.txt'

  Nota: Asegúrate de tener ROOT instalado y configurado en tu sistema para que funcione correctamente con Python.

  3.	Configurar el entorno si es necesario. Asegúrate de que los archivos de datos y las carpetas necesarias estén en las ubicaciones correctas.

### Uso

Ejecuta el archivo main.py para iniciar la aplicación:

   'python main.py'

### Funcionalidades Principales

## Campañas

	•	Crear Nueva Campaña: Permite crear una nueva campaña experimental.
	•	Agregar Datos a Campaña en Curso: Agrega nuevos datos a una campaña existente.
	•	Traer archivos ROOT desde PC Adquisición: Facilita la transferencia de archivos ROOT desde el equipo de adquisición.
	•	Traer archivos DLT desde PC Adquisición: Facilita la transferencia de archivos DLT.
	•	Reporte de Incidencias: Registra incidencias ocurridas durante la campaña.
	•	LookUpTable Setup: Configura las tablas de búsqueda para la campaña.
	•	Editar Materiales en Campaña: Permite editar los materiales asociados a la campaña.

## Gráficos

	•	Plot Neutron Counting Rates: Genera gráficos de la tasa de conteo de neutrones.
	•	Plot Campaigns Comparison: Compara gráficamente diferentes campañas.

## Calibraciones

	•	Calibrate: Realiza la calibración de los detectores.
	•	Calibrar desde ROOT: Permite calibrar utilizando archivos ROOT.
	•	Recalibrar desde ROOT: Recalibra los detectores basándose en archivos ROOT.

## Análisis

	•	Online Noise Analysis: Analiza el ruido en los detectores en línea.

## Estructura del Proyecto

	•	main.py: Archivo principal de la aplicación.
	•	utils.py: Funciones utilitarias para manejar campañas y detectores.
	•	plot_cr_evo.py: Módulo para gráficos de evolución temporal.
	•	plot_comparison.py: Módulo para comparación gráfica entre campañas.
	•	noise_analysis.py: Módulo para análisis de ruido online.
	•	calibrate.py: Módulo para calibración de detectores.
	•	recalibrate.py: Módulo para recalibración de detectores.
	•	recalibrate_root.py: Módulo para recalibración utilizando ROOT.
	•	fetch_root_files.py: Módulo para transferir archivos ROOT.
	•	fetch_dlt_files.py: Módulo para transferir archivos DLT.
	•	lookuptable_setup.py: Módulo para configurar tablas de búsqueda.
	•	edit_materials.py: Módulo para editar materiales en campaña.
	•	incident_report.py: Módulo para reportar incidencias.
	•	data/: Carpeta que contiene los archivos de datos de las campañas.
	•	calibration/: Carpeta para almacenar los archivos de calibración.
	•	Graficos/: Carpeta donde se guardarán los gráficos generados.
	•	reports/: Carpeta para los reportes generados.
	•	Logo_CEFNEN.png: Logo utilizado en la interfaz.

## Contribuciones

Si deseas contribuir a este proyecto, por favor sigue los pasos:

	1.	Haz un fork del repositorio.
	2.	Crea una rama con tu nueva funcionalidad (git checkout -b nueva-funcionalidad).
	3.	Haz commit de tus cambios (git commit -am 'Agrega nueva funcionalidad').
	4.	Haz push a la rama (git push origin nueva-funcionalidad).
	5.	Abre un Pull Request.

## Licencia

Este proyecto está bajo la Licencia MIT.

## Contacto

Para consultas o soporte, puedes contactarnos en francisco.molina@cchen.cl.


Nota: Asegúrate de reemplazar https://github.com/tu_usuario/CEFNEN_Online_v1.git con la URL real de tu repositorio. También actualiza el correo electrónico de contacto y cualquier otra información específica de tu proyecto.

Además, es recomendable crear un archivo requirements.txt con las dependencias necesarias. Puedes generar este archivo utilizando:


 'pip freeze > requirements.txt'

Esto facilitará a otros usuarios instalar las dependencias correctas para ejecutar tu proyecto.

Francisco Molina P. CCHEN-CEFNEN 2024
