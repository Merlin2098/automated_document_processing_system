"""
Worker para generar diagnóstico (Paso 3) - WRAPPER PATTERN
Usa directamente las funciones del módulo core sin reimplementar lógica
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
from core_pipeline.step3_generar_diagnostico import (
    procesar_carpeta,
    generar_excel_multihoja,
    CARPETAS_CONFIG
)


class CorePipelineStep3Worker(QThread):
    """Worker wrapper para generar diagnóstico Excel"""
    
    # Señales
    progress_signal = Signal(int, int)  # (current, total)
    log_signal = Signal(str, str)  # (type, message)
    stats_signal = Signal(dict)  # estadísticas
    finished_signal = Signal(dict)  # resultado final
    error_signal = Signal(str)  # mensaje de error
    
    def __init__(self, folder_path: str, guardar_json: bool = False):
        super().__init__()
        self.folder_path = folder_path
        self.guardar_json = guardar_json
        self._is_running = True
        self.logger = Logger("CorePipelineStep3Worker")
    
    def run(self):
        """Ejecuta el proceso usando funciones del core"""
        start_time = time.time()
        
        try:
            self.logger.info("🚀 Iniciando generación de diagnóstico")
            self.log_signal.emit("info", "🚀 Iniciando generación de diagnóstico")
            self.logger.info(f"📂 Carpeta de trabajo: {self.folder_path}")
            self.log_signal.emit("info", f"📂 Carpeta de trabajo: {self.folder_path}")
            
            # Validar carpeta
            if not os.path.isdir(self.folder_path):
                error_msg = f"La carpeta no existe: {self.folder_path}"
                self.logger.error(error_msg)
                self.error_signal.emit(error_msg)
                return
            
            # Verificar openpyxl
            try:
                import openpyxl
            except ImportError:
                error_msg = "openpyxl no está instalado. Instale con: pip install openpyxl"
                self.logger.error(error_msg)
                self.error_signal.emit(error_msg)
                return
            
            # Generar timestamp para el Excel
            timestamp = time.strftime("%d.%m.%Y_%H.%M.%S")
            nombre_excel = f"diagnostico_consolidado_{timestamp}.xlsx"
            ruta_excel = os.path.join(self.folder_path, nombre_excel)
            
            self.log_signal.emit("info", f"📊 Excel: {nombre_excel}")
            self.logger.info(f"📊 Excel: {nombre_excel}")
            
            # ============================================================
            # FASE 1-3: Procesar cada carpeta (USA EL CORE)
            # ============================================================
            datos_por_hoja = {}
            total_carpetas = len(CARPETAS_CONFIG)
            carpetas_procesadas = 0
            total_registros = 0
            
            for nombre_carpeta, config in CARPETAS_CONFIG.items():
                if not self._is_running:
                    self.logger.warning("Proceso cancelado por el usuario")
                    return
                
                ruta_subcarpeta = os.path.join(self.folder_path, nombre_carpeta)
                
                if not os.path.isdir(ruta_subcarpeta):
                    msg = f"⚠️ Carpeta '{nombre_carpeta}' no encontrada, omitiendo..."
                    self.log_signal.emit("warning", msg)
                    self.logger.warning(msg)
                    carpetas_procesadas += 1
                    self.progress_signal.emit(carpetas_procesadas, total_carpetas + 1)
                    continue
                
                self.log_signal.emit("info", "")
                msg = f"📋 Procesando: {nombre_carpeta} ({config['tipo']})"
                self.log_signal.emit("info", msg)
                self.logger.info(msg)
                
                # Procesar carpeta (USA EL CORE)
                registros = procesar_carpeta(ruta_subcarpeta, config)
                datos_por_hoja[nombre_carpeta] = registros
                
                total_registros += len(registros)
                
                msg = f"   ✅ {len(registros)} registros generados"
                self.log_signal.emit("success", msg)
                self.logger.info(msg)
                
                # Guardar JSON opcional si se solicita
                if self.guardar_json and registros:
                    import json
                    ruta_json = os.path.join(self.folder_path, f"diagnostico_{nombre_carpeta}.json")
                    try:
                        with open(ruta_json, 'w', encoding='utf-8') as f:
                            json.dump(registros, f, ensure_ascii=False, indent=2)
                        msg = f"   💾 JSON guardado: {os.path.basename(ruta_json)}"
                        self.log_signal.emit("info", msg)
                        self.logger.info(msg)
                    except Exception as e:
                        self.logger.error(f"Error guardando JSON: {e}")
                
                carpetas_procesadas += 1
                self.progress_signal.emit(carpetas_procesadas, total_carpetas + 1)
            
            # Verificar que haya datos para procesar
            if not datos_por_hoja or total_registros == 0:
                error_msg = "No se generaron registros. Verifique que las carpetas contengan PDFs válidos."
                self.logger.error(error_msg)
                self.error_signal.emit(error_msg)
                return
            
            # ============================================================
            # FASE 4: Generar Excel (USA EL CORE)
            # ============================================================
            if not self._is_running:
                self.logger.warning("Proceso cancelado por el usuario")
                return
            
            self.log_signal.emit("info", "")
            self.log_signal.emit("info", "📋 Generando archivo Excel...")
            self.logger.info("📋 Generando archivo Excel...")
            
            exito = generar_excel_multihoja(datos_por_hoja, ruta_excel)
            
            if not exito:
                error_msg = "Error al generar el archivo Excel"
                self.logger.error(error_msg)
                self.error_signal.emit(error_msg)
                return
            
            self.progress_signal.emit(total_carpetas + 1, total_carpetas + 1)
            
            # ============================================================
            # FASE 5: Resumen final
            # ============================================================
            elapsed_time = time.time() - start_time
            
            # Calcular estadísticas por tipo
            stats_por_tipo = {}
            total_exitosos = 0
            total_fallidos = 0
            
            for nombre_carpeta, registros in datos_por_hoja.items():
                exitosos = sum(1 for r in registros if r.get('exito_extraccion', False))
                fallidos = len(registros) - exitosos
                
                stats_por_tipo[nombre_carpeta] = {
                    'total': len(registros),
                    'exitosos': exitosos,
                    'fallidos': fallidos
                }
                
                total_exitosos += exitosos
                total_fallidos += fallidos
            
            self.log_signal.emit("info", "")
            self.log_signal.emit("info", "=" * 50)
            self.log_signal.emit("info", "📊 RESUMEN FINAL")
            self.log_signal.emit("info", f"📂 Carpetas procesadas: {carpetas_procesadas}")
            self.log_signal.emit("info", f"📄 Total registros: {total_registros}")
            self.log_signal.emit("success", f"✅ Extracciones exitosas: {total_exitosos}")
            
            if total_fallidos > 0:
                self.log_signal.emit("error", f"❌ Extracciones fallidas: {total_fallidos}")
                porcentaje_exito = (total_exitosos / total_registros * 100) if total_registros > 0 else 0
                self.log_signal.emit("info", f"📊 Tasa de éxito: {porcentaje_exito:.1f}%")
            
            self.log_signal.emit("info", f"📊 Excel generado: {nombre_excel}")
            self.log_signal.emit("info", f"⏱️ Tiempo transcurrido: {elapsed_time:.2f}s")
            self.log_signal.emit("info", "=" * 50)
            
            # Log a archivo
            self.logger.info("=" * 50)
            self.logger.info("📊 RESUMEN FINAL")
            self.logger.info(f"📂 Carpetas procesadas: {carpetas_procesadas}")
            self.logger.info(f"📄 Total registros: {total_registros}")
            self.logger.info(f"✅ Extracciones exitosas: {total_exitosos}")
            
            if total_fallidos > 0:
                self.logger.error(f"❌ Extracciones fallidas: {total_fallidos}")
            
            self.logger.info(f"📊 Excel: {ruta_excel}")
            self.logger.info(f"⏱️ Tiempo: {elapsed_time:.2f}s")
            self.logger.info("=" * 50)
            
            # Emitir estadísticas
            stats = {
                'carpetas_procesadas': carpetas_procesadas,
                'total_registros': total_registros,
                'exitosos': total_exitosos,
                'fallidos': total_fallidos,
                'stats_por_tipo': stats_por_tipo,
                'ruta_excel': ruta_excel,
                'time': elapsed_time
            }
            self.stats_signal.emit(stats)
            
            # Emitir resultado final
            resultado = {
                'success': True,
                'stats': stats,
                'excel_path': ruta_excel,
                'datos_por_hoja': datos_por_hoja
            }
            
            self.logger.info("🎉 ¡Diagnóstico completado exitosamente!")
            self.log_signal.emit("success", "🎉 ¡Diagnóstico completado exitosamente!")
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