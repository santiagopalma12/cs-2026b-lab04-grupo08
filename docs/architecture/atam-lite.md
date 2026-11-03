# Evaluación Arquitectural ATAM-lite: SismoReporta AQP

**Proyecto:** SismoReporta AQP — Red Ciudadana y Alerta Temprana Sísmica para Arequipa  
**Curso:** Construcción de Software — EPIS UNSA (2026-B)  
**Grupo Evaluado:** Grupo 08 (Santiago Palma, Dario Rafael Cornejo Hurtado)  
**Equipo Evaluador:** Evaluador de Pares / Evaluador Adversario con IA (Prompt IA 3)  
**Fecha de Evaluación:** 31 de Octubre de 2026  
**Iteraciones Evaluadas:** Árbol de Utilidad (E1) e Iteración 1 de ADD (E2 - Rendimiento)  

---

## 1. Resumen Ejecutivo y Objetivos de la Evaluación

El método **ATAM-lite** (*Architecture Tradeoff Analysis Method - versión ligera*) tiene por objetivo evaluar la idoneidad de las decisiones arquitecturales tomadas durante el proceso **Attribute-Driven Design (ADD 3.0)** frente a los atributos de calidad prioritarios del sistema.

En el caso de **SismoReporta AQP**, el escenario crítico de crecimiento corresponde al **Simulacro Nacional**:
> *"Simulacro nacional o evento telúrico: recepción de 20 000 reportes ciudadanos de intensidad y daños en el lapso de 1 hora (tasa promedio de 5.56 req/s y ráfagas pico de 28 req/s) con la red móvil congestionada en la provincia de Arequipa."*

Los atributos de calidad de máxima criticidad analizados son:
1. **Rendimiento (QA-01):** Latencia de respuesta $p95 \le 1.5\text{ s}$ ante ráfagas de 28 req/s.
2. **Disponibilidad (QA-02):** Pérdida de reportes $= 0\%$ ante fallas de conectividad celular o caídas del broker.
3. **Seguridad (QA-04):** Aislamiento estricto de reportes sensibles por distrito/jurisdicción (PostgreSQL RLS).
4. **Modificabilidad (QA-05):** Adaptación a nuevos proveedores de mapas/sensores con esfuerzo $\le 16\text{ ph}$.

---

## 2. Matriz Consolidada de Hallazgos ATAM-lite

