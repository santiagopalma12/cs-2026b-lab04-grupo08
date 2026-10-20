# SismoReporta AQP — Plataforma de Gestión y Coordinación de Emergencias
**Construcción de Software · EPIS-UNSA · 2026-B · Grupo 08**  
Docente: Mg. Antonio Arroyo Paz

---

## Integrantes
| Nombre | Usuario GitHub | Correo Institucional | Rol en los Laboratorios |
| :--- | :---: | :---: | :--- |
| **Santiago Palma** | `@santiagopalma12` | `spalmaa@unsa.edu.pe` | Arquitecto de Software, Diagramador (Mermaid, Diagrams, Structurizr DSL), Autor de ADRs, Modelado de Clases y Secuencia. |
| **Dario Rafael Cornejo Hurtado** | `@darich1010` | `dcornejohu@unsa.edu.pe` | Especialista en Resiliencia y Datos, Diagramador C4-PlantUML, Auditor de Consistencia C1–C5 y Lista Oficial C4, Verificador de IA. |

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
    CIU["Ciudadano Afectado<br/>(PWA con IndexedDB)"]
    BRIG["Brigadista en Campo<br/>(PWA / App Movil)"]
    COE["Coordinador COE / Defensa Civil<br/>(Dashboard Web)"]

    %% Capa perimetral de red
    subgraph EDGE["Capa Perimetral & Proxy"]
        NGX["Reverse Proxy Nginx<br/>(SSL + Rate Limiting + Gzip)"]
    end

    %% Núcleo del Monolito Modular
    subgraph MONOLITH["SismoReporta AQP — Monolito Modular Asincrono (Un solo despliegue en VPS)"]
        direction TB
        
        subgraph PRESENTATION["Capa de Presentacion & API Gateway Interno"]
            API["FastAPI REST / WebSocket Gateway<br/>(Validacion de Schemas Pydantic)"]
        end

        subgraph MODULES["Modulos de Dominio (Bounded Contexts)"]
            direction LR
            M_INGEST["Ingesta & Sync<br/>(Ack Inmediato + Idempotencia)"]
            M_TRIAGE["Triaje & Severidad<br/>(Priorizacion Automatica)"]
            M_DISPATCH["Despacho & Brigadas<br/>(Asignacion por Proximidad)"]
            M_GIS["GIS & Mapa de Calor<br/>(Clustering & Geocercas)"]
            M_NOTIF["Notificaciones<br/>(Alertas Masivas Zonales)"]
        end

        subgraph WORKERS["Procesamiento Asincrono en Background"]
            ASYNC_WORKERS["Workers Celery / Arq<br/>(Compresion de fotos, Triaje en cola, Deduplicacion)"]
        end

        subgraph INFRA_ADAPTERS["Capa de Infraestructura & Adaptadores"]
            REPO["Repositorios de Datos & Adaptadores Externos"]
        end
    end

    %% Capa de Almacenamiento y Persistencia
    subgraph DATA["Almacenamiento & Colas"]
        REDIS[("Redis en Memoria<br/>(Cola de Ingesta Masiva + Cache de Mapa)")]
        POSTGIS[("PostgreSQL + PostGIS<br/>(Esquemas aislados por modulo + Indices R-Tree)")]
        MINIO[("MinIO / Almacenamiento Local<br/>(Imagenes de Daños Estructurales)")]
    end

    %% Servicios Externos
    subgraph EXTERNAL["Servicios Externos & Respaldo"]
        OSM["OpenStreetMap / Tile Server<br/>(Cartografia & Capas Base)"]
        SMS_GW["Gateway SMS / Mensajeria Masiva<br/>(Alertas de Evacuacion)"]
        INDECI["API SINAGERD / INDECI<br/>(Interoperabilidad Gubernamental)"]
    end

    %% Conexiones de actores a capa perimetral
    CIU -->|"1. Envia reporte (Online/Sync)"| NGX
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
    REDIS -->|"Consume rafaga de reportes"| ASYNC_WORKERS

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
    REPO -->|"Envia broadcast"| SMS_GW
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

---

## Diseño UML (Lab 05)

En este laboratorio se profundiza el diseño detallado del sistema mediante el paradigma **UML como Código (Diagram as Code)** versionado en Git, aplicando ingeniería directa e inversa con soporte crítico de Inteligencia Artificial y auditoría mediante las reglas de consistencia C1–C5.

### Entregables del Laboratorio
* **E1: Historia de Usuario y Diagrama de Clases:**  
  * Documento de Historia: [`docs/design/historia.md`](docs/design/historia.md)
  * Código PlantUML: [`docs/design/clases.puml`](docs/design/clases.puml)
  * Imagen Renderizada: [`docs/design/img/clases.png`](docs/design/img/clases.png)
