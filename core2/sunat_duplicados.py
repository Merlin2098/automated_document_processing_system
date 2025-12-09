import os
import re
from typing import Optional, Dict, List, Tuple
from collections import defaultdict
from tkinter import Tk, filedialog
import time

# ============================================================
# CONFIGURACIÓN
# ============================================================
# Detecta número de contrato al inicio del nombre (ej: "9728 CAMPOS...")
PATRON_CONTRATO = re.compile(r'^(\d+)\s')


# ============================================================
# CLASE: Analizador de Duplicados
# ============================================================
class DuplicateAnalyzer:
    """Analiza archivos y detecta duplicados por número de contrato."""
    
    def __init__(self, folder_path):
        """
        Inicializa el analizador.
        
        Args:
            folder_path (str): Ruta de la carpeta a analizar
        """
        self.folder_path = folder_path
        self.archivos_por_contrato = defaultdict(list)
        self.total_archivos = 0
    
    def detectar_duplicados(self):
        """
        Analiza los PDFs en la carpeta y detecta duplicados por número de contrato.
        
        Returns:
            dict: Diccionario con contratos duplicados y sus archivos
        """
        pdf_files = [f for f in os.listdir(self.folder_path) if f.lower().endswith('.pdf')]
        self.total_archivos = len(pdf_files)
        
        for filename in pdf_files:
            match = PATRON_CONTRATO.search(filename)
            if match:
                contrato = match.group(1)
                self.archivos_por_contrato[contrato].append(filename)
        
        # Filtrar solo los contratos con más de un archivo
        duplicados = {
            contrato: files 
            for contrato, files in self.archivos_por_contrato.items() 
            if len(files) > 1
        }
        
        return duplicados


# ============================================================
# CLASE: Limpiador de Duplicados
# ============================================================
class DuplicateCleaner:
    """Elimina archivos duplicados conservando solo el primero."""
    
    def __init__(self, folder_path):
        """
        Inicializa el limpiador.
        
        Args:
            folder_path (str): Ruta de la carpeta
        """
        self.folder_path = folder_path
        self.eliminados = 0
        self.errores = 0
    
    def eliminar_duplicados(self, duplicados):
        """
        Elimina archivos duplicados, conservando solo el primero de cada contrato.
        
        Args:
            duplicados (dict): Diccionario con contratos y sus archivos duplicados
            
        Returns:
            tuple: (archivos_eliminados, errores)
        """
        print("\n🔄 Iniciando eliminación de duplicados...\n")
        print("="*70)
        
        for contrato, archivos in duplicados.items():
            print(f"\n📋 Contrato duplicado: {contrato}")
            print(f"   Total de archivos: {len(archivos)}")
            
            # Mostrar todos los archivos
            for idx, archivo in enumerate(archivos, 1):
                marcador = "✅ CONSERVAR" if idx == 1 else "🗑️  ELIMINAR"
                print(f"   [{idx}] {marcador} → {archivo}")
            
            # Mantener el primero, eliminar el resto
            archivos_a_eliminar = archivos[1:]
            
            for archivo in archivos_a_eliminar:
                resultado = self._eliminar_archivo(archivo)
                if resultado:
                    self.eliminados += 1
                else:
                    self.errores += 1
        
        print("="*70 + "\n")
        return self.eliminados, self.errores
    
    def _eliminar_archivo(self, filename):
        """
        Elimina un archivo específico.
        
        Args:
            filename (str): Nombre del archivo
            
        Returns:
            bool: True si se eliminó correctamente, False si hubo error
        """
        try:
            ruta = os.path.join(self.folder_path, filename)
            os.remove(ruta)
            print(f"      ✅ Eliminado exitosamente")
            return True
        except Exception as e:
            print(f"      ❌ Error al eliminar: {str(e)}")
            return False


# ============================================================
# CLASE: Reporteador
# ============================================================
class DuplicateReporter:
    """Genera reportes de duplicados detectados."""
    
    @staticmethod
    def mostrar_reporte(duplicados, total_archivos):
        """
        Muestra un reporte detallado de los duplicados encontrados.
        
        Args:
            duplicados (dict): Diccionario con contratos duplicados
            total_archivos (int): Total de archivos analizados
        """
        print("\n" + "="*70)
        print("📊 REPORTE DE DUPLICADOS DETECTADOS")
        print("="*70)
        
        if not duplicados:
            print("\n✅ No se encontraron duplicados por número de contrato.")
            print(f"   Total de archivos únicos: {total_archivos}")
            print("="*70)
            return
        
        print(f"\n📁 Total de archivos analizados: {total_archivos}")
        print(f"🔍 Contratos con duplicados: {len(duplicados)}")
        
        total_duplicados = sum(len(files) - 1 for files in duplicados.values())
        print(f"🗑️  Archivos duplicados a eliminar: {total_duplicados}\n")
        
        for contrato, archivos in duplicados.items():
            print(f"\n📌 Contrato: {contrato} ({len(archivos)} archivos)")
            for idx, archivo in enumerate(archivos, 1):
                marcador = "✅ CONSERVAR" if idx == 1 else "❌ ELIMINAR"
                print(f"   [{idx}] {marcador}")
                print(f"       {archivo}")
        
        print("\n" + "="*70)
    
    @staticmethod
    def mostrar_resumen_final(total_inicial, duplicados_count, eliminados, errores):
        """
        Muestra el resumen final del proceso.
        
        Args:
            total_inicial (int): Total de archivos iniciales
            duplicados_count (int): Número de contratos duplicados
            eliminados (int): Archivos eliminados exitosamente
            errores (int): Errores durante la eliminación
        """
        total_final = total_inicial - eliminados
        
        print("\n" + "="*70)
        print("📋 RESUMEN FINAL DE LIMPIEZA")
        print("="*70)
        print(f"📂 Total de archivos iniciales    : {total_inicial}")
        print(f"🔍 Contratos duplicados detectados : {duplicados_count}")
        print(f"✅ Archivos eliminados exitosamente: {eliminados}")
        print(f"❌ Errores durante eliminación     : {errores}")
        print(f"📁 Archivos únicos restantes       : {total_final}")
        print("="*70 + "\n")


