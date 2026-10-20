# Cuestionario Oficial de Laboratorio 06: Modelo C4
**Construcción de Software · EPIS-UNSA · Semestre 2026-B · Grupo 08**  
Docente: Mg. Antonio Arroyo Paz  
Integrantes: Santiago Palma (`spalmaa@unsa.edu.pe`), Dario Rafael Cornejo Hurtado (`dcornejohu@unsa.edu.pe`)

---

### 1. ¿Qué problema de los diagramas tradicionales de "cajas y flechas" resuelve el modelo C4? Dé un ejemplo de ambigüedad que haya evitado en su caso.

**Respuesta:**  
Los diagramas tradicionales de "cajas y flechas" adolecen de severa ambigüedad semántica: carecen de una jerarquía de abstracción definida (mezclan capas lógicas de código con servidores físicos en el mismo gráfico), omiten la tecnología y los protocolos de red, y utilizan flechas genéricas rotuladas como "usa" o "se conecta" sin especificar la dirección de los datos ni la intención funcional del conector.

**Ejemplo en SismoReporta AQP:**  
En un diagrama informal, una caja rotulada simplemente como *"Servicio de Mapas"* conectada con una flecha bidireccional a la aplicación no aclara si se trata de un componente interno desarrollado por el equipo (como un motor SIG en Python), una base de datos geoespacial local, o una API externa de terceros consumida bajo demanda. El modelo C4 resolvió esto de forma unívoca:
- En **Nivel 1 (Contexto)**, se definió `Servicio de Mapas y Teselas` explícitamente como un **Sistema Externo** (`softwareSystem ... "Externo"`), estableciendo que se encuentra fuera del límite de responsabilidad del equipo y especificando la intención: *"Descarga teselas y capas cartográficas base desde"* vía `HTTPS/Tiles`.
- En **Nivel 2 (Contenedores)**, se diferenció nítidamente dicho servicio externo del contenedor interno `Base de Datos Geoespacial` (`PostgreSQL 16, PostGIS`), dejando en claro qué datos residen bajo control transaccional del monolito y cuáles son consumidos vía CDN.

---

### 2. ¿Qué es un "contenedor" en C4 y por qué no equivale a un contenedor Docker? Indique un contenedor de su caso que no se ejecute en Docker.

**Respuesta:**  
En el modelo C4, un **contenedor** se define como una unidad de software ejecutable y desplegable de forma independiente, o un almacén de datos (como una base de datos relacional, un sistema de archivos o un esquema en memoria) que aloja código o datos y forma parte integral de la arquitectura del sistema.  

No equivale a un contenedor Docker porque Docker es una tecnología específica de virtualización a nivel de sistema operativo (infraestructura de ejecución), mientras que el contenedor C4 es una **abstracción arquitectónica y lógica**. Un contenedor C4 puede ejecutarse dentro de un contenedor Docker, pero también puede ser un ejecutable nativo en bare-metal, una aplicación móvil instalada en un smartphone, una función serverless o una base de datos administrada en la nube (DBaaS).

**Ejemplo en SismoReporta AQP:**  
El contenedor `PWA Cliente Offline` (`TypeScript, React, PWA, IndexedDB`) **no se ejecuta en Docker**. Es una aplicación que corre directamente en el dispositivo móvil del ciudadano o brigadista, interpretada por el motor del navegador web local (V8 / WebKit) y respaldada por la API de almacenamiento local del cliente (`IndexedDB`). Tratarlo como un contenedor Docker sería un error conceptual de infraestructura.

---

### 3. ¿Qué público y qué nivel de detalle tiene cada uno de los cuatro niveles de C4? ¿Por qué rara vez se dibuja el nivel 4 a mano?

**Respuesta:**  

| Nivel C4 | Nivel de Detalle Arquitectónico | Público Objetivo Primario |
| :--- | :--- | :--- |
| **Nivel 1: Contexto (System Context)** | Vista satelital del sistema, mostrando actores (personas) y dependencias con sistemas externos sin detalles técnicos internos. | Autoridades de gestión, líderes de proyectos, evaluadores de negocio y usuarios no técnicos. |
| **Nivel 2: Contenedores (Container)** | Muestra la forma de la arquitectura: aplicaciones web/móviles, APIs backend, brokers y bases de datos con sus tecnologías y protocolos. | Arquitectos de software, desarrolladores del equipo, personal de DevOps y soporte de infraestructura. |
| **Nivel 3: Componentes (Component)** | Zoom interno sobre un contenedor específico, mostrando sus módulos de código, controladores, servicios y dependencias lógicas. | Desarrolladores de software que implementarán o modificarán código dentro de dicho contenedor. |
| **Nivel 4: Código (Code)** | Diagramas de clases UML, diagramas de entidad-relación o estructuras de datos a nivel de métodos y atributos. | Ingenieros de software y redactores de pruebas unitarias que requieren precisión milimétrica de código. |

