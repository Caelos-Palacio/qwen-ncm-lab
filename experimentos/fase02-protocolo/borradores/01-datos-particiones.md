## 1. Datos, particiones y docente

Borrador de sección. Ámbito: aritmética entera con +, - y *; no se afirma nada fuera de ella. Todo lo de esta sección se fija y se hashea antes de la primera consulta al docente de 0.2.

### 1.1 Por qué hay que ampliar el rango

El rango 0..30 solo ofrece 496 pares canónicos de suma, 496 de producto y 961 de resta: 1953 en total. La fase 0 ya usó 288. Una escalera hasta 3072 TRAIN sin repetir pares es imposible con ese rango, y repetir un par con otra plantilla no aporta cobertura numérica nueva. Por eso 0.2 usa operandos 0..60 (`N=60`), con los siguientes pares canónicos (conmutativos de + y * deduplicados, `a<=b`):

| op | pares 0..60 | uso máximo previsto |
|---|---:|---:|
| + | 1891 | 1024 + 86 + 171 = 1281 (68%) |
| * | 1891 | 1281 (68%) |
| - | 3721 | 1281 (34%) |

Es un cambio de la tarea y se declara como tal: los resultados de 0.2 no son comparables con los 0..30 de fase 0, salvo mediante el ancla del punto 1.6. Los productos llegan a 3600 (4 dígitos) y las restas a -60; todo cabe en 8 bytes y en el prompt de 64 bytes (se comprueba con `assert`).

### 1.2 Tamaños y escalera

Unidad de partición: `(op, a, b)` canónico, igual que en fase 0. Se sortea con SHA256 `NCM170020|02|<id>` (clave nueva, no reutiliza el orden de fase 0). Sin solapamiento de par entre TRAIN, DEV y TEST, ni con el DEV/TEST de fase 0 (TEST de fase 0 ya se abrió; sus 96 pares de DEV+TEST se excluyen de todo 0.2 para que no sirva como señal indirecta). Los 192 pares TRAIN de fase 0 sí pueden reaparecer.

TRAIN es una escalera anidada: cada peldaño contiene al anterior (prefijo del orden hash dentro de cada operación, 1/3 por operación). Así el docente se consulta una vez por par y la curva de escala no mezcla muestras distintas.

| Partición | n | Por operación | Plantillas |
|---|---:|---|---|
| TRAIN-192 / 768 / (1536) / 3072 | 192, 768, 1536, 3072 | 64/256/512/1024 cada una | 4 vistas (T1..T4) |
| TRAIN-PROBE (submuestra fija de TRAIN-192) | 192 | 64 cada una | las de TRAIN |
| DEV | 256 | 86+85+85 | 128 vistas, 128 plantilla DEV-nueva (U0) |
| TEST | 512 | 171+171+170 | 256 vistas, 256 nuevas (U1, U2) |

TRAIN-PROBE son los 192 pares de TRAIN-192 (están en todos los peldaños); mide memorización en cada checkpoint con la misma métrica que DEV y TEST, de modo que la brecha TRAIN-PROBE vs DEV es la medida de generalización. El peldaño 1536 es opcional (decisión de presupuesto en la sección de entrenamiento), pero sus pares se extraen igualmente porque el coste de docente es incremental.

### 1.3 Plantillas seen / unseen

- Vistas (en TRAIN, y en las mitades "vistas" de DEV y TEST): T1 `Compute {a} {op} {b}. Integer only.` (la de fase 0), T2 `What is {a} {op} {b}? Integer only.`, T3 `{a} {op} {b} = ? Integer only.`, T4 `Calculate {a} {op} {b}. Integer only.` Cada par recibe una plantilla por hash (`NCM170020|02|tpl|<id>`), repartidas ~25% cada una por operación. Una sola plantilla por par: no se multiplican consultas.
- Nuevas: U0 (solo DEV) `Evaluate the expression {a}{op}{b}. Integer only.` (la nueva de fase 0, ahora usada en DEV como diagnóstico, nunca como criterio de selección); U1 y U2 (solo TEST) `Result of {a} {op} {b}? Integer only.` y `Please work out {a} {op} {b}. Integer only.`, cada una en 128 pares. U1/U2 no aparecen en TRAIN ni DEV. El texto de U1/U2 no se discute fuera del archivo congelado hasta abrir TEST.
- Mide transferencia de formulación, no de rango numérico. El hecho de que TRAIN pase de 1 a 4 plantillas confunde a propósito "más datos" con "más variedad de formulación": la ablación mínima es una escalera 3072 con solo T1 (misma lista de pares, plantilla única), que se reserva como contraste y no se amplía el docente (solo cambia el prompt: 3072 consultas nuevas, ver 1.7).

