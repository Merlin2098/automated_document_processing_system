"""
Worker para dividir y clasificar PDFs (Paso 2)
Ejecuta el proceso en segundo plano sin congelar la UI
"""
from PySide6.QtCore import QThread, Signal
import os
import time
from PyPDF2 import PdfReader, PdfWriter
import PyPDF2

# Importar sistema de logging
from utils.logger import (
    get_logger, log_start, log_end, log_progress,
    log_file_operation, log_exception, format_time_elapsed
)

# Obtener logger para este worker
logger = get_logger('workers.core_pipeline_step2')


class CorePipelineStep2Worker(QThread):
    """Worker para dividir y clasificar PDFs en segundo plano"""
    
    # Señales
    progress_signal = Signal(int, int)  # (current, total)
    log_signal = Signal(str, str)  # (type, message)
    stats_signal = Signal(dict)  # estadísticas
    finished_signal = Signal(dict)  # resultado final
    error_signal = Signal(str)  # mensaje de error
    
    # Configuración de palabras clave
    PALABRAS_CLAVE = {
        "1_Boletas": ["boleta", "boletas"],
        "2_Afp": ["afp"],
        "3_5ta": ["quinta"]
    }
    
    # Nombres base para archivos resultantes
    NOMBRES_BASE = {
        "1_Boletas": "boleta",
        "2_Afp": "afp", 
        "3_5ta": "quinta"
    }
    
    def __init__(self, folder_path: str):
        super().__init__()
        self.folder_path = folder_path
        self._is_running = True
        
        logger.info(f"Worker Step 2 creado - Carpeta: {folder_path}")
    
    def run(self):
        """Ejecuta el proceso de división y clasificación"""
        start_time = time.time()
        
        try:
            log_start(logger, "División y Clasificación PDFs (Step 2)", carpeta_madre=self.folder_path)
            
            self.log_signal.emit("info", "🚀 Iniciando división y clasificación de PDFs")
            self.log_signal.emit("info", f"📂 Carpeta madre: {self.folder_path}")
            
            # Validar carpeta
            if not os.path.isdir(self.folder_path):
                logger.error(f"Carpeta no existe: {self.folder_path}")
                self.error_signal.emit(f"La carpeta no existe: {self.folder_path}")
                return
            
            # 1. Buscar y clasificar PDFs
            logger.info("Buscando y clasificando PDFs...")
            self.log_signal.emit("info", "🔍 Buscando y clasificando PDFs...")
            pdfs_por_tipo, pdfs_no_clasificados = self._buscar_pdfs_por_tipo()
            
            # 2. Validar un solo archivo por tipo
            logger.debug("Validando archivos por tipo...")
            self.log_signal.emit("info", "✔️ Validando archivos por tipo...")
            if not self._validar_unico_archivo_por_tipo(pdfs_por_tipo):
                self.error_signal.emit("Se encontraron múltiples archivos para un mismo tipo")
                return
            
            # 3. Verificar que hay archivos para procesar
            total_pdfs = sum(len(archivos) for archivos in pdfs_por_tipo.values())
            if total_pdfs == 0:
                logger.warning("No se encontraron archivos PDF con palabras clave válidas")
                self.error_signal.emit("No se encontraron archivos PDF con palabras clave válidas")
                return
            
            # 4. Procesar cada tipo de PDF
            logger.info("Procesando PDFs...")
            self.log_signal.emit("info", "🔄 Procesando PDFs...")
            resumen = {
                "total_paginas": 0,
                "pdfs_procesados": 0,
                "pdfs_con_error": 0,
                "errores": [],
                "detalle_por_tipo": {}
            }
            
            for tipo, archivos in pdfs_por_tipo.items():
                if not self._is_running:
                    logger.warning("Proceso cancelado por el usuario")
                    self.log_signal.emit("warning", "⚠️ Proceso cancelado por el usuario")
                    return
                
                if not archivos:
                    resumen["detalle_por_tipo"][tipo] = {"procesado": False, "mensaje": "No hay archivos"}
                    continue
                
                archivo = archivos[0]
                ruta_pdf = os.path.join(self.folder_path, archivo)
                carpeta_destino = os.path.join(self.folder_path, tipo)
                nombre_base = self.NOMBRES_BASE[tipo]
                
                self.log_signal.emit("info", f"")
                self.log_signal.emit("info", f"📋 Procesando {tipo}: {archivo}")
                logger.info(f"Procesando {tipo}: {archivo}")
                
                # Dividir PDF
                exito, paginas, mensaje_error = self._dividir_pdf(ruta_pdf, carpeta_destino, nombre_base)
                
                if exito:
                    resumen["total_paginas"] += paginas
                    resumen["pdfs_procesados"] += 1
                    resumen["detalle_por_tipo"][tipo] = {
                        "procesado": True,
                        "archivo": archivo,
                        "paginas": paginas
                    }
                    logger.info(f"✅ {tipo} procesado: {paginas} páginas")
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
                    logger.error(f"❌ Error en {tipo}: {mensaje_error}")
                    self.log_signal.emit("error", f"  ❌ Error: {mensaje_error}")
            
            # 5. Registrar PDFs no clasificados
            resumen["pdfs_no_clasificados"] = len(pdfs_no_clasificados)
            if pdfs_no_clasificados:
                logger.warning(f"{len(pdfs_no_clasificados)} PDFs no clasificados")
                self.log_signal.emit("info", "")
                self.log_signal.emit("info", f"📋 PDFs no clasificados: {len(pdfs_no_clasificados)}")
                for archivo in pdfs_no_clasificados[:5]:
                    self.log_signal.emit("info", f"  • {archivo}")
                if len(pdfs_no_clasificados) > 5:
                    self.log_signal.emit("info", f"  ... y {len(pdfs_no_clasificados) - 5} más")
            
            # Calcular tiempo transcurrido
            elapsed_time = time.time() - start_time
            
            # Mostrar resumen
            self.log_signal.emit("info", "")
            self.log_signal.emit("info", "=" * 50)
            self.log_signal.emit("info", "📊 RESUMEN DEL PROCESAMIENTO")
            self.log_signal.emit("success", f"✅ PDFs procesados: {resumen['pdfs_procesados']}")
            self.log_signal.emit("error", f"❌ PDFs con error: {resumen['pdfs_con_error']}")
            self.log_signal.emit("info", f"📄 Total páginas generadas: {resumen['total_paginas']}")
            self.log_signal.emit("info", f"⚠️ PDFs no clasificados: {resumen['pdfs_no_clasificados']}")
            self.log_signal.emit("info", f"⏱️ Tiempo transcurrido: {elapsed_time:.2f}s")
            self.log_signal.emit("info", "=" * 50)
            
            # Emitir estadísticas
            stats = {
                'pdfs_procesados': resumen['pdfs_procesados'],
                'pdfs_con_error': resumen['pdfs_con_error'],
                'total_paginas': resumen['total_paginas'],
                'time': elapsed_time
            }
            self.stats_signal.emit(stats)
            
            # Log final
            log_end(
                logger,
                "División y Clasificación PDFs (Step 2)",
                success=(resumen['pdfs_con_error'] == 0),
                **stats
            )
            
            # Emitir resultado final
            resultado = {
                'success': resumen['pdfs_con_error'] == 0,
                'resumen': resumen,
                'tiempo_transcurrido': elapsed_time
            }
            
            if resumen['pdfs_con_error'] == 0 and resumen['pdfs_procesados'] > 0:
                self.log_signal.emit("success", "🎉 ¡Proceso completado exitosamente!")
            elif resumen['pdfs_procesados'] == 0:
                self.log_signal.emit("warning", "⚠️ No se procesó ningún archivo")
            else:
                self.log_signal.emit("warning", "⚠️ Proceso completado con algunos errores")
            
            self.finished_signal.emit(resultado)
            
        except Exception as e:
            log_exception(logger, e, "ejecución del worker Step 2")
            error_msg = f"Error durante el procesamiento: {str(e)}"
            self.log_signal.emit("error", f"❌ {error_msg}")
            self.error_signal.emit(error_msg)
    
    def _buscar_pdfs_por_tipo(self):
        """Busca PDFs en la carpeta madre y los clasifica por tipo"""
        pdfs_por_tipo = {tipo: [] for tipo in self.PALABRAS_CLAVE.keys()}
        pdfs_no_clasificados = []
        
        if not os.path.exists(self.folder_path):
            logger.error(f"Carpeta no existe: {self.folder_path}")
            self.log_signal.emit("error", f"❌ Carpeta no existe: {self.folder_path}")
            return pdfs_por_tipo, pdfs_no_clasificados
        
        # Buscar todos los archivos PDF
        archivos_pdf = [f for f in os.listdir(self.folder_path) 
                       if f.lower().endswith('.pdf') and os.path.isfile(os.path.join(self.folder_path, f))]
        
        logger.info(f"Encontrados {len(archivos_pdf)} archivos PDF")
        self.log_signal.emit("info", f"📄 Encontrados {len(archivos_pdf)} archivo(s) PDF en carpeta madre")
        
        for archivo in archivos_pdf:
            nombre_lower = archivo.lower()
            asignado = False
            
            for tipo, palabras in self.PALABRAS_CLAVE.items():
                for palabra in palabras:
                    if palabra in nombre_lower:
                        pdfs_por_tipo[tipo].append(archivo)
                        logger.debug(f"'{archivo}' → {tipo}")
                        self.log_signal.emit("info", f"  ✅ '{archivo}' → {tipo}")
                        asignado = True
                        break
                if asignado:
                    break
            
            if not asignado:
                pdfs_no_clasificados.append(archivo)
                logger.debug(f"No clasificado: '{archivo}'")
                self.log_signal.emit("warning", f"  ⚠️ No clasificado: '{archivo}'")
        
        return pdfs_por_tipo, pdfs_no_clasificados
    
    def _validar_unico_archivo_por_tipo(self, pdfs_por_tipo):
        """Valida que haya solo un archivo PDF por cada tipo"""
        tipos_problematicos = []
        
        for tipo, archivos in pdfs_por_tipo.items():
            if len(archivos) > 1:
                tipos_problematicos.append((tipo, archivos))
                logger.error(f"Múltiples archivos para {tipo}: {len(archivos)}")
                self.log_signal.emit("error", f"❌ Múltiples archivos para {tipo}: {len(archivos)} encontrados")
        
        if tipos_problematicos:
            self.log_signal.emit("error", "")
            self.log_signal.emit("error", "❌ ERROR: Múltiples archivos por tipo")
            for tipo, archivos in tipos_problematicos:
                self.log_signal.emit("error", f"  {tipo}:")
                for archivo in archivos:
                    self.log_signal.emit("error", f"    • {archivo}")
            self.log_signal.emit("error", "Solo se permite un archivo por tipo")
            return False
        
        return True
    
    def _dividir_pdf(self, ruta_pdf, carpeta_destino, nombre_base):
        """Divide un PDF en páginas individuales"""
        try:
            logger.debug(f"Iniciando división de: {os.path.basename(ruta_pdf)}")
            
            # Verificar que el PDF existe
            if not os.path.exists(ruta_pdf):
                logger.error(f"Archivo no encontrado: {ruta_pdf}")
                return False, 0, f"Archivo no encontrado"
            
            # Leer PDF
            with open(ruta_pdf, 'rb') as file:
                reader = PdfReader(file)
                
                # Verificar si está encriptado
                if reader.is_encrypted:
                    logger.error(f"PDF protegido con contraseña: {os.path.basename(ruta_pdf)}")
                    return False, 0, f"PDF protegido con contraseña"
                
                num_paginas = len(reader.pages)
                logger.info(f"Dividiendo {num_paginas} páginas...")
                self.log_signal.emit("info", f"  📄 Dividiendo {num_paginas} páginas...")
                
                # Crear carpeta destino si no existe
                os.makedirs(carpeta_destino, exist_ok=True)
                
                # Dividir en páginas individuales
                paginas_procesadas = 0
                for i, page in enumerate(reader.pages):
                    if not self._is_running:
                        logger.warning("División cancelada")
                        return False, paginas_procesadas, "Proceso cancelado"
                    
                    # Crear nombre de archivo
                    nombre_archivo = f"{nombre_base}_{i+1}.pdf"
                    ruta_salida = os.path.join(carpeta_destino, nombre_archivo)
                    
                    # Crear PDF de una sola página
                    writer = PdfWriter()
                    writer.add_page(page)
                    
                    # Guardar página individual
                    with open(ruta_salida, 'wb') as output_file:
                        writer.write(output_file)
                    
                    paginas_procesadas += 1
                    log_file_operation(logger, "crear", ruta_salida, success=True)
                    
                    # Emitir progreso cada 10 páginas
                    if paginas_procesadas % 10 == 0:
                        self.progress_signal.emit(paginas_procesadas, num_paginas)
                
                # Emitir progreso final
                self.progress_signal.emit(num_paginas, num_paginas)
                
                logger.info(f"✅ {paginas_procesadas} páginas creadas en {os.path.basename(carpeta_destino)}")
                self.log_signal.emit("success", f"  ✅ {paginas_procesadas} páginas creadas en {os.path.basename(carpeta_destino)}")
                return True, paginas_procesadas, None
                
        except PyPDF2.errors.PdfReadError as e:
            log_exception(logger, e, f"lectura de PDF {os.path.basename(ruta_pdf)}")
            return False, 0, f"Error al leer PDF: {str(e)}"
        except Exception as e:
            log_exception(logger, e, f"división de PDF {os.path.basename(ruta_pdf)}")
            return False, 0, f"Error inesperado: {str(e)}"
    
    def stop(self):
        """Detiene el worker"""
        logger.info("Solicitando detención del worker Step 2")
        self._is_running = False