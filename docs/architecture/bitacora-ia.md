# Bitácora de Uso Crítico de Inteligencia Artificial — SismoReporta AQP
**Construcción de Software · EPIS-UNSA · 2026-B · Grupo 08**  
**Integrantes:** Santiago Palma (`santiagopalma12`), Dario Rafael Cornejo Hurtado (`darich1010`)

---

## 1. Registro de Interacciones

| # | Fecha | Herramienta | Prompt (Resumen) | Qué propuso la IA | Qué verificamos o corregimos | Decisión |
| :-: | :---: | :---: | :--- | :--- | :--- | :---: |
| **1** | 2026-09-29 | Claude Opus 5.5 | **Prompt 1 (RCRTF):** Generar 3 alternativas de estilo arquitectónico para SismoReporta AQP con 2 devs, 1 mes y 1 VPS. | Recomendó como "mejor alternativa" una solución Serverless en AWS: API Gateway + Lambda + Kinesis + DynamoDB + S3, argumentando escalabilidad infinita ante sismos. | Se constató que excede la restricción **R-03** (presupuesto bajo de VPS de \$10-\$20; el costo serverless por ráfaga y transferencias multimedia es impredecible), introduce fuerte *vendor lock-in* y el tiempo de configuración supera el plazo de 1 mes (**R-01**). | **Rechazada** |
| **2** | 2026-09-29 | Claude Sonnet 5.5 | **Prompt 2 (Crítica Adversarial):** Actuar como "abogado del diablo" contra el Monolito Modular Asíncrono e identificar 5 riesgos críticos y mitigaciones. | Señaló que encolar imágenes directamente en Redis como cadenas Base64 colapsaría la memoria RAM del VPS e impactaría la latencia de eventos en el *single-thread* de Redis. | Se confirmó en la documentación de Redis que almacenar payloads $> 1\text{ MB}$ degrada severamente el *event loop*. Se corrigió el diseño arquitectónico: la PWA comprime la foto en el cliente ($< 400\text{ KB}$), la sube a almacenamiento de objetos local (MinIO), y a Redis solo viaja un payload liviano con metadatos y la URL firmada. | **Corregida** |
| **3** | 2026-09-29 | Gemini 3.8 Flash | **Generación Mermaid:** Generar el código Mermaid del Monolito Modular con subgraphs, módulos e integraciones. | Generó un diagrama con dependencias circulares entre el módulo de Brigadas y Triaje, y propuso usar la API comercial de Google Maps Directions para el ruteo de brigadas. | Se depuró la sintaxis en https://mermaid.live, se eliminaron los ciclos aplicando inversión de dependencias mediante interfaces de dominio, y se sustituyó Google Maps por OpenStreetMap / Carto Tiles Open Source para respetar **R-03** (presupuesto cero en licencias). | **Corregida** |
| **4** | 2026-09-29 | GPT 5.6 Luna | **Revisión de ADR-002:** Consultar la viabilidad de la *Background Sync API* de PWAs para enviar reportes guardados en smartphones sin conexión. | Afirmó que la Background Sync API garantiza la transmisión transparente en segundo plano de forma idéntica tanto en Android Chrome como en iOS Safari. | Se verificó en *MDN Web Docs* y la documentación de WebKit que Safari en iOS tiene soporte sumamente restringido o nulo para Background Sync cuando la app está cerrada. Se corrigió el ADR-002 agregando listeners en `visibilitychange` y `focus` como estrategia de respaldo obligatoria para iPhones. | **Corregida** |
| **5** | 2026-09-29 | GitHub Copilot (Sonnet 5.5) | **Optimización SQL PostGIS:** Generar consulta geoespacial para agrupar reportes a menos de 50 metros en un lapso de 15 minutos (anti-duplicados). | Propuso utilizar `ST_ClusterDBSCAN` combinado con una función de ventana y filtro espacial mediante índice GiST en PostgreSQL. | Se evaluó el plan de ejecución con `EXPLAIN ANALYZE` sobre un conjunto sintético de 25,000 registros georreferenciados, confirmando que el índice `idx_reportes_geom` resuelve la consulta en menos de 10 ms sin barrido secuencial. | **Aceptada** |
| **6** | 2026-10-31 | Claude Sonnet 3.7 | **Prompt IA 1 (Árbol de Utilidad):** Proponer escenarios de calidad medibles para rendimiento, disponibilidad, seguridad y modificabilidad ante el simulacro nacional. | Sugirió QA-06 (Consulta de mapa de calor) con clasificación (H, H) y formuló escenarios sin umbrales numéricos de latencia. | Se refutó que el mapa de calor sea de vida o muerte (la ingesta sí lo es); se reclasificó QA-06 a (M, L) y se fijaron medidas numéricas concretas: $p95 \le 1.5\text{ s}$ ante 20 000 reportes/h (28 req/s pico). | **Corregida** |
| **7** | 2026-10-31 | ChatGPT-4o | **Prompt IA 2 (ADD Iteración 1 - Rendimiento):** Proponer conceptos de diseño para absorber ráfagas de 28 req/s en el simulacro nacional. | Recomendó migrar el backend a microservicios distribuidos sobre un clúster Kubernetes con Apache Kafka. | Se simuló el comportamiento M/G/c en `fitness/rendimiento.py`. La táctica de buffer en Redis con Fast ACK HTTP 202 logra $p95 = 16.4\text{ ms}$ operando a solo 7% de capacidad ($\rho = 0.07$), haciendo innecesario K8s y evitando violar el presupuesto de \$15 USD/mes (R-03). | **Rechazada** |
| **8** | 2026-10-31 | Gemini 3.8 Flash | **ADD Iteración 2 (Disponibilidad QA-02):** Proponer mecanismo para evitar pérdida de reportes cuando el broker sufre una caída de 20 minutos. | Sugirió acumular los reportes pendientes en una cola volátil en memoria dentro de Redis. | Se detectó que si el servidor o Redis experimentan un corte eléctrico súbito, la memoria se vacía y se pierden los reportes ciudadanos en tránsito. Se adoptó el patrón Outbox transaccional persistente en PostgreSQL (ACID) y almacenamiento persistente IndexedDB en el cliente móvil. | **Corregida** |
| **9** | 2026-10-31 | Claude Sonnet 3.7 | **ADD Iteración 3 (Seguridad QA-04):** Diseñar estrategia multitenant para aislar datos entre los 29 distritos de Arequipa. | Recomendó aprovisionar 29 bases de datos PostgreSQL físicas independientes (una por distrito). | Se calculó el consumo de memoria en el VPS (4 GB RAM): 29 bases de datos fragmentan los buffer pools y saturan las conexiones. Se adoptó Row-Level Security (RLS) en una base de datos única con claims en JWT, reduciendo el consumo de RAM a $< 150\text{ MB}$. | **Corregida** |
| **10** | 2026-10-31 | Prompt IA 3 (Evaluador Adversario) | **Evaluación ATAM-lite (Riesgo R5):** Criticar la arquitectura evaluando cuellos de botella para el simulacro nacional. | **Falso Positivo de la IA:** Afirmó que *"Celery y Python colapsarán con 20 000 reportes en 1 hora por culpa del GIL y no podrán procesar la carga"*. | **Refutado con evidencia cuantitativa:** 20 000 reportes en 1 hora corresponden a una tasa promedio de apenas 5.56 req/s y pico de 28 req/s. Un solo worker Celery procesa $> 100\text{ reportes/s}$ en PostGIS; 4 workers procesan $> 400\text{ req/s}$, consumiendo menos del 15% de CPU. Se pidió evidencia matemática a la IA y no pudo sustentarla. | **Rechazada (Falso Positivo)** |
| **11** | 2026-10-31 | GitHub Copilot | **Diseño de Fitness Functions (CI):** Sugerir cómo verificar en CI que los desarrolladores no violen las capas arquitectónicas. | Sugirió crear scripts en Bash con expresiones regulares (`grep -rn "import"`) en el pipeline de GitHub Actions. | Se constató que `grep` genera falsos positivos, no comprende imports indirectos ni resuelve el árbol de dependencias AST. Se implementó `import-linter` con contratos formales (FF-01 capas sin ciclos y FF-02 aislamiento de adaptadores externos). | **Corregida** |

