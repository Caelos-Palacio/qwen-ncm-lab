# Qwen → mini-NCM: resultados de fase 0 y coadaptación 0.1

Cierre: 2026-10-20T16:08:14.477239+00:00.

Se creó un proyecto separado con pesos e inferencia autónomos. El prototipo usa las clases oficiales de NCM: un VQ-VAE residual de cuatro escalas y un Transformer que predice todos los códigos de cada escala en paralelo. La variante conjunta entrena además el decoder Transformer desde el texto generado con straight-through. El Qwen original no se modifica.

La tarea es aritmética de enteros 0–30, salida de hasta 8 bytes. TRAIN 192, DEV 32 y TEST 64 se fijaron antes del entrenamiento; los pares conmutativos no cruzan particiones. TEST contiene 32 prompts de plantilla vista y 32 de plantilla inédita. La novedad de plantilla mide transferencia de formulación, no extrapolación numérica.

## Calidad de generación libre

| Modelo | Aciertos /64 | Exactitud | Plantilla vista /32 | Plantilla nueva /32 | Acuerdo docente |
|---|---:|---:|---:|---:|---:|
| Qwen original | 58 | 90.62% | 31 | 27 | 100.00% |
| NCM KD por etapas | 1 | 1.56% | 1 | 0 | 1.56% |
| NCM referencia exacta parcial200 (exploratorio) | 0 | 0.00% | 0 | 0 | 0.00% |
| NCM generador sin entrenar | 0 | 0.00% | 0 | 0 | 0.00% |
| NCM + decoder conjunto | 0 | 0.00% | 0 | 0 | 0.00% |
| NCM continuado, decoder fijo | 0 | 0.00% | 0 | 0 | 0.00% |
| Vecino TRAIN privilegiado | 1 | 1.56% | 1 | 0 | 1.56% |

La inferencia recibe solo el prompt y sus propias predicciones anteriores. Los códigos de respuesta no entran en el rollout libre. La reconstrucción del codec es una medición separada. El vecino TRAIN recibe operación y operandos estructurados: es un control de memorización privilegiado, no una comparación arquitectural equitativa.

## Codec y gradiente de texto

El codec tiene 199,296 parámetros. Se entrenó 400 pasos y se seleccionó solo con los 31 DEV cuyo objetivo docente era un entero admisible. La reconstrucción TEST del codec congelado de `kd.pt` (anterior al entrenamiento conjunto): 100.00% caracteres sin PAD y 100.00% secuencias completas (64 objetivos admisibles).

- NCM + decoder conjunto: norma del gradiente de texto→generador 0.0212423; gradiente total decoder 0.0557843; encoder 0.0; codebooks 0.0. Forward duro coincide con la inferencia oficial.
- NCM continuado, decoder fijo: norma del gradiente de texto→generador 0.0212423; gradiente total decoder 0; encoder 0.0; codebooks 0.0. Forward duro coincide con la inferencia oficial.

Los codebooks, encoder y convoluciones RVQ quedan fijos en la fase conjunta. Los códigos son duros en forward y usan la derivada de softmax en backward; es una aproximación straight-through, no una derivada del argmax discreto. El decoder recibe gradiente de texto junto al generador. No se evaluó la reconstrucción del decoder después de la coadaptación conjunta; el 100% de reconstrucción pertenece al codec de KD por etapas. Se guarda también un smoke test independiente de gradiente solo de texto en `PREFIT-GRADIENTES.json`.

## Coste real del proceso

Los cinco procesos principales consumieron 865.72 segundos de pared sumados y 2179.64 CPU-segundos; no se solaparon. Con las dos demos CLI: 870.54 s y 2184.44 CPU-s. Es coste de ejecución medido, no tiempo transcurrido del usuario ni coste de investigación, instalación o pausas.

| Fase | Pared s | CPU s | Pasos reales |
|---|---:|---:|---:|
| Docente TRAIN/DEV224 consultas | 151.32 | 662.27 | — |
| Codec | 7.74 | 13.17 | 400 /1500 |
| NCM KD por etapas | 263.34 | 526.50 | 1400 |
| NCM + decoder conjunto | 159.76 | 319.46 | 500 |
| NCM continuado, decoder fijo | 159.92 | 319.73 | 500 |
| teacher-test | 44.02 | 190.97 | — |
| evaluacion | 8.44 | 13.19 | — |
| Referencia exacta parcial, interrumpida | 63.89 | no atribuible por separado | checkpoint200; trabajo entre200–399 |

