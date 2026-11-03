# Iteración 1 de ADD 3.0: Eficiencia de Desempeño en Ingesta Masiva (QA-01)

**Sistema:** SismoReporta AQP  
**Asignatura:** Construcción de Software (2026-B)  
**Grupo:** Grupo 08 — Santiago Palma (`santiagopalma12`) y Dario Rafael Cornejo Hurtado (`darich1010`)  
**Entregable:** E2 (Iteración 1 de ADD con Evidencia Cuantitativa)

---

## 1. Paso 1 de ADD: Revisar las Entradas

| Insumo | Origen | Qué aporta a esta iteración |
| :--- | :--- | :--- |
| **Escenario de Crecimiento** | Tabla 11 Guía Lab 08 | **Simulacro nacional con 20,000 reportes en 1 hora** con red móvil congestionada. Demanda una tasa de procesamiento de hasta 28 req/s en ráfagas de reconexión. |
| **Escenario de Calidad Objetivo** | Árbol de Utilidad (`QA-01`) | Calificado como **(H, H)**: $p95 \le 1.5\text{ s}$ en la entrega del acuse de recibo HTTP 202 Accepted al cliente; tasa de errores $5xx < 0.05\%$. |
| **Drivers y Restricciones** | `drivers.md` (Lab 04) | **R-01:** Plazo estricto de entrega del MVP en producción en 1 mes.<br>**R-02:** Equipo de desarrollo de 2 ingenieros.<br>**R-03:** Presupuesto restringido a un único servidor VPS en la nube (\$10–\$20 USD/mes). |
| **Estilo Arquitectónico Base** | ADR-001 (Lab 04) | Monolito Modular Asíncrono: se mantiene como decisión basal y no se fractura en microservicios salvo que la evidencia lo justifique numéricamente. |
| **Modelo Estructural C4** | `workspace.dsl` (Lab 06) | Contenedor `API Backend Monolítico` y almacén de datos `Base de Datos Geoespacial`. |

---

## 2. Paso 2 de ADD: Establecer el Objetivo de la Iteración

- **Objetivo Arquitectónico:** Garantizar que la plataforma absorba el pico masivo de 20,000 reportes transmitidos durante la primera hora del simulacro nacional sin saturar los hilos HTTP del servidor ni exceder la capacidad del único VPS asignado.
- **Métrica de Éxito:** Latencia de aceptación de la petición $p95 \le 1500\text{ ms}$ (1.5 s) bajo carga extrema de hasta 28 req/s.

---

## 3. Paso 3 de ADD: Elegir el Elemento del Sistema a Refinar

Se selecciona el contenedor **`API Backend Monolítico`** (específicamente su módulo de **Ingesta**) y su mecanismo de interacción con la capa de persistencia relacional y espacial.

---

## 4. Paso 4 de ADD: Elegir Conceptos de Diseño (Tácticas Candidatas)

Se utilizó el catálogo canónico de tácticas arquitectónicas de Bass, Clements y Kazman (2021) para evaluar cuatro conceptos de diseño frente al escenario QA-01:

| Concepto de Diseño Evaluado | Táctica Formal de Bass et al. | Pros / Qué Mejora | Contras / Qué Empeora | Costo / Complejidad (1 mes / 2 devs) | Decisión del Equipo |
| :--- | :--- | :--- | :--- | :--- | :---: |
| **1. Migrar a Microservicios en Kubernetes / Cloud Run** | *Escalabilidad elástica horizontal* | Aislamiento total de pods de ingesta; autoescalado dinámico según CPU. | Introduce latencia de red entre microservicios, sobrecarga de observabilidad distribuida y costo de clúster K8s ($>\$150$ USD/mes). | Crítico: Imposible de operar en 1 mes con 2 personas; viola R-01 y R-03. | **RECHAZADA:** Sobreingeniería injustificada; la simulación demuestra que no se requiere escalado horizontal masivo. |
| **2. Escalar Verticalmente a 2 VPS con Balanceador (8 workers)** | *Aumentar recursos del sistema* | Incrementa la concurrencia bruta de hilos Uvicorn/FastAPI. | Duplica el costo mensual de infraestructura; no resuelve la saturación de I/O síncrona en disco en PostgreSQL. | Medio: Requiere contratar y configurar Nginx como load balancer entre 2 servidores. | **POSTERGADA (Plan B):** La simulación indica que a 28 req/s aún viola el presupuesto ($p95 = 50.0\text{ s}$). |
| **3. Ingesta Asíncrona con Buffer en Memoria (Redis) y Fast ACK HTTP 202** | *Gestionar la tasa de eventos (Buffer / Queue)* | Libera de inmediato las conexiones HTTP en $< 20\text{ ms}$; amortigua picos extremos protegiendo la base de datos relacional. | Introduce consistencia eventual: el reporte se confirma como recibido antes de que los workers completen el triaje. | Bajo: Redis 7 corre en el mismo VPS como servicio en memoria ligero ($\sim 60\text{ MB}$ RAM). | **ACEPTADA (Principal):** Cumple con creces el presupuesto QA-01 sin salir del presupuesto VPS. |
| **4. Índices Espaciales GiST en PostGIS y Particionamiento** | *Optimizar recursos computacionales* | Acelera consultas de geocerca `ST_DWithin` y clustering de duplicados de 380 ms a 110 ms en los workers Celery. | Ligero incremento en el tiempo de escritura en disco al actualizar el índice espacial. | Mínimo: Requiere crear el índice espacial `CREATE INDEX idx_reportes_geom ON reportes USING GIST (geometria);`. | **ACEPTADA (Complementaria):** Garantiza que los workers en segundo plano no se acumulen indefinidamente. |

