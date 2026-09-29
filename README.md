# SismoReporta AQP — Laboratorio 04: Fundamentos de Arquitectura de Software
**Construcción de Software · EPIS-UNSA · 2026-B · Grupo 08**  
Docente: Mg. Antonio Arroyo Paz

---

## Integrantes
| Nombre | Usuario GitHub | Correo Institucional | Rol en el Laboratorio |
| :--- | :---: | :---: | :--- |
| **Santiago Palma** | `@santiagopalma12` | `spalmaa@unsa.edu.pe` | Arquitecto de Software, Diagramador (Mermaid & Python Diagrams), Redactor de ADR-001 y ADR-003. |
| **Dario Rafael Cornejo Hurtado** | `@darich1010` | `dcornejohu@unsa.edu.pe` | Especialista en Resiliencia y Datos, Diagramador PlantUML, Redactor de ADR-002, Verificador y Auditor de IA. |

---

## Caso 8: SismoReporta AQP
Plataforma ciudadana y de coordinación de emergencias para la región Arequipa tras un evento sísmico de gran magnitud. Permite a los ciudadanos afectados registrar reportes de colapsos estructurales, personas atrapadas y vías bloqueadas adjuntando fotografías comprimidas y geolocalización GPS, incluso sin conectividad a internet. El sistema consolida los incidentes en un tablero de comando con mapa de calor para que el Centro de Operaciones de Emergencia (COE) y Defensa Civil prioricen zonas de auxilio y despachen brigadas de rescate en función de la severidad del daño.  
**Atributo de Calidad Crítico:** *Disponibilidad y Rendimiento ante picos extremos:* Absorber hasta **20,000 reportes en la primera hora** con la red móvil colapsada o intermitente, garantizando **0 reportes perdidos** mediante persistencia local en el cliente (IndexedDB) y sincronización asíncrona diferida con latencia de aceptación $p95 \le 1.5\text{ s}$.

---

## Arquitectura Elegida: Monolito Modular Asíncrono
La arquitectura seleccionada organiza el sistema en un único artefacto desplegable en Python estructurado en módulos de dominio desacoplados (*Ingesta*, *Triaje*, *Brigadas*, *GIS*, *Notificaciones*), empleando **Redis** como buffer de ingesta masiva en memoria y workers en segundo plano (**Celery/arq**) para compresión multimedia y procesamiento geoespacial sobre **PostgreSQL + PostGIS**.

```mermaid
flowchart TB
    %% Actores del sistema
    CIU["👤 Ciudadano Afectado<br/>(PWA con IndexedDB)"]
    BRIG["👷 Brigadista en Campo<br/>(PWA / App Móvil)"]
    COE["🏢 Coordinador COE / Defensa Civil<br/>(Dashboard Web)"]

    %% Capa perimetral de red
    subgraph EDGE["Capa Perimetral & Proxy"]
        NGX["Reverse Proxy Nginx<br/>(SSL + Rate Limiting + Gzip)"]
    end

    %% Núcleo del Monolito Modular
    subgraph MONOLITH["SismoReporta AQP — Monolito Modular Asíncrono (Un solo despliegue en VPS)"]
        direction TB
        
        subgraph PRESENTATION["Capa de Presentación & API Gateway Interno"]
            API["FastAPI REST / WebSocket Gateway<br/>(Validación de Schemas Pydantic)"]
        end

        subgraph MODULES["Módulos de Dominio (Bounded Contexts)"]
            direction LR
            M_INGEST["📥 Ingesta & Sync<br/>(Ack Inmediato + Idempotencia)"]
            M_TRIAGE["⚖️ Triaje & Severidad<br/>(Priorización Automática)"]
            M_DISPATCH["🚑 Despacho & Brigadas<br/>(Asignación por Proximidad)"]
            M_GIS["🗺️ GIS & Mapa de Calor<br/>(Clustering & Geocercas)"]
            M_NOTIF["📢 Notificaciones<br/>(Alertas Masivas Zonales)"]
        end

        subgraph WORKERS["Procesamiento Asíncrono en Background"]
            ASYNC_WORKERS["Workers Celery / Arq<br/>(Compresión de fotos, Triaje en cola, Deduplicación)"]
        end

        subgraph INFRA_ADAPTERS["Capa de Infraestructura & Adaptadores"]
            REPO["Repositorios de Datos & Adaptadores Externos"]
        end
    end

    %% Capa de Almacenamiento y Persistencia
    subgraph DATA["Almacenamiento & Colas"]
        REDIS[("⚡ Redis en Memoria<br/>(Cola de Ingesta Masiva + Caché de Mapa)")]
        POSTGIS[("🐘 PostgreSQL + PostGIS<br/>(Esquemas aislados por módulo + Índices R-Tree)")]
        MINIO[("📦 MinIO / Almacenamiento Local<br/>(Imágenes de Daños Estructurales)")]
    end

    %% Servicios Externos
    subgraph EXTERNAL["Servicios Externos & Respaldo"]
        OSM["🌍 OpenStreetMap / Tile Server<br/>(Cartografía & Capas Base)"]
        SMS_GW["📲 Gateway SMS / Mensajería Masiva<br/>(Alertas de Evacuación)"]
        INDECI["🏛️ API SINAGERD / INDECI<br/>(Interoperabilidad Gubernamental)"]
    end

    %% Conexiones de actores a capa perimetral
    CIU -->|"1. Envía reporte (Online/Sync)"| NGX
    BRIG -->|"Consulta ruta & actualiza estado"| NGX
    COE -->|"Monitorea mapa & despacha brigadas"| NGX

    %% De proxy a API Gateway
    NGX --> API

    %% De API Gateway a Módulos
    API --> M_INGEST
    API --> M_TRIAGE
    API --> M_DISPATCH
    API --> M_GIS
    API --> M_NOTIF

    %% Flujo asíncrono de Ingesta hacia Redis
    M_INGEST -->|"Encola evento bruto (HTTP 202 Ack)"| REDIS
    REDIS -->|"Consume ráfaga de reportes"| ASYNC_WORKERS

    %% Workers procesan con módulos
    ASYNC_WORKERS --> M_TRIAGE
    ASYNC_WORKERS --> M_GIS

    %% Módulos hacia capa de infraestructura
    M_INGEST & M_TRIAGE & M_DISPATCH & M_GIS & M_NOTIF --> REPO

    %% Conexiones de persistencia
    REPO --> POSTGIS
    REPO --> REDIS
    ASYNC_WORKERS -->|"Guarda fotos comprimidas"| MINIO

    %% Conexiones con servicios externos
    REPO -->|"Consulta tiles"| OSM
    REPO -->|"Envía broadcast"| SMS_GW
    REPO -->|"Sincroniza emergencias"| INDECI

    %% Estilos visuales
    classDef usr fill:#E3F2FD,stroke:#1565C0,stroke-width:2px,color:#0D47A1;
    classDef edge fill:#ECEFF1,stroke:#455A64,stroke-width:2px,color:#263238;
    classDef mod fill:#E8F5E9,stroke:#2E7D32,stroke-width:2px,color:#1B5E20;
    classDef worker fill:#FFF3E0,stroke:#E65100,stroke-width:2px,color:#BF360C;
    classDef db fill:#F3E5F5,stroke:#7B1FA2,stroke-width:2px,color:#4A148C;
    classDef ext fill:#FBE9E7,stroke:#D84315,stroke-width:1.5px,stroke-dasharray: 4 3,color:#BF360C;

    class CIU,BRIG,COE usr;
    class NGX edge;
    class M_INGEST,M_TRIAGE,M_DISPATCH,M_GIS,M_NOTIF mod;
    class ASYNC_WORKERS worker;
    class REDIS,POSTGIS,MINIO db;
    class OSM,SMS_GW,INDECI ext;
```

