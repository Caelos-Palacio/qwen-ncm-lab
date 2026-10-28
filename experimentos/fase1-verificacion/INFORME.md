# Verificación del cuello de botella NCM

20 de octubre de 2026. Diagnóstico exploratorio de checkpoints existentes; no se entrenó ni se abrió de nuevo TEST. El protocolo quedó escrito antes de ejecutar. Los históricos y pesos permanecen intactos.

El entrenamiento conjunto sí aprende a reproducir las respuestas de TRAIN: 192/192, incluidos los seis errores del docente. En DEV solo acierta 1/32 problemas. La evidencia indica memorización y generalización insuficiente; también hay propagación de errores entre escalas. No demuestra que NCM sea incapaz de aprender la tarea.

| Checkpoint | TRAIN acierto aritmético libre | TRAIN texto docente libre | DEV acierto aritmético libre | DEV texto docente libre | DEV texto docente con niveles previos verdaderos |
|---|---:|---:|---:|---:|---:|
| KD | 183/192 | 189/192 | 1/32 | 2/32 | 10/31 |
| Conjunto | 186/192 | 192/192 | 1/32 | 2/32 | 9/31 |
| Continuado, decoder fijo | 186/192 | 192/192 | 1/32 | 2/32 | 9/31 |
| Supervisado parcial | 33/192 | 32/192 | 1/32 | 1/32 | 12/31 |
| Sin entrenar | 0/192 | 0/192 | 0/32 | 0/32 | 0/31 |

La última columna es un diagnóstico asistido por objetivos y no generación autónoma. Excluye la respuesta docente DEV inválida de diez bytes. Las otras columnas conservan las 32 preguntas. El supervisado tuvo un presupuesto histórico menor y aquí el forcing se evalúa contra códigos del docente, por consistencia diagnóstica; no permite comparar causalmente sus objetivos de entrenamiento.

El codec reconstruye 192/192 objetivos TRAIN y 31/31 objetivos DEV admitidos en los cinco checkpoints. También se verificó por primera vez esta reconstrucción DEV después de coadaptar el decoder conjunto: 31/31. La reconstrucción y la generación son mediciones separadas.

En generación libre conjunta, los bytes de respuesta correctos, excluido PAD, son 417/424 en TRAIN y 21/67 en DEV; parsea como entero 192/192 y 31/32 respectivamente, con UTF-8 válido en todos. Las cifras completas de cada condición están en `RESULTADOS.json`.

## Qué cambia al retirar los códigos verdaderos

Exactitud de códigos DEV del checkpoint conjunto, 31 objetivos admitidos:

| Longitud de nivel | Historial verdadero | Historial generado |
|---|---:|---:|
| 1 | 61,3% | 61,3% |
| 2 | 66,1% | 66,1% |
| 4 | 76,6% | 71,0% |
| 8 | 81,5% | 68,5% |

La degradación final bajo historial propio mide exposición a errores anteriores. El primer nivel ya falla sin tener ningún nivel anterior del que depender; por ello corregir solo la exposición no resuelve toda la brecha TRAIN/DEV. Forcing tampoco alcanza reconstrucción perfecta. No se identificó un defecto de implementación en las rutas verificadas.

## Fidelidad y controles

- Todos los hashes del freeze histórico coinciden antes y después; no se modifica el manifiesto.
- El forward discreto de `joint.rollout` coincide con los códigos y bytes de la inferencia oficial para el primer batch de cada split y checkpoint, 160 ejemplos en total.
- El primer ejemplo de cada split/checkpoint da los mismos bytes generado solo o en batch16: diez comprobaciones.
- En cuatro ejemplos TRAIN, gradiente de pérdida de texto únicamente: generador 0,012203; decoder 0,016799; encoder y codebooks cero. Confirma aprendizaje conjunto de ambas redes en esta ruta.
- La generación libre recibe prompt y pesos; los objetivos se usan después para puntuar. El forcing se calcula por una ruta separada.

## Coste y decisión

La ejecución completa válida consumió 12,12 s de pared y 24,14 s de CPU; RSS máxima 363,77 MiB, swap propia máxima muestreada 0 KiB en 61 muestras cada 0,2 s; dos hilos, batch16. Cinco condiciones por 224 prompts: 1.120 generaciones, 71.680 posiciones byte de prompt con PAD y 8.960 posiciones byte de salida. Las comprobaciones y rutas de forcing/reconstrucción añaden cómputo incluido en esos tiempos; las posiciones reportadas corresponden solo a generación principal, no a todos los forwards internos. No son tokens Qwen. Parámetros por condición: codec 197.889 y generador 835.968, según el JSON. Cero pasos de optimización, cero nuevas consultas Qwen. Carga y evaluación incluidas; no es un benchmark de latencia estable.

Un primer intento del diagnóstico falló al intentar codificar la respuesta DEV inválida de diez bytes; se preserva `intento1-error.log`. Se corrigió únicamente este script: métricas libres usan referencia aritmética exacta en todas las filas y forcing/reconstrucción solo objetivos admitidos. No fue un error detectado en el entrenamiento histórico. Ese arranque fallido no tiene medición integral de recursos y no está incluido en los 12,12 s de la ejecución válida.

Se detiene aquí: entrenar un nuevo sanity de memorización aportaría poco cuando conjunto y continuado ya reproducen las 192 respuestas TRAIN sin asistencia. No se ejecuta un grid ni se vuelve a evaluar TEST. La siguiente hipótesis a contrastar, en un experimento posterior, es si una tarea de copia/patrón con referencias exactas y un vocabulario controlado mejora el primer nivel y la generalización con un generador compacto, antes de escalar corpus o entrenar encoder/codebooks. La igualdad observada de conjunto y decoder fijo en DEV no acredita sinergia útil en este dominio.

## Reproducción

Desde `/home/carlos/qwen-ncm-lab/`, ejecutar `sh experimentos/fase1-verificacion/ejecutar.sh`. El wrapper obtiene un lock compartido no bloqueante; si está ocupado sale con código75 y no inicia cómputo. Timeout600 s. El script solo escribe en esta carpeta. Se reutiliza el entorno existente y las clases upstream intactas.

La revisión manual comprobó denominadores, separación de rutas, rechazo de objetivos inválidos, congelación por hashes, ausencia de TEST y límites de presupuesto. La skill `code-simplifier` no está disponible en las rutas de skills activas; no se instaló ni se sustituyó por instrucciones externas.
