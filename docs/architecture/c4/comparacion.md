# Comparación de Enfoques y Vistas — Laboratorio 06
**Construcción de Software · EPIS-UNSA · Semestre 2026-B · Grupo 08**  
Integrantes: Santiago Palma (`spalmaa@unsa.edu.pe`), Dario Rafael Cornejo Hurtado (`dcornejohu@unsa.edu.pe`)

---

## 1. Comparación entre Secuencia UML y Vista Dinámica C4 (Entregable E4)

El diagrama de secuencia UML (`docs/design/secuencia-sincronizar-reporte.puml`) modela a nivel micro el protocolo de llamadas internas entre objetos y clases (`SyncController`, `ServicioSincronizacion`, `Reporte`, interfaces de puertos), detallando bloques de control algorítmico (`alt`, `loop`, `opt`), activación de líneas de vida y llamadas asíncronas no bloqueantes. En contraste, la vista dinámica C4 (`SincronizacionOffline` en Structurizr DSL) abstrae la interacción a nivel de contenedores macro (`pwaCliente`, `proxyNginx`, `apiBackend`, `brokerRedis`, `workerAsincrono`), omitiendo variables locales y condiciones lógicas internas.

* **Audiencia del Diagrama de Secuencia UML:** Desarrolladores backend, ingenieros de integración y autores de pruebas unitarias que requieren implementar las firmas exactas de métodos y controlar el flujo de ejecución de la máquina de estados.
* **Audiencia de la Vista Dinámica C4:** Arquitectos de sistemas, ingenieros de operaciones (DevOps/SRE) y evaluadores técnicos que necesitan comprender la topología de la ráfaga de datos, los protocolos de red (HTTPS, Redis RESP, SQL/TCP) y el punto exacto de absorción de carga sin abrumarse con la estructura de código fuente.

---

## 2. Comparación entre Modelado Único (Structurizr DSL) y Diagramado Manual (C4-PlantUML) (Entregable E6)

A continuación se evalúa de manera comparativa la experiencia de construir la arquitectura mediante un modelo formal centralizado en Structurizr DSL frente a la redacción artesanal de diagramas independientes en C4-PlantUML (`contexto-manual.puml`):

| Dimensión de Análisis | Diagramación Manual (C4-PlantUML) | Modelo Único Central (Structurizr DSL) |
| :--- | :--- | :--- |
| **Tiempo Invertido Inicial** | Menor para un diagrama aislado (~10 minutos), pues se escriben directamente las macros `Person`, `System` y `Rel`. | Ligeramente mayor al inicio (~25 minutos) para definir la jerarquía de identificadores, contenedores y componentes en un único archivo. |
| **Tiempo de Mantenimiento Acumulado** | Extremadamente alto. Cada vista (contexto, contenedores, componentes, despliegue) debe duplicar nombres, descripciones y relaciones en archivos separados. | Prácticamente cero en duplicación. Cualquier modificación en un elemento se propaga instantáneamente a todas las vistas derivadas. |
| **Errores Encontrados y Consistencia** | Propensión a incoherencias léxicas (por ejemplo, llamar a la base de datos "PostgreSQL" en contexto y "PostGIS DB" en contenedores). Las relaciones manuales pueden quedar huérfanas sin validación sintáctica cruzada. | El comando de validación del compilador (`structurizr.sh validate`) actúa como un sistema de tipos estático, impidiendo relaciones hacia elementos inexistentes o violaciones de ámbito (como intentar referenciar componentes en vistas de sistema). |
| **Impacto de Renombrar un Contenedor** | Supone una labor manual de búsqueda y reemplazo propensa a omisiones en múltiples ficheros `.puml`, `.mmd` y documentos markdown, con alto riesgo de degradación documental. | Se modifica el identificador o el nombre en una sola línea del bloque `model` en `workspace.dsl`. Al ejecutar `structurizr.sh export`, todas las representaciones (PlantUML, Mermaid, JSON) se regeneran de forma idéntica e inmediata. |
| **Portabilidad y Salidas Multiformato** | Acoplado exclusivamente al motor de renderizado de PlantUML. No permite generar nativamente especificaciones interactivas o exportaciones a Mermaid para Markdown de GitHub. | Agnóstico del renderizador final. Desde una única fuente de verdad se compila a C4-PlantUML, Mermaid nativo para GitHub, Graphviz (DOT) e interfaces interactivas web mediante Structurizr Lite. |

---

## 3. Conclusión Académica

El paradigma de **Arquitectura como Código (AaC)** sustentado en Structurizr DSL supera ampliamente la diagramación gráfica aislada. Permite tratar los artefactos arquitectónicos con el mismo rigor ingenieril del código fuente: control de versiones semántico, validación estricta en pipelines de integración continua y eliminación del desfase entre diseño e implementación.
