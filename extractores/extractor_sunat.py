import pdfplumber
import re


class PDFProcessor:
    """Clase base para el procesamiento de archivos PDF."""
    
    def extract_text_from_page(self, pdf_path, page_number=0):
        """Extrae el texto de una página específica del PDF."""
        try:
            with pdfplumber.open(pdf_path) as pdf:
                if len(pdf.pages) > page_number:
                    return pdf.pages[page_number].extract_text()
                else:
                    return None
        except Exception:
            return None


class SunatDocumentExtractor(PDFProcessor):
    """Extractor especializado para documentos SUNAT (ALTA/BAJA/MODIFICACIÓN)."""
    
    MODIFICACION_KEYWORDS = ['MODIFICACIÓN', 'MODIFICACION', 'ACTUALIZACIÓN', 'ACTUALIZACION']
    BAJA_KEYWORDS = ['FECHA DE BAJA:']  # Más específico para evitar falsos positivos
    ALTA_KEYWORDS = ['ALTA']

    def extract_document_info(self, pdf_path):
        """
        Extrae la información completa de un documento SUNAT.
        
        Returns:
            tuple: (document_number, name, doc_type, fecha)
        """
        text = self.extract_text_from_page(pdf_path, page_number=0)
        if not text:
            return None, None, None, None

        document_number = self._extract_document_number(text)
        name = self._extract_name(text)
        doc_type = self._detect_document_type(text)
        fecha = self._extract_date(text, doc_type)

        return document_number, name, doc_type, fecha

    def _extract_document_number(self, text):
        """Extrae el número de documento (DNI) del texto."""
        for line in text.split('\n'):
            if 'L.E / DNI' in line or 'CARNÉ EXT.' in line:
                parts = line.split('-')
                if len(parts) > 1:
                    return parts[1].strip().split()[0]
        return None

    def _extract_name(self, text):
        """Extrae el nombre completo del texto."""
        for line in text.split('\n'):
            if 'Apellidos y nombres:' in line:
                parts = line.split('Apellidos y nombres:')
                if len(parts) > 1:
                    return parts[1].strip()
        return None

    def _detect_document_type(self, text):
        """Detecta el tipo de documento (ALTA/BAJA/MODIFICACIÓN)."""
        text_upper = text.upper()
        
        # Primero verificar si es documento de MODIFICACIÓN (tratar como ALTA)
        if any(k in text_upper for k in self.MODIFICACION_KEYWORDS):
            return 'ALTA-SUNAT'
        
        # Luego verificar BAJA (con keyword más específico)
        if any(k in text_upper for k in self.BAJA_KEYWORDS):
            return 'BAJA-SUNAT'
        
        # Finalmente verificar ALTA explícito
        if any(k in text_upper for k in self.ALTA_KEYWORDS):
            return 'ALTA-SUNAT'
        
        # Por defecto, si no se identifica claramente, tratarlo como ALTA
        return 'ALTA-SUNAT'

    def _extract_date(self, text, doc_type):
        """Extrae la fecha relevante según el tipo de documento."""
        if doc_type == 'ALTA-SUNAT':
            # Buscar fecha de inicio en la tabla de periodos laborales
            match = re.search(
                r'Fecha de inicio\s+Fecha de fin\s+Motivo de baja\s+(\d{2}/\d{2}/\d{4})',
                text,
                re.DOTALL
            )
            if match:
                return match.group(1)
        elif doc_type == 'BAJA-SUNAT':
            match = re.search(r'Fecha de baja:\s*(\d{2}/\d{2}/\d{4})', text)
            if match:
                return match.group(1)
        return None