# architect.md

# Arquitectura Técnica de DocFlow

## Core Stack
- **Lenguaje:** Python.
- **UI:** PySide6 para la interfaz de escritorio.
- **Preferencia técnica:** usar librerías estándar cuando sea suficiente y evitar frameworks innecesarios.

## Extracción y reglas
- La extracción de datos y aplicación de **patrones regex** se realiza con:
  - **PyPDF2**
  - **pdfplumber**
  - **pdfminer.six**
  - **pypdfium2**

## Pipeline de procesamiento
Flujo principal del ETL documental:
1. **Cleaning**: validación de entradas y limpieza de archivos no válidos.
2. **Splitting**: división de PDFs por páginas o reglas de negocio.
3. **Renaming**: renombrado basado en **JSON** (mapeos generados previamente).
4. **Grouping**: agrupación y consolidación de documentos finales.

## Rendimiento
- Procesamiento en paralelo para manejar alto volumen.
- Uso de workers configurables según capacidad del equipo.

## Observabilidad
- Sistema de logging integrado.
- Reportes automáticos para auditoría y trazabilidad.

## Validación de integridad
- Conteo de archivos procesados vs. esperados.
- Verificación de resultados por etapa.
- Registro de errores y advertencias para diagnóstico rápido.

## Nota de confidencialidad
- Hay un procesamiento intermedio mediante **macros** para reglas de negocio.
- Dichas macros **no se incluyen** en el repositorio por confidencialidad.
