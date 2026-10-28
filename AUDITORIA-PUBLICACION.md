# Auditoría previa a la publicación (2026-10-28)

Copia de trabajo: `/home/carlos/qwen-ncm-lab-publico` (origen `/home/carlos/qwen-ncm-lab`, no modificado).

## Exclusiones
| Excluido | Motivo |
|---|---|
| `.symbiaxis/` (860 KB) | Telemetría/ledger de la sesión del agente de desarrollo; contiene rutas y trazas personales, no es parte del experimento. |
| `__pycache__/` | Artefactos de compilación. |
| `CACHE-kd.pt`, `CACHE-supervised.pt` (~3,1 MB c/u) | Cachés regenerables de códigos/embeddings; reducen superficie pickle. Siguen listados en `MANIFEST.json` (aviso en README). |
| `upstream/.git` | Se publica como archivos planos (commit documentado en FUENTES.md), no como repositorio anidado. |
| Pesos/GGUF de Qwen | Nunca estuvieron en esta carpeta. |

## Secretos
Grep de patrones (api_key, secret, passw, ghp_/gho_, sk-, AKIA, claves privadas, hf_, bearer) sobre todo el árbol incluido (y upstream): **sin coincidencias**. Las apariciones de "token" son tokens de modelo (tokenizer). Las únicas direcciones con "@" son el operador matricial de `joint.py`; no hay correos en los archivos publicados.

## Datos personales
Nombre de usuario del sistema (`carlos`) en rutas absolutas. Titular de la licencia: Carlos Palacio Naranjo (autorizado por el usuario). Sin correos, teléfonos ni credenciales.

## Rutas absolutas `/home/carlos` (archivos publicados fuera de upstream; recuento de líneas)
- teacher.py:2
- README-FASE0.md:3
- informe.py:1
- evaluacion-RUN.json:3
- demo-train-RUN.json:3
- demo-RUN.json:3
- RESUMEN-COSTE.json:21
- fit.log:1
- teacher-train-cost.json:2
- AGENTS.md:1
- PREPARACION.json:2
- MANIFEST.json:1
- cerrar_fase.py:1
- teacher-test-cost.json:2
- joint-fit-RUN.json:3
- revision/PROPUESTA-PROTOCOLO.md:1
- teacher-test-RUN.json:3
- README.md:1
- fit-RUN.json:3
- teacher-train-dev-RUN.json:3
- MIGRACION.json:3
- RUNS.jsonl:7
- PROTOCOLO.json:1
- experimentos/fase02-protocolo/PROTOCOLO-0.2.md:1
- PARADA-PLANIFICADA.json:2
- revision/AUDITORIA-FINAL.md:1
- experimentos/fase1-verificacion/intento1-error.log:5
- experimentos/fase1-verificacion/ejecutar.sh:2
- experimentos/fase1-verificacion/INFORME.md:1
- teacher-engine.log:2

Se conservan sin reescribir (resultados congelados/hasheados); documentado en README. `upstream/` no contiene rutas del autor.

## Tamaño
Total publicado ~24 MB (origen 32 MB). Checkpoints: continued.pt 4,28 MB, joint.pt 4,27 MB, kd.pt 4,27 MB, supervised.pt 4,28 MB, untrained.pt 4,28 MB, tokenizer.pt 0,88 MB. Ninguno cerca del límite de GitHub (100 MB).

## Licencias
- Código propio: MIT, Carlos Palacio Naranjo, 2026.
- `upstream/`: MIT (c) 2025 hermann kumbong, LICENSE conservado.
- Qwen3.5-0.8B: la ficha oficial en Hugging Face declara **Apache-2.0** (consulta web 2026-10-28; metadatos locales del GGUF de ggml-org también `license:apache-2.0`). No hay copia local de un LICENSE de Qwen. Apache-2.0 permite redistribuir; no declara derechos sobre las salidas ni las restringe. Se **publican** `data/teacher-*.jsonl` y `PREDICCIONES.json` (salidas de Qwen, aritmética corta) y los checkpoints (modelo de 1 M de parámetros entrenado desde cero con esas salidas, sin pesos de Qwen). Se incluye atribución en `NOTICE.md`. Duda residual baja: no se verificó un LICENSE de Qwen concreto en archivo; si se quisiera máxima cautela, retirar teacher-*.jsonl y *.pt.

## Otros riesgos
Los `.pt` son pickles de PyTorch: advertencia en README. Sin otros hallazgos.
