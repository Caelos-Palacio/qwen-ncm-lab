# Revisión independiente del contenido del tablero

20 de octubre de 2026. Alcance: lectura estática del HTML, código del modelo, protocolo, resultados y costes. No se ejecutaron inferencias, entrenamiento ni navegador. No se editaron pesos, HTML, resultados congelados ni el manifiesto raíz.

**Dictamen: contenido fiel a la prueba, sin discrepancias materiales identificadas.** La revisión renderizada corresponde al agente constructor; este documento no la sustituye.

## Arquitectura y resultados

- Destilación por secuencias Qwen→mini-NCM, sin conversión de pesos. Qwen permanece congelado y fuera de la inferencia del estudiante.
- Generador de cuatro bloques, dimensión128, cuatro cabezas; cuatro escalas [1,2,4,8], códigos paralelos dentro de cada escala y dependencia entre escalas. No se afirma generar las cuatro escalas simultáneamente.
- Codec199.296 parámetros; generador835.520; total1.034.816. Decoder Transformer66.496, entrenable junto al generador en la rama conjunta;902.016 parámetros ajustables. Ese decoder no procede de pesos Qwen.
- Straight-through duro en forward y softmax en backward; gradiente de texto hacia generador y decoder. Encoder, codebooks y convoluciones RVQ permanecen congelados. No se atribuye el gradiente del decoder al encoder congelado ni se presenta argmax como diferenciable exactamente.
- Calidad libre: Qwen58/64; KD1/64; joint0/64; continued0/64. Reconstrucción64/64 claramente atribuida al codec KD congelado anterior a joint, recibiendo respuesta, separada de resolver desde el prompt.
- TRAIN192/DEV32/TEST64, pares conmutativos sin cruzar particiones;32 plantillas vistas y32 nuevas. Congelación de checkpoints anterior a TEST. Se identifica una semilla y la referencia supervisada parcial200 de presupuesto desigual.
- El marco de siguiente protocolo está identificado como «Propuesto · No entrenado». El TEST anterior ya examinado queda como diagnóstico; propone TEST nuevo y controles de aprendizaje y autorregresión equivalentes. Es plan, no resultado ejecutado.

## Costes y comparaciones

- Se separan pared y CPU-segundos, modelos cargados de coste de proceso, RSS de payload, costes NCM de memoria Qwen y métricas aritméticas de F1 QASPER.
- Totales865,72s/2179,64CPU-s corresponden a cinco procesos principales sin solapamiento; demos aparte870,54s/2184,44CPU-s. Las subfases no se duplican en la suma.
- Coste de referencia parcial63,89s/interrupción y presupuesto desigual están presentes en detalle. Se identifican muestreo RSS/swap, hilos distintos y ausencia de medición de energía/FLOPs.
- Tabla R16 presenta medias por pregunta, consulta frente a total reconstruido e ingesta compartida. BM25 combina indexación medida después con consultas originales; no se disfraza como reloj único end-to-end. No se suman variantes compartidas como coste real de toda la corrida.
- Menor latencia de estudiante1M frente a Qwen0,8B no se anuncia como eficiencia a calidad equivalente. Códigos discretos no se afirman conceptos semánticos explícitos. El buffer FFN21 y NCM son proyectos separados.

## Accesibilidad estática y enlaces

- Documento español, jerarquía de títulos, navegación rotulada, botones nativos, foco visible, instrucciones de teclado, dialog nativo y cierre identificado. Modo lectura permite reflujo sin zoom del lienzo y se activa en anchura pequeña.
- Siete marcos encontrados; nueve vínculos locales comprobados, ninguno ausente; no se encontraron IDs duplicados.
- Contrastes calculados: texto principal14,30:1; secundario6,60:1; enlaces7,80:1; navegación activa14,44:1; texto verde sobre fondo de aprendizaje6,46:1. Esto cubre pares de texto principales, no constituye certificación integral de accesibilidad.
- No hay afirmaciones de comprobación visual, lector de pantalla o interacción real por este revisor. El constructor informó que CUA rechazó file:// por política; no hay verificación renderizada ni capturas de esta entrega. Sus comprobaciones JS/DOM simuladas no sustituyen navegador real.

Fuentes contrastadas: INFORME.md, PROTOCOLO.md/.json, modelo.py, joint.py, GENERATOR-FIT.json, RESUMEN-COSTE.json, revision/AUDITORIA-FINAL.md; R16/INFORME.md y ronda17/costes/INFORME-COSTES.md.

HTML revisado SHA256: `021f7236025f6fa077427be47b3a2f857324b0de6e2bd19fd493a1e129f606e7`. Huella de esta lectura, sin modificar manifiestos congelados.