| Tipo de Hallazgo | ID | Escenario | Descripción del Hallazgo | Prob. (1-5) | Imp. (1-5) | Severidad (P × I) | Pregunta Incómoda del Evaluador | Respuesta y Decisión Técnica del Grupo 08 |
| :--- | :---: | :---: | :--- | :---: | :---: | :---: | :--- | :--- |
| **Sensibilidad** | S1 | QA-01 | La latencia $p95$ en la ingesta depende críticamente del tiempo de encolamiento en Redis (`LPUSH`) y la ausencia de I/O síncrono. | — | — | — | *¿Qué pasa si el endpoint FastAPI ejecuta validación espacial síncrona en lugar de solo parseo Pydantic?* | **Confirmado y blindado:** El endpoint `POST /api/v1/reportes` únicamente valida esquema en memoria y encola en Redis con Fast ACK HTTP 202. La validación espacial PostGIS se delega 100% a Celery. |
| **Sensibilidad** | S2 | QA-02 | La tasa de entrega de reportes con red móvil intermitente es sensible al tamaño del buffer local en el cliente (IndexedDB/SQLite). | — | — | — | *¿Cuántos reportes puede retener el dispositivo del ciudadano si la red se corta por 3 horas?* | **Confirmado:** El Outbox local almacena los reportes en IndexedDB (aprox. 1 KB por reporte). Una cuota de 5 MB permite almacenar más de 5,000 reportes locales sin degradación. |
| **Sensibilidad** | S3 | QA-06 | El tiempo de agregación de mapa de calor es altamente sensible a la existencia del índice GiST en la columna geográfica. | — | — | — | *¿Se degrada la consulta analítica a $O(N)$ si el índice espacial no se reconstruye tras 20 000 inserciones?* | **Confirmado:** PostGIS GiST escala logarítmicamente $O(\log N)$. Se programó mantenimiento `VACUUM ANALYZE` automático cada 24 horas y caché de 15 s para el mapa de calor. |
| **Trade-off** | T1 | QA-01 | **Rendimiento vs. Consistencia Inmediata:** Desacoplar la ingesta mediante cola Redis garantiza $p95 = 16.4\text{ ms}$, pero introduce inconsistencia eventual (delay de 2-5 s para ver el reporte en el mapa). | — | — | — | *¿Acepta INDECI y Defensa Civil un retraso de 3 segundos para visualizar el reporte en el mapa de mando?* | **Aceptado y justificado:** En emergencias sísmicas, la prioridad absoluta es no perder reportes ciudadanos por timeouts HTTP 504. Un retraso de 2-5 segundos es plenamente tolerable para la agregación del mapa. |
| **Trade-off** | T2 | QA-02 | **Disponibilidad vs. Complejidad de Implementación:** El patrón Circuit Breaker + Outbox garantiza 0 reportes perdidos, pero añade sincronización compleja y reconciliación de duplicados. | — | — | — | *¿Cómo evitan reportes duplicados si la red se reconecta mientras se procesaba una confirmación?* | **Aceptado y resuelto:** Idempotencia estricta en el backend mediante clave primaria UUID generada en el cliente (`id_reporte`). `INSERT ... ON CONFLICT (id_reporte) DO NOTHING`. |
| **Trade-off** | T3 | QA-04 | **Seguridad vs. Rendimiento de Consultas:** Filtrar con PostgreSQL RLS asegura aislamiento de distritos pero añade un predicado oculto a cada query. | — | — | **Severidad:** — | *¿Cuánto ralentiza el predicado RLS las consultas analíticas del COE Provincial sobre miles de filas?* | **Aceptado y medido:** El overhead de RLS con índice compuesto `(distrito_id, fecha_registro)` es menor al 3.8% en benchmarks de PostgreSQL. |
| **Riesgo** | R1 | QA-01 | Saturación de memoria RAM en Redis si los background workers colapsan o se detienen durante el simulacro de 20 000 reportes. | 2 | 5 | **10** (Atención) | *¿Qué pasa si Celery se cae y se acumulan 20 000 reportes en RAM? ¿Se agota la memoria del VPS?* | **Mitigado:** 20,000 reportes en Redis consumen solo ~10 MB de RAM. Se configuró `maxmemory 512mb` con política `noeviction` y persistencia AOF (`appendonly yes`). |
| **Riesgo** | R2 | QA-03 | Punto único de falla (SPOF) en la instancia única del VPS/PostgreSQL para la persistencia definitiva. | 3 | 4 | **12** (Crítico) | *Si el VPS principal se apaga durante el terremoto, ¿cómo garantizan MTTR < 15 min sin clúster HA?* | **Mitigado en E4:** Se implementa snapshot automatizado de volúmenes EBS/almacenamiento en bloque y réplica secundaria en standby frío, con procedimiento de failover documentado en ADR-007. |
| **Riesgo** | R3 | QA-02 | Tormenta de reintentos (*Thundering Herd*) cuando 15 000 celulares recuperan señal simultáneamente tras el corte. | 4 | 4 | **16** (Crítico) | *¿Cómo evitan que la API colapse si 15 000 clientes sincronizan su Outbox al mismo segundo?* | **Mitigado en E4:** Circuit Breaker en el cliente con algoritmo de *Exponential Backoff con Jitter aleatorio* (5 a 60 s) y rate-limiting en NGINX Gateway a 50 req/s por IP/subred. |
| **Riesgo** | R4 | QA-04 | Fuga de información sensible o bypass de políticas RLS por error en roles de conexión en PostgreSQL. | 2 | 4 | **8** (Aceptación) | *¿Cómo aseguran en CI que un operador del distrito A no puede ver reportes confidenciales del distrito B?* | **Mitigado en E5:** Fitness function automatizada (FF-06) en integración continua que ejecuta tests de penetración de roles y verifica 0 filas filtradas. |
| **"Riesgo" (Falso Positivo IA)** | R5 | QA-01 | *"Celery y Python no escalan para 20 000 reportes en 1 hora por culpa del GIL; se requiere migrar a Go/Rust o Kubernetes"*. | 1 | 2 | **2** (Descartado) | *¿Por qué insisten en Python si la IA sugiere que Kubernetes y microservicios en Go son indispensables?* | **Refutado con evidencia matemática:** 20,000 reportes/hora = 5.56 req/s promedio (pico 28 req/s). Cuatro workers Celery procesan >400 req/s. La simulación M/G/c demuestra $\rho = 0.07$ y $p95 = 16.4\text{ ms}$. La sugerencia de la IA añade sobrecosto operativo injustificado. |
| **No Riesgo** | NR1 | QA-01 | Capacidad de procesamiento del Monolito Modular con FastAPI + Redis + Celery para la carga del simulacro. | — | — | — | — | **Confirmado por simulación:** En `fitness/rendimiento.py`, la latencia $p95$ pasa de 213 s (cola saturada síncrona) a 16.4 ms con la táctica de buffer asíncrono. |
| **No Riesgo** | NR2 | QA-05 | Flexibilidad para cambiar el proveedor de mapas satelitales o sensor sísmico sin afectar la lógica de negocio. | — | — | — | — | **Confirmado por arquitectura:** Arquitectura Hexagonal (Puertos y Adaptadores) separa estrictamente el dominio (`DominioSismos`) de los adaptadores externos (`OpenStreetMapAdapter`, `IGPAdapter`). |

