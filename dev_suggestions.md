# architect.md

## Nota Operativa (Legacy)
Este repositorio opera en modo **legacy**. La arquitectura fue estabilizada y cualquier cambio estructural grande puede degradar el rendimiento.

## Cambios en formatos de documentos
Si necesitas ajustar cómo se leen/extraen datos de PDFs o cambios de formato:
- **Editar directamente los extractores en `extractores/`**.
- Evita mover o renombrar módulos de esta carpeta sin una razón crítica.

## Advertencia de rendimiento
Históricamente, refactorizaciones agresivas han provocado **pérdidas de performance** difíciles de revertir.
- **Principio:** si funciona y el rendimiento es bueno, **no lo refactorices**.
- Cualquier reestructuración debe justificarse con métricas y pruebas comparativas.

## Regla práctica
> “Si está roto, no lo arregles.”

Antes de tocar la arquitectura:
1. Mide tiempos actuales (baseline).
2. Cambia lo mínimo posible.
3. Vuelve a medir y compara.
