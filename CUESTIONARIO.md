# Cuestionario Oficial — Laboratorio 08: Diseño Arquitectónico con ADD, ATAM-lite y Fitness Functions

**Asignatura:** Construcción de Software (2026-B)  
**Grupo:** 08 — SismoReporta AQP  
**Integrantes:**  
- Santiago Palma (`spalmaa@unsa.edu.pe`)  
- Dario Rafael Cornejo Hurtado (`dcornejohu@unsa.edu.pe`)  
**Docente:** Mg. Alexander Javier Benavides Rojas  
**Fecha:** 31 de Octubre de 2026  

---

### Pregunta 1: ¿En qué se diferencia diseñar la arquitectura con ADD de elegir un estilo arquitectónico como en el Laboratorio 04?

**Respuesta:**  
La diferencia radica en que **elegir un estilo arquitectónico** (Lab 04) es una decisión macroscópica de una sola vez que establece la estructura global de alto nivel (por ejemplo, seleccionar un *Monolito Modular* frente a *Microservicios* o *Serverless*), mientras que **diseñar con Attribute-Driven Design (ADD 3.0)** (Lab 08) es un **proceso iterativo, guiado y sistemático** de refinamiento paso a paso, cuyo motor son los atributos de calidad concretos expresados en escenarios medibles:

1. **Granularidad y Enfoque:**
   - En el Laboratorio 04, el estilo arquitectónico se seleccionó para acotar el universo de diseño respondiendo a restricciones globales (plazo de 1 mes, presupuesto de 1 VPS de \$15 USD/mes, equipo de 2 ingenieros). El estilo actúa como marco contenedor (*coarse-grained*).
   - En ADD 3.0 (Cervantes y Kazman, 2016; Bass et al., 2021), no se asume que el estilo resuelve mágicamente la calidad. En cada iteración se toma un elemento del sistema y se le aplican **tácticas arquitectónicas específicas** (ej. *Buffer asíncrono con Fast ACK*, *Circuit Breaker*, *Row-Level Security*) para satisfacer un escenario cuantificable prioritario ($p95 \le 1.5\text{ s}$, 0 pérdidas).
2. **Evidencia y Decisiones Fundamentadas:**
   - En la elección de estilo se compara conceptualmente con matrices ponderadas. En ADD, cada decisión táctica exige **evidencia cuantitativa experimental** (simulación estocástica M/G/c, modelo Monte Carlo o prototipo medido) que demuestre que el escenario se cumple antes de comprometer la decisión en un ADR.
3. **Evolución:**
   - ADD permite descomponer contenedores en componentes e interfaces de forma progresiva a lo largo de 7 pasos formales, adaptando el sistema ante escenarios de crecimiento sin necesidad de derribar el estilo arquitectónico base.

---

### Pregunta 2: ¿Para qué sirve calificar los escenarios con (importancia, dificultad)? ¿Qué escenario de su árbol tiene la mayor prioridad y por qué?

**Respuesta:**  
La calificación bidimensional **(Importancia para el Negocio / Stakeholders, Dificultad Técnica de Implementación)** en escala High (H), Medium (M), Low (L) cumple una función estratégica fundamental en la priorización arquitectónica:

- **Propósito Metodológico:**
  Permite clasificar los escenarios en una matriz de cuatro cuadrantes. Los escenarios calificados como **(H, H)** representan el **núcleo crítico del riesgo arquitectónico** (*architecturally significant requirements - ASR*). Estos escenarios son los primeros que deben abordarse en las primeras iteraciones de ADD, ya que determinan las decisiones no reversibles de la arquitectura. Intentar resolver escenarios de baja dificultad o baja importancia al inicio pospone los riesgos mayores al final del proyecto, aumentando la probabilidad de colapso (*fail late*).