**Por qué rara vez se dibuja el Nivel 4 a mano:**  
El nivel de código presenta una tasa de cambio (volatilidad) extremadamente acelerada: cualquier refactorización, cambio de firma en una función o adición de atributos deja obsoleto un diagrama manual en cuestión de días o semanas. Dibujarlo a mano representa un desperdicio de esfuerzo de ingeniería (*overhead*). Por ello, las mejores prácticas de la industria estipulan que el nivel 4 debe generarse de manera automatizada bajo demanda a partir del código fuente mediante herramientas de ingeniería inversa (como `pyreverse`, herramientas integradas en IDEs o plugins de compilación).

---

### 4. Compare la vista dinámica de C4 con el diagrama de secuencia UML de su flujo crítico. ¿Cuándo usaría cada una?

**Respuesta:**  

* **Diferencias Estructurales y de Abstracción:**  
  La vista dinámica C4 (`SincronizacionOffline`) modela la interacción entre **contenedores macro** del sistema (`pwaCliente`, `proxyNginx`, `apiBackend`, `brokerRedis`, `workerAsincrono`), concentrándose en el flujo de la información, el orden cronológico de red y los protocolos de transporte (`HTTPS`, `RESP`, `SQL/TCP`). En cambio, el diagrama de secuencia UML (`docs/design/secuencia-sincronizar-reporte.puml`) desciende a nivel de **clases e instancias de código** (`SyncController`, `ServicioSincronizacion`, `Reporte`, `IRepositorioReportes`), documentando bifurcaciones lógicas (`alt/else`), bucles de procesamiento (`loop`) y llamadas locales sincrónicas y asíncronas.

* **Criterio de Uso:**  
  - **Usaría la Vista Dinámica C4:** En sesiones de revisión de diseño de sistemas, auditorías de escalabilidad, análisis de resiliencia con el equipo de DevOps/SRE y explicaciones técnicas de alto nivel para justificar cómo el sistema absorbe picos de 20,000 peticiones sin colapsar.
  - **Usaría el Diagrama de Secuencia UML:** Durante la fase de construcción de código fuente, diseño de pruebas unitarias y de integración (*mocking*), y resolución de errores (*debugging*) donde se necesita garantizar que los controladores invoquen los métodos adecuados en las entidades de dominio y respeten la máquina de estados.

---

### 5. ¿Qué ventaja concreta tiene modelar con Structurizr DSL frente a dibujar cada vista con C4-PlantUML o Mermaid?

**Respuesta:**  
La ventaja fundamental radica en el principio de **Fuente Única de Verdad (Single Source of Truth - SSoT)**.  

Al utilizar Structurizr DSL, se construye un **modelo relacional abstracto centralizado**: las personas, contenedores, componentes y sistemas externos se definen exactamente una vez dentro del bloque `model`. A partir de dicha definición única, el compilador infiere y proyecta automáticamente las distintas vistas (`systemContext`, `container`, `component`, `dynamic`, `deployment`).  

Si se dibujara cada vista por separado en archivos C4-PlantUML o Mermaid:
1. Existiría duplicación masiva de código visual y alto riesgo de inconsistencia sintáctica (por ejemplo, alterar la descripción de un contenedor en una vista y olvidar actualizarla en las otras tres).
2. Si un componente o tecnología cambia, en Structurizr DSL basta con modificar una sola línea del modelo y compilar con `structurizr.sh export` para regenerar todos los diagramas de manera idéntica y sincronizada.
3. El compilador de Structurizr DSL provee **análisis semántico y tipado estricto** (`validate`), impidiendo relaciones hacia elementos inexistentes, enlaces huérfanos o violaciones en la jerarquía de abstracción (como referenciar un componente en una vista de contexto).

---

### 6. ¿Qué elementos del modelo C4 de su caso se justifican con el ADR-001 del Laboratorio 04? Cite al menos dos.

**Respuesta:**  
El documento `ADR-001: Adopción de Monolito Modular Asíncrono con Colas en Memoria` fundamenta directamente las siguientes decisiones modeladas en el C4:

1. **El contenedor `Buffer y Broker de Colas` (`Redis 7`):**  
   *Justificación en el ADR-001:* Para satisfacer el atributo de calidad crítico **QA-01 (Disponibilidad y Rendimiento)** ante ráfagas masivas de 20,000 reportes en la primera hora post-sismo, el ADR prohíbe la persistencia relacional síncrona inmediata en el endpoint HTTP. Se definió Redis como un amortiguador de ráfagas (*shock-absorber*) en memoria que recibe el evento y permite que el contenedor `API Backend` emita una respuesta `HTTP 202 Accepted` en menos de 100 ms (cumpliendo $p95 \le 1.5\text{ s}$ de QA-02), desacoplando la ingesta de las tareas pesadas de base de datos.