* **E2: Diagrama de Secuencia del Flujo Crítico:**  
  * Código PlantUML: [`docs/design/secuencia-sincronizar-reporte.puml`](docs/design/secuencia-sincronizar-reporte.puml)
  * Imagen Renderizada: [`docs/design/img/secuencia-sincronizar-reporte.png`](docs/design/img/secuencia-sincronizar-reporte.png)
* **E3: Diagrama de Máquina de Estados:**  
  * Código Mermaid: [`docs/design/estados-reporte.mmd`](docs/design/estados-reporte.mmd)
  * Imagen Renderizada: [`docs/design/img/estados-reporte.png`](docs/design/img/estados-reporte.png)
* **E4: Diagrama de Actividades de Procesos:**  
  * Código PlantUML: [`docs/design/actividades-priorizar-asignar.puml`](docs/design/actividades-priorizar-asignar.puml)
  * Imagen Renderizada: [`docs/design/img/actividades-priorizar-asignar.png`](docs/design/img/actividades-priorizar-asignar.png)
* **E5: Diagrama de Paquetes Modulares:**  
  * Código PlantUML: [`docs/design/paquetes.puml`](docs/design/paquetes.puml)
  * Imagen Renderizada: [`docs/design/img/paquetes.png`](docs/design/img/paquetes.png)
* **E6: Round-Trip con IA e Ingeniería Inversa:**  
  * Código Fuente en Python: [`src/sismoreporta/dominio.py`](src/sismoreporta/dominio.py)
  * Diagrama Obtenido por Pyreverse: [`docs/design/classes_sismoreporta.puml`](docs/design/classes_sismoreporta.puml)
  * Imagen de Ingeniería Inversa: [`docs/design/img/classes_sismoreporta.png`](docs/design/img/classes_sismoreporta.png)
  * Análisis de Diferencias: [`docs/design/round-trip.md`](docs/design/round-trip.md)
* **E7: Auditoría de Consistencia y Bitácora de IA:**  
  * Matriz de Verificación C1–C5: [`docs/design/consistencia.md`](docs/design/consistencia.md)
  * Bitácora de Prompts e Interacciones Críticas: [`docs/design/bitacora-ia.md`](docs/design/bitacora-ia.md)
* **Cuestionario Teórico-Práctico:**  
  * Solución a las 8 Preguntas: [`CUESTIONARIO.md`](CUESTIONARIO.md)
* **Informe Formal:**  
  * Documento Typst compilable: [`informe_lab05.typ`](informe_lab05.typ)
  * Documento PDF final: [`informe_lab05.pdf`](informe_lab05.pdf)

---

### Diagrama de Máquina de Estados Embebido (E3 — Mermaid)

```mermaid
stateDiagram-v2
    [*] --> BORRADOR : guardarBorrador()
    
    BORRADOR --> ENCOLADO : encolarOffline() [sin conexion de red]
    BORRADOR --> RECIBIDO : sincronizar() [conexion de red disponible]
    
    ENCOLADO --> RECIBIDO : sincronizar(fecha) [senal detectada y geocerca valida]
    ENCOLADO --> DESCARTADO : descartar(motivo) [fuera de perimetro provincial]
    
    RECIBIDO --> VERIFICADO : verificarTriaje(score) [scorePrioridad >= 0.70]
    RECIBIDO --> DESCARTADO : descartar("duplicado") [reporte duplicado < 50m]
    
    VERIFICADO --> ATENDIDO : atenderIncidente() [brigada reporta mision cumplida]
    
    ATENDIDO --> [*]
    DESCARTADO --> [*]

    note right of ENCOLADO
        Persistido localmente en IndexedDB
        del dispositivo movil del ciudadano
    end note

    note right of RECIBIDO
        Al entrar: Almacenar en PostgreSQL
        y encolar en Redis para triaje
    end note

    note right of VERIFICADO
        Al entrar: Clasificado por severidad
        y visible en mapa de calor COE
    end note
```

---

## Arquitectura C4 (Lab 06)

En este laboratorio se consolida la arquitectura del sistema mediante el **Modelo C4** y el paradigma de **Arquitectura como Código (Architecture as Code - AaC)** utilizando un modelo único y centralizado en **Structurizr DSL**, del cual se derivan coherentemente todas las vistas visuales hacia **C4-PlantUML** y **Mermaid**.

### Entregables del Laboratorio
* **E1: Inventario de Elementos y Diagrama de Contexto:**
  * Inventario de Elementos y Trazabilidad: [`docs/architecture/c4/inventario.md`](docs/architecture/c4/inventario.md)
  * Modelo Central en Structurizr DSL: [`docs/architecture/c4/workspace.dsl`](docs/architecture/c4/workspace.dsl)
  * Vista de Contexto (PlantUML): [`docs/architecture/c4/export/structurizr-Contexto.puml`](docs/architecture/c4/export/structurizr-Contexto.puml)
  * Imagen Renderizada: [`docs/architecture/c4/img/structurizr-Contexto.png`](docs/architecture/c4/img/structurizr-Contexto.png)