- **Escenario con Mayor Prioridad en SismoReporta AQP:**
  El escenario con mayor prioridad es **QA-01 (H, H) — Ingesta Masiva durante el Simulacro Nacional**:
  > *"Cuando 20 000 ciudadanos emiten reportes de incidentes en el lapso de 1 hora bajo una red móvil congestionada en la provincia de Arequipa (tasa pico de 28 req/s), el sistema procesa las solicitudes respondiendo con p95 \le 1.5 s, sin saturar sockets ni disparar timeouts 504."*
  
- **Justificación:**
  1. *Importancia de Negocio (H):* Es el propósito fundamental y de supervivencia de la plataforma. Si durante los primeros 60 minutos de una crisis telúrica el sistema colapsa por denegación de servicio, los ciudadanos perderán la confianza, los datos de personas atrapadas no llegarán a Defensa Civil y la plataforma resultará inútil para salvar vidas.
  2. *Dificultad Técnica (H):* Exige absorber picos de concurrencia extremos dentro de la restricción severa de hardware de un único VPS modesto (2 vCPUs y 4 GB de RAM), impidiendo el procesamiento síncrono tradicional de geolocalización PostGIS e imágenes en el hilo HTTP.

---

### Pregunta 3: ¿Qué diferencia hay entre una táctica y un patrón? Ilustre con el circuit breaker.

**Respuesta:**  
La diferencia esencial entre táctica y patrón se define en función de su **naturaleza, nivel de abstracción y alcance de diseño**:

- **Táctica Arquitectónica (Bass, Clements y Kazman, 2021):**
  Es una **decisión de diseño elemental** enfocada en controlar la respuesta de un único atributo de calidad específico (rendimiento, disponibilidad, seguridad, modificabilidad). Una táctica describe *qué principio fundamental se aplica*, sin prescribir cómo se implementa en clases u objetos de código fuente.
  - *En Disponibilidad:* La táctica es **"Prevenir la propagación de fallas / Falla Rápida (Fail-Fast)"** y **"Degradación elegante"**, evitando sobrecargar un recurso dependiente que no está respondiendo.
  
- **Patrón de Software (GoF / POSA / Nygard):**
  Es una **solución estructural empaquetada y reusable** a un problema recurrente dentro de un contexto dado, que describe un conjunto coordinado de componentes, responsabilidades y colaboraciones entre clases u objetos. Un patrón suele materializar o combinar una o varias tácticas arquitectónicas.

- **Ilustración con el Circuit Breaker:**
  - *Como Táctica:* Consiste en cortar inmediatamente el flujo de peticiones hacia un servicio no disponible tras superar un umbral de fallas consecutivas, liberando hilos de ejecución y permitiendo que el sistema dependiente se recupere.
  - *Como Patrón (Nygard, 2018):* Se implementa mediante una máquina de estados finita explícita con tres estados (`CERRADO`, `ABIERTO`, `SEMIABIERTO`), contadores de fallas temporizados, mecanismos de sondeo (*canary requests*) y la aplicación del patrón estructural **Decorator** (como en `ConCircuitBreaker` en Python), encapsulando la interfaz del servicio sin modificar a los consumidores.

---

### Pregunta 4: Describa un punto de sensibilidad y un punto de trade-off de su arquitectura, con la evidencia que los respalda.

**Respuesta:**  

1. **Punto de Sensibilidad (S1 — Tiempo de Encolamiento en Redis):**
   - *Descripción:* La latencia global de respuesta $p95$ ante el simulacro nacional es críticamente sensible al tiempo de persistencia en memoria del payload en Redis mediante `LPUSH` y a la ausencia de operaciones I/O bloqueantes en el hilo de FastAPI. Si en el endpoint de recepción se introduce inadvertidamente una validación espacial relacional en disco (`ST_Within`) o una llamada de red síncrona a un servicio externo, la latencia se degrada de $16.4\text{ ms}$ a más de $1800\text{ ms}$, violando el presupuesto de QA-01.
   - *Evidencia Cuantitativa:* En `fitness/rendimiento.py`, la simulación M/G/c demostró que la función síncrona sin buffer a 28 req/s satura la cola ($\rho = 1.68$) con $p95 = 213.8\text{ s}$, mientras que el buffer Redis con respuesta asíncrona pura opera a $\rho = 0.07$ logrando $p95 = 16.4\text{ ms}$.