---

## 2. Anexo: Prompts Completos

### Interacción 1 — Generación de Alternativas de Estilo (RCRTF)
```text
Actúa como arquitecto de software senior especializado en sistemas de respuesta rápida ante desastres y emergencias civiles.
Contexto: Diseñamos la plataforma "SismoReporta AQP" para la región Arequipa (Perú), cuyo fin es permitir a la ciudadanía reportar daños estructurales, heridos y vías colapsadas tras un sismo, para que el Centro de Operaciones de Emergencia (COE) y Defensa Civil prioricen zonas y despachen brigadas. Durante la primera hora se esperan ráfagas de hasta 20,000 reportes bajo redes móviles congestionadas.
Restricciones obligatorias:
1. Plazo: El MVP debe estar en producción en exactamente 1 mes.
2. Equipo: Solo 2 desarrolladores con experiencia en Python (FastAPI/Django), TypeScript y SQL.
3. Presupuesto: Bajo, limitado a un único VPS en la nube (ej. Hetzner o DigitalOcean de 15 USD/mes). Quedan descartados servicios gestionados con tarificación por consumo variable.
4. Conectividad: La app debe funcionar en smartphones de gama media/baja con conectividad intermitente.
Tarea: Propón 3 alternativas de estilo arquitectónico. Para cada una explica: idea central, fortalezas, debilidades, riesgos y qué atributos de calidad favorece o penaliza (según ISO/IEC 25010). Concluye con tu recomendación justificada.
Formato: Tabla comparativa en Markdown y conclusión técnica. No inventes capacidades ni costos; si no estás seguro de algo, indícalo.
```

