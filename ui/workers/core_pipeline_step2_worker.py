"""
Worker para clasificar y dividir PDFs (Paso 2) - WRAPPER PATTERN
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
from core_pipeline.step2_mover import (
    buscar_pdfs_por_tipo,
    validar_unico_archivo_por_tipo,
    verificar_archivos_en_carpetas,
    limpiar_carpeta_destino,
    dividir_pdf,
    PALABRAS_CLAVE,
    NOMBRES_BASE
)


class CorePipelineStep2Worker(QThread):
    """Worker wrapper para clasificación y división de PDFs"""
    
    # Señales
    progress_signal = Signal(int, int)  # (current, total)
    log_signal = Signal(str, str)  # (type, message)
    stats_signal = Signal(dict)  # estadísticas
    finished_signal = Signal(dict)  # resultado final
    error_signal = Signal(str)  # mensaje de error
    
    def __init__(self, folder_path: str, sobrescribir: bool = False):
        super().__init__()
        self.folder_path = folder_path
        self.sobrescribir = sobrescribir
        self._is_running = True
        self.logger = Logger("CorePipelineStep2Worker")
    
    def run(self):
        """Ejecuta el proceso usando funciones del core"""
        try:
            self.logger.info("🚀 Iniciando clasificación y división de PDFs")
            self.log_signal.emit("info", "🚀 Iniciando clasificación y división de PDFs")
            self.logger.info(f"📂 Carpeta de trabajo: {self.folder_path}")
            self.log_signal.emit("info", f"📂 Carpeta de trabajo: {self.folder_path}")
            
            # Validar carpeta
            if not os.path.isdir(self.folder_path):
                error_msg = f"La carpeta no existe: {self.folder_path}"
                self.logger.error(error_msg)
                self.error_signal.emit(error_msg)
                return
            
            # Verificar PyPDF2
            try:
                from PyPDF2 import PdfReader, PdfWriter
            except ImportError:
                error_msg = "PyPDF2 no está instalado. Instale con: pip install PyPDF2"
                self.logger.error(error_msg)
                self.error_signal.emit(error_msg)
                return
            
            # ============================================================
            # FASE 1: Buscar y clasificar PDFs (USA EL CORE)
            # ============================================================
            self.log_signal.emit("info", "")
            self.log_signal.emit("info", "📋 [1/5] Buscando y clasificando PDFs...")
            self.logger.info("📋 [1/5] Buscando y clasificando PDFs...")
            
            pdfs_por_tipo, pdfs_no_clasificados = buscar_pdfs_por_tipo(self.folder_path)
            
            total_clasificados = sum(len(archivos) for archivos in pdfs_por_tipo.values())
            
            if total_clasificados == 0:
                error_msg = "No se encontraron PDFs clasificables en la carpeta"
                self.logger.error(error_msg)
                self.error_signal.emit(error_msg)
                return
            
            self.log_signal.emit("success", f"✅ PDFs clasificados: {total_clasificados}")
            self.logger.info(f"✅ PDFs clasificados: {total_clasificados}")
            
            if pdfs_no_clasificados:
                msg = f"⚠️ PDFs no clasificados: {len(pdfs_no_clasificados)}"
                self.log_signal.emit("warning", msg)
                self.logger.warning(msg)
            
            # ============================================================
            # FASE 2: Validar un solo archivo por tipo (USA EL CORE)
            # ============================================================
            if not self._is_running:
                self.logger.warning("Proceso cancelado por el usuario")
                return
            
            self.log_signal.emit("info", "")
            self.log_signal.emit("info", "📋 [2/5] Validando archivos...")
            self.logger.info("📋 [2/5] Validando archivos...")
            
            if not validar_unico_archivo_por_tipo(pdfs_por_tipo):
                error_msg = "Se encontraron múltiples archivos para un mismo tipo"
                self.logger.error(error_msg)
                self.error_signal.emit(error_msg)
                return
            
            self.log_signal.emit("success", "✅ Validación correcta: un archivo por tipo")
            self.logger.info("✅ Validación correcta")
            
            # ============================================================
            # FASE 3: Verificar y limpiar carpetas destino (USA EL CORE)
            # ============================================================
            if not self._is_running:
                self.logger.warning("Proceso cancelado por el usuario")
                return
            
            self.log_signal.emit("info", "")
            self.log_signal.emit("info", "📋 [3/5] Preparando carpetas destino...")
            self.logger.info("📋 [3/5] Preparando carpetas destino...")
            
            carpetas_destino = [os.path.join(self.folder_path, tipo) for tipo in PALABRAS_CLAVE.keys()]
            carpetas_con_archivos = verificar_archivos_en_carpetas(carpetas_destino)
            
            if carpetas_con_archivos:
                if self.sobrescribir:
                    msg = f"⚠️ Limpiando {len(carpetas_con_archivos)} carpetas con archivos existentes..."
                    self.log_signal.emit("warning", msg)
                    self.logger.warning(msg)
                    
                    for carpeta in carpetas_destino:
                        limpiar_carpeta_destino(carpeta)
                    
                    self.log_signal.emit("success", "✅ Carpetas limpiadas")
                else:
                    total_archivos = sum(carpetas_con_archivos.values())
                    error_msg = f"Existen {total_archivos} archivos en las carpetas destino. Active 'sobrescribir' para continuar."
                    self.logger.error(error_msg)
                    self.error_signal.emit(error_msg)
                    return
            
            # ============================================================
            # FASE 4: Dividir PDFs (USA EL CORE)
            # ============================================================
            if not self._is_running:
                self.logger.warning("Proceso cancelado por el usuario")
                return
            
            self.log_signal.emit("info", "")
            self.log_signal.emit("info", "📋 [4/5] Dividiendo PDFs por páginas...")
            self.logger.info("📋 [4/5] Dividiendo PDFs...")
            
            resumen = {
                "total_paginas": 0,
                "pdfs_procesados": 0,
                "pdfs_con_error": 0,
                "errores": [],
                "detalle_por_tipo": {}
            }
            
            tipos_con_archivos = [tipo for tipo, archivos in pdfs_por_tipo.items() if archivos]
            total_pdfs = len(tipos_con_archivos)
            
            for idx, tipo in enumerate(tipos_con_archivos, 1):
                if not self._is_running:
                    break
                
                archivos = pdfs_por_tipo[tipo]
                archivo = archivos[0]  # Solo hay uno (validado anteriormente)
                
                ruta_pdf = os.path.join(self.folder_path, archivo)
                carpeta_destino = os.path.join(self.folder_path, tipo)
                nombre_base = NOMBRES_BASE[tipo]
                
                msg = f"   📄 {tipo}: {archivo}"
                self.log_signal.emit("info", msg)
                self.logger.info(msg)
                
                # Dividir PDF (USA EL CORE)
                exito, paginas, mensaje_error = dividir_pdf(ruta_pdf, carpeta_destino, nombre_base)
                
                if exito:
                    resumen["total_paginas"] += paginas
                    resumen["pdfs_procesados"] += 1
                    resumen["detalle_por_tipo"][tipo] = {
                        "procesado": True,
                        "archivo": archivo,
                        "paginas": paginas
                    }
                    
                    msg = f"      ✅ {paginas} páginas generadas"
                    self.log_signal.emit("success", msg)
                    self.logger.info(msg)
                else:
                    resumen["pdfs_con_error"] += 1
                    resumen["errores"].append({
                        "tipo": tipo,
                        "archivo": archivo,
                        "error": mensaje_error
                    })
                    resumen["detalle_por_tipo"][tipo] = {
                        "procesado": False,
                        "archivo": archivo,
                        "error": mensaje_error
                    }
                    
                    msg = f"      ❌ Error: {mensaje_error}"
                    self.log_signal.emit("error", msg)
                    self.logger.error(msg)
                
                # Actualizar progreso: solo PDFs procesados
                self.progress_signal.emit(idx, total_pdfs)
            
            # ============================================================
            # FASE 5: Resumen final
            # ============================================================
            resumen["pdfs_no_clasificados"] = len(pdfs_no_clasificados)
            
            self.log_signal.emit("info", "")
            self.log_signal.emit("info", "=" * 50)
            self.log_signal.emit("info", "📊 RESUMEN FINAL")
            self.log_signal.emit("success", f"✅ PDFs procesados: {resumen['pdfs_procesados']}")
            self.log_signal.emit("info", f"📄 Total páginas: {resumen['total_paginas']}")
            
            if resumen['pdfs_con_error'] > 0:
                self.log_signal.emit("error", f"❌ PDFs con errores: {resumen['pdfs_con_error']}")
            
            if pdfs_no_clasificados:
                self.log_signal.emit("warning", f"⚠️ PDFs no clasificados: {len(pdfs_no_clasificados)}")
            
            self.log_signal.emit("info", "=" * 50)
            
            # Log a archivo
            self.logger.info("=" * 50)
            self.logger.info("📊 RESUMEN FINAL")
            self.logger.info(f"✅ PDFs procesados: {resumen['pdfs_procesados']}")
            self.logger.info(f"📄 Total páginas: {resumen['total_paginas']}")
            
            if resumen['pdfs_con_error'] > 0:
                self.logger.error(f"❌ PDFs con errores: {resumen['pdfs_con_error']}")
            
            if pdfs_no_clasificados:
                self.logger.warning(f"⚠️ PDFs no clasificados: {len(pdfs_no_clasificados)}")
            
            self.logger.info("=" * 50)
            
            # Emitir estadísticas
            stats = {
                'pdfs_procesados': resumen['pdfs_procesados'],
                'pdfs_con_error': resumen['pdfs_con_error'],
                'total_paginas': resumen['total_paginas'],
                'pdfs_no_clasificados': len(pdfs_no_clasificados),
                'detalle_por_tipo': resumen['detalle_por_tipo']
            }
            self.stats_signal.emit(stats)
            
            # Emitir resultado final
            resultado = {
                'success': True,
                'stats': stats,
                'resumen': resumen
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