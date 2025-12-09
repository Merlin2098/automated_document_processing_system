"""
PDF Splitter Worker - Worker thread para dividir PDFs sin bloquear la UI
"""
from PySide6.QtCore import QThread, Signal
import os
from datetime import datetime


class PdfSplitterWorker(QThread):
    """Worker para dividir PDFs en segundo plano"""
    
    # Señales
    log_message = Signal(str, str)  # (tipo, mensaje)
    progress_updated = Signal(int, int)  # (current, total)
    finished = Signal(dict)  # resultado final
    error = Signal(str)  # mensaje de error
    
    def __init__(self, pdf_path: str, pages_per_file: int):
        super().__init__()
        self.pdf_path = pdf_path
        self.pages_per_file = pages_per_file
        self._is_running = True
    
    def run(self):
        """Ejecuta el proceso de división"""
        start_time = datetime.now()
        
        try:
            # Importar aquí para evitar problemas de importación circular
            from PyPDF2 import PdfReader, PdfWriter
            
            self.log_message.emit("info", "🔍 Validando PDF...")
            
            # Validar archivo
            if not os.path.exists(self.pdf_path):
                self.error.emit(f"El archivo no existe: {self.pdf_path}")
                return
            
            # Leer PDF y validar división
            with open(self.pdf_path, 'rb') as archivo_pdf:
                reader = PdfReader(archivo_pdf)
                total_pages = len(reader.pages)
            
            self.log_message.emit("info", f"📄 Total de páginas: {total_pages}")
            
            # Validar que sea divisible exactamente
            if total_pages % self.pages_per_file != 0:
                residuo = total_pages % self.pages_per_file
                error_msg = (
                    f"El total de páginas ({total_pages}) no es divisible exactamente "
                    f"por la cantidad deseada ({self.pages_per_file}). "
                    f"Residuo: {residuo} páginas."
                )
                self.error.emit(error_msg)
                return
            
            num_pdfs_to_generate = total_pages // self.pages_per_file
            self.log_message.emit("success", f"✅ Se generarán {num_pdfs_to_generate} archivos PDF")
            
            # Crear carpeta de salida
            directorio_pdf = os.path.dirname(self.pdf_path)
            base_dir_salida = os.path.join(directorio_pdf, "Archivos_Divididos")
            dir_salida = base_dir_salida
            contador = 1
            
            # Evitar sobrescribir carpetas previas
            while os.path.exists(dir_salida):
                dir_salida = f"{base_dir_salida}_{contador}"
                contador += 1
            
            os.makedirs(dir_salida, exist_ok=True)
            self.log_message.emit("info", f"📁 Carpeta de salida: {os.path.basename(dir_salida)}")
            
            # Procesar división
            self.log_message.emit("info", "🔄 Iniciando división de PDF...")
            pdfs_generados = 0
            
            with open(self.pdf_path, 'rb') as archivo_pdf:
                reader = PdfReader(archivo_pdf)
                
                for i in range(num_pdfs_to_generate):
                    if not self._is_running:
                        self.log_message.emit("warning", "⚠️ Proceso cancelado por el usuario")
                        return
                    
                    writer = PdfWriter()
                    inicio_pagina = i * self.pages_per_file
                    fin_pagina = inicio_pagina + self.pages_per_file
                    
                    # Añadir páginas al writer
                    for j in range(inicio_pagina, fin_pagina):
                        writer.add_page(reader.pages[j])
                    
                    # Guardar archivo
                    nombre_archivo = f"Output_{i + 1}.pdf"
                    ruta_salida = os.path.join(dir_salida, nombre_archivo)
                    
                    with open(ruta_salida, 'wb') as output_file:
                        writer.write(output_file)
                    
                    pdfs_generados += 1
                    
                    # Emitir progreso
                    self.progress_updated.emit(pdfs_generados, num_pdfs_to_generate)
                    self.log_message.emit("info", f"✓ Generado: {nombre_archivo}")
            
            # Calcular tiempo transcurrido
            elapsed_time = (datetime.now() - start_time).total_seconds()
            
            # Emitir resultado final
            resultado = {
                'success': True,
                'pdfs_generados': pdfs_generados,
                'carpeta_salida': dir_salida,
                'tiempo_transcurrido': elapsed_time,
                'errores': 0
            }
            
            self.log_message.emit("success", f"🎉 ¡Proceso completado exitosamente!")
            self.log_message.emit("info", f"📊 Total de archivos generados: {pdfs_generados}")
            self.log_message.emit("info", f"⏱️ Tiempo transcurrido: {elapsed_time:.2f}s")
            self.log_message.emit("info", f"📂 Ubicación: {dir_salida}")
            
            self.finished.emit(resultado)
            
        except Exception as e:
            error_msg = f"Error durante el procesamiento: {str(e)}"
            self.log_message.emit("error", f"❌ {error_msg}")
            self.error.emit(error_msg)
    
    def stop(self):
        """Detiene el worker"""
        self._is_running = False