* **E2: Diagrama de Contenedores:**
  * Vista de Contenedores (PlantUML): [`docs/architecture/c4/export/structurizr-Contenedores.puml`](docs/architecture/c4/export/structurizr-Contenedores.puml)
  * Imagen Renderizada: [`docs/architecture/c4/img/structurizr-Contenedores.png`](docs/architecture/c4/img/structurizr-Contenedores.png)
* **E3: Diagrama de Componentes del API Backend:**
  * Vista de Componentes (PlantUML): [`docs/architecture/c4/export/structurizr-Componentes.puml`](docs/architecture/c4/export/structurizr-Componentes.puml)
  * Imagen Renderizada: [`docs/architecture/c4/img/structurizr-Componentes.png`](docs/architecture/c4/img/structurizr-Componentes.png)
* **E4: Vista Dinámica del Flujo Crítico de Sincronización:**
  * Vista Dinámica (PlantUML): [`docs/architecture/c4/export/structurizr-SincronizacionOffline.puml`](docs/architecture/c4/export/structurizr-SincronizacionOffline.puml)
  * Imagen Renderizada: [`docs/architecture/c4/img/structurizr-SincronizacionOffline.png`](docs/architecture/c4/img/structurizr-SincronizacionOffline.png)
  * Comparación Secuencia UML vs Dinámica C4: [`docs/architecture/c4/comparacion.md`](docs/architecture/c4/comparacion.md)
* **E5: Vista de Despliegue en Producción:**
  * Vista de Despliegue (PlantUML): [`docs/architecture/c4/export/structurizr-Despliegue.puml`](docs/architecture/c4/export/structurizr-Despliegue.puml)
  * Imagen Renderizada: [`docs/architecture/c4/img/structurizr-Despliegue.png`](docs/architecture/c4/img/structurizr-Despliegue.png)
* **E6: Exportación Multiformato y Comparación de Herramientas:**
  * Diagrama de Contexto Escrito a Mano: [`docs/architecture/c4/contexto-manual.puml`](docs/architecture/c4/contexto-manual.puml)
  * Imagen Renderizada del Contexto Manual: [`docs/architecture/c4/img/contexto-manual.png`](docs/architecture/c4/img/contexto-manual.png)
  * Análisis Comparativo (Manual vs DSL Centralizado): [`docs/architecture/c4/comparacion.md`](docs/architecture/c4/comparacion.md)
* **E7: Auditoría de Calidad Oficial, Explicación y Bitácora de IA:**
  * Lista de Revisión Oficial C4 y Falso Positivo: [`docs/architecture/c4/revision-c4.md`](docs/architecture/c4/revision-c4.md)
  * Explicación Ejecutiva No Técnica (<= 120 palabras): [`docs/architecture/c4/explicacion.md`](docs/architecture/c4/explicacion.md)
  * Bitácora de 5+ Interacciones con IA: [`docs/architecture/c4/bitacora-ia.md`](docs/architecture/c4/bitacora-ia.md)
* **E8: Cuestionario e Informe Formal:**
  * Solución al Cuestionario de 8 Preguntas: [`CUESTIONARIO.md`](CUESTIONARIO.md)
  * Documento Typst Compilable: [`informe_lab06.typ`](informe_lab06.typ)
  * Documento PDF Final: [`informe_lab06.pdf`](informe_lab06.pdf)

---

### Diagrama de Contexto Embebido (E8 — Mermaid exportado desde Structurizr DSL)

