# Revisión independiente de PROTOCOLO-0.2.md

Alcance: lectura de `AGENTS.md`, `PROTOCOLO-0.2.md`, `DECISIONES-PENDIENTES.md`, contraste puntual con `borradores/` y `revision/`, y recálculo ligero en Python (sin trabajos pesados). No se editó el protocolo ni nada congelado. Cifras marcadas (recalculado) las rehice yo; (medido) vienen de `RESUMEN-COSTE.json`, `RUNS.jsonl`, `GENERATOR-FIT.json`, `JOINT-FIT.json`, `TEACHER-TRAINDEV-STATS.json`.

## Veredicto

**Requiere correcciones antes de congelar.** La estructura es sólida y la aritmética central es correcta, pero hay 4 bloqueantes, todos de texto y de bajo coste: una marca TODO, un criterio de evidencia que no usa el control fuerte que él mismo define, una contradicción entre el piloto y la regla R04, y dos reglas sin definir (N y la consecuencia de incumplir la admisión). Después de corregirlos y de resolver D1..D13, el protocolo puede pasar al usuario para congelar. No encontré ninguna violación frontal de `AGENTS.md`.

## 1. Cálculos verificados (recalculado)

| Elemento | Protocolo | Recalculado |
|---|---|---|
| Pares canónicos 0..60 | `+` 1891, `*` 1891, `-` 3721 = 7503 | Correcto (61·62/2 y 61²). En 0..30: 496/496/961 correcto |
| Uso máximo por operación | 1337 (70,7 % y 35,9 %) | 1024+86+171+56 = 1337; 1337/1891 = 70,7 %; 1337/3721 = 35,9 % |
| Particiones | DEV 86+85+85, TEST 171+171+170, piloto 168 | Suman 256, 512 y 168 |
| Presupuesto de ejemplos | 52 800 | 1400·32 + 500·16 = 52 800; 275 pasadas con 192, 17,2 con 3072 |
| Wilson n=256 y n=512 (sección 7.2) | todos los intervalos citados | Coinciden al decimal (0/256 → 0,0–1,5; 4/256 → 0,6–3,9; 8/512 → 0,8–3,1; 90 % → 85,5–93,0 y 87,1–92,3; etc.) |
| Wilson del piloto | 160/168 → L = 90,9; 151/168 → L = 84,4 | Correcto |
| Diferencia mínima detectable | 3,9/4,8/6,2; 4,7/5,7/7,4; 5,5/6,8/8,8; 6,6/8,1/10,4 | Coinciden exactamente con `z·sqrt(q/n)` |
| Tiempo por ejecución | 1057 s (hasta 1277) | 8+527+100+320+102 = 1057; con K/S a 320, 1277 |
| 7 ejecuciones | 7399–8939 s (123–149 min) | Correcto |
| Total sección 11 | 186–212 min; 27–31 ks CPU; 7,5–8,6 CPU-h | 11 184 s = 186,4 min; límite alto 212 min; CPU 27,5–30,6 ks. Correcto |
| Docente | 3328 consultas = 2296 s, 9,9 ks | 3328 × 0,69 = 2296; 3328 × 2,96 = 9851. Correcto |
| TEST 38 evaluaciones | 35 + 3 | 7·5 + 3 = 38; 38·512·0,019 ≈ 370 s ≈ 6 min. Correcto |
| Tiempos de D1/D3/D6/D10 | +2,3–2,8 h; +18–21 min; 70–85 min | Correctos. D1-C da 2,5–2,8 h (no 2,6–3,0): menor |
| Medidas de fase 0 | 263,3 s/1400 pasos; 159,8/159,9 s; 8,4 s; 0,675 s/consulta; 662,3 CPU-s/224 | Coinciden con los JSON (CPU/pared ≈ 2,0) |

## 2. Hallazgos

### Bloqueantes

