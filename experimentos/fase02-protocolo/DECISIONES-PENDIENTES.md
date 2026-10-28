# Fase 0.2: decisiones del usuario

Estado: D1 a D13 RESUELTAS el 2026-10-28 (aceptada por el usuario en chat: se adoptó la recomendación de cada una). Resolverlas no congela el protocolo: `PROTOCOLO-0.2.md` sigue siendo BORRADOR NO CONGELADO y el congelado único ocurre después de P0 y de la revisión independiente del código (ver `PROTOCOLO-0.2.md` secciones 10, 14 y 15). Las opciones y cifras de abajo se conservan tal como estaban para trazabilidad. Actualizado tras `REVISION-PROTOCOLO-0.2.md`: cifras corregidas y recomendaciones ajustadas. Cifras: (estimado) o (calculado) salvo indicación.

**D1. Diseño factorial (peldaños x semillas).**
- A. Escalera 192/768/3072 con 1 semilla + 4 semillas más solo en 3072: 7 ejecuciones, ~3,2-3,6 h totales (estimado, incluye ~5 min de añadidos de la revisión). Curva exploratoria sin inferencia; inferencia con 5 semillas en 3072.
- B. Cruce completo 3 x 5: 15 ejecuciones, +2,3-2,8 h sobre A. Permite inferir en cada peldaño, pero la pregunta principal no lo requiere.
- C. Solo 3072 x 5 semillas (sin curva): 5 ejecuciones, ~2,5-2,8 h. Pierde la curva de escala.
- Recomendación: A.
- **RESUELTA: A** (2026-10-28, aceptada por el usuario en chat).

**D2. Dominio de operandos.**
- A. 0..60: única opción con DEV 256 + TEST 512 + escalera sin repetir pares; rompe comparabilidad con fase 0 y deja los tiempos como estimados.
- B. Mantener 0..30 con partición pequeña: escalera máxima ~768 y DEV/TEST menores (en `+` y `*` solo hay 496 pares por operación, ya con 96 excluidos de fase 0 y 288 usados); menos potencia.
- Recomendación: A, con ancla solo informativa y primera ejecución como re-medición de coste.
- **RESUELTA: A, con ancla solo informativa y primera ejecución como re-medición de coste** (2026-10-28, aceptada por el usuario en chat).

**D3. Peldaño 1536 y contraste "3072 solo con T1".**
- A. Extraer 1536 anidado (sin coste de docente) pero no entrenarlo; sin contraste T1.
- B. Entrenar 1536 (+1 ejecución, ~18-21 min).
- C. Añadir contraste T1-solo: 3072 consultas nuevas del docente (~2120 s) y más ejecuciones.
- Recomendación: A.
- **RESUELTA: A** (2026-10-28, aceptada por el usuario en chat).

**D4. Peldaño decisivo.**
- A. Fijo a priori en 3072.
- B. Elegido tras la etapa A por regla sobre DEV (p. ej. el menor peldaño que alcance 90 % del máximo DEV): introduce adaptividad y un segundo punto de decisión.
- Recomendación: A.
- **RESUELTA: A** (2026-10-28, aceptada por el usuario en chat).

**D5. Qué mide la selección en DEV.**
- A. Los 256 ítems de DEV (vistas + U0).
- B. Solo los 128 de plantillas vistas (como pedía 01 al excluir U0 de la selección).
- Recomendación: A (más resolución; U0 no está en TEST, que usa U1/U2); se informan ambos estratos.
- **RESUELTA: A (más resolución; U0 no está en TEST, que usa U1/U2); se informan ambos estratos** (2026-10-28, aceptada por el usuario en chat).

**D6. Piloto del docente y regla del umbral de admisión.**
- A. 168 consultas (56 por operación, 7 plantillas), ~2 min; regla: L(Wilson) >= 90 % mantiene 90 %; a >= 85 % con L < 90 % baja el umbral, nunca bajo 80 %; a < 85 % o alguna operación < 70 % es NO-GO.
- B. Piloto mayor (336, ~4 min): mejor cota por operación.
- C. Sin piloto: mantener 90 % sin dato (en 0..30 la admisión fue 99,6 %, medido).
- Recomendación: A. Hay que decidir también qué hacer en NO-GO (reducir rango, cambiar prompt del docente o aceptar).
- **RESUELTA: A** (2026-10-28, aceptada por el usuario en chat). Queda abierta, sin decidir, la acción en caso de NO-GO (reducir rango, cambiar prompt del docente o aceptar): se decide solo si P0 da NO-GO.

**D7. Umbrales +5 / +10 pp.**
- A. Mantener, presentados como convenciones: +5 = piso de no aprendizaje (~3,5 pp sobre el Wilson del control con TEST 512: 6,6 % frente a 3,1 %) y +10 = 1,4-2x la diferencia mínima detectable (4,7-7,4 pp con Holm 4 y 5,0-7,9 con Holm 8, q de 0,10 a 0,25, no medida).
- B. Derivar los umbrales de la diferencia mínima detectable tras medir q en DEV (no es posible antes del congelado salvo en el piloto).
- C. Umbrales por orden: +6 / +12.
- Recomendación: A.
- **RESUELTA: A** (2026-10-28, aceptada por el usuario en chat).

