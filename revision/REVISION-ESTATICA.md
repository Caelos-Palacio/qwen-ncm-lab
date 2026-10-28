# Revisión estática previa al entrenamiento

20 de octubre de 2026. Inspección de `modelo.py`, `train.py`, `teacher.py`, `preparar_datos.py`, `PROTOCOLO.json` y clases oficiales importadas. No se ejecutó inferencia ni entrenamiento durante esta revisión.

## Mecanismos correctos observados

- **Arquitectura:** se importan `VQVAE` y `NextConceptTransformer` oficiales; no se reemplazan por un MLP. RVQ tiene niveles `[1,2,4,8]`; decoder y encoder contextuales de un bloque. El generador compartido tiene cuatro bloques, cuatro cabezas y ancho 128.
- **Gradiente del primer nivel:** `training_inputs` no está decorada con `no_grad`. La reconstrucción condicionante se prepara congelada; `gen.build_l0_query_input` y su concatenación quedan en el grafo del generador. La cabeza del primer nivel se entrena junto con las demás.
- **Entrenamiento del decoder:** el tokenizer se entrena con `vq(batch)` y CE sobre logits, no con su método `decode` decorado con `no_grad`. El estimador directo y EMA quedan dentro de las clases oficiales.
- **Congelación:** tras seleccionar tokenizer por DEV se carga su checkpoint, se pone en `eval` y se desactiva gradiente de todos sus parámetros. La generación usa ese tokenizer congelado.
- **Sin respuesta en generación libre:** `generate(vq, gen, prefix)` llama `gen.generate(None, prefix, ...)`, luego decodifica sus códigos producidos. El TEST no requiere códigos de respuesta ni encoder de respuesta. Los códigos verdaderos aparecen solo en las pérdidas y diagnóstico con historial verdadero.
- **Conservación del maestro:** la plantilla del maestro cierra explícitamente `think`; el parseo entero requiere coincidencia de toda la respuesta. Los errores cortos del maestro no se reemplazan con respuestas aritméticas correctas.
- **Selección:** la selección del generador usa exactitud de generación libre DEV; TEST del maestro exige primero un archivo de congelación de checkpoints. Es un control procedimental, no aislamiento criptográfico.

## Comprobación ligera de datos

Lectura JSON con biblioteca estándar: TRAIN 192 (64 por operación), DEV 32 (12 suma, 10 resta, 10 multiplicación), TEST 64 (22/21/21). Intersección de IDs y prompts exactos entre cada par de particiones: **0**. Suma y multiplicación excluyen espejos conmutativos por construcción. Resta conserva pares dirigidos. Máximo prompt: TRAIN/DEV 30 bytes, TEST 44; máximo objetivo exacto: 3 bytes. Todos caben en los límites 64/8.

## Riesgos comunicados antes del entrenamiento

1. `train.py` construye `xd` con todos los `teacher_target` DEV sin filtrar `kd_usable`. Si un resultado DEV excede 8 bytes, `encode` falla. Debe manejarse explícitamente y registrarse el denominador; no truncar ni sustituir silenciosamente.
2. `kd_usable` admite respuestas no enteras cortas, según el protocolo. No es un error accidental del parseo, pero exige recuento de enteros válidos, correctos, no enteros y descartados. Si hay muchos, la calidad del corpus del maestro será parte del diagnóstico.
3. Si se descartan ejemplos KD, el control supervisado actual usa más IDs TRAIN que KD. Para una comparación del efecto de los objetivos, usar los mismos IDs o declarar que también cambia el corpus. No alterar el conjunto TEST por la respuesta del maestro.
4. La CE del tokenizer incluye PAD: es una convención de entrenamiento explícita, pero puede favorecer relleno con salidas de ocho posiciones y números de hasta tres bytes. La selección usa EM completa, y ya se registra exactitud sin PAD. El informe debe conservar ambas y añadir diagnósticos de colapso por nivel en la evaluación.

Esta revisión no exige nuevos experimentos previos ni altera el presupuesto. Las correcciones de robustez y sus hashes deben quedar reflejados antes del FIT.

## Hashes de la versión inspeccionada

| Archivo | SHA256 |
|---|---|
| modelo.py | c5755d5aa5da5ae905387d3eca454bb6bfec3ef1f6a94fd27e2d006474f4e614 |
| train.py | 395501ea13c169e26241bb4303ab3626828f71a4a6f2e57d2a854327b8f20352 |
| teacher.py | 7ea28eb7b3e37b657455d1f3b1c466786dd11500fca62d2327331216bec1c87c |
| preparar_datos.py | 71b0aa3b65ba9e568df5cf2e3a8b1673f45b85d61a546b55a609a42e047b7ee0 |
| PROTOCOLO.json | a80b2af705a19c3e09a257b88f5c8ebd4da6e303b1fde0ef6bf58be515f54cac |

Estado: **mecanismos centrales correctos por inspección; robustez DEV y comparabilidad de descartes pendientes de respuesta del implementador; evaluación final todavía pendiente**.
