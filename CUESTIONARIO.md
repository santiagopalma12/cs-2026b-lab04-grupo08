# Cuestionario Oficial — Laboratorio 07: Patrones de Diseño con IA

**Asignatura:** Construcción de Software (2026-B)  
**Grupo:** 08 — SismoReporta AQP  
**Integrantes:**  
- Santiago Palma (`spalmaa@unsa.edu.pe`)  
- Dario Rafael Cornejo Hurtado (`dcornejohu@unsa.edu.pe`)  
**Docente:** Mg. Alexander Javier Benavides Rojas

---

### Pregunta 1: ¿Qué diferencia hay entre un patrón arquitectónico (Laboratorio 04) y un patrón de diseño? Dé un ejemplo de cada uno en su caso.

**Respuesta:**  
La diferencia radica fundamentalmente en el **alcance (scope), nivel de abstracción y escala de impacto** en el ciclo de vida del software:

- **Patrón Arquitectónico (Laboratorio 04):** Define la estructura macroscópica de todo el sistema, estableciendo las divisiones de subsistemas, los límites de despliegue, la topología de red, los mecanismos de persistencia y las estrategias globales para satisfacer atributos de calidad (drivers y escenarios QA). Tiene un alto costo de reversión.
  - *Ejemplo en SismoReporta AQP:* El patrón **Monolito Modular Asíncrono con Buffer en Memoria (ADR-001)**. Organiza todo el software en un único artefacto desplegable en Python estructurado en módulos desacoplados (*Ingesta*, *Triaje*, *Brigadas*, *GIS*), utilizando Redis como buffer no bloqueante para absorber 20,000 peticiones en la primera hora post-terremoto ($p95 \le 1.5\text{ s}$). Afecta la infraestructura física, los pipelines de CI/CD y los protocolos de comunicación (`RESP`, `SQL/TCP`, `HTTPS`).

- **Patrón de Diseño (Laboratorio 07):** Resuelve problemas recurrentes de diseño a nivel microscópico dentro de un módulo, estructurando la relación, creación y colaboración entre clases y objetos en el código fuente. Aplica directamente los principios SOLID (*"programar contra interfaces"*, *"composición sobre herencia"*). Su alcance es local y su refactorización no altera la arquitectura global.
  - *Ejemplo en SismoReporta AQP:* El patrón **Strategy + Adapter (`ICanalDespacho`)** en el módulo de Ingesta. Encapsula los algoritmos intercambiables de transporte de reportes (Redis, RabbitMQ, SMS Satelital, Mesh LoRa). Su impacto se circunscribe a la forma en que `ServicioSincronizacion` despacha un paquete sin acoplarse a los métodos `rpush()`, `basic_publish()` o `transmitir_trama()` de los SDKs externos.

---

### Pregunta 2: Explique con su código cómo Strategy materializa el principio abierto/cerrado. ¿Qué tuvo que modificar para agregar una variante nueva?

**Respuesta:**  
El Principio Abierto/Cerrado (OCP - Bertrand Meyer / Robert C. Martin) establece que las entidades de software deben estar **abiertas para su extensión, pero cerradas para su modificación**.

En la versión antes (`antes/servicio.py`), incorporar un nuevo canal de contingencia (como radios de largo alcance Mesh LoRa) obligaba a violar OCP: era mandatorio editar `sincronizar_reporte()`, añadir una nueva rama `elif canal == "MESH_LORA":` con su bucle de reintentos duplicado, y arriesgar regresiones en los canales existentes.

Con el patrón Strategy (`canales.py`), la variación se encapsula detrás de la abstracción `ICanalDespacho`:
```python
class ICanalDespacho(ABC):
    @abstractmethod
    def despachar(self, reporte_id: str, descripcion: str) -> ResultadoDespacho:
        ...
```
Para agregar la nueva estrategia `MeshLoraCanalAdapter` (demostrado en `tests/test_patrones.py`), se realizaron exactamente dos acciones:
1. **Crear una clase nueva que implementa la interfaz:**
   ```python
   class MeshLoraCanalAdapter(ICanalDespacho):
       def despachar(self, reporte_id: str, descripcion: str) -> ResultadoDespacho:
           # Lógica específica de transmisión por radio LoRa
           return ResultadoDespacho(exitoso=True, canal_usado="MESH_LORA")
   ```