**D8. Límites de memoria y swap.**
- A. Negarse a iniciar con `MemAvailable` < 1,5 GiB; ejecución inválida con RSS de árbol > 2,0 GiB o swap libre < 2 GiB al inicio. Cifras medidas: `MemAvailable` 1,70 GiB antes del docente (mínimo 1,64 GiB en todas las fases), RSS del docente 925 MiB, entrenamiento 0,58 GiB, swap libre 10,6-10,8 GiB. El umbral deja solo ~0,14 GiB de margen sobre el mínimo observado.
- B. Umbral de 2,5 GiB: habría impedido las corridas de fase 0 (1,64-1,70 GiB disponibles, medido); obliga a cerrar otras aplicaciones.
- C. Umbral 1,5 GiB pero cerrando antes las demás aplicaciones y comprobando `MemAvailable` al inicio de cada etapa (puede subir el margen real); o bajarlo (p. ej. 1,3 GiB) a costa de menos margen frente al RSS del docente.
- Recomendación: A (o C), con compromiso de cerrar aplicaciones durante las ~3,6 h; decides tú si es viable y si el umbral debe cambiar.
- **RESUELTA: A (o C), con compromiso de cerrar aplicaciones durante las ~3,6 h** (2026-10-28, aceptada por el usuario en chat). En ambas variantes el umbral es el mismo (1,5 GiB); sin cambio del umbral.

**D9. Puerta de coste tras la primera ejecución.**
- A. Perfilado corto previo P-COSTE (~50 pasos con 3072 ejemplos sintéticos, ~2 min, antes del congelado, separado del entrenamiento como pide `AGENTS.md`); parar la cola si proyecta una pared > 1,9 ks (1,5x la cota alta) o un coste por paso desviado > 20 %, y esperar tu decisión. Tras A-192 y A-3072 solo se registra la desviación.
- B. Sin perfilado: la ejecución A-192 hace de medición y de entrenamiento (excepción a la separación de `AGENTS.md`); el supuesto de la caché RVQ a 3072 se vería tarde, en A-3072.
- C. No parar; solo registrar.
- Recomendación: A.
- **RESUELTA: A** (2026-10-28, aceptada por el usuario en chat).

**D10. Etapa B sin puerta de futilidad.**
- A. Ejecutar siempre las 4 semillas restantes (~70-85 min), aunque la etapa A muestre DEV nulo.
- B. Detener si en A-3072 todas las condiciones quedan en DEV <= U + 2 pp: ahorra ~75 min, pero introduce una decisión de parada y el negativo tendría 1 semilla.
- Recomendación: A (coherente con el borrador 02: sin análisis intermedio ni futilidad).
- **RESUELTA: A** (2026-10-28, aceptada por el usuario en chat).

**D11. Texto de las plantillas y del piloto.** Confirmar T1..T4, U0, U1, U2 tal cual están en `PROTOCOLO-0.2.md` 3.3, o cambiarlas ahora; tras el congelado no se tocan. U1/U2 no se discuten fuera del archivo congelado.
- Recomendación (implícita): confirmarlas tal cual.
- **RESUELTA: textos de T1..T4, U0, U1 y U2 confirmados tal cual figuran en `PROTOCOLO-0.2.md` 3.3** (2026-10-28, aceptada por el usuario en chat).

**D12. Ancla con fase 0.**
- A. Re-evaluar sobre el TEST legacy de 64 solo como comprobación de la tubería, sin inferencia.
- B. No hacerla.
- Recomendación: A (coste de docente 0, ~1 min).
- **RESUELTA: A** (2026-10-28, aceptada por el usuario en chat).

**D13. Alcance de la implementación y orden de aprobación.** Quién escribe y revisa el código nuevo (`preparar_datos_02.py`, `verificar_rigor.py`, ejecutor, evaluador) y si apruebas el congelado único antes de P0 o después: este protocolo lo coloca después de P0 y antes de toda consulta de TRAIN/DEV/TEST. Recomendación: revisión independiente del código (incluido el script de N) frente a R01..R27 antes de ejecutar P0 o el perfilado; el protocolo la recoge como paso 0 de la sección 10 por defecto.
- **RESUELTA: revisión independiente del código (incluido el script de N) frente a R01..R27 antes de ejecutar P0 o el perfilado; congelado único después de P0 y antes de toda consulta de TRAIN/DEV/TEST** (2026-10-28, aceptada por el usuario en chat). El texto de la recomendación no nombra quién escribe y quién revisa el código: eso queda pendiente de asignar (distinto el revisor del autor).