**B1. Sección 8.1: marca "TODO" y criterio incoherente con el control fuerte.**
- El encabezado dice "…en el peldaño decisivo, TODO". Es el único TODO del texto. Hay que decidir qué falta (casi seguro lo de abajo) y borrarlo.
- El criterio (iii) exige McNemar frente a **N**, y la familia A de 7.1 también contrasta solo contra N. Pero `CF = max(p_U, p_N)`: si `p_U > p_N` en el peldaño 3072, la condición pasa (iii) sin haber superado el control fuerte.
- Arreglo: en 7.1 y 8.1(iii) contrastar frente al control que realiza el `max` (o frente a ambos, ocho contrastes con Holm). Declarar cómo se recalcula CF dentro de cada remuestreo bootstrap (hoy no se dice).
- Alinear también la "Refutación declarada" de la sección 2 ("si ninguna supera CF+5 se acepta H0-A") con 8.2, que además exige el límite superior del IC < +10. Dejar solo una regla.

**B2. R04/R06 contradicen la secuencia con el piloto P0.**
- R04 (borrador 03) exige `frozen_utc` menor que el primer `started_utc` de una fase `teacher-*`. P0 consulta al docente antes del congelado principal (sección 10, paso 2 antes del 4), así que `verificar_rigor.py` daría FAIL por diseño. El "ajuste del integrador" de R04 no lo resuelve.
- Además, el umbral de admisión (resultado de P0) debe entrar en `PROTOCOLO-0.2.md/.json`, que se hashea después de P0, pero R06 pide un hash de protocolo por etapa y P0 corrió con otro hash.
- Arreglo: R04 se refiere a las fases `teacher-train|dev|test`, y P0 es una fase `teacher-piloto` cubierta por `PILOTO-FREEZE.json` (R06 usa ese hash). Y el umbral va en un archivo propio (`UMBRAL-ADMISION.json`, hash registrado) o se declara que `PROTOCOLO-0.2.json` se completa tras P0 y solo entonces se hashea, con el texto de la sección 3.6 fijo.

**B3. El control N no está definido.** Falta la regla de vecino: métrica de distancia, qué se considera vecino (misma operación, operandos más cercanos, desempate), qué conjunto de TRAIN usa (los 3072 o solo los admitidos) y cómo resuelve conmutatividad. Con TRAIN-3072 cubriendo ~54 % del universo `+`/`*`, N puede estar bastante por encima del 1,6 % de fase 0 (p. ej. `0*x`, respuestas coincidentes), y como CF = max(U, N), N fija el umbral de toda la inferencia. Arreglo: especificar N en la sección 4 antes de congelar y registrar el código o hash del script.

**B4. Consecuencia de incumplir el umbral de admisión sin definir (3.4, 3.6, 10 paso 5).** Se informa la admisión "por peldaño y partición contra el umbral", pero no se dice qué pasa si TRAIN-3072, DEV o TEST caen por debajo (¿ejecución inválida?, ¿se entrena igualmente?, ¿protocolo nuevo?). Como no se puede reintentar ni sustituir, es una decisión que debe tomarse antes de ver datos. Arreglo: "Admisión < umbral en cualquier peldaño de TRAIN o en DEV: parar y decidir el usuario (protocolo nuevo 0.2b); en TEST: se informa, no se excluye (la métrica usa la respuesta exacta)". Aclarar además que la métrica de TEST es exactitud numérica, no acuerdo con docente, y qué papel cumple el docente de TEST.

### Importantes

**I1. Hipótesis H-B/H-C/H-D: margen declarado frente a criterio usado (2 y 8.4).**
- H-B y H-D declaran H1 ≥ +5 pp, y H-C declara |dif| > 5, pero 8.4 pide "IC con límite inferior > 0" (no > 5). Para rechazar H0 de margen hay que exigir límite inferior > 5 (o > 0 si la hipótesis es de superioridad sin margen). Hoy 8.4 es más débil que H1 y distinta de 8.1(ii).
- H-B exige además +5 en el estrato de plantilla nueva (256 ítems), cuya diferencia mínima detectable es 6,8–10,4 pp (7.2). Con una diferencia verdadera de +5 la potencia es ~50 % o menos, y con el criterio de IC y signo en 4/5 semillas es casi inalcanzable. Arreglo: bajar a "signo positivo y no contradicción" en el estrato, o subir a un margen que 256 ítems pueda detectar (≥ 8 pp), y decirlo.
- H-D (J−K) mezcla dos factores (fase de 500 pasos con CE de texto y decoder entrenable), así que no responde a "la fase con texto". El contraste limpio es C−K (decoder fijo). La familia B tiene 3 contrastes y no incluye C−K. Añadir C−K (Holm 4) o renombrar H-D como "J frente a K, conjunto".
- Sin corrección entre hipótesis (H-A..H-D) ni entre las 4 condiciones X de H-A en 8.1(ii). Declarar que son 4 familias separadas y que las afirmaciones por condición X no están ajustadas, o aplicar Holm al IC.