### 1.4 Potencia estadística (Wilson 95%, calculada)

Semianchura aproximada en puntos porcentuales para la proporción observada `p`:

| n | p=0 (0/n) | p=1/n | p=50% | p=90% |
|---:|---|---|---|---|
| 32 (DEV fase 0) | [0, 10.7] | [0.6, 15.7] | [33.6, 66.4] | [71.9, 95.0] |
| 64 (TEST fase 0) | [0, 5.7] | [0.3, 8.3] | [38.1, 61.9] | [79.1, 94.6] |
| 128 | [0, 2.9] | [0.1, 4.3] | [41.5, 58.5] | [83.4, 94.0] |
| 256 (DEV; estrato TEST) | [0, 1.5] | [0.1, 2.2] | [43.9, 56.1] | [85.5, 93.0] |
| 512 (TEST) | [0, 0.7] | [0.0, 1.1] | [45.7, 54.3] | [86.9, 92.2] |

Consecuencias: con TEST=512, un 1.6% observado (como el 1/64 de fase 0) ya se distingue de un 10% real, y la diferencia entre estudiante y Qwen (~90%) es nítida. Para comparar dos modelos sobre el mismo TEST se usa McNemar exacto sobre pares discordantes (misma lista). Con DEV=256 la selección de checkpoint resuelve diferencias de ~6 puntos solo con dos o más peldaños de empate; cualquier empate se desempata por CE como en fase 0. Los dos estratos de 256 (vistas/nuevas) permiten un contraste de ~±6 puntos en transferencia de plantilla.

### 1.5 Regla de congelado antes del docente

1. Un script nuevo `preparar_datos_02.py` (fuera de `preparar_datos.py`, que no se toca) escribe `data02/{train,dev,test}.json`, la lista de peldaños y `PROTOCOLO-02.json`, y falla si `ENTRADA-FREEZE-02.json` ya existe.
2. Antes de cualquier consulta al docente se calcula SHA256 de los archivos de datos, del script, de las plantillas y de `PROTOCOLO-02.json`, y se guarda en `ENTRADA-FREEZE-02.json`. Ese archivo y sus hashes se commitean.
3. Se ejecutan y registran las verificaciones de 1.8 sobre los archivos congelados; si alguna falla, se descarta el directorio entero y se regenera con un `NCM170020|02b` documentado (el fallo y el motivo se conservan, no se edita a mano).
4. Orden fijo de operaciones: congelar datos, docente TRAIN/DEV, entrenar, congelar checkpoints (`CHECKPOINTS-FREEZE-02.json`), solo entonces docente TEST. Los IDs y las respuestas exactas de TEST existen en disco desde el congelado inicial, pero la salida del docente sobre TEST no existe hasta el último paso.

### 1.6 Caché del docente y ancla con fase 0

- Clave: SHA256 de `{config del docente, prompt completo}` (igual que `teacher.py`). Se reutiliza la configuración congelada de `TEACHER-CACHE-CONFIG.json` (modelo `37ae48...`, binario `8964c9...`, temp 0, `max_new=8`, pensamiento cerrado); un cambio de cualquiera de los dos hashes invalida la caché y obliga a documentarlo como protocolo nuevo.
- Los 224 registros existentes de fase 0 se mantienen intactos; solo hay acierto de caché cuando el prompt completo coincide (T1 con pares de 0..30 que reaparezcan). Las entradas nuevas se añaden en un archivo de caché de 0.2 separado; nunca se reescriben líneas crudas.
- Ancla barata: re-evaluar los 3 modelos de fase 0 y los nuevos sobre el TEST legacy de 64 (ya abierto; solo informativo, no selecciona). El docente de esos 64 está en caché: coste 0.
- Extracción en lotes de 256 consultas reanudables (~3 min cada uno), un trabajo pesado a la vez, con RSS/swap/CPU en `RUNS.jsonl`. Una interrupción conserva lo hecho; no se vuelve a pedir lo cacheado.