2. **Registrar la nueva variante en la factoría en tiempo de ejecución:**
   ```python
   fabrica.registrar("MESH_LORA", lambda: MeshLoraCanalAdapter())
   ```
**¿Qué se modificó en `ServicioSincronizacion`?**  
**Absolutamente nada (0 líneas de código modificadas).** El servicio sigue invocando `canal = self.fabrica.crear(canal_nombre)` y `canal.despachar(...)`. El sistema se extendió sin abrir a modificación la lógica de orquestación de emergencias.

---

### Pregunta 3: ¿En qué se diferencian Adapter y Decorator si ambos "envuelven" un objeto?

**Respuesta:**  
Aunque ambos patrones estructurales utilizan la técnica de composición mediante un objeto envoltorio (*wrapper*), difieren radicalmente en su **intención arquitectónica y en la compatibilidad de sus interfaces**:

| Criterio | Patrón Adapter (GoF) | Patrón Decorator (GoF) |
| :--- | :--- | :--- |
| **Intención principal** | **Convertir una interfaz ajena e incompatible** en la que el cliente espera, permitiendo que clases dispares colaboren. | **Agregar responsabilidades o comportamientos transversales** dinámicamente a un objeto sin alterar su interfaz. |
| **Relación con la interfaz envuelta** | El Adapter implementa la interfaz esperada por el cliente (`ICanalDespacho`), pero el objeto envuelto (*Adaptee*, ej. `RabbitMQSDK`) tiene una **interfaz completamente diferente** (`basic_publish()`). | El Decorator implementa **exactamente la misma interfaz** que el objeto que envuelve (`ICanalDespacho` envuelve a otro `ICanalDespacho`). |
| **Transparencia para el cliente** | El cliente sabe que invoca la interfaz de destino, pero ignora los métodos nativos del SDK de terceros. | Es 100% transparente y recursivo: un decorador puede envolver a otro decorador y al cliente le resulta indistinguible. |
| **Ejemplo en SismoReporta AQP** | `RabbitMQCanalAdapter` envuelve a `RabbitMQSDK` convirtiendo llamadas `despachar()` a `basic_publish(..., body_bytes)`. | `ConReintentos` envuelve a cualquier `ICanalDespacho` para añadir captura de `TimeoutError` sin cambiar la firma `despachar()`. |
| **En el componente de IA** | `ClienteLLMAdapter` convierte `generate_text() -> dict` a `completar() -> str`. | `ConCacheLLM` envuelve a `ProveedorLLM` añadiendo almacenamiento en memoria de respuestas a prompts repetidos. |

---

### Pregunta 4: ¿Por qué el patrón State es la implementación natural de un diagrama de máquina de estados? ¿Qué ganó frente a usar condicionales?

**Respuesta:**  
El patrón State es la traducción formal 1 a 1 de una máquina de estados finitos (FSM) a la programación orientada a objetos:
- Cada estado del diagrama (`BORRADOR`, `ENCOLADO`, `RECIBIDO`, `VERIFICADO`, `ATENDIDO`, `DESCARTADO` en `estados-reporte.mmd`) se materializa como una **clase concreta independiente** que hereda de una clase base común (`EstadoReporteState`).
- Cada flecha o evento de transición del diagrama se modela como un **método formal** (`encolar_offline()`, `sincronizar()`, `verificar_triaje()`, `atender_incidente()`, `descartar()`).

**Ganancias determinantes frente al uso de condicionales procedimentales:**
1. **Transiciones ilegales imposibles por construcción:** La clase base prohíbe todas las transiciones por defecto elevando `ValueError`. Cada subclase de estado redefine únicamente las transiciones válidas según el diagrama. Intentar sincronizar un reporte `ATENDIDO` o `DESCARTADO` falla automáticamente sin requerir bloques `if/elif` defensivos.
2. **Eliminación del olor "Primitive Obsession":** El estado deja de ser un `string` mutable y propenso a errores tipográficos (`"RECIBIDO"`, `"recibido"`, `"RECIVIDO"`) para convertirse en un objeto con identidad y reglas formales.
3. **Principio de Responsabilidad Única (SRP):** La lógica de validación de un estado específico (ej. verificar que un reporte en borrador posea descripción antes de encolar) reside en `BorradorState`, no dispersa en el servicio.
4. **Aciclicidad y claridad:** Si en el futuro se añade un nuevo estado (ej. `EN_VERIFICACION_RADIAL`), basta agregar una nueva subclase sin tocar ni arriesgar el funcionamiento de los 5 estados restantes.

---

### Pregunta 5: ¿Por qué son indispensables las pruebas de caracterización antes de refactorizar? Describa un error que sus pruebas detectaron.

**Respuesta:**  
Según Michael Feathers (*Working Effectively with Legacy Code*), el código sin pruebas es código heredado peligroso de modificar. Las pruebas de caracterización son indispensables porque actúan como una **red de seguridad inmutable**:
- Capturan y congelan el comportamiento observable actual del sistema (tanto casos de éxito como errores y reglas de borde) antes de alterar una sola línea de código.
- Al ejecutarse con el fixture parametrizado (`@pytest.fixture(params=["sismoreporta.antes.servicio", "sismoreporta.servicio"])`), proporcionan una garantía matemática de que el refactor preservó intacto el comportamiento preexistente sin introducir regresiones silenciosas.

**Error real detectado por las pruebas durante el laboratorio:**
Durante la implementación del Decorator `ConReintentos`, la primera versión generada con asistencia de IA capturaba de forma genérica cualquier fallo con `except Exception:`.
- **Falla detectada:** La prueba `test_canal_no_soportado_lanza_error` esperaba que si se ingresaba un canal inválido, el sistema arrojara inmediatamente `ValueError`. Sin embargo, `ConReintentos` interceptaba el error y reintentaba 3 veces antes de fallar. En producción, esto causaría reintentos inútiles ante errores no recuperables (cargas malformadas o falta de permisos).
- **Corrección:** Guiados por la falla de la prueba, se restringió la captura exclusivamente a `except TimeoutError:`. Las fallas transitorias de red se reintentan; los errores de validación de negocio fallan de inmediato como corresponde.

---

### Pregunta 6: ¿Qué patrón propuso la IA que ustedes rechazaron y por qué? ¿Qué es la "patternitis"?

**Respuesta:**  
**Patrones propuestos por la IA y rechazados por el equipo:**
1. **`Singleton` para `FabricaCanales`:**
   - *Propuesta de la IA:* Implementar la factoría como una instancia global única accesible mediante `FabricaCanales.get_instance()` para "ahorrar memoria y centralizar el registro".
   - *Por qué se rechazó:* El patrón Singleton introduce acoplamiento global encubierto, dificulta las pruebas concurrentes y bloquea la inyección de canales simulados (`MeshLoraCanalAdapter`) en entornos de prueba aislados. Se sustituyó por inyección de dependencias explícita en el constructor.
2. **`Abstract Factory` para familias de canales y notificadores:**
   - *Por qué se rechazó:* No existen familias cohesivas interdependientes de productos en SismoReporta AQP. Forzar interfaces abstractas paralelas para crear simultáneamente transporte y notificaciones era sobreingeniería estéril.

**¿Qué es la "Patternitis"?**  
La *Patternitis* (o sobreingeniería por patrones) es un antipatrón cognitivo y de diseño donde los desarrolladores o los modelos de lenguaje intentan forzar la mayor cantidad posible de patrones de diseño GoF en una base de código, sin que exista un olor de código concreto que lo demande ni una justificación de mantenibilidad.  
Como consecuencia, el sistema sufre de **indirección excesiva, proliferación inmanejable de interfaces, dificultad de rastreo en debugging y pérdida de legibilidad**. Como regla de oro aprendida en la práctica: *Un patrón solo debe introducirse cuando un olor medible lo exige y las pruebas confirman su beneficio neto.*

---

### Pregunta 7: ¿Por qué se debe tratar la salida de un LLM como dato no confiable? Describa los guardrails de su caso y qué protegen.

