# Qwen → Next-Concept Modeling

Proyecto independiente: `/home/carlos/qwen-ncm-lab/`.

La fase 0 destila secuencias de respuestas de Qwen3.5-0.8B a un NCM pequeño para aritmética. Reutiliza las clases oficiales de HazyResearch: VQ-VAE residual multiescala y Transformer que predice un nivel completo cada vez. El prototipo genera hasta 8 bytes en 4 escalas. No es un modelo de conversación ni una conversión directa de los pesos de Qwen.

El código oficial está en `upstream/`, fijado al commit de `FUENTES.md`, con licencia MIT. Los pesos originales de Qwen permanecen separados y congelados. El entorno CPU está en `/home/carlos/qwen3.5-0.8b/laboratorio-cognitivo/ronda17/ncm/.venv/`; se conserva allí para mantener sus rutas internas.

`PROTOCOLO.json` y `ENTRADA-FREEZE.json` fijan el experimento antes de obtener los datos del docente. `teacher.py` conserva respuestas crudas, errores y tiempos. `train.py` entrena el tokenizador, lo congela y entrena el generador con respuestas del docente. Un control usa referencias aritméticas exactas con la misma arquitectura y los mismos IDs admitidos. `evaluar.py` compara generación libre, controles, uso de códigos y costes; la reconstrucción del tokenizador se informa por separado.

`ejecutar_fase.py` registra pared, CPU, RSS, swap y código de salida en `RUNS.jsonl`. Las mediciones de inferencia excluyen la carga y se distinguen del coste de entrenar y consultar al docente.

Ejemplo, cuando existan checkpoints:

```sh
/home/carlos/qwen3.5-0.8b/laboratorio-cognitivo/ronda17/ncm/.venv/bin/python /home/carlos/qwen-ncm-lab/inferir.py 'Compute 15 * 26. Integer only.' --model joint
```

La fase 1 propuesta será texto real de corpus con licencia, documentos disjuntos y longitudes mayores. Se decidirá después de comprobar reconstrucción, colapso de códigos, generación sin respuesta y coste de este prototipo. La conversión directa de pesos queda como línea de investigación separada.

La fase 0.1 añade entrenamiento conjunto del generador NCM y el decoder Transformer que traduce los códigos a texto. Usa cuatro niveles predichos propios y straight-through para conservar un forward discreto y permitir gradiente desde el texto; encoder y codebooks permanecen fijos. Un control continúa el generador desde el mismo checkpoint con decoder fijo durante el mismo número de actualizaciones. Los tiempos se comparan por separado porque el cómputo por actualización difiere.

Los primeros 50 pasos constituyen un scout incluido en el presupuesto, y las paradas por DEV reducen trabajo que no mejora. Códigos y embeddings congelados se cachean; las consultas aprendibles siguen recibiendo gradiente. Las capturas del docente se reutilizan por clave del modelo, motor, prompt completo y configuración. No se modifica el modelo Qwen original.

## Estado de esta ejecución

El prototipo y la inferencia autónoma están guardados. El codec congelado de KD por etapas reconstruyó las 64 respuestas TEST exactamente; no se midió la reconstrucción del decoder después de coadaptarlo; la generación libre obtuvo 1/64 con KD por etapas y 0/64 con entrenamiento conjunto, frente a 58/64 de Qwen. El aprendizaje de la tarea no se ha demostrado: las respuestas de TRAIN se memorizan, pero no se transfieren a estos problemas nuevos. Este resultado no identifica un defecto general de NCM.

Consulta `INFORME.md`, `RESULTADOS.json`, `RESUMEN-COSTE.json` y `DEMO-USABILIDAD.json`. El programa de inferencia no necesita Qwen ni calcula la respuesta con reglas aritméticas. El ejemplo TRAIN `15 * 26` produjo `390`; una pregunta adicional `7 + 9` produjo `18`, y se conserva ese error.

`preparar_datos.py` y `train.py` rechazan regenerar datos o reentrenar una ejecución congelada. Los otros programas se ejecutan explícitamente; importar sus módulos no arranca el pipeline. No vuelvas a ejecutar el cierre sobre estas predicciones congeladas: para un nuevo experimento crea un directorio de ejecución y un protocolo nuevos.
