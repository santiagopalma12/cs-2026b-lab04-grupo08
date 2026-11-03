// =============================================================================
// INFORME DE LABORATORIO N° 08 - CONSTRUCCIÓN DE SOFTWARE (2026-B)
// EPIS - UNIVERSIDAD NACIONAL DE SAN AGUSTÍN DE AREQUIPA
// =============================================================================

#set page(
  paper: "a4",
  margin: (top: 3.6cm, bottom: 2.2cm, left: 2.2cm, right: 2.2cm),
  header-ascent: 18%,
  header: context [
    #align(center)[
      #table(
        columns: (3.2cm, 1fr, 2.8cm),
        stroke: 0.5pt + rgb("#000000"),
        align: horizon + center,
        inset: (x: 4pt, y: 3pt),
        [#image("sistemas.png", width: 80%)],
        [
          #text(size: 6.5pt, weight: "bold")[UNIVERSIDAD NACIONAL DE SAN AGUSTIN]\
          #text(size: 6pt, weight: "bold")[FACULTAD DE INGENIERÍA DE PRODUCCIÓN Y SERVICIOS]\
          #text(size: 6pt, weight: "bold")[ESCUELA PROFESIONAL DE INGENIERÍA DE SISTEMAS]
        ],
        [#image("abet.png", width: 70%)],

        table.cell(colspan: 3, inset: 2pt)[
          #text(size: 6pt)[*Formato:* Guía de Práctica de Laboratorio / Talleres / Centros de Simulación]
        ],
        [#text(size: 6pt)[*Aprobación:* 2022/03/01]],
        [#text(size: 6pt)[*Código:* GUIA-PRLD-001]],
        [#text(size: 6pt)[*Página:* #counter(page).display()]]
      )
    ]
  ]
)

#set text(font: ("Liberation Serif", "Nimbus Roman"), size: 8.5pt)
#set par(justify: true, leading: 0.55em)

#let institutional-red = rgb("#cf4d36")
#let border-black = 0.5pt + rgb("#000000")

#v(4pt)
#align(center)[
  #text(size: 13pt, weight: "bold")[INFORME DE LABORATORIO N° 08]
  #v(2pt)
  #text(size: 10.5pt, weight: "bold")[CONSTRUCCIÓN DE SOFTWARE]
]
#v(4pt)

// ==========================================
// 1. INFORMACIÓN BÁSICA
// ==========================================
#table(
  columns: (3.2cm, 1.8cm, 2.2cm, 2.6cm, 1.8cm, 1fr),
  stroke: border-black,
  inset: 4pt,
  align: (left + horizon),

  table.cell(colspan: 6, fill: institutional-red, align: center)[
    #text(fill: white, weight: "bold", size: 8.5pt)[INFORMACIÓN BÁSICA]
  ],

  [ASIGNATURA:],
  table.cell(colspan: 5)[Construcción de Software],

  [TÍTULO DE LA PRÁCTICA:],
  table.cell(colspan: 5)[Diseñar la arquitectura guiada por atributos de calidad: árbol de utilidad, ADD, tácticas, evaluación ATAM-lite con IA y fitness functions automatizadas],

  [NÚMERO DE PRÁCTICA:],
  [08],
  [AÑO LECTIVO:],
  [2026B],
  [NRO. SEMESTRE:],
  [VI],

  [FECHA DE PRESENTACIÓN:],
  [31/10/2026],
  [HORA:],
  [23:59],
  [],
  [],

  table.cell(colspan: 3)[
    INTEGRANTE(S):
    - Santiago Enrique Palma Apaza (`spalmaa@unsa.edu.pe`)
    - Dario Rafael Cornejo Hurtado (`dcornejohu@unsa.edu.pe`)
  ],
  table.cell(colspan: 1)[NOTA:],
  table.cell(colspan: 2)[],

  table.cell(colspan: 6)[
    DOCENTE(S):
    Mg. Alexander Javier Benavides Rojas / Mg. Antonio Arroyo Paz
  ]
)

#v(8pt)