### 1.7 Política de errores del docente

Se conserva todo: salida cruda, errores del docente, tiempos, `kd_usable`. Un entero incorrecto bien formado entra en KD como objetivo. Las salidas no enteras estrictas, vacías o de más de 8 bytes se rechazan con ID preservado; los controles supervisados usan los mismos IDs admitidos que KD. No se reemplaza ninguna respuesta errónea por la exacta, no se repite una consulta con otra semilla, no se filtra por acierto. Se informa por separado: exactitud del docente por operación y plantilla, tasa de admisión, y acuerdo del estudiante con el docente frente a exactitud numérica. Una caída de precisión de Qwen en productos de dos cifras (0..60) es un hallazgo, no un fallo: marca el techo de KD en la tarea.

### 1.8 Evitar influencia de TEST

- TEST no entra en ninguna fase de ajuste: ni codec, ni selección de checkpoint o paciencia, ni elección de peldaño, ni hiperparámetros, ni redacción de plantillas posteriores. DEV (256) es el único criterio.
- Los archivos TEST se leen solo desde `evaluar.py` y solo tras `CHECKPOINTS-FREEZE-02.json`; el código de entrenamiento no importa ni abre `data02/test.json` (comprobación por grep en el congelado).
- Se evalúa TEST una sola vez por checkpoint congelado. Un fallo se conserva como resultado; no se reentrena ni se reabre TEST.
- Verificaciones de datos congelados (todas deben pasar): sin pares compartidos entre particiones ni con DEV/TEST legacy; commutatividad deduplicada; peldaños anidados; U1/U2 ausentes de TRAIN/DEV; prompts <=64 bytes; reparto por operación; respuestas exactas recomputadas por separado.

### 1.9 Tamaños, coste de docente y criterios de aceptación

Coste por consulta: 0.675 s de pared (224 consultas en 151.3 s, carga incluida) y 0.688 s (64 en 44.0 s); se usa 0.69 s con 2.96 CPU-s por consulta (662.3 CPU-s / 224). Qwen usa 4 hilos de generación y ocupa unos 925 MiB RSS; es un trabajo único. Estimación de pared sin caché; la caché solo la reduce, y no es una medición hasta ejecutarse.

| Bloque | Consultas nuevas | Pared estimada | CPU estimada | Criterio de aceptación |
|---|---:|---:|---:|---|
| TRAIN-192 | 192 | 132 s | 568 s | los 4 chequeos de 1.8; admisión KD >= 90% |
| TRAIN-768 (incremental +576) | 576 | 397 s | 1.7 ks | idem; mismo reparto por operación (+-1) |
| TRAIN-1536 (+768, opcional) | 768 | 530 s | 2.3 ks | idem |
| TRAIN-3072 (+1536) | 1536 | 1060 s | 4.5 ks | idem |
| DEV | 256 | 177 s | 758 s | admisión >= 90%; sin pares de TRAIN |
| TRAIN+DEV total | 3328 | 2296 s (38 min) | 9.9 ks | docente sin fallos de ejecución; hashes registrados |
| TEST (tras congelar) | 512 | 353 s | 1.5 ks | admisión >= 90% o se informa; no se usa para decidir |
| Total | 3840 | 2650 s (44 min) | 11.4 ks | |
| Contraste T1-solo 3072 (opcional) | 3072 | 2120 s | 9.1 ks | solo si se pide la ablación de plantilla |

Aceptación global: (1) `ENTRADA-FREEZE-02.json` existe y precede en el tiempo al primer registro del docente; (2) las verificaciones de 1.8 pasan sobre los hashes congelados; (3) ningún peldaño pierde pares ni quiebra el anidamiento; (4) hay 0 respuestas sustituidas; (5) cada ID rechazado está en el registro con su salida cruda; (6) swap y RSS de cada lote quedan en `RUNS.jsonl`; (7) si la admisión baja de 90% en algún peldaño, se informa y se sigue con el subconjunto admitido (mismo para los controles), sin editar objetivos.
