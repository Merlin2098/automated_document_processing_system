import os

def generar_arbol(directorio, prefijo="", excluidos=None, carpetas_ignoradas=None):
    """
    Genera la estructura tipo árbol sin barras proporcionales.
    """
    if excluidos is None:
        excluidos = set()
    if carpetas_ignoradas is None:
        carpetas_ignoradas = set()

    contenido = []

    try:
        elementos = sorted(os.listdir(directorio))
    except PermissionError:
        return contenido

    # Filtrar excluidos (incluye archivos .spec)
    elementos = [
        e for e in elementos
        if e not in excluidos
        and e not in carpetas_ignoradas
        and not e.endswith(".spec")
    ]

    for index, nombre in enumerate(elementos):
        ruta = os.path.join(directorio, nombre)
        es_ultimo = index == len(elementos) - 1
        conector = "└── " if es_ultimo else "├── "

        if os.path.isdir(ruta):
            contenido.append(f"{prefijo}{conector}{nombre}/")
            extension = "    " if es_ultimo else "│   "
            contenido.extend(
                generar_arbol(ruta, prefijo + extension, excluidos, carpetas_ignoradas)
            )
        else:
            contenido.append(f"{prefijo}{conector}{nombre}")

    return contenido


if __name__ == "__main__":
    raiz = os.path.dirname(os.path.abspath(__file__))

    # Exclusiones por defecto
    script_actual = os.path.basename(__file__)
    excluidos = {
        "__init__.py",
        "requirements.txt",
        script_actual,
    }

    # Carpetas ignoradas (PyInstaller y entornos)
    carpetas_ignoradas = {
        ".git",
        "__pycache__",
        ".venv",
        "venv",
        "dist",
        "build",
        ".idea",
        ".vscode",
        "logs",
    }

    # Generar árbol
    arbol = generar_arbol(raiz, excluidos=excluidos, carpetas_ignoradas=carpetas_ignoradas)
    salida = "\n".join(arbol)

    # Guardar en treemap.md
    with open("treemap.md", "w", encoding="utf-8") as f:
        f.write("## 🗂️ Treemap del Proyecto\n\n```\n")
        f.write(salida)
        f.write("\n```\n")

    print("\n✅ Treemap generado en treemap.md\n")