2. **Punto de Trade-off (T1 — Rendimiento de Ingesta vs. Consistencia Inmediata):**
   - *Descripción:* Al aplicar la táctica de *Buffer Asíncrono con Fast ACK HTTP 202*, se optimiza drásticamente el Rendimiento ($p95 \le 16.4\text{ ms}$), pero se penaliza la Consistencia Inmediata (Eventual Consistency). El reporte no se encuentra inmediatamente indexado en la base de datos geográfica de PostGIS, sino que existe una ventana temporal de inconsistencia de 1 a 3 segundos mientras Celery consume la cola y genera los índices de calor.
   - *Evidencia:* Se midió el tiempo medio de espera en la cola Celery ($W_q \approx 2.1\text{ s}$) a máxima carga de 28 req/s. Se concluyó que este trade-off es plenamente favorable, ya que en una emergencia sísmica es infinitamente preferible tener consistencia eventual de 2 segundos que perder reportes por timeouts HTTP 504.

---

### Pregunta 5: ¿Qué supuestos hizo su simulación y cómo podrían invalidar la decisión si fueran falsos?

**Respuesta:**  
En las simulaciones ejecutadas en `fitness/rendimiento.py` y `fitness/disponibilidad.py` se asumieron tres supuestos técnicos clave:

1. **Llegadas con Proceso de Poisson (Distribución Exponencial entre arribos):**
   - *Supuesto:* Los 20 000 reportes en 1 hora arriban de forma aleatoria independiente siguiendo un proceso de Poisson con tasa media $\lambda = 5.56\text{ req/s}$ y ráfagas pico estacionarias de $\lambda = 28\text{ req/s}$.
   - *Cómo invalidaría la decisión:* Si tras el terremoto real se produce un arribo sincronizado masivo de tipo impulso Dirac (por ejemplo, 10 000 peticiones en exactamente 2 segundos provocadas por una alerta pública en televisión), el buffer Redis absorbería los sockets pero la cola en memoria podría saturar la capacidad de consumo de los 4 workers de Celery, incrementando el retraso de visualización en el mapa a más de 5 minutos.
2. **Independencia en los Tiempos de Servicio (Distribución Lognormal Calibrada):**
   - *Supuesto:* Cada petición de FastAPI requiere en promedio 2.5 ms ($\sigma = 0.3$) para serializar y encolar en Redis, asumiendo ancho de banda de bus interno local (`localhost`/socket Unix).
   - *Cómo invalidaría la decisión:* Si Redis estuviera alojado en un nodo remoto sobre red WAN con alta fluctuación de latencia de red ($> 50\text{ ms}$), el hilo de FastAPI esperaría por el ACK de red, invalidando la respuesta inmediata y requiriendo un buffer local en la memoria del propio proceso Gunicorn.
3. **Persistencia Permanente en Almacenamiento IndexedDB del Cliente:**
   - *Supuesto:* Se asumió que los smartphones de los ciudadanos no son reiniciados de fábrica ni el usuario limpia compulsivamente el almacenamiento de su navegador PWA durante los 20 minutos de corte de señal.
   - *Cómo invalidaría la decisión:* Si el sistema operativo móvil (ej. iOS en modo de bajo almacenamiento) purga la caché de IndexedDB para liberar espacio antes de que el Circuit Breaker cierre y sincronice, los reportes locales se perderían antes del drenado.

---

### Pregunta 6: ¿Qué riesgo de la evaluación cruzada aceptaron sin mitigarlo y por qué es razonable para un plazo de 1 mes?

**Respuesta:**  

