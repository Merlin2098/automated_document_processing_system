"""
Worker para unir PDFs finales por contrato (Paso 5)
Ejecuta el proceso en segundo plano sin congelar la UI

COMPORTAMIENTO:
1. Copia PDFs de subcarpetas a carpeta temporal Documentos_Procesar
2. Analiza y agrupa archivos por número de contrato
3. Genera diagnóstico JSON
4. Fusiona PDFs por contrato (un pack por cada contrato único)
5. Guarda en carpeta Documentos_Enviar
"""
from PySide6.QtCore import QThread, Signal
from utils.logger import Logger
import os
import json
import shutil
import re
import time
from typing import Dict, List, Optional, Tuple


class CorePipelineStep5Worker(QThread):
    """Worker para unir PDFs por contrato en segundo plano"""
    
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
        
        # Subcarpetas a procesar (igual que core)
        self.SUBCARPETAS_ESPERADAS = [
            '1_Boletas',
            '2_Afp',
            '3_5ta',
            '4_Convocatoria',
            '5_CertificadosTrabajo'
        ]
    
    def run(self):
        """Ejecuta el proceso completo de fusión por contratos"""
        start_time = time.time()
        
        try:
            self.logger.info("🚀 Iniciando proceso de fusión por contratos")
            self.log_signal.emit("info", "🚀 Iniciando proceso de fusión por contratos")
            self.logger.info(f"📂 Carpeta madre: {self.folder_path}")
            self.log_signal.emit("info", f"📂 Carpeta madre: {self.folder_path}")
            
            # Validar carpeta madre
            if not os.path.isdir(self.folder_path):
                error_msg = f"La carpeta no existe: {self.folder_path}"
                self.logger.error(error_msg)
                self.error_signal.emit(error_msg)
                return
            
            # Verificar PyPDF2
            try:
                from PyPDF2 import PdfMerger
            except ImportError:
                error_msg = "PyPDF2 no está instalado. Instale con: pip install PyPDF2"
                self.logger.error(error_msg)
                self.error_signal.emit(error_msg)
                return
            
            # Generar timestamp único
            timestamp = time.strftime("%d.%m.%Y_%H.%M.%S")
            
            # FASE 1: Validar subcarpetas
            self.log_signal.emit("info", "")
            self.log_signal.emit("info", "📋 [1/5] Validando estructura...")
            self.logger.info("📋 [1/5] Validando estructura...")
            
            encontradas, faltantes = self._validar_subcarpetas()
            
            if not encontradas:
                error_msg = "No se encontró ninguna de las 5 subcarpetas esperadas"
                self.logger.error(error_msg)
                self.error_signal.emit(error_msg)
                return
            
            self.log_signal.emit("success", f"✅ Subcarpetas encontradas: {len(encontradas)}")
            self.logger.info(f"✅ Subcarpetas encontradas: {len(encontradas)}")
            
            if faltantes:
                msg = f"⚠️ Subcarpetas faltantes: {', '.join(faltantes)}"
                self.log_signal.emit("warning", msg)
                self.logger.warning(msg)
            
            # FASE 2: Copiar PDFs a carpeta de procesamiento
            self.log_signal.emit("info", "")
            self.log_signal.emit("info", "📋 [2/5] Copiando PDFs a carpeta temporal...")
            self.logger.info("📋 [2/5] Copiando PDFs a carpeta temporal...")
            
            ruta_procesar, copiados, errores_copia = self._copiar_pdfs_a_procesamiento(
                encontradas, timestamp
            )
            
            if not ruta_procesar:
                error_msg = "Error al crear carpeta de procesamiento"
                self.logger.error(error_msg)
                self.error_signal.emit(error_msg)
                return
            
            self.log_signal.emit("success", f"✅ PDFs copiados: {copiados}")
            self.logger.info(f"✅ PDFs copiados: {copiados}")
            
            if errores_copia > 0:
                msg = f"⚠️ Errores durante copia: {errores_copia}"
                self.log_signal.emit("warning", msg)
                self.logger.warning(msg)
            
            # FASE 3: Generar diagnóstico de contratos
            self.log_signal.emit("info", "")
            self.log_signal.emit("info", "📋 [3/5] Analizando contratos...")
            self.logger.info("📋 [3/5] Analizando contratos...")
            
            diagnostico = self._generar_diagnostico(ruta_procesar, timestamp)
            
            if diagnostico['total_contratos_unicos'] == 0:
                error_msg = "No se encontraron contratos válidos para procesar"
                self.logger.error(error_msg)
                self.error_signal.emit(error_msg)
                return
            
            self.log_signal.emit("success", f"✅ Contratos únicos: {diagnostico['total_contratos_unicos']}")
            self.log_signal.emit("info", f"📄 Total archivos: {diagnostico['total_archivos']}")
            self.logger.info(f"✅ Contratos únicos: {diagnostico['total_contratos_unicos']}")
            self.logger.info(f"📄 Total archivos: {diagnostico['total_archivos']}")
            
            # Guardar diagnóstico
            self._guardar_diagnostico(diagnostico, ruta_procesar, timestamp)
            
            # FASE 4: Generar packs documentarios
            self.log_signal.emit("info", "")
            self.log_signal.emit("info", "📋 [4/5] Generando packs por contrato...")
            self.logger.info("📋 [4/5] Generando packs por contrato...")
            
            ruta_enviar, packs_generados, errores_fusion = self._generar_packs_documentales(
                ruta_procesar, diagnostico, timestamp, PdfMerger
            )
            
            if not ruta_enviar:
                error_msg = "Error al generar packs documentarios"
                self.logger.error(error_msg)
                self.error_signal.emit(error_msg)
                return
            
            # FASE 5: Resumen final
            elapsed_time = time.time() - start_time
            
            self.log_signal.emit("info", "")
            self.log_signal.emit("info", "=" * 50)
            self.log_signal.emit("info", "📊 RESUMEN FINAL")
            self.log_signal.emit("success", f"✅ Packs generados: {packs_generados}")
            self.log_signal.emit("info", f"📂 Carpeta salida: {os.path.basename(ruta_enviar)}")
            
            if errores_fusion > 0:
                self.log_signal.emit("error", f"❌ Errores: {errores_fusion}")
            
            self.log_signal.emit("info", f"⏱️ Tiempo total: {elapsed_time:.2f}s")
            self.log_signal.emit("info", "=" * 50)
            
            # Log archivo
            self.logger.info("=" * 50)
            self.logger.info("📊 RESUMEN FINAL")
            self.logger.info(f"✅ Packs generados: {packs_generados}")
            self.logger.info(f"📂 Carpeta salida: {os.path.basename(ruta_enviar)}")
            if errores_fusion > 0:
                self.logger.error(f"❌ Errores: {errores_fusion}")
            self.logger.info(f"⏱️ Tiempo total: {elapsed_time:.2f}s")
            self.logger.info("=" * 50)
            
            # Emitir estadísticas
            stats = {
                'contratos_unicos': diagnostico['total_contratos_unicos'],
                'archivos_procesados': diagnostico['total_archivos'],
                'packs_generados': packs_generados,
                'errores': errores_fusion,
                'carpeta_enviar': ruta_enviar,
                'carpeta_procesar': ruta_procesar,
                'time': elapsed_time
            }
            self.stats_signal.emit(stats)
            
            # Emitir resultado final
            resultado = {
                'success': True,
                'stats': stats,
                'diagnostico': diagnostico,
                'ruta_enviar': ruta_enviar
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
    
    def _validar_subcarpetas(self) -> Tuple[List[str], List[str]]:
        """
        Valida existencia de subcarpetas esperadas.
        
        Returns:
            Tupla (encontradas, faltantes)
        """
        encontradas = []
        faltantes = []
        
        for subcarpeta in self.SUBCARPETAS_ESPERADAS:
            ruta_completa = os.path.join(self.folder_path, subcarpeta)
            if os.path.exists(ruta_completa) and os.path.isdir(ruta_completa):
                encontradas.append(subcarpeta)
            else:
                faltantes.append(subcarpeta)
        
        return encontradas, faltantes
    
    def _copiar_pdfs_a_procesamiento(self, subcarpetas: List[str], 
                                     timestamp: str) -> Tuple[str, int, int]:
        """
        Copia todos los PDFs a carpeta Documentos_Procesar.
        
        Returns:
            Tupla (ruta_carpeta_procesar, archivos_copiados, errores)
        """
        # Crear carpeta Documentos_Procesar
        nombre_carpeta = f"Documentos_Procesar_{timestamp}"
        ruta_procesar = os.path.join(self.folder_path, nombre_carpeta)
        
        try:
            os.makedirs(ruta_procesar, exist_ok=True)
            self.logger.info(f"Carpeta creada: {nombre_carpeta}")
        except Exception as e:
            self.logger.error(f"Error al crear carpeta: {e}")
            return "", 0, 0
        
        archivos_copiados = 0
        errores = 0
        total_subcarpetas = len(subcarpetas)
        
        for idx, subcarpeta in enumerate(subcarpetas, 1):
            if not self._is_running:
                self.logger.warning("Proceso cancelado por el usuario")
                return "", archivos_copiados, errores
            
            ruta_subcarpeta = os.path.join(self.folder_path, subcarpeta)
            pdfs = self._escanear_pdfs_subcarpeta(ruta_subcarpeta)
            
            self.log_signal.emit("info", f"  📁 {subcarpeta}: {len(pdfs)} PDFs")
            self.logger.info(f"  📁 {subcarpeta}: {len(pdfs)} PDFs")
            
            for pdf in pdfs:
                origen = os.path.join(ruta_subcarpeta, pdf)
                destino = os.path.join(ruta_procesar, pdf)
                
                try:
                    shutil.copy2(origen, destino)
                    archivos_copiados += 1
                except Exception as e:
                    self.logger.error(f"Error copiando '{pdf}': {e}")
                    errores += 1
            
            # Actualizar progreso
            self.progress_signal.emit(idx, total_subcarpetas * 3)  # 3 fases por carpeta
        
        return ruta_procesar, archivos_copiados, errores
    
    def _escanear_pdfs_subcarpeta(self, ruta_subcarpeta: str) -> List[str]:
        """
        Escanea subcarpeta y retorna solo archivos PDF.
        
        Returns:
            Lista de nombres de archivos PDF
        """
        try:
            archivos = os.listdir(ruta_subcarpeta)
            pdfs = [
                f for f in archivos 
                if f.lower().endswith('.pdf') and not f.lower().endswith('.json')
            ]
            return pdfs
        except Exception as e:
            self.logger.error(f"Error al escanear subcarpeta: {e}")
            return []
    
    def _extraer_identificador_contrato(self, nombre_archivo: str) -> Optional[str]:
        """
        Extrae número de contrato del nombre de archivo.
        Formato esperado: NUMERO_CATEGORIA.pdf
        
        Returns:
            Identificador (número de contrato) o None
        """
        # Regex para parsing robusto
        match = re.match(r'^(.+?)_(.+?)\.pdf$', nombre_archivo, re.IGNORECASE)
        if not match:
            return None
        
        parte_antes_guion = match.group(1)
        
        # Extraer solo el número de contrato (primeros dígitos)
        match_numero = re.match(r'^(\d+)', parte_antes_guion)
        if not match_numero:
            return None
        
        return match_numero.group(1)
    
    def _generar_diagnostico(self, ruta_procesar: str, timestamp: str) -> Dict:
        """
        Analiza carpeta y genera diagnóstico de contratos.
        
        Returns:
            Diccionario con estructura del diagnóstico
        """
        diagnostico = {
            'timestamp': timestamp,
            'carpeta_procesamiento': os.path.basename(ruta_procesar),
            'total_contratos_unicos': 0,
            'total_archivos': 0,
            'contratos': {}
        }
        
        try:
            archivos = os.listdir(ruta_procesar)
            pdfs = [f for f in archivos if f.lower().endswith('.pdf')]
            
            # Analizar cada PDF
            for pdf in pdfs:
                identificador = self._extraer_identificador_contrato(pdf)
                
                if not identificador:
                    self.logger.warning(f"No se pudo extraer contrato de: {pdf}")
                    continue
                
                # Inicializar contrato si no existe
                if identificador not in diagnostico['contratos']:
                    diagnostico['contratos'][identificador] = {
                        'archivos': [],
                        'cantidad_total': 0,
                        'nombre_pack': None
                    }
                
                # Agregar archivo al contrato
                diagnostico['contratos'][identificador]['archivos'].append(pdf)
                diagnostico['contratos'][identificador]['cantidad_total'] += 1
                diagnostico['total_archivos'] += 1
                
                # Si es boleta, usar como nombre del pack
                if 'BOLETA DE PAGO Y CERTIFICADOS' in pdf.upper():
                    # Extraer nombre sin extensión
                    nombre_base = os.path.splitext(pdf)[0]
                    diagnostico['contratos'][identificador]['nombre_pack'] = nombre_base
            
            diagnostico['total_contratos_unicos'] = len(diagnostico['contratos'])
            
        except Exception as e:
            self.logger.error(f"Error generando diagnóstico: {e}")
        
        return diagnostico
    
    def _guardar_diagnostico(self, diagnostico: Dict, ruta_procesar: str, timestamp: str):
        """Guarda diagnóstico en archivo JSON"""
        try:
            nombre_json = f"diagnostico_merge_{timestamp}.json"
            ruta_json = os.path.join(ruta_procesar, nombre_json)
            
            with open(ruta_json, 'w', encoding='utf-8') as f:
                json.dump(diagnostico, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Diagnóstico guardado: {nombre_json}")
            self.log_signal.emit("success", f"✅ Diagnóstico guardado: {nombre_json}")
        except Exception as e:
            self.logger.error(f"Error guardando diagnóstico: {e}")
    
    def _generar_packs_documentales(self, ruta_procesar: str, diagnostico: Dict, 
                                   timestamp: str, PdfMerger) -> Tuple[str, int, int]:
        """
        Genera packs documentarios fusionando PDFs por contrato.
        
        Returns:
            Tupla (ruta_enviar, packs_generados, errores)
        """
        # Crear carpeta Documentos_Enviar DENTRO de Documentos_Procesar
        nombre_carpeta = f"Documentos_Enviar_{timestamp}"
        ruta_enviar = os.path.join(ruta_procesar, nombre_carpeta)
        
        try:
            os.makedirs(ruta_enviar, exist_ok=True)
            self.logger.info(f"Carpeta creada: {nombre_carpeta}")
        except Exception as e:
            self.logger.error(f"Error al crear carpeta de envío: {e}")
            return "", 0, 0
        
        packs_generados = 0
        errores = 0
        total_contratos = diagnostico['total_contratos_unicos']
        
        for idx, (identificador, info) in enumerate(diagnostico['contratos'].items(), 1):
            if not self._is_running:
                self.logger.warning("Proceso cancelado por el usuario")
                break
            
            # Usar nombre_pack si existe (nombre de boleta), sino usar Pack_{identificador}
            nombre_pack = info['nombre_pack'] if info['nombre_pack'] else f"Pack_{identificador}"
            
            msg = f"  📦 [{idx}/{total_contratos}] {nombre_pack} ({info['cantidad_total']} docs)"
            self.log_signal.emit("info", msg)
            self.logger.info(msg)
            
            # Fusionar PDFs del contrato
            exito = self._fusionar_pdfs_contrato(
                info['archivos'],
                ruta_procesar,
                nombre_pack,
                ruta_enviar,
                PdfMerger
            )
            
            if exito:
                packs_generados += 1
                self.log_signal.emit("success", "     ✅ Pack generado")
                self.logger.info("     ✅ Pack generado")
            else:
                errores += 1
                self.log_signal.emit("error", "     ❌ Error en pack")
                self.logger.error("     ❌ Error en pack")
            
            # Actualizar progreso (fase 4 de 5)
            progreso_actual = len(self.SUBCARPETAS_ESPERADAS) * 3 + idx
            progreso_total = len(self.SUBCARPETAS_ESPERADAS) * 3 + total_contratos
            self.progress_signal.emit(progreso_actual, progreso_total)
        
        return ruta_enviar, packs_generados, errores
    
    def _fusionar_pdfs_contrato(self, archivos: List[str], ruta_procesar: str,
                               nombre_pack: str, ruta_enviar: str, 
                               PdfMerger) -> bool:
        """
        Fusiona todos los PDFs de un contrato en un único pack.
        
        Args:
            nombre_pack: Nombre base del pack (sin extensión si viene de boleta)
        
        Returns:
            True si tuvo éxito, False en caso contrario
        """
        try:
            merger = PdfMerger()
            
            # Agregar cada PDF al merger (ordenados alfabéticamente)
            for archivo in sorted(archivos):
                ruta_pdf = os.path.join(ruta_procesar, archivo)
                
                try:
                    merger.append(ruta_pdf)
                except Exception as e:
                    self.logger.warning(f"Error agregando {archivo}: {e}")
                    continue
            
            # Asegurar extensión .pdf en el nombre final
            if not nombre_pack.lower().endswith('.pdf'):
                nombre_pack_final = f"{nombre_pack}.pdf"
            else:
                nombre_pack_final = nombre_pack
            
            # Guardar pack fusionado
            ruta_salida = os.path.join(ruta_enviar, nombre_pack_final)
            merger.write(ruta_salida)
            merger.close()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error fusionando pack {nombre_pack}: {e}")
            return False
    
    def stop(self):
        """Detiene el worker"""
        self._is_running = False
        self.logger.warning("ℹ️ Worker detenido por el usuario")