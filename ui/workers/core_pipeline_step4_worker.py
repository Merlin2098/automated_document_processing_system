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
            
            # Procesar carpetas (cada una tiene su propio JSON)
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
                
                # Procesar la carpeta (busca su propio JSON)
                stats = self._procesar_carpeta(ruta_subcarpeta, nombre_carpeta)
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
            self.logger.warning(f"⭕️ Archivos omitidos: {total_omitidos}")
            self.logger.error(f"❌ Errores: {total_errores}")
            self.logger.info(f"⏱️ Tiempo transcurrido: {elapsed_time:.2f}s")
            self.logger.info("=" * 50)
            
            self.log_signal.emit("info", "")
            self.log_signal.emit("info", "=" * 50)
            self.log_signal.emit("info", "📊 RESUMEN DEL RENOMBRADO")
            self.log_signal.emit("success", f"✅ Archivos renombrados: {total_renombrados}")
            self.log_signal.emit("warning", f"⭕️ Archivos omitidos: {total_omitidos}")
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
    
    def _buscar_json_en_carpeta(self, ruta_carpeta):
        """
        Busca el primer archivo JSON en la carpeta especificada.
        Imita el comportamiento del módulo core 4_rename.py
        
        Returns:
            str: Ruta completa al JSON encontrado, o None si no hay
        """
        try:
            archivos_json = [f for f in os.listdir(ruta_carpeta) if f.lower().endswith('.json')]
            
            if not archivos_json:
                return None
            
            if len(archivos_json) > 1:
                msg = f"⚠️ Múltiples JSON encontrados: {archivos_json}, usando: {archivos_json[0]}"
                self.logger.warning(msg)
                self.log_signal.emit("warning", msg)
            
            json_path = os.path.join(ruta_carpeta, archivos_json[0])
            return json_path
            
        except Exception as e:
            self.logger.error(f"Error al buscar JSON: {str(e)}")
            return None
    
    def _cargar_json(self, json_path):
        """
        Carga y valida el JSON de renombrado.
        Maneja múltiples encodings como el módulo core.
        
        Returns:
            dict: Mapeo {archivo_original: nuevo_nombre} o None si falla
        """
        try:
            import json
            
            # Probar múltiples encodings
            encodings = ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252']
            data = None
            
            for encoding in encodings:
                try:
                    with open(json_path, 'r', encoding=encoding) as f:
                        data = json.load(f)
                    self.logger.info(f"✅ JSON cargado con encoding: {encoding}")
                    break
                except UnicodeDecodeError:
                    continue
                except json.JSONDecodeError as e:
                    self.logger.error(f"Error en estructura JSON: {e}")
                    return None
            
            if data is None:
                self.logger.error("No se pudo leer el JSON con ningún encoding")
                return None
            
            # Convertir a mapeo (como hace el core)
            if isinstance(data, list):
                # Formato lista de diccionarios con "ARCHIVO ORIGINAL" y "NUEVO NOMBRE"
                mapeo = self._convertir_lista_a_mapeo(data)
            elif isinstance(data, dict):
                # Formato directo {original: nuevo}
                mapeo = data
            else:
                self.logger.error(f"Formato JSON inesperado: {type(data).__name__}")
                return None
            
            msg = f"✅ {len(mapeo)} registros de renombrado cargados"
            self.logger.info(msg)
            self.log_signal.emit("success", msg)
            
            return mapeo
            
        except Exception as e:
            self.logger.error(f"Error al cargar JSON: {str(e)}")
            return None
    
    def _convertir_lista_a_mapeo(self, datos_json):
        """
        Convierte lista de diccionarios a mapeo directo.
        Réplica del comportamiento del core.
        """
        mapeo = {}
        duplicados = {}
        
        for idx, item in enumerate(datos_json):
            if not isinstance(item, dict):
                continue
            
            archivo_original = item.get("ARCHIVO ORIGINAL")
            nuevo_nombre = item.get("NUEVO NOMBRE")
            
            if not archivo_original or not nuevo_nombre:
                continue
            
            # Detectar duplicados
            if archivo_original in mapeo:
                if archivo_original not in duplicados:
                    duplicados[archivo_original] = [mapeo[archivo_original]]
                duplicados[archivo_original].append(nuevo_nombre)
            
            # Guardar (sobrescribe si hay duplicados)
            mapeo[archivo_original] = nuevo_nombre
        
        # Reportar duplicados
        if duplicados:
            msg = f"⚠️ {len(duplicados)} archivos con múltiples nombres (se usa la última ocurrencia)"
            self.logger.warning(msg)
            self.log_signal.emit("warning", msg)
        
        return mapeo
    
    def _procesar_carpeta(self, ruta_carpeta, nombre_carpeta):
        """
        Procesa todos los PDFs en una carpeta.
        Busca el JSON dentro de la misma carpeta.
        """
        stats = {
            'renombrados': 0,
            'errores': 0,
            'omitidos': 0
        }
        
        self.logger.info(f"📂 Procesando: {nombre_carpeta}")
        self.log_signal.emit("info", "")
        self.log_signal.emit("info", f"📂 Procesando: {nombre_carpeta}")
        
        # Buscar JSON en esta carpeta
        json_path = self._buscar_json_en_carpeta(ruta_carpeta)
        
        if not json_path:
            msg = f"⚠️ No se encontró JSON en '{nombre_carpeta}', omitiendo..."
            self.logger.warning(msg)
            self.log_signal.emit("warning", msg)
            return stats
        
        nombre_json = os.path.basename(json_path)
        msg = f"✅ JSON encontrado: {nombre_json}"
        self.logger.info(msg)
        self.log_signal.emit("success", msg)
        
        # Cargar mapeo de renombrado
        rename_data = self._cargar_json(json_path)
        
        if not rename_data:
            msg = f"❌ Error al cargar JSON de '{nombre_carpeta}'"
            self.logger.error(msg)
            self.log_signal.emit("error", msg)
            return stats
        
        # Obtener archivos PDF
        archivos_pdf = [f for f in os.listdir(ruta_carpeta) 
                       if f.lower().endswith('.pdf')]
        
        self.logger.info(f"   📄 PDFs encontrados: {len(archivos_pdf)}")
        self.log_signal.emit("info", f"   📄 PDFs encontrados: {len(archivos_pdf)}")
        
        # Renombrar archivos
        for archivo in archivos_pdf:
            if not self._is_running:
                break
            
            # Verificar si está en el mapeo
            if archivo not in rename_data:
                stats['omitidos'] += 1
                continue
            
            nuevo_nombre = rename_data[archivo]
            
            # Si es el mismo nombre, omitir
            if archivo == nuevo_nombre:
                stats['omitidos'] += 1
                continue
            
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