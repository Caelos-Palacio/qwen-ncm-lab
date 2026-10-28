# Atribuciones y licencias

## Código propio
Código, protocolos e informes de este repositorio (fuera de `upstream/`): MIT, (c) 2026 Carlos Palacio Naranjo. Ver `LICENSE`.

## upstream/ (HazyResearch/ncm)
`upstream/` es una copia del código oficial de Next-Concept Modeling, https://github.com/HazyResearch/ncm, commit `c70274273f489abc73832b2b98584a8483b6b203`, licencia MIT (c) 2025 hermann kumbong. Su `upstream/LICENSE` se conserva sin cambios, igual que los archivos. Este repositorio reutiliza `models.vqvae.VQVAE` y `models.next_concept.NextConceptTransformer`.

## Paper
Next-Concept Modeling, arXiv 2610.14162, https://arxiv.org/abs/2610.14162. Este repositorio no es una implementación ni una réplica de sus resultados.

## Qwen3.5-0.8B
Modelo docente: Qwen3.5-0.8B (Alibaba/Qwen), publicado en Hugging Face (https://huggingface.co/Qwen/Qwen3.5-0.8B) bajo licencia Apache-2.0 (campo de licencia de la ficha; consultada el 2026-10-28; la copia local del modelo no incluía un archivo LICENSE). La ficha no impone restricciones sobre el uso de las salidas. Este repositorio NO incluye pesos, GGUF ni tokenizador de Qwen. Sí incluye respuestas generadas por Qwen (`data/teacher-*.jsonl`, `PREDICCIONES.json`) y checkpoints de un modelo pequeño entrenado desde cero con ellas; ver `AUDITORIA-PUBLICACION.md`. Apache-2.0 es el texto de licencia aplicable a Qwen: https://www.apache.org/licenses/LICENSE-2.0
