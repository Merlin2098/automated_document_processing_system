"""
Worker para renombrar archivos (Paso 4) - WRAPPER PATTERN
Usa directamente las funciones del módulo core sin reimplementar lógica
"""
from PySide6.QtCore import QThread, Signal
from utils.logger import Logger
import os
import sys

# Agregar rutas para imports del core
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(os.path.dirname(current_dir))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Importar funciones PURAS del core (sin dependencias de UI)
from core_pipeline.step4_rename import (
    cargar_json,
    convertir_json_a_mapeo,
    renombrar_archivos
)


class CorePipelineStep4Worker(QThread):
    """Worker wrapper para renombrar archivos"""
    
    # Señales
    progress_signal = Signal(int, int)  # (current, total)
    log_signal = Signal(str, str)  # (type, message)
    stats_signal = Signal(dict)  # estadísticas
    finished_signal = Signal(dict)  # resultado final
    error_signal = Signal(str)  # mensaje de error
    
    def __init__(self, folder_path: str):
        super().__init__()
        self.folder_path = folder_path
        self._is_running = True
        self.logger = Logger("CorePipelineStep4Worker")
        
        # Carpetas a procesar (las 3 primeras)
        self.carpetas_a_procesar = ['1_Boletas', '2_Afp', '3_5ta']
    
    def run(self):
        """Ejecuta el proceso usando funciones del core"""
        try:
            self.logger.info("🚀 Iniciando renombrado de archivos")
            self.log_signal.emit("info", "🚀 Iniciando renombrado de archivos")
            self.logger.info(f"📂 Carpeta madre: {self.folder_path}")
            self.log_signal.emit("info", f"📂 Carpeta madre: {self.folder_path}")
            
            # Validar carpeta
            if not os.path.isdir(self.folder_path):
                error_msg = f"La carpeta no existe: {self.folder_path}"
                self.logger.error(error_msg)
                self.error_signal.emit(error_msg)
                return
            
            # ============================================================
            # Procesar cada lote
            # ============================================================
            estadisticas = []
            total_carpetas = len(self.carpetas_a_procesar)
            
            for idx, nombre_carpeta in enumerate(self.carpetas_a_procesar, 1):
                if not self._is_running:
                    self.logger.warning("Proceso cancelado por el usuario")
                    return
                
                ruta_lote = os.path.join(self.folder_path, nombre_carpeta)
                
                # Verificar que la carpeta existe
                if not os.path.exists(ruta_lote):
                    msg = f"⚠️ Carpeta '{nombre_carpeta}' no existe, omitiendo..."
                    self.log_signal.emit("warning", msg)
                    self.logger.warning(msg)
                    
                    estadisticas.append({
                        'lote': nombre_carpeta,
                        'exitosos': 0,
                        'fallidos': 0,
                        'omitidos': 0,
                        'total': 0,
                        'estado': 'no_existe'
                    })
                    
                    self.progress_signal.emit(idx, total_carpetas)
                    continue
                
                if not os.path.isdir(ruta_lote):
                    msg = f"⚠️ '{nombre_carpeta}' no es una carpeta, omitiendo..."
                    self.log_signal.emit("warning", msg)
                    self.logger.warning(msg)
                    self.progress_signal.emit(idx, total_carpetas)
                    continue
                
                # Procesar el lote
                self.log_signal.emit("info", "")
                self.log_signal.emit("info", f"📋 Procesando: {nombre_carpeta}")
                self.logger.info(f"📋 Procesando: {nombre_carpeta}")
                
                resultado = self._procesar_lote(ruta_lote, nombre_carpeta)
                estadisticas.append(resultado)
                
                # Mostrar resultado del lote
                if resultado['estado'] == 'procesado':
                    msg = f"   ✅ Renombrados: {resultado['exitosos']} | Omitidos: {resultado['omitidos']} | Errores: {resultado['fallidos']}"
                    self.log_signal.emit("success", msg)
                    self.logger.info(msg)
                else:
                    msg = f"   ⚠️ Estado: {resultado['estado']}"
                    self.log_signal.emit("warning", msg)
                    self.logger.warning(msg)
                
                self.progress_signal.emit(idx, total_carpetas)
            
            # ============================================================
            # Resumen final
            # ============================================================
            total_exitosos = sum(e['exitosos'] for e in estadisticas)
            total_fallidos = sum(e['fallidos'] for e in estadisticas)
            total_omitidos = sum(e['omitidos'] for e in estadisticas)
            total_archivos = sum(e['total'] for e in estadisticas)
            
            self.log_signal.emit("info", "")
            self.log_signal.emit("info", "=" * 50)
            self.log_signal.emit("info", "📊 RESUMEN FINAL")
            self.log_signal.emit("info", f"📂 Lotes procesados: {len(estadisticas)}")
            self.log_signal.emit("success", f"✅ Archivos renombrados: {total_exitosos}")
            self.log_signal.emit("info", f"⊘ Archivos omitidos: {total_omitidos}")
            
            if total_fallidos > 0:
                self.log_signal.emit("error", f"❌ Archivos con errores: {total_fallidos}")
            
            if total_archivos > 0:
                porcentaje = (total_exitosos / total_archivos) * 100
                self.log_signal.emit("info", f"📊 Tasa de éxito: {porcentaje:.1f}%")
            
            self.log_signal.emit("info", "=" * 50)
            
            # Log a archivo
            self.logger.info("=" * 50)
            self.logger.info("📊 RESUMEN FINAL")
            self.logger.info(f"📂 Lotes procesados: {len(estadisticas)}")
            self.logger.info(f"✅ Archivos renombrados: {total_exitosos}")
            self.logger.info(f"⊘ Archivos omitidos: {total_omitidos}")
            
            if total_fallidos > 0:
                self.logger.error(f"❌ Archivos con errores: {total_fallidos}")
            
            if total_archivos > 0:
                porcentaje = (total_exitosos / total_archivos) * 100
                self.logger.info(f"📊 Tasa de éxito: {porcentaje:.1f}%")
            
            self.logger.info("=" * 50)
            
            # Emitir estadísticas
            stats = {
                'lotes_procesados': len(estadisticas),
                'total_exitosos': total_exitosos,
                'total_fallidos': total_fallidos,
                'total_omitidos': total_omitidos,
                'total_archivos': total_archivos,
                'detalle_por_lote': estadisticas
            }
            self.stats_signal.emit(stats)
            
            # Emitir resultado final
            resultado = {
                'success': True,
                'stats': stats
            }
            
            self.logger.info("🎉 ¡Renombrado completado exitosamente!")
            self.log_signal.emit("success", "🎉 ¡Renombrado completado exitosamente!")
            self.finished_signal.emit(resultado)
            
        except Exception as e:
            error_msg = f"Error durante el proceso: {str(e)}"
            self.logger.error(error_msg)
            self.log_signal.emit("error", f"❌ {error_msg}")
            import traceback
            self.logger.error(traceback.format_exc())
            self.error_signal.emit(error_msg)
    
    def _procesar_lote(self, carpeta_lote: str, nombre_lote: str) -> dict:
        """
        Procesa un lote (carpeta) usando funciones del core.
        
        Returns:
            dict: Estadísticas del procesamiento
        """
        try:
            # Buscar archivo JSON (USA EL CORE)
            archivos_json = [f for f in os.listdir(carpeta_lote) if f.endswith('.json')]
            
            if not archivos_json:
                self.logger.warning(f"   ⚠️ No se encontró archivo JSON en {nombre_lote}")
                return {
                    'lote': nombre_lote,
                    'exitosos': 0,
                    'fallidos': 0,
                    'omitidos': 0,
                    'total': 0,
                    'estado': 'sin_json'
                }
            
            if len(archivos_json) > 1:
                msg = f"   ⚠️ Múltiples JSON encontrados, usando: {archivos_json[0]}"
                self.log_signal.emit("warning", msg)
                self.logger.warning(msg)
            
            ruta_json = os.path.join(carpeta_lote, archivos_json[0])
            
            msg = f"   📄 JSON: {archivos_json[0]}"
            self.log_signal.emit("info", msg)
            self.logger.info(msg)
            
            # Cargar datos del JSON (USA EL CORE)
            datos_json = cargar_json(ruta_json)
            
            if datos_json is None:
                return {
                    'lote': nombre_lote,
                    'exitosos': 0,
                    'fallidos': 0,
                    'omitidos': 0,
                    'total': 0,
                    'estado': 'json_invalido'
                }
            
            if not datos_json:
                self.logger.warning(f"   ⚠️ El archivo JSON está vacío")
                return {
                    'lote': nombre_lote,
                    'exitosos': 0,
                    'fallidos': 0,
                    'omitidos': 0,
                    'total': 0,
                    'estado': 'json_vacio'
                }
            
            msg = f"   📋 Registros en JSON: {len(datos_json)}"
            self.log_signal.emit("info", msg)
            self.logger.info(msg)
            
            # Convertir a mapeo (USA EL CORE)
            mapeo = convertir_json_a_mapeo(datos_json)
            
            if not mapeo:
                self.logger.error(f"   ❌ No se pudo generar mapeo de renombrado")
                return {
                    'lote': nombre_lote,
                    'exitosos': 0,
                    'fallidos': 0,
                    'omitidos': 0,
                    'total': 0,
                    'estado': 'mapeo_vacio'
                }
            
            msg = f"   🔄 Archivos únicos a renombrar: {len(mapeo)}"
            self.log_signal.emit("info", msg)
            self.logger.info(msg)
            
            # Ejecutar renombrado (USA EL CORE)
            exitosos, fallidos, omitidos, total = renombrar_archivos(carpeta_lote, mapeo)
            
            return {
                'lote': nombre_lote,
                'exitosos': exitosos,
                'fallidos': fallidos,
                'omitidos': omitidos,
                'total': total,
                'estado': 'procesado'
            }
            
        except Exception as e:
            self.logger.error(f"Error procesando lote {nombre_lote}: {str(e)}")
            return {
                'lote': nombre_lote,
                'exitosos': 0,
                'fallidos': 0,
                'omitidos': 0,
                'total': 0,
                'estado': 'error'
            }
    
    def stop(self):
        """Detiene el worker"""
        self._is_running = False
        self.logger.warning("ℹ️ Worker detenido por el usuario")