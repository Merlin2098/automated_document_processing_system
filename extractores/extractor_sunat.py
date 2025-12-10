"""
Extractor de datos para Documentos SUNAT
Extrae: nombre, DNI, tipo de documento (ALTA/BAJA) y fecha
"""

import re
import pdfplumber
from pathlib import Path
from typing import Dict, Optional


class PDFProcessor:
    """Clase base para el procesamiento de archivos PDF."""
    
    def __init__(self, logger=None):
        """
        Inicializa el procesador de PDF.
        
        Args:
            logger: Logger opcional para registro de eventos
        """
        self.logger = logger
    
    def extract_text_from_page(self, pdf_path: str, page_number: int = 0) -> Optional[str]:
        """
        Extrae el texto de una página específica del PDF.
        
        Args:
            pdf_path: Ruta completa del archivo PDF
            page_number: Número de página a extraer (default: 0)
            
        Returns:
            Texto extraído o None si hay error
        """
        try:
            with pdfplumber.open(pdf_path) as pdf:
                if len(pdf.pages) > page_number:
                    return pdf.pages[page_number].extract_text()
                else:
                    if self.logger:
                        self.logger.warning(f"⚠️ PDF no tiene página {page_number}")
                    return None
        except FileNotFoundError:
            if self.logger:
                self.logger.error(f"❌ Archivo no encontrado: {pdf_path}")
            return None
        except Exception as e:
            if self.logger:
                self.logger.error(f"❌ Error al extraer texto: {str(e)}")
            return None


