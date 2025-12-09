"""
Worker para generar diagnóstico SUNAT (Paso 1)
Ejecuta el proceso en segundo plano sin congelar la UI
"""
from PySide6.QtCore import QThread, Signal
import os
import sys

# Agregar rutas para imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(os.path.dirname(current_dir))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from core_sunat.sunat import SUNATDiagnosticGenerator


class SunatDiagnosticWorker(QThread):
    """Worker para generar diagnóstico SUNAT en segundo plano"""
    
    # Señales
    progress_signal = Signal(int, int)  # (current, total)
    log_signal = Signal(str, str)  # (type, message)
    stats_signal = Signal(dict)  # estadísticas
    finished_signal = Signal(str, dict)  # (excel_path, stats)
    error_signal = Signal(str)  # mensaje de error
    
    def __init__(self, folder_path: str, max_workers: int = 4):
        super().__init__()
        self.folder_path = folder_path
        self.max_workers = max_workers
        self.generator = None
    
    def run(self):
        """Ejecuta el proceso de generación de diagnóstico"""
        try:
            self.log_signal.emit("info", f"🚀 Iniciando análisis SUNAT")
            self.log_signal.emit("info", f"📂 Carpeta: {self.folder_path}")
            self.log_signal.emit("info", f"⚡ Workers: {self.max_workers}")
            
            # Validar carpeta
            if not os.path.isdir(self.folder_path):
                self.error_signal.emit(f"La carpeta no existe: {self.folder_path}")
                return
            
            # Contar PDFs
            pdf_files = [f for f in os.listdir(self.folder_path) if f.lower().endswith('.pdf')]
            if not pdf_files:
                self.error_signal.emit("No se encontraron archivos PDF en la carpeta")
                return
            
            self.log_signal.emit("success", f"✅ Encontrados {len(pdf_files)} archivos PDF")
            
            # Crear generador con callback personalizado
            self.generator = SUNATDiagnosticGeneratorWithCallbacks(
                self.folder_path,
                self.max_workers,
                progress_callback=self._on_progress,
                log_callback=self._on_log
            )
            
            # Ejecutar proceso
            excel_path, stats = self.generator.run()
            
            # Emitir resultado exitoso
            self.log_signal.emit("success", f"✅ Diagnóstico completado")
            self.log_signal.emit("success", f"📄 Excel: {os.path.basename(excel_path)}")
            
            self.finished_signal.emit(excel_path, stats)
            
        except Exception as e:
            error_msg = f"Error durante el diagnóstico: {str(e)}"
            self.log_signal.emit("error", error_msg)
            self.error_signal.emit(error_msg)
    
    def _on_progress(self, current: int, total: int):
        """Callback para actualizar progreso"""
        self.progress_signal.emit(current, total)
    
    def _on_log(self, log_type: str, message: str):
        """Callback para logs"""
        self.log_signal.emit(log_type, message)


class SUNATDiagnosticGeneratorWithCallbacks(SUNATDiagnosticGenerator):
    """Extensión del generador original con callbacks para la UI"""
    
    def __init__(self, folder_path, max_workers=4, progress_callback=None, log_callback=None):
        super().__init__(folder_path, max_workers)
        self.progress_callback = progress_callback
        self.log_callback = log_callback
    
    def process_single_pdf(self, filename):
        """Override para emitir progreso"""
        result = super().process_single_pdf(filename)
        
        # Emitir progreso después de cada archivo
        if self.progress_callback:
            processed = self.stats['processed'] + self.stats['errors'] + self.stats['sin_datos']
            self.progress_callback(processed, self.stats['total_files'])
        
        # Emitir log del resultado
        if self.log_callback:
            if result['status'] == 'OK':
                self.log_callback("info", f"✓ {filename}")
            elif result['status'] == 'SIN_DATOS':
                self.log_callback("warning", f"⚠ {filename} - Sin datos")
            else:
                self.log_callback("error", f"✗ {filename} - Error")
        
        return result
    
    def run(self):
        """Override para emitir logs personalizados"""
        if self.log_callback:
            self.log_callback("info", "🔍 Escaneando documentos...")
        
        # Escanear y procesar
        self.scan_folder()
        
        if self.log_callback:
            self.log_callback("info", "📊 Generando Excel...")
        
        # Generar Excel
        excel_path = self.generate_diagnostic_excel()
        
        # Emitir resumen
        if self.log_callback:
            self._emit_summary()
        
        return excel_path, self.stats
    
    def _emit_summary(self):
        """Emite resumen de estadísticas"""
        self.log_callback("info", "=" * 50)
        self.log_callback("info", "📊 RESUMEN DEL DIAGNÓSTICO")
        self.log_callback("info", f"📄 Total archivos: {self.stats['total_files']}")
        self.log_callback("success", f"✅ Procesados: {self.stats['processed']}")
        self.log_callback("info", f"   • ALTA: {self.stats['alta']}")
        self.log_callback("info", f"   • BAJA: {self.stats['baja']}")
        self.log_callback("info", f"   • OTROS: {self.stats['otros']}")
        self.log_callback("warning", f"⚠️ Sin datos: {self.stats['sin_datos']}")
        self.log_callback("error", f"❌ Errores: {self.stats['errors']}")
        self.log_callback("info", "=" * 50)