Se evitaron 2700 actualizaciones respecto a los máximos originales mediante las reglas DEV fijadas antes del FIT. Los 50 pasos de scout están incluidos en los totales; no son entrenamiento extra. Los códigos RVQ y los embeddings congelados se cachearon. El coste docente TEST se paga una vez y se reutiliza en todas las comparaciones.

El scout del codec mide pared después de crear el optimizador, mientras su CPU incluye esa inicialización: sus ámbitos difieren. El total de la fase codec sí incluye ambas. Las proyecciones de scouts son estimaciones, no ahorros medidos.

| Proceso | RSS máxima árbol MiB | Swap máxima árbol MiB |
|---|---:|---:|
| teacher-train-dev | 924.88 | 85.74 |
| fit | 522.55 | 83.69 |
| joint-fit | 598.46 | 197.62 |
| teacher-test | 925.34 | 0.00 |
| evaluacion | 301.05 | 0.00 |
| demo | 286.73 | 0.00 |
| demo-train | 286.79 | 0.00 |

Los subtotales de codec/generadores están dentro de los runs integrales fit/joint-fit y no deben sumarse otra vez a estos. Los máximos del árbol son muestras cada 0.2 s, no suma de máximos individuales. La swap global se registra aparte y no se atribuye al modelo. CPU y pared se obtienen del proceso hijo real; el entrenamiento usa 2 hilos. Qwen conserva 4 hilos de generación y 8 de prefill, especificados por el motor.

## Inferencia estable

| Modelo | Pared media ms | Pared p95 ms | CPU media ms | Checkpoint MiB |
|---|---:|---:|---:|---:|
| Qwen original | 657.044 | 710.704 | 2955.937 | GGUF original separado |
| NCM KD por etapas | 15.594 | 16.020 | 31.186 | 4.07 |
| NCM referencia exacta parcial200 (exploratorio) | 15.488 | 16.419 | 30.954 | 4.08 |
| NCM generador sin entrenar | 15.783 | 16.723 | 31.560 | 4.08 |
| NCM + decoder conjunto | 15.249 | 15.923 | 30.545 | 4.07 |
| NCM continuado, decoder fijo | 15.586 | 16.251 | 31.158 | 4.08 |

Batch 1; estudiante 2 hilos, carga excluida y un calentamiento excluido. Incluye embeddings del prompt, cuatro forwards del generador y decoder paralelo. Los parámetros y runtimes difieren de Qwen: una menor latencia no prueba mayor eficiencia a calidad equivalente. La carga y el coste docente/entrenamiento se presentan aparte. No se adopta la cifra de aceleración publicada del paper para este equipo.

## Procedencia y límites de la transferencia

Docente TRAIN: 186/192 aciertos; DEV: 30/32. TRAIN admitió 192 y DEV 31 objetivos. Los errores del docente se conservaron, no se sustituyeron por resultados exactos. La destilación es de secuencias, no conversión de sus pesos ni de toda su capacidad.

La variante supervisada comparte el codec aprendido de respuestas Qwen, mismos IDs admitidos, arquitectura y semilla. Se interrumpió para ahorrar proceso por instrucción del usuario; se evalúa su checkpoint200 solo como comparación exploratoria de presupuesto desigual, sin inferencia causal de KD frente a supervisión. El run integral fit incluye el trabajo parcial y terminó con señal−15 planificada USER_PROCESS_EFFICIENCY, no un fallo numérico. Joint y continuado parten del mismo checkpoint, mismos 500 pasos y minibatches; el gradiente adicional del decoder cambia el coste real. Hay una semilla: los 64 problemas no representan 64 entrenamientos independientes.

La fase 1 de texto real con licencia queda como diseño posterior. Este resultado permite examinar codec, generación, sobreajuste y coadaptación; no es aún un modelo general de lenguaje.

Fuentes: [paper NCM](https://arxiv.org/abs/2610.14162), [código oficial MIT](https://github.com/HazyResearch/ncm). Commit: `c70274273f489abc73832b2b98584a8483b6b203`.
