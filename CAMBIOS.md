# Solicitudes de cambio

Escribe aquí los cambios que quieras hacer en el programa. La automatización revisará este archivo periódicamente, implementará las solicitudes claras, documentará dónde y por qué hizo cada modificación y subirá el resultado a la rama `Danny`.

## Cómo escribir una solicitud

Copia este formato debajo de `Solicitudes pendientes`:

```text
- [ ] Título corto del cambio
  - Solicitud: Explica exactamente qué quieres modificar.
  - Resultado esperado: Describe cómo debe comportarse al terminar.
```

Puedes incluir varias solicitudes. Si una depende de otra, indícalo expresamente.

## Solicitudes pendientes

<!-- Escribe aquí tus solicitudes usando casillas sin marcar: - [ ] -->
- [ ] El nombre del programa que tiene como titulo solo dejalo como OLLIN

## Historial de cambios

<!-- La automatización moverá aquí las solicitudes terminadas y explicará dónde, qué y por qué cambió. -->

- [x] Cambiar el fondo de la interfaz a rojo `#F54927`.
  - Ubicación: `ventana.py`, constante `COLOR_FONDO` y método `Ventana._construir()`.
  - Cambio y motivo: se aplicó el rojo a la ventana principal y sus secciones para que el color cubra el fondo visible. Se conservó el fondo de los cuadros de texto para facilitar la lectura.
  - Verificación: se comprobó la compilación de ambos módulos Python y se creó una ventana de Tkinter para verificar el color de los contenedores y que el editor y el resultado conservaran su fondo.

- [x] Cambia el color de fondo de la interface al siguinete color #272AF5
  - Origen: solicitud en `main`, commit `df94181`.
  - Ubicación: `ventana.py`, constantes `COLOR_FONDO` y `COLOR_TEXTO_FONDO` y método `Ventana._construir()`.
  - Cambio y motivo: se cambió el fondo principal a azul `#272AF5` y se puso en blanco el texto que queda sobre ese fondo para mantener el contraste. El editor y el panel de resultados conservan sus fondos.
  - Verificación: se compilaron ambos módulos Python y se comprobaron en Tkinter los colores de fondo y texto y los fondos de ambos cuadros.
