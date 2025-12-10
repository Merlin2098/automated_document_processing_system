"""
Worker para generar diagnóstico (Paso 3)
Ejecuta el proceso en segundo plano sin congelar la UI
"""
from PySide6.QtCore import QThread, Signal
from utils.logger import get_logger, log_start, log_end, log_exception
import os

logger = get_logger('workers.core_pipeline_step3')


class CorePipelineStep3Worker(QThread):
    """Worker para generar diagnóstico en segundo plano"""
    
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
        logger.info(f"Worker Step 3 creado - Carpeta: {folder_path}")
    
    def run(self):
        """Ejecuta el proceso de diagnóstico"""
        try:
            log_start(logger, "Generación de Diagnóstico (Step 3)", carpeta_base=self.folder_path)
            
            self.log_signal.emit("info", "🚀 Iniciando generación de diagnóstico")
            self.log_signal.emit("info", f"📂 Carpeta base: {self.folder_path}")
            
            # Validar carpeta
            if not os.path.isdir(self.folder_path):
                error_msg = f"La carpeta no existe: {self.folder_path}"
                logger.error(error_msg)
                self.error_signal.emit(error_msg)  # ← AÑADIDO
                return
            
            # ... resto del código de procesamiento ...
            
            resultado = self._generar_diagnostico()
            
            if not resultado['success']:
                error_msg = resultado.get('error', 'Error desconocido en diagnóstico')
                logger.error(error_msg)
                self.error_signal.emit(error_msg)  # ← AÑADIDO
                return
            
            self.finished_signal.emit(resultado)
            
        except Exception as e:
            log_exception(logger, e, "ejecución del worker Step 3")
            error_msg = f"Error durante la generación de diagnóstico: {str(e)}"
            self.log_signal.emit("error", f"❌ {error_msg}")
            self.error_signal.emit(error_msg)  # ← AÑADIDO
    
    def _generar_diagnostico(self):
        """Método auxiliar de ejemplo"""
        # Aquí iría la lógica real del Step 3
        return {'success': True}
    
    def stop(self):
        """Detiene el worker"""
        logger.info("Solicitando detención del worker Step 3")
        self._is_running = False