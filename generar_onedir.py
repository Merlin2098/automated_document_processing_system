"""
Script de Generación de Ejecutable Onedir
Proyecto: DocFlow_Eventuales
Genera un ejecutable Windows con carpeta distribuible

Autor: Richi
Fecha: 2025
Migrado a PySide6 con arquitectura modular
"""

import os
import sys
import pkg_resources
import subprocess
import shutil
from pathlib import Path
import time
import threading

# ==========================================================
# CONFIGURACIÓN
# ==========================================================
NOMBRE_EXE = "DocFlow_Eventuales.exe"
MAIN_SCRIPT = "main.py"

DIST_PATH = "dist"
BUILD_PATH = "build"
SPEC_PATH = "spec"

# CORRECCIÓN: Se han eliminado 'distutils', 'setuptools' y 'pkg_resources'
# de las exclusiones para evitar el ValueError en los hooks de PyInstaller.
EXCLUSIONES = [
    "pip", "wheel", "ensurepip", "test", "tkinter.test",
    "pytest", "pytest_cov", "coverage", "notebook",
    "IPython", "jupyter", "matplotlib", "scipy",
    "numpy.testing", "pandas.tests"
]

# ==========================================================
# VALIDAR ENTORNO VIRTUAL
# ==========================================================
def validar_entorno_virtual():
    """Verifica que se esté ejecutando dentro de un entorno virtual"""
    print("=" * 60)
    print("🔍 VALIDACIÓN DE ENTORNO VIRTUAL")
    print("=" * 60)

    if sys.prefix == sys.base_prefix:
        print("❌ ERROR: No estás dentro de un entorno virtual (venv).")
        print("   Activa uno antes de continuar.")
        print("   Ejemplo Windows: venv\\Scripts\\activate")
        print("   Ejemplo Linux/Mac: source venv/bin/activate")
        sys.exit(1)

    print(f"✅ Entorno virtual detectado: {sys.prefix}\n")

    # Nota: pkg_resources puede lanzar advertencias si no está instalado, 
    # pero es estándar en venv.
    try:
        paquetes = sorted([(pkg.key, pkg.version) for pkg in pkg_resources.working_set])
        print(f"📦 Librerías instaladas ({len(paquetes)}):")
        for nombre, version in paquetes:
            flag = "🧹 (excluir)" if nombre in EXCLUSIONES else "✅"
            print(f"   {flag} {nombre:<25} {version}")
    except Exception:
        print("⚠️ No se pudo listar paquetes con pkg_resources (no crítico).")
    print("\n")

# ==========================================================
# CONFIRMACIÓN MANUAL
# ==========================================================
def confirmar_ejecucion():
    """Solicita confirmación del usuario antes de continuar"""
    print("=" * 60)
    print("⚠️  CONFIRMACIÓN DE EJECUCIÓN")
    print("=" * 60)
    print("Este proceso generará un ejecutable Windows onedir.")
    print("Se incluirán todos los recursos, temas y configuraciones.\n")
    
    respuesta = input("¿Deseas generar el ejecutable ahora? (S/N): ").strip().lower()

    if respuesta not in ("s", "si", "sí"):
        print("\n🛑 Proceso cancelado por el usuario.")
        sys.exit(0)

    print("\n✅ Confirmado. Continuando con la generación...\n")

# ==========================================================
# LIMPIAR BUILDS ANTERIORES
# ==========================================================
def limpiar_builds():
    """Elimina carpetas de builds anteriores"""
    print("🧹 Limpiando builds anteriores...")
    for carpeta in [DIST_PATH, BUILD_PATH, SPEC_PATH]:
        if os.path.exists(carpeta):
            try:
                shutil.rmtree(carpeta)
                print(f"   ✅ Eliminado: {carpeta}")
            except Exception as e:
                print(f"   ⚠️  No se pudo eliminar {carpeta}: {e}")
    print()