# ============================================================
# CLASE: Orquestador Principal
# ============================================================
class SUNATDuplicateOrchestrator:
    """Orquestador principal del proceso de eliminación de duplicados."""
    
    def __init__(self, folder_path):
        """
        Inicializa el orquestador.
        
        Args:
            folder_path (str): Ruta de la carpeta
        """
        self.folder_path = folder_path
        self.analyzer = DuplicateAnalyzer(folder_path)
        self.cleaner = DuplicateCleaner(folder_path)
        self.reporter = DuplicateReporter()
        self.start_time = None
    
    def run(self):
        """
        Ejecuta el proceso completo de detección y eliminación de duplicados.
        
        Returns:
            tuple: (total_inicial, duplicados_detectados, archivos_eliminados, errores)
        """
        self.start_time = time.time()
        
        print("\n" + "="*70)
        print("🔍 DETECTOR Y LIMPIADOR DE DUPLICADOS SUNAT")
        print("   (Basado en número de contrato)")
        print("="*70)
        print(f"\n📁 Carpeta: {self.folder_path}\n")
        
        # PASO 1: Detectar duplicados
        duplicados = self.analyzer.detectar_duplicados()
        total_inicial = self.analyzer.total_archivos
        
        if not duplicados:
            self.reporter.mostrar_reporte(duplicados, total_inicial)
            return total_inicial, 0, 0, 0
        
        # PASO 2: Mostrar reporte
        self.reporter.mostrar_reporte(duplicados, total_inicial)
        
        # PASO 3: Eliminar duplicados
        eliminados, errores = self.cleaner.eliminar_duplicados(duplicados)
        
        # PASO 4: Mostrar resumen final
        elapsed_time = time.time() - self.start_time
        self.reporter.mostrar_resumen_final(
            total_inicial, 
            len(duplicados), 
            eliminados, 
            errores
        )
        
        print(f"⏱️  Tiempo de ejecución: {elapsed_time:.2f} segundos\n")
        
        return total_inicial, len(duplicados), eliminados, errores


# ============================================================
# FUNCIONES DE UTILIDAD
# ============================================================
def seleccionar_carpeta():
    """
    Abre un diálogo para que el usuario seleccione una carpeta.
    
    Returns:
        str: Ruta de la carpeta seleccionada o None si se canceló
    """
    root = Tk()
    root.withdraw()
    root.attributes('-topmost', True)
    
    folder_path = filedialog.askdirectory(
        title="Selecciona la carpeta con archivos SUNAT renombrados"
    )
    
    root.destroy()
    
    return folder_path if folder_path else None


def procesar_duplicados_sunat(folder_path: Optional[str] = None):
    """
    Función de interfaz para procesar duplicados SUNAT.
    
    Args:
        folder_path (str, optional): Ruta de la carpeta
        
    Returns:
        tuple: (total_inicial, duplicados, eliminados, errores)
    """
    if not folder_path:
        folder_path = seleccionar_carpeta()
    
    if not folder_path:
        print("❌ No se seleccionó ninguna carpeta. Proceso cancelado.")
        return 0, 0, 0, 0
    
    if not os.path.isdir(folder_path):
        raise ValueError(f"La ruta '{folder_path}' no es una carpeta válida")
    
    orchestrator = SUNATDuplicateOrchestrator(folder_path)
    return orchestrator.run()


# ============================================================
# EJECUCIÓN STANDALONE
# ============================================================
if __name__ == "__main__":
    import sys
    
    print("🔍 Selecciona la carpeta con archivos SUNAT renombrados...")
    
    # Permitir pasar ruta por argumento o usar selector
    if len(sys.argv) >= 2:
        folder_path = sys.argv[1]
    else:
        folder_path = seleccionar_carpeta()
    
    if not folder_path:
        print("❌ No se seleccionó ninguna carpeta. Proceso cancelado.")
        sys.exit(1)
    
    try:
        total, duplicados, eliminados, errores = procesar_duplicados_sunat(folder_path)
        
        if eliminados > 0 or duplicados == 0:
            print("✅ Proceso completado exitosamente")
            sys.exit(0)
        else:
            print("⚠️ No se eliminaron archivos")
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ Error crítico: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)