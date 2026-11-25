# Flujo de solicitudes automáticas

Este repositorio usa `CAMBIOS.md` como bandeja de solicitudes del usuario.

## Procedimiento

1. Trabaja únicamente en la rama `Danny` y nunca uses `push --force`.
2. Lee `CAMBIOS.md` y procesa solo las entradas sin marcar de la sección `Solicitudes pendientes`.
3. Antes de modificar código, ejecuta `git fetch origin` y actualiza `Danny` mediante un avance seguro. No sobrescribas cambios locales ajenos.
4. Implementa cada solicitud respetando la separación existente: `ventana.py` contiene la interfaz y `analizador.py` contiene la lógica del análisis.
5. Verifica el cambio con las pruebas o comandos adecuados. Como mínimo, comprueba que los archivos Python compilen; cuando el cambio afecte al análisis, ejecuta también un ejemplo contra la base `OLLIN`.
6. Después de verificarlo, mueve la solicitud al `Historial de cambios` de `CAMBIOS.md` y documenta:
   - archivos modificados;
   - funciones, clases o secciones afectadas;
   - qué se cambió;
   - por qué se cambió;
   - cómo se verificó.
7. Crea un commit descriptivo por solicitud y súbelo a `origin/Danny`.
8. Si una solicitud es ambigua, peligrosa, requiere credenciales o no puede verificarse, no improvises ni la marques como terminada. Registra el bloqueo y solicita aclaración.
9. Si no hay solicitudes pendientes, no modifiques archivos, no crees commits y no hagas `push`.

## Archivos generados

No agregues al repositorio `__pycache__`, archivos `.pyc`, credenciales, bases locales ni resultados temporales.
