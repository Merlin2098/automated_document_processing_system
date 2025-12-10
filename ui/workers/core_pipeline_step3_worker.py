"""
Worker para generar diagnóstico de datos (Paso 3)
Ejecuta el proceso en segundo plano sin congelar la UI
"""
from PySide6.QtCore import QThread, Signal
from utils.logger import Logger
import os
import sys
import time


class CorePipelineStep3Worker(QThread):
    """Worker para generar diagnóstico en segundo plano"""
    
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
        self.logger = Logger("CorePipelineStep3")
        
        # Configuración de carpetas y tipos
        self.CARPETAS_CONFIG = {
            "1_Boletas": {
                "tipo": "BOLETA",
                "extractor": None,  # Se cargará dinámicamente
                "campos_extra": ["fecha_extraida"]
            },
            "2_Afp": {
                "tipo": "AFP",
                "extractor": None,
                "campos_extra": []
            },
            "3_5ta": {
                "tipo": "QUINTA",
                "extractor": None,
                "campos_extra": []
            }
        }
    
    def run(self):
        """Ejecuta el proceso de generación de diagnóstico"""
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
            
            # Importar extractores
            if not self._cargar_extractores():
                error_msg = "Error al cargar extractores"
                self.logger.error(error_msg)
                self.error_signal.emit(error_msg)
                return
            
            # Procesar carpetas
            datos_por_hoja = {}
            
            # Contadores para progreso por carpeta
            total_carpetas = len([k for k, v in self.CARPETAS_CONFIG.items()])
            carpeta_actual = 0
            
            for nombre_carpeta, config in self.CARPETAS_CONFIG.items():
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
                
                registros = self._procesar_carpeta(ruta_subcarpeta, config)
                datos_por_hoja[nombre_carpeta] = registros
                
                # Emitir progreso por carpeta completada
                carpeta_actual += 1
                self.progress_signal.emit(carpeta_actual, total_carpetas)
            
            if not datos_por_hoja:
                error_msg = "No se procesó ninguna carpeta"
                self.logger.error(error_msg)
                self.error_signal.emit(error_msg)
                return
            
            # Generar Excel
            self.logger.info("📊 Generando archivo Excel...")
            self.log_signal.emit("info", "")
            self.log_signal.emit("info", "📊 Generando archivo Excel...")
            
            timestamp = time.strftime("%d.%m.%Y_%H.%M.%S")
            nombre_excel = f"diagnostico_consolidado_{timestamp}.xlsx"
            ruta_excel = os.path.join(self.folder_path, nombre_excel)
            
            if not self._generar_excel_multihoja(datos_por_hoja, ruta_excel):
                error_msg = "Error al generar archivo Excel"
                self.logger.error(error_msg)
                self.error_signal.emit(error_msg)
                return
            
            # Calcular tiempo transcurrido
            elapsed_time = time.time() - start_time
            
            # Calcular estadísticas totales
            total_archivos = sum(len(registros) for registros in datos_por_hoja.values())
            exitosos = sum(1 for registros in datos_por_hoja.values() 
                          for r in registros if r.get("exito_extraccion"))
            
            # Mostrar resumen
            self.logger.info("=" * 50)
            self.logger.info("📊 RESUMEN DEL DIAGNÓSTICO")
            self.logger.info(f"📄 Total archivos procesados: {total_archivos}")
            self.logger.info(f"✅ Extracciones exitosas: {exitosos}")
            self.logger.error(f"❌ Errores: {total_archivos - exitosos}")
            self.logger.info(f"📁 Excel generado: {nombre_excel}")
            self.logger.info(f"⏱️ Tiempo transcurrido: {elapsed_time:.2f}s")
            self.logger.info("=" * 50)
            
            self.log_signal.emit("info", "")
            self.log_signal.emit("info", "=" * 50)
            self.log_signal.emit("info", "📊 RESUMEN DEL DIAGNÓSTICO")
            self.log_signal.emit("info", f"📄 Total archivos procesados: {total_archivos}")
            self.log_signal.emit("success", f"✅ Extracciones exitosas: {exitosos}")
            self.log_signal.emit("error", f"❌ Errores: {total_archivos - exitosos}")
            self.log_signal.emit("info", f"📁 Excel generado: {nombre_excel}")
            self.log_signal.emit("info", f"⏱️ Tiempo transcurrido: {elapsed_time:.2f}s")
            self.log_signal.emit("info", "=" * 50)
            
            # Emitir estadísticas
            stats = {
                'total_archivos': total_archivos,
                'exitosos': exitosos,
                'errores': total_archivos - exitosos,
                'time': elapsed_time
            }
            self.stats_signal.emit(stats)
            
            # Emitir resultado final
            resultado = {
                'success': True,
                'excel_path': ruta_excel,
                'stats': stats,
                'tiempo_transcurrido': elapsed_time
            }
            
            self.logger.info("🎉 ¡Diagnóstico completado exitosamente!")
            self.log_signal.emit("success", "🎉 ¡Diagnóstico completado exitosamente!")
            self.finished_signal.emit(resultado)
            
        except Exception as e:
            error_msg = f"Error durante el diagnóstico: {str(e)}"
            self.logger.error(error_msg)
            self.log_signal.emit("error", f"❌ {error_msg}")
            import traceback
            self.logger.error(traceback.format_exc())
            self.error_signal.emit(error_msg)
    
    def _cargar_extractores(self):
        """Carga dinámicamente los extractores"""
        try:
            # Agregar directorio padre al path
            current_dir = os.path.dirname(os.path.abspath(__file__))
            parent_dir = os.path.dirname(os.path.dirname(current_dir))
            if parent_dir not in sys.path:
                sys.path.insert(0, parent_dir)
            
            from extractores.extractor_boleta import extraer_datos_boleta
            from extractores.extractor_afp import extraer_datos_afp
            from extractores.extractor_quinta import extraer_datos_quinta
            
            self.CARPETAS_CONFIG["1_Boletas"]["extractor"] = extraer_datos_boleta
            self.CARPETAS_CONFIG["2_Afp"]["extractor"] = extraer_datos_afp
            self.CARPETAS_CONFIG["3_5ta"]["extractor"] = extraer_datos_quinta
            
            self.logger.info("✅ Extractores cargados correctamente")
            self.log_signal.emit("success", "✅ Extractores cargados correctamente")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error al cargar extractores: {str(e)}")
            self.log_signal.emit("error", f"❌ Error al cargar extractores: {str(e)}")
            return False
    
    def _procesar_carpeta(self, ruta_carpeta, config):
        """Procesa todos los PDFs en una carpeta y genera registros"""
        registros = []
        tipo_documento = config["tipo"]
        extractor = config["extractor"]
        
        archivos_pdf = [f for f in os.listdir(ruta_carpeta) if f.lower().endswith('.pdf')]
        
        self.logger.info(f"📂 Procesando: {os.path.basename(ruta_carpeta)}")
        self.logger.info(f"   Tipo: {tipo_documento}")
        self.logger.info(f"   PDFs: {len(archivos_pdf)}")
        
        self.log_signal.emit("info", "")
        self.log_signal.emit("info", f"📂 Procesando: {os.path.basename(ruta_carpeta)}")
        self.log_signal.emit("info", f"   Tipo: {tipo_documento}")
        self.log_signal.emit("info", f"   PDFs: {len(archivos_pdf)}")
        
        for idx, archivo in enumerate(archivos_pdf, 1):
            if not self._is_running:
                break
            
            ruta_completa = os.path.join(ruta_carpeta, archivo)
            resultado = extractor(ruta_completa)
            
            registro = {
                "archivo_original": archivo,
                "tipo_documento": tipo_documento,
                "nombre_extraido": resultado.get("nombre"),
                "dni_extraido": resultado.get("dni"),
                "exito_extraccion": resultado.get("exito", False),
                "observaciones": resultado.get("observaciones", "")
            }
            
            if "fecha" in resultado and resultado["fecha"]:
                registro["fecha_extraida"] = resultado["fecha"]
            
            registros.append(registro)
            
            # Mostrar progreso cada 100 archivos
            if idx % 100 == 0:
                msg = f"   Procesados: {idx}/{len(archivos_pdf)}"
                self.logger.info(msg)
                self.log_signal.emit("info", msg)
        
        exitosos = sum(1 for r in registros if r["exito_extraccion"])
        msg = f"   ✅ Completado: {len(registros)} archivos ({exitosos} exitosos)"
        self.logger.info(msg)
        self.log_signal.emit("success", msg)
        
        return registros
    
    def _generar_excel_multihoja(self, datos_por_hoja, ruta_excel):
        """Genera Excel con múltiples hojas"""
        try:
            import openpyxl
            from openpyxl.styles import Font, PatternFill, Alignment
            
            wb = openpyxl.Workbook()
            wb.remove(wb.active)
            
            header_font = Font(bold=True, color="FFFFFF")
            header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
            header_alignment = Alignment(horizontal="center", vertical="center")
            
            for nombre_hoja, registros in datos_por_hoja.items():
                ws = wb.create_sheet(title=nombre_hoja)
                if not registros:
                    continue
                
                encabezados = list(registros[0].keys())
                for col_idx, encabezado in enumerate(encabezados, 1):
                    cell = ws.cell(row=1, column=col_idx)
                    cell.value = encabezado.replace("_", " ").upper()
                    cell.font = header_font
                    cell.fill = header_fill
                    cell.alignment = header_alignment
                
                for row_idx, registro in enumerate(registros, 2):
                    for col_idx, encabezado in enumerate(encabezados, 1):
                        valor = registro.get(encabezado, "")
                        cell = ws.cell(row=row_idx, column=col_idx)
                        cell.value = valor
                        
                        if encabezado in ["tipo_documento", "exito_extraccion", "dni_extraido"]:
                            cell.alignment = Alignment(horizontal="center")
                        
                        if encabezado == "exito_extraccion":
                            if valor:
                                cell.fill = PatternFill(start_color="C6EFCE", end_color="C6EFCE", fill_type="solid")
                            else:
                                cell.fill = PatternFill(start_color="FFC7CE", end_color="FFC7CE", fill_type="solid")
                
                # Ajustar anchos de columna
                for col_idx, encabezado in enumerate(encabezados, 1):
                    column_letter = openpyxl.utils.get_column_letter(col_idx)
                    if encabezado == "archivo_original":
                        ws.column_dimensions[column_letter].width = 40
                    elif encabezado == "observaciones":
                        ws.column_dimensions[column_letter].width = 35
                    elif encabezado == "nombre_extraido":
                        ws.column_dimensions[column_letter].width = 30
                    elif encabezado == "tipo_documento":
                        ws.column_dimensions[column_letter].width = 15
                    elif encabezado == "dni_extraido":
                        ws.column_dimensions[column_letter].width = 12
                    elif encabezado == "fecha_extraida":
                        ws.column_dimensions[column_letter].width = 15
                    elif encabezado == "exito_extraccion":
                        ws.column_dimensions[column_letter].width = 18
                    else:
                        ws.column_dimensions[column_letter].width = 20
                
                ws.freeze_panes = "A2"
            
            wb.save(ruta_excel)
            msg = f"   ✅ Excel guardado: {os.path.basename(ruta_excel)}"
            self.logger.info(msg)
            self.log_signal.emit("success", msg)
            return True
            
        except Exception as e:
            error_msg = f"   ❌ Error al generar Excel: {e}"
            self.logger.error(error_msg)
            self.log_signal.emit("error", error_msg)
            import traceback
            self.logger.error(traceback.format_exc())
            return False
    
    def stop(self):
        """Detiene el worker"""
        self._is_running = False
        self.logger.warning("⏹️ Worker detenido por el usuario")