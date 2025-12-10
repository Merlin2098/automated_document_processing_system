"""
Worker para generar estructura de carpetas (Paso 1)
Ejecuta el proceso en segundo plano sin congelar la UI
"""
from PySide6.QtCore import QThread, Signal
import os

# Importar sistema de logging
from utils.logger import get_logger, log_start, log_end, log_exception

# Obtener logger para este worker
logger = get_logger('workers.core_pipeline_step1')


class CorePipelineStep1Worker(QThread):
    """Worker para generar estructura de carpetas en segundo plano"""
    
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
        
        # Lista de subcarpetas a crear
        self.subcarpetas = [
            "1_Boletas",
            "2_Afp", 
            "3_5ta",
            "4_Convocatoria",
            "5_CertificadosTrabajo"
        ]
        
        logger.info(f"Worker Step 1 creado - Carpeta: {folder_path}")
    
    def run(self):
        """Ejecuta el proceso de creación de estructura"""
        try:
            log_start(logger, "Creación de Estructura (Step 1)", carpeta_base=self.folder_path)
            
            self.log_signal.emit("info", "🚀 Iniciando creación de estructura")
            self.log_signal.emit("info", f"📂 Carpeta base: {self.folder_path}")
            
            # Validar que la carpeta base existe o crearla
            if not os.path.exists(self.folder_path):
                try:
                    os.makedirs(self.folder_path)
                    logger.info(f"Carpeta base creada: {self.folder_path}")
                    self.log_signal.emit("success", f"✅ Carpeta base creada")
                except Exception as e:
                    log_exception(logger, e, "creación de carpeta base")
                    self.error_signal.emit(f"Error al crear carpeta base: {str(e)}")
                    return
            
            carpetas_creadas = []
            carpetas_existentes = []
            errores = []
            total = len(self.subcarpetas)
            
            logger.debug(f"Creando {total} subcarpetas...")
            
            # Crear cada subcarpeta
            for idx, subcarpeta in enumerate(self.subcarpetas, 1):
                if not self._is_running:
                    logger.warning("Proceso cancelado por el usuario")
                    self.log_signal.emit("warning", "⚠️ Proceso cancelado por el usuario")
                    return
                
                ruta_completa = os.path.join(self.folder_path, subcarpeta)
                
                try:
                    if os.path.exists(ruta_completa):
                        carpetas_existentes.append(ruta_completa)
                        logger.debug(f"Carpeta ya existe: {subcarpeta}")
                        self.log_signal.emit("info", f"ℹ️ Ya existe: {subcarpeta}")
                    else:
                        os.makedirs(ruta_completa)
                        carpetas_creadas.append(ruta_completa)
                        logger.info(f"✅ Carpeta creada: {subcarpeta}")
                        self.log_signal.emit("success", f"✅ Creada: {subcarpeta}")
                except Exception as e:
                    error_msg = f"Error al crear '{subcarpeta}': {str(e)}"
                    errores.append(error_msg)
                    logger.error(error_msg)
                    self.log_signal.emit("error", f"❌ Error en {subcarpeta}: {str(e)}")
                
                # Emitir progreso
                self.progress_signal.emit(idx, total)
            
            # Generar resumen
            self.log_signal.emit("info", "=" * 50)
            self.log_signal.emit("info", "📊 RESUMEN DE LA OPERACIÓN")
            self.log_signal.emit("success", f"✅ Carpetas creadas: {len(carpetas_creadas)}")
            self.log_signal.emit("info", f"ℹ️ Carpetas existentes: {len(carpetas_existentes)}")
            self.log_signal.emit("error", f"❌ Errores: {len(errores)}")
            self.log_signal.emit("info", "=" * 50)
            
            # Emitir estadísticas
            stats = {
                'carpetas_creadas': len(carpetas_creadas),
                'carpetas_existentes': len(carpetas_existentes),
                'errores': len(errores),
                'total': total
            }
            self.stats_signal.emit(stats)
            
            # Log final
            log_end(
                logger,
                "Creación de Estructura (Step 1)",
                success=(len(errores) == 0),
                **stats
            )
            
            # Emitir resultado final
            resultado = {
                'success': len(errores) == 0,
                'carpetas_creadas': carpetas_creadas,
                'carpetas_existentes': carpetas_existentes,
                'errores': errores,
                'folder_path': self.folder_path
            }
            
            if len(errores) == 0:
                self.log_signal.emit("success", "🎉 ¡Estructura creada exitosamente!")
            else:
                self.log_signal.emit("warning", "⚠️ Proceso completado con algunos errores")
            
            self.finished_signal.emit(resultado)
            
        except Exception as e:
            log_exception(logger, e, "ejecución del worker Step 1")
            error_msg = f"Error durante la creación de estructura: {str(e)}"
            self.log_signal.emit("error", f"❌ {error_msg}")
            self.error_signal.emit(error_msg)
    
    def stop(self):
        """Detiene el worker"""
        logger.info("Solicitando detención del worker Step 1")
        self._is_running = False