# ==========================================================
# CONSTRUIR COMANDO PYINSTALLER
# ==========================================================
def construir_comando():
    """Construye el comando completo de PyInstaller"""
    base_dir = Path.cwd()

    comando = [
        sys.executable, "-m", "PyInstaller",
        "--onedir",              # Modo directorio (no onefile)
        "--windowed",            # Sin consola (GUI)
        "--clean",               # Limpiar cache
        "--log-level", "WARN",   # Solo warnings y errores
        "--distpath", DIST_PATH,
        "--workpath", BUILD_PATH,
        "--specpath", SPEC_PATH,
        "--name", NOMBRE_EXE.replace(".exe", ""),
        "--noconfirm",           # No preguntar confirmar sobreescritura
    ]

    # ======================================================
    # PATHS: Agregar rutas para imports
    # ======================================================
    # Directorio raíz (para encontrar todos los módulos)
    comando += ["--paths", str(base_dir)]

    # Agregar carpetas específicas
    for carpeta in ["ui", "core_pipeline", "core_sunat", "core_tools", "extractores", "utils"]:
        ruta = base_dir / carpeta
        if ruta.exists():
            comando += ["--paths", str(ruta)]

    # ======================================================
    # HIDDEN IMPORTS: Dependencias no detectadas automáticamente
    # ======================================================
    hidden_imports = [
        # PySide6 core (reemplaza PyQt5)
        "PySide6.QtCore",
        "PySide6.QtGui", 
        "PySide6.QtWidgets",
        
        # PDF processing
        "PyPDF2",
        "pdfplumber",
        
        # Excel y datos
        "pandas",
        "openpyxl",
        "duckdb",
        "pyarrow",
        "pyarrow.parquet",
        
        # Multiprocessing (CRÍTICO para Paso 3)
        "multiprocessing",
        "multiprocessing.spawn",
        "multiprocessing.pool",
        "multiprocessing.managers",
        "multiprocessing.queues",
        
        # Expresiones regulares y utilidades
        "re",
        "pathlib",
        "json",
        "datetime",
        "shutil",
        "logging",
        
        # Sistema
        "psutil",
        
        # Módulos del proyecto (importación explícita)
        "ui.main_window",
        "ui.splash_screen",
        "ui.tabs.tab_pipeline_core",
        "ui.tabs.tab_pipeline_sunat",
        "ui.tabs.tab_quick_tools",
        "ui.tabs.tab_settings",
        "ui.widgets.console_widget",
        "ui.widgets.file_selector",
        "ui.widgets.monitoring_panel",
        "ui.widgets.stepper_widget",
        "ui.workers.core_pipeline_step1_worker",
        "ui.workers.core_pipeline_step2_worker",
        "ui.workers.core_pipeline_step3_worker",
        "ui.workers.core_pipeline_step4_worker",
        "ui.workers.core_pipeline_step5_worker",
        "ui.workers.pdf_splitter_worker",
        "ui.workers.sunat_diagnostic_worker",
        "ui.workers.sunat_duplicates_worker",
        "ui.workers.sunat_rename_worker",
        "utils.theme_manager",
        "utils.logger",
        "utils.logger_config",
        "utils.excel_converter",
        
        # Core modules (para multiprocessing)
        "core_pipeline.step3_generar_diagnostico",
        "extractores.extractor_afp",
        "extractores.extractor_boleta",
        "extractores.extractor_quinta",
    ]
    
    for imp in hidden_imports:
        comando += ["--hidden-import", imp]

    # ======================================================
    # EXCLUSIONES: Módulos innecesarios
    # ======================================================
    for excl in EXCLUSIONES:
        comando += ["--exclude-module", excl]

    # ======================================================
    # ICONO DE LA APLICACIÓN
    # ======================================================
    ico_path = base_dir / "resources" / "app.ico"
    if ico_path.exists():
        comando += ["--icon", str(ico_path)]
        print(f"   ✅ Icono encontrado: {ico_path}")
    else:
        print(f"   ⚠️  Advertencia: No se encontró el icono en {ico_path}")
    
    # ======================================================
    # RUNTIME HOOKS (para multiprocessing)
    # ======================================================
    print("\n🔧 Configurando runtime hooks...")
    
    # Crear directorio hooks si no existe
    hooks_dir = base_dir / "hooks"
    hooks_dir.mkdir(exist_ok=True)
    
    # Verificar si existe el hook de multiprocessing
    hook_mp_path = hooks_dir / "pyi_rth_multiprocessing.py"
    if hook_mp_path.exists():
        comando += ["--runtime-hook", str(hook_mp_path)]
        print(f"   ✅ Runtime hook multiprocessing: {hook_mp_path}")
    else:
        print(f"   ⚠️  Advertencia: Runtime hook no encontrado en {hook_mp_path}")
        print(f"      El Paso 3 puede no funcionar correctamente en producción")
    
    # ======================================================
    # CONFIGURACIÓN ADICIONAL DE MULTIPROCESSING
    # ======================================================
    # Recolectar todos los submódulos de multiprocessing
    comando += ["--collect-all", "multiprocessing"]

    # ======================================================
    # ARCHIVOS Y CARPETAS DE DATOS (--add-data)
    # ======================================================
    print("\n📁 Agregando archivos y carpetas de recursos...")
    
    # 1. CONFIG: config.json
    config_json = base_dir / "resources" / "config.json"
    if config_json.exists():
        comando += ["--add-data", f"{config_json};resources"]
        print(f"   ✅ config.json")
    else:
        print(f"   ⚠️  No se encontró resources/config.json")

    # 2. THEMES: archivos JSON de temas
    themes_dir = base_dir / "resources" / "themes"
    if themes_dir.exists():
        for theme_file in themes_dir.glob("*.json"):
            comando += ["--add-data", f"{theme_file};resources/themes"]
            print(f"   ✅ {theme_file.name}")
    else:
        print(f"   ⚠️  No se encontró carpeta resources/themes")

    # 3. ICONO: también incluido en bundle (además de --icon)
    if ico_path.exists():
        comando += ["--add-data", f"{ico_path};resources"]
        print(f"   ✅ app.ico (bundle)")

    # ======================================================
    # SCRIPT PRINCIPAL
    # ======================================================
    main_path = base_dir / MAIN_SCRIPT
    comando.append(str(main_path))
    
    return comando

