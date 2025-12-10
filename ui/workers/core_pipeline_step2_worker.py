"""
Worker para mover/clasificar PDFs (Paso 2)
Ejecuta el proceso en segundo plano sin congelar la UI
"""
from PySide6.QtCore import QThread, Signal
from utils.logger import get_logger, log_start, log_end, log_exception
import os
import sys

logger = get_logger('workers.core_pipeline_step2')


class CorePipelineStep2Worker(QThread):
    """Worker para clasificar PDFs en segundo plano"""
    
    # Señales
    progress_signal = Signal(int, int)  # (current, total)
    log_signal = Signal(str, str)  # (type, message)
    stats_signal = Signal(dict)  # estadísticas
    finished_signal = Signal(dict)  # resultado final
    error_signal = Signal(str)  # ← AÑADIDO: mensaje de error
    
    def __init__(self, folder_path: str):
        super().__init__()
        self.folder_path = folder_path
        self._is_running = True
        logger.info(f"Worker Step 2 creado - Carpeta: {folder_path}")
    
    def run(self):
        """Ejecuta el proceso de clasificación"""
        try:
            log_start(logger, "Clasificación de PDFs (Step 2)", carpeta_base=self.folder_path)
            
            self.log_signal.emit("info", "🚀 Iniciando clasificación de PDFs")
            self.log_signal.emit("info", f"📂 Carpeta base: {self.folder_path}")
            
            # Validar carpeta
            if not os.path.isdir(self.folder_path):
                error_msg = f"La carpeta no existe: {self.folder_path}"
                logger.error(error_msg)
                self.error_signal.emit(error_msg)  # ← AÑADIDO
                return
            
            # ... resto del código de procesamiento ...
            
            # EJEMPLO: Si hay un error crítico durante el proceso
            resultado = self._procesar_archivos()
            
            if not resultado['success']:
                error_msg = resultado.get('error', 'Error desconocido en clasificación')
                logger.error(error_msg)
                self.error_signal.emit(error_msg)  # ← AÑADIDO
                return
            
            self.finished_signal.emit(resultado)
            
        except Exception as e:
            log_exception(logger, e, "ejecución del worker Step 2")
            error_msg = f"Error durante la clasificación: {str(e)}"
            self.log_signal.emit("error", f"❌ {error_msg}")
            self.error_signal.emit(error_msg)  # ← AÑADIDO
    
    def _procesar_archivos(self):
        """Método auxiliar de ejemplo"""
        # Aquí iría la lógica real del Step 2
        return {'success': True}
    
    def stop(self):
        """Detiene el worker"""
        logger.info("Solicitando detención del worker Step 2")
        self._is_running = False