### Interacción 2 — Crítica Adversarial ("Abogado del Diablo")
```text
Ahora actúa como el más exigente y crítico "abogado del diablo" arquitectónico.
Critica con rigor técnico la alternativa que seleccionamos: "Monolito Modular Asíncrono en un único VPS con Redis para buffering y Celery para procesamiento de fotos y triaje geoespacial".
Analiza:
1. ¿Qué supuestos optimistas estamos cometiendo que podrían fallar catastróficamente en producción ante 20,000 reportes en 1 hora?
2. ¿Qué cuellos de botella ocultos existen en el uso de Redis y PostgreSQL en un solo servidor?
3. ¿Qué ocurre con la memoria RAM si se acumulan fotos pesadas?
Enumera los 5 riesgos más graves y proporciona para cada uno una táctica arquitectónica concreta de mitigación.
```

### Interacción 3 — Modelado en Diagram as Code (Mermaid)
```text
Actúa como especialista en Diagram as Code con Mermaid.
Genera el código fuente de un diagrama de arquitectura (flowchart TB) para el Monolito Modular Asíncrono de SismoReporta AQP.
Requisitos del diagrama:
- Actores: Ciudadano (PWA con IndexedDB), Brigadista en Campo (PWA/Móvil), Coordinador COE (Web Dashboard).
- Subgraphs:
  1. Capa Perimetral: Nginx (SSL, Rate Limiting).
  2. Monolito Modular: Capa de Presentación (FastAPI), Módulos de Dominio (Ingesta, Triaje, Brigadas, GIS, Notificaciones), Workers Asíncronos (Celery) y Repositorios.
  3. Almacenamiento: Redis en memoria, PostgreSQL + PostGIS (esquemas aislados), Almacenamiento de objetos local MinIO.
  4. Servicios Externos: OpenStreetMap Tiles, Gateway SMS Masivo, Interoperabilidad INDECI/SINAGERD.
- Flujo de datos etiquetado: Muestra la ingesta inmediata con HTTP 202 hacia Redis y el posterior consumo asíncrono hacia PostGIS y MinIO.
- Estilos visuales legibles con classDef.
Asegúrate de que la sintaxis sea estrictamente compatible con mermaid.live y GitHub sin errores de compilación.
```

### Interacción 4 — Viabilidad de Background Sync en Dispositivos Móviles
```text
Actúa como ingeniero frontend senior especializado en PWAs y APIs de navegación web.
Evalúa la viabilidad técnica de utilizar la "Background Sync API" de Service Workers para garantizar el envío de reportes de emergencia almacenados en IndexedDB cuando el celular de un ciudadano recupera conectividad tras un sismo.
Detalla:
1. Compatibilidad real entre navegadores (Chromium en Android vs WebKit en iOS Safari).
2. Comportamiento cuando la pantalla está apagada o el navegador está en background.
3. Qué táctica de mitigación debemos implementar en el código para dispositivos que no soportan Background Sync de forma nativa.
```

### Interacción 5 — Optimización de Consulta Geoespacial de Deduplicación en PostGIS
```text
Actúa como administrador de bases de datos senior especializado en PostgreSQL 16 y PostGIS.
Escribe una consulta SQL altamente eficiente para resolver el siguiente problema de triaje post-sismo:
"Detectar y consolidar reportes duplicados que se encuentren a menos de 50 metros geodésicos de distancia entre sí y hayan sido creados en una ventana temporal de 15 minutos en el departamento de Arequipa (SRID 4326)".
Requisitos:
- Debe utilizar índices espaciales GiST y evitar full table scans.
- Debe agrupar los incidentes asignándoles un cluster_id común.
- Explica qué índices específicos se deben crear para garantizar que la consulta ejecute en menos de 20 ms con 50,000 registros.
```