**I2. "Transferencia de formulación" (sección 2) es ambigua y floja.** "Al menos una de K, J, C, S alcanza ≥ 5 %" no dice si es la media de 5 semillas o una semilla, ni sobre U1 y U2 juntas (256) o por separado (128). Un 5 % absoluto está por debajo de CF+5 y no usa IC. "Al menos una de cuatro" infla el falso positivo. Arreglo: medirla sobre la media de 5 semillas en U1∪U2, con Wilson o bootstrap con límite inferior > CF_nuevas (CF recalculado en ese estrato), y declarar la multiplicidad.

**I3. 8.1(v) "cero fallos numéricos/formato" puede ser imposible.** Un generador de 1,0 M parámetros producirá salidas no enteras (sección 6 mide "formato inválido" como diagnóstico). Exigir cero formato inválido hace inalcanzable 8.1 por una propiedad que se puntúa ya como error. Arreglo: separar "fallo de ejecución" (NaN/inf, código de salida ≠ 0), que invalida, de "formato inválido", que cuenta como incorrecto y se informa.

**I4. Techo del codec: un negativo en H-A puede ser un fallo del codec.** La sección 3.1(2) admite que la reconstrucción del codec con respuestas de hasta 4 dígitos y signo es desconocida y solo se "informa". Si el codec reconstruye mal, K, J, C y S (ambos usan el mismo codec) no pueden superar CF+5 y 8.2 aceptaría H0-A con un alcance engañoso. Arreglo: medir en DEV el techo (decodificar el código de la respuesta exacta/docente: exactitud entera) y declarar en 8.2/8.3 que si techo < CF+10 el resultado es "no concluyente por codec", no "no aprendizaje". Esto además es una medición de reconstrucción etiquetada aparte, como exige `AGENTS.md`.

**I5. Separación perfilado/entrenamiento (AGENTS.md).** La ejecución A-192 hace a la vez de medición de coste (3.1, 5, 11, puerta D9) y de ejecución de entrenamiento con checkpoints DEV. Es un solo trabajo, pero `AGENTS.md` pide mantener separados perfilado y entrenamiento. Además el supuesto de caché RVQ a 3072 ejemplos solo se comprueba en la tercera ejecución (A-3072), tarde para la puerta. Arreglo: un perfilado corto previo (p. ej. 50 pasos con 3072 ejemplos y longitudes de 0..60, antes del congelado, no seleccionable) que alimente la puerta, o declarar explícitamente en D9 que se acepta la excepción.

**I6. Estimador de varianza entre semillas (7.1, 8.1(ii)).** El bootstrap por ítems promedia 5 semillas pero ignora la varianza de inicialización; lo mitigan solo el signo por semilla y el reporte individual. Con 5 semillas y mismos ítems, el IC de 8.1(ii) es optimista. Arreglo: añadir un IC que remuestree semillas e ítems (bootstrap de dos niveles) o el intervalo t sobre las 5 diferencias por semilla (4 g.l.) como criterio adicional de 8.1/8.2.