# ==========================================================
# GENERAR EJECUTABLE CON BARRA DE PROGRESO
# ==========================================================
def generar_exe():
    """Ejecuta PyInstaller para generar el ejecutable con barra de progreso"""
    print("=" * 60)
    print("🚀 INICIANDO GENERACIÓN DEL EJECUTABLE (MODO ONEDIR)")
    print("=" * 60)
    
    limpiar_builds()
    cmd = construir_comando()
    
    print("\n💻 Comando PyInstaller:")
    print("─" * 60)
    print(" ".join(cmd))
    print("─" * 60 + "\n")
    
    # Ejecutar PyInstaller con captura de salida en tiempo real
    print("🔨 Ejecutando PyInstaller...\n")
    
    # Fases estimadas del proceso
    fases = [
        ("📦 Analizando dependencias", 0, 15),
        ("🔍 Detectando módulos", 15, 30),
        ("📚 Recopilando archivos", 30, 50),
        ("⚙️  Compilando ejecutable", 50, 75),
        ("📁 Empaquetando recursos", 75, 90),
        ("✨ Finalizando bundle", 90, 100),
    ]
    
    # Variable para controlar el progreso
    progreso_actual = [0]
    proceso_completado = [False]
    
    def mostrar_progreso():
        """Muestra una barra de progreso animada"""
        simbolos = ['⣾', '⣽', '⣻', '⢿', '⡿', '⣟', '⣯', '⣷']
        idx = 0
        fase_actual = 0
        
        while not proceso_completado[0]:
            # Determinar fase actual basada en progreso
            for i, (nombre, inicio, fin) in enumerate(fases):
                if inicio <= progreso_actual[0] < fin:
                    fase_actual = i
                    break
            
            fase_nombre = fases[fase_actual][0]
            porcentaje = progreso_actual[0]
            
            # Construir barra
            barra_len = 40
            lleno = int(barra_len * porcentaje / 100)
            vacio = barra_len - lleno
            barra = "█" * lleno + "░" * vacio
            
            # Mostrar con animación
            print(f"\r{simbolos[idx]} {fase_nombre:<35} [{barra}] {porcentaje:3d}%", end="", flush=True)
            
            idx = (idx + 1) % len(simbolos)
            time.sleep(0.1)
        
        # Barra completa al finalizar
        print(f"\r✅ Generación completada          [{'█' * 40}] 100%")
    
    def actualizar_progreso():
        """Simula el progreso basado en tiempo estimado"""
        tiempo_total = 60  # Reducido a 1 min para no bloquear visualmente
        intervalos = 100
        tiempo_por_intervalo = tiempo_total / intervalos
        
        for i in range(intervalos + 1):
            if proceso_completado[0]:
                break
            progreso_actual[0] = i
            time.sleep(tiempo_por_intervalo)
    
    # Iniciar thread de progreso
    thread_progreso = threading.Thread(target=mostrar_progreso, daemon=True)
    thread_actualizar = threading.Thread(target=actualizar_progreso, daemon=True)
    
    thread_progreso.start()
    thread_actualizar.start()
    
    # Ejecutar PyInstaller
    # Importante: para debug, a veces es util quitar stdout=PIPE si falla,
    # pero aqui mantenemos la logica original
    result = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    # Marcar como completado
    proceso_completado[0] = True
    progreso_actual[0] = 100
    
    # Esperar a que termine la animación
    time.sleep(0.5)
    
    print("\n\n" + "=" * 60)
    if result.returncode == 0:
        carpeta_exe = Path(DIST_PATH) / NOMBRE_EXE.replace(".exe", "")
        print(f"✅ GENERACIÓN COMPLETADA CORRECTAMENTE")
        print("=" * 60)
        print(f"\n📂 Carpeta de salida:")
        print(f"   {carpeta_exe.absolute()}")
        print(f"\n📦 Ejecutable principal:")
        print(f"   {(carpeta_exe / NOMBRE_EXE).absolute()}")
        print(f"\n💡 IMPORTANTE:")
        print(f"   - Distribuye toda la carpeta '{NOMBRE_EXE.replace('.exe', '')}/'")
        print(f"   - No separar el .exe de la carpeta _internal/")
        print(f"   - Los recursos y temas están embebidos en _internal/")
    else:
        print("❌ ERROR EN LA GENERACIÓN")
        print("=" * 60)
        print("\n💡 Detalles del error:")
        print("─" * 60)
        if result.stderr:
            # Mostrar todo el error para debugging si es grave
            print(result.stderr)
        else:
            print("   No se capturó stderr, revisa los logs en build/")
        print("─" * 60)
    print("=" * 60)

