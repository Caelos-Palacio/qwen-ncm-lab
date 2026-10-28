# Pizarra Qwen → mini-NCM

Abrir `index.html` en un navegador local. No necesita instalar nada ni acceso a red; las referencias enlazan los artefactos existentes del proyecto. El HTML conserva una copia embebida de las seis filas agregadas de costes para funcionar sin fetch desde file://.

Recorrido: arquitectura, entrenamiento, protocolo, resultados, coste NCM, coste de memoria Qwen y siguiente protocolo propuesto. Arrastrar el fondo mueve el lienzo; rueda desplaza; Ctrl + rueda hace zoom. Botones centran cada marco, ajustan todo o abren modo lectura. Teclado: Tab y Enter en controles, flechas / + / − / Inicio sobre lienzo, Escape en detalles. El modo lectura se inicia automáticamente con ancho móvil.

## Verificación realizada

- PASS: sintaxis JavaScript comprobada con Node.
- PASS: IDs únicos y 9 vínculos locales existentes.
- PASS: lógica con DOM mínimo simulado a anchos 1280 y 390: 7 destinos, 10 detalles abrir/cerrar, zoom, ajuste general, centrado, minimapa y modo lectura.
- PASS: ninguna dependencia externa de ejecución; HTML/CSS/JS propios, sin librerías remotas ni fuentes descargadas.
- PASS: 81 entradas del manifiesto histórico verificadas intactas; manifiesto de esta presentación separado.
- PASS: métricas y arquitectura contrastadas con archivos cerrados; revisión independiente en `revision/REVISION-CONTENIDO.md`.
- PASS: decisiones visuales y diales escritos en `DESIGN.md`; colores semánticos, contraste estático revisado y foco visible definido.
- PENDIENTE: revisión visual del resultado renderizado y clics reales. CUA rechazó abrir file:// por política de protocolos y prohibió rodeos por otras superficies o servidores. No se intentó evitarlos. No hay capturas ni afirmación de render verificado. La simulación DOM no sustituye esta revisión.

El intento permitido de mostrar el archivo con `open_in_codex` devolvió `queued`. Las métricas de tiempo son las ya medidas por los experimentos; construir el tablero no vuelve a entrenar modelos.

`verificar.cjs` verifica lógica aislada en un DOM mínimo, no utiliza navegador. Sus salidas se guardan en `VERIFICACION-LOGICA.json`.