**I7. Errores de unidades en medidas citadas (11.2, 13 fila r, 3.5, D8).**
- "RSS pico del docente 947 MiB" es en realidad 947 076 **KiB = 925 MiB** (mismo muestreo; la "otra medición" de la auditoría no es distinta). Corregir a 925 MiB en 3.5 y 11.2.
- "`MemAvailable` 1,78 GiB" es 1 780 152 KiB = **1,70 GiB**. El mínimo medido en todas las fases es 1,64 GiB. El umbral 1,5 GiB deja solo ~0,14 GiB de margen frente a lo observado, y el texto que lo justifica (13.r, D8) cita una cifra falsa. Arreglo: citar 1,70/1,64 GiB y reconsiderar si 1,5 GiB es viable sin cerrar aplicaciones (D8 ya pregunta).
- "entrenamiento 0,61 GiB máximo" es 611 992 KiB = 0,58 GiB; "swap libre 10,9 GiB" es 10,6–10,8 GiB.

**I8. Garantía de presupuesto igual no verificada por R.** Sección 4 promete 1900 actualizaciones y 52 800 ejemplos iguales por condición, y R12 registra los contadores, pero ningún R exige que el verificador compruebe la igualdad entre K, J, C, S en cada ejecución (mismo número de pasos, lote, lr, ejemplos, índices por (semilla, paso)). Tampoco se dice si el estado del optimizador (Adam) se restablece al pasar a la fase de 500 pasos ni cómo se reinician el lr y el lote. Arreglo: añadir a R12/R24 un chequeo de igualdad de contadores y declarar el tratamiento del optimizador.

**I9. Reglas de repetición e invalidez (4, 11.2, R02).** "Ejecución inválida … se repite entera" no dice dónde se escribe la repetición (R01/R02 prohíben sobrescribir), si se conserva la inválida, ni cuántas repeticiones se permiten. Arreglo: directorio nuevo por intento, la inválida se conserva con su causa, máximo 1 repetición con la misma semilla y registro en `RUNS.jsonl`. Añadir también un límite de swap usado durante la ejecución (hoy solo hay límite al inicio) o declararlo solo descriptivo.

**I10. Verificación de "un solo pase de TEST" (sección 6).** R08 controla accesos a rutas `*test*`, pero ningún R comprueba que cada checkpoint se evaluó exactamente una vez en TEST ni que no se re-evaluó. Arreglo: R08 añade contador de evaluaciones TEST por checkpoint = 1 y falla si es mayor.

### Menores

