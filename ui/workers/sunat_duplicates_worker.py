"""
Worker para limpiar duplicados SUNAT (Paso 3)
Ejecuta el proceso en segundo plano sin congelar la UI
"""
from PySide6.QtCore import QThread, Signal
from utils.logger import Logger
import os
import sys

# Agregar rutas para imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(os.path.dirname(current_dir))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from core_sunat.sunat_duplicados import (
    SUNATDuplicateOrchestrator,
    DuplicateAnalyzer,
    DuplicateCleaner
)


class SunatDuplicatesWorker(QThread):
    """Worker para limpiar duplicados SUNAT en segundo plano"""
    
    # Señales
    progress_signal = Signal(int, int)  # (current, total)
    log_signal = Signal(str, str)  # (type, message)
    stats_signal = Signal(dict)  # estadísticas
    finished_signal = Signal(int, int, int, int)  # (total, duplicados, eliminados, errores)
    error_signal = Signal(str)  # mensaje de error
    
    def __init__(self, folder_path: str):
        super().__init__()
        self.folder_path = folder_path
        self.orchestrator = None
        self.logger = Logger("SunatDuplicates")
    
    def run(self):
        """Ejecuta el proceso de limpieza de duplicados"""
        try:
            self.logger.info("🚀 Iniciando limpieza de duplicados")
            self.log_signal.emit("info", "🚀 Iniciando limpieza de duplicados")
            self.logger.info(f"📂 Carpeta: {self.folder_path}")
            self.log_signal.emit("info", f"📂 Carpeta: {self.folder_path}")
            
            # Validar carpeta
            if not os.path.isdir(self.folder_path):
                error_msg = f"La carpeta no existe: {self.folder_path}"
                self.logger.error(error_msg)
                self.error_signal.emit(error_msg)
                return
            
            # Verificar archivos PDF
            pdf_files = [f for f in os.listdir(self.folder_path) if f.lower().endswith('.pdf')]
            if not pdf_files:
                error_msg = "No se encontraron archivos PDF en la carpeta"
                self.logger.error(error_msg)
                self.error_signal.emit(error_msg)
                return
            
            msg = f"✅ Encontrados {len(pdf_files)} archivos PDF"
            self.logger.info(msg)
            self.log_signal.emit("success", msg)
            
            # Crear orquestador con callbacks
            self.orchestrator = SUNATDuplicateOrchestratorWithCallbacks(
                self.folder_path,
                progress_callback=self._on_progress,
                log_callback=self._on_log,
                logger=self.logger
            )
            
            # Ejecutar proceso
            total, duplicados, eliminados, errores = self.orchestrator.run()
            
            # Emitir resultado
            if eliminados > 0 or duplicados == 0:
                self.logger.info("✅ Limpieza completada exitosamente")
                self.log_signal.emit("success", "✅ Limpieza completada exitosamente")
            else:
                self.logger.warning("⚠️ No se eliminaron archivos")
                self.log_signal.emit("warning", "⚠️ No se eliminaron archivos")
            
            self.finished_signal.emit(total, duplicados, eliminados, errores)
            
        except Exception as e:
            error_msg = f"Error durante la limpieza: {str(e)}"
            self.logger.error(error_msg)
            self.log_signal.emit("error", error_msg)
            import traceback
            self.logger.error(traceback.format_exc())
            self.error_signal.emit(error_msg)
    
    def _on_progress(self, current: int, total: int):
        """Callback para actualizar progreso"""
        self.progress_signal.emit(current, total)
    
    def _on_log(self, log_type: str, message: str):
        """Callback para logs"""
        self.log_signal.emit(log_type, message)


class SunatDuplicatesPreviewWorker(QThread):
    """Worker solo para análisis previo sin eliminar"""
    
    # Señales
    preview_ready = Signal(dict, int)  # (duplicados_dict, total_archivos)
    log_signal = Signal(str, str)  # (type, message)
    error_signal = Signal(str)  # mensaje de error
    
    def __init__(self, folder_path: str):
        super().__init__()
        self.folder_path = folder_path
        self.logger = Logger("SunatDuplicatesPreview")
    
    def run(self):
        """Ejecuta solo el análisis sin eliminar"""
        try:
            self.logger.info("🔍 Analizando duplicados...")
            self.log_signal.emit("info", "🔍 Analizando duplicados...")
            
            # Validar carpeta
            if not os.path.isdir(self.folder_path):
                error_msg = f"La carpeta no existe: {self.folder_path}"
                self.logger.error(error_msg)
                self.error_signal.emit(error_msg)
                return
            
            # Crear analizador
            analyzer = DuplicateAnalyzer(self.folder_path)
            duplicados = analyzer.detectar_duplicados()
            total_archivos = analyzer.total_archivos
            
            if not duplicados:
                msg = "✅ No se encontraron duplicados"
                self.logger.info(msg)
                self.log_signal.emit("success", msg)
            else:
                total_duplicados = sum(len(files) - 1 for files in duplicados.values())
                msg = (f"📊 Encontrados {len(duplicados)} contratos con duplicados "
                       f"({total_duplicados} archivos a eliminar)")
                self.logger.info(msg)
                self.log_signal.emit("info", msg)
            
            self.preview_ready.emit(duplicados, total_archivos)
            
        except Exception as e:
            error_msg = f"Error al analizar duplicados: {str(e)}"
            self.logger.error(error_msg)
            self.log_signal.emit("error", error_msg)
            import traceback
            self.logger.error(traceback.format_exc())
            self.error_signal.emit(error_msg)


