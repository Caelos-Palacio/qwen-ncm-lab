# 2. Diseño experimental (fase 0.2)

Estado: borrador de sección. Todo umbral se fija antes de entrenar; no se cambia tras ver TEST. Ámbito: aritmética de enteros 0-30, respuestas de hasta 8 bytes, mini-NCM de ~1.0 M parámetros, CPU de 2 hilos. Nada de esto se extrapola a lenguaje general.

## 2.1 Punto de partida y qué corrige

La fase 0/0.1 dejó 1/64 (KD), 0/64 (joint, continuado, sin entrenar) y 1/64 (vecino TRAIN) en TEST, con una semilla (170020). Defectos de diseño que 0.2 corrige y que impiden hoy concluir nada comparativo:
- una sola semilla: los 64 ítems no son 64 entrenamientos independientes;
- la rama supervisada se interrumpió en el paso 200 (presupuesto desigual, no comparable);
- el presupuesto efectivo difería entre condiciones (KD paró en 1400 por regla DEV; joint/continuado añadieron 500 desde un KD seleccionado);
- la selección usó pérdida de minibatch/CE como desempate, y DEV tiene 32 ítems (resolución 3,1 pp; 0/32 o 1/32 en casi todas las revisiones, es decir, ruido);
- TEST de fase 0 ya fue abierto: no puede servir como confirmación de 0.2.

Requisito previo (lo define la sección de datos): una partición TEST-0.2 nueva, disjunta de TRAIN/DEV/TEST de fase 0, de >=128 ítems (mitad plantilla vista, mitad nueva), congelada y con docente obtenido una sola vez tras congelar checkpoints. Se recomienda DEV >=128. Si DEV queda en 32, se declara que la selección es casi aleatoria y los resultados se leen a nivel de trayectoria, no de checkpoint óptimo.

## 2.2 Condiciones (todas con el mismo codec por semilla, mismos IDs admitidos, mismos prompts)

| Id | Condición | Entrenamiento del generador | Decoder |
|---|---|---|---|
| U | Sin entrenar | 0 actualizaciones (init de la semilla) | fijo |
| N | Vecino TRAIN | ninguna; control privilegiado (usa operación/operandos estructurados), determinista | n/a |
| K | KD por etapas | 1400 + 500 actualizaciones con objetivo docente (CE de código por escala, corrupción 5%) | fijo |
| J | KD + joint | 1400 como K; luego 500 con CE de texto + 0,25 CE auxiliar, straight-through | entrenable |
| C | KD + continuado | 1400 como K; luego 500 con la misma pérdida de texto que J | fijo |
| S | Supervisado completo | 1400 + 500 actualizaciones con respuesta exacta como objetivo, ININTERRUMPIDO | fijo |

K, J y C comparten el prefijo de 1400 actualizaciones (mismo estado, mismas semillas de minibatch); S tiene su propio prefijo de 1400 con el mismo calendario. J y C son comparables entre sí exactamente como en 0.1 (mismo inicio, mismos minibatches). K contra J/C aísla el efecto de la fase de 500 pasos con pérdida de texto frente a seguir con pérdida de códigos.

## 2.3 Presupuesto igual

- Actualizaciones de generador idénticas en U-excluido: 1900 = 1400 (lote 32, lr 5e-4) + 500 (lote 16, lr 1e-4). Sin parada temprana por paciencia: se ejecuta el presupuesto completo, o la ejecución se declara inválida y se repite entera (nunca se cuenta una ejecución interrumpida).
- Ejemplos vistos iguales: 1400x32 + 500x16 = 52 800 por condición; mismos 192 TRAIN usables; el mismo generador de índices de minibatch por (semilla, paso).
- Codec: 400 pasos fijos, lote 32, por semilla (sin parada temprana), idéntico para K/J/C/S/U de esa semilla.
- Parámetros: se declaran, no se igualan. Generador 835 520; codec 199 296; J entrena además el decoder (902 016 entrenables). El coste por actualización de J difiere; se informa pared/CPU real aparte, no se corrige.
- Eficiencia: ningún resultado se expresa como ahorro de FLOP ni energía; solo pared, CPU, RSS y swap medidos con `ejecutar_fase.py`.

## 2.4 Semillas

Lista fija, 5 semillas: 170020, 170021, 170022, 170023, 170024. La semilla controla init del generador, orden de minibatches, corrupción de condición y codec. Se ejecutan todas; no se añaden ni se descartan semillas según el resultado. 170020 se rehace con el calendario nuevo (los artefactos de fase 0 están congelados y no se reutilizan). N es determinista y se calcula una vez.

## 2.5 Selección de checkpoint (solo DEV)

