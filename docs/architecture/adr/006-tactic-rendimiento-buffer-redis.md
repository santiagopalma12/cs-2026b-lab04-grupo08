# ADR-006: Buffer Asíncrono en Redis con Fast ACK HTTP 202 para Ingesta Masiva (QA-01)

- **Estado:** Aceptado
- **Fecha:** 2026-10-31
- **Decisores:** Santiago Palma (`santiagopalma12`), Dario Rafael Cornejo Hurtado (`darich1010`)
- **Iteración ADD:** Iteración 1 (Rendimiento)
- **Escenario Asociado:** QA-01 (H, H)

---

## 1. Contexto y Problema

Durante el **Simulacro Nacional** (o un sismo real de gran magnitud en Arequipa), el sistema SismoReporta AQP debe procesar una avalancha de **20 000 reportes ciudadanos en el lapso de 1 hora**. Esto equivale a una tasa media de $5.56\text{ req/s}$ con ráfagas pico estimadas de **28 req/s**.

El escenario de calidad prioritario **QA-01 (H, H)** exige:
> *"Cuando 20 000 ciudadanos envían reportes simultáneos durante el simulacro bajo una red móvil congestionada, el sistema los recibe y responde con una latencia p95 \le 1.5\text{ s} (1500 ms), evitando saturación de conexiones HTTP y timeouts 504."*

En la arquitectura previa (Lab 07), el procesamiento síncrono realizaba validación espacial en PostGIS (`ST_Within`), compresión de imágenes y escritura en disco dentro del ciclo de vida de la petición HTTP. Con 4 workers web en el VPS (2 vCPU, 4 GB RAM), la simulación demostró que a 18 req/s la latencia $p95$ colapsaba a **97.5 s** y a 28 req/s superaba los **213 s** con colas infinitas.

---

## 2. Alternativas Consideradas

1. **Escalado Horizontal Agresivo a 8 Workers Web [Puntaje: 2.4 / 5.0]:**
   * Aumentar el número de procesos Gunicorn/FastAPI de 4 a 8 sin alterar la sincronía de la ingesta.
   * *Resultado de simulación:* A 18 req/s, $p95 = 1798.8\text{ ms}$ (viola el presupuesto de 1500 ms); a 28 req/s, la cola colapsa a $50.0\text{ s}$. Además, duplica el consumo de RAM en el VPS excediendo el presupuesto mensual (R-03).
2. **Reingeniería a Microservicios con Kubernetes y Apache Kafka (Sugerencia inicial de la IA) [Puntaje: 1.8 / 5.0]:**
   * Desacoplar en microservicios independientes orquestados con K8s y un clúster Kafka de 3 nodos.
   * *Refutación técnica:* Requiere un clúster de al menos 3 nodos (\$120 USD/mes), violando la restricción presupuestaria R-03 (\$15 USD/mes) y el plazo de entrega de 1 mes (R-01) para un equipo de 2 desarrolladores. Añade sobrecarga operativa desproporcionada para una tasa pico de 28 req/s.
3. **Táctica de Buffer Asíncrono en Redis con Fast ACK HTTP 202 [Puntaje: 4.9 / 5.0] (Seleccionada):**
   * El endpoint `POST /api/v1/reportes` valida únicamente la sintaxis Pydantic en memoria y ejecuta `redis.lpush("cola:ingesta", payload)`. Responde inmediatamente al cliente con `HTTP 202 Accepted` y un `reporte_id` (UUID).
   * Un pool de workers Celery en segundo plano drena la cola, ejecuta la validación espacial PostGIS y persiste en base de datos.

---

## 3. Decisión

**Adoptamos la Táctica de Buffer Asíncrono en Redis con Fast ACK HTTP 202.**
- El controlador FastAPI libera la conexión HTTP del ciudadano en tiempo constante ($< 15\text{ ms}$).
- Se mantiene el Monolito Modular en Python sin migrar a microservicios ni Kubernetes.
- Se implementa un índice espacial **GiST** en la columna de coordenadas en PostgreSQL para asegurar que las consultas espaciales de los workers tarden $< 5\text{ ms}$.

---

## 4. Consecuencias y Evidencia

### Consecuencias Positivas:
- **Cumplimiento estricto de QA-01:** La simulación M/G/c (`fitness/rendimiento.py`) demostró que con el buffer en Redis, a 28 req/s pico:
  - $p95 = \mathbf{16.4\text{ ms}}$ (frente al límite de $1500\text{ ms}$, reduciendo la latencia en un 99.99%).
  - Tasa de utilización del buffer $\rho = \mathbf{0.07}$ (el buffer opera al 7% de capacidad, absorbiendo ráfagas sin esfuerzo).
- **Protección de la batería y ancho de banda móvil:** Al liberar el socket en 16 ms, los smartphones no sufren timeouts bajo redes 3G/4G congestionadas.
- **Cero incremento de costos:** Opera dentro del VPS existente de \$15 USD/mes.

### Consecuencias Negativas y Mitigación:
- **Consistencia Eventual (Trade-off T1):** Los reportes tardan entre 1 y 3 segundos en aparecer en el mapa del COE mientras Celery procesa la cola.
  * *Mitigación:* Plenamente aceptable en emergencias; el panel del COE realiza sondeo WebSocket cada 2 segundos.
- **Riesgo R1 (Memoria Redis):** Si Celery colapsa, 20 000 reportes en memoria ocuparían ~10 MB. Se configuró Redis con `maxmemory 512mb` y persistencia AOF (`appendonly yes`).
