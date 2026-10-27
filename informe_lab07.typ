// =============================================================================
// INFORME DE LABORATORIO N° 07 - CONSTRUCCIÓN DE SOFTWARE (2026-B)
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

#set text(font: ("Liberation Serif", "Nimbus Roman"), size: 9pt)
#set par(justify: true, leading: 0.55em)

#let institutional-red = rgb("#cf4d36")
#let border-black = 0.5pt + rgb("#000000")

#v(4pt)
#align(center)[
  #text(size: 13pt, weight: "bold")[INFORME DE LABORATORIO N° 07]
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
  table.cell(colspan: 5)[Refactorizar hacia patrones de diseño con IA: Strategy, Adapter, Factory, Decorator, State, Observer y Chain of Responsibility, medidos con pruebas y métricas],

  [NÚMERO DE PRÁCTICA:],
  [07],
  [AÑO LECTIVO:],
  [2026B],
  [NRO. SEMESTRE:],
  [VI],

  [FECHA DE PRESENTACIÓN:],
  [24/10/2026],
  [HORA:],
  [23:59],
  [],
  [],

  table.cell(colspan: 3)[
    INTEGRANTE(S):
    - Santiago Enrique Palma Apaza
    - Dario Rafael Cornejo Hurtado
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

    En este laboratorio se aborda la refactorización formal hacia patrones de diseño orientados a objetos (Gang of Four - GoF, 1994), aplicando principios de código limpio (Fowler, 2018), principios SOLID (Martin, 2017) y patrones emergentes para el aislamiento de componentes de Inteligencia Artificial no deterministas (Huyen, 2025; Lakshmanan et al., 2020):

    - *Patrón de Diseño vs. Patrón Arquitectónico:* Mientras que los patrones arquitectónicos (Laboratorio 04) estructuran la topología global y el estilo macroscópico del sistema (ej. Monolito Modular Asíncrono con Redis), los patrones de diseño organizan las clases, objetos y métodos dentro de un módulo para resolver problemas recurrentes de acoplamiento, extensibilidad y cohesión.
    - *Principios Fundamentales Detrás de los Patrones:*
      - *Programar contra interfaces, no contra implementaciones:* Depender de abstracciones portuarias (`ICanalDespacho`, `ProveedorLLM`) en lugar de clases concretas o SDKs específicos.
      - *Composición sobre herencia:* Lograr flexibilidad dinámica envolviendo objetos colaboradores (Decorator, Strategy, Adapter) en lugar de rígidas jerarquías de herencia estática.
      - *Principios SOLID:* Responsabilidad Única (SRP), Abierto/Cerrado (OCP), Sustitución de Liskov (LSP), Segregación de Interfaces (ISP) e Inversión de Dependencias (DIP).
    - *Olores de Código y Refactorización hacia Patrones (Kerievsky, 2004):* No se agregan patrones por capricho ni por anticipación especulativa. Los patrones se justifican única y exclusivamente cuando un olor concreto (métodos largos, condicionales sobre estados, SDKs dispersos, código duplicado) lo exige.
    - *Métricas Objetivas de Complejidad:* Se utiliza la *Complejidad Ciclomática de McCabe* ($CC$), calculada con la herramienta `radon`, para cuantificar el número de caminos de ejecución independientes de cada método, buscando reducir módulos en rango crítico ($CC > 10$, Rangos C, D o F) hacia rangos óptimos ($CC \le 5$, Rango A).
    - *Aislamiento de la Inteligencia Artificial (LLM):* Los modelos de lenguaje son componentes no deterministas, con costos por token, latencia de red y riesgo inherente de alucinaciones. Se deben tratar como entradas no confiables mediante:
      1. *Strategy / Adapter:* Dobles de prueba (`ClienteLLMSimulado`) para pruebas unitarias sin conexión ni claves de API.
      2. *Decorator:* Caché en memoria (`ConCacheLLM`) para amortiguar llamadas idénticas.
      3. *Chain of Responsibility:* Guardrails deterministas que censuran alucinaciones y pánico social antes de emitir la salida al dominio.

    #v(8pt)
    #text(weight: "bold", size: 9.5pt)[II. DESARROLLO DE LA PRÁCTICA (CASO 8: SISMOREPORTA AQP)]
    #v(4pt)

    Siguiendo las especificaciones de la Guía Oficial para el *Caso 8: SismoReporta AQP*, se refactorizó el flujo crítico de *"Envío Offline y Sincronización Diferida de Reportes Post-Sismo"* (modelado en el diagrama de secuencia del Lab 05), implementando las sugerencias de la Tabla 7:
    - *Reporte sin señal:* Patrón Command + Cola offline de sincronización.
    - *Variación de transporte e infraestructura:* Strategy + Adapter + Factory + Decorator (reintentos).
    - *Ciclo de vida del reporte:* Patrón State a partir de `estados-reporte.mmd`.
    - *Notificaciones y telemetría:* Patrón Observer.
    - *Función de IA (E5):* Clasificación de severidad de daños aislada con caché y cadena de Guardrails.

    #v(6pt)
    #text(weight: "bold")[1. Entregable E1: Versión Antes, Red de Seguridad y Detección de Olores]
    #v(2pt)

    Se implementó la versión ingenua monolítica en `src/sismoreporta/antes/servicio.py`, reuniendo en un único método `sincronizar_reporte()` la validación de estados mediante condicionales anidados, la verificación de geocerca provincial, la negociación con SDKs disímiles (`RedisBrokerSDK`, `RabbitMQSDK`, `SmsSatelitalGatewaySDK` simulados en `externos.py`), bucles de reintentos duplicados y notificaciones concatenadas a mano.
    - *Medición con Radon:* El método `sincronizar_reporte()` arrojó una *complejidad ciclomática de 22 (Rango D)*, confirmando un código de alto riesgo de mantenimiento.
    - *Red de Seguridad:* Se diseñó `tests/test_comportamiento.py` con 12 pruebas de caracterización que congelaron el comportamiento observable previo (casos exitosos, fallas por 3 timeouts, descarte por geocerca y rechazo de estados inconsistentes), ejecutándose mediante un fixture parametrizado sobre el módulo antes (`12 passed in 0.05s`).
    - *Catálogo de Olores (`docs/design/patrones/olores.md`):* Se documentaron 6 olores aceptados y 2 patrones propuestos por la IA formalmente rechazados (*Singleton* en la factoría y *Abstract Factory* por sobreingeniería).

    #v(6pt)
    #text(weight: "bold")[2. Entregable E2: Strategy, Adapter, Decorator y Factory para Canales de Despacho]
    #v(2pt)

    Para resolver el acoplamiento a los SDKs externos y eliminar los bloques `if/elif` por medio de transporte, se implementó `src/sismoreporta/canales.py`:
    - *Strategy (`ICanalDespacho`):* Interfaz de dominio con el método declarativo `despachar(reporte_id, descripcion) -> ResultadoDespacho`.
    - *Adapters:* `RedisCanalAdapter`, `RabbitMQCanalAdapter` y `SmsSatelitalCanalAdapter` traducen llamadas del dominio a los formatos propios de cada SDK (JSON, bytes binarios AMQP y tramas hexadecimales).
    - *Decorator (`ConReintentos`):* Envuelve cualquier canal para capturar selectivamente `TimeoutError` y reintentar hasta 3 veces sin contaminar los adaptadores.
    - *Factory por Registro (`FabricaCanales`):* Permite registrar e instanciar dinámicamente estrategias por nombre sin usar estado global ni Singleton.
    - *Demostración del Principio Abierto/Cerrado (OCP):* La prueba `test_open_closed_nuevo_canal_sin_modificar_servicio` demostró la incorporación del canal de radio de contingencia `MeshLoraCanalAdapter` registrándolo en la factoría con *cero modificaciones en el servicio central*.

    #v(4pt)
    #align(center)[
      #image("docs/design/patrones/img/strategy-adapter-factory.png", width: 90%)
      #v(2pt)
      #text(size: 7.5pt, style: "italic")[Figura 1: Diagrama de Clases PlantUML para Strategy, Adapter, Decorator y Factory en canales de despacho.]
    ]

    #v(6pt)
    #text(weight: "bold")[3. Entregable E3: Patrón State para el Ciclo de Vida de la Entidad Reporte]
    #v(2pt)

    Se transformó la máquina de estados de Lab 05 (`estados-reporte.mmd`) en una jerarquía formal en `src/sismoreporta/estados.py`:
    - La clase base `EstadoReporteState` define todas las transiciones posibles (`encolar_offline()`, `sincronizar()`, `verificar_triaje()`, `atender_incidente()`, `descartar()`) prohibiéndolas por defecto mediante excepciones `ValueError`.
    - Cada subclase concreta (`BorradorState`, `EncoladoState`, `RecibidoState`, `VerificadoState`, `AtendidoState`, `DescartadoState`) sobreescribe con exclusividad las transiciones válidas.
    - En `src/sismoreporta/servicio.py`, la entidad `Reporte` delega sus transiciones polimórficamente en `self._estado`.
    - La prueba `test_state_impide_transiciones_invalidas` corroboró que reportes atendidos o descartados no pueden reiniciarse ni sincronizarse.

    #v(4pt)
    #align(center)[
      #image("docs/design/patrones/img/state-reporte.png", width: 85%)
      #v(2pt)
      #text(size: 7.5pt, style: "italic")[Figura 2: Diagrama de Clases del Patrón State modelando el ciclo de vida de la emergencia.]
    ]

    #v(6pt)
    #text(weight: "bold")[4. Entregable E4: Patrones Observer y Command (Notificaciones y Cola Offline)]
    #v(2pt)

    - *Patrón Observer (`src/sismoreporta/eventos.py`):* Se reemplazaron las concatenaciones manuales del servicio orquestador por el sujeto `PublicadorEventos`, difundiendo el evento `reporte_recibido` hacia observadores independientes (`NotificadorCOE`, `AuditorEventosSismicos`, y el nuevo suscriptor `TableroOperacionesMapa` para actualización de capas GIS en tiempo real).
    - *Patrón Command + Cola (`src/sismoreporta/comandos.py`):* Para atender la sincronización ciudadana sin señal (sugerencia de Tabla 7), se encapsuló la petición en `ComandoSincronizarReporte` y se implementó `ColaComandosOffline` como invocador que almacena peticiones en lote y las transmite en bloque al detectar conectividad.

    #v(4pt)
    #align(center)[
      #grid(
        columns: (1fr, 1fr),
        gutter: 8pt,
        [
          #image("docs/design/patrones/img/observer-eventos.png", width: 100%)
          #text(size: 7pt, style: "italic")[Figura 3a: Patrón Observer.]
        ],
        [
          #image("docs/design/patrones/img/command-offline.png", width: 100%)
          #text(size: 7pt, style: "italic")[Figura 3b: Patrón Command + Cola.]
        ]
      )
    ]

    #v(6pt)
    #text(weight: "bold")[5. Entregable E5: Aislamiento del Componente de IA con Guardrails]
    #v(2pt)

    Se implementó `src/sismoreporta/ia.py` para la función de dominio *"Clasificar la severidad del daño a partir de la descripción ciudadana"*:
    - *Strategy / Adapter:* `ProveedorLLM` y `ClienteLLMAdapter` aíslan al SDK generativo (`ClienteLLMSimulado`), permitiendo pruebas unitarias deterministas sin claves de API.
    - *Decorator (`ConCacheLLM`):* Almacena en memoria las inferencias para descripciones idénticas, reduciendo a 0 la latencia y costo de llamadas repetidas.
    - *Chain of Responsibility (`Guardrail`):* Cadena de sanitización determinista que procesa la respuesta del LLM antes de entregarla al sistema:
      1. `SinAlucinacionMagnitud`: Prohíbe inventar magnitudes sismológicas no oficiales (solo IGP).
      2. `SinPanicoSocial`: Censa frases sensacionalistas de evacuación ("evacúen Arequipa", "saqueos inminentes").
      3. `FormatoSeveridadValido`: Exige una severidad oficial (`LEVE`, `MODERADA`, `GRAVE`, `CATASTROFICA`).

    #v(4pt)
    #align(center)[
      #image("docs/design/patrones/img/chain-guardrails-ia.png", width: 88%)
      #v(2pt)
      #text(size: 7.5pt, style: "italic")[Figura 4: Componente de IA aislado con Strategy, Adapter, Decorator y Chain of Responsibility.]
    ]

    #v(6pt)
    #text(weight: "bold")[6. Entregable E6: Métricas de Código y Análisis Honesto de Trade-off]
    #v(2pt)

    Se calcularon las métricas objetivas de McCabe con `radon cc`, `radon raw` y `radon mi`:

    #table(
      columns: (3.5cm, 2.5cm, 2.5cm, 1fr),
      stroke: 0.5pt + rgb("#666666"),
      inset: 3pt,
      align: (left, center, center, left),
      fill: (col, row) => if row == 0 { rgb("#eeeeee") } else { none },

      [*Métrica Evaluada*], [*Versión ANTES*], [*Versión DESPUÉS*], [*Evaluación de Impacto*],
      [Complejidad `sincronizar_reporte`], [22 (Rango D)], [3 (Rango A)], [-86.4% (Reducción crítica)],
      [Complejidad `clasificar_severidad`], [3 (Rango A)], [2 (Rango A)], [-33.3%],
      [Promedio Clase Principal], [6.71 (Rango B)], [1.93 (Rango A)], [-71.2% (Excelente)],
      [Promedio del Sistema Completo], [6.71 (Rango B)], [2.04 (Rango A)], [Rango A en todos los métodos],
      [Líneas de Código Lógicas (SLOC)], [106 SLOC], [121 / 480 SLOC], [+352% (Mayor modularidad)],
      [Índice Mantenibilidad (MI)], [52.93 (Rango A)], [58.73 (Rango A)], [+10.9% (Menor acoplamiento)],
      [Pruebas Automatizadas], [12 pruebas], [35 pruebas en verde], [100% cobertura funcional]
    )

    *Lectura del Trade-off:* El refactor redujo la complejidad ciclomática de 22 a 3 y aisló por completo las dependencias de red e IA, facilitando la incorporación de nuevas estrategias sin alterar la base de código. A cambio, el sistema aumentó de 1 a 6 archivos modulares y de 106 a 480 SLOC, introduciendo niveles de indirección que requieren que los ingenieros conozcan los patrones GoF. La versión previa habría sido suficiente para un prototipo rápido de una semana con un solo canal fijo; para un sistema de emergencias real que debe tolerar picos extremos de tráfico y fallas de antenas celulares en Arequipa, los patrones son indispensables.

    #v(6pt)
    #text(weight: "bold")[7. Entregables E7 y E8: Diagramas Actualizados, Bitácora, ADR-005 y Reto Opcional]
    #v(2pt)

    - *Diagrama de Clases Actualizado:* Se actualizó `docs/design/clases.puml` con los estereotipos formales y se renderizó a PNG con el motor Smetana.
    - *Bitácora de IA (`docs/design/patrones/bitacora-ia.md`):* Se documentaron 6 interacciones estructuradas, destacando la corrección de `ConReintentos` (que capturaba genéricamente `except Exception:` y fue corregido a `except TimeoutError:`) y el rechazo de la propuesta de un segundo LLM como juez.
    - *ADR-005 (`docs/architecture/adr/005-patrones-de-diseno.md`):* Registro formal de la decisión arquitectónica justificando patrones adoptados y rechazados.
    - *Reto Opcional (+2 Puntos - CI Workflow):* Se implementó `.github/workflows/patrones-ci.yml`, configurando una GitHub Action que ejecuta la suite de Pytest y falla de forma automática si algún método de `src/sismoreporta/` supera complejidad ciclomática 10 (`radon cc -s --min C`), garantizando calidad continua en cada commit.

    #v(8pt)
    #text(weight: "bold", size: 9.5pt)[III. SOLUCIÓN DEL CUESTIONARIO OFICIAL]
    #v(4pt)

    #text(weight: "bold")[Pregunta 1: ¿Qué diferencia hay entre un patrón arquitectónico (Laboratorio 04) y un patrón de diseño? Dé un ejemplo de cada uno en su caso.]\
    La diferencia radica en el alcance y nivel de abstracción. El patrón arquitectónico (Lab 04) define la estructura macroscópica de todo el sistema, su topología de despliegue y sus límites de infraestructura para satisfacer drivers globales (ej. *Monolito Modular Asíncrono con Redis*, ADR-001, para absorber 20,000 reportes post-sismo en 1 hora). El patrón de diseño (Lab 07) organiza clases, objetos e interfaces dentro de un módulo para solucionar olores microscópicos concretos (ej. *Strategy + Adapter `ICanalDespacho`* para intercambiar transportes de red sin tocar el servicio orquestador).

    #v(4pt)
    #text(weight: "bold")[Pregunta 2: Explique con su código cómo Strategy materializa el principio abierto/cerrado. ¿Qué tuvo que modificar para agregar una variante nueva?]\
    Strategy encapsula algoritmos intercambiables tras la interfaz común `ICanalDespacho`. Para incorporar la nueva estrategia de contingencia por radio `MeshLoraCanalAdapter`, se creó la clase adaptadora y se registró en la factoría en tiempo de ejecución (`fabrica.registrar("MESH_LORA", ...)`). En `ServicioSincronizacion` se modificaron exactamente *0 líneas de código*: el sistema quedó abierto para su extensión pero cerrado para su modificación.

    #v(4pt)
    #text(weight: "bold")[Pregunta 3: ¿En qué se diferencian Adapter y Decorator si ambos "envuelven" un objeto?]\
    Difieren en su intención y en la compatibilidad de interfaces. *Adapter* convierte una interfaz ajena e incompatible en la que el cliente espera (`RabbitMQCanalAdapter` adapta los métodos binarios de `RabbitMQSDK` a `ICanalDespacho`). *Decorator* implementa exactamente la misma interfaz del objeto que envuelve para añadirle responsabilidades transversales transparentes (`ConReintentos` envuelve a `ICanalDespacho` para añadir tolerancia a fallas por reintentos sin alterar su firma).

    #v(4pt)
    #text(weight: "bold")[Pregunta 4: ¿Por qué el patrón State es la implementación natural de un diagrama de máquina de estados? ¿Qué ganó frente a usar condicionales?]\
    Porque cada estado del diagrama (`BORRADOR`, `ENCOLADO`, `RECIBIDO`, etc.) se mapea a una clase concreta (`EstadoReporteState`), y cada flecha de transición se modela como un método formal. Se ganó: (1) transiciones ilegales prohibidas por construcción (la clase base eleva `ValueError` si se intenta sincronizar un reporte atendido), (2) eliminación del olor *Primitive Obsession* sobre cadenas de texto, y (3) alta cohesión, ya que cada estado administra exclusivamente sus propias reglas de negocio.

    #v(4pt)
    #text(weight: "bold")[Pregunta 5: ¿Por qué son indispensables las pruebas de caracterización antes de refactorizar? Describa un error que sus pruebas detectaron.]\
    Porque congelan el comportamiento observable del sistema previo a la modificación, garantizando que el refactor no introduzca regresiones silenciosas. En nuestra práctica, las pruebas detectaron que la primera versión de `ConReintentos` capturaba genéricamente `except Exception:`, reintentando 3 veces incluso cuando se ingresaba un nombre de canal inválido. Gracias a `test_canal_no_soportado_lanza_error`, se restringió la captura exclusivamente a `TimeoutError`.

    #v(4pt)
    #text(weight: "bold")[Pregunta 6: ¿Qué patrón propuso la IA que ustedes rechazaron y por qué? ¿Qué es la "patternitis"?]\
    La IA propuso implementar `FabricaCanales` como un *Singleton* global y aplicar *Abstract Factory* para familias de transportes y notificadores. Se rechazaron porque Singleton introduce estado global mutable que bloquea pruebas unitarias aisladas, y Abstract Factory añadía indirección innecesaria (*patternitis*). La patternitis es el sobreuso indiscriminado de patrones GoF sin un olor de código concreto que lo justifique, resultando en bases de código infladas, difíciles de depurar y costosas de mantener.

    #v(4pt)
    #text(weight: "bold")[Pregunta 7: ¿Por qué se debe tratar la salida de un LLM como dato no confiable? Describa los guardrails de su caso y qué protegen.]\
    Porque los LLM son modelos probabilísticos propensos a alucinaciones lingüísticas. En SismoReporta AQP se diseñó una cadena de guardrails (`Guardrail`): `SinAlucinacionMagnitud` impide que el LLM invente grados sismológicos en escala Richter sin confirmación oficial del IGP; `SinPanicoSocial` bloquea frases sensacionalistas ("evacúen Arequipa de inmediato") que provocarían caos ciudadano; y `FormatoSeveridadValido` asegura que la clasificación coincida estrictamente con el catálogo oficial (`LEVE`, `MODERADA`, `GRAVE`, `CATASTROFICA`).

    #v(4pt)
    #text(weight: "bold")[Pregunta 8: Según sus métricas, ¿valió la pena el refactor? Argumente con la complejidad ciclomática, las líneas de código y los cambios previstos.]\
    Sí, valió absolutamente la pena para un sistema crítico de emergencias. La complejidad ciclomática máxima cayó un *86.4% (de 22 a 3)*, situando todos los métodos en Rango A. Aunque el código creció de 106 a 480 SLOC, la mantenibilidad global subió de 52.93 a 58.73 y la modularidad alcanzada permite que la plataforma conmute dinámicamente entre Redis, RabbitMQ, enlaces satelitales y radios LoRa sin tocar el código central, ejecutando 35 pruebas automatizadas en menos de 0.1 segundos.

    #v(8pt)
    #text(weight: "bold", size: 9.5pt)[IV. CONCLUSIONES]
    #v(4pt)

    1. La refactorización guiada por olores de código y métricas cuantitativas de Radon transforma código procedimental frágil y de alta complejidad en arquitecturas modulares, mantenibles y conformes a los principios SOLID.
    2. La combinación de patrones creacionales (Factory por registro), estructurales (Adapter, Decorator) y de comportamiento (Strategy, State, Observer, Command) desacopla de forma limpia las responsabilidades de transporte, ciclo de vida y telemetría en emergencias sísmicas.
    3. Aislar los componentes de Inteligencia Artificial detrás de puertos abstractos, decoradores de caché y cadenas de responsabilidad (Guardrails) es un requisito innegociable en sistemas de misión crítica para garantizar determinismo, bajo costo y protección contra alucinaciones.
    4. La suite de pruebas de caracterización y unitarias (35 passed) combinada con integración continua en GitHub Actions asegura un control de calidad implacable donde ningún cambio de código puede superar complejidad ciclomática 10.

    #v(8pt)
    #text(weight: "bold", size: 9.5pt)[V. REFERENCIAS BIBLIOGRÁFICAS]
    #v(4pt)

    - Feathers, M. (2004). _Working effectively with legacy code_. Prentice Hall.
    - Fowler, M. (2018). _Refactoring: Improving the design of existing code_ (2nd ed.). Addison-Wesley.
    - Gamma, E., Helm, R., Johnson, R., & Vlissides, J. (1994). _Design patterns: Elements of reusable object-oriented software_. Addison-Wesley.
    - Huyen, C. (2025). _AI engineering: Building applications with foundation models_. O'Reilly Media.
    - Kerievsky, J. (2004). _Refactoring to patterns_. Addison-Wesley.
    - Lakshmanan, V., Robinson, S., & Munn, M. (2020). _Machine learning design patterns_. O'Reilly Media.
    - Martin, R. C. (2017). _Clean architecture: A craftsman's guide to software structure and design_. Prentice Hall.
    - McCabe, T. J. (1976). A complexity measure. _IEEE Transactions on Software Engineering_, SE-2(4), 308–320.
    - Refactoring.Guru. (s. f.). _Patrones de diseño_. https://refactoring.guru/es/design-patterns
  ]
)