- Candidatos idénticos para K, J, C, S: actualizaciones {1500, 1600, 1700, 1800, 1900} (5 por ejecución). Se guardan los 5. U no tiene selección.
- Métrica única, declarada de antemano: exactitud entera de generación libre en DEV (solo el prompt entra al rollout; la respuesta es un entero completo igual a la referencia aritmética), sobre todos los ítems de DEV.
- Empate: se elige el candidato más temprano. Se prohíbe usar pérdida de minibatch de TRAIN, CE de DEV o cualquier otra métrica para desempatar o elegir.
- TEST-0.2 no se abre hasta que los 4x5 checkpoints seleccionados y sus hashes estén en un archivo de congelación firmado. Un solo pase de evaluación TEST por checkpoint seleccionado; no se re-evalúa tras ver resultados.
- Diagnóstico secundario (no selecciona): acuerdo con docente, exactitud de caracteres, formato inválido, uso/entropía de códigos y reconstrucción TEST del decoder tras coadaptar (J), que en 0.1 no se midió.

## 2.6 Criterios de parada y de invalidez

- Parada normal: presupuesto de 2.3 completo. No hay parada por plateau.
- Parada de seguridad (ejecución inválida, se repite desde cero): pérdida no finita, código de salida distinto de 0, RSS de árbol >2,0 GiB, o swap libre <2 GiB al inicio de una ejecución (hoy: 10,9 GiB libres). Una interrupción manual también invalida la ejecución y se conserva su log y su coste como run aparte.
- Parada del experimento: no hay parada por futilidad ni análisis intermedio en TEST. Si tras las 5 semillas el resultado es negativo, se conserva como resultado.

## 2.7 Hipótesis y predicciones falsables

Estimador: exactitud TEST-0.2 por semilla, p_X = media sobre las 5 semillas (U y N solo una vez). Margen = diferencia absoluta en puntos porcentuales (pp). Control fuerte = max(p_U, p_N) (en 0.1: <=1,6%).

- H0-A (no hay aprendizaje) para X en {K, J, C, S}: p_X <= control fuerte + 5 pp. H1-A: p_X >= control fuerte + 10 pp.
- H0-B (el entrenamiento conjunto no ayuda): p_J - p_C <= 0 pp. H1-B: p_J - p_C >= +5 pp (en TEST completo; predicción adicional: >= +5 pp también en el subconjunto de plantilla nueva).
- H0-C (KD no aporta sobre supervisión exacta a presupuesto igual): |p_K - p_S| <= 5 pp. H1-C: |p_K - p_S| > 5 pp, con el signo observado; no se predice dirección.
- H0-D (la fase de 500 pasos con texto no ayuda a KD): p_J - p_K <= 0. H1-D: >= +5 pp.
- Predicción de transferencia: p_X en plantilla nueva >= 5% en al menos una de {K, J, C, S}; si todas quedan <5%, la generalización de formulación no se demuestra aunque la plantilla vista sí mejore.
- Predicción de refutación (declarada): si ninguna condición supera control fuerte + 5 pp en TEST, se acepta H0-A con alcance "este tamaño, este presupuesto, esta tarea".

## 2.8 Análisis estadístico

- Intervalos: Wilson al 95% de la exactitud por condición y semilla (n = ítems TEST-0.2); además, para la media de semillas, bootstrap por ítems (10 000 remuestreos de ítems, semillas fijas, promedio de semillas por remuestreo).
- Comparación pareada sobre los mismos ítems: por semilla, McNemar exacto (binomial bilateral sobre discordantes) entre condiciones; ítems no emparejables no existen (todas generan para el mismo TEST). Diferencia de medias entre condiciones con intervalo bootstrap pareado por ítems (percentil 95%).
- Familias y corrección: familia A (aprendizaje: K, J, C, S contra N) y familia B (comparaciones: J-C, K-S, J-K), Holm con alfa 0,05 dentro de cada familia, aplicado sobre el p de McNemar combinado por semilla (Fisher); se reportan también los p por semilla sin ajustar.
- Potencia orientativa: con 128 ítems y ~30 discordantes por semilla, McNemar detecta ~10 pp a alfa 0,05; con 5 semillas el bootstrap sobre la media acorta el intervalo, pero las semillas no son ítems independientes. No se interpreta ausencia de significación como equivalencia salvo por la regla de 2.9.
- Se reportan todas las semillas individuales, no solo la media; la mejor semilla nunca se presenta como resultado.

## 2.9 Criterios de conclusión

- Evidencia de aprendizaje (condición X), requiere TODO: (i) p_X >= control fuerte + 10 pp; (ii) extremo inferior del IC bootstrap de p_X - control fuerte > +5 pp; (iii) McNemar con Holm < 0,05 contra N en >= 4 de 5 semillas, con la diferencia positiva en todas; (iv) la exactitud DEV del checkpoint seleccionado es > la de U (sin que DEV decida TEST); (v) cero fallos numéricos/formato.
- No aprendizaje (aceptar H0-A): p_X < control fuerte + 5 pp Y extremo superior del IC bootstrap de la diferencia < +10 pp.
- No concluyente: cualquier otro caso (por ejemplo diferencia entre +5 y +10 pp, o IC que cruza ambos umbrales, o ganancia solo en alguna semilla). También no concluyente: DEV < 128 ítems y la diferencia depende del checkpoint elegido; o una ejecución inválida no repetida.
- Para H1-B/H1-C/H1-D la regla es análoga con margen +5 pp, IC bootstrap pareado con límite inferior > 0 y mismo signo en >= 4/5 semillas. Si ninguna condición muestra aprendizaje (2.9, primer punto), las comparaciones entre condiciones se informan como "sin base" porque comparan ruido.

