"""
PDF Splitter Worker - WRAPPER PATTERN
Usa directamente las funciones del módulo core sin reimplementar lógica
"""
from PySide6.QtCore import QThread, Signal
from utils.logger import Logger
import os
import sys
from datetime import datetime

# Agregar rutas para imports del core
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(os.path.dirname(current_dir))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Importar funciones PURAS del core (sin dependencias de UI)
from core_tools.dividir_pdf import (
    validar_division,
    dividir_pdf
)


class PdfSplitterWorker(QThread):
    """Worker wrapper para dividir PDFs"""
    
    # Señales
    log_message = Signal(str, str)  # (tipo, mensaje)
    progress_updated = Signal(int, int)  # (current, total)
    finished = Signal(dict)  # resultado final
    error = Signal(str)  # mensaje de error
    
    def __init__(self, pdf_path: str, pages_per_file: int):
        super().__init__()
        self.pdf_path = pdf_path
        self.pages_per_file = pages_per_file
        self._is_running = True
        self.logger = Logger("PdfSplitterWorker")
    
    def run(self):
        """Ejecuta el proceso usando funciones del core"""
        start_time = datetime.now()
        
        try:
            self.logger.info("🚀 Iniciando división de PDF")
            self.log_message.emit("info", "🚀 Iniciando división de PDF")
            self.logger.info(f"📂 Archivo: {os.path.basename(self.pdf_path)}")
            self.log_message.emit("info", f"📂 Archivo: {os.path.basename(self.pdf_path)}")
            
            # Validar que el archivo existe
            if not os.path.exists(self.pdf_path):
                error_msg = f"El archivo no existe: {self.pdf_path}"
                self.logger.error(error_msg)
                self.error.emit(error_msg)
                return
            
            # Verificar PyPDF2
            try:
                from PyPDF2 import PdfReader, PdfWriter
            except ImportError:
                error_msg = "PyPDF2 no está instalado. Instale con: pip install PyPDF2"
                self.logger.error(error_msg)
                self.error.emit(error_msg)
                return
            
            # ============================================================
            # FASE 1: Validar división (USA EL CORE)
            # ============================================================
            self.log_message.emit("info", "")
            self.log_message.emit("info", "📋 Validando división de PDF...")
            self.logger.info("📋 Validando división de PDF...")
            
            # Llamar a la función del core con manejo de prints
            num_pdfs_to_generate = validar_division(self.pdf_path, self.pages_per_file)
            
            if num_pdfs_to_generate is None:
                # La validación falló - el core ya logueo el error
                error_msg = (
                    f"Validación fallida: El PDF no es divisible exactamente por {self.pages_per_file} páginas. "
                    f"Verifique que el total de páginas sea múltiplo de {self.pages_per_file}."
                )
                self.logger.error(error_msg)
                self.error.emit(error_msg)
                return
            
            msg = f"✅ Se generarán {num_pdfs_to_generate} archivos PDF"
            self.logger.info(msg)
            self.log_message.emit("success", msg)
            
            # ============================================================
            # FASE 2: Dividir PDF (USA EL CORE)
            # ============================================================
            if not self._is_running:
                self.logger.warning("Proceso cancelado por el usuario")
                return
            
            self.log_message.emit("info", "")
            self.log_message.emit("info", "📋 Dividiendo PDF...")
            self.logger.info("📋 Dividiendo PDF...")
            
            # Crear callback para el progreso
            def progress_callback(current, total):
                """Callback que el core llamará para reportar progreso"""
                if self._is_running:
                    self.progress_updated.emit(current, total)
                    
                    # Log cada 10 archivos
                    if current % 10 == 0:
                        msg = f"   Progreso: {current}/{total}"
                        self.log_message.emit("info", msg)
            
            # Llamar a la función del core
            resultado = dividir_pdf(
                self.pdf_path,
                self.pages_per_file,
                num_pdfs_to_generate,
                progress_callback=progress_callback
            )
            
            # Verificar resultado
            if not resultado['success']:
                error_msg = resultado.get('error_message', 'Error desconocido durante la división')
                self.logger.error(error_msg)
                self.error.emit(error_msg)
                return
            
            # ============================================================
            # FASE 3: Resultado final
            # ============================================================
            elapsed_time = (datetime.now() - start_time).total_seconds()
            
            # Añadir tiempo al resultado
            resultado['tiempo_transcurrido'] = elapsed_time
            
            self.log_message.emit("info", "")
            self.log_message.emit("info", "=" * 50)
            self.log_message.emit("success", "🎉 ¡Proceso completado exitosamente!")
            self.log_message.emit("info", f"📊 Archivos generados: {resultado['pdfs_generados']}")
            
            if resultado.get('errores', 0) > 0:
                self.log_message.emit("warning", f"⚠️ Errores: {resultado['errores']}")
            
            self.log_message.emit("info", f"📂 Ubicación: {os.path.basename(resultado['carpeta_salida'])}")
            self.log_message.emit("info", f"⏱️ Tiempo: {elapsed_time:.2f}s")
            self.log_message.emit("info", "=" * 50)
            
            # Log a archivo
            self.logger.info("=" * 50)
            self.logger.info("🎉 ¡Proceso completado exitosamente!")
            self.logger.info(f"📊 Archivos generados: {resultado['pdfs_generados']}")
            
            if resultado.get('errores', 0) > 0:
                self.logger.warning(f"⚠️ Errores: {resultado['errores']}")
            
            self.logger.info(f"📂 Ubicación: {resultado['carpeta_salida']}")
            self.logger.info(f"⏱️ Tiempo: {elapsed_time:.2f}s")
            self.logger.info("=" * 50)
            
            # Emitir resultado final
            self.finished.emit(resultado)
            
        except Exception as e:
            error_msg = f"Error durante el procesamiento: {str(e)}"
            self.logger.error(error_msg)
            self.log_message.emit("error", f"❌ {error_msg}")
            import traceback
            self.logger.error(traceback.format_exc())
            self.error.emit(error_msg)
    
    def stop(self):
        """Detiene el worker"""
        self._is_running = False
        self.logger.warning("ℹ️ Worker detenido por el usuario")