---

## 3. Análisis Detallado de Hallazgos

### 3.1 Puntos de Sensibilidad
1. **Sensibilidad S1 (Tiempo de encolamiento en Redis):** La ingesta ultra-rápida ($p95 = 16.4\text{ ms}$) requiere que el worker web de FastAPI libere el socket de red inmediatamente tras ejecutar `redis.lpush()`. Si se introdujera accidentalmente una llamada a base de datos relacional síncrona o una llamada HTTP saliente a un servicio de geolocalización dentro del controlador, la latencia se dispararía de 16 ms a >1200 ms, violando el SLA.
2. **Sensibilidad S2 (Buffer local del cliente):** La garantía de 0 reportes perdidos depende de que la PWA o aplicación móvil no dependa de memoria volátil. Si el usuario cierra el navegador o se apaga el teléfono sin que el reporte esté en IndexedDB, el dato se pierde.

### 3.2 Puntos de Trade-off
1. **Trade-off T1 (Rendimiento vs. Consistencia Eventual):** El buffer asíncrono desacopla la recepción de la indexación espacial. Esto significa que el operador de emergencias verá los nuevos puntos en el mapa con un retraso máximo de $W_q$ (tiempo medio de espera en cola Celery: aprox. 2.1 segundos durante ráfaga de 28 req/s). Se priorizó la disponibilidad de ingesta sobre la visualización en tiempo real estricto ($<500\text{ ms}$).
2. **Trade-off T2 (Disponibilidad vs. Sobrecarga de Almacenamiento):** Mantener un patrón Outbox transaccional tanto en el cliente (IndexedDB) como en el servidor (tabla `outbox_eventos`) introduce la necesidad de un proceso de recolección de basura (*garbage collection*) que elimine los eventos confirmados con más de 7 días de antigüedad.

### 3.3 Clasificación de Riesgos y Matriz de Probabilidad e Impacto
Los riesgos identificados por el evaluador se clasifican en una escala de 1 a 5:
* **Zona Crítica (Severidad $\ge 12$):** R3 (Tormenta de reintentos por reconexión masiva, severidad 16), R2 (SPOF en nodo único de base de datos, severidad 12).
* **Zona de Atención (Severidad $8 \le S \le 11$):** R1 (Saturación de memoria en Redis ante caída de workers, severidad 10), R4 (Fuga entre distritos por política RLS, severidad 8).
* **Zona Aceptable / Descartado (Severidad $< 8$):** R5 (Falso positivo de la IA sobre escalabilidad de Celery, severidad 2).

![Matriz de Riesgos ATAM-lite](diagramas/img/riesgos.png)

*Figura: Matriz de probabilidad e impacto generada con matplotlib (fitness/matriz_riesgos.py).*

---

## 4. Estrategias de Mitigación para los Riesgos de la Zona Crítica y de Atención

### 4.1 Mitigación de Riesgos Críticos (Severidad $\ge 12$)

