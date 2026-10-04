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