### Interacción 6 — Prompt IA 1: Escenarios para el Árbol de Utilidad
```text
Actúa como arquitecto de software senior.
Contexto: Plataforma SismoReporta AQP, monolito modular con FastAPI, Celery, Redis y PostgreSQL + PostGIS (ADR-001).
Nuevo contexto: Simulacro nacional con 20 000 reportes ciudadanos en 1 hora bajo red móvil congestionada en la provincia de Arequipa (28 req/s pico).
Tarea: Propón escenarios de calidad estructurados en seis partes (fuente, estímulo, entorno, artefacto, respuesta y medida numérica) para los atributos de Rendimiento, Disponibilidad, Seguridad y Modificabilidad.
Para cada escenario sugiere su calificación de (importancia para el negocio, dificultad técnica) en escala H/M/L y justifícala.
Restricciones: Cada escenario debe incluir una métrica numérica objetiva y verificable; no propongas soluciones tecnológicas todavía.
```

### Interacción 7 — Prompt IA 2: Conceptos de Diseño para Iteración 1 de ADD
```text
Actúa como arquitecto de software experto en sistemas de alta concurrencia.
Contexto: Escenario prioritario QA-01 de SismoReporta AQP: Ingesta de 20 000 reportes en 1 hora (28 req/s pico) con p95 <= 1.5 s en un único VPS con 2 vCPUs y 4 GB de RAM.
Tarea: Propón 3 conceptos de diseño alternativos para absorber esta carga.
Para cada concepto analiza sus trade-offs, costo de infraestructura y viabilidad para un equipo de 2 desarrolladores en 1 mes.
Identifica cuál descartarías y cuál seleccionarías, justificando la decisión con un modelo formal o simulación.
```

### Interacción 8 — Iteración 2 de ADD: Resiliencia y Mitigación ante Caída de Broker
```text
Actúa como especialista en ingeniería de confiabilidad (SRE) y arquitecturas resilientes.
Contexto: SismoReporta AQP, escenario QA-02. Durante un sismo real, la red 4G sufre 8% de timeouts transitorios y el broker central de mensajería experimenta una caída no programada de 20 minutos.
Tarea: Evalúa la viabilidad de implementar una cola de reintentos en memoria en Redis frente al patrón Circuit Breaker con Outbox relacional en PostgreSQL y almacenamiento local IndexedDB en la PWA.
Demuestra cuál de las dos opciones garantiza 0 reportes perdidos en caso de que el propio servidor se reinicie.
```

### Interacción 9 — Iteración 3 de ADD: Multitenencia Distrital y Seguridad
```text
Actúa como arquitecto de seguridad y especialista en PostgreSQL.
Contexto: SismoReporta AQP debe dar soporte a 29 municipalidades distritales de Arequipa y Defensa Civil (QA-04).
Restricción: Presupuesto limitado a un solo VPS de 4 GB RAM.
Tarea: Compara tres enfoques multitenancy:
1. Una base de datos por distrito.
2. Un schema por distrito.
3. Una tabla compartida con columna distrito_id y Row-Level Security (RLS) en PostgreSQL nativo con claims JWT.
Evalúa impacto en consumo de memoria RAM, complejidad de migraciones con Alembic y prevención de filtración de datos entre distritos.
```

### Interacción 10 — Prompt IA 3: Evaluador Adversario ATAM-lite (Detección y Refutación de Falso Positivo)
```text
Actúa como un evaluador ATAM escéptico y riguroso.
Te paso el árbol de utilidad, los ADR-006 a 008, la vista de contenedores C4 y los resultados de las simulaciones de SismoReporta AQP.
Para cada escenario prioritario identifica: puntos de sensibilidad, puntos de trade-off, riesgos (con probabilidad e impacto de 1 a 5) y no riesgos.
Para cada riesgo formula una pregunta incómoda que el equipo debería poder responder. No propongas rediseños completos; cita la evidencia que te falta.
```

### Interacción 11 — Diseño de Fitness Functions en CI/CD
```text
Actúa como ingeniero de calidad y arquitectura de software.
Contexto: Queremos proteger la arquitectura del monolito modular de SismoReporta AQP frente a su degradación en el repositorio Git (ADR-001 y ADR-005).
Tarea: Propón cómo implementar fitness functions estructurales (que impidan dependencias circulares o violaciones entre capas) y de calidad (que verifiquen latencia p95 y cero pérdida de reportes) en un pipeline de GitHub Actions en Python.
```