# ==========================================================
# VERIFICAR SCRIPT PRINCIPAL
# ==========================================================
def verificar_main():
    """Verifica que exista el script principal"""
    ruta = Path.cwd() / MAIN_SCRIPT
    if not ruta.is_file():
        print(f"❌ ERROR: No se encontró '{MAIN_SCRIPT}' en el directorio actual.")
        print(f"   Asegúrate de ejecutar este script desde la raíz del proyecto.")
        sys.exit(1)
    else:
        print(f"✅ Archivo principal encontrado: {MAIN_SCRIPT}\n")

# ==========================================================
# VERIFICAR ESTRUCTURA DEL PROYECTO
# ==========================================================
def verificar_estructura():
    """Verifica que existan las carpetas y archivos necesarios"""
    print("🔍 Verificando estructura del proyecto:")
    print("=" * 60)
    
    base_dir = Path.cwd()
    
    # Carpetas críticas
    carpetas_requeridas = [
        "ui",
        "ui/tabs",
        "ui/widgets",
        "ui/workers",
        "core_pipeline",
        "core_sunat",
        "core_tools",
        "extractores",
        "utils",
        "resources",
        "resources/themes"
    ]
    
    # Archivos críticos
    archivos_requeridos = [
        "main.py",
        "resources/app.ico",
        "resources/config.json",
        "resources/themes/theme_dark.json",
        "resources/themes/theme_light.json",
        "ui/main_window.py",
        "ui/splash_screen.py",
    ]
    
    todo_ok = True
    
    print("\n📁 Carpetas:")
    for carpeta in carpetas_requeridas:
        ruta = base_dir / carpeta
        if ruta.exists():
            print(f"   ✅ {carpeta}/")
        else:
            print(f"   ❌ {carpeta}/ NO ENCONTRADA")
            todo_ok = False
    
    print("\n📄 Archivos:")
    for archivo in archivos_requeridos:
        ruta = base_dir / archivo
        if ruta.exists():
            print(f"   ✅ {archivo}")
        else:
            print(f"   ⚠️  {archivo} no encontrado")
            # No todos son críticos, pero advertimos
    
    if not todo_ok:
        print("\n❌ ERROR: Estructura del proyecto incompleta.")
        print("   Asegúrate de ejecutar este script desde la raíz del proyecto.")
        print("   Deben existir todas las carpetas: ui/, core_pipeline/, core_sunat/, etc.")
        sys.exit(1)
    
    print("\n" + "=" * 60)


# ==========================================================
# EJECUCIÓN PRINCIPAL
# ==========================================================
if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("   GENERADOR DE EJECUTABLE - DOCFLOW EVENTUALES")
    print("   Modo: Onedir (carpeta distribuible)")
    print("   Framework: PySide6")
    print("=" * 60 + "\n")
    
    try:
        verificar_main()
        verificar_estructura()
        validar_entorno_virtual()
        confirmar_ejecucion()
        generar_exe()
        
        print("\n" + "=" * 60)
        print("🎉 PROCESO COMPLETADO EXITOSAMENTE")
        print("=" * 60)
        print("\n💡 PRÓXIMOS PASOS:")
        print("   1. Prueba el ejecutable localmente")
        print("   2. Verifica que todos los tabs funcionen correctamente")
        print("   3. Prueba cambiar de tema (Dark ↔ Light)")
        print("   4. Verifica que los workers procesen correctamente")
        print("   5. Distribuye toda la carpeta del ejecutable\n")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Proceso interrumpido por el usuario.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Error inesperado: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)