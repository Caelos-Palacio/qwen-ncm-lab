# Fase 0: destilación por secuencias a mini-NCM

Se fija antes de la extracción del docente y del entrenamiento. La especificación ejecutable está en `PROTOCOLO.json`; las huellas de entrada, en `ENTRADA-FREEZE.json`.

Hipótesis: una implementación reducida de las clases oficiales puede reconstruir respuestas cortas y aprender a generar códigos desde preguntas sin recibir los códigos de la respuesta. Esto valida el procedimiento de destilación; no supone conservar el conocimiento general de Qwen.

Se usan 192 preguntas TRAIN, 32 DEV y 64 TEST de suma, resta y multiplicación de enteros de 0 a 30. Las unidades son operación y par de operandos; los pares conmutativos se canonizan. TEST contiene 32 casos con plantilla vista y 32 con una plantilla nueva. Esta última partición mide transferencia de formulación, no extrapolación numérica. Las respuestas exactas se calculan al crear el corpus, pero ningún dato TEST entra en entrenamiento ni selección.

Qwen genera como máximo 8 tokens, con temperatura cero y pensamiento cerrado. Se conservan todas las salidas crudas. Solo las respuestas que son enteros completos de hasta 8 bytes entran en KD; las respuestas incorrectas del docente se mantienen incorrectas. Los controles supervisados usan los mismos IDs admitidos. Se documentan todos los rechazos.

Se entrena el VQ-VAE oficial hasta 1500 pasos con entropía cruzada y pérdidas VQ, con dropout anidado oficial. Se selecciona la reconstrucción DEV y se congela. El Transformer oficial se entrena hasta 3000 pasos con corrupción del 5% de códigos de condición y CE media por escala. La selección usa generación libre DEV y, en empate, pérdida DEV. TEST se evalúa después de congelar los checkpoints. La generación libre recibe solo el prompt; la reconstrucción se mide por separado.

Se comparan docente, mini-NCM KD, la misma arquitectura con supervisión aritmética exacta, generador sin entrenar y vecino más próximo de TRAIN. Las métricas primarias son exactitud numérica y acuerdo con el docente. También se miden exactitud de caracteres sin PAD, UTF-8 inválido, formatos fallidos, utilización y entropía de códigos por escala.

Cada fase registra tiempo de pared, CPU, RSS muestreada del árbol de procesos, swap, pasos, parámetros y bytes de checkpoints. Se usa un solo trabajo pesado a la vez y CPU de 2 hilos para los estudiantes. No se estima energía a partir del tiempo ni se confunde menor número de pasos con menor FLOP medido.

Criterios: continuar hacia texto real solo si la arquitectura genera sin respuesta objetivo, el tokenizador reconstruye al menos 95% de caracteres no PAD DEV y no hay fallo numérico. Este umbral condiciona la fase 1; si el codec no lo alcanza, aun así se conserva y se evalúa el generador de fase 0 dentro del presupuesto fijado para localizar el fallo. Una generación sin ventaja sobre el control sin entrenar o el vecino de TRAIN indica que el aprendizaje no se ha demostrado. No se modifican presupuesto ni selección al observar TEST; un fallo se conserva como resultado.

La fase 1 requerirá corpus de texto real con licencia, TRAIN/DEV/TEST por documentos, salidas más largas y comparativa de calidad a coste comparable. No se inicia entrenamiento grande como parte de esta fase 0. La conversión directa de pesos Transformer→NCM no equivale a la destilación por secuencias y no se afirma haberla realizado.

## Enmienda previa al FIT: entrenamiento conjunto y eficiencia

La fase 0.1 parte del generador KD seleccionado y crea dos ramas de 500 pasos con los mismos ejemplos e inicialización: generador más decoder Transformer entrenados conjuntamente, y generador continuado con decoder fijo. No tienen el mismo coste por paso; se miden CPU y tiempo reales. El encoder, codebooks y convoluciones de reconstrucción RVQ permanecen fijos.

La ruta conjunta predice sus cuatro niveles propios desde el prompt. En forward usa códigos argmax duros; backward usa el gradiente de softmax mediante straight-through. La pérdida es CE del texto más 0.25 CE auxiliar por escala. Ningún código objetivo entra en el rollout de texto; solo sirve como etiqueta auxiliar. Se comprueba gradiente positivo del generador y del decoder conjunto, gradiente nulo de encoder/codebooks y coincidencia del forward duro con la inferencia oficial. Esta coadaptación es experimental y no se atribuye al entrenamiento publicado del paper.

Para ahorrar proceso, los primeros 50 pasos constituyen el scout medido y cuentan dentro del presupuesto. El tokenizador termina tras 400 pasos si reconstruye DEV perfectamente, o tras cuatro revisiones de 100 pasos sin mejorar exactitud, siempre con máximo 1500. Los generadores por etapas paran tras tres revisiones de 200 pasos sin mejorar exactitud DEV, con mínimo 600 y máximo 3000. El empate por CE elige checkpoint pero no reinicia la paciencia. Se cachean códigos RVQ y embeddings congelados del prefijo, sin desconectar la consulta aprendible del nivel 0. El docente TRAIN/DEV se obtiene una vez; TEST se obtiene una vez después de congelar todos los checkpoints.

## Ajuste operativo por prioridad del usuario al coste del proceso

Tras el cierre KD por la regla DEV al paso1400, se interrumpió el proceso propio para no completar el control supervisado opcional. El control ya había guardado un checkpoint al paso200; se conserva solo como comparación exploratoria de presupuesto desigual. El tiempo gastado hasta la señal, incluidos unos63.9s después del cierre KD, figura en el run integral y no se declara cero. La fase conjunta y el control de decoder fijo continúan desde KD mediante un runner dedicado. No se había abierto TEST.
