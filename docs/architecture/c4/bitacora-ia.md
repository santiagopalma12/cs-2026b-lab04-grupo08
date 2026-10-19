# Bitácora de Interacciones Críticas con Inteligencia Artificial — Laboratorio 06
**Construcción de Software · EPIS-UNSA · Semestre 2026-B · Grupo 08**  
Integrantes: Santiago Palma (`spalmaa@unsa.edu.pe`), Dario Rafael Cornejo Hurtado (`dcornejohu@unsa.edu.pe`)

---

El equipo aplicó la regla fundamental: *"La IA propone, el equipo decide y verifica"*. A continuación se detallan 5 interacciones estructuradas con modelos de lenguaje durante el desarrollo de la arquitectura C4:

### Interacción 1: Generación del Borrador Inicial del Modelo en Structurizr DSL
* **Fecha:** 2026-10-20
* **Herramienta:** Asistente LLM (Gemini 3.8 / Claude 3.5 Sonnet)
* **Prompt Ejecutado:**  
  `Actúa como arquitecto de software experto en el modelo C4 y en Structurizr DSL. Contexto: [inventario.md, ADR-001 y despliegue.py]. Genera un borrador completo de workspace.dsl con personas, sistema, contenedores, componentes, sistemas externos y relaciones con protocolo. Aplica !identifiers hierarchical.`
* **Propuesta de la IA:** La IA incluyó un contenedor llamado `"Docker Compose"` dentro de `sismoReporta` y definió al sistema externo de mapas como un contenedor interno de base de datos.
* **Verificación Humana:** Docker Compose es una herramienta de orquestación de infraestructura local, no un contenedor de software en el modelo C4. Asimismo, el servicio de mapas es un proveedor externo SaaS (OpenStreetMap/Mapbox) que no es desarrollado ni desplegado por el equipo.
* **Decisión del Equipo:** Se corrigió el modelo: Docker Compose fue ubicado como nodo de despliegue en la vista física, y el servicio de mapas se etiquetó como `softwareSystem "Servicio de Mapas y Teselas" ... "Externo"`.

---

### Interacción 2: Modelado de Dependencias entre Módulos y Aciclicidad (Regla C4)
* **Fecha:** 2026-10-20
* **Herramienta:** Asistente LLM
* **Prompt Ejecutado:**  
  `A partir de docs/design/paquetes.puml del Lab 05, genera las relaciones entre componentes dentro del contenedor apiBackend asegurando aciclicidad y coherencia con el flujo asíncrono del ADR-001.`
* **Propuesta de la IA:** La IA sugirió una llamada síncrona directa: `compIngesta -> compTriaje "Invoca evaluación inmediata de severidad" "HTTP/REST"`.
* **Verificación Humana:** En un monolito modular, la comunicación entre módulos empaquetados en el mismo artefacto no utiliza HTTP interno. Además, acoplar síncronamente Ingesta con Triaje viola directamente el driver QA-01 y el ADR-001, pues bloquearía el endpoint de ingesta bajo ráfagas de 20,000 reportes mientras se calculan análisis espaciales.
* **Decisión del Equipo:** Se rechazó la llamada síncrona. Se modeló a `compIngesta` encolando el evento en el contenedor `brokerRedis` (`LPUSH`), permitiendo que el procesamiento pesado sea consumido asíncronamente por el worker en background.

---

### Interacción 3: Estructuración de la Vista Dinámica y Reglas del Compilador DSL
* **Fecha:** 2026-10-20
* **Herramienta:** Asistente LLM
* **Prompt Ejecutado:**  
  `Escribe la vista dinámica para el flujo de sincronización diferida en Structurizr DSL combinando llamadas de componentes y contenedores.`
* **Propuesta de la IA:** La IA redactó una vista dinámica de ámbito `softwareSystem` (`dynamic sismoReporta`) mezclando directamente componentes internos (`apiBackend.compIngesta`) con contenedores perimetrales (`proxyNginx`).
* **Verificación Humana:** Al ejecutar `structurizr.sh validate`, el compilador arrojó error formal: *"Components can't be added to a dynamic view when the scope is a software system"*. La especificación C4 exige que una vista dinámica mantenga un nivel de abstracción uniforme (solo contenedores o solo componentes dentro de un contenedor).
* **Decisión del Equipo:** Se corrigió la vista dinámica para que sus 8 pasos interconecten contenedores del sistema (`pwaCliente`, `proxyNginx`, `apiBackend`, `bdPostgis`, `brokerRedis`, `workerAsincrono`), logrando validación exitosa (código de salida 0).

---

### Interacción 4: Auditoría de Calidad Oficial y Detección de Falsos Positivos
* **Fecha:** 2026-10-20
* **Herramienta:** Asistente LLM
* **Prompt Ejecutado (Prompt IA 2):**  
  `Actúa como revisor de diagramas de arquitectura. Evalúa estas vistas exportadas de un modelo C4 de SismoReporta AQP con la lista de revisión de c4model.com: generales, elementos y relaciones. Responde en una tabla y no inventes problemas.`
* **Propuesta de la IA:** La IA validó la coherencia global, identificó correctamente la ausencia del protocolo `HTTPS/REST` en la flecha hacia la pasarela de SMS, pero declaró como error crítico que el contenedor `PWA Cliente Offline` tuviera las etiquetas `Web Browser` y `Mobile App` al mismo tiempo, exigiendo duplicar el contenedor.
* **Verificación Humana:** El estándar de Progressive Web App (PWA) combina intencionalmente ejecución en motor de navegador web con características nativas móviles (instalación en home screen, almacenamiento offline IndexedDB, service workers en background). Dividir la PWA en dos contenedores falsearía el código fuente y duplicaría el alcance del MVP.
* **Decisión del Equipo:** Se aceptó la corrección del protocolo de red en la pasarela SMS, pero se descartó el requerimiento de bifurcar la PWA, documentándolo como falso positivo formal en `revision-c4.md`.

---

### Interacción 5: Redacción de Explicación Ejecutiva para Interesados No Técnicos
* **Fecha:** 2026-10-20
* **Herramienta:** Asistente LLM
* **Prompt Ejecutado (Prompt IA 3):**  
  `Explica el diagrama de contexto de SismoReporta AQP al Director del COE y Defensa Civil Arequipa, que no es técnico, en máximo 120 palabras: qué hace el sistema, quién lo usa y de qué servicios externos depende. Evita toda jerga técnica.`
* **Propuesta de la IA:** La IA produjo un texto de 165 palabras que utilizaba términos técnicos abstractos como *"arquitectura monolítica desacoplada"*, *"buffers volátiles en memoria"* e *"ingesta de payloads HTTP"*.
* **Verificación Humana:** El texto violaba la restricción de extensión máxima (120 palabras) e incumplía la regla de accesibilidad para autoridades civiles operativas que desconocen conceptos de ingeniería de software.
* **Decisión del Equipo:** Se reescribió y editó el contenido, conservando la explicación funcional de ciudadanos reportando, COE monitoreando el mapa, brigadas siendo despachadas y uso de mapas públicos y alertas masivas, alcanzando exactamente 107 palabras sin ninguna jerga técnica.
