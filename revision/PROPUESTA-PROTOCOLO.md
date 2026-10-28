# Protocolo propuesto para Qwen–NCM Lab

Fecha: 20 de octubre de 2026. Diseño y revisión independiente. Este proyecto tiene ruta propia, `/home/carlos/qwen-ncm-lab/`; la ronda 17 del laboratorio de memoria es procedencia histórica, no el directorio activo de entrenamiento. El piloto de aritmética ya aprobado continúa con su presupuesto. La fase de texto real se diseña aquí y no autoriza por sí sola una nueva corrida extensa.

Actualización de objetivo: el usuario pide **alta eficiencia y aprendizaje conjunto del Transformer conceptual y del decoder a texto**, además del control NCM de dos etapas. La destilación Qwen es una fuente de supervisión para las pruebas, no el objetivo exclusivo ni una obligación de imitar su arquitectura. La extensión conjunta se identifica separadamente del NCM oficial.

Prioridad posterior del usuario: **eficiencia del proceso de experimentación y entrenamiento**. Prevalece sobre ejecutar todos los controles extensos descritos como opciones: el mínimo práctico es piloto destilado más extensión conjunta y snapshot/control; la condición supervisada completa se ejecuta solo si entra en el presupuesto comunicado. Toda desigualdad de cómputo se informa. No se añaden corridas por este documento.

## Pregunta e hipótesis

¿Un estudiante pequeño con representación discreta jerárquica puede aprender de las respuestas de Qwen y producir respuestas autónomas útiles, con menos coste de inferencia medido?

- **H0-D, transferencia:** a igual arquitectura, tokenizer, ejemplos admitidos e inicialización, las respuestas Qwen no mejoran la calidad heldout frente a entrenar con referencias exactas. El efecto puede ser cero o negativo.
- **H1-D, transferencia:** el estudiante destilado obtiene una diferencia positiva de calidad heldout frente al control de referencias exactas. Una comparación inconclusa no rechaza H0-D.
- **H0-C, eficiencia útil:** no existe una ventaja de coste local que conserve el nivel de calidad acordado. Menos pasos o menos parámetros por sí solos no la refutan.
- **H1-C, eficiencia útil:** para la tarea delimitada, el estudiante alcanza una calidad útil declarada y reduce latencia/CPU-segundos frente al maestro en el mismo equipo. El coste de preparación y entrenamiento se informa por separado, junto con el punto de amortización si puede calcularse con mediciones comparables.
- **Hipótesis de mecanismo:** si el codec reconstruye bien pero la generación libre falla, el cuello está después de la codificación; si falla también la reconstrucción heldout, se pierde información antes de generar. Comparar ambos resultados permite localizar el fallo sin atribuirlo automáticamente a toda la arquitectura NCM.

En el piloto no se fija retrospectivamente un umbral de éxito según el resultado. Se presentan diferencias y sus denominadores. No se exige superar a Qwen para considerar válida la ejecución del experimento.

## Arquitectura y significado de destilación

