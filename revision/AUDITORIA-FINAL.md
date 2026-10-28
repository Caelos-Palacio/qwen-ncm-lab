# Auditoría final: fase 0 y extensión conjunta 0.1

20 de octubre de 2026. Revisión independiente de fuentes y artefactos, sin nuevas inferencias, reentrenamientos ni cambios de pesos. Proyecto: `/home/carlos/qwen-ncm-lab/`.

**Conclusión:** la implementación ejecutó un mini-NCM real y su extensión conjunta diferenciable; el estudiante **no aprendió a resolver problemas nuevos con utilidad** en esta prueba. Su menor latencia no constituye eficiencia a calidad equivalente. La corrida aporta un fallo reproducible de generación/generalización, con codec capaz de reconstruir las respuestas.

## Comprobaciones de integridad y cronología

| Comprobación | Resultado y evidencia |
|---|---|
| Arquitectura | PASS por lectura: clases oficiales VQVAE y NextConceptTransformer; RVQ residual `[1,2,4,8]`, cuatro bloques del generador y decoder neuronal. La ruta ST es una extensión local identificada. |
| Datos | PASS: TRAIN192/DEV32/TEST64; intersecciones de IDs y prompts entre particiones 0; espejos de suma/multiplicación excluidos por construcción. TEST32 plantilla vista y32 nueva. |
| Congelación | PASS: los18 hashes de pesos, código, protocolo y particiones de CHECKPOINTS-FREEZE coinciden con archivos activos. Freeze a16:04:13 UTC, anterior a inicio teacher-test16:04:16 UTC. |
| Selección | PASS por flujo y registros: checkpoints elegidos con DEV; archivo freeze declara TEST del maestro todavía no obtenido. El protocolo fue enmendado durante el proceso antes de TEST; esa cronología se conserva. No se certifica un protocolo único e inalterado desde el principio. |
| Predicciones | PASS:448 registros; siete métodos con64 IDs únicos cada uno y exactamente el conjunto TEST. El hash de PREDICCIONES y su vínculo al freeze de checkpoints coinciden. |
| Recuento independiente | PASS: se recalculó exactitud entera desde cada texto y referencia TEST usando biblioteca estándar; coincide con correct guardado y RESULTADOS. |
| Maestro | PASS: salidas crudas preservadas, parseo entero completo, objetivos admitidos sin sustituir errores del maestro; caché verifica hash del request antes de reanudar por ID. |
| Inferencia autónoma | PASS por código: generación recibe prompt y códigos propios; no recibe objetivo ni código verdadero TEST. El vecino TRAIN utiliza campos aritméticos privilegiados y está identificado. |

La separación es procedimental: las referencias exactas de aritmética existen en disco desde la preparación, pero no aparecen en las rutas de entrenamiento/selección como datos TEST. No se afirma custodia criptográfica inaccesible al ejecutor.

## Entrenamiento conjunto y continuidad

El decoder se entrena desde la CE del texto generado con embeddings duros en forward y gradiente softmax mediante straight-through. La reconstrucción acumulada se compone con operaciones diferenciables, evitando los métodos oficiales decorados con `no_grad` para esa ruta. Encoder, codebooks y operadores RVQ permanecen fuera del optimizador.

`PREFIT-GRADIENTES.json` conserva prueba de pérdida **solo de texto**: norma generador1,071986; decoder7,631765; query inicial0,011603; encoder/codebooks0. Además, `JOINT-FIT.json` registra en el arranque desde KD gradiente de texto→generador0,021242 en ambos modos y gradiente total decoder0,055784 en joint frente a0 en continued. Los códigos duros del rollout coinciden con inferencia oficial en el control conservado. Esto valida el cableado del gradiente, no el aprendizaje generalizable.

Joint y continued recargan el mismo checkpoint KD y reinician la misma semilla antes de construir modelo y tomar minibatches. Corren500 pasos cada uno con dropout0. El control continued también recibe CE de texto, pero mantiene decoder fijo. El presupuesto en pasos está emparejado; el coste computacional real se mide y puede diferir.

KD terminó con regla DEV a1400 pasos; se seleccionó checkpoint800. La condición supervisada opcional fue interrumpida con señal−15 para limitar gasto, conservando checkpoint200; el número real de actualizaciones queda acotado200–399. `PARADA-PLANIFICADA.json`, `SUPERVISED-PARCIAL.json` y fit-RUN preservan la intervención y su coste. No permite una comparación causal concluyente de destilación frente a supervisión exacta.

## Resultados recomputados