---

## Decisiones Arquitectónicas (ADRs)
- [ADR-001: Adopción de Monolito Modular Asíncrono con Colas en Memoria](docs/architecture/adr/001-estilo-arquitectonico.md)
- [ADR-002: Estrategia de Cliente Offline-First mediante PWA con Service Workers e IndexedDB](docs/architecture/adr/002-estrategia-offline-pwa.md)
- [ADR-003: Selección de PostgreSQL con Extensión Espacial PostGIS para Persistencia y Análisis Geoespacial](docs/architecture/adr/003-base-de-datos-postgis.md)

---

## Modelado y Diagramas del Sistema
* **Drivers y Escenarios de Calidad:** [docs/architecture/drivers.md](docs/architecture/drivers.md)
* **Matriz de Decisión Ponderada:** [docs/architecture/matriz-decision.md](docs/architecture/matriz-decision.md)
* **Diagrama de Arquitectura Elegida (Mermaid):** [docs/architecture/diagramas/arquitectura.mmd](docs/architecture/diagramas/arquitectura.mmd)
* **Alternativa B Descartada (PlantUML):** [docs/architecture/diagramas/alternativa.puml](docs/architecture/diagramas/alternativa.puml)
* **Vista de Despliegue de Infraestructura (Python Diagrams):** [docs/architecture/diagramas/despliegue.py](docs/architecture/diagramas/despliegue.py)
* **Vista de Despliegue en PlantUML:** [docs/architecture/diagramas/despliegue.puml](docs/architecture/diagramas/despliegue.puml)
* **Bitácora de Uso Crítico de IA:** [docs/architecture/bitacora-ia.md](docs/architecture/bitacora-ia.md)
* **Respuestas al Cuestionario Teórico:** [CUESTIONARIO.md](CUESTIONARIO.md)

---

## Reflexión sobre el uso de la IA (5 a 8 líneas)
Los asistentes de Inteligencia Artificial demostraron una gran agilidad para generar esqueletos de diagramas en sintaxis de código y redactar borradores iniciales de escenarios y ADRs. Sin embargo, su tendencia a recomendar por defecto soluciones hipercomplejas de moda (como microservicios serverless en AWS o clústeres de Kubernetes) requirió una postura crítica constante por parte del equipo para rechazar propuestas incompatibles con nuestro presupuesto de un único VPS y el plazo límite de 1 mes. Asimismo, la IA introdujo inconsistencias en capacidades reales de los navegadores (como asegurar falsamente soporte total de Background Sync en Safari iOS), lo que reforzó nuestro aprendizaje de contrastar siempre cada afirmación técnica contra la documentación oficial de ingeniería. En conclusión, la IA es un acelerador productivo excepcional para explorar opciones, pero el juicio arquitectónico final, la verificación empírica y la asunción de compromisos corresponden exclusivamente a los ingenieros.
