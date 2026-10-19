# Auditoría y Lista de Revisión Oficial del Modelo C4 — Laboratorio 06
**Construcción de Software · EPIS-UNSA · Semestre 2026-B · Grupo 08**  
Integrantes: Santiago Palma (`spalmaa@unsa.edu.pe`), Dario Rafael Cornejo Hurtado (`dcornejohu@unsa.edu.pe`)

---

## 1. Evaluación con la Lista Oficial de Calidad (c4model.com/diagrams/checklist)

Se aplicó la lista de verificación oficial estructurada en las tres dimensiones normativas (General, Elementos y Relaciones) sobre las 5 vistas generadas a partir del modelo formal en Structurizr DSL:

| Vista Auditada | Grupo de Criterio | Pregunta de Revisión Oficial | Cumple (Sí / No) | Evidencia en el Modelo / Corrección Aplicada |
| :--- | :--- | :--- | :---: | :--- |
| **Contexto** (`systemContext`) | General | ¿Tiene título, alcance explícito y leyenda clara? | Sí | Título: *SismoReporta AQP - System Context*. Incluye leyenda de colores (#08427B para personas, #1168BD para el sistema, #999999 para sistemas externos). |
| **Contexto** (`systemContext`) | Elementos | ¿Cada elemento posee nombre, tipo C4 y descripción de intención sin jerga técnica interna? | Sí | Personas modeladas con roles claros (Ciudadano, Brigadista, Coordinador). Ningún elemento expone tecnologías de bajo nivel ni frameworks en este nivel. |
| **Contexto** (`systemContext`) | Relaciones | ¿Cada flecha describe la intención del flujo en dirección correcta y con verbo activo? | Sí | Conectores con verbos declarativos: *"Registra reportes de daños..."*, *"Monitorea mapa de calor..."*. Se eliminó el uso de verbos genéricos como "usa". |
| **Contenedores** (`container`) | General | ¿Se identifican claramente los límites del sistema frente a los actores y servicios externos? | Sí | Límite perimetral (*boundary*) demarcado para SismoReporta AQP; servicios de Mapas y Pasarela SMS se ubican fuera del límite como sistemas externos. |
| **Contenedores** (`container`) | Elementos | ¿Cada contenedor declara su tecnología específica y no se confunde con infraestructura? | Sí | Tecnologías declaradas explícitamente: PWA (TypeScript/React/IndexedDB), API (Python/FastAPI), Broker (Redis 7), DB (PostgreSQL 16/PostGIS). Ningún contenedor se llama "Docker" ni "VPS". |
| **Contenedores** (`container`) | Relaciones | ¿Se especifican los protocolos de comunicación exactos en cada interacción? | Sí | Protocolos explícitos: HTTPS/JSON, HTTPS/WSS, Redis Protocol (RESP), SQL/TCP y S3 API (HTTPS). |
| **Componentes** (`component`) | General | ¿El diagrama corresponde al contenedor principal y es coherente con el diseño UML? | Sí | Contenedor principal: API Backend Monolítico. Los 6 componentes coinciden con los paquetes definidos en `docs/design/paquetes.puml` del Lab 05. |
| **Componentes** (`component`) | Elementos | ¿Los componentes representan unidades modulares de software y no capas técnicas genéricas? | Sí | Módulos de dominio desacoplados: Ingesta, Triaje, Despacho, GIS, Notificaciones y Dominio Compartido. |
| **Componentes** (`component`) | Relaciones | ¿Las dependencias respetan el Grafo Dirigido Acíclico (DAG) sin referencias circulares? | Sí | Todas las dependencias son unidireccionales; no existen ciclos. Los módulos acceden a Dominio Compartido y se comunican internamente mediante llamadas in-process desacopladas. |
| **Dinámica** (`dynamic`) | General | ¿Modela una colaboración concreta con secuencia numerada paso a paso? | Sí | Flujo *SincronizacionOffline* numerado del paso 1 al 8, ilustrando el ingreso de la ráfaga masiva y el fast ACK. |
| **Dinámica** (`dynamic`) | Relaciones | ¿Cada paso corresponde a una relación ya existente en el modelo estático? | Sí | Todos los pasos conectan contenedores definidos previamente; Structurizr valida que no existan saltos no autorizados en el modelo. |
| **Despliegue** (`deployment`) | General | ¿Identifica el entorno de ejecución, los nodos físicos/virtuales y las instancias mapeadas? | Sí | Entorno "Producción" con nodos anidados: dispositivos móviles, estación de trabajo COE y servidor VPS en nube. |
| **Despliegue** (`deployment`) | Elementos | ¿Los nodos declaran sistema operativo, especificación de hardware y presupuesto? | Sí | Servidor Cloud VPS configurado con 4 vCPUs, 8 GB RAM, Ubuntu 24.04 LTS, coste $15 USD/mes, en estricta coherencia con la restricción R-03 de `drivers.md`. |

---

## 2. Auditoría Asistida por Inteligencia Artificial y Detección de Falsos Positivos

Se ejecutó una revisión cruzada mediante el asistente de Inteligencia Artificial utilizando el **Prompt IA 2** normado en la guía de práctica:

### Prompt Ejecutado
> *"Actúa como revisor de diagramas de arquitectura. Evalúa estas vistas exportadas de un modelo C4 de SismoReporta AQP con la lista de revisión de c4model.com: generales, elementos y relaciones. Responde en una tabla (vista, pregunta de la lista, cumple sí/no, evidencia, corrección sugerida). No inventes problemas: si algo cumple, indícalo."*

### Análisis de Hallazgos y Falso Positivo Detectado

1. **Observación Válida de la IA:** La IA señaló que en la primera versión del borrador del DSL, la relación entre el componente de Notificaciones y la Pasarela SMS carecía del protocolo explícito `HTTPS/REST`.  
   *Acción del equipo:* Se agregó el protocolo formal en el conector correspondiente de `workspace.dsl`.

2. **Falso Positivo Detectado (Error de la IA):**  
   *Afirmación de la IA:* La IA marcó como **incumplimiento crítico** que el contenedor `PWA Cliente Offline` poseyera las etiquetas simultáneas `Web Browser` y `Mobile App`, argumentando que *"un elemento en C4 no puede ser una aplicación de navegador y una aplicación móvil al mismo tiempo, debiendo desdoblarse en dos contenedores independientes"*.  
   *Análisis y Veredicto del Equipo:* **Falso Positivo.** La arquitectura de SismoReporta AQP implementa una **Progressive Web App (PWA)** unificada bajo estándares W3C. La aplicación se ejecuta dentro del motor del navegador móvil del smartphone (lo que justifica la forma y naturaleza web) pero se instala en la pantalla de inicio con acceso a almacenamiento local persistente (IndexedDB) y sensores de geolocalización en segundo plano mediante Service Workers (justificando el rol móvil). Separarla en dos contenedores habría falseado la realidad del código fuente (que es una sola base de código en React/TypeScript) e introducido redundancia innecesaria en el MVP de 1 mes. Se mantuvo la modelación del contenedor único.
