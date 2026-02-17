# README.md

# DocFlow
DocFlow es una aplicación de escritorio en Python que elimina el trabajo manual en áreas administrativas, contables y de RR.HH. Automatiza la manipulación de PDFs (dividir, renombrar, organizar) con alto rendimiento y una interfaz moderna.

## Propuesta de valor
Reduce tiempos operativos, minimiza errores humanos y entrega resultados consistentes en procesos documentales masivos.

## Características clave
- Renombrado automático de documentos.
- División de PDFs por reglas predefinidas.
- Eliminación de duplicados.
- Procesamiento en paralelo para grandes volúmenes.

## Interfaz de usuario
- Modo **Profesional** (Light).
- Modo **DarkBlue** (Dark).

## Distribución
- Ejecutable standalone para Windows (`.exe`).
- No requiere instalación de Python en el equipo del usuario final.

## Validación y logging
- Registro de eventos y errores en logs para trazabilidad.
- Validación de conteos de archivos y consistencia de salidas.
- Reportes automáticos para control de calidad del procesamiento.

## Stack principal
- Python
- PySide6 (interfaz)
- PyPDF2, pdfplumber, pdfminer.six, pypdfium2 (extracción de datos y patrones regex)

## Nota sobre renombrado y macros
- El **renombrado** se realiza mediante **mapeos JSON** generados en etapas previas.
- Existe un procesamiento intermedio mediante **macros** para normalización y negocio, pero **no se incluye** en este repositorio por confidencialidad.