#### Riesgo R3: Tormenta de Reintentos (*Thundering Herd*) tras Reconexión Masiva (Severidad: 16)
* **Escenario:** Al restablecerse las antenas celulares 4G o el broker de backend, 15 000 terminales móviles intentan simultáneamente vaciar su Outbox local, saturando los sockets de Nginx y colapsando el API Gateway.
* **Táctica de Mitigación Implementada:**
  1. **Circuit Breaker del Cliente:** El cliente conmuta a estado `ABIERTO` tras 3 fallos consecutivos, suspendiendo las llamadas a la red.
  2. **Exponential Backoff con Jitter Aleatorio:** En lugar de reintentos fijos, cada cliente calcula un retardo:
     $$T_{\text{reintento}} = \min(T_{\max}, T_{\text{base}} \times 2^{\text{intento}}) + \text{random}(0, \text{Jitter})$$
     con retardos distribuidos uniformemente entre 5 y 60 segundos, aplanando completamente el pico de reconexión.
  3. **Rate Limiting Perimetral en NGINX:** Cuota máxima de 50 req/s por bloque de IP para impedir inanición de recursos.
* **Evidencia Numérica:** La simulación Monte Carlo demostró una reducción del 97.3% en peticiones inútiles durante la interrupción (de 450 a 12 peticiones).

#### Riesgo R2: Punto Único de Falla (SPOF) en Instancia Única de PostgreSQL / VPS (Severidad: 12)
* **Escenario:** El servidor VPS en la nube sufre una falla de hardware físico o corte del proveedor durante el desastre, inhabilitando la base de datos central.
* **Táctica de Mitigación Aceptada para el MVP:**
  1. **Snapshots Horarios Automatizados:** Copias de seguridad atómicas en almacenamiento en bloque independiente del hipervisor.
  2. **Estrategia Offline-First en Clientes:** La PWA preserva los reportes en el almacenamiento persistente IndexedDB del dispositivo del usuario con cuota garantizada de 5 MB por tiempo indefinido.
  3. **Plan de Contingencia (Standby Frío):** Script de infraestructura como código (Docker Compose + restore) capaz de provisionar un nuevo VPS en un proveedor alterno en un tiempo de recuperación objetivo $\text{MTTR} \le 15\text{ minutos}$ (registrado formalmente para fase post-MVP).

### 4.2 Mitigación de Riesgos en Zona de Atención (Severidad 8 a 11)

#### Riesgo R1: Desborde de Memoria en Redis ante Parada de Background Workers (Severidad: 10)
* **Mitigación:** Configuración estricta de Redis: `maxmemory 512mb` y directiva `maxmemory-policy noeviction` con persistencia `appendonly yes` (AOF) en volumen SSD. Veinte mil reportes ciudadanos ligeros insumen menos de 10 MB de memoria volátil, dejando más de 500 MB de margen para buffers. Monitoreo activo con alertas al 70% de uso.

#### Riesgo R4: Fuga de Reportes entre Distritos por Error en Query SQL (Severidad: 8)
* **Mitigación:** Activación de **Row-Level Security (RLS)** forzada en el motor PostgreSQL. Ninguna consulta SQL de FastAPI puede eludir el filtro distrital, garantizado por la fitness function `test_ff06_aislamiento_rls_distrital` en CI.

### 4.3 Refutación de Falso Positivo de la IA (R5: "Celery no escala para 20 000 req/h")
* **Afirmación del Evaluador IA:** *"El worker de Celery en Python será el cuello de botella y no podrá procesar 20 000 reportes por culpa del GIL; se requiere migrar a microservicios en Go o Rust."*
* **Refutación Técnica con Evidencia:**
  * En una hora hay 3,600 segundos; 20 000 reportes representan una tasa media de **5.56 reportes/segundo**.
  * Cada worker Celery procesa entre 80 y 150 tareas de persistencia/segundo en PostgreSQL. Con 4 workers Celery, la capacidad del backend es de **>400 reportes/segundo**, superando por más de un orden de magnitud la ráfaga pico de 28 req/s.
  * La IA confundió 20 000 solicitudes por segundo con 20 000 por hora. El equipo rechazó la sobreingeniería de microservicios con base en mediciones concretas.