La referencia primaria es [Next-Concept Modeling](https://arxiv.org/html/2610.14162v1), con [implementación oficial](https://github.com/HazyResearch/ncm). El estudiante conserva tres componentes: codec neuronal RVQ multiescala, Transformer que genera niveles y decoder aprendido que convierte la reconstrucción latente a texto. El generador condiciona cada nivel en la reconstrucción acumulada anterior; sus posiciones se predicen simultáneamente.

**Destilación de secuencias** significa entrenar al estudiante con salidas realmente producidas por Qwen, guardadas con su procedencia. No equivale a convertir los pesos GGUF de Qwen en pesos NCM ni a transferir toda su capacidad. La inferencia final del estudiante no llama al maestro, no recupera la respuesta TEST y no usa una plantilla que escriba el resultado correcto.

Registrar commit oficial y hash de fuentes vendorizadas. Mantener las clases oficiales intactas cuando sea posible y concentrar adaptaciones CPU y vocabulario en archivos locales. Si se cambia una clase, conservar parche e identificar el cambio. El codec se aprende en la primera etapa y permanece congelado durante la segunda. Una red sin Transformer o sin residuo multiescala debe nombrarse como control o aproximación.

## Fase 0: piloto aprobado de aritmética

Tarea: suma, resta y multiplicación de enteros 0–30; respuestas breves. TRAIN 192, DEV 32, TEST 64. TEST tiene 32 prompts de plantilla vista y 32 de plantilla nueva. División por operación y pareja de operandos; suma y multiplicación excluyen espejos conmutativos. Resta usa pares dirigidos. El cambio de plantilla se mide como tal, sin llamarlo generalización a cualquier matemática.

Configuración aprobada: bytes más PAD, salida de 8 posiciones, latente 64, RVQ `[1,2,4,8]` con 64 códigos por nivel; generador compartido de cuatro bloques, ancho 128 y cuatro cabezas; prefijo 64 bytes; batch 32; dos hilos CPU; límites tokenizer 1500 y generador 3000 actualizaciones por condición. Semilla 170020. El maestro responde con `think` cerrado y máximo 8 tokens Qwen. Registrar salidas crudas, parseo entero completo, errores y descartes; no sustituir errores Qwen con la referencia correcta.

Condiciones mínimas:

| Condición | Propósito |
|---|---|
| NCM destilado | Objetivo = salida Qwen admitida. |
| NCM supervisado | Misma arquitectura, tokenizer congelado, IDs TRAIN admitidos, semilla y presupuesto; objetivo = referencia exacta. |
| Generador sin entrenar | Comprueba la ganancia frente a inicialización; no sustituye el control entrenado. |
| Vecino TRAIN | Detecta si memorizar/responder por proximidad explica el resultado. El índice solo contiene TRAIN. |
| Qwen original | Mide maestro, calidad disponible para destilar y coste real. |

El tokenizer común del piloto se aprende con respuestas Qwen de TRAIN admitidas. Esto favorece potencialmente ese dominio de respuestas; informarlo. Los dos generadores comparten exactamente ese codec. Si el maestro comete errores, la comparación separa imitación del maestro y acierto de tarea.

## Fase 1: texto real, diseño posterior

Usar un corpus pequeño de textos reales con licencia verificable y permiso de uso, documentando origen, revisión, licencia y hash. Seleccionar una tarea concreta de salida corta, por ejemplo resumir un párrafo o responder una pregunta sobre un documento; conservar referencia humana cuando exista. Evitar que las respuestas de Qwen sean la única definición de calidad.

Dividir por documento, conversación o fuente original antes de extraer ventanas o generar paráfrasis. Deduplicar textos cercanos entre divisiones. Mantener una segunda prueba de fuente o formato distinto, identificada antes del ajuste. La división debe evitar que distintas ventanas del mismo artículo actúen como ejemplos independientes entre TRAIN y TEST.

Elegir longitud mediante distribución de longitudes TRAIN, coste y tasa de truncamiento; congelarla antes de TEST. Entrenar codec y ambos generadores con el mismo vocabulario y IDs cuando se comparen objetivos. Para esta fase puede convenir un tokenizer común aprendido solo de referencias TRAIN o de una mezcla TRAIN declarada, para no dar una ventaja de representación encubierta a una condición.

Antes de iniciar la fase 1, fijar tamaño, presupuesto, métrica primaria de tarea, nivel útil de calidad y comparación de coste. Esta sección no exige que el piloto aritmético resuelva esa fase ni añade tareas a la corrida actual.

## División, congelación y reglas de parada

1. Guardar particiones e IDs con hash antes de capturar al maestro o entrenar. Verificar intersecciones y espejos. No regenerar TEST por ser difícil ni por fallar el maestro.
2. Guardar respuestas Qwen TRAIN/DEV y manifiesto de errores. Los objetivos admitidos son enteros completos que caben en 8 bytes. Filtrar objetivos inválidos solo para pérdidas que los necesitan; la exactitud de generación libre DEV conserva las 32 preguntas.
3. Entrenar y seleccionar con DEV. Guardar historial completo, regla de selección, configuración, semillas y checkpoints. No elegir checkpoint por TEST.
4. Congelar checkpoints, código de evaluación y particiones antes de obtener respuestas del maestro TEST o medir resultados finales del estudiante. La referencia exacta aritmética puede existir en el archivo, pero no debe entrar en entrenamiento ni selección.
5. Congelar predicciones TEST antes de agregarlas en el informe. Conservar todos los casos, incluidas salidas vacías, inválidas y errores.

Parar por pérdida no finita, error de integridad, falta de memoria o presupuesto predeclarado agotado. Registrar la causa y entregar lo producido. El tokenizer puede terminar temprano según la regla aprobada de DEV (reconstrucción exacta 100% después de al menos 400 pasos); no trasladar esa regla al TEST. Una falla técnica reparable permite corregir código y registrar una nueva revisión. Si se cambia arquitectura o entrenamiento después de ver TEST, denominar nueva iteración exploratoria y usar después un conjunto nuevo para validación confirmatoria.

## Evaluación de representación y generación

Separar cuatro fenómenos:

- **Reconstrucción:** el encoder recibe una respuesta heldout, la cuantiza y el decoder intenta reconstruirla. Medir EM de secuencia y exactitud de posiciones sin PAD. Es diagnóstico del codec, no capacidad de contestar.
- **Predicción condicionada con historial verdadero:** CE y acierto de códigos por nivel con niveles previos verdaderos. Es diagnóstico del generador y no equivale a generación libre.
- **Generación libre:** solo el prompt inicial y códigos propios sucesivos. Medir exactitud aritmética frente a referencia independiente y coincidencia con Qwen por separado. El primer nivel también nace del prompt o distribución TRAIN declarada; nunca de códigos de respuesta TEST.
- **Fidelidad semántica:** en texto real, conservación de hechos y pertinencia frente al documento/referencia humana. Una reconstrucción exacta de TRAIN o una CE baja no prueba esta capacidad. Utilizar métrica de tarea y revisión de ejemplos; declarar si un evaluador automático depende del propio maestro.

Diagnósticos económicos sobre la evaluación ya ejecutada: uso y entropía de cada codebook, frecuencia de códigos dominantes, reconstrucciones por nivel, longitud efectiva, PAD inicial, repetición, salida vacía, bytes UTF-8 inválidos y respuestas no enteras. Reportar exactitud total y por operación/plantilla; no esconder fallos dentro del promedio. La CE del codec puede incluir PAD según la implementación aprobada, pero la métrica principal excluye el premio artificial por acertar relleno.

## Coste y registro reproducible

Usar mediciones locales de tiempo, CPU, memoria y disco. No presentar una estimación de FLOPs sin conteo fundamentado como coste medido. Menos evaluaciones secuenciales del generador no garantiza menor tiempo total: incluir prefijo, búsquedas de códigos, decoder y conversión final.

Las investigaciones y preparación pueden avanzar en paralelo. Para medir latencia, serializar los trabajos intensivos y registrar si hubo contención; no comparar un modelo aislado con otro que comparte CPU con un entrenamiento. Separar carga/calentamiento de inferencia estable. Usar las mismas entradas y repeticiones para cada condición e informar mediana/p95 y tiempo total cuando el número de casos lo permita.

Guardar un evento JSONL por fase o inferencia con campos explícitos, permitiendo `null` cuando no se midió algo:

```json
{"run_id":"fase0-170020","phase":"student_inference","condition":"kd","split":"test","example_id":"+:2:3","seed":170020,"config_sha256":"...","checkpoint_sha256":"...","source_sha256":"...","started_utc":"...","wall_seconds":0.0,"cpu_user_seconds":0.0,"cpu_system_seconds":0.0,"peak_rss_kib":0,"rss_scope":"process","swap_kib":null,"swap_scope":"not_measured","input_bytes":0,"output_bytes":0,"qwen_input_tokens":null,"qwen_output_tokens":null,"level_lengths":[1,2,4,8],"generator_forward_calls":4,"decoder_forward_calls":1,"train_updates":0,"batch_size":1,"threads":2,"artifact_bytes":0,"success":true,"error":null}
```

Las cifras del ejemplo son esquema, no resultados. Para procesos hijos, CPU y RSS deben incluir al hijo real; aclarar si un máximo es de toda la ejecución o muestreo por método. `ru_maxrss` es un máximo acumulado del proceso, no una medición exclusiva de cada pregunta. La suma de picos tampoco es el pico simultáneo. Registrar swap del proceso cuando esté disponible; no confundir swap global del sistema con consumo atribuible al modelo.

Añadir manifiesto de artefactos con tamaño en bytes y hash: modelo Qwen, tokenizer, cada generador, corpus del maestro, logs y checkpoints seleccionados. Separar espacio de ejecución final de cachés, datasets y checkpoints de entrenamiento. Contar pasos reales ejecutados y tokens/bytes reales, no solo límites configurados. Registrar semillas de inicialización, minibatches, generación y particiones. El piloto tiene una semilla; no fingir variabilidad entre semillas a partir de muchas preguntas.

## Resultado esperado del proyecto

Entregar una inferencia del estudiante cargable sin Qwen, pesos, procedencia, configuración y tabla calidad–coste por condición. Si el estudiante falla, conservar la arquitectura y los datos para estudiar si el problema está en codec, condicionamiento, generación o calidad del maestro. No reemplazar fallos por respuestas calculadas a mano.

El informe distingue: ejecución correcta, fidelidad arquitectural, transferencia de conocimiento, utilidad de tarea y mejora de coste. Una de ellas no demuestra las otras.

## Extensión conjunta: Transformer conceptual y decoder

Tras entrenar el codec y el generador de referencia, conservar un snapshot cargable del sistema con decoder congelado. Agregar una fase acotada de 300–500 actualizaciones conjuntas según el presupuesto final que registre el ejecutor. Encoder y codebooks permanecen congelados para que los objetivos discretos no cambien durante esta comparación. También se congelan los operadores de reconstrucción del codec, salvo cambio explícito de protocolo; sus operaciones sí deben dejar pasar gradiente hacia las entradas.

La finalidad es que el decoder aprenda a transformar las representaciones que **realmente produce el generador**, y que la pérdida de texto enseñe al generador cuáles errores de código afectan el resultado final. Una actualización exclusiva del decoder, o CE de texto sobre códigos verdaderos, no demuestra ese entrenamiento conjunto.

### Ruta diferenciable propuesta

Para cada nivel, convertir logits del generador a probabilidades `p = softmax(logits / tau)`. Con codebook fijo `E`, formar `e_soft = p @ E`; elegir códigos duros con argmax y sus embeddings `e_hard`; usar `e_ST = e_soft + (e_hard - e_soft).detach()`. El forward ve códigos duros como la inferencia; el backward usa la aproximación suave. Tau, su calendario, ponderaciones y normalización se guardan antes de TEST.

Acumular los embeddings de códigos propios mediante los mismos operadores de subida y reconstrucción del codec. Alimentar la reconstrucción al decoder **con gradiente habilitado**. Optimizar CE de texto frente al objetivo de tarea o supervisión declarada, más CE auxiliar de códigos por nivel. La respuesta verdadera se permite como etiqueta de las pérdidas; nunca como entrada al rollout que se presenta como generación autónoma.

En el código oficial, `vq.decode`, `idx_to_z_q`, `idx_to_ncm_input` y `get_next_autoregressive_input` tienen rutas decoradas con `no_grad`. No reutilizarlas para la ruta diferenciable esperando que optimicen el generador. La extensión debe componer explícitamente las operaciones de lookup suave, subida, suma y decoder, o proveer un método diferenciable separado; conservar intacta la inferencia oficial dura como comparación. No quitar indiscriminadamente `no_grad` de todos los métodos oficiales.

Preferir rollout diferenciable de los cuatro niveles desde el prompt, alimentando en cada paso sus predicciones ST anteriores. Si por coste se utiliza condicionamiento verdadero de niveles previos, declararlo y separar esa pérdida de la generación libre: un forward con códigos verdaderos no tiene la misma distribución de entradas que la inferencia. La sustitución suave sin ST también requiere declarar la diferencia entre entrenamiento continuo e inferencia discreta.

### Verificación económica de gradientes y alineación

El ejecutor puede aprovechar un minibatch del entrenamiento, sin una corrida extra: registrar que la pérdida de texto produce gradientes finitos y no nulos en parámetros del generador y del decoder; comprobar codebooks y encoder sin cambios por hash o comparación exacta; confirmar modificación de ambos grupos entrenables tras un paso. Si el gradiente al generador solo proviene de CE de códigos, el entrenamiento no está acoplando conceptos y texto como se pidió.

Comparar un forward ST duro sin dropout con la inferencia dura sobre los mismos códigos/prompt dentro de tolerancia numérica. Revisar formas por nivel y ausencia de datos de la respuesta en las entradas del rollout. Las diferencias intencionales, por ejemplo temperatura de muestreo o prompts, se registran. No exigir equivalencia de los gradientes del estimador ST con la derivada exacta del argmax, que no existe en esa forma.

### Controles e interpretación

- Conservar el modelo anterior de dos etapas con decoder congelado.
- Si el presupuesto permite atribuir el efecto del coentrenamiento, extender también el control con el mismo número adicional de actualizaciones y decoder congelado. Ajustar solo generador y conservar el resto del presupuesto emparejado. Registrar que igualar actualizaciones no iguala necesariamente CPU: reportar ambos.
- Si solo se corre la extensión conjunta, comparar con el snapshot como exploración; no atribuir toda diferencia al acoplamiento, porque también hubo más entrenamiento.
- Medir nuevamente reconstrucción heldout con el decoder actualizado. Los codebooks fijos evitan deriva de las etiquetas pero no evitan que el decoder olvide su interpretación anterior. Un deterioro del codec y una mejora de generación son un intercambio que debe verse en la tabla.
- Si se añade una pérdida de reconstrucción con códigos verdaderos para preservar el decoder, declararla como regularización y mantener separada su métrica de la generación autónoma.

### Alta eficiencia en el hardware disponible

Con cuatro niveles cortos y decoder pequeño, la extensión es razonable como piloto CPU; su coste de entrenamiento puede superar el esquema original que calcula todos los niveles en un solo forward. No prometer aceleración de entrenamiento por usar pocos códigos. La medición debe separar generación de conceptos, reconstrucción/decoder y conversión a texto, además del total por respuesta.

Conservar dos hilos, prefijos con máscara y secuencias pequeñas. Evitar introducir un maestro residente en cada minibatch: capturar ejemplos una vez y cerrarlo. No introducir búsqueda externa ni múltiples candidatos para mejorar calidad sin contabilizar sus llamadas. Priorizar entrenamiento estable y salidas correctas por CPU-segundo, no el mayor número de actualizaciones dentro del límite.

La comparación final incluye calidad, latencia, CPU-segundos, memoria máxima y coste adicional de la fase conjunta. Si el modelo se hace más rápido por emitir una salida vacía o más corta, ese cambio se reconoce con longitud y exactitud. No concluir que ocho bytes de aritmética representan la eficiencia para párrafos de texto.

## Eficiencia del proceso: cachés y parada sin fuga

Estas medidas sustituyen trabajo repetido, no añaden experimentos:

- **Caché del maestro:** clave por hash del modelo, binario/runtime relevante, prompt completo ya renderizado y configuración de generación (máximo, temperatura, semilla y opciones). Conservar respuesta cruda y telemetría originales. El objetivo exacto no participa en construir la salida cacheada; la fila de un nuevo split referencia ese objeto y su procedencia. Reutilizar una salida idéntica evita otra inferencia, pero no permite compartir respuestas de un problema entre TRAIN y TEST saltándose la división por problema.
- **Códigos RVQ:** tras congelar el tokenizer, codificar TRAIN/DEV una vez y guardar hash del tokenizer, partición y orden de filas junto al tensor. Invalidar ante cualquier cambio de encoder, codebook, operador de cuantización, vocabulario o normalización. TEST se mantiene fuera de los datos de selección; sus códigos verdaderos solo sirven de diagnóstico final, nunca de entrada a generación libre.
- **Entradas congeladas:** embeddings del prefijo pueden cachearse si el encoder es fijo. Proyección del generador, posición, query aprendida del primer nivel y las predicciones del rollout conjunto deben calcularse con gradiente en cada paso. No cachear o reutilizar una versión `detach` de la query ni embeddings predichos del generador. Un caché de reconstrucciones previas verdaderas es válido para teacher forcing, pero no sustituye el rollout autónomo de la pérdida conjunta.
- **Vectorización:** lotes, operaciones matriciales y pérdidas por nivel, con dos hilos CPU. Evitar inferencia Qwen o codificación RVQ repetida por minibatch. Mantener el buffer de datos pequeño y evitar procesos concurrentes intensivos durante las mediciones.
- **Scout de 50 pasos:** medir CPU, wall y memoria sobre TRAIN y, si corresponde, DEV. Sus pasos cuentan en el presupuesto y su decisión depende de recursos/estabilidad, nunca TEST. Registrar si se continúa el mismo estado del optimizador o se reinicia. No describir como coste cero una prueba descartada.
- **Parada DEV predefinida:** registrar mínimo de pasos, frecuencia de evaluación, paciencia y criterio antes del entrenamiento completo. Puede detener trabajo sin mejora o reconstrucción ya resuelta. No aumentar el límite por ver un TEST malo ni usar TEST para decidir una parada. Si se aborta por NaN, memoria o tiempo, conservar ese gasto en el informe.

La reutilización cacheada debe reproducir exactamente los datos y etiquetas de una ejecución sin caché. Solo se ahorra cómputo redundante. El registro de tiempo separa trabajo nuevo, trabajo cacheado y coste histórico del maestro, sin volver a cobrarlo como CPU actual ni ocultarlo del coste de construir el modelo.

## Revisión previa al FIT y primer estado observado

Comprobación independiente por lectura de archivos, sin ejecutar otro motor ni entrenamiento:

- Los ocho hashes de fuentes de `PREFIT-FREEZE.json` y el hash del protocolo coinciden con los archivos activos. En esa comprobación todavía no existía `data/teacher-test.jsonl`.
- Se corrigieron el nombre de scout de la fase conjunta y su referencia temporal; el scout usa `start` y presupuesto 500, sin sobrescribir el scout del tokenizer. La evaluación conjunta cada 100 pasos queda dentro del bucle.
- La reanudación de `teacher.py` ya verifica que el `request_key` guardado coincide con la configuración y prompt actuales antes de reutilizar una fila por ID.
- `joint.py` reconstruye explícitamente cuatro niveles desde códigos propios. `_up_to_full` y `_apply_quant_resi` oficiales no tienen decorador `no_grad`; la operación permite gradiente hacia las entradas con sus pesos congelados. Las etiquetas se usan solo en CE auxiliar y de texto.
- `PREFIT-GRADIENTES.json` registra igualdad de códigos duros con inferencia oficial y gradientes de **pérdida de texto sola**: generador 1,071986; decoder 7,631765; query inicial 0,011603; encoder y codebooks 0. Es una comprobación del ejecutor preservada en artefacto y revisada aquí, no una segunda corrida independiente.
- Primer resultado del codec: 400 pasos, 7,735 segundos wall y 13,170 CPU-segundos; reconstrucción DEV reportada 100% y posiciones sin PAD 100% sobre 31 objetivos del maestro admitidos. Una pregunta DEV del maestro fue rechazada; las 32 permanecen para exactitud de generación libre. Este resultado del codec no demuestra capacidad de contestar.
- Scout del generador KD: 50 pasos incluidos, 9,516 segundos wall, 19,029 CPU-segundos y máximo de proceso 523460 KiB. Su proyección a 3000 pasos es una extrapolación de presupuesto, no coste final medido.

El código de evaluación conserva la reconstrucción como diagnóstico separado y generación libre con `generate(None,prefix)`. El control de vecino usa operación y operandos estructurados de la tarea; es una referencia privilegiada respecto a la entrada puramente textual y debe describirse así. La lectura final de predicciones, coste y checkpoints sigue pendiente.

## Enmienda operativa revisada antes de TEST

Tras el piloto KD, se interrumpió el proceso original para evitar completar una condición supervisada opcional y priorizar la fase conjunta. `fit-RUN.json` conserva el retorno −15, 336,996 segundos wall y 669,465 CPU-segundos del proceso completo hasta esa parada. Es una interrupción operativa documentada, no una finalización normal con código cero.

`SUPERVISED-PARCIAL.json` conserva el checkpoint de evaluación a 200 pasos y un intervalo de actualizaciones efectivas entre 200 y 399; no se conoce el número exacto porque la interrupción ocurrió entre registros. Su tiempo desde el límite KD es 63,893 segundos, incluyendo preparación. Este control sirve como exploración de presupuesto desigual y su coste no se omite. No permite estimar limpiamente el efecto causal de cambiar los objetivos Qwen por referencias exactas.

`continuar_joint.py` retoma únicamente la extensión conjunta y su control desde el checkpoint KD seleccionado. Por inspección, ambos modos recargan el mismo tokenizer y generador de partida y reinician la misma semilla antes de construir el modelo; con dropout cero y generación argmax las selecciones de minibatch quedan emparejadas. Son 500 pasos cada uno, pero el coste CPU difiere al habilitar gradiente del decoder en uno. El freeze final previsto incluye fuentes, runner, particiones y todos los checkpoints existentes antes de obtener respuestas Qwen TEST.

Esta modificación se decidió después de observar TRAIN/DEV y antes de TEST. Debe preservarse la congelación inicial y la enmienda con sus tiempos; no presentarla como si todo el proceso hubiera seguido sin cambios un protocolo definido antes del primer FIT.

## Auditoría de correcciones antes del FIT

En los archivos de procedencia de ronda 17, inspeccionados tras la corrección:

- `teacher.py`: `kd_usable = parsed and len(canonical.encode('utf8')) <= 8 and bool(canonical)`; enteros estrictos y longitud controlada.
- `train.py`: `dv_usable` se usa para reconstrucción y pérdidas KD; los prompts y exactitud aritmética libre conservan `dv` completo.
- `train.py`: ambas condiciones usan `data=usable`; mismos IDs admitidos, presupuestos y semilla. La referencia exacta no recupera los descartados solo para una condición.

Estas correcciones resuelven los riesgos concretos de la revisión estática inicial. La fidelidad de los archivos migrados y los resultados se revisará al cierre; esta propuesta no certifica un entrenamiento todavía pendiente.