---

## 5. Paso 5 de ADD: Instanciar Elementos y Asignar Responsabilidades

1. **`Nginx Reverse Proxy`:** Recibe tráfico HTTPS en el puerto 443, realiza terminación TLS, compresión Gzip y delega por socket Unix a la API.
2. **`FastAPI IngestController`:** Expone el endpoint `POST /api/v1/ingesta/sync`. Valida sintácticamente el esquema JSON con Pydantic, genera un identificador UUID y ejecuta `LPUSH cola:ingesta payload` en Redis. Retorna inmediatamente `HTTP 202 Accepted { "status": "recibido", "id": "..." }`.
3. **`Redis Buffer`:** Cola FIFO en memoria que actúa como amortiguador de choques (*shock absorber*) desacoplando la tasa de llegada de la tasa de procesamiento.
4. **`Celery Worker Pool`:** Conjunto de 4 procesos en background que consumen de `cola:ingesta`, ejecutan validaciones espaciales con PostGIS y persisten de forma transaccional ACID en PostgreSQL.

---

## 6. Paso 6 de ADD: Definir Interfaces para los Elementos Instanciados

- **Interfaz Externa (HTTP REST):**
  - `POST /api/v1/ingesta/sync`
  - *Request Body:* `{ "reporte_id": "uuid", "lat": -16.40, "lon": -71.53, "descripcion": "...", "foto_hash": "..." }`
  - *Response:* `HTTP 202 Accepted` en $\le 25\text{ ms}$ con `{ "codigo": 202, "mensaje": "Reporte encolado para triaje", "timestamp": "..." }`.
- **Interfaz Interna (Broker Redis):**
  - Comando: `LPUSH cola:triaje json_payload`
  - Estructura del mensaje: canal `cola:triaje`, clave de deduplicación espacial en memoria `set:hashes_recibidos`.

---

## 7. Paso 7 de ADD: Verificar y Refinar Requisitos con Evidencia Cuantitativa

Para respaldar la decisión y no basarse en especulaciones, se ejecutó una **simulación de eventos discretos M/G/c** (`fitness/rendimiento.py`) modelando las tasas de servicio y llegada durante el simulacro nacional:

### Tabla Comparativa de Resultados de la Simulación (2 minutos por nivel de carga, 4 workers)

| Escenario de Carga | Táctica Arquitectónica Evaluada | Latencia $p50$ | Latencia $p95$ | Evaluación frente a QA-01 ($p95 \le 1.5\text{ s}$) |
| :--- | :--- | :---: | :---: | :---: |
| **Normal post-sismo (6 req/s)** | Sin tácticas (Síncrono en BD) | 449.8 ms | 1004.2 ms | Cumple holgadamente |
| | Escalar a 8 workers (Síncrono) | 399.9 ms | 765.3 ms | Cumple |
| | Índices espaciales GiST | 114.5 ms | 202.5 ms | Cumple |
| | **Buffer Redis + GiST (Solución)** | **11.9 ms** | **16.4 ms** | **Cumple (Excelente)** |
| **Hora pico / réplica (18 req/s)** | Sin tácticas (Síncrono en BD) | 48,851.5 ms | 97,519.2 ms | **VIOLA PRESUPUESTO (Saturación)** |
| | Escalar a 8 workers (Síncrono) | 682.0 ms | 1,798.8 ms | **VIOLA PRESUPUESTO (1.8 s)** |
| | Índices espaciales GiST | 116.7 ms | 206.2 ms | Cumple |
| | **Buffer Redis + GiST (Solución)** | **11.7 ms** | **16.3 ms** | **Cumple (Margen del 98.9%)** |
| **Simulacro nacional (28 req/s)** | Sin tácticas (Síncrono en BD) | 113,091.9 ms | 213,844.3 ms | **COLAPSO CRÍTICO (Cola infinita)** |
| | Escalar a 8 workers (Síncrono) | 26,879.1 ms | 50,050.7 ms | **COLAPSO (Cola saturada)** |
| | Índices espaciales GiST | 154.7 ms | 399.7 ms | Cumple (Límite de I/O) |
| | **Buffer Redis + GiST (Solución)** | **11.7 ms** | **16.4 ms** | **CUMPLE RIGUROSAMENTE ($p95 = 16.4\text{ ms}$)** |

![Gráfico de Rendimiento ante el Simulacro](rendimiento.png)

### Hallazgos y Conclusiones de la Iteración 1
1. **La táctica de escalar recursos (8 workers) es insuficiente y costosa:** A 28 req/s, duplicar los workers únicamente retrasa el colapso unos segundos ($p95 = 50.0\text{ s}$), duplicando la factura mensual en dólares.
2. **El Buffer en Memoria Redis garantiza el éxito del escenario:** Mantiene una latencia $p95$ prácticamente plana de **$\approx 16.4\text{ ms}$** ante cualquier nivel de ráfaga, utilizando menos del $2\%$ del presupuesto límite de 1.5 s.
3. **Se valida y ratifica el ADR-001:** No existe necesidad de migrar a microservicios ni clústeres Kubernetes; el Monolito Modular Asíncrono en un único VPS satisface de manera óptima y económica el simulacro nacional de 20,000 reportes por hora.