// ==========================================
// 2. SOLUCIÓN Y RESULTADOS
// ==========================================
#table(
  columns: (1fr),
  stroke: border-black,
  inset: 6pt,

  table.cell(fill: institutional-red, align: center)[
    #text(fill: white, weight: "bold", size: 8.5pt)[SOLUCIÓN Y RESULTADOS]
  ],

  [
    #v(4pt)
    #text(weight: "bold", size: 9.5pt)[I. MARCO TEÓRICO Y CONCEPTUAL]
    #v(4pt)

    En este laboratorio se aplica el proceso formal de diseño arquitectónico centrado en atributos de calidad, evaluación sistemática de riesgos y protección continua frente a la degradación arquitectónica:

    - *Attribute-Driven Design (ADD 3.0) (Cervantes y Kazman, 2016):* Es un método sistemático en 7 pasos que descompone progresivamente el sistema mediante iteraciones guiadas por los requerimientos arquitecturalmente significativos (ASR). Cada iteración revisa entradas, elige elementos para refinar, evalúa conceptos y tácticas de diseño, genera evidencia cuantitativa y formaliza la decisión mediante un Registro de Decisión Arquitectónica (ADR).
    - *Árbol de Utilidad y Escenarios Medibles (Bass et al., 2021):* Estructura jerárquicamente las necesidades del sistema desde los atributos de calidad raíz hacia escenarios concretos formulados en seis partes (fuente, estímulo, entorno, artefacto, respuesta y medida numérica objetiva), priorizados mediante una tupla bidimensional *(Importancia para el negocio, Dificultad técnica)* en escala High (H), Medium (M), Low (L).
    - *Tácticas Arquitectónicas:* Decisiones de diseño elementales que controlan directamente la respuesta de un atributo de calidad específico. A diferencia de un patrón, una táctica es abstracta e independiente de la implementación:
      - *Rendimiento:* Buffer asíncrono, colas en memoria, respuestas rápidas con Fast ACK, índices espaciales.
      - *Disponibilidad:* Prevención de cascada de fallas mediante Circuit Breaker, almacenamiento persistente Outbox, reintentos con Jitter.
      - *Seguridad:* Control de acceso a nivel de fila (Row-Level Security) forzado en el kernel relacional.
      - *Modificabilidad:* Puertos y adaptadores (Arquitectura Hexagonal) para aislar dependencias volátiles.
    - *Evaluación ATAM y ATAM-lite (Kazman, Klein y Clements, 2000):* Identifica de forma temprana puntos de sensibilidad (parámetros críticos cuyo cambio altera radicalmente un atributo), trade-offs (compromisos entre dos atributos contrapuestos), riesgos (decisiones con probabilidad e impacto de consecuencias negativas) y no-riesgos justificados con evidencia.
    - *Arquitectura Evolutiva y Fitness Functions (Ford, Parsons, Kua y Sadalage, 2022):* Pruebas automatizadas en Integración Continua (CI) que verifican objetivamente que las reglas estructurales (ausencia de ciclos y aislamiento de capas con `import-linter`) y los presupuestos de calidad (latencias y cero pérdidas con `pytest`) no se degraden con el tiempo.
    - *Uso Responsable y Crítico de la IA:* La IA actúa como asesora proponiendo alternativas y asumiendo el rol de evaluador adversario escéptico. El equipo humano decide exclusivamente respaldado por evidencia cuantitativa y refuta afirmaciones o sesgos hacia modas tecnológicas no justificadas.

    #v(8pt)
    #text(weight: "bold", size: 9.5pt)[II. DESARROLLO DE LA PRÁCTICA (CASO 8: SISMOREPORTA AQP)]
    #v(4pt)

    El proyecto *SismoReporta AQP* aborda el escenario de crecimiento crítico establecido en la Tabla 11 de la guía:
    #align(center)[
      #block(
        fill: rgb("#f8f9fa"),
        stroke: 0.5pt + rgb("#ced4da"),
        inset: 6pt,
        radius: 4pt,
        [
          *Detonante de Rediseño (Simulacro Nacional):* \
          _"Recepción de 20 000 reportes ciudadanos en el lapso de 1 hora bajo red móvil congestionada en la provincia de Arequipa (tasa media de 5.56 req/s y ráfagas pico de 28 req/s)."_
        ]
      )
    ]

    === E1. Árbol de Utilidad y Priorización de Escenarios
    A partir de `drivers.md` y del escenario de crecimiento, se elaboró el árbol de utilidad (`docs/architecture/utilidad/arbol.dot` y `.png`) con 8 escenarios estructurados cubriendo Rendimiento, Disponibilidad, Seguridad y Modificabilidad:

    #align(center)[
      #image("docs/architecture/utilidad/arbol.png", width: 95%)
      #text(size: 7.5pt, style: "italic")[Figura 1: Árbol de Utilidad de SismoReporta AQP con 8 escenarios medibles.]
    ]

    #table(
      columns: (1.2cm, 2.2cm, 1fr, 1.8cm),
      stroke: 0.5pt + rgb("#adb5bd"),
      inset: 3pt,
      align: (center + horizon, left + horizon, left + horizon, center + horizon),
      table.cell(fill: rgb("#e9ecef"))[*ID*],
      table.cell(fill: rgb("#e9ecef"))[*Atributo*],
      table.cell(fill: rgb("#e9ecef"))[*Escenario de Calidad y Medida Numérica*],
      table.cell(fill: rgb("#e9ecef"))[*Prioridad*],

      [*QA-01*], [Rendimiento], [20 000 reportes en 1 h en simulacro (pico 28 req/s); respuesta Fast ACK con $"p95" <= 1.5$ s.], [*(H, H)*],
      [*QA-02*], [Disponibilidad], [8% timeouts transitorios y broker caído 20 min; reintento local logrando 0% de pérdida.], [*(H, H)*],
      [*QA-03*], [Disponibilidad], [Caída de hardware o nodo VPS en la nube; recuperación desde snapshots con $"MTTR" <= 15$ min.], [*(H, M)*],
      [*QA-04*], [Seguridad], [Operador municipal consulta API; PostgreSQL RLS garantiza 100% de aislamiento distrital.], [*(H, M)*],
      [*QA-05*], [Modificabilidad], [Integrar nuevo proveedor de mapas (IGN) o sensor sísmico (IGP); esfuerzo $<= 16$ ph.], [*(M, M)*],
      [*QA-06*], [Rendimiento], [Consulta de mapa de calor de intensidad Mercalli con 50k filas; PostGIS GiST con $"p95" <= 500$ ms.], [*(M, L)*],
      [*QA-07*], [Seguridad], [Ráfaga maliciosa de spam/DDoS; rate limiting en NGINX limita peticiones a $< 50$ req/s por IP.], [*(M, M)*],
      [*QA-08*], [Modificabilidad], [Exportación analítica en formato GeoJSON/CAP para SINAGERD/INDECI; desarrollo $<= 8$ ph.], [*(L, L)*]
    )

    *Corrección Justificada a la IA:* La IA propuso inicialmente QA-06 como (H, H). El equipo refutó esta calificación argumentando que el mapa de calor no es el canal crítico de ingesta en tiempo real y que la optimización espacial mediante índices GiST en PostGIS es de baja dificultad técnica, reclasificándolo a (M, L).

    === E2. Iteración 1 de ADD: Rendimiento ante Ingesta Masiva (QA-01)
    - *Objetivo:* Lograr $"p95" <= 1.5$ s ante 28 req/s pico en el VPS (2 vCPU, 4 GB RAM).
    - *Conceptos Evaluados:* (1) Procesamiento síncrono escalado a 8 workers ($"p95" = 50.0$ s a 28 req/s, duplica RAM sin resolver I/O); (2) Microservicios con Kubernetes y Kafka (costo de \$180 USD/mes, inmanejable en 1 mes con 2 devs); (3) Buffer asíncrono en Redis con Fast ACK HTTP 202.
    - *Táctica Adoptada:* *Buffer Asíncrono en Redis + Fast ACK (HTTP 202)* diferiendo validación espacial PostGIS a workers Celery (ADR-006).
    - *Evidencia Cuantitativa (`fitness/rendimiento.py`):* La simulación M/G/c demostró que sin buffer el sistema colapsa ($"p95" = 213.8$ s a 28 req/s), mientras que con la táctica se obtiene *$"p95" = 16.4$ ms* con utilización del buffer de apenas *$rho = 0.07$* (7%).

    #align(center)[
      #image("docs/architecture/diagramas/img/rendimiento.png", width: 90%)
      #text(size: 7.5pt, style: "italic")[Figura 2: Curvas de simulación M/G/c de teoría de colas para Rendimiento (QA-01).]
    ]

    === E3. Evaluación ATAM-lite Cruzada
    El análisis cruzado identificó:
    - *Sensibilidad S1:* El $"p95"$ depende de liberar el socket HTTP tras el encolamiento `LPUSH` sin I/O bloqueante.
    - *Trade-off T1 (Rendimiento vs. Consistencia Eventual):* La ingesta responde en 16 ms, pero el reporte demora 2 s en reflejarse en el mapa del COE.
    - *Riesgo R1 (Memoria Redis):* Caída de workers acumulando reportes en RAM (Mitigado con `maxmemory 512mb` y AOF).
    - *Riesgo R2 (SPOF VPS):* Nodo único de persistencia (Aceptado para el MVP con PWA Offline-First y snapshots horarios).
    - *Riesgo R3 (Thundering Herd):* 15 000 celulares reconectando simultáneamente tras un corte (Mitigado en E4 con Circuit Breaker + Jitter).
    - *Riesgo R4 (Fuga RLS):* Bypass de distritos por error de query (Mitigado en E4 con RLS en PostgreSQL y FF-06).
    - *Falso Positivo de la IA (R5):* La IA afirmó que Celery no escala para 20 000 req/h. Se refutó demostrando que 20 000 req/h es apenas 5.56 req/s y 4 workers Celery procesan $> 400$ req/s.

    === E4. Iteraciones 2 y 3 de ADD
    - *Iteración 2 (Disponibilidad QA-02 - Mitigación R3):* Se combinó el patrón *Client-side Circuit Breaker (Decorator)* con *Local Outbox (IndexedDB)* y *Server Outbox (PostgreSQL ACID)* con algoritmo de *Exponential Backoff y Jitter aleatorio*.
      - *Evidencia (`fitness/disponibilidad.py`):* Simulación Monte Carlo de 1800 reportes bajo 8% de timeouts y 20 min de caída total. La estrategia base perdió 274 reportes; los reintentos saturaron la red (450 llamadas en caída) y perdieron 150 reportes; el Circuit Breaker + Outbox logró *0 reportes perdidos (100% entrega)* y redujo las llamadas al broker caído a solo 12 (*-97.3%*). (ADR-007).
    - *Iteración 3 (Seguridad QA-04 y Modificabilidad QA-05 - Mitigación R4):* Se descartaron 29 bases de datos físicas (colapso de RAM en VPS) y 29 esquemas (migraciones complejas). Se adoptó *PostgreSQL Row-Level Security (RLS)* nativo con claims JWT (`distrito_id`), logrando aislamiento invulnerable a errores de programación en FastAPI y alta de distritos en $< 1$ s. Se implementó Arquitectura Hexagonal con puertos `ProveedorCartografiaPort` para extensibilidad en $< 16$ ph. (ADR-008).

    #align(center)[
      #image("docs/architecture/diagramas/img/disponibilidad.png", width: 90%)
      #text(size: 7.5pt, style: "italic")[Figura 3: Resultados de simulación Monte Carlo de Disponibilidad (QA-02) y mitigación de Thundering Herd.]
    ]

    === E5. Fitness Functions en Integración Continua (CI)
    Se implementaron 6 fitness functions automatizadas en GitHub Actions (`.github/workflows/fitness.yml`):
    - *FF-01 (Estructural):* Capas del monolito modular sin ciclos de dependencias (`import-linter layers`).
    - *FF-02 (Estructural):* Dominio y estados aislados de adaptadores externos y SDKs (`import-linter forbidden`).
    - *FF-03 (Calidad):* Presupuesto de latencia $"p95" <= 1500$ ms ante 28 req/s pico (`pytest`).
    - *FF-04 (Calidad):* Cero reportes perdidos ante intermitencia móvil y caída del broker (`pytest`).
    - *FF-05 (Calidad):* Reducción de llamadas al broker caído en $> 80%$ mediante Circuit Breaker (`pytest`).
    - *FF-06 (Calidad):* Aislamiento estricto de distritos vía PostgreSQL RLS (`pytest`).
    
    *Demostración de Violación Intencional:* Se inyectó una dependencia prohibida en `dominio.py` (`from sismoreporta.externos import RedisCanalAdapter`). `lint-imports` falló inmediatamente con código 1:
    ```text
    FF-02 Dominio y estados aislados de adaptadores externos (ADR-005) BROKEN
    Contracts: 1 kept, 1 broken.
    sismoreporta.dominio is not allowed to import sismoreporta.externos:
    - sismoreporta.dominio -> sismoreporta.externos (l.294)
    ```
    Al revertir la violación, ambos contratos quedaron en estado `KEPT` (2 kept, 0 broken).

    === E6. ADR y Modelo C4 Actualizado
    Se formalizaron las decisiones en `ADR-006` (Buffer Redis), `ADR-007` (Circuit Breaker y Outbox) y `ADR-008` (Row-Level Security y Puertos Hexagonales). Asimismo, se actualizó el modelo C4 (`docs/architecture/c4/workspace.dsl`), etiquetando cada contenedor y componente con el escenario que atiende: `[QA-01]`, `[QA-02]`, `[QA-04]`, `[QA-05]`, `[QA-06]`. Se validó la consistencia con `structurizr validate` y se exportó la vista de contenedores:

    #align(center)[
      #image("docs/architecture/c4/img/structurizr-Contenedores.png", width: 92%)
      #text(size: 7.5pt, style: "italic")[Figura 4: Modelo C4 de Contenedores actualizado con etiquetas de atributos de calidad [QA-xx].]
    ]

    === E7. Matriz de Riesgos ATAM-lite y Bitácora de IA
    Se graficó la matriz de probabilidad e impacto (`fitness/matriz_riesgos.py`):

    #align(center)[
      #image("docs/architecture/diagramas/img/riesgos.png", width: 75%)
      #text(size: 7.5pt, style: "italic")[Figura 5: Matriz de probabilidad e impacto de riesgos clasificados por severidad.]
    ]

    Se completó `bitacora-ia.md` con 11 interacciones críticas documentadas, registrando la detección y refutación sistemática del falso positivo sobre la escalabilidad de Celery.

    #v(8pt)
    #text(weight: "bold", size: 9.5pt)[III. CUESTIONARIO OFICIAL]
    #v(4pt)

    *1. ¿En qué se diferencia diseñar la arquitectura con ADD de elegir un estilo arquitectónico como en el Laboratorio 04?* \
    Elegir un estilo arquitectónico (Lab 04) es una decisión macroscópica inicial que delimita la estructura física y lógica global del sistema en respuesta a restricciones de contorno (presupuesto, plazo, equipo). Por el contrario, diseñar con ADD 3.0 (Lab 08) es un proceso iterativo de descomposición donde cada ciclo toma un elemento concreto y le aplica tácticas arquitectónicas puntuales para satisfacer escenarios de calidad cuantitativos y verificables mediante evidencia empírica.

    *2. ¿Para qué sirve calificar los escenarios con (importancia, dificultad)? ¿Qué escenario de su árbol tiene la mayor prioridad y por qué?* \
    La calificación bidimensional permite construir una matriz de riesgo técnico. Los escenarios clasificados como *(H, H)* son Requerimientos Arquitecturalmente Significativos (ASR) que concentran la mayor incertidumbre y determinan las decisiones de alto costo de reversión; deben abordarse en las primeras iteraciones para evitar fallar tarde. En SismoReporta AQP, el escenario de mayor prioridad es *QA-01 (H, H)* (ingesta masiva de 20 000 reportes en 1 h en el simulacro nacional con $"p95" <= 1.5$ s) porque garantiza la supervivencia operativa del sistema en el momento más crítico del desastre bajo severas restricciones de hardware (1 VPS).

    *3. ¿Qué diferencia hay entre una táctica y un patrón? Ilustre con el circuit breaker.* \
    Una táctica es un principio fundamental abstracto que controla un único atributo de calidad (ej. "falla rápida y prevención de fallas en cascada" para Disponibilidad). Un patrón es una solución de diseño concreta, reusable y empaquetada que combina componentes y colaboraciones de clases. En el Circuit Breaker, la táctica consiste en no invocar un servicio caído para permitirle recuperarse; el patrón lo concreta mediante una máquina de estados finita (`CERRADO`, `ABIERTO`, `SEMIABIERTO`), umbrales temporizados de sondeo y la aplicación del patrón estructural Decorator.

    *4. Describa un punto de sensibilidad y un punto de trade-off de su arquitectura, con la evidencia que los respalda.* \
    - *Punto de Sensibilidad (S1):* La latencia $"p95"$ es sensible a que el endpoint de FastAPI no ejecute I/O síncrono. La simulación demostró que con procesamiento síncrono $"p95" = 213.8$ s, mientras que con encolamiento asíncrono puro $"p95" = 16.4$ ms.
    - *Punto de Trade-off (T1):* Rendimiento de ingesta frente a Consistencia Inmediata. El buffer Redis logra $"p95" = 16.4$ ms pero introduce un retraso de 2 s en la indexación en PostGIS. Se priorizó no rechazar reportes ciudadanos sobre la visualización en tiempo real estricto.

    *5. ¿Qué supuestos hizo su simulación y cómo podrían invalidar la decisión si fueran falsos?* \
    Se asumieron llegadas de Poisson independientes y tiempos de servicio lognormales con Redis en red local de bus rápido. Si tras el sismo se produce un arribo sincronizado de impulso Dirac (10 000 peticiones en 1 segundo por aviso televisivo), la cola en memoria saturaría a los workers, elevando el tiempo de espera en cola a varios minutos. Si Redis estuviera en un servidor remoto sobre red WAN inestable, el ACK de red bloquearía los hilos de FastAPI.

    *6. ¿Qué riesgo de la evaluación cruzada aceptaron sin mitigarlo y por qué es razonable para un plazo de 1 mes?* \
    Se aceptó el *Riesgo R2 (SPOF en instancia única de PostgreSQL / VPS)*. Desplegar un clúster de alta disponibilidad multi-zona con Patroni y replicación síncrona triplica el costo de infraestructura violando el presupuesto R-03 (\$15 USD/mes) y consumiría más del 60% del tiempo de desarrollo de 2 personas. Es razonable aceptarlo porque se mitiga operativamente con la PWA Offline-First (los celulares retienen los reportes), snapshots automáticos horarios y un procedimiento de restauración en $< 15$ min.

    *7. Explique qué es una fitness function y qué degradación concreta de su arquitectura detectaría cada una de las suyas.* \
    Es una prueba automatizada en CI que protege las características de la arquitectura frente a su deterioro. FF-01 detecta atajos temporales y dependencias circulares entre capas del monolito; FF-02 detecta que el dominio importe adaptadores de infraestructura; FF-03 detecta degradación de latencia ($"p95" > 1500$ ms); FF-04 detecta pérdida de reportes ante caídas; FF-05 detecta tormentas de reintentos por mal enfriamiento del breaker; y FF-06 detecta filtraciones de datos entre distritos en consultas SQL.

    *8. ¿Qué propuesta de la IA rechazaron con evidencia? ¿Qué habría pasado si la aceptaban sin medir?* \
    Se rechazó la propuesta de rediseñar hacia microservicios en Go/Rust sobre Kubernetes y Kafka. La simulación demostró que a 28 req/s el buffer en Redis opera a solo 7% de capacidad ($rho = 0.07$) y logra $"p95" = 16.4$ ms. Si se aceptaba sin medir, se habría incurrido en costos de infraestructura de más de \$180 USD/mes (quebrando el presupuesto R-03) y el proyecto habría colapsado al no completarse en el plazo de 1 mes (R-01).

    #v(8pt)
    #text(weight: "bold", size: 9.5pt)[IV. CONCLUSIONES Y LECCIONES APRENDIDAS]
    #v(4pt)

    1. El método ADD 3.0 proporciona una disciplina estructurada que evita tanto la parálisis por análisis como el diseño apresurado no sustentado, vinculando cada línea de código y contenedor a un requerimiento de calidad explícito.
    2. La evidencia cuantitativa (simulaciones M/G/c y Monte Carlo) es el antídoto contra la sobreingeniería y las recomendaciones sesgadas de la IA hacia modas tecnológicas complejas.
    3. Las fitness functions en integración continua transforman las intenciones arquitectónicas de los ADRs en salvaguardas ejecutables vivas, garantizando que el software permanezca íntegro a lo largo del tiempo.

    #v(8pt)
    #text(weight: "bold", size: 9.5pt)[V. REFERENCIAS BIBLIOGRÁFICAS]
    #v(4pt)
    - Bass, L., Clements, P., & Kazman, R. (2021). _Software architecture in practice_ (4th ed.). Addison-Wesley.
    - Cervantes, H., & Kazman, R. (2016). _Designing software architectures: A practical approach_. Addison-Wesley.
    - Ford, N., Parsons, R., Kua, P., & Sadalage, P. (2022). _Building evolutionary architectures_ (2nd ed.). O'Reilly Media.
    - Kazman, R., Klein, M., & Clements, P. (2000). _ATAM: Method for architecture evaluation_ (CMU/SEI-2000-TR-004). Software Engineering Institute, Carnegie Mellon University.
    - Nygard, M. T. (2018). _Release it! Design and deploy production-ready software_ (2nd ed.). Pragmatic Bookshelf.
    - Richards, M., & Ford, N. (2020). _Fundamentals of software architecture: An engineering approach_. O'Reilly Media.
  ]
)
