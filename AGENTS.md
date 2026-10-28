# Qwen → NCM: laboratorio separado

Trabaja en español. Mantén las fuentes oficiales de `upstream/` intactas y fijadas al commit documentado. No alteres el GGUF original de Qwen ni los resultados congelados del laboratorio cognitivo.

Este proyecto prueba destilación por secuencias a NCM, no afirma conversión directa de pesos. La fase 0 es aritmética pequeña; cualquier afirmación debe incluir su ámbito y medición.

Hardware: CPU i5-13420H, 7.3 GiB RAM, sin GPU. Reserva un solo trabajo pesado a la vez; conserva la separación entre perfilado y entrenamiento.

Congela protocolo y particiones antes del entrenamiento. Selecciona únicamente con TRAIN/DEV; TEST se abre tras congelar checkpoints. Preserva datos crudos, errores y hashes. Mide pared, CPU, memoria, estado de swap, pasos, parámetros y calidad. No confundir reconstrucción con generación desde el prompt.

Entorno aislado existente: `/home/carlos/qwen3.5-0.8b/laboratorio-cognitivo/ronda17/ncm/.venv/bin/python`. No instalar paquetes en el entorno del modelo original.
