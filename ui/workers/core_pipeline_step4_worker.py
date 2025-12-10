"""
Worker para renombrar archivos (Paso 4)
Ejecuta el proceso en segundo plano sin congelar la UI
"""
from PySide6.QtCore import QThread, Signal
from utils.logger import Logger
import os
import sys
import time


class CorePipelineStep4Worker(QThread):
    """Worker para renombrar archivos en segundo plano"""
    
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
        self.logger = Logger("CorePipelineStep4")
        
        # Configuración de carpetas
        self.CARPETAS_CONFIG = {
            "1_Boletas": "BOLETA",
            "2_Afp": "AFP",
            "3_5ta": "QUINTA"
        }
    
    def run(self):
        """Ejecuta el proceso de renombrado"""
        start_time = time.time()
        
        try:
            self.logger.info("🚀 Iniciando renombrado de archivos")
            self.log_signal.emit("info", "🚀 Iniciando renombrado de archivos")
            self.logger.info(f"📂 Carpeta de trabajo: {self.folder_path}")
            self.log_signal.emit("info", f"📂 Carpeta de trabajo: {self.folder_path}")
            
            # Validar carpeta
            if not os.path.isdir(self.folder_path):
                error_msg = f"La carpeta no existe: {self.folder_path}"
                self.logger.error(error_msg)
                self.error_signal.emit(error_msg)
                return
            
            # Buscar JSON de renombrado
            json_path = self._buscar_json_renombrado()
            if not json_path:
                error_msg = "No se encontró archivo JSON de renombrado"
                self.logger.error(error_msg)
                self.error_signal.emit(error_msg)
                return
            
            # Cargar datos del JSON
            rename_data = self._cargar_json(json_path)
            if not rename_data:
                error_msg = "Error al cargar datos del JSON"
                self.logger.error(error_msg)
                self.error_signal.emit(error_msg)
                return
            
            # Procesar carpetas
            stats_por_carpeta = {}
            total_renombrados = 0
            total_errores = 0
            total_omitidos = 0
            
            total_carpetas = len(self.CARPETAS_CONFIG)
            carpeta_actual = 0
            
            for nombre_carpeta, tipo_doc in self.CARPETAS_CONFIG.items():
                if not self._is_running:
                    self.logger.warning("⚠️ Proceso cancelado por el usuario")
                    self.log_signal.emit("warning", "⚠️ Proceso cancelado por el usuario")
                    return
                
                ruta_subcarpeta = os.path.join(self.folder_path, nombre_carpeta)
                
                if not os.path.isdir(ruta_subcarpeta):
                    msg = f"⚠️ Carpeta '{nombre_carpeta}' no encontrada, omitiendo..."
                    self.logger.warning(msg)
                    self.log_signal.emit("warning", msg)
                    continue
                
                stats = self._procesar_carpeta(ruta_subcarpeta, nombre_carpeta, rename_data)
                stats_por_carpeta[nombre_carpeta] = stats
                
                total_renombrados += stats['renombrados']
                total_errores += stats['errores']
                total_omitidos += stats['omitidos']
                
                carpeta_actual += 1
                self.progress_signal.emit(carpeta_actual, total_carpetas)
            
            # Calcular tiempo transcurrido
            elapsed_time = time.time() - start_time
            
            # Mostrar resumen
            self.logger.info("=" * 50)
            self.logger.info("📊 RESUMEN DEL RENOMBRADO")
            self.logger.info(f"✅ Archivos renombrados: {total_renombrados}")
            self.logger.warning(f"⏭️ Archivos omitidos: {total_omitidos}")
            self.logger.error(f"❌ Errores: {total_errores}")
            self.logger.info(f"⏱️ Tiempo transcurrido: {elapsed_time:.2f}s")
            self.logger.info("=" * 50)
            
            self.log_signal.emit("info", "")
            self.log_signal.emit("info", "=" * 50)
            self.log_signal.emit("info", "📊 RESUMEN DEL RENOMBRADO")
            self.log_signal.emit("success", f"✅ Archivos renombrados: {total_renombrados}")
            self.log_signal.emit("warning", f"⏭️ Archivos omitidos: {total_omitidos}")
            self.log_signal.emit("error", f"❌ Errores: {total_errores}")
            self.log_signal.emit("info", f"⏱️ Tiempo transcurrido: {elapsed_time:.2f}s")
            self.log_signal.emit("info", "=" * 50)
            
            # Emitir estadísticas
            stats = {
                'renombrados': total_renombrados,
                'omitidos': total_omitidos,
                'errores': total_errores,
                'time': elapsed_time,
                'por_carpeta': stats_por_carpeta
            }
            self.stats_signal.emit(stats)
            
            # Emitir resultado final
            resultado = {
                'success': True,
                'stats': stats,
                'tiempo_transcurrido': elapsed_time
            }
            
            self.logger.info("🎉 ¡Renombrado completado exitosamente!")
            self.log_signal.emit("success", "🎉 ¡Renombrado completado exitosamente!")
            self.finished_signal.emit(resultado)
            
        except Exception as e:
            error_msg = f"Error durante el renombrado: {str(e)}"
            self.logger.error(error_msg)
            self.log_signal.emit("error", f"❌ {error_msg}")
            import traceback
            self.logger.error(traceback.format_exc())
            self.error_signal.emit(error_msg)
    
    def _buscar_json_renombrado(self):
        """Busca el archivo JSON de renombrado"""
        try:
            self.logger.info("🔍 Buscando archivo JSON de renombrado...")
            self.log_signal.emit("info", "🔍 Buscando archivo JSON de renombrado...")
            
            for archivo in os.listdir(self.folder_path):
                if archivo.lower().endswith('.json') and 'rename' in archivo.lower():
                    json_path = os.path.join(self.folder_path, archivo)
                    msg = f"✅ JSON encontrado: {archivo}"
                    self.logger.info(msg)
                    self.log_signal.emit("success", msg)
                    return json_path
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error al buscar JSON: {str(e)}")
            return None
    
    def _cargar_json(self, json_path):
        """Carga y valida el JSON de renombrado"""
        try:
            import json
            
            self.logger.info("📖 Cargando datos del JSON...")
            self.log_signal.emit("info", "📖 Cargando datos del JSON...")
            
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if not isinstance(data, dict):
                self.logger.error("Formato de JSON inválido")
                return None
            
            msg = f"✅ {len(data)} registros cargados"
            self.logger.info(msg)
            self.log_signal.emit("success", msg)
            return data
            
        except Exception as e:
            self.logger.error(f"Error al cargar JSON: {str(e)}")
            return None
    
    def _procesar_carpeta(self, ruta_carpeta, nombre_carpeta, rename_data):
        """Procesa todos los PDFs en una carpeta"""
        stats = {
            'renombrados': 0,
            'errores': 0,
            'omitidos': 0
        }
        
        archivos_pdf = [f for f in os.listdir(ruta_carpeta) if f.lower().endswith('.pdf')]
        
        self.logger.info(f"📂 Procesando: {nombre_carpeta}")
        self.logger.info(f"   PDFs: {len(archivos_pdf)}")
        
        self.log_signal.emit("info", "")
        self.log_signal.emit("info", f"📂 Procesando: {nombre_carpeta}")
        self.log_signal.emit("info", f"   PDFs: {len(archivos_pdf)}")
        
        for archivo in archivos_pdf:
            if not self._is_running:
                break
            
            # Verificar si está en el JSON
            if archivo not in rename_data:
                stats['omitidos'] += 1
                continue
            
            nuevo_nombre = rename_data[archivo]
            ruta_actual = os.path.join(ruta_carpeta, archivo)
            ruta_nueva = os.path.join(ruta_carpeta, nuevo_nombre)
            
            # Intentar renombrar
            try:
                # Verificar si el destino ya existe
                if os.path.exists(ruta_nueva):
                    msg = f"   ⚠️ Ya existe: {nuevo_nombre}"
                    self.logger.warning(msg)
                    stats['errores'] += 1
                    continue
                
                os.rename(ruta_actual, ruta_nueva)
                stats['renombrados'] += 1
                
            except Exception as e:
                msg = f"   ❌ Error en {archivo}: {str(e)}"
                self.logger.error(msg)
                stats['errores'] += 1
        
        msg = f"   ✅ Completado: {stats['renombrados']} renombrados, {stats['omitidos']} omitidos, {stats['errores']} errores"
        self.logger.info(msg)
        self.log_signal.emit("success", msg)
        
        return stats
    
    def stop(self):
        """Detiene el worker"""
        self._is_running = False
        self.logger.warning("⏹️ Worker detenido por el usuario")