- **Riesgo Aceptado:**
  **Riesgo R2 — Punto Único de Falla (SPOF) en la Instancia Única de PostgreSQL / VPS (Severidad: 12 - Probabilidad: 3, Impacto: 4).**
  La evaluación ATAM-lite formuló la pregunta incómoda: *"Si el servidor VPS físico en la nube sufre un corte eléctrico catastrófico durante el terremoto, ¿cómo garantizan un MTTR < 15 min sin un clúster de alta disponibilidad multi-región?"*

- **Justificación de por qué es razonable aceptarlo para el plazo de 1 mes:**
  1. *Restricción de Recursos y Plazo (R-01, R-02, R-03):* Configurar un clúster PostgreSQL de alta disponibilidad con replicación síncrona multizona (Patroni + etcd + PgBouncer) requiere al menos 3 instancias independientes (\$60-\$120 USD/mes), violando directamente la restricción presupuestaria de \$15 USD/mes (R-03).
  2. *Curva de Complejidad Operativa:* Para un equipo de 2 desarrolladores en un plazo de 1 mes, depurar particiones de red (*split-brain*) y pruebas de conmutación en clústeres distribuidos consumiría más del 60% del tiempo del proyecto, sacrificando las funcionalidades vitales de triaje y la PWA ciudadana.
  3. *Mitigación Compensatoria Aceptada:* Se mitigó el impacto mediante una estrategia pragmática: **PWA Offline-First** (los reportes siguen acumulándose en los celulares de los usuarios aunque el servidor esté caído), snapshots horarios automatizados del volumen SSD a nivel de hipervisor, y un script de recuperación automatizada mediante Docker Compose con $\text{MTTR} \le 15\text{ minutos}$ documentado en el plan de contingencia.

---

### Pregunta 7: Explique qué es una fitness function y qué degradación concreta de su arquitectura detectaría cada una de las suyas.

**Respuesta:**  
Una **Fitness Function Arquitectural** (Ford, Parsons, Kua y Sadalage, 2022) es una prueba automatizada, objetiva e integrada en el pipeline de Integración Continua (CI) que evalúa si la arquitectura de software preserva sus características deseadas y no se degrada con el tiempo ante cambios en el código fuente.

En SismoReporta AQP, cada fitness function protege el sistema contra una degradación concreta:

1. **FF-01 (Estructural — Capas sin ciclos en el monolito modular, ADR-001):**
   - *Herramienta:* `import-linter` (tipo: `layers`).
   - *Degradación que detecta:* Si un programador añade un atajo temporal importando el servicio de aplicación desde los estados o entidades de dominio (`sismoreporta.estados -> sismoreporta.servicio`), la prueba falla inmediatamente en CI, impidiendo la formación de grafos acoplados y dependencias circulares que convierten el monolito en una "gran bola de lodo".
2. **FF-02 (Estructural — Aislamiento de adaptadores externos, ADR-005):**
   - *Herramienta:* `import-linter` (tipo: `forbidden`).
   - *Degradación que detecta:* Si una entidad nuclear del dominio o un comando importa directamente SDKs externos o drivers concretos (`sismoreporta.externos`, como Redis, RabbitMQ o Twilio), la prueba bloquea el Pull Request, garantizando que el dominio solo conozca abstracciones (Puertos).
3. **FF-03 (Calidad — Presupuesto de Rendimiento en Simulacro, QA-01):**
   - *Herramienta:* `pytest` sobre `fitness.rendimiento.simular`.
   - *Degradación que detecta:* Si alguien modifica el endpoint de ingesta eliminando el Fast ACK HTTP 202 o reintroduciendo tareas síncronas pesadas, el cálculo de $p95$ a 28 req/s superará los $1500\text{ ms}$, disparando un aserto que rompe el build.