2. **La separación entre el contenedor `API Backend Monolítico` y el contenedor `Worker de Procesamiento Asíncrono` (`Celery`):**  
   *Justificación en el ADR-001:* El ADR estipuló que las operaciones intensivas en CPU y disco —tales como la compresión de imágenes de colapsos estructurales, la deduplicación espacial mediante algoritmos PostGIS y el triaje automático— deben ejecutarse fuera de los hilos de atención HTTP. En el modelo C4, esto se traduce en dos contenedores de software diferenciados comunicados asíncronamente mediante Redis RESP, protegiendo al monolito de la degradación por saturación de hilos.

---

### 7. Describa un error de la IA al generar o revisar su modelo C4 y cómo lo detectó con la lista de revisión.

**Respuesta:**  
Durante la generación inicial del borrador del modelo mediante el Prompt IA 1, la Inteligencia Artificial incluyó dentro de los límites del sistema `sismoReporta` un contenedor denominado `"Docker Compose"` y ubicó al servicio de cartografía como una base de datos interna.  

**Cómo se detectó mediante la lista de revisión:**  
Al aplicar la **Lista de Revisión Oficial (Tabla 3 de la guía - Grupo Elementos)**, la pregunta clave establece:  
> *"¿Cada elemento tiene nombre, tipo (persona, sistema, contenedor o componente), descripción de lo que hace y, si corresponde, tecnología? ¿Se entiende claramente su rol arquitectónico sin confundir infraestructura con software?"*  

Al someter la propuesta a esta pregunta, se evidenció que:
1. `Docker Compose` no aloja lógica de negocio ni representa un almacén de datos; es una herramienta de orquestación de infraestructura. Su lugar correcto en el modelo C4 es un **nodo de despliegue** (`deploymentNode`), no un contenedor de software.
2. El servicio de mapas no es desarrollado, desplegado ni mantenido por el equipo; es un servicio de terceros. Su categoría formal es **Sistema Externo** (`softwareSystem ... "Externo"`).  
Ambos errores fueron corregidos inmediatamente en el archivo `workspace.dsl`, garantizando la estricta pureza arquitectónica del modelo.

---

### 8. ¿Cómo adaptaría la explicación de su arquitectura para un docente evaluador, un inversionista y un nuevo developer del equipo?

**Respuesta:**  

* **Para el Docente Evaluador (Enfoque Teórico-Práctico, Normativo y de Consistencia):**  
  *"SismoReporta AQP adopta una arquitectura de Monolito Modular Asíncrono respaldada formalmente por los ADR-001, ADR-002 y ADR-003. El diseño mitiga el colapso de red mediante persistencia offline en PWA (IndexedDB) y amortiguación en memoria con Redis para absorber ráfagas extremas de 20,000 incidentes. El modelo C4 se estructuró como una fuente única de verdad en Structurizr DSL, demostrando aciclicidad estricta entre los módulos de dominio (C4), coherencia con los diagramas de paquetes UML del Lab 05 y conformidad total con la lista de calidad de Simon Brown."*

* **Para un Inversionista / Patrocinador Institucional (Enfoque de Impacto, Costo-Beneficio y Viabilidad):**  
  *"SismoReporta AQP es la solución tecnológica más costo-eficiente para coordinar el auxilio ciudadano tras terremotos en el sur del país. Con una inversión mínima de infraestructura en la nube (menos de 20 dólares al mes), la plataforma garantiza cero reportes perdidos, operando incluso si los teléfonos no tienen señal. Esto permite a Defensa Civil optimizar el desplazamiento de brigadas y salvar vidas en las horas críticas, logrando un MVP listo para producción en tan solo un mes de desarrollo."*

* **Para un Nuevo Desarrollador del Equipo (Enfoque de Implementación, Stack y Flujo de Trabajo):**  
  *"Bienvenido al proyecto. Trabajamos con una PWA en React/TypeScript que guarda todo en IndexedDB cuando se pierde la conexión. El backend es un monolito modular en FastAPI con esquemas Pydantic y PostgreSQL/PostGIS para cálculo geoespacial. Cuando un usuario envía un reporte, la API lo valida rápido y lo manda a una cola de Redis con HTTP 202; los workers en Celery se encargan de comprimir las fotos y calcular la severidad en segundo plano. Toda la arquitectura está versionada en `docs/architecture/c4/workspace.dsl`: compílala con `structurizr.sh` antes de subir cualquier commit para asegurar consistencia."*
