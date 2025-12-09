import os
from datetime import datetime
from pathlib import Path
import sys
from tkinter import Tk, filedialog, messagebox
import time
import json


class FileRenamer:
    """Clase para renombrar archivos PDF basándose en información extraída."""
    
    def __init__(self):
        self.stats = {
            'total_files': 0,
            'renamed': 0,
            'errors': 0,
            'skipped': 0
        }
    
    def rename_file(self, old_path, new_filename):
        """
        Renombra un archivo PDF al nuevo nombre especificado.
        
        Args:
            old_path (str): Ruta completa del archivo original
            new_filename (str): Nuevo nombre del archivo
            
        Returns:
            tuple: (mensaje, éxito)
        """
        original_filename = os.path.basename(old_path)
        folder_path = os.path.dirname(old_path)
        
        # Construir nueva ruta
        new_path = os.path.join(folder_path, new_filename)
        
        # Resolver duplicados si existe
        new_path = self._resolve_duplicate(new_path)
        final_filename = os.path.basename(new_path)
        
        try:
            os.rename(old_path, new_path)
            return f"✅ {original_filename} → {final_filename}", True
        except Exception as e:
            return f"❌ Error: {original_filename} - {str(e)}", False
    
    def _resolve_duplicate(self, file_path):
        """Resuelve duplicados agregando un contador al nombre."""
        if not os.path.exists(file_path):
            return file_path
        
        base, ext = os.path.splitext(file_path)
        count = 1
        while True:
            new_path = f"{base}_{count}{ext}"
            if not os.path.exists(new_path):
                return new_path
            count += 1


class JSONReader:
    """Clase para leer el archivo JSON de renombrado."""
    
    def read_rename_json(self, json_path):
        """
        Lee el archivo JSON y extrae la información de renombrado.
        
        Args:
            json_path (str): Ruta del archivo JSON
            
        Returns:
            dict: Diccionario con archivo original como clave y nuevo nombre como valor
        """
        rename_data = {}
        
        # Lista de codificaciones a probar
        encodings = ['utf-8', 'latin-1', 'iso-8859-1', 'cp1252', 'utf-16']
        
        data = None
        for encoding in encodings:
            try:
                with open(json_path, 'r', encoding=encoding) as f:
                    data = json.load(f)
                break  # Si funciona, salir del loop
            except (UnicodeDecodeError, UnicodeError):
                continue
            except Exception as e:
                raise Exception(f"Error al leer JSON: {str(e)}")
        
        if data is None:
            raise Exception("No se pudo decodificar el archivo JSON con ninguna codificación conocida")
        
        try:
            # Procesar cada entrada del JSON
            for entry in data:
                original = entry.get('ARCHIVO ORIGINAL')
                nuevo = entry.get('NUEVO NOMBRE')
                
                if original and nuevo:
                    rename_data[original] = nuevo
            
            return rename_data
            
        except Exception as e:
            raise Exception(f"Error al procesar datos del JSON: {str(e)}")


class FolderScanner:
    """Clase para escanear carpetas y localizar archivos."""
    
    def find_json_file(self, folder_path):
        """
        Busca el archivo JSON de renombrado en la carpeta.
        
        Args:
            folder_path (str): Ruta de la carpeta
            
        Returns:
            str: Ruta del archivo JSON encontrado o None
        """
        json_files = [f for f in os.listdir(folder_path) 
                     if f.endswith('.json') and 'rename' in f.lower()]
        
        if not json_files:
            return None
        
        # Si hay múltiples, tomar el más reciente
        json_files.sort(reverse=True)
        return os.path.join(folder_path, json_files[0])
    
    def get_pdf_files(self, folder_path):
        """
        Obtiene la lista de archivos PDF en la carpeta.
        
        Args:
            folder_path (str): Ruta de la carpeta
            
        Returns:
            list: Lista de nombres de archivos PDF
        """
        return [f for f in os.listdir(folder_path) if f.lower().endswith('.pdf')]