## 2.10 Orden de ejecución (un solo trabajo pesado a la vez)

Cola secuencial, nunca en paralelo; `ejecutar_fase.py` registra cada paso en `RUNS.jsonl`. El docente (~0,93 GiB RSS) y el entrenamiento no coinciden.
1. Docente TEST-0.2: solo después de congelar protocolo, particiones y checkpoints (paso 5); se pospone a la fase de evaluación. El docente TRAIN/DEV de 0.2 solo se lanza si el protocolo exige nuevas particiones.
2. Por semilla, en el orden 170020 a 170024 (intercalado por semilla, no por condición, para repartir deriva térmica): codec -> prefijo KD (1400) -> prefijo S (1400) -> K (500) -> S (500) -> J (500) -> C (500) -> evaluación DEV de los 20 candidatos de la semilla.
3. Tras cada semilla: verificación de hashes y de que no hay swap creciente. Un trabajo pesado = un proceso; no se lanza el siguiente hasta código de salida 0.
4. Cuando las 5 semillas terminan: congelar los 20 checkpoints seleccionados con hashes (`CHECKPOINTS-FREEZE`-equivalente nuevo, en directorio de ejecución nuevo).
5. Docente TEST-0.2 (una vez) -> evaluación TEST de U, N, K, J, C, S -> informe.

## 2.11 Estimación de tiempo (costes medidos en `RESUMEN-COSTE.json`/`RUNS.jsonl`, fase 0/0.1)

Medidos: codec 400 pasos = 7,74 s; generador por etapas lote 32 = 263,3 s por 1400 pasos (0,188 s/paso, CPU/pared = 2,0); joint y continuado, 500 pasos lote 16 = 159,8 y 159,9 s (0,32 s/paso). Los tiempos medidos incluyen las revisiones DEV de esos runs. Estimado (no medido): K y S en lote 16, 500 pasos, ~50 s cada uno (cota alta: 160 s si el coste por paso fuera el de J/C). Evaluación 7 métodos x64 ítems = 8,4 s; ~15-20 s para 128 ítems; docente TEST de 64 ítems = 44 s (126 ítems: ~90 s).

| Concepto por semilla | Pared s |
|---|---:|
| Codec | 8 |
| Prefijos KD y S (2 x 263) | 527 |
| K y S, 500 pasos | 100 (hasta 320) |
| J y C, 500 pasos (2 x 160) | 320 |
| Evaluación DEV de candidatos | ~20 |
| **Subtotal** | **~975 (hasta ~1195)** |

5 semillas: ~4 900 s a ~6 000 s (81 a 100 min) de entrenamiento y DEV; + docente TEST ~90 s + evaluación TEST ~20 s; total estimado ~83-102 min de pared y ~165-205 CPU-min (CPU/pared ~2). Solo ejecución medida: excluye redacción, instalación, huecos y la obtención de nuevos datos DEV/TRAIN si se amplían (docente TRAIN/DEV de 224 consultas costó 151 s). RSS esperada ~0,6 GiB (máx. observada 0,61 GiB entrenando, 0,93 GiB docente); swap observada de hasta 198 MiB en joint-fit. Supuesto: máquina igual y sin otra carga; si el coste real por paso supera el 20% del estimado, se registra y no se recorta el presupuesto.

## 2.12 Lo que NO se afirmará aunque salga bien

- Que NCM "aprende como Qwen" o conserva su conocimiento: es destilación de secuencias de aritmética 0-30, no conversión de pesos ni capacidad general.
- Que haya eficiencia: menor latencia por pregunta (~15 ms frente a ~657 ms) no es calidad equivalente; Qwen y el estudiante difieren en parámetros, runtime e hilos. No se afirmará ahorro de energía ni FLOP.
- Que el entrenamiento conjunto sea mejor "en general": solo en este diseño (decoder coadaptado con straight-through, no el del paper), 500 pasos, 192 ejemplos, 5 semillas.
- Causalidad KD frente a supervisión más allá de este presupuesto y este codec compartido (entrenado con respuestas del docente).
- Que una buena exactitud TEST demuestre generalización numérica: TEST usa operandos 0-30 como TRAIN; la plantilla nueva mide formulación, no extrapolación.
- Que TEST-0.2 sea confirmación independiente si se reutiliza para decidir la fase 1; la decisión de pasar a texto real requiere además reconstrucción DEV >=95% y ausencia de fallo numérico.
- Que las cinco semillas representen la población de todas las inicializaciones, ni que los ítems TEST sean muestras aleatorias de la aritmética en general.
- Que la reconstrucción del codec (100% en fase 0) sea generación; ni que la de J sea la del codec congelado: se mide aparte.
