"""
Worker para unir PDFs finales por contrato (Paso 5) - WRAPPER PATTERN
Usa directamente las funciones del módulo core sin reimplementar lógica

Este worker actúa como un puente entre la UI (PySide6) y el módulo core,
proporcionando señales para actualizar la interfaz sin duplicar código.

VERSION 1.1: Progreso detallado por pack generado
"""
from PySide6.QtCore import QThread, Signal
from utils.logger import Logger
import os
import sys
import time

# Agregar rutas para imports del core
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(os.path.dirname(current_dir))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Importar funciones PURAS del core (sin dependencias de UI)
from core_pipeline.step5_unir_final import (
    validar_y_detectar_subcarpetas,
    copiar_pdfs_a_procesamiento,
    generar_diagnostico,
    guardar_diagnostico,
    generar_packs_documentales,
    generar_timestamp
)


class CorePipelineStep5Worker(QThread):
    """Worker wrapper que usa el módulo core para fusión por contratos"""
    
    # Señales
    progress_signal = Signal(int, int)  # (current, total) - Ahora reporta packs generados
    log_signal = Signal(str, str)  # (type, message)
    stats_signal = Signal(dict)  # estadísticas
    finished_signal = Signal(dict)  # resultado final
    error_signal = Signal(str)  # mensaje de error
    
    def __init__(self, folder_path: str):
        super().__init__()
        self.folder_path = folder_path
        self._is_running = True
        self.logger = Logger("CorePipelineStep5Worker")
    
    def _emit_pack_progress(self, current: int, total: int):
        """
        Callback interno para emitir progreso de generación de packs.
        
        Args:
            current: Pack actual siendo generado
            total: Total de packs a generar
        """
        self.progress_signal.emit(current, total)
        self.log_signal.emit("info", f"   📦 Generando pack {current}/{total}...")
    
    def run(self):
        """Ejecuta el proceso usando funciones del core"""
        start_time = time.time()
        
        try:
            self.logger.info("🚀 Iniciando proceso de fusión por contratos")
            self.log_signal.emit("info", "🚀 Iniciando proceso de fusión por contratos")
            self.logger.info(f"📂 Carpeta madre: {self.folder_path}")
            self.log_signal.emit("info", f"📂 Carpeta madre: {self.folder_path}")
            
            # Validar carpeta madre
            if not os.path.isdir(self.folder_path):
                error_msg = f"La carpeta no existe: {self.folder_path}"
                self.logger.error(error_msg)
                self.error_signal.emit(error_msg)
                return
            
            # Verificar PyPDF2
            try:
                from PyPDF2 import PdfMerger
            except ImportError:
                error_msg = "PyPDF2 no está instalado. Instale con: pip install PyPDF2"
                self.logger.error(error_msg)
                self.error_signal.emit(error_msg)
                return
            
            # Generar timestamp único
            timestamp = generar_timestamp()
            self.logger.info(f"Timestamp: {timestamp}")
            
            # ============================================================
            # FASE 1: Validar subcarpetas (USA EL CORE)
            # ============================================================
            self.log_signal.emit("info", "")
            self.log_signal.emit("info", "📋 [1/4] Validando estructura...")
            self.logger.info("📋 [1/4] Validando estructura...")
            
            encontradas, faltantes = validar_y_detectar_subcarpetas(self.folder_path)
            
            if not encontradas:
                error_msg = "No se encontró ninguna de las 5 subcarpetas esperadas"
                self.logger.error(error_msg)
                self.error_signal.emit(error_msg)
                return
            
            self.log_signal.emit("success", f"✅ Subcarpetas encontradas: {len(encontradas)}")
            self.logger.info(f"✅ Subcarpetas encontradas: {', '.join(encontradas)}")
            
            if faltantes:
                msg = f"⚠️ Subcarpetas faltantes: {', '.join(faltantes)}"
                self.log_signal.emit("warning", msg)
                self.logger.warning(msg)
            
            # ============================================================
            # FASE 2: Copiar PDFs a carpeta temporal (USA EL CORE)
            # ============================================================
            if not self._is_running:
                self.logger.warning("Proceso cancelado por el usuario")
                return
            
            self.log_signal.emit("info", "")
            self.log_signal.emit("info", "📋 [2/4] Copiando PDFs a carpeta temporal...")
            self.logger.info("📋 [2/4] Copiando PDFs a carpeta temporal...")
            
            ruta_procesar, copiados, errores_copia = copiar_pdfs_a_procesamiento(
                self.folder_path,
                encontradas,
                timestamp
            )
            
            if not ruta_procesar:
                error_msg = "Error al crear carpeta de procesamiento"
                self.logger.error(error_msg)
                self.error_signal.emit(error_msg)
                return
            
            self.log_signal.emit("success", f"✅ PDFs copiados: {copiados}")
            self.logger.info(f"✅ PDFs copiados: {copiados}")
            self.logger.info(f"Carpeta procesamiento: {os.path.basename(ruta_procesar)}")
            
            if errores_copia > 0:
                msg = f"⚠️ Errores durante copia: {errores_copia}"
                self.log_signal.emit("warning", msg)
                self.logger.warning(msg)
            
            # ============================================================
            # FASE 3: Generar diagnóstico de contratos (USA EL CORE)
            # ============================================================
            if not self._is_running:
                self.logger.warning("Proceso cancelado por el usuario")
                return
            
            self.log_signal.emit("info", "")
            self.log_signal.emit("info", "📋 [3/4] Analizando contratos...")
            self.logger.info("📋 [3/4] Analizando contratos...")
            
            diagnostico = generar_diagnostico(ruta_procesar, timestamp)
            
            if diagnostico['total_contratos_unicos'] == 0:
                error_msg = "No se encontraron contratos válidos para procesar"
                self.logger.error(error_msg)
                self.error_signal.emit(error_msg)
                return
            
            self.log_signal.emit("success", f"✅ Contratos únicos: {diagnostico['total_contratos_unicos']}")
            self.log_signal.emit("info", f"📄 Total archivos: {diagnostico['total_archivos']}")
            self.logger.info(f"✅ Contratos únicos: {diagnostico['total_contratos_unicos']}")
            self.logger.info(f"📄 Total archivos: {diagnostico['total_archivos']}")
            
            # Guardar diagnóstico (USA EL CORE)
            ruta_json = guardar_diagnostico(diagnostico, ruta_procesar, timestamp)
            if ruta_json:
                self.log_signal.emit("success", f"✅ Diagnóstico guardado: {os.path.basename(ruta_json)}")
            
            # ============================================================
            # FASE 4: Generar packs documentarios (USA EL CORE)
            # ============================================================
            if not self._is_running:
                self.logger.warning("Proceso cancelado por el usuario")
                return
            
            self.log_signal.emit("info", "")
            self.log_signal.emit("info", "📋 [4/4] Generando packs por contrato...")
            self.logger.info("📋 [4/4] Generando packs por contrato...")
            self.log_signal.emit("info", f"   Se generarán {diagnostico['total_contratos_unicos']} packs...")
            
            # Inicializar progreso en 0
            self.progress_signal.emit(0, diagnostico['total_contratos_unicos'])
            
            # Llamar a generar_packs_documentales CON callback de progreso
            ruta_enviar, packs_generados, errores_fusion = generar_packs_documentales(
                ruta_procesar,
                diagnostico,
                timestamp,
                progress_callback=self._emit_pack_progress  # ⭐ CALLBACK PARA PROGRESO
            )
            
            if not ruta_enviar:
                error_msg = "Error al generar packs documentarios"
                self.logger.error(error_msg)
                self.error_signal.emit(error_msg)
                return
            
            # ============================================================
            # FASE 5: Resumen final
            # ============================================================
            elapsed_time = time.time() - start_time
            
            self.log_signal.emit("info", "")
            self.log_signal.emit("info", "=" * 50)
            self.log_signal.emit("info", "📊 RESUMEN FINAL")
            self.log_signal.emit("success", f"✅ Packs generados: {packs_generados}")
            self.log_signal.emit("info", f"📂 Carpeta temporal: {os.path.basename(ruta_procesar)}")
            self.log_signal.emit("info", f"📦 Carpeta salida: {os.path.basename(ruta_enviar)}")
            
            if errores_fusion > 0:
                self.log_signal.emit("error", f"❌ Errores en fusión: {errores_fusion}")
                tasa_exito = (packs_generados / (packs_generados + errores_fusion)) * 100
                self.log_signal.emit("info", f"📊 Tasa de éxito: {tasa_exito:.1f}%")
            
            self.log_signal.emit("info", f"⏱️ Tiempo total: {elapsed_time:.2f}s")
            self.log_signal.emit("info", "=" * 50)
            
            # Log a archivo
            self.logger.info("=" * 50)
            self.logger.info("📊 RESUMEN FINAL")
            self.logger.info(f"✅ Contratos procesados: {diagnostico['total_contratos_unicos']}")
            self.logger.info(f"📄 Archivos fusionados: {diagnostico['total_archivos']}")
            self.logger.info(f"✅ Packs generados: {packs_generados}")
            if errores_fusion > 0:
                self.logger.error(f"❌ Errores: {errores_fusion}")
            self.logger.info(f"📂 Carpeta temporal: {ruta_procesar}")
            self.logger.info(f"📦 Carpeta salida: {ruta_enviar}")
            self.logger.info(f"⏱️ Tiempo total: {elapsed_time:.2f}s")
            self.logger.info("=" * 50)
            
            # Emitir estadísticas
            stats = {
                'contratos_unicos': diagnostico['total_contratos_unicos'],
                'archivos_procesados': diagnostico['total_archivos'],
                'packs_generados': packs_generados,
                'errores': errores_fusion,
                'carpeta_procesar': ruta_procesar,
                'carpeta_enviar': ruta_enviar,
                'time': elapsed_time
            }
            self.stats_signal.emit(stats)
            
            # Emitir resultado final
            resultado = {
                'success': True,
                'stats': stats,
                'diagnostico': diagnostico,
                'ruta_procesar': ruta_procesar,
                'ruta_enviar': ruta_enviar,
                'timestamp': timestamp
            }
            
            self.logger.info("🎉 ¡Proceso completado exitosamente!")
            self.log_signal.emit("success", "🎉 ¡Proceso completado exitosamente!")
            self.finished_signal.emit(resultado)
            
        except Exception as e:
            error_msg = f"Error durante el proceso: {str(e)}"
            self.logger.error(error_msg)
            self.log_signal.emit("error", f"❌ {error_msg}")
            import traceback
            self.logger.error(traceback.format_exc())
            self.error_signal.emit(error_msg)
    
    def stop(self):
        """Detiene el worker"""
        self._is_running = False
        self.logger.warning("ℹ️ Worker detenido por el usuario")