class SUNATRenameOrchestrator:
    """Orquestador principal del proceso de renombrado."""
    
    def __init__(self, folder_path):
        """
        Inicializa el orquestador.
        
        Args:
            folder_path (str): Ruta de la carpeta de trabajo
        """
        self.folder_path = folder_path
        self.scanner = FolderScanner()
        self.reader = JSONReader()
        self.renamer = FileRenamer()
        self.start_time = None
    
    def run(self):
        """
        Ejecuta el proceso completo de renombrado.
        
        Returns:
            dict: Estadísticas del proceso
        """
        self.start_time = time.time()
        
        print(f"🚀 Iniciando proceso de renombrado SUNAT")
        print(f"📁 Carpeta: {self.folder_path}\n")
        
        # PASO 1: Localizar archivo JSON
        json_path = self._locate_json()
        if not json_path:
            return None
        
        # PASO 2: Leer datos del JSON
        rename_data = self._read_json_data(json_path)
        if not rename_data:
            return None
        
        # PASO 3: Obtener archivos PDF
        pdf_files = self._get_pdf_files()
        if not pdf_files:
            return None
        
        # PASO 4: Ejecutar renombrado
        self._execute_rename(pdf_files, rename_data)
        
        # PASO 5: Mostrar resumen
        elapsed_time = time.time() - self.start_time
        self._print_summary(elapsed_time)
        
        return self.renamer.stats
    
    def _locate_json(self):
        """Localiza el archivo JSON de renombrado."""
        print("🔍 Buscando archivo JSON de renombrado...")
        json_path = self.scanner.find_json_file(self.folder_path)
        
        if not json_path:
            print("❌ No se encontró archivo JSON de renombrado en la carpeta.")
            print("   El archivo debe contener 'rename' en su nombre.\n")
            return None
        
        print(f"✅ JSON encontrado: {os.path.basename(json_path)}\n")
        return json_path
    
    def _read_json_data(self, json_path):
        """Lee los datos del archivo JSON."""
        print("📖 Leyendo datos del JSON...")
        
        try:
            rename_data = self.reader.read_rename_json(json_path)
            print(f"✅ Se cargaron {len(rename_data)} registros del JSON\n")
            return rename_data
        except Exception as e:
            print(f"❌ Error al leer JSON: {str(e)}\n")
            return None
    
    def _get_pdf_files(self):
        """Obtiene la lista de archivos PDF."""
        print("📄 Escaneando archivos PDF...")
        pdf_files = self.scanner.get_pdf_files(self.folder_path)
        
        if not pdf_files:
            print("⚠️ No se encontraron archivos PDF en la carpeta.\n")
            return None
        
        print(f"✅ Se encontraron {len(pdf_files)} archivos PDF\n")
        self.renamer.stats['total_files'] = len(pdf_files)
        return pdf_files
    
    def _execute_rename(self, pdf_files, rename_data):
        """Ejecuta el renombrado de archivos."""
        print("🔄 Iniciando renombrado de archivos...\n")
        print("="*70)
        
        for pdf_file in pdf_files:
            # Verificar si el archivo está en el JSON de renombrado
            if pdf_file not in rename_data:
                print(f"⏭️  Omitido (no en JSON): {pdf_file}")
                self.renamer.stats['skipped'] += 1
                continue
            
            # Obtener nuevo nombre del JSON
            new_filename = rename_data[pdf_file]
            old_path = os.path.join(self.folder_path, pdf_file)
            
            # Ejecutar renombrado
            message, success = self.renamer.rename_file(old_path, new_filename)
            
            print(message)
            
            if success:
                self.renamer.stats['renamed'] += 1
            else:
                self.renamer.stats['errors'] += 1
        
        print("="*70 + "\n")
    
    def _print_summary(self, elapsed_time):
        """Imprime el resumen final del proceso."""
        stats = self.renamer.stats
        
        print("\n" + "="*70)
        print("📊 RESUMEN DEL PROCESO DE RENOMBRADO")
        print("="*70)
        print(f"📄 Total de archivos PDF: {stats['total_files']}")
        print(f"✅ Renombrados exitosamente: {stats['renamed']}")
        print(f"⏭️  Omitidos (no en JSON): {stats['skipped']}")
        print(f"❌ Errores: {stats['errors']}")
        print(f"⏱️  Tiempo de ejecución: {elapsed_time:.2f} segundos")
        print("="*70 + "\n")


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
        title="Selecciona la carpeta con PDFs y JSON de renombrado"
    )
    
    root.destroy()
    
    return folder_path if folder_path else None


def ejecutar_renombrado_sunat(folder_path: str):
    """
    Función de interfaz para ejecutar el renombrado SUNAT.
    
    Args:
        folder_path (str): Ruta de la carpeta de trabajo
        
    Returns:
        dict: Estadísticas del proceso
    """
    if not os.path.isdir(folder_path):
        raise ValueError(f"La ruta '{folder_path}' no es una carpeta válida")
    
    orchestrator = SUNATRenameOrchestrator(folder_path)
    return orchestrator.run()


# Punto de entrada para uso standalone
if __name__ == "__main__":
    print("🔍 Selecciona la carpeta con los PDFs y el JSON de renombrado...")
    
    # Permitir pasar ruta por argumento o usar selector
    if len(sys.argv) >= 2:
        folder_path = sys.argv[1]
    else:
        folder_path = seleccionar_carpeta()
    
    if not folder_path:
        print("❌ No se seleccionó ninguna carpeta. Proceso cancelado.")
        sys.exit(1)
    
    try:
        stats = ejecutar_renombrado_sunat(folder_path)
        
        if stats:
            print("✅ Proceso completado exitosamente")
            sys.exit(0)
        else:
            print("⚠️ El proceso no se completó correctamente")
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ Error crítico: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)