- **7.3:** "DEV 256 resuelve ~±6 pp en una proporción de 90 %" es incorrecto: al 90 % el Wilson es 85,5–93,0 (−4,5/+3,0 pp); ±6 pp corresponde al 50 %.
- **7.4:** "CF+5 queda ~2 pp por encima del extremo superior del control" es incorrecto: CF+5 = 6,6 % frente a un límite superior de 3,1 %, es decir ~3,5 pp (repetido en D7). Además CF probablemente sea mayor que 1,6 % en 0..60 (ver B3).
- **Huecos numéricos para PROTOCOLO-0.2.json:** tolerancia de R09, `timeout_s` de cada etapa, valor de `PYTHONHASHSEED`, semilla del bootstrap, límite de reinicios del motor por lote (3 está en R16), ruta/hash del intérprete del venv aislado (`AGENTS.md` lo fija y no se menciona). Todo debe estar en el archivo hasheado.
- **TRAIN-PROBE** (3.3, "mide memorización") no aparece en la sección 6, 10 ni 11: añadir dónde y cuándo se evalúa (192 ítems × checkpoints seleccionados, coste despreciable).
- **Fases anteriores de código:** D13 recomienda revisión independiente del código frente a R01..R25 antes de P0; el protocolo no lo establece como precondición ni exige que los scripts existan antes del congelado que los hashea. Incorporarlo a la sección 10 (paso 0).
- **Sección 3.2:** el reaparecimiento de los 192 TRAIN legacy en DEV/TEST nuevos es aceptable, pero conviene registrar cuántos reaparecen (diagnóstico).
- **Referencias cruzadas:** no hay numeración inexistente. Todas las referencias internas (3.1, 3.6, 7.4, 8.1, 11, 14, R#, D#) existen. Las referencias del tipo "1.8", "2.6", "2.10" son a los borradores y se dice así; la fila 13 usa "02.8/02.9" sin la palabra "borrador" (aclarar).

## 3. Cumplimiento de AGENTS.md

| Requisito | Estado |
|---|---|
| Protocolo y particiones congelados antes de entrenar | Cumple (paso 4 antes de 5–6); con la salvedad de B2 |
| Selección solo TRAIN/DEV, métrica única, desempate al más temprano | Cumple (sección 6, prohíbe CE de DEV y pérdida) |
| TEST tras congelar checkpoints | Cumple (pasos 7 antes que 8, docente TEST una sola vez); falta I10 |
| Datos crudos, errores y hashes | Cumple (R07, R16–R18, 3.4, R25) |
| Pared, CPU, memoria, swap, pasos, parámetros, calidad | Cumple (R11–R13, sección 4, parámetros declarados); swap solo al inicio (I9) |
| Un solo trabajo pesado | Cumple (sección 10 y R13) |
| Separación perfilado/entrenamiento | **Parcial**: I5 |
| Reconstrucción ≠ generación | Cumple (estimador con solo prompt, reconstrucción como diagnóstico); falta el techo del codec (I4) |
| Ámbito de cada afirmación | Cumple (sección 12 es completa y prudente) |
| No tocar upstream/ ni resultados congelados | Cumple (R03, R22, caché nueva) |
| Entorno aislado, no instalar en el del modelo | No mencionado explícitamente (menor) |

## 4. Cobertura de defectos de la revisión previa en R01..R25

- **Guardias anti-sobrescritura:** R01, R02 (modo `'x'`, código 3, `--reanudar`), R25 (solo lectura). Cubierto. Falta la política de repetición (I9).
- **Atestados medidos:** R08, R09, R10, R17, R18, R19. Cubierto.
- **Desempate:** sección 6 (más temprano; prohíbe CE) y 7.3. Cubierto en el protocolo; sin R que lo compruebe (el verificador debería recomputar la selección desde las filas de DEV; sugerido).
- **Presupuesto igual:** sección 4 y R12; sin verificación de igualdad (I8).
- **Swap:** R13 y 11.2. Cubierto, con las salvedades de I7 e I9.
- **Semillas:** R21 y sección 4 (170020..170024, sin añadir ni descartar). Cubierto. Un R equivalente debería comprobar que las 7 ejecuciones previstas existen y que las semillas coinciden con el protocolo (parcialmente en R24/R25).

## 5. Hipótesis y criterios de evidencia

- **Falsables:** H-A, H-B, H-C y H-D están formuladas con H0/H1 numéricas y son falsables en el papel. 8.1 es alcanzable solo si algún estudiante supera ~CF+10 en 0..60 (probablemente ≥ 12 %), lo cual el diseño reconoce implícitamente al aceptar H0-A.
- **Potencialmente imposible o débil:** el "cero formato inválido" de 8.1(v) (I3); la prueba por estrato de 256 de H-B (I1); la transferencia ≥ 5 % absoluta, que no es un contraste (I2). 8.2 es alcanzable: con TEST 512 y q pequeña el IC pareado queda por debajo de +10 pp si el efecto es nulo.
- **Cobertura de decisión:** el espacio (5,10) pp queda como "no concluyente" (8.3), consistente y honesto.

## 6. Lista de correcciones mínimas antes de congelar

1. Quitar el TODO de 8.1 y reescribir (iii) frente al control que realiza el `max(p_U, p_N)`; unificar la "Refutación declarada" con 8.2 (B1).
2. Reconciliar P0 con R04/R06 (fase `teacher-piloto`, umbral en archivo propio con hash) (B2).
3. Definir N con precisión (B3) y la acción si la admisión incumple el umbral (B4).
4. Alinear márgenes de H-B/H-C/H-D con los criterios de 8.4; decidir C−K y el estrato de 256 (I1); precisar la transferencia (I2).
5. Separar "fallo de ejecución" de "formato inválido" en 8.1(v) (I3); añadir el techo del codec (I4).
6. Resolver D1..D13 (aún "ninguna decidida"), en particular D5, D8 (umbral con la cifra real de 1,70 GiB), D9 (I5) y D13.
7. Corregir las cifras de I7 y los menores de 7.3 y 7.4; completar los huecos de `PROTOCOLO-0.2.json`.
