# Fase 0.2: protocolo unificado

**Estado: BORRADOR NO CONGELADO.** Integra los borradores `borradores/01-datos-particiones.md`, `02-diseno-experimental.md` y `03-instrumentacion-y-rigor.md` (que no se editan). Nada de lo que sigue está en vigor hasta el congelado de la sección 14, que ocurre una sola vez, después de P0 y de la revisión independiente del código (sección 10). Las decisiones D1..D13 están **resueltas** el 2026-10-28 (aceptada por el usuario en chat; registro en `DECISIONES-PENDIENTES.md`) con la opción recomendada de cada una, y se marcan con [D#]. Resolverlas no congela el protocolo. Esta versión incorpora las correcciones de `REVISION-PROTOCOLO-0.2.md` (B1-B4, I1-I10, menores); lo que sigue sin fijar está en la sección 15.

Convención: **(medido)** = cifra de fase 0/0.1 con archivo de origen; **(estimado)** = cálculo a partir de medidas, no una medición hasta ejecutarse; **(calculado)** = aritmética o estadística exacta sin ejecución.

## 1. Objetivo y ámbito

Objetivo: comprobar, con un diseño que la fase 0/0.1 no tuvo (varias semillas, presupuesto igual, DEV y TEST con potencia, protocolo congelado una sola vez), si un mini-NCM de ~1,0 M parámetros entrenado por destilación de secuencias desde Qwen genera respuestas aritméticas de pares que no están en TRAIN, y si el coentrenamiento del decoder (J) o la destilación (K) aportan algo frente a controles.

Ámbito: aritmética entera con `+`, `-`, `*`, operandos **0..60** [D2], respuestas de hasta 8 bytes, CPU de 2 hilos para los estudiantes. Es destilación por secuencias, no conversión de pesos. Nada se extrapola a lenguaje general ni a otros rangos. El cambio 0..30 a 0..60 es un cambio de tarea (sección 3.1).

Punto de partida (medido, `revision/AUDITORIA-FINAL.md`): TEST de fase 0, 64 ítems, una semilla: Qwen 58/64, NCM KD 1/64, joint 0/64, continuado 0/64, sin entrenar 0/64, vecino TRAIN 1/64. Defectos que 0.2 corrige: una semilla; rama supervisada interrumpida (presupuesto desigual); protocolo enmendado durante el proceso; DEV de 32 ítems (resolución ~3 pp); TEST de fase 0 ya abierto.

## 2. Hipótesis y predicciones

Estimador: exactitud entera de generación libre en TEST-0.2 (el rollout recibe solo el prompt). Margen en puntos porcentuales (pp). Todas las hipótesis de inferencia se evalúan en el **peldaño decisivo (TRAIN-3072, 5 semillas)** [D1][D4]. Control fuerte `CF = max(p_U, p_N)` calculado en ese peldaño (p_U media de semillas; N determinista, definido en 4.1). CF se usa igual en la hipótesis, en 8.1 y en 8.2; dentro de cada remuestreo bootstrap se recalculan p_U, p_N y CF = max (7.1), y en un estrato se calcula con U y N de ese estrato.

- **H-A (aprendizaje)**, para X en {K, J, C, S}. H0: `p_X <= CF + 5`. H1: `p_X >= CF + 10`.
- **H-B** (el coentrenamiento ayuda): H0 `p_J - p_C <= 0`. H1 `>= +5` en el conjunto de TEST; en el estrato de plantilla nueva (256 ítems, diferencia mínima detectable 6,8-10,4 pp, 7.2) solo se exige signo positivo del estimador y ausencia de contradicción (8.4), no un margen de +5 que ese estrato no puede detectar.
- **H-C** (KD frente a supervisión exacta, presupuesto igual): H0 `|p_K - p_S| <= 5`. H1 `> 5`, con el signo observado (sin predicción de dirección).
- **H-D** (la fase de 500 pasos con CE de texto, decoder fijo): contraste limpio `C - K`. H0 `p_C - p_K <= 0`. H1 `>= +5`. `J - K` mezcla dos factores (fase de texto y decoder entrenable): se informa como efecto conjunto, sin hipótesis propia, dentro de la misma familia (7.1).
- **Transferencia de formulación**, para X en {K, J, C, S}: medida sobre la media de las 5 semillas en U1 y U2 juntas (256 ítems; U1 y U2 también por separado, 128 cada una, solo descriptivo). Se demuestra si el límite inferior del IC bootstrap de dos niveles (7.1; unilateral 95 %, ajuste de Bonferroni sobre las 4 condiciones) de `p_X - CF_nuevas` es > 0, con `CF_nuevas = max(p_U, p_N)` calculado en ese estrato. Si ninguna lo cumple, no se demuestra transferencia aunque mejore en plantillas vistas. Se compara con el control, no con un 5 % absoluto.
- **Refutación declarada**: la única regla es 8.2 (`p_X < CF + 5` y límite superior del IC < +10, con el techo del codec comprobado). "Ninguna condición supera `CF + 5`" por sí solo no basta para aceptar H0-A.
- **Curva de escala (exploratoria)**: exactitud DEV y TEST en los peldaños 192, 768 y 3072 con una semilla (170020). Es descriptiva: sin contrastes ni IC de diferencias entre peldaños (una semilla no separa efecto de datos de ruido de inicialización).

Justificación de los umbrales +5 / +10: sección 7.4.

## 3. Datos y particiones

### 3.1 Dominio y su consecuencia

Con operandos 0..30 hay 496 pares canónicos de suma, 496 de producto y 961 de resta (1953). Con DEV 256 + TEST 512 + la escalera de TRAIN no caben sin repetir pares (por operación faltarían pares en `+` y `*`); con 0..60 hay 1891 + 1891 + 3721 = 7503 [D2]. Consecuencias que se asumen, no se ocultan:

1. **Los tiempos medidos en 0..30 no son medidas de 0..60.** Los costes por paso (codec 7,74 s por 400 pasos; 263,3 s por 1400 pasos de generador) se miden con secuencias de longitud fija de 64 bytes y el coste por paso probablemente no depende del contenido, pero eso es un supuesto no verificado. Se tratan como (estimado) y el primer run de 0.2 los re-mide (sección 11, puerta de coste).
2. **El codec (400 pasos) no está probado con respuestas de hasta 4 dígitos y signo (-60..3600).** Su reconstrucción en 0..60 es desconocida. Se mide en DEV, por (peldaño, semilla), con el criterio de fase 1 (>= 95 % de caracteres sin PAD) y, además, el **techo del codec**: exactitud entera al codificar y decodificar la respuesta exacta de cada ítem de DEV (reconstrucción, etiquetada aparte; no es generación desde el prompt). Es una medición, no toca el presupuesto. Como K, J, C y S comparten el codec, ninguno puede superar su techo: si el techo medio del peldaño decisivo es < `CF + 10`, un resultado negativo se clasifica "no concluyente por codec", no "no aprendizaje" (8.2, 8.3).
3. **Los controles y el control fuerte no están medidos en 0..60.** El `<= 1,6 %` de fase 0 es referencia, no línea base.
4. **Ancla con fase 0: solo informativa.** Se re-evalúan los modelos de fase 0 y los de 0.2 sobre el TEST legacy de 64 (pares 0..30, ya abierto, excluidos de todo 0.2; docente en caché, coste 0). No selecciona ni se usa para inferencia: los modelos de fase 0 se entrenaron en otro dominio. Su único uso es comprobar que la tubería reproduce los números de fase 0 (58/64 Qwen, 1/64 KD) y detectar regresiones.
5. Los operandos individuales de TEST sí aparecen en TRAIN (en otros pares): se mide interpolación entre pares y transferencia de formulación, no extrapolación de rango.

### 3.2 Unidad, sorteo y exclusiones

Unidad `(op, a, b)` canónica (a<=b en `+` y `*`). Sorteo con SHA256 `NCM170020|02|<id>`; plantilla por par con `NCM170020|02|tpl|<id>`. Sin solapamiento de par entre TRAIN, DEV, TEST y PILOTO. Se excluyen de todo 0.2 los 96 pares de DEV+TEST de fase 0. Los 192 pares TRAIN de fase 0 pueden reaparecer en DEV/TEST/TRAIN de 0.2; se registra cuántos reaparecen y en qué partición (diagnóstico, en `ENTRADA-FREEZE-02.json`).

### 3.3 Particiones

| Partición | n | Por operación | Plantillas |
|---|---:|---|---|
| PILOTO (docente, sección 3.6) | 168 | 56 cada una | 7 (T1..T4, U0..U2) en rotación, 24 por plantilla |
| TRAIN escalera 192 / 768 / 3072 (anidada) | 192, 768, 3072 | 64 / 256 / 1024 cada una | 4 vistas T1..T4 (~25 % cada una) |
| TRAIN-PROBE (= TRAIN-192) | 192 | 64 | las de TRAIN; mide memorización |
| DEV | 256 | 86 + 85 + 85 | 128 vistas + 128 U0 |
| TEST | 512 | 171 + 171 + 170 | 256 vistas + 256 nuevas (U1 128, U2 128) |

Uso máximo de pares por operación (calculado): `+` y `*` 1024 + 86 + 171 + 56 = 1337 de 1891 (70,7 %); `-` 1337 de 3721 (35,9 %).

El peldaño intermedio 1536 se extrae anidado (coste de docente nulo adicional) pero **no se entrena** [D3]. La escalera mantiene 4 plantillas en todos los peldaños, por lo que la curva de escala no confunde datos con variedad de formulación (la referencia de 1 plantilla es la de fase 0, no un peldaño de 0.2). El contraste "3072 solo con T1" queda fuera de 0.2 [D3].

Plantillas: T1 `Compute {a} {op} {b}. Integer only.`; T2 `What is {a} {op} {b}? Integer only.`; T3 `{a} {op} {b} = ? Integer only.`; T4 `Calculate {a} {op} {b}. Integer only.`; U0 (DEV) `Evaluate the expression {a}{op}{b}. Integer only.`; U1 `Result of {a} {op} {b}? Integer only.`; U2 `Please work out {a} {op} {b}. Integer only.`. U1/U2 no aparecen en TRAIN ni DEV y su texto no se discute fuera del archivo congelado hasta abrir TEST. Una plantilla por par: no se multiplican consultas. Los textos exactos quedaron confirmados tal cual por el usuario el 2026-10-28 [D11] y no se tocan tras el congelado.

### 3.4 Docente: configuración, caché y errores

Configuración congelada de `TEACHER-CACHE-CONFIG.json` (modelo, binario, temperatura 0, `max_new=8`, pensamiento cerrado). Un cambio de hash invalida la caché y obliga a un protocolo nuevo (R20). Caché nueva y separada para 0.2; los 224 registros de fase 0 no se tocan (solo hay acierto con prompt completo idéntico). Extracción en lotes reanudables de 256 consultas (~3 min cada uno, estimado), un proceso a la vez, con RSS/swap/CPU en `RUNS.jsonl`.

Política de errores: se conserva todo (salida cruda sin `strip`, errores, tiempos). Un entero bien formado pero incorrecto entra en KD como objetivo. Se rechazan (con ID y salida cruda preservados) las salidas no enteras estrictas, vacías o de más de 8 bytes. Los fallos de ejecución del motor (`teacher_failed`, R16) se distinguen de los rechazos de contenido; ambos cuentan como no admitidos en la tasa de admisión, que se informa desglosada. No se sustituye ninguna respuesta por la exacta, no se reintenta con otra semilla, no se filtra por acierto. Los controles supervisados usan los mismos IDs admitidos. Se informa por separado: exactitud del docente por operación y plantilla, admisión, y acuerdo del estudiante con el docente frente a exactitud numérica. Una caída de precisión de Qwen en productos de dos cifras es un hallazgo, no un fallo.

### 3.5 Referencia medida del docente en fase 0 (0..30)

Admisión 192/192 en TRAIN y 31/32 en DEV; acierto del docente 186/192 y 30/32 (`TEACHER-TRAINDEV-STATS.json`); en TEST 58/64 (`AUDITORIA-FINAL.md`). Coste: 0,675 s de pared por consulta (224 en 151,3 s con carga) y 0,688 s (64 en 44,0 s); 662,3 CPU-s por 224 consultas (2,96 CPU-s por consulta); RSS pico 925 MiB (947 076 KiB; la cifra "947 MiB" era un error de unidad, y la "otra medición" de 925 MiB de la auditoría es la misma). No hay medidas del docente en 0..60: de ahí el piloto.

### 3.6 Piloto del docente (calibra el umbral de admisión)

Problema: el 90 % de admisión de los borradores no tiene dato previo en 0..60 (en 0..30 fue 223/224 = 99,6 %, lo que lo hace laxo allí y no informa sobre productos de dos cifras).

Piloto P0, **fase propia previa al congelado principal** (`teacher-piloto`), con minicongelado propio: (1) lista de 168 pares (56 por operación) sorteados con la clave `NCM170020|02p` y apartados de todas las particiones; (2) las 7 plantillas, la configuración del docente y la regla de abajo (extraída como `REGLA-ADMISION.txt`), con sus hashes en `PILOTO-FREEZE.json`, creado antes de la primera consulta de P0; (3) 168 consultas (~116 s de pared, estimado) con registro crudo íntegro. Es un trabajo pesado de un solo proceso. El piloto no entrena, no selecciona ni usa pares de TRAIN/DEV/TEST. El resultado se escribe en un archivo propio, `UMBRAL-ADMISION.json` (umbral, admisión observada, L de Wilson, hash de `PILOTO-FREEZE.json`, hash propio registrado), que el congelado principal incluye por hash. `PROTOCOLO-0.2.md/.json` se hashean solo en el congelado principal, después de P0; el texto de 3.6 y 3.7 no puede cambiar tras `PILOTO-FREEZE.json` (su hash se verifica en el congelado principal). Así R04 y R06 (sección 9) no fallan por diseño.

Regla (fijada antes de ver el piloto): sea `a` la admisión observada y `L` su cota inferior de Wilson al 95 % (calculado: 160/168 da L = 90,9 %; 151/168 da L = 84,4 %).
- Si `L >= 90 %`: umbral por peldaño y partición = 90 %.
- Si `a >= 85 %` pero `L < 90 %`: umbral = `floor5(a - 5 pp)` (múltiplo de 5), nunca menor de 80 %.
- Si `a < 85 %` o alguna operación tiene admisión < 70 %: **NO-GO**; el usuario decide (reducir el rango, cambiar el prompt del docente, o aceptar) y el piloto se repite como protocolo nuevo. La regla y el piloto de 168 consultas están resueltos [D6]; la acción concreta ante NO-GO sigue sin decidir y se decide solo si ocurre.
La exactitud del docente por operación del piloto es solo descriptiva y se publica en el protocolo congelado como referencia; no fija umbral. El piloto no modifica la configuración del docente.

### 3.7 Consecuencias de incumplir el umbral de admisión

Se fija antes de ver datos. La admisión se calcula por peldaño de TRAIN (192, 768 y 3072, anidados: cada subconjunto cuenta) y por partición (DEV, TEST) frente a `UMBRAL-ADMISION.json`, desglosada como en 3.4.
- **TRAIN (cualquier peldaño) o DEV por debajo del umbral:** la cola se detiene tras el lote que lo revela y no se entrena ninguna ejecución afectada. Decide el usuario; no se sustituyen respuestas, no se filtra y no se reintenta. Continuar con otros datos, otro prompt del docente u otro umbral es un protocolo nuevo (0.2b, sección 14); los datos y el registro de esta tentativa se conservan.
- **TEST por debajo del umbral:** se informa y no se excluye ningún ítem. La métrica de TEST es exactitud numérica frente a la respuesta exacta (calculada aparte), no acuerdo con el docente. El docente de TEST solo aporta su propia exactitud y el acuerdo estudiante-docente, descriptivos; no entra en ningún contraste ni en CF. Una admisión baja en TEST se lee como limitación del docente en esa partición y se declara en el informe.

## 4. Condiciones y presupuesto igual

| Id | Condición | Entrenamiento del generador | Decoder |
|---|---|---|---|
| U | Sin entrenar | 0 actualizaciones (init de la semilla) | fijo |
| N | Vecino TRAIN | ninguna; control privilegiado (usa operación y operandos), determinista, calculado por peldaño | n/a |
| K | KD por etapas | 1400 + 500 con objetivo docente (CE de códigos por escala, corrupción 5 %) | fijo |
| J | KD + joint | 1400 como K; luego 500 con CE de texto + 0,25 CE auxiliar, straight-through | entrenable |
| C | KD + continuado | 1400 como K; luego 500 con la misma pérdida de texto que J | fijo |
| S | Supervisado | 1400 + 500 con respuesta exacta como objetivo, ININTERRUMPIDO | fijo |

- K, J y C comparten el prefijo de 1400 pasos (mismo estado, mismos minibatches); S tiene su propio prefijo con el mismo calendario. J y C: mismo inicio y minibatches (como en 0.1).
- Actualizaciones idénticas: 1900 = 1400 (lote 32, lr 5e-4) + 500 (lote 16, lr 1e-4). Ejemplos vistos iguales: 1400x32 + 500x16 = 52 800 por condición, también entre peldaños (con 192 son ~275 pasadas, con 3072 ~17; por eso el presupuesto es en actualizaciones, no en épocas). Mismo generador de índices por (semilla, paso). Sin parada temprana: o se ejecuta el presupuesto completo o la ejecución es inválida y se repite según la regla de repetición de abajo. Al pasar de la fase de 1400 a la de 500 pasos, lote, lr y estado del optimizador (Adam: reinicio o continuación) se tratan igual en K, J, C y S; el tratamiento se fija en `PROTOCOLO-0.2.json` (sección 15; recomendación: reiniciar) y R26 lo verifica.
- **Ejecución inválida y repetición:** la ejecución inválida (11.2) se conserva íntegra en su directorio, con su causa (`INVALIDA.json`) y su fila en `RUNS.jsonl`; se repite una sola vez, con la misma semilla y los mismos datos, en un directorio nuevo (`intento-2`), sin sobrescribir (R01, R02). Nunca se elige entre intentos según el resultado: vale el primer intento válido. Si el segundo también es inválido, la ejecución queda "no completada" y cuenta como tal en 8.3.
- Codec: 400 pasos fijos, lote 32, por (peldaño, semilla), idéntico para K/J/C/S/U de esa ejecución (entrenado con los objetivos del docente sobre los IDs admitidos del peldaño; S usa ese codec con respuestas exactas como objetivo, lo cual es parte de lo que se compara).
- Parámetros declarados, no igualados: generador 835 520; codec 199 296; J entrena además el decoder (902 016 entrenables) (según el borrador 02, de 0.1). Se informa pared/CPU reales por condición; ningún resultado se expresa como ahorro de FLOP ni de energía.
- Semillas: 170020..170024. La semilla controla init, minibatches, corrupción y codec. Se ejecutan las previstas en el diseño (sección 5); no se añaden ni descartan según el resultado.

### 4.1 Control N (vecino TRAIN): definición

Control determinista y privilegiado (usa operación y operandos), sin entrenamiento y sin docente, calculado por peldaño de TRAIN y para cada partición evaluada.
- **Conjunto de referencia:** todos los pares del TRAIN del peldaño (192, 768 o 3072 pares, con su respuesta exacta), independientemente de la admisión del docente. N es un control de la tarea, no de la destilación; usar los pares completos lo hace el control más fuerte.
- **Vecino:** misma operación. Distancia L1 entre operandos, `|a - a'| + |b - b'|`. En `+` y `*` ambos pares están en forma canónica (a <= b), de modo que la conmutatividad queda resuelta por la canonización y no se prueba también el par permutado. En `-` el par es ordenado y se compara tal cual.
- **Desempate (en este orden):** menor `|a - a'|`; luego menor `a'`; luego menor `b'`. No hay distancia 0 (no hay solapamiento de pares entre particiones).
- **Salida:** la respuesta exacta del vecino, como entero. N se evalúa con la misma regla de acierto que los estudiantes.
- N no depende de la plantilla ni de la semilla. Con TRAIN-3072 cubriendo ~54 % del universo de `+` y `*`, N puede quedar por encima del 1,6 % de fase 0 (p. ej. `0*x`, respuestas coincidentes): por eso N fija CF y no se presupone su valor. El hash del script de N se registra en el congelado (R04).

## 5. Diseño factorial viable en CPU

Un cruce completo de 3 peldaños x 5 semillas son 15 ejecuciones (~4,4 a 5,3 h solo entrenamiento y DEV, estimado) para responder preguntas que no lo exigen. Diseño adoptado [D1]:

| Etapa | Peldaño | Semillas | Ejecuciones | Uso |
|---|---|---|---:|---|
| A (curva) | 192, 768, 3072 | 170020 | 3 | curva exploratoria; la primera ejecución sirve de medición de coste |
| B (decisiva) | 3072 | 170021..170024 | 4 | junto con A-3072 da las 5 semillas de H-A..H-D |

Total **7 ejecuciones** (una ejecución = codec + prefijos KD y S + 4 ramas de 500 pasos + evaluación DEV de 20 candidatos + U). El peldaño decisivo es 3072 por fijación a priori [D4]: es el más favorable al aprendizaje, por lo que un negativo ahí es el más fuerte; no se elige por DEV ni por TEST. La etapa B se ejecuta sin puerta de futilidad (coherente con 2.6 del borrador 02); la única puerta es de coste (sección 11). N se calcula por peldaño (barato); U por ejecución. Orden: A-192, A-768, A-3072, B-170021, B-170022, B-170023, B-170024 (intercalado por ejecución, no por condición, para repartir deriva térmica). Los checkpoints de los peldaños 192 y 768 se evalúan en TEST solo tras el congelado y solo descriptivamente.

## 6. Selección de checkpoint (solo DEV)

- Candidatos idénticos para K, J, C, S: actualizaciones {1500, 1600, 1700, 1800, 1900}, los 5 guardados con hash (R07). U y N sin selección.
- Métrica única, fijada de antemano: exactitud entera de generación libre sobre **todo DEV (256 ítems)** [D5]. Empate: el candidato más temprano. Prohibido usar pérdida de minibatch, CE de DEV o cualquier otra métrica para elegir o desempatar. La exactitud en U0 (128) y en vistas (128) se informa por separado como diagnóstico.
- TEST-0.2 no se abre hasta congelar los checkpoints seleccionados de las 7 ejecuciones (4 condiciones cada una) con sus hashes en `CHECKPOINTS-FREEZE-02.json`. Un solo pase de TEST por checkpoint; no se re-evalúa tras ver resultados.
- **Un solo pase de TEST por checkpoint** (R27 lo verifica con un contador).
- **TRAIN-PROBE** (192 pares): tras la selección en DEV, se evalúa solo el checkpoint seleccionado de cada condición (4 por ejecución, ~15 s, estimado) y se informa como memorización; no selecciona.
- Diagnósticos secundarios (no seleccionan): acuerdo con docente, exactitud de caracteres, formato inválido (cuenta como incorrecto, 8.1(v)), techo del codec (3.1), uso/entropía de códigos, fracción con basura tras PAD (R17), reconstrucción del codec y reconstrucción del decoder tras coadaptar (J), no medida en 0.1.

## 7. Estadística

### 7.1 Intervalos y pruebas

Wilson 95 % por condición, semilla y estrato (n = ítems). Para la media de semillas en el peldaño decisivo: bootstrap por ítems (10 000 remuestreos, semilla fija, promedio de las 5 semillas por remuestreo), percentil 95 %. Ese bootstrap por ítems **no incorpora la varianza de inicialización**. Por eso los IC de los criterios de 8.1, 8.2 y de la transferencia son de **dos niveles**: en cada remuestreo se remuestrean las 5 semillas (con reemplazo) y los ítems (con reemplazo), se recalculan p_U (media de semillas), p_N y `CF = max(p_U, p_N)`, y se calcula el estadístico. Además se informa el intervalo t sobre las 5 diferencias por semilla `X - max(U_s, N)` (4 g.l.); si su límite inferior contradice el del bootstrap (8.1(ii)), el caso es "no concluyente" (8.3). Se exige signo consistente por semilla y se reportan todas las semillas individuales, nunca solo la mejor.

Pareado sobre los mismos ítems: McNemar exacto bilateral por semilla; diferencia de medias con IC bootstrap pareado por ítems. Familia A (K, J, C, S frente a U y frente a N, el control que realiza el `max` incluido: 8 contrastes) y familia B (J-C, K-S, C-K, J-K, 4 contrastes): Holm con alfa 0,05 **dentro de cada familia y de cada semilla**. Las hipótesis H-A..H-D son familias separadas, sin corrección entre ellas, y las afirmaciones por condición X de H-A no se ajustan entre X más allá del Holm por semilla: se declara así en el informe. No se usa la combinación de Fisher entre semillas (el borrador 02 la mencionaba): las semillas comparten los mismos ítems y no son independientes. Se informan también los p sin ajustar.

### 7.2 Potencia (calculada)

Wilson 95 % de la proporción observada (calculado): n=256: 0/256 -> [0,0; 1,5]; 1/256 -> [0,1; 2,2]; 4/256 (1,6 %) -> [0,6; 3,9]; 50 % -> [43,9; 56,1]; 90 % -> [85,5; 93,0]. n=512: 0/512 -> [0,0; 0,7]; 1/512 -> [0,0; 1,1]; 8/512 (1,6 %) -> [0,8; 3,1]; 50 % -> [45,7; 54,3]; 90 % -> [87,1; 92,3]. Las filas de n<=128 del borrador 01 no se usan.

Diferencia mínima detectable con 80 % de potencia, aproximada por `z*sqrt(q/n)` con z = z(1-alfa/2) + z(0,8) y `q` = fracción de pares discordantes (**no medida**: se desconoce en 0..60):

| n | q=0,10 | q=0,15 | q=0,25 |
|---|---:|---:|---:|
| 512, alfa 0,05 | 3,9 pp | 4,8 pp | 6,2 pp |
| 512, Holm 4 (alfa 0,0125) | 4,7 pp | 5,7 pp | 7,4 pp |
| 512, Holm 8 (alfa 0,00625) | 5,0 pp | 6,1 pp | 7,9 pp |
| 256, alfa 0,05 | 5,5 pp | 6,8 pp | 8,8 pp |
| 256, Holm 4 | 6,6 pp | 8,1 pp | 10,4 pp |
| 256, Holm 8 | 7,1 pp | 8,7 pp | 11,2 pp |

Esto corrige el borrador 02 (que partía de 128 ítems, ~30 discordantes y "~10 pp"): con TEST 512 y q de 0,10 a 0,25 la diferencia detectable por semilla es ~4-7 pp. El estrato de 256 ítems (plantilla nueva) resuelve ~7-10 pp.

### 7.3 Resolución de DEV

DEV 256 resuelve ~±6 pp en una proporción del 50 % (Wilson 43,9-56,1), ~-4,5/+3,0 pp al 90 % (85,5-93,0) y ~±2-3 pp cerca de 0-5 %. Cuando la exactitud es casi nula, la selección entre candidatos empatados es casi arbitraria: se declara y los resultados se leen a nivel de trayectoria; la regla del más temprano la hace determinista. La frase del borrador 01 de que la selección "resuelve ~6 puntos solo con dos o más peldaños de empate" no es coherente y se descarta.

### 7.4 Justificación de +5 y +10

Los umbrales son convenciones de relevancia, **no efectos estimados**; se justifican por detectabilidad y por la anchura del control, y se congelan antes de ver cualquier dato de 0.2:
- Control fuerte esperado ~1,6 % (referencia de fase 0 en otro dominio, no medida aquí). Con TEST 512 el Wilson de 1,6 % llega a 3,1 %, de modo que `CF + 5` (6,6 %) queda ~3,5 pp por encima del extremo superior del control (3,1 %) y funciona como "piso de no aprendizaje". CF probablemente sea mayor que 1,6 % en 0..60 (4.1), lo que sube también ese piso.
- `+5` coincide con la diferencia mínima detectable por semilla con Holm 4 para q de 0,10 a 0,15 (4,7-5,7 pp; 5,0-6,1 con Holm 8): una sola semilla no lo demuestra y por eso nunca basta por sí solo (8.1 exige además el IC y el signo en las 5 semillas).
- `+10` es ~1,4-2x esa diferencia mínima: suficientemente por encima del ruido para que `CF + 10` sea una afirmación y no un efecto marginal.
Si la q realizada en el peldaño decisivo queda fuera de [0,10; 0,25], se informa que el umbral quedó por debajo o por encima de la diferencia mínima efectiva, sin cambiar el umbral. Los umbrales +5/+10 quedan fijados como convenciones [D7, resuelta]; no se derivan de q.

## 8. Criterios de evidencia

### 8.1 Evidencia de aprendizaje (condición X) en el peldaño decisivo

Todos los criterios usan el mismo control fuerte `CF = max(p_U, p_N)` (la media de semillas de U y el N determinista); el IC lo recalcula en cada remuestreo (7.1).

(i) `p_X >= CF + 10`; (ii) extremo inferior del IC bootstrap de dos niveles de `p_X - CF` > +5 pp (el intervalo t de 7.1 no debe contradecirlo; si lo hace, 8.3); (iii) McNemar exacto con Holm < 0,05 (familia A, 8 contrastes) frente a **ambos** controles, U de la misma semilla y N, en >= 4 de 5 semillas, con diferencia positiva en las 5 frente a ambos (así se supera siempre el control que realiza el `max`); (iv) exactitud DEV del checkpoint seleccionado > la de U (DEV no decide TEST); (v) ningún fallo de ejecución (NaN o inf, código de salida distinto de 0, 11.2). Un **formato inválido** del generador (salida no entera) no invalida: cuenta como respuesta incorrecta y se informa su tasa por condición.

### 8.2 No aprendizaje (aceptar H0-A)

`p_X < CF + 5` Y extremo superior del IC bootstrap de dos niveles de `p_X - CF` < +10 pp Y techo medio del codec (3.1) >= `CF + 10`. Si el techo del codec es < `CF + 10`, el resultado es "no concluyente por codec" (8.3), no "no aprendizaje". Es la única regla de refutación (sección 2).

### 8.3 No concluyente

Cualquier otro caso: diferencia entre +5 y +10, IC que cruza ambos umbrales, ganancia solo en algunas semillas, contradicción entre el bootstrap y el intervalo t, techo del codec por debajo de `CF + 10` con resultado negativo, o una ejecución no completada (4). También si el empate en DEV cambia el signo del resultado según el checkpoint elegido.

### 8.4 Comparaciones entre condiciones (H-B, H-C, H-D)

IC bootstrap de dos niveles de la diferencia de medias de 5 semillas (pareado por ítems), Holm dentro de la familia B (4 contrastes: J-C, K-S, C-K, J-K) y mismo signo en >= 4/5 semillas. El criterio sigue la H1 de cada hipótesis:
- **H-B (J-C):** se rechaza H0 si el límite inferior del IC > 0 y el estimador puntual >= +5. En el estrato de plantilla nueva (256 ítems): solo signo positivo del estimador y ningún IC totalmente negativo; el IC se informa pero no se exige.
- **H-C (K-S):** diferencia relevante si el IC queda por completo fuera de [-5, +5] (límite inferior > +5 o superior < -5), con el signo observado.
- **H-D (C-K):** se rechaza H0 si el límite inferior del IC > 0 y el estimador >= +5. J-K se informa sin hipótesis (efecto conjunto).
Si ninguna condición muestra aprendizaje (8.1), se informan como "sin base": comparan ruido. La transferencia (sección 2) se evalúa aparte y se declara su multiplicidad.

### 8.5 Condición para fase 1

Pasar a texto real exige además reconstrucción DEV >= 95 % de caracteres sin PAD y ausencia de fallo numérico. TEST-0.2 no es confirmación independiente si se reutiliza para decidir la fase 1.

## 9. Requisitos de rigor (R01..R27)

Detalle y verificación de cada uno en `borradores/03-instrumentacion-y-rigor.md`; aquí el contrato y los ajustes del integrador. `verificar_rigor.py` se ejecuta antes del docente principal, antes de TEST y al cierre; cualquier FAIL aborta. Salida `RUN/VERIFICACION-RIGOR.json` con una fila por R. Sin FAIL ni filas ausentes no se declara cerrada la fase.

| R | Contrato | Ajuste del integrador |
|---|---|---|
| R01 | Directorio de ejecución nuevo, sin sobrescribir; aborta con código 3 si existe y no está vacío | Los datos viven en `RUN/data02/`, no fuera de RUN (el borrador 01 los ponía fuera) |
| R02 | Abortar si existen salidas; escritura en modo `'x'`; `--reanudar` explícito | `--reanudar` solo para lotes del docente. Una ejecución inválida se repite desde cero en directorio nuevo (`intento-2`, sección 4), nunca sobrescribiendo; la inválida se conserva con su causa |
| R03 | Artefactos de fase 0/0.1 y `upstream/` de solo lectura, verificados por hash | `RUNS.jsonl` histórico es desfase conocido de 0.1 |
| R04 | Congelación única del protocolo antes del docente | Se aplica a las fases `teacher-train`, `teacher-dev` y `teacher-test` (`frozen_utc` < primer `started_utc` de cada una). La fase `teacher-piloto` (P0) queda cubierta por `PILOTO-FREEZE.json` (su `frozen_utc` < primer `started_utc` de `teacher-piloto`). Hashea `PROTOCOLO-0.2.md` y `PROTOCOLO-0.2.json`, `UMBRAL-ADMISION.json` y el script de N; sección 14 |
| R05 | Enmiendas versionadas en cadena de hashes | Sección 14: tras el congelado solo enmiendas operativas declaradas |
| R06 | Hash de protocolo por etapa, sin cambios a mitad | La etapa `teacher-piloto` registra el hash de `PILOTO-FREEZE.json`; las demás, el del congelado principal |
| R07 | Hash de cada checkpoint al guardarlo (`CHECKPOINTS-LOG.jsonl`) | Los 5 candidatos por condición y ejecución |
| R08 | `test_used_for_selection` derivado de un hook de auditoría de accesos a rutas `*test*` | Contador de evaluaciones TEST por checkpoint (R27). Lista blanca: lectura solo para hash y verificación (etapas `congelado` y `verificacion-datos`); el campo se calcula sobre etapas `train`, `fit`, `seleccion`. El borrador 01 exigía que TEST se leyera solo desde `evaluar.py`, lo que choca con el hasheo del congelado |
| R09 | `hard_forward_equals_official` calculado, no literal | Tolerancia declarada en `PROTOCOLO-0.2.json` |
| R10 | Todo booleano de atestado con `medido_por` y evidencia | - |
| R11 | RSS pico por etapa en proceso hijo propio, muestreo <= 0,2 s, `VmHWM` | Una etapa = un proceso |
| R12 | Pared de entrenamiento separada de DEV/guardado/overhead (suma +-2 %) | Corrige que los tiempos de 0.1 incluían revisiones DEV. Los contadores se verifican en R26 |
| R13 | Telemetría de MemAvailable/swap/carga; negarse a iniciar con otro trabajo pesado | Umbral numérico en 11.2 |
| R14 | `iniciando` antes de `Popen`; registro final en `finally`; huérfanos reconciliables | - |
| R15 | `timeout_s` por etapa; SIGTERM, 10 s de gracia, SIGKILL; temporizador por pregunta del docente | `timeout_s` = 3x la cota alta estimada de la etapa |
| R16 | Errores crudos del docente en `teacher-<split>-errores.jsonl`, sin sustituir | Reinicios del motor <= 3 por lote; fallos distintos de rechazos de contenido (3.4) |
| R17 | `raw_ids` de 8 ids, `first_pad_index`, `basura_tras_pad` | - |
| R18 | `teacher_raw_sin_strip` y `request_key` reproducible | - |
| R19 | Regex ASCII `fullmatch(r'[+-]?[0-9]+', s, re.ASCII)` y `isascii()` | - |
| R20 | Hash del binario y del modelo del docente justificados y comparados con el protocolo | Valores heredados de `TEACHER-CACHE-CONFIG.json` |
| R21 | Semillas, `PYTHONHASHSEED`, hilos y versiones registrados y reproducibles | 2 hilos para estudiantes. Intérprete: el del entorno aislado `/home/carlos/qwen3.5-0.8b/laboratorio-cognitivo/ronda17/ncm/.venv/bin/python` (ruta y hash en `PROTOCOLO-0.2.json`); no se instala nada en el entorno del modelo original |
| R22 | `dont_write_bytecode`; reverificación de `upstream/` (commit `c70274273f489abc73832b2b98584a8483b6b203`) | - |
| R23 | El cierre rechaza `*-RUN.json` obsoletos (run_id, `started_utc`, protocolo, `return_code`) | - |
| R24 | `INFORME.md` generado desde JSON; sin cifras fijas | Los denominadores (256, 512, 7 ejecuciones) salen de los datos |
| R25 | `MANIFEST.json` último, cubre todo `RUN`, luego `RUN` de solo lectura | - |
| R26 | (nuevo) Presupuesto igual verificado, no solo registrado | En cada ejecución, K, J, C y S deben coincidir en número de actualizaciones (1400 + 500), lote y lr por fase, ejemplos vistos (52 800) y secuencia de índices por (semilla, paso); y en tratamiento del optimizador en la transición. Cualquier diferencia es FAIL |
| R27 | (nuevo) Un solo pase de TEST | `CHECKPOINTS-FREEZE-02.json` precede a toda evaluación TEST; cada checkpoint congelado se evalúa en TEST exactamente una vez (contador = 1; > 1 es FAIL); el docente de TEST se consulta una vez; no hay acceso a TEST en etapas de entrenamiento o selección (R08) |

## 10. Orden de ejecución (un solo trabajo pesado a la vez)

Cola secuencial, nunca en paralelo; cada paso en proceso propio, `RUNS.jsonl` registra `iniciando` antes del arranque y no se lanza el siguiente sin código de salida 0 y sin revisar swap.

0. **Revisión independiente del código** (precondición, [D13] resuelta; el nombre de quien escribe y de quien revisa sigue sin asignar, y deben ser distintos): `preparar_datos_02.py`, `verificar_rigor.py`, el ejecutor, el evaluador y el script de N existen antes de cualquier congelado y los revisa una persona o agente distinto de quien los escribió, frente a R01..R27 y 4.1. Sin esa revisión no se ejecuta P0 ni el perfilado.
1. Verificación de entorno y de hashes de fase 0/upstream (R03, R22). `preparar_datos_02.py` genera piloto, particiones, escalera y `PROTOCOLO-0.2.json` (sin consultar al docente).
2. **P-COSTE (perfilado, trabajo propio y previo a todo entrenamiento de 0.2)**: ~50 pasos de generador y 400 pasos de codec con 3072 ejemplos sintéticos (clave `NCM170020|02c`, respuestas exactas, sin docente), longitudes 0..60, para medir el coste por paso y comprobar el supuesto de la caché RVQ a 3072 ejemplos (~2 min, estimado). No guarda checkpoints, no se selecciona nada con él y no toca TRAIN/DEV/TEST. Alimenta la puerta de coste (11.1) [D9].
3. **P0** (`teacher-piloto`): minicongelado (`PILOTO-FREEZE.json`), 168 consultas del docente, `UMBRAL-ADMISION.json` (3.6). Si NO-GO, parar.
4. Verificaciones de datos (las 7 del borrador 01, 1.8): sin pares compartidos entre particiones ni con DEV/TEST legacy; conmutatividad deduplicada; peldaños anidados; U1/U2 ausentes de TRAIN/DEV; prompts <= 64 bytes; reparto por operación; respuestas exactas recomputadas aparte. Si alguna falla, se descarta el directorio y se regenera con `NCM170020|02b`, conservando el fallo.
5. **Congelado único (sección 14)**: `ENTRADA-FREEZE-02.json` y `PROTOCOLO.freeze.json` con hashes de datos, scripts (incluido el de N), plantillas, protocolo (md y json), `UMBRAL-ADMISION.json`, R04 y R20.
6. Docente TRAIN-3072 + DEV (3328 consultas, lotes de 256, reanudables). Informe de admisión por peldaño y partición contra el umbral; si incumple, 3.7.
7. Entrenamiento por ejecución, en el orden de la sección 5: codec (con techo en DEV), prefijo KD, prefijo S, K, S, J, C, evaluación DEV de los 20 candidatos y U, TRAIN-PROBE del seleccionado. Tras cada ejecución: hashes, swap, telemetría y filas R11/R12/R13/R26.
8. Congelado de checkpoints (`CHECKPOINTS-FREEZE-02.json`) de las 7 ejecuciones, con N y U. No hay análisis de TEST antes de este paso.
9. Docente TEST (512 consultas, una sola vez), evaluación TEST de U, N, K, J, C, S por ejecución (un solo pase, R27) y, solo informativo, ancla legacy; estadística (sección 7); `INFORME.md` por plantilla (R24); `verificar_rigor.py`; `MANIFEST.json` (R25).

El docente TEST aparece una sola vez, en el paso 9 (el borrador 02 lo nombraba dos veces en 2.10).

## 11. Presupuesto de tiempo y memoria

### 11.1 Tiempo

**Medido (fase 0/0.1, 0..30, `RESUMEN-COSTE.json`, `RUNS.jsonl`, según el borrador 02):** codec 400 pasos = 7,74 s; generador por etapas, lote 32, 1400 pasos = 263,3 s (0,188 s/paso, CPU/pared ~2,0); joint y continuado, 500 pasos lote 16 = 159,8 s y 159,9 s (0,32 s/paso); evaluación de 7 métodos x 64 ítems = 8,4 s (~0,019 s por ítem y método); docente 0,69 s por consulta con 2,96 CPU-s. Estos tiempos incluían revisiones DEV de 32 ítems.

**Estimado para 0.2:** K y S, 500 pasos lote 16, ~50 s cada uno (cota alta 160 s); evaluación DEV de 20 candidatos x 256 ítems x 0,019 s = ~97 s (el borrador 02 usaba ~20 s: subestimado); U sobre DEV ~5 s.

| Concepto por ejecución | Pared s (estimado) |
|---|---:|
| Codec | 8 |
| Prefijos KD y S (2 x 263) | 527 |
| K y S, 500 pasos | 100 (hasta 320) |
| J y C, 500 pasos (2 x 160) | 320 |
| Evaluación DEV (20 candidatos + U) | ~102 |
| **Total por ejecución** | **~1057 (hasta ~1277)** = 17,6 a 21,3 min |

| Bloque | Pared (estimado) | CPU (estimado) |
|---|---:|---:|
| Piloto P0 (168 consultas) | 116 s | 0,5 ks |
| Docente TRAIN-3072 + DEV (3328 consultas) | 2296 s | 9,9 ks |
| 7 ejecuciones de entrenamiento y DEV | 7399 a 8939 s (123 a 149 min) | 14,8 a 17,9 ks (CPU/pared ~2) |
| Docente TEST (512 consultas) | 353 s | 1,5 ks |
| Evaluación TEST: 38 evaluaciones (7 ejecuciones x {K,J,C,S,U} + 3 N) x 512 ítems + ancla 64 | ~7 min | ~0,8 ks |
| Verificadores, hashes, informe | ~10 min (supuesto) | - |
| Añadidos de la revisión: P-COSTE ~2 min, TRAIN-PROBE (28 x ~4 s) ~2 min, techo del codec ~1 min | ~5 min | ~0,6 ks |
| **Total** | **~3,2 a 3,6 h** (191-217 min) | **~28-31 ks (7,8-8,7 CPU-h)** |

Referencia para decidir: el cruce completo 3x5 son 15 ejecuciones, +8 sobre este plan (+2,3 a 2,8 h) [D1]. Solo es pared de ejecución; excluye redacción, instalación, huecos y repeticiones por invalidez (cada repetición suma 18-21 min; una ejecución como máximo se repite, sección 4). Supuestos no medidos: coste por paso independiente del dominio (3.1) y caché de códigos RVQ con coste despreciable al pasar de 192 a 3072 ejemplos (se verifica en P-COSTE).

**Puerta de coste:** el perfilado P-COSTE (sección 10, paso 2) está separado del entrenamiento, como pide `AGENTS.md`. Si de él se proyecta una pared por ejecución > 1,5 x la cota alta (1,9 ks) o un coste por paso desviado > 20 % del estimado, o si la caché RVQ a 3072 ejemplos no es despreciable, se registra y no se lanza la cola hasta decisión del usuario. Tras A-192 y A-3072 se registra la desviación real con las mismas reglas, sin que esas ejecuciones hagan de perfilado. La puerta no recorta pasos ni cambia el diseño por sí misma [D9]. P-COSTE queda adoptado [D9, resuelta A]; no se acepta que A-192 haga de perfilado.

### 11.2 Memoria y swap

Observado (medido): RSS pico del docente 925 MiB (947 076 KiB); entrenamiento 0,58 GiB máximo (611 992 KiB); swap de hasta ~198 MiB (joint-fit); `MemAvailable` antes del docente en fase 0: 1,70 GiB (1 780 152 KiB), con mínimo de 1,64 GiB en todas las fases (`RESUMEN-COSTE.json`); swap total 21,2 GiB, libre 10,6-10,8 GiB. Reglas de 0.2 [D8, resuelta: A (o C), con compromiso de cerrar aplicaciones durante las ~3,6 h; umbral sin cambio]: no iniciar una etapa si `MemAvailable` < 1,5 GiB o hay otro trabajo pesado (R13); ejecución inválida si RSS del árbol > 2,0 GiB, pérdida no finita, código de salida distinto de 0, interrupción manual o swap libre < 2 GiB al inicio. **Aviso:** el umbral de 1,5 GiB deja solo ~0,14 GiB de margen sobre el mínimo observado (1,64) y ~0,20 sobre 1,70; solo es viable cerrando otras aplicaciones, y el usuario asumió ese compromiso en D8; se comprueba `MemAvailable` al inicio de cada etapa. El borrador 03 pide un umbral "del protocolo" sin valor; uno de 2,5 GiB habría impedido las propias corridas de fase 0 con la memoria disponible observada (1,64-1,70 GiB). El swap usado durante la ejecución solo se registra (descriptivo) hasta que se fije un límite (sección 15).

## 12. Lo que NO se afirmará aunque salga bien

- Que NCM "aprende como Qwen" o conserva su conocimiento: es destilación de secuencias de aritmética 0..60 con tres operaciones, no conversión de pesos ni capacidad general.
- Eficiencia: menor latencia (15 ms frente a 657 ms, medido en 0..30) no es calidad equivalente; parámetros, runtime e hilos difieren. Ni ahorro de energía ni de FLOP.
- Que el entrenamiento conjunto sea mejor "en general": solo este diseño (decoder coadaptado con straight-through, no el del paper), 500 pasos, peldaño 3072, 5 semillas.
- Causalidad KD frente a supervisión más allá de este presupuesto y de un codec entrenado con respuestas del docente.
- Que una buena exactitud demuestre generalización numérica: TEST usa pares nuevos de operandos 0..60 ya vistos en otros pares de TRAIN; la plantilla nueva mide formulación, no extrapolación.
- Efectos de escala a partir de la curva 192/768/3072: una semilla, sin inferencia.
- Comparabilidad con fase 0: dominio distinto; el ancla es informativa.
- Que TEST-0.2 sea confirmación independiente si decide la fase 1.
- Que 5 semillas representen todas las inicializaciones, ni que los ítems sean muestra aleatoria de la aritmética.
- Que la reconstrucción del codec (100 % en fase 0, en 0..30) sea generación, ni que la de J sea la del codec congelado (se mide aparte).
- Que los umbrales +5/+10 sean efectos verdaderos: son convenciones justificadas por detectabilidad (7.4).

## 13. Inconsistencias entre borradores y su resolución

| # | Inconsistencia | Resolución |
|---|---|---|
| a | DEV/TEST: 02 pide >=128; 01 propone 256/512 | 256/512. Potencia recalculada (7.2); se retiran las cifras de 128 |
| b | Escalera 192/768/3072 (01) sin cruzar con 5 semillas x 4 condiciones (02) | Diseño A/B de 7 ejecuciones (5); tiempo recalculado (11) |
| c | 01 cambia a 0..60; 02 mide tiempos y alcance en 0..30 | 0..60 por necesidad de pares únicos; tiempos como estimados; ancla informativa (3.1) |
| d | Admisión 90 % sin dato previo | Piloto P0 y regla (3.6) |
| e | Umbrales +5/+10 sin calibrar | 7.4 con potencia calculada |
| f | Docente TEST mencionado dos veces en 2.10 | Una sola vez, paso 9 de la sección 10 |
| g | 01: congelar antes de cualquier consulta al docente, y piloto pedido para calibrar | Piloto como fase propia (`teacher-piloto`) con `PILOTO-FREEZE.json` y `UMBRAL-ADMISION.json`; el congelado principal sigue siendo único y previo a toda consulta de TRAIN/DEV/TEST (R04, R06) |
| h | 02 2.10 paso 1: docente TRAIN/DEV "solo si hay nuevas particiones" | Las particiones son nuevas: se ejecuta siempre |
| i | 01: U0 nunca criterio de selección; 02: selección sobre todo DEV | DEV 256 completo selecciona [D5]; se retira la frase de 01 |
| j | 01 1.9: "los 4 chequeos de 1.8"; 1.8 lista 7 | Las 7 verificaciones |
| k | Borrador 02, 2.8, combina por Fisher; 2.9 (iii) exige Holm por semilla | Sin Fisher; Holm por semilla y familia (7.1) |
| l | Borrador 02, 2.7: H0-A usa `<=`; 2.9: no-aprendizaje usa `<` más IC | Unificado en 8.2 |
| m | Docente TEST ~90 s (02) frente a 353 s (01) | 353 s para 512 consultas |
| n | Evaluación DEV ~20 s (02) para 20 candidatos | ~97 s a 256 ítems |
| o | 01: TEST solo desde `evaluar.py`; R08 y el hash del congelado leen TEST | Lista blanca de etapas en R08 |
| p | 01: `data02/` y `ENTRADA-FREEZE-02.json`; R01: todo bajo RUN; R04: `RUN/PROTOCOLO.json` | Todo bajo `RUN/`; nombres unificados (sección 14) |
| q | 02.12 "TEST usa operandos 0-30" | Corregido a 0..60 |
| r | R13 umbral de memoria sin valor; fase 0 corrió con 1,70 GiB disponibles (mínimo 1,64) | 1,5 GiB (11.2), con margen estrecho; confirmado en D8 con compromiso de cerrar aplicaciones |
| s | 02: "170020 se rehace" sin mencionar peldaños | 170020 en los 3 peldaños (etapa A) |
| t | 02: N calculado "una vez"; con escalera depende del peldaño | N por peldaño |
| u | 01.3: "TRAIN pasa de 1 a 4 plantillas"; 01.2 usa 4 en todos los peldaños | 4 en todos los peldaños; la referencia de 1 es fase 0 |

## 14. Congelado único y enmiendas

**Regla de congelado único.** El protocolo, las particiones, las plantillas, los umbrales (incluido el de admisión resultante de P0), el diseño de la sección 5 y las reglas de selección y análisis se congelan **una sola vez**, antes de la primera consulta del docente sobre TRAIN, DEV o TEST. El congelado registra `sha256` de este archivo y de `PROTOCOLO-0.2.json`, de los scripts, de las plantillas y de los archivos de datos, el umbral de P0 y `frozen_utc`; escribe `ENTRADA-FREEZE-02.json` y `PROTOCOLO.freeze.json` en `RUN/` y se commitean. `PILOTO-FREEZE.json` (previo a P0) solo cubre el piloto y la regla de 3.6/3.7, y no modifica ningún otro elemento; `UMBRAL-ADMISION.json` entra por hash en el congelado principal. El perfilado P-COSTE es previo, no usa docente ni datos de TRAIN/DEV/TEST y no es seleccionable.

**Tras el congelado:** quedan prohibidas las enmiendas que cambien hipótesis, umbrales, datos, particiones, condiciones, presupuesto, semillas, selección o estadística. Cualquier cambio de ese tipo crea un protocolo nuevo (0.2b), con resultados declarados como de otro protocolo y sin mezclar con los de 0.2. Solo se admiten enmiendas operativas (fallo de herramienta, ruta, reinicio de motor) mediante R05, con `afecta_resultados` justificado y cadena de hashes; no se admiten tras el congelado de checkpoints. A diferencia de la fase 0/0.1 (`AUDITORIA-FINAL.md`: "no se certifica un protocolo único e inalterado"), 0.2 se certifica como protocolo único solo si la tabla siguiente permanece vacía.

**Historial de enmiendas**

| Versión | Fecha UTC | sha256 | Hash anterior | Motivo | Etapa afectada | afecta_resultados |
|---|---|---|---|---|---|---|
| (vacío) | | | | | | |

Estado a la fecha de este borrador (2026-10-28): D1..D13 resueltas, protocolo sin congelar, 0 enmiendas, 0 consultas del docente de 0.2. No existen `PROTOCOLO-0.2.json` ni hashes.

## 15. Pendiente de fijar en PROTOCOLO-0.2.json antes del congelado

Resoluciones de D1..D13 (2026-10-28, aceptada por el usuario en chat), que el archivo hasheado debe recoger tal cual: D1 A (7 ejecuciones); D2 A (0..60, ancla solo informativa, primera ejecución como re-medición de coste); D3 A (1536 anidado sin entrenar, sin contraste T1); D4 A (3072 fijo); D5 A (selección sobre los 256 de DEV); D6 A (piloto de 168 y regla de 3.6; acción ante NO-GO sin decidir); D7 A (+5/+10); D8 A (o C) (1,5 GiB, cerrar aplicaciones); D9 A (P-COSTE); D10 A (etapa B sin futilidad); D11 (plantillas confirmadas); D12 A (ancla legacy informativa); D13 (revisión independiente antes de P0; congelado después de P0). Siguen pendientes, y solo se pueden fijar con el código o con P0, los valores siguientes: (1) tolerancia numérica de R09; (2) `timeout_s` de cada etapa (R15: 3x la cota alta); (3) valor de `PYTHONHASHSEED`; (4) semilla del bootstrap (7.1) y número de remuestreos de dos niveles; (5) límite de reinicios del motor por lote (R16: 3); (6) ruta y hash del intérprete del entorno aislado (R21); (7) tratamiento del estado de Adam al pasar de 1400 a 500 pasos, y lr/lote por fase, a contrastar con el código de 0.1 (4, R26); (8) límite de swap usado durante la ejecución, o su declaración como solo descriptivo (11.2); (9) umbrales numéricos de la puerta de coste con P-COSTE (11.1) y número exacto de pasos del perfilado; (10) transcripción de los textos de plantillas ya confirmados [D11] (el contenido está decidido; falta solo copiarlos y hashearlos); (11) hash del script de N (4.1) y de la regla `REGLA-ADMISION.txt`; (12) transcripción de las resoluciones de D1..D13 de arriba; (13) umbral de admisión resultante de P0 (`UMBRAL-ADMISION.json`), no medido; (14) asignación de quién escribe y quién revisa el código [D13], y resultado de la revisión; (15) acción ante un NO-GO de P0 [D6], solo si ocurre; (16) umbral de la puerta de coste con las cifras de P-COSTE, no medidas todavía (11.1). Nada de lo anterior se ha ejecutado ni medido.