class SunatDocumentExtractor(PDFProcessor):
    """Extractor especializado para documentos SUNAT (ALTA/BAJA/MODIFICACIÓN)."""
    
    MODIFICACION_KEYWORDS = ['MODIFICACIÓN', 'MODIFICACION', 'ACTUALIZACIÓN', 'ACTUALIZACION']
    BAJA_KEYWORDS = ['FECHA DE BAJA:']  # Más específico para evitar falsos positivos
    ALTA_KEYWORDS = ['ALTA']

    def extract_document_info(self, pdf_path: str) -> Dict:
        """
        Extrae la información completa de un documento SUNAT.
        
        Args:
            pdf_path: Ruta completa del archivo PDF
            
        Returns:
            Diccionario con: nombre, dni, tipo_doc, fecha, exito, observaciones
        """
        # Inicializar resultado base
        resultado = {
            "nombre": None,
            "dni": None,
            "tipo_doc": None,
            "fecha": None,
            "exito": False,
            "observaciones": ""
        }
        
        # Validar existencia del archivo
        ruta_path = Path(pdf_path)
        if not ruta_path.exists():
            resultado["observaciones"] = "Archivo no encontrado"
            if self.logger:
                self.logger.error(f"❌ SUNAT - Archivo no encontrado: {pdf_path}")
            return resultado
        
        if self.logger:
            self.logger.debug(f"🔍 Procesando SUNAT: {ruta_path.name}")
        
        # Extraer texto de la primera página
        text = self.extract_text_from_page(pdf_path, page_number=0)
        if not text:
            resultado["observaciones"] = "No se pudo extraer texto del PDF"
            if self.logger:
                self.logger.warning(f"⚠️ SUNAT - Sin texto extraíble: {ruta_path.name}")
            return resultado
        
        # Extraer datos
        document_number = self._extract_document_number(text)
        name = self._extract_name(text)
        doc_type = self._detect_document_type(text)
        fecha = self._extract_date(text, doc_type)
        
        # Asignar resultados
        resultado["dni"] = document_number
        resultado["nombre"] = name
        resultado["tipo_doc"] = doc_type
        resultado["fecha"] = fecha
        
        # Determinar éxito y observaciones
        if name and document_number:
            resultado["exito"] = True
            if fecha:
                resultado["observaciones"] = "OK"
            else:
                resultado["observaciones"] = "Fecha no encontrada"
        else:
            resultado["exito"] = False
            if not name and not document_number:
                resultado["observaciones"] = "No se encontró nombre ni DNI"
            elif not name:
                resultado["observaciones"] = "Nombre no encontrado"
            else:
                resultado["observaciones"] = "DNI no encontrado"
        
        # Logging según resultado
        if self.logger:
            if resultado["exito"]:
                self.logger.info(
                    f"✅ {doc_type} - Nombre: {name}, DNI: {document_number}, "
                    f"Fecha: {fecha if fecha else 'N/A'}"
                )
            else:
                self.logger.warning(
                    f"⚠️ SUNAT - Extracción incompleta: {resultado['observaciones']}"
                )
        
        return resultado

    def _extract_document_number(self, text: str) -> Optional[str]:
        """
        Extrae el número de documento (DNI) del texto.
        
        Args:
            text: Texto extraído del PDF
            
        Returns:
            DNI o None si no se encuentra
        """
        for line in text.split('\n'):
            if 'L.E / DNI' in line or 'CARNÉ EXT.' in line:
                parts = line.split('-')
                if len(parts) > 1:
                    dni = parts[1].strip().split()[0]
                    if self.logger:
                        self.logger.debug(f"📋 DNI encontrado: {dni}")
                    return dni
        return None

    def _extract_name(self, text: str) -> Optional[str]:
        """
        Extrae el nombre completo del texto.
        
        Args:
            text: Texto extraído del PDF
            
        Returns:
            Nombre completo o None si no se encuentra
        """
        for line in text.split('\n'):
            if 'Apellidos y nombres:' in line:
                parts = line.split('Apellidos y nombres:')
                if len(parts) > 1:
                    nombre = parts[1].strip()
                    if self.logger:
                        self.logger.debug(f"👤 Nombre encontrado: {nombre}")
                    return nombre
        return None

    def _detect_document_type(self, text: str) -> str:
        """
        Detecta el tipo de documento (ALTA/BAJA/MODIFICACIÓN).
        
        Args:
            text: Texto extraído del PDF
            
        Returns:
            Tipo de documento: 'ALTA-SUNAT' o 'BAJA-SUNAT'
        """
        text_upper = text.upper()
        
        # Primero verificar si es documento de MODIFICACIÓN (tratar como ALTA)
        if any(k in text_upper for k in self.MODIFICACION_KEYWORDS):
            if self.logger:
                self.logger.debug("📄 Tipo detectado: ALTA-SUNAT (Modificación)")
            return 'ALTA-SUNAT'
        
        # Luego verificar BAJA (con keyword más específico)
        if any(k in text_upper for k in self.BAJA_KEYWORDS):
            if self.logger:
                self.logger.debug("📄 Tipo detectado: BAJA-SUNAT")
            return 'BAJA-SUNAT'
        
        # Finalmente verificar ALTA explícito
        if any(k in text_upper for k in self.ALTA_KEYWORDS):
            if self.logger:
                self.logger.debug("📄 Tipo detectado: ALTA-SUNAT")
            return 'ALTA-SUNAT'
        
        # Por defecto, si no se identifica claramente, tratarlo como ALTA
        if self.logger:
            self.logger.debug("📄 Tipo detectado: ALTA-SUNAT (por defecto)")
        return 'ALTA-SUNAT'

    def _extract_date(self, text: str, doc_type: str) -> Optional[str]:
        """
        Extrae la fecha relevante según el tipo de documento.
        
        Args:
            text: Texto extraído del PDF
            doc_type: Tipo de documento detectado
            
        Returns:
            Fecha en formato dd/mm/yyyy o None si no se encuentra
        """
        if doc_type == 'ALTA-SUNAT':
            # Buscar fecha de inicio en la tabla de periodos laborales
            match = re.search(
                r'Fecha de inicio\s+Fecha de fin\s+Motivo de baja\s+(\d{2}/\d{2}/\d{4})',
                text,
                re.DOTALL
            )
            if match:
                fecha = match.group(1)
                if self.logger:
                    self.logger.debug(f"📅 Fecha de inicio encontrada: {fecha}")
                return fecha
        elif doc_type == 'BAJA-SUNAT':
            match = re.search(r'Fecha de baja:\s*(\d{2}/\d{2}/\d{4})', text)
            if match:
                fecha = match.group(1)
                if self.logger:
                    self.logger.debug(f"📅 Fecha de baja encontrada: {fecha}")
                return fecha
        
        if self.logger:
            self.logger.debug(f"⚠️ No se encontró fecha para tipo: {doc_type}")
        return None


# Función auxiliar para mantener compatibilidad con código existente
def extraer_datos_sunat(ruta_pdf: str, logger=None) -> Dict:
    """
    Función wrapper para mantener consistencia con otros extractores.
    
    Args:
        ruta_pdf: Ruta completa del archivo PDF
        logger: Logger opcional para registro de eventos
        
    Returns:
        Diccionario con: nombre, dni, tipo_doc, fecha, exito, observaciones
    """
    extractor = SunatDocumentExtractor(logger=logger)
    return extractor.extract_document_info(ruta_pdf)