"""
Worker para renombrar documentos SUNAT (Paso 2)
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

from core_sunat.sunat_rename import SUNATRenameOrchestrator, validar_preflight_renombrado_sunat


class SunatRenameWorker(QThread):
    """Worker para renombrar documentos SUNAT en segundo plano"""
    
    # Señales
    progress_signal = Signal(int, int)  # (current, total)
    log_signal = Signal(str, str)  # (type, message)
    stats_signal = Signal(dict)  # estadísticas
    finished_signal = Signal(dict)  # stats
    error_signal = Signal(str)  # mensaje de error
    
    def __init__(self, folder_path: str):
        super().__init__()
        self.folder_path = folder_path
        self.orchestrator = None
        self.logger = Logger("SunatRename")
        self.preflight_report = None
    
    def run(self):
        """Ejecuta el proceso de renombrado"""
        try:
            self.logger.info("🚀 Iniciando renombrado SUNAT")
            self.log_signal.emit("info", "🚀 Iniciando renombrado SUNAT")
            self.logger.info(f"📂 Carpeta: {self.folder_path}")
            self.log_signal.emit("info", f"📂 Carpeta: {self.folder_path}")
            
            # Validar carpeta
            if not os.path.isdir(self.folder_path):
                error_msg = f"La carpeta no existe: {self.folder_path}"
                self.logger.error(error_msg)
                self.error_signal.emit(error_msg)
                return
            
            self.log_signal.emit("info", "🔎 Ejecutando validación previa del renombrado SUNAT...")
            self.logger.info("🔎 Ejecutando validación previa del renombrado SUNAT...")
            self.preflight_report = validar_preflight_renombrado_sunat(self.folder_path)
            
            if not self.preflight_report.get('preflight_ok'):
                self._handle_preflight_failure(self.preflight_report)
                return
            
            json_path = self.preflight_report.get('selected_json_path')
            msg = f"✅ JSON validado: {os.path.basename(json_path)}"
            self.logger.info(msg)
            self.log_signal.emit("success", msg)
            
            pdf_files = self.preflight_report.get('pdf_files', [])
            msg = f"✅ Encontrados {len(pdf_files)} archivos PDF"
            self.logger.info(msg)
            self.log_signal.emit("success", msg)
            
            # Crear orquestador con callbacks
            self.orchestrator = SUNATRenameOrchestratorWithCallbacks(
                self.folder_path,
                progress_callback=self._on_progress,
                log_callback=self._on_log,
                logger=self.logger
            )
            
            # Ejecutar proceso
            stats = self.orchestrator.run()
            
            if stats:
                self.logger.info("✅ Renombrado completado exitosamente")
                self.log_signal.emit("success", "✅ Renombrado completado exitosamente")
                self.finished_signal.emit({
                    'success': True,
                    'preflight_ok': True,
                    'preflight_report': self.preflight_report,
                    'stats': stats,
                })
            else:
                error_msg = "El proceso de renombrado no se completó correctamente"
                self.logger.error(error_msg)
                self.error_signal.emit(error_msg)
            
        except Exception as e:
            error_msg = f"Error durante el renombrado: {str(e)}"
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
    
    def _handle_preflight_failure(self, preflight_report: dict):
        """Bloquea el paso 2 si la carpeta SUNAT no está lista para renombrar."""
        status = preflight_report.get('status')
        message = preflight_report.get('message', "La carpeta no pasó la validación previa.")
        
        if status == 'missing_json':
            error_msg = (
                "Validación previa bloqueada.\n"
                "Falta el archivo JSON de renombrado en la carpeta seleccionada."
            )
        elif status == 'multiple_json':
            candidates = ", ".join(preflight_report.get('json_files_found', []))
            error_msg = (
                "Validación previa bloqueada.\n"
                "Se encontró más de un JSON de renombrado.\n"
                f"JSON detectados: {candidates}"
            )
        elif status == 'pdfs_missing_in_json':
            missing_files = preflight_report.get('missing_pdf_entries', [])
            visible_files = missing_files[:10]
            listed = "\n".join(f"• {name}" for name in visible_files)
            extra_count = max(0, len(missing_files) - len(visible_files))
            extra_text = f"\n... y {extra_count} archivo(s) más." if extra_count else ""
            error_msg = (
                "Validación previa bloqueada.\n"
                "El JSON no cubre todos los PDFs de la carpeta.\n"
                "Archivos faltantes en el JSON:\n"
                f"{listed}{extra_text}"
            )
        else:
            error_msg = f"Validación previa bloqueada.\n{message}"
        
        self.logger.error(error_msg.replace("\n", " | "))
        self.log_signal.emit("error", error_msg)
        self.stats_signal.emit({
            'preflight_ok': False,
            'status': status,
            'errors': 1,
            'preflight_report': preflight_report,
        })
        self.error_signal.emit(error_msg)
        self.finished_signal.emit({
            'success': False,
            'preflight_ok': False,
            'preflight_report': preflight_report,
            'stats': None,
        })


class SUNATRenameOrchestratorWithCallbacks(SUNATRenameOrchestrator):
    """Extensión del orquestador con callbacks para la UI"""
    
    def __init__(self, folder_path, progress_callback=None, log_callback=None, logger=None):
        super().__init__(folder_path)
        self.progress_callback = progress_callback
        self.log_callback = log_callback
        self.logger = logger if logger else Logger("RenameOrchestrator")
    
    def _locate_json(self):
        """Override para emitir logs"""
        if self.log_callback:
            self.log_callback("info", "🔍 Buscando archivo JSON...")
        self.logger.info("🔍 Buscando archivo JSON...")
        
        json_path = self.scanner.find_json_file(self.folder_path)
        
        if not json_path:
            if self.log_callback:
                self.log_callback("error", "❌ No se encontró JSON de renombrado")
            self.logger.error("❌ No se encontró JSON de renombrado")
            return None
        
        if self.log_callback:
            msg = f"✅ JSON: {os.path.basename(json_path)}"
            self.log_callback("success", msg)
            self.logger.info(msg)
        
        return json_path
    
    def _read_json_data(self, json_path):
        """Override para emitir logs"""
        if self.log_callback:
            self.log_callback("info", "📖 Leyendo datos del JSON...")
        self.logger.info("📖 Leyendo datos del JSON...")
        
        try:
            rename_data = self.reader.read_rename_json(json_path)
            if self.log_callback:
                msg = f"✅ {len(rename_data)} registros cargados"
                self.log_callback("success", msg)
                self.logger.info(msg)
            return rename_data
        except Exception as e:
            if self.log_callback:
                msg = f"❌ Error: {str(e)}"
                self.log_callback("error", msg)
                self.logger.error(msg)
            return None
    
    def _get_pdf_files(self):
        """Override para emitir logs"""
        if self.log_callback:
            self.log_callback("info", "📄 Escaneando PDFs...")
        self.logger.info("📄 Escaneando PDFs...")
        
        pdf_files = self.scanner.get_pdf_files(self.folder_path)
        
        if not pdf_files:
            if self.log_callback:
                self.log_callback("warning", "⚠️ No se encontraron PDFs")
            self.logger.warning("⚠️ No se encontraron PDFs")
            return None
        
        if self.log_callback:
            msg = f"✅ {len(pdf_files)} archivos encontrados"
            self.log_callback("success", msg)
            self.logger.info(msg)
        
        self.renamer.stats['total_files'] = len(pdf_files)
        return pdf_files
    
    def _execute_rename(self, pdf_files, rename_data):
        """Override para emitir progreso y logs"""
        if self.log_callback:
            self.log_callback("info", "📄 Iniciando renombrado...")
        self.logger.info("📄 Iniciando renombrado...")
        
        total = len(pdf_files)
        
        for idx, pdf_file in enumerate(pdf_files, 1):
            # Actualizar progreso
            if self.progress_callback:
                self.progress_callback(idx, total)
            
            # Verificar si está en JSON
            if pdf_file not in rename_data:
                if self.log_callback:
                    msg = f"⏭️ Omitido: {pdf_file}"
                    self.log_callback("warning", msg)
                    self.logger.warning(msg)
                self.renamer.stats['skipped'] += 1
                continue
            
            # Obtener nuevo nombre
            new_filename = rename_data[pdf_file]
            old_path = os.path.join(self.folder_path, pdf_file)
            
            # Ejecutar renombrado
            message, success = self.renamer.rename_file(old_path, new_filename)
            
            if self.log_callback:
                if success:
                    self.log_callback("success", message)
                    self.logger.info(message)
                else:
                    self.log_callback("error", message)
                    self.logger.error(message)
            
            if success:
                self.renamer.stats['renamed'] += 1
            else:
                self.renamer.stats['errors'] += 1
    
    def _print_summary(self, elapsed_time):
        """Override para emitir resumen"""
        if not self.log_callback:
            return
        
        stats = self.renamer.stats
        
        self.log_callback("info", "=" * 50)
        self.log_callback("info", "📊 RESUMEN DEL RENOMBRADO")
        self.log_callback("info", f"📄 Total PDFs: {stats['total_files']}")
        self.log_callback("success", f"✅ Renombrados: {stats['renamed']}")
        self.log_callback("warning", f"⏭️ Omitidos: {stats['skipped']}")
        self.log_callback("error", f"❌ Errores: {stats['errors']}")
        self.log_callback("info", f"⏱️ Tiempo: {elapsed_time:.2f}s")
        self.log_callback("info", "=" * 50)
        
        # Log al archivo
        self.logger.info("=" * 50)
        self.logger.info("📊 RESUMEN DEL RENOMBRADO")
        self.logger.info(f"📄 Total PDFs: {stats['total_files']}")
        self.logger.info(f"✅ Renombrados: {stats['renamed']}")
        self.logger.warning(f"⏭️ Omitidos: {stats['skipped']}")
        self.logger.error(f"❌ Errores: {stats['errors']}")
        self.logger.info(f"⏱️ Tiempo: {elapsed_time:.2f}s")
        self.logger.info("=" * 50)
    
    def run(self):
        """Override sin print statements"""
        import time
        self.start_time = time.time()
        
        # Localizar JSON
        json_path = self._locate_json()
        if not json_path:
            return None
        
        # Leer datos
        rename_data = self._read_json_data(json_path)
        if not rename_data:
            return None
        
        # Obtener PDFs
        pdf_files = self._get_pdf_files()
        if not pdf_files:
            return None
        
        # Ejecutar renombrado
        self._execute_rename(pdf_files, rename_data)
        
        # Resumen
        elapsed_time = time.time() - self.start_time
        self._print_summary(elapsed_time)
        
        return self.renamer.stats