4. **FF-04 (Calidad — Integridad y Cero Pérdida de Reportes, QA-02):**
   - *Herramienta:* `pytest` sobre `fitness.disponibilidad.simular`.
   - *Degradación que detecta:* Si se desactiva el drenado del Outbox persistente o se altera la lógica de almacenamiento local, el número de reportes perdidos tras una interrupción superará $0$, bloqueando la integración.
5. **FF-05 (Calidad — Protección contra Thundering Herd, Mitigación R3):**
   - *Herramienta:* `pytest` comparativo (`simular("breaker")` vs `simular("reintentos")`).
   - *Degradación que detecta:* Si un desarrollador reduce el enfriamiento del Circuit Breaker o implementa reintentos inmediatos sin Jitter, el número de llamadas durante una caída se disparará por encima de la quinta parte de la línea base, fallando la aserción.
6. **FF-06 (Calidad — Aislamiento Multidistrital RLS, QA-04 / Mitigación R4):**
   - *Herramienta:* `pytest` con consulta parametrizada multi-tenant.
   - *Degradación que detecta:* Si una migración de base de datos desactiva la directiva `ENABLE ROW LEVEL SECURITY` o introduce una cláusula SQL que permite a un usuario de *Yanahuara* leer filas de *Cerro Colorado*, la prueba detecta la filtración y bloquea el despliegue.

---

### Pregunta 8: ¿Qué propuesta de la IA rechazaron con evidencia? ¿Qué habría pasado si la aceptaban sin medir?

**Respuesta:**  

- **Propuesta de la IA Rechazada:**
  Durante la Iteración 1 de ADD (Prompt IA 2) y la posterior crítica adversarial de ATAM-lite (Riesgo R5), la IA sostuvo insistentemente que:
  > *"Un monolito en Python con Celery colapsará inevitablemente bajo 20 000 peticiones en 1 hora debido al Global Interpreter Lock (GIL) y la sobrecarga del event loop. Para el simulacro nacional es mandatorio rediseñar la arquitectura hacia microservicios distribuidos desarrollados en Go o Rust, orquestados sobre un clúster Kubernetes (EKS/GKE) con Apache Kafka."*

- **Evidencia Cuantitativa que la Refutó:**
  El equipo realizó el cálculo matemático dimensional y ejecutó la simulación de colas en `fitness/rendimiento.py`:
  1. *Carga Real:* 20 000 reportes en 1 hora equivalen a una tasa promedio de **$5.56\text{ reportes/segundo}$**, con picos estocásticos de **$28\text{ req/s}$**.
  2. *Capacidad Medida:* Un único proceso Celery en Python ejecutando queries espaciales simples en PostgreSQL procesa entre 80 y 150 operaciones por segundo. Con 4 workers Celery independientes (procesos de SO separados que no comparten GIL), la capacidad de procesamiento del backend supera los **$400\text{ reportes/segundo}$**, lo que representa un margen de holgura de más del **$1400\%$** frente al pico del simulacro.
  3. *Utilización:* La simulación demostró que con el buffer en Redis y Fast ACK, la latencia es de $p95 = 16.4\text{ ms}$ con una utilización de buffer de tan solo $\rho = 0.07$ (7% de carga).

- **¿Qué habría pasado si la aceptaban sin medir?**
  1. **Quiebre del Presupuesto (R-03):** El clúster Kubernetes administrado con Kafka de 3 nodos habría incrementado el costo mensual de \$15 USD a más de \$180 USD/mes, haciendo inviable el proyecto para el presupuesto asignado.
  2. **Fracaso en la Entrega (R-01):** Reimplementar el sistema en Go/Rust y configurar mallas de servicio, observabilidad distribuida y manifiestos de Kubernetes con un equipo de solo 2 desarrolladores habría demandado al menos 4 meses de trabajo, incumpliendo el plazo fatal de 1 mes para el simulacro.
  3. **Vulnerabilidad a Errores Operativos:** La sobrecomplejidad arquitectónica no justificada (*accidental complexity*) habría multiplicado los puntos de falla en producción durante el evento sísmico.
