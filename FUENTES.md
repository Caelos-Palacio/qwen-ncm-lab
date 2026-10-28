# Fuentes y adaptación

Se leyó el paper [Next-Concept Modeling](https://arxiv.org/html/2610.14162v1) y el [repositorio oficial](https://github.com/HazyResearch/ncm), commit `c70274273f489abc73832b2b98584a8483b6b203`, licencia MIT. El código oficial local permanece intacto.

Se reutilizan `models.vqvae.VQVAE` y `models.next_concept.NextConceptTransformer`. El experimento reduce vocabulario de entrada a 257 valores (bytes y PAD), salida a 8 bytes, dimensión y número de capas; conserva cuantización residual multiescala, predicción simultánea por escala y decodificación paralela. El entrenador local implementa las dos fases porque el repositorio publicado contiene evaluación e inferencia.

La destilación es por secuencias: Qwen produce respuestas aritméticas que sirven como textos objetivo. No se copian sus pesos ni sus capacidades generales. Los códigos se aprenden; no son conceptos humanos anotados.

La versión mini usa corrupción de códigos del 5% y pérdida media por escala. La comparación numérica publicada con modelos de difusión no se traslada a esta CPU ni a este experimento.