class SUNATDuplicateOrchestratorWithCallbacks(SUNATDuplicateOrchestrator):
    """Extensión del orquestador con callbacks para la UI"""
    
    def __init__(self, folder_path, progress_callback=None, log_callback=None, logger=None):
        super().__init__(folder_path)
        self.progress_callback = progress_callback
        self.log_callback = log_callback
        self.logger = logger if logger else Logger("SUNATOrchestrator")
        
        # Reemplazar cleaner con versión con callbacks
        self.cleaner = DuplicateCleanerWithCallbacks(
            folder_path,
            progress_callback=progress_callback,
            log_callback=log_callback,
            logger=self.logger
        )
    
    def run(self):
        """Override sin prints, solo callbacks"""
        import time
        self.start_time = time.time()
        
        if self.log_callback:
            self.log_callback("info", "🔍 Detectando duplicados...")
        self.logger.info("🔍 Detectando duplicados...")
        
        # Detectar duplicados
        duplicados = self.analyzer.detectar_duplicados()
        total_inicial = self.analyzer.total_archivos
        
        if not duplicados:
            if self.log_callback:
                self.log_callback("success", "✅ No se encontraron duplicados")
            self.logger.info("✅ No se encontraron duplicados")
            return total_inicial, 0, 0, 0
        
        if self.log_callback:
            total_dup = sum(len(files) - 1 for files in duplicados.values())
            msg = f"📋 {len(duplicados)} contratos con duplicados ({total_dup} a eliminar)"
            self.log_callback("info", msg)
            self.logger.info(msg)
        
        # Eliminar duplicados
        eliminados, errores = self.cleaner.eliminar_duplicados(duplicados)
        
        # Resumen final
        elapsed_time = time.time() - self.start_time
        if self.log_callback:
            self._emit_summary(total_inicial, len(duplicados), eliminados, errores, elapsed_time)
        
        return total_inicial, len(duplicados), eliminados, errores
    
    def _emit_summary(self, total_inicial, duplicados_count, eliminados, errores, elapsed_time):
        """Emite resumen de resultados"""
        total_final = total_inicial - eliminados
        
        self.log_callback("info", "=" * 50)
        self.log_callback("info", "📋 RESUMEN DE LIMPIEZA")
        self.log_callback("info", f"📂 Archivos iniciales: {total_inicial}")
        self.log_callback("info", f"🔍 Contratos duplicados: {duplicados_count}")
        self.log_callback("success", f"✅ Archivos eliminados: {eliminados}")
        self.log_callback("error", f"❌ Errores: {errores}")
        self.log_callback("info", f"📄 Archivos finales: {total_final}")
        self.log_callback("info", f"⏱️ Tiempo: {elapsed_time:.2f}s")
        self.log_callback("info", "=" * 50)
        
        # Log al archivo
        self.logger.info("=" * 50)
        self.logger.info("📋 RESUMEN DE LIMPIEZA")
        self.logger.info(f"📂 Archivos iniciales: {total_inicial}")
        self.logger.info(f"🔍 Contratos duplicados: {duplicados_count}")
        self.logger.info(f"✅ Archivos eliminados: {eliminados}")
        self.logger.error(f"❌ Errores: {errores}")
        self.logger.info(f"📄 Archivos finales: {total_final}")
        self.logger.info(f"⏱️ Tiempo: {elapsed_time:.2f}s")
        self.logger.info("=" * 50)


class DuplicateCleanerWithCallbacks(DuplicateCleaner):
    """Extensión del limpiador con callbacks"""
    
    def __init__(self, folder_path, progress_callback=None, log_callback=None, logger=None):
        super().__init__(folder_path)
        self.progress_callback = progress_callback
        self.log_callback = log_callback
        self.logger = logger if logger else Logger("DuplicateCleaner")
    
    def eliminar_duplicados(self, duplicados):
        """Override para emitir progreso y logs"""
        if self.log_callback:
            self.log_callback("info", "🗑️ Eliminando duplicados...")
        self.logger.info("🗑️ Eliminando duplicados...")
        
        total_contratos = len(duplicados)
        current_contrato = 0
        
        for contrato, archivos in duplicados.items():
            current_contrato += 1
            
            # Actualizar progreso
            if self.progress_callback:
                self.progress_callback(current_contrato, total_contratos)
            
            if self.log_callback:
                msg = f"📋 Contrato {contrato}: {len(archivos)} archivos"
                self.log_callback("info", msg)
                self.logger.info(msg)
            
            # Mantener primero, eliminar resto
            archivos_a_eliminar = archivos[1:]
            
            for archivo in archivos_a_eliminar:
                resultado = self._eliminar_archivo(archivo)
                
                if resultado:
                    self.eliminados += 1
                    if self.log_callback:
                        msg = f"   ✓ Eliminado: {archivo}"
                        self.log_callback("success", msg)
                        self.logger.info(msg)
                else:
                    self.errores += 1
                    if self.log_callback:
                        msg = f"   ✗ Error: {archivo}"
                        self.log_callback("error", msg)
                        self.logger.error(msg)
        
        return self.eliminados, self.errores