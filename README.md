# Qwen → NCM: laboratorio de destilación por secuencias

Laboratorio reproducible que prueba si un NCM pequeño (Next-Concept Modeling, arXiv 2610.14162; ~1,03 M de parámetros, 8 bytes de salida en 4 escalas) puede aprender, por **destilación de secuencias**, a responder aritmética entera pequeña a partir de respuestas de Qwen3.5-0.8B.

## Qué es y qué NO es

- **No** es una conversión de los pesos de Qwen a NCM.
- **No** es un modelo de chat ni de lenguaje general.
- Es una **prueba de concepto de fase 0 sin evidencia de aprendizaje de la tarea**. El detalle de arquitectura, costes y uso está en [`README-FASE0.md`](README-FASE0.md) (README original, sin duplicarlo aquí), [`INFORME.md`](INFORME.md) y [`revision/AUDITORIA-FINAL.md`](revision/AUDITORIA-FINAL.md).

## Resultados de la fase 0 (ámbito: aritmética de operandos pequeños, TEST de 64 problemas)

| Método | Aciertos TEST /64 |
|---|---:|
| Qwen3.5-0.8B (docente) | 58 |
| NCM por destilación (KD) | 1 |
| NCM + decoder conjunto (joint) | 0 |
| Control continuado, decoder fijo | 0 |
| Referencia exacta parcial (control supervisado) | 0 |
| Generador sin entrenar | 0 |

Además, en DEV el checkpoint conjunto acierta 1/32, mientras que reproduce TRAIN casi por completo (186-192/192): **memoriza TRAIN y no generaliza** (`experimentos/fase1-verificacion/`). La menor latencia del estudiante (~15 ms frente a ~657 ms por pregunta) no equivale a eficiencia a calidad equivalente.

## Limitaciones que conviene leer antes de citar nada

1. **Una sola semilla.** No hay varianza estimada; las cifras son descriptivas.
2. **El protocolo se enmendó durante el proceso**, antes de abrir TEST y sin conservar copias de las versiones previas. La cronología se conserva en los registros, pero no se certifica un protocolo único e inalterado desde el principio (ver auditoría).
3. **El control supervisado fue interrumpido** (señal -15) para limitar gasto; conserva el checkpoint de 200 pasos (entre 200 y 399 actualizaciones reales). La comparación destilación frente a supervisión exacta es **exploratoria**, no causal.
4. **La memorización es un diagnóstico posterior** (fase1-verificacion, tras ver los resultados de TEST), no una hipótesis preregistrada.
5. La separación TRAIN/DEV/TEST es procedimental: las referencias exactas existen en disco desde la preparación. No hay custodia criptográfica.
6. El tiempo de Qwen y el del estudiante no son comparables a igualdad de capacidad, runtime e hilos.
7. El fallo observado no demuestra una limitación general de NCM.

## Protocolo 0.2 (fase siguiente)

[`experimentos/fase02-protocolo/`](experimentos/fase02-protocolo/) contiene el **borrador / preregistro, NO congelado**, de la fase 0.2 (varias semillas, DEV y TEST con potencia, congelado único). Nada ahí está en vigor ni se ha ejecutado: las cifras marcadas "estimado" o "calculado" no son mediciones. Las decisiones D1-D13 están resueltas, pero el congelado ocurre después de P0 y de la revisión independiente del código.

## Estructura

- `upstream/`: código oficial HazyResearch/ncm (MIT), intacto, commit `c702742...` (ver `FUENTES.md`, `UPSTREAM-VERIFY.json`).
- `data/`: particiones TRAIN192/DEV32/TEST64 y respuestas crudas de Qwen (`teacher-*.jsonl`).
- `*.py`: pipeline (`preparar_datos.py`, `teacher.py`, `train.py`, `joint.py`, `evaluar.py`, ...).
- `*.pt`: checkpoints (~4 MB cada uno) y `tokenizer.pt`; `PREDICCIONES.json`, `RESULTADOS.json`, `RUNS.jsonl`, `MANIFEST.json`: resultados y hashes congelados.
- `revision/`, `tablero/`, `experimentos/`: auditorías, pizarra HTML y protocolos.

## Reproducción

Requisitos: Python con las versiones de `requirements-lock.txt` (torch 2.14.1+cpu), CPU sin GPU, ~7 GiB de RAM.

```sh
python -m venv .venv && .venv/bin/pip install -r requirements-lock.txt
# inferencia autónoma con un checkpoint incluido (no necesita Qwen):
.venv/bin/python inferir.py 'Compute 15 * 26. Integer only.' --model joint
```

- Regenerar las respuestas del docente exige tener Qwen3.5-0.8B (GGUF) y un motor de inferencia aparte; **no se incluyen**. `preparar_datos.py` y `train.py` se niegan a regenerar o reentrenar una ejecución congelada; para repetir el experimento use un directorio de ejecución y un protocolo nuevos.
- Verifique integridad con los hashes de `MANIFEST.json` y `CHECKPOINTS-FREEZE.json`. Nota: `MANIFEST.json` y `RUNS.jsonl` están descritos en la auditoría; el manifiesto lista `CACHE-kd.pt` y `CACHE-supervised.pt`, que **no se publican** (cachés regenerables, ~3 MB cada una), y `RUNS.jsonl` se actualizó después del manifiesto.
- Cargar `*.pt` con `torch.load` ejecuta deserialización pickle: úselos solo si confía en este repositorio.

## Advertencia: rutas absolutas

Los scripts, `*-RUN.json`, `RUNS.jsonl`, `MIGRACION.json`, `PREPARACION.json`, logs y varios informes contienen rutas absolutas `/home/carlos/...` (proyecto, entorno `/home/carlos/qwen3.5-0.8b/laboratorio-cognitivo/ronda17/ncm/.venv/` y modelo original). **Son esperadas**: apuntan al entorno del autor y se conservan sin reescribir porque los archivos de resultados están congelados y verificados por hash. Para reproducir en otra máquina hay que adaptar esas rutas en los scripts (no en los archivos congelados).

## Licencias

Código propio: MIT (`LICENSE`). `upstream/`: MIT de sus autores. Respuestas de Qwen3.5-0.8B (Apache-2.0): ver `NOTICE.md` y `AUDITORIA-PUBLICACION.md`.
