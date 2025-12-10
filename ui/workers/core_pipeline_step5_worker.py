"""
Worker para unir PDFs finales (Paso 5)
Ejecuta el proceso en segundo plano sin congelar la UI
"""
from PySide6.QtCore import QThread, Signal
from utils.logger import Logger
import os
import time


class CorePipelineStep5Worker(QThread):
    """Worker para unir PDFs en segundo plano"""
    
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
        self.logger = Logger("CorePipelineStep5")
        
        # Configuración de carpetas
        self.CARPETAS_CONFIG = {
            "1_Boletas": "BOLETA",
            "2_Afp": "AFP",
            "3_5ta": "QUINTA"
        }
    
    def run(self):
        """Ejecuta el proceso de unión de PDFs"""
        start_time = time.time()
        
        try:
            self.logger.info("🚀 Iniciando unión de PDFs")
            self.log_signal.emit("info", "🚀 Iniciando unión de PDFs")
            self.logger.info(f"📂 Carpeta de trabajo: {self.folder_path}")
            self.log_signal.emit("info", f"📂 Carpeta de trabajo: {self.folder_path}")
            
            # Validar carpeta
            if not os.path.isdir(self.folder_path):
                error_msg = f"La carpeta no existe: {self.folder_path}"
                self.logger.error(error_msg)
                self.error_signal.emit(error_msg)
                return
            
            # Importar PyPDF2
            try:
                from PyPDF2 import PdfMerger
            except ImportError:
                error_msg = "PyPDF2 no está instalado. Instale con: pip install PyPDF2"
                self.logger.error(error_msg)
                self.error_signal.emit(error_msg)
                return
            
            # Crear carpeta de salida
            timestamp = time.strftime("%d.%m.%Y_%H.%M.%S")
            carpeta_salida = os.path.join(self.folder_path, f"PDFs_Unificados_{timestamp}")
            os.makedirs(carpeta_salida, exist_ok=True)
            
            msg = f"📁 Carpeta de salida: {os.path.basename(carpeta_salida)}"
            self.logger.info(msg)
            self.log_signal.emit("info", msg)
            
            # Procesar cada carpeta
            pdfs_generados = []
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
                    carpeta_actual += 1
                    self.progress_signal.emit(carpeta_actual, total_carpetas)
                    continue
                
                pdf_unificado = self._procesar_carpeta(
                    ruta_subcarpeta, 
                    nombre_carpeta, 
                    tipo_doc,
                    carpeta_salida,
                    PdfMerger
                )
                
                if pdf_unificado:
                    pdfs_generados.append(pdf_unificado)
                
                carpeta_actual += 1
                self.progress_signal.emit(carpeta_actual, total_carpetas)
            
            if not pdfs_generados:
                error_msg = "No se generó ningún PDF unificado"
                self.logger.error(error_msg)
                self.error_signal.emit(error_msg)
                return
            
            # Calcular tiempo transcurrido
            elapsed_time = time.time() - start_time
            
            # Mostrar resumen
            self.logger.info("=" * 50)
            self.logger.info("📊 RESUMEN DE UNIFICACIÓN")
            self.logger.info(f"✅ PDFs unificados generados: {len(pdfs_generados)}")
            self.logger.info(f"📁 Ubicación: {os.path.basename(carpeta_salida)}")
            self.logger.info(f"⏱️ Tiempo transcurrido: {elapsed_time:.2f}s")
            self.logger.info("=" * 50)
            
            self.log_signal.emit("info", "")
            self.log_signal.emit("info", "=" * 50)
            self.log_signal.emit("info", "📊 RESUMEN DE UNIFICACIÓN")
            self.log_signal.emit("success", f"✅ PDFs unificados generados: {len(pdfs_generados)}")
            self.log_signal.emit("info", f"📁 Ubicación: {os.path.basename(carpeta_salida)}")
            self.log_signal.emit("info", f"⏱️ Tiempo transcurrido: {elapsed_time:.2f}s")
            self.log_signal.emit("info", "=" * 50)
            
            # Emitir estadísticas
            stats = {
                'pdfs_generados': len(pdfs_generados),
                'carpeta_salida': carpeta_salida,
                'time': elapsed_time
            }
            self.stats_signal.emit(stats)
            
            # Emitir resultado final
            resultado = {
                'success': True,
                'pdfs_generados': pdfs_generados,
                'carpeta_salida': carpeta_salida,
                'stats': stats,
                'tiempo_transcurrido': elapsed_time
            }
            
            self.logger.info("🎉 ¡Unificación completada exitosamente!")
            self.log_signal.emit("success", "🎉 ¡Unificación completada exitosamente!")
            self.finished_signal.emit(resultado)
            
        except Exception as e:
            error_msg = f"Error durante la unificación: {str(e)}"
            self.logger.error(error_msg)
            self.log_signal.emit("error", f"❌ {error_msg}")
            import traceback
            self.logger.error(traceback.format_exc())
            self.error_signal.emit(error_msg)
    
    def _procesar_carpeta(self, ruta_carpeta, nombre_carpeta, tipo_doc, carpeta_salida, PdfMerger):
        """Procesa una carpeta y genera un PDF unificado"""
        try:
            self.logger.info(f"📂 Procesando: {nombre_carpeta}")
            self.log_signal.emit("info", "")
            self.log_signal.emit("info", f"📂 Procesando: {nombre_carpeta}")
            
            # Obtener PDFs ordenados
            archivos_pdf = sorted([
                f for f in os.listdir(ruta_carpeta) 
                if f.lower().endswith('.pdf')
            ])
            
            if not archivos_pdf:
                msg = f"   ⚠️ No hay PDFs para unificar"
                self.logger.warning(msg)
                self.log_signal.emit("warning", msg)
                return None
            
            msg = f"   📄 PDFs encontrados: {len(archivos_pdf)}"
            self.logger.info(msg)
            self.log_signal.emit("info", msg)
            
            # Crear merger
            merger = PdfMerger()
            
            # Agregar PDFs
            for idx, archivo in enumerate(archivos_pdf, 1):
                if not self._is_running:
                    break
                
                ruta_pdf = os.path.join(ruta_carpeta, archivo)
                
                try:
                    merger.append(ruta_pdf)
                    
                    # Log cada 100 archivos
                    if idx % 100 == 0:
                        msg = f"   Agregados: {idx}/{len(archivos_pdf)}"
                        self.logger.info(msg)
                        self.log_signal.emit("info", msg)
                        
                except Exception as e:
                    msg = f"   ⚠️ Error en {archivo}: {str(e)}"
                    self.logger.warning(msg)
                    continue
            
            # Generar nombre de salida
            timestamp = time.strftime("%d.%m.%Y_%H.%M.%S")
            nombre_salida = f"{tipo_doc}_UNIFICADO_{timestamp}.pdf"
            ruta_salida = os.path.join(carpeta_salida, nombre_salida)
            
            # Guardar PDF unificado
            self.logger.info("   💾 Guardando PDF unificado...")
            self.log_signal.emit("info", "   💾 Guardando PDF unificado...")
            
            merger.write(ruta_salida)
            merger.close()
            
            msg = f"   ✅ Generado: {nombre_salida}"
            self.logger.info(msg)
            self.log_signal.emit("success", msg)
            
            return nombre_salida
            
        except Exception as e:
            msg = f"   ❌ Error al procesar {nombre_carpeta}: {str(e)}"
            self.logger.error(msg)
            self.log_signal.emit("error", msg)
            return None
    
    def stop(self):
        """Detiene el worker"""
        self._is_running = False
        self.logger.warning("⏹️ Worker detenido por el usuario")