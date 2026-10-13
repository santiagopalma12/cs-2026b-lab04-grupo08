# Cuestionario — Laboratorio 05: Diagramas de Diseño UML 2.5.1
**Construcción de Software · EPIS-UNSA · 2026-B · Grupo 08**  
**Integrantes:** Santiago Palma (`santiagopalma12`), Dario Rafael Cornejo Hurtado (`darich1010`)  
**Caso de Estudio:** Caso 8 — SismoReporta AQP  

---

### 1. ¿Qué diferencia hay entre el diseño arquitectónico del Laboratorio 04 y el diseño detallado de este laboratorio? Dé un ejemplo de su caso.
* **Diseño Arquitectónico (Laboratorio 04):** Opera a nivel macroestructural; define los subsistemas, módulos de alto nivel (*Bounded Contexts*), estilos arquitectónicos (ej. Monolito Modular Asíncrono), protocolos de comunicación física entre nodos y los atributos de calidad transversales que guían la estructura global del sistema conforme a la norma ISO/IEC/IEEE 42010. Sus decisiones se plasman en diagramas de contenedores, despliegue físico y registros de decisiones arquitectónicas (ADRs).
* **Diseño Detallado (Laboratorio 05):** Opera a nivel microestructural dentro de los límites de cada módulo; modela la estructura interna de clases, tipos de datos, visibilidad de atributos, contratos de métodos, estados del ciclo de vida de las entidades y la coreografía exacta de intercambio de mensajes entre objetos en tiempo de ejecución conforme a la especificación UML 2.5.1.

**Ejemplo en SismoReporta AQP:**  
En el **Laboratorio 04**, el diseño arquitectónico estableció que existiría un módulo desacoplado de *Ingesta* que se comunicaría de forma asíncrona mediante colas *Redis* con el motor de *Triaje* para soportar un pico de 20,000 reportes/hora.  
En el **Laboratorio 05**, el diseño detallado especificó exactamente qué clases componen dicho módulo: la clase `Reporte`, el value object `Coordenadas`, la interfaz `IBrokerCola` con el método `encolarReporte(canal: String, payloadJson: String): bool`, el adaptador `RedisBrokerAdapter`, la máquina de estados de `Reporte` (con transiciones como `sincronizar()` y `verificarTriaje()`) y la secuencia de llamadas polimórficas del método `procesarLoteOffline()`.

---

### 2. ¿Cuándo usaría composición y cuándo agregación? Justifique con dos relaciones de su diagrama de clases.
* **Composición ($*--$):** Se emplea cuando existe una relación de **pertenencia fuerte y ciclo de vida dependiente (todo-parte)**. Las partes no tienen existencia conceptual ni persistencia independiente fuera del objeto contenedor; si el objeto padre se destruye, todas sus partes subordinadas se eliminan en cascada.
* **Agregación ($o--$):** Se emplea cuando existe una relación de **agrupamiento débil o contenedor independiente**. Las partes existen previamente y pueden persistir de forma autónoma aunque el contenedor deje de existir.

**Justificación con dos relaciones de nuestro diagrama de clases:**
1. **Composición: `Reporte` y `FotoEvidencia` (`1 *-- 0..3`):**  
   Una `FotoEvidencia` representa un registro fotográfico de daño capturado en el contexto de un incidente sísmico específico. No tiene valor de negocio ni entidad autónoma si no está vinculada a su `Reporte`. Si el usuario o el administrador descartan o eliminan un reporte, las fotos asociadas se destruyen del almacenamiento. El ciclo de vida de la evidencia fotográfica está subordinado al reporte.
2. **Agregación: `ZonaImpacto` y `Reporte` (`1 o-- 0..*`):**  
   Una `ZonaImpacto` (por ejemplo, el distrito de Cayma o Miraflores) agrupa dinámicamente un conjunto de reportes incidentales para calcular mapas de calor y densidad geoespacial. Sin embargo, los reportes ciudadanos existen por sí mismos antes de que la zona territorial sea agregada o calculada por el motor GIS, y si se redefine la zonificación o se disuelve una geocerca territorial, los reportes individuales permanecen intactos en la base de datos central.

---

### 3. ¿Por qué en el diagrama de clases se modela la pasarela de pagos (o el servicio externo de su caso) como interfaz y no como superclase? Relaciónelo con el ADR-001.
En el caso de **SismoReporta AQP**, los servicios externos críticos son el **Broker de Mensajería en Memoria** (`IBrokerCola`) y el **Subsistema de Notificaciones Masivas** (`INotificadorEmergencias`).

**¿Por qué se modelan como interfaz (`<<puerto>>`) y no como superclase?**
1. **Inversión de Dependencias (Principio DIP de SOLID):**  
   Modelar el broker como una superclase obligaría al módulo de negocio de dominio a heredar de una clase acoplada a detalles de implementación técnica (redes, sockets de Redis, credenciales de conexión). Al definir `IBrokerCola` como una **interfaz o puerto abstracto**, el dominio define contractualmente *qué servicio requiere*, obligando a que la infraestructura dependa del dominio y no a la inversa.
2. **Principio de Sustitución de Liskov y Desacoplamiento (ADR-001):**  
   En el ADR-001 se estableció que para el MVP en 1 mes sobre un VPS de bajo costo se utilizaría **Redis** (`RedisBrokerAdapter`). Sin embargo, si en el futuro la carga escala y se migra a **RabbitMQ**, **AWS SQS** o un mock en memoria para pruebas unitarias (`InMemoryBrokerMock`), el dominio del sistema no sufrirá ningún cambio; solo se sustituye el adaptador que implementa la interfaz. Con herencia de superclase, el código de dominio quedaría irremediablemente atado a la librería de Redis.

---

### 4. Explique la regla C1 y muestre un mensaje de su diagrama de secuencia que la incumplía antes de corregirlo.
* **Definición de la Regla C1:**  
  *Todo mensaje sincrónico o asincrónico enviado en un diagrama de secuencia hacia una línea de vida que represente una instancia de una clase debe existir como una operación pública definida con parámetros compatibles en la clase correspondiente dentro del diagrama de clases.*

**Incumplimiento detectado antes de la corrección:**  
En el primer borrador generado por la IA para el flujo de sincronización offline, el `ServicioSincronizacion` enviaba a la instancia `reporte` el mensaje:
```text
S -> R : sincronizar(fechaActual)
```
Sin embargo, al auditar `clases.puml`, la operación en la clase `Reporte` había sido declarada sin parámetros:
```plantuml
class Reporte {
  ...
  + sincronizar(): void
}
```
**Violación de C1:** El diagrama de secuencia exigía inyectar la fecha de recepción en el servidor para efectos de auditoría y descarte por antigüedad, pero la clase receptora no declaraba dicho argumento en su signatura.  
**Corrección aplicada:** Se actualizó la definición en `clases.puml` a `+ sincronizar(fecha: DateTime): void`, satisfaciendo formalmente la consistencia entre comportamiento y estructura.

---

### 5. ¿Cómo se derivan casos de prueba a partir de un diagrama de máquina de estados? Indique cuántas pruebas mínimas requiere su diagrama.
* **Metodología de derivación de casos de prueba (State-Based Testing):**  
  A partir de un diagrama de máquina de estados, los casos de prueba se derivan sistemáticamente mediante la cobertura del grafo de transiciones:
  1. **Cobertura de Estados (State Coverage):** Cada estado válido debe ser visitado al menos una vez por una secuencia de pruebas.
  2. **Cobertura de Transiciones (Transition Coverage o 0-Switch):** Cada transición $(S_i \xrightarrow{\text{evento}[\text{guarda}]} S_j)$ debe ser ejecutada exitosamente al menos una vez.
  3. **Cobertura de Pares de Transición (1-Switch Coverage):** Cada par de transiciones consecutivas $(S_i \rightarrow S_j \rightarrow S_k)$ debe ser probado.
  4. **Pruebas de Transiciones Inválidas (Sneak Paths):** Se debe verificar que eventos invocados en estados no permitidos disparen una excepción controlada (ej. invocar `atenderIncidente()` en un reporte en estado `BORRADOR`).

**Cálculo de pruebas mínimas en nuestra máquina de estados (`estados-reporte.mmd`):**  
Nuestro diagrama contiene **6 estados** (`BORRADOR`, `ENCOLADO`, `RECIBIDO`, `VERIFICADO`, `ATENDIDO`, `DESCARTADO`) y **8 transiciones dirigidas**:
1. `[*] -> BORRADOR` (`guardarBorrador()`)
2. `BORRADOR -> ENCOLADO` (`encolarOffline() [sin conexion]`)
3. `BORRADOR -> RECIBIDO` (`sincronizar() [conexion directa]`)
4. `ENCOLADO -> RECIBIDO` (`sincronizar(fecha) [senal y geocerca valida]`)
5. `ENCOLADO -> DESCARTADO` (`descartar() [fuera de perimetro]`)
6. `RECIBIDO -> VERIFICADO` (`verificarTriaje() [score >= 0.70]`)
7. `RECIBIDO -> DESCARTADO` (`descartar() [duplicado espacial]`)
8. `VERIFICADO -> ATENDIDO` (`atenderIncidente()`)

**Resultado:** Para garantizar una cobertura básica de transiciones (0-Switch Coverage) se requieren como **mínimo 8 casos de prueba unitarios**, a los que se suman **4 pruebas negativas de caminos no permitidos**, totalizando **12 pruebas automatizadas mínimas**.

---

### 6. ¿Qué información del diagrama de diseño se perdió en la ingeniería inversa (E6) y por qué?
Al ejecutar `pyreverse` sobre `src/sismoreporta/dominio.py` para generar `classes_sismoreporta.puml`, se perdieron las siguientes piezas clave del diseño conceptual:
1. **Semántica de Composición frente a Agregación/Asociación:**  
   En el diagrama de diseño, `Reporte` y `FotoEvidencia` estaban vinculados con composición fuerte (`*--`). En el diagrama inverso, la relación se degradó a un simple atributo `fotos: List[FotoEvidencia]`. Esto ocurre porque Python no posee primitivas sintácticas para declarar la subordinación del ciclo de vida de objetos en memoria.
2. **Multiplicidades Numéricas:**  
   Se perdieron los límites de negocio (`1`, `0..3`, `1..*`). Python usa colecciones dinámicas (`list`, `dict`), por lo que el AST de `pyreverse` no puede inferir cotas superiores sin ejecutar el código.
3. **Estereotipos y Metadatos de Dominio:**  
   Los estereotipos `<<ValueObject>>`, `<<puerto>>`, `<<adaptador>>` y `<<servicio>>` desaparecieron por completo.
4. **Distinción entre Interfaz y Clase Abstracta:**  
   Las interfaces `IBrokerCola` y `IRepositorioReportes` se renderizaron como clases comunes con el modificador `{abstract}`, perdiéndose la noción de contrato desacoplado de puerto.

---

### 7. ¿Qué falso positivo detectó en la revisión de consistencia con IA? ¿Qué habría pasado si lo aceptaba sin verificar?
* **Falso Positivo Detectado:**  
  La IA indicó en la revisión de consistencia C4 que existía un *acoplamiento cíclico entre los módulos `ingesta` y `triaje`*, señalando erróneamente que "Ingesta depende de Triaje porque ambos conocen y manipulan la entidad `Reporte`".
* **¿Por qué fue un error de la IA?**  
  La IA confundió una dependencia legítima hacia un paquete compartido de dominio (`compartido`) con una dependencia circular directa entre módulos operacionales. En nuestra arquitectura, `ingesta` solo coloca un mensaje en la cola de Redis y `triaje` lo consume de forma asíncrona. Ninguno importa clases del otro.
* **¿Qué habría pasado si se aceptaba sin verificar?**  
  Si hubiésemos aceptado ciegamente la advertencia de la IA, habríamos intentado crear interfaces redundantes innecesarias o desmembrar la entidad `Reporte` en dos representaciones artificiales (ej. `ReporteIngesta` y `ReporteTriaje`), introduciendo mapeadores complejos, duplicación de código y sobrecarga cognitiva injustificada, todo para resolver un "ciclo fantasma" que jamás existió.

---

### 8. Según Fowler, UML puede usarse como boceto, plano o lenguaje de programación. ¿Cuál de esos usos aplicó en este laboratorio y por qué es adecuado para un MVP de 1 mes?
* **Clasificación de Martin Fowler (UML Distilled):**
  1. **UML como Boceto (Sketch):** Diagramas rápidos, informales y parciales dibujados en pizarras o libretas para comunicar ideas preliminares entre ingenieros y luego descartarse.
  2. **UML como Plano (Blueprint):** Diagramas detallados, precisos y formalmente consistentes que especifican la estructura y el comportamiento previo a la programación, sirviendo de guía rigurosa para los desarrolladores.
  3. **UML como Lenguaje de Programación (Executable UML):** Modelos completos y ejecutables que compilan automáticamente a código fuente de producción sin intervención manual.

**Uso aplicado en este laboratorio y justificación:**  
En este laboratorio aplicamos **UML como Plano (Blueprint)**.
* **¿Por qué es adecuado para un MVP de 1 mes?**  
  Para un equipo reducido de 2 ingenieros con un plazo perentorio de 30 días, el uso de UML como boceto es insuficiente porque deja demasiadas ambigüedades técnicas que desembocan en retrabajo costoso, interfaces incompatibles y discusiones de diseño a mitad del sprint. Por otro lado, UML como lenguaje de programación es inviable porque las herramientas MDA/Executable UML son extremadamente complejas, rígidas y costosas.  
  El enfoque de **Plano** proporciona el balance perfecto: permite acordar contractualmente los puertos, la máquina de estados y las firmas de métodos antes de programar, habilitando el trabajo en paralelo de los desarrolladores y la generación asistida de esqueletos con IA, reduciendo los tiempos de integración y garantizando cero sorpresas en producción.