| Método | Aciertos TEST /64 | Plantilla vista /32 | Nueva /32 |
|---|---:|---:|---:|
| Qwen original |58|31|27|
| NCM KD |1|1|0|
| Referencia exacta parcial |0|0|0|
| Generador sin entrenar |0|0|0|
| NCM + decoder conjunto |0|0|0|
| NCM continuado, decoder fijo |0|0|0|
| Vecino TRAIN privilegiado |1|1|0|

La reconstrucción del **codec del checkpoint KD** obtuvo64/64 secuencias completas y100% posiciones sin PAD sobre objetivos del maestro admisibles. No se confunde con generación libre. No se midió aquí de nuevo la reconstrucción de cada decoder adaptado; ese diagnóstico no puede extrapolarse al checkpoint joint.

El generador sin entrenar emitió `11111` en64/64 casos. Los entrenados producen salidas variadas: KD usa4/11/20/37 códigos distintos por nivel; joint4/11/23/38. Por tanto, los resultados no son un colapso global a un solo código o a una única respuesta, aunque esto no excluye restricciones de representación. Hay aprendizaje de distribución/formato y pérdida TRAIN baja, con casi nula exactitud heldout. La explicación compatible con los datos es sobreajuste y mala transferencia del prompt a la solución; no se identificó todavía una causa única ni se demuestra una limitación general de NCM.

Ejemplos conservados, sin nueva inferencia:

| Prompt | Referencia | Qwen | Joint |
|---|---:|---:|---:|
| Compute28−4 |24|14|28|
| Compute5×16 |80|80|130|
| Compute11−24 |−13|−13|3|
| Compute0+23 |23|23|29|

El maestro también tiene errores; sin embargo,58/64 frente a0–1/64 del estudiante indica una pérdida de capacidad mucho mayor que el error docente por sí solo.

## Coste auditado

Estudiante completo:1.034.816 parámetros; KD checkpoint4.268.662 bytes (4,07MiB), incluyendo codec y generador. Inferencia estable batch1 incluye embeddings, cuatro niveles y decoder, con carga y un calentamiento excluidos.

| Método | Wall media por pregunta | CPU media por pregunta |
|---|---:|---:|
| Qwen |657,04ms|2955,94ms|
| NCM KD |15,59ms|31,19ms|
| Joint |15,25ms|30,55ms|
| Continued |15,59ms|31,16ms|

Qwen usa más parámetros, otro runtime y4 hilos de generación/8 prefill; estudiantes2 hilos. El dato demuestra menor latencia del prototipo, **no ahorro útil manteniendo calidad**, ni una comparación aislada del algoritmo con igual capacidad.

Cinco runs principales, sumados una sola vez: teacher-train-dev, fit, joint-fit, teacher-test y evaluacion. Total medido: **865,717380 segundos wall y2179,638114 CPU-segundos**. Es suma de fases instrumentadas, no toda la duración humana entre inicio y cierre. Incluye el supervisado parcial y overhead de procesos. No sumar encima codec/KD/joint internos, porque ya están dentro de esos runs.

Las dos demostraciones posteriores registradas añaden2,408963 y2,412617 segundos wall, y2,400903 y2,397426 CPU-segundos. Con ambas: **870,538960 segundos wall y2184,436443 CPU-segundos**. Si se generan más demostraciones, ampliar este subtotal sin volver a entrenar ni mezclarlo con la medición estable por pregunta.

Picos muestreados del árbol entre los runs: RSS925,34375MiB y swap197,61719MiB. Son máximos por proceso/árbol muestreado a0,2s, no suma de picos ni atribución de toda la swap del sistema. El pico de joint-fit fue598,46MiB RSS. Los scouts están incluidos en los pasos reales. Las proyecciones a máximos no se presentan como cómputo ejecutado.

El tokenizer ejecutó400/1500 pasos y KD1400/3000:2700 actualizaciones menos que esos máximos. Es una reducción de trabajo planificado por parada DEV, no una estimación de FLOPs ni una comparación contra una corrida completa que no se ejecutó.

## Manifiesto y cierre

Al revisar MANIFEST se comprobaron73 entradas: todos los archivos enumerados coincidían salvo RUNS.jsonl, actualizado por demostraciones posteriores a crear el manifiesto. Los checkpoints y predicciones congelados permanecen íntegros. Se comunicó al ejecutor regenerar el manifiesto tras terminar demostraciones y añadir esta auditoría. Es un desfase de inventario de logs, no evidencia de cambio de resultados. El estado final de ese refresco se añade debajo una vez verificado.

**Dictamen:** ejecución y arquitectura válidas para el piloto; transferencia útil y generalización de aritmética no demostradas, con resultado negativo claro. El coentrenamiento requerido sí tuvo ruta de gradiente real y tampoco mejoró TEST. No escalar este checkpoint como si ya fuera un generador de lenguaje útil. La fase1 de texto real sigue siendo diseño pendiente.