**Respuesta:**  
La salida de un Modelo de Lenguaje (LLM) es intrínsecamente **probabilística y no determinista**: ante prompts idénticos puede generar respuestas disímiles, no tiene comprensión física del mundo y padece de alucinaciones (afirmaciones falsas emitidas con alta confianza lingüística). En una catástrofe sísmica en Arequipa, tratar la respuesta de un LLM como un dato confiable en el flujo transaccional puede costar vidas humanas.

**Guardrails implementados con Chain of Responsibility (`ia.py`):**
1. **`SinAlucinacionMagnitud`:**
   - *Qué protege:* Prohíbe que el LLM invente grados o escalas sísmicas (ej. *"Sismo de magnitud 8.5 Mw"* o *"Escala Richter 7.9"*) basándose únicamente en la descripción de un ciudadano común.  
   - *Justificación de dominio:* Únicamente el Instituto Geofísico del Perú (IGP) y el Centro Sismológico Nacional poseen acelerógrafos calibrados para certificar magnitudes oficiales. Si la IA inventa una magnitud errónea, puede generar pánico infundado o inducir al COE a desestimar réplicas reales.
2. **`SinPanicoSocial`:**
   - *Qué protege:* Censa y bloquea frases alarmistas o de inducción al caos (ej. *"Evacúen Arequipa de inmediato"*, *"Saqueos inminentes"*, *"Tsunami en la ciudad"*).
   - *Justificación de dominio:* Las instrucciones de evacuación zonal corresponden con exclusividad a las autoridades de Defensa Civil. Un mensaje alarmista propagado a través del mapa de calor provocaría estampidas humanas y congestión de vías de auxilio.
3. **`FormatoSeveridadValido`:**
   - *Qué protege:* Garantiza que la clasificación contenga de forma estricta una de las 4 categorías del catálogo oficial de incidentes: `LEVE`, `MODERADA`, `GRAVE` o `CATASTROFICA`.
   - *Justificación de dominio:* Evita que respuestas ambiguas o poéticas del LLM rompan la máquina de estados o impidan priorizar el incidente en el algoritmo de triaje geoespacial.

---

### Pregunta 8: Según sus métricas, ¿valió la pena el refactor? Argumente con la complejidad ciclomática, las líneas de código y los cambios previstos.

**Respuesta:**  
**Sí, valió absolutamente la pena desde una perspectiva de ingeniería de software para sistemas de misión crítica.** El análisis se sustenta en tres dimensiones cuantificables:

1. **Complejidad Ciclomática (Reducción del 86.4%):**
   - El método crítico `sincronizar_reporte()` pasó de una **complejidad 22 (Rango D - difícil de testear y propenso a bugs)** a una **complejidad 3 (Rango A - simple, lineal y testeable)**.
   - El promedio de complejidad de la clase bajó de **6.71 (B) a 1.93 (A)**. Esto reduce drásticamente el número de caminos independientes necesarios para lograr 100% de cobertura de ramas en pruebas unitarias.

2. **Líneas de Código y Granularidad (El costo asumido):**
   - El código de la lógica orquestadora pasó de 106 SLOC en 1 solo archivo procedural a 480 SLOC distribuidos en 6 módulos especializados (`servicio.py`, `canales.py`, `estados.py`, `eventos.py`, `comandos.py`, `ia.py`).
   - Aunque el volumen total creció en un 352%, la cohesión de cada archivo es máxima (Single Responsibility Principle) y el índice de mantenibilidad (MI) aumentó de 52.93 a 58.73.

3. **Justificación por los Cambios Previstos en SismoReporta AQP:**
   - Si la plataforma fuera un software estático que solo despachara por Redis y nunca integrara nuevos medios de comunicación, la versión inicial de 106 líneas habría sido suficiente.
   - Sin embargo, en un escenario real de catástrofe en Arequipa donde las antenas 4G colapsan, el sistema **requiere conmutar dinámicamente entre Redis, RabbitMQ, Gateway Satelital y radio Mesh LoRa**. Gracias a Strategy + Factory, agregar LoRa demandó 0 cambios en el servicio central.
   - Asimismo, aislar el LLM detrás de caché (`ConCacheLLM`) reduce la latencia en un 95% para descripciones recurrentes y los guardrails aseguran que ninguna alucinación comprometa la coordinación de brigadas.
