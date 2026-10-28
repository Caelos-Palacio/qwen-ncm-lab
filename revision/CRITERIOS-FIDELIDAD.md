# Criterios de fidelidad y evaluación: estudiante NCM de Qwen

Revisión independiente, 20 de octubre de 2026 (America/Bogota). Este documento fija criterios para el prototipo; no certifica resultados de un entrenamiento todavía no inspeccionado.

## Fuentes primarias verificadas

El artículo existe: **Next-Concept Modeling: Fast, Parallel Coarse-to-Fine Text Generation**, arXiv 2610.14162v1, publicado el 9 de octubre de 2026. Describe dos etapas: aprender un tokenizer RVQ multiescala con reconstrucción de texto, congelarlo y entrenar un Transformer que genere códigos por niveles. El paralelismo ocurre dentro de cada nivel. Los códigos son discretos aprendidos; llamarlos conceptos no demuestra que sean categorías humanas interpretables. El artículo no requiere destilación de un maestro. Nuestra destilación desde Qwen sería una adaptación adicional. [Artículo y secciones 3, C](https://arxiv.org/html/2610.14162v1).

El [repositorio oficial](https://github.com/HazyResearch/ncm) es público y MIT. Ofrece checkpoints separados del tokenizer y del generador, configuraciones y evaluación. El ejemplo TinyStories contiene 12 niveles crecientes hasta 128 posiciones, diccionarios de 4096 códigos, latentes de 384 dimensiones y un generador de 12 bloques/ancho 768. Son referencias publicadas, **no tamaños mínimos obligatorios**. [Configuración oficial](https://raw.githubusercontent.com/HazyResearch/ncm/main/config/eval/tinystories.yaml).

El código permite revisar los mecanismos concretos: [generador](https://raw.githubusercontent.com/HazyResearch/ncm/main/models/next_concept.py), [VQ-VAE](https://raw.githubusercontent.com/HazyResearch/ncm/main/models/vqvae.py), [interfaz del tokenizer](https://raw.githubusercontent.com/HazyResearch/ncm/main/tokenization/vqvae_tokenizer.py). La interfaz devuelve logits de todas las posiciones y reconstrucciones parciales. El generador acumula contribuciones de códigos, redimensiona esa reconstrucción y predice el siguiente nivel; ofrece atención por bloques y prefijo condicional. La opción publicada TinyStories toma el primer código de una distribución marginal guardada, mientras el generador también admite aprenderlo desde el prefijo. Por tanto, documentar exactamente cómo nace el primer nivel; no asumir que todos los checkpoints lo predicen del mismo modo.

El evaluador publicado requiere GPUs visibles y el ejecutor usa `.cuda()` explícitamente. Reducir el batch no lo convierte automáticamente en ejecutable CPU: nuestro camino CPU debe adaptar esas operaciones o implementar la misma arquitectura y registrar la desviación. [Entrada de evaluación](https://raw.githubusercontent.com/HazyResearch/ncm/main/evaluate.py), [ejecutor](https://raw.githubusercontent.com/HazyResearch/ncm/main/scripts/eval_shard.py).

## Condiciones propuestas para aceptar el prototipo

Los siguientes son criterios locales de esta revisión, no umbrales prometidos por el artículo.

| Componente | Evidencia exigida |
|---|---|
| Tokenizer aprendido | Parámetros guardados de encoder, codebooks y decoder. Pérdida de reconstrucción de texto, y tratamiento explícito del paso discreto: estimador directo/straight-through o alternativa documentada. |
| Residuo multiescala | Al menos dos longitudes estrictamente crecientes, última igual a la longitud de salida. Cada nivel cuantiza el residuo dejado por anteriores y suma una contribución a la reconstrucción. No basta asignar agrupaciones independientes. |
| Jerarquía utilizable | Reconstrucciones heldout por nivel, uso/entropía de cada codebook, errores de cuantización y comparación con usar solamente el último nivel. Nested dropout o reconstrucción de prefijos ayuda a entrenar el uso de niveles tempranos; si se omite, declararlo y medir el resultado. |
| Generador NCM | Transformer compartido con atención contextual; entradas contienen prefijo y reconstrucción de niveles previos, sin códigos verdaderos del nivel a predecir. Predicción simultánea de sus posiciones. Guardar trazas de formas y número de llamadas. |
| Decoder | Red aprendida que produce texto desde la reconstrucción final, sin pedir a Qwen que redacte o repare la salida. Toda reparación externa debe medirse aparte. |
| Inferencia autónoma | En TEST, acceder solamente al prompt y pesos del estudiante. Ni respuesta del maestro ni códigos de respuesta verdadera ni vecinos buscados en TEST. |
| Destilación verificable | Corpus que identifica prompts TRAIN y respuestas realmente emitidas por nuestro Qwen, hash del GGUF, parámetros de generación y recuento. El estudiante recibe supervisión de esas respuestas. Reutilizar el tokenizer de Qwen o ajustar una regresión sobre activaciones por sí solo no demuestra destilación de generación. |

Una implementación NumPy del entrenamiento es válida si implementa y verifica esos mecanismos. Un MLP, clustering de embeddings o regresión con códigos puede servir de control, pero debe etiquetarse como aproximación, no como reproducción del Transformer NCM.

## Reducción CPU viable propuesta

Para este equipo de 7,3 GiB sin GPU, propongo inicialmente un **dominio de respuestas breves**, sin prometer conversación general. Configuración orientativa: bytes UTF-8 más PAD/EOS (258 símbolos), longitud 32 o 64, latente 32 o 64, cuatro niveles `[1, 4, 16, 32]` o `[1, 4, 16, 64]`, 32–64 códigos por nivel, generador de dos bloques/ancho 64 con cuatro cabezas, decoder contextual de un bloque y batch 8–16. Esta selección es un presupuesto de ingeniería propio, no configuración evaluada en el paper.

Mantener los buffers, entrenamiento, pesos y corpus del estudiante aislados de Qwen. Ejecutar el maestro para capturar TRAIN y cerrarlo antes de entrenar al estudiante si compiten por memoria. Medir el pico real: los pesos pequeños no incluyen activaciones, gradientes, optimizador ni bibliotecas.

Los bytes reducen vocabulario, pero cambian unidades y longitud: registrar bytes y caracteres, no presentar 64 bytes como 64 tokens Qwen. Medir cobertura de respuestas y truncamiento antes del entrenamiento. Para castellano, medir validez UTF-8 y no ocultar bytes inválidos mediante un decoder que los descarte silenciosamente. Una tarea de salida corta facilita la primera prueba; se debe declarar su alcance explícitamente.

No hace falta copiar los grandes checkpoints oficiales para entrenar este prototipo. Reducir dimensiones y datos conserva la estructura; eliminar el mecanismo jerárquico, el Transformer o el decoder aprendido cambia la arquitectura.

## Diseño de la comparación

1. Separar TRAIN/DEV/TEST por documento o problema original antes de generar variantes. Evitar que paráfrasis o plantillas del mismo ejemplo atraviesen divisiones. Guardar lista y hash antes de entrenar; elegir hiperparámetros solo con DEV.
2. Capturar respuestas de Qwen para TRAIN y, si hace falta selección, DEV. TEST humano u objetivo permanece independiente. Medir al maestro en los mismos prompts para conocer la calidad realmente disponible para destilar.
3. Entrenar dos estudiantes con **misma arquitectura, tokenizer, inicialización emparejada y presupuesto de actualizaciones**: destilado con respuestas Qwen; control sin destilación con referencias originales de TRAIN. Mantener el tokenizer compartido entrenado exclusivamente sobre TRAIN y especificar su corpus. Si cada tokenizer usa corpus distinto, esa diferencia también forma parte del efecto.
4. Si no existen referencias humanas/objetivas, reportar solo imitación del maestro y el control pertinente; no llamar «sin destilación» a un estudiante aleatorio y concluir que se transfirió capacidad. Añadir un control de etiquetas del maestro permutadas permite detectar memorización o ausencia de condicionamiento, pero no sustituye el control entrenado real.
5. Congelar pesos y configuración antes de TEST. Evaluar generación libre por niveles, además de predicción con niveles previos verdaderos: esta última es diagnóstico y sobreestima la generación autónoma.

## Métricas mínimas y diagnóstico

- **Tokenizer heldout:** exactitud de posiciones excluyendo PAD, exactitud de secuencia completa, pérdida CE, reconstrucción por nivel, uso y entropía de códigos; tasa de truncamiento y UTF-8 inválido. Incluir exactitud sobre PAD por separado para detectar una cifra inflada por relleno.
- **Generador:** CE y exactitud de códigos por nivel con historial verdadero, junto con las mismas métricas bajo historial generado. Separarlas revela propagación de error. Si las reconstrucciones son buenas y generación falla, no culpar al codec.
- **Utilidad:** F1/EM o exactitud de tarea frente a referencias independientes, fidelidad a Qwen por separado, varias respuestas visibles con prompt y referencia. Para tarea abierta, diversidad y repetición evitan premiar una salida común para todos los prompts. Un TEST de 24 ejemplos sirve de exploración, no como prueba suficiente de utilidad general.
- **Coste:** tiempo total del maestro, entrenamiento de tokenizer y generador, tiempo por respuesta estudiante incluyendo decoder, CPU-segundos, pico RSS y tamaño total de artefactos. Para inferencia, repeticiones con calentamiento separado y mediana/p95; declarar hilos y longitud efectiva.
- **Comparación justa:** mismo equipo y prompts, medidas de Qwen y estudiante serializadas para no contaminar latencias. Paralelizar investigación/implementación no obliga a ejecutar simultáneamente los benchmarks pesados. Dar curva calidad–latencia: ser menor y más rápido con texto roto no es una mejora útil.

Los speedups publicados frente a difusión no son una predicción de aceleración frente a nuestro Qwen en CPU. Tampoco deben sumarse los pasos del generador sin contar decoder y prefijo. Cualquier afirmación de beneficio se apoya en la comparación local medida.

## Regla de cierre

Entregar pesos cargables, comando de inferencia del estudiante, corpus/procedencia, curvas TRAIN/DEV y resultados TEST congelados aunque sean negativos. Si el entrenamiento no produce texto útil, entregar el prototipo y el fallo medido; no reemplazarlo silenciosamente por plantillas ni llamarlo conversor completo de Qwen a NCM.

## Aplicación al plan inicial comunicado por el orquestador

El plan local comunicado consiste en aritmética de suma, resta y multiplicación con operandos de 0 a 30: TRAIN 192, DEV 32 y TEST 64, dividido por operación y pareja de operandos; 32 TEST usan plantilla vista y 32 plantilla nueva. El VQ-VAE propuesto tiene latentes 64, niveles `[1, 2, 4, 8]` y 64 códigos por nivel; el Transformer tiene ancho 128 y cuatro bloques; prefijo de 64 bytes y salida de 8 bytes. Presupuestos máximos 1500/3000 actualizaciones y dos hilos CPU. Controles previstos: supervisión exacta con la misma arquitectura, modelo no entrenado y vecino TRAIN. Esta sección registra el plan, **no afirma su ejecución ni resultados**.

El plan puede conservar fidelidad NCM pese a ser pequeño. Para el cierre, verificar particularmente:

- Suma y multiplicación deben canonizar pares conmutativos o agrupar sus espejos. En resta, agrupar también ambos sentidos es más estricto; registrar cuál regla se aplicó. Revisar intersección de parejas y de cadenas exactas entre particiones.
- Ocho bytes bastan para los resultados enteros de ese rango, pero una respuesta Qwen puede incluir explicación o formato. Registrar respuestas completas, truncadas, inválidas y cualquier extracción posterior, y aplicar la misma regla declarada a entrenamiento y evaluación.
- La proporción de PAD puede dominar una secuencia tan corta: informar exactitud de caracteres/bytes sin PAD y EM del resultado numérico completo. Una respuesta vacía o EOS inmediato no debe contar como acierto de posiciones de relleno.
- Asegurar que TEST libre no llama al encoder con la respuesta ni toma códigos iniciales verdaderos. Para el primer nivel, generar desde el prompt o distribución aprendida TRAIN, nunca desde el objetivo TEST.
- Separar acierto aritmético frente a referencia exacta de coincidencia con Qwen. El maestro puede equivocarse; el control de supervisión exacta cuantifica esa fuente de error.
- La transferencia entre dos plantillas no es todavía transferencia a operaciones, idiomas o longitudes nuevas. Nombrarla por su alcance concreto.

No se añade una barrera previa al entrenamiento: estas comprobaciones se auditan sobre los artefactos producidos y se registran aunque el resultado sea negativo.