```mermaid
graph LR
  linkStyle default fill:#ffffff

  subgraph diagram ["System Context View: SismoReporta AQP"]
    style diagram fill:#ffffff,stroke:#ffffff

    1["<div style='font-weight: bold'>Ciudadano Afectado</div><div style='font-size: 70%; margin-top: 0px'>[Person]</div><div style='font-size: 80%; margin-top:10px'>Habitante de la región<br />Arequipa que reporta daños<br />estructurales, personas<br />atrapadas o vías colapsadas<br />mediante fotografías y GPS.</div>"]
    style 1 fill:#08427b,stroke:#052e56,color:#ffffff
    2["<div style='font-weight: bold'>Brigadista en Campo</div><div style='font-size: 70%; margin-top: 0px'>[Person]</div><div style='font-size: 80%; margin-top:10px'>Personal de rescate<br />(Bomberos, Cruz Roja, Defensa<br />Civil) que recibe órdenes de<br />auxilio y actualiza la<br />atención de víctimas en<br />tiempo real.</div>"]
    style 2 fill:#08427b,stroke:#052e56,color:#ffffff
    3["<div style='font-weight: bold'>Coordinador del COE</div><div style='font-size: 70%; margin-top: 0px'>[Person]</div><div style='font-size: 80%; margin-top:10px'>Operador de Defensa Civil y<br />COE que evalúa el mapa de<br />calor de incidentes, prioriza<br />severidades críticas y<br />despacha brigadas de rescate.</div>"]
    style 3 fill:#08427b,stroke:#052e56,color:#ffffff
    4["<div style='font-weight: bold'>Servicio de Mapas y Teselas</div><div style='font-size: 70%; margin-top: 0px'>[Software System]</div><div style='font-size: 80%; margin-top:10px'>Servicio externo de<br />cartografía base y<br />geocodificación<br />(OpenStreetMap / Mapbox<br />Tiles).</div>"]
    style 4 fill:#999999,stroke:#6b6b6b,color:#ffffff
    5["<div style='font-weight: bold'>Pasarela de Alertas SMS / Broadcast</div><div style='font-size: 70%; margin-top: 0px'>[Software System]</div><div style='font-size: 80%; margin-top:10px'>Servicio externo de<br />telecomunicaciones para<br />difusión masiva de alertas<br />tempranas y órdenes de<br />evacuación.</div>"]
    style 5 fill:#999999,stroke:#6b6b6b,color:#ffffff
    6["<div style='font-weight: bold'>SismoReporta AQP</div><div style='font-size: 70%; margin-top: 0px'>[Software System]</div><div style='font-size: 80%; margin-top:10px'>Plataforma ciudadana y de<br />coordinación de emergencias<br />post-sismo con soporte de<br />funcionamiento sin conexión y<br />sincronización diferida<br />masiva.</div>"]
    style 6 fill:#1168bd,stroke:#0b4884,color:#ffffff

    1-. "<div>Registra reportes de daños<br />estructurales y personas<br />atrapadas en</div><div style='font-size: 70%'></div>" .->6
    2-. "<div>Consulta órdenes de auxilio y<br />actualiza estado de rescate<br />en</div><div style='font-size: 70%'></div>" .->6
    3-. "<div>Monitorea mapa de calor y<br />despacha cuadrillas de<br />rescate desde</div><div style='font-size: 70%'></div>" .->6
    6-. "<div>Descarga teselas y capas<br />cartográficas base desde</div><div style='font-size: 70%'>[HTTPS/Tiles]</div>" .->4
    6-. "<div>Emite órdenes de evacuación y<br />alertas masivas a través de</div><div style='font-size: 70%'>[HTTPS/REST]</div>" .->5

  end
```

---

## Cómo Reproducir el Proyecto

### 1. Requisitos del Entorno
* Python 3.10+
* OpenJDK 17+ (Java 25 probado)
* Structurizr CLI (`structurizr.sh`) o imagen Docker `structurizr/cli`
* PlantUML y Graphviz (`plantuml.jar` o Docker `plantuml/plantuml`)
* Typst CLI (`typst`)
* Pylint / Pyreverse (`pip install pylint`)

### 2. Validación y Exportación de la Arquitectura C4 (Lab 06)
```bash
# Validar la consistencia semántica del modelo DSL
structurizr.sh validate -w docs/architecture/c4/workspace.dsl

# Exportar el modelo a C4-PlantUML y Mermaid
structurizr.sh export -w docs/architecture/c4/workspace.dsl -f plantuml/c4plantuml -o docs/architecture/c4/export
structurizr.sh export -w docs/architecture/c4/workspace.dsl -f mermaid -o docs/architecture/c4/export

# Renderizar diagramas a imágenes PNG de alta resolución
docker run --rm -v "$PWD":/work -w /work plantuml/plantuml "docs/architecture/c4/export/*.puml" -o ../img/
docker run --rm -v "$PWD":/work -w /work plantuml/plantuml docs/architecture/c4/contexto-manual.puml -o img/
```

### 3. Renderizado de Diagramas UML (Lab 05)
```bash
java -jar plantuml.jar -tpng docs/design/clases.puml -o img/
java -jar plantuml.jar -tpng docs/design/secuencia-sincronizar-reporte.puml -o img/
java -jar plantuml.jar -tpng docs/design/actividades-priorizar-asignar.puml -o img/
java -jar plantuml.jar -tpng docs/design/paquetes.puml -o img/
java -jar plantuml.jar -tpng docs/design/estados-reporte.puml -o img/
```

### 4. Compilación de Informes Formales en Typst
```bash
# Compilar informe del Laboratorio 05
typst compile informe_lab05.typ informe_lab05.pdf

# Compilar informe del Laboratorio 06
typst compile informe_lab06.typ informe_lab06.pdf
```

