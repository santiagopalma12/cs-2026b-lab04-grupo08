# Cuestionario — Laboratorio 04: Fundamentos de Arquitectura de Software
**Construcción de Software · EPIS-UNSA · 2026-B · Grupo 08**  
**Integrantes:** Santiago Palma (`santiagopalma12`), Dario Rafael Cornejo Hurtado (`darich1010`)  
**Caso de Estudio:** Caso 8 — SismoReporta AQP

---

### 1. ¿Por qué se afirma que una decisión arquitectónica es aquella "costosa de cambiar"? Dé un ejemplo de su caso.
Según Bass, Clements y Kazman (2021) y Martin Fowler, las decisiones arquitectónicas son aquellas que dan forma a las estructuras fundamentales del sistema y sobre las cuales descansan múltiples subsistemas e implementaciones posteriores. Cambiarlas tarde en el ciclo de vida no implica simplemente refactorizar unas cuantas clases o funciones, sino demoler cimientos técnicos, reescribir contratos de datos, migrar esquemas de persistencia y alterar los supuestos operativos del equipo, lo que se traduce en semanas o meses de trabajo perdido, altísimos costos económicos y severo riesgo de regresiones.

**Ejemplo en SismoReporta AQP:**  
La decisión de adoptar un **modelo de cliente Offline-First basado en PWA con IndexedDB y sincronización diferida** frente a un modelo Web tradicional síncrono. Si hubiésemos asumido erróneamente que la red móvil siempre estaría disponible y programado todas las pantallas asumiendo llamadas HTTP síncronas bloqueantes, revertir esa decisión tras el colapso del sistema en un sismo requeriría reestructurar el 100% del frontend (manejo de estado local, colas en el navegador, resolución de conflictos de concurrencia y reintentos) y rediseñar los endpoints del backend para soportar idempotencia y recepción por lotes, implicando un costo de retrabajo inasumible.

---

### 2. ¿Cuál es la diferencia entre un requisito funcional y un atributo de calidad? ¿Por qué los atributos de calidad influyen más en la arquitectura?
* **Requisito Funcional (RF):** Expresa **lo que el sistema debe hacer**; describe las capacidades, comportamientos, casos de uso y transformaciones de entrada a salida que el software provee a sus usuarios (ej. *"El ciudadano registra un reporte de colapso con foto"* o *"El brigadista consulta la lista de incidentes asignados"*).
* **Atributo de Calidad (QA):** Expresa **qué tan bien o bajo qué condiciones de exigencia** el sistema realiza dichas funciones; cualifica las propiedades intrínsecas del producto según la norma ISO/IEC 25010:2023, tales como rendimiento, disponibilidad, tolerancia a fallos, seguridad, usabilidad y modificabilidad.

**¿Por qué los atributos de calidad influyen más en la arquitectura?**  
Cualquier función de negocio puede implementarse conceptualmente mediante cualquier lenguaje o estructura arbitraria (un simple script PHP de un solo archivo puede registrar un reporte de daños en una tabla). Sin embargo, cuando se le exige a esa función responder a **20,000 usuarios concurrentes en menos de 1.5 segundos con una red móvil congestionada y tolerancia a cortes totales de señal**, el script simple fracasa de inmediato. Los atributos de calidad son los verdaderos *drivers* que fuerzan las decisiones estructurales: exigen particionamiento de datos, brokers de mensajería asíncrona (Redis), cachés en memoria, protocolos desacoplados y redundancia perimetral.

---

### 3. Reescriba el requisito "el sistema debe ser seguro" como un escenario de atributo de calidad de seis partes.
La afirmación *"el sistema debe ser seguro"* es ambigua, subjetiva y no verificable. Aplicando el marco formal de escenarios de 6 partes de Bass et al. (2021) en el contexto de la norma ISO/IEC 25010:2023 (Seguridad: confidencialidad, integridad y autenticidad), se reescribe de la siguiente forma:

| Parte | Pregunta | Definición para SismoReporta AQP |
| :--- | :--- | :--- |
| **Fuente del estímulo** | ¿Quién o qué genera el evento? | Un actor malicioso externo no autorizado (o script bot automatizado). |
| **Estímulo** | ¿Qué acción o ataque se ejecuta? | Intenta inyectar 1,000 reportes falsos con coordenadas aleatorias y enviar peticiones maliciosas de SQL Injection en el campo de descripción para acceder a los números telefónicos y datos personales de los denunciantes. |
| **Entorno** | ¿Bajo qué condiciones operativas? | Operación crítica activa en producción tras un sismo (pico de tráfico y red congestionada). |
| **Artefacto** | ¿Qué parte del sistema recibe el ataque? | Proxy perimetral Nginx, Gateway FastAPI (esquemas Pydantic / ORM) y base de datos PostgreSQL. |
| **Respuesta del sistema** | ¿Qué debe hacer el software? | Nginx bloquea el origen abusivo mediante *Rate Limiting*; los validadores de esquema sanean los inputs neutralizando cualquier inyección SQL; se verifica la geocerca de Arequipa y se cifra en reposo (AES-256) todo dato personal de contacto. |
| **Medida de respuesta** | ¿Cómo se verifica objetivamente? | **100% de los intentos de inyección y reportes fuera de perímetro bloqueados**; 0 registros de datos personales expuestos; el incidente de seguridad queda registrado en los logs de auditoría en **$\le 50$ milisegundos**. |

---

### 4. Compare el monolito modular y los microservicios en términos de costo, modificabilidad y complejidad operativa. ¿En qué momento convendría migrar de uno a otro?

| Criterio | Monolito Modular Asíncrono | Microservicios Distribuidos |
| :--- | :--- | :--- |
| **Costo** | **Muy bajo:** Se despliega como un único artefacto ejecutable en un solo VPS económico (\$10-\$20/mes); comparte recursos de CPU/RAM de forma eficiente y no requiere costos de transferencia entre servicios en nube. | **Alto:** Requiere infraestructura elástica (múltiples nodos o clúster Kubernetes EKS/GKE), múltiples bases de datos independientes, colas administradas (Kafka/MSK) y herramientas de telemetría distribuida de alto costo. |
| **Modificabilidad** | **Alta en desarrollo, acoplada en despliegue:** Los límites de dominio (*Bounded Contexts*) están bien definidos en el código mediante interfaces. Modificar un módulo es limpio, pero actualizarlo requiere recompilar y desplegar nuevamente el artefacto completo. | **Máxima y autónoma:** Cada servicio tiene su propio ciclo de vida y repositorio. Equipos independientes pueden modificar, testear y desplegar el servicio de Triaje sin tocar el de Mapas. |
| **Complejidad Operativa** | **Baja:** Un solo pipeline de CI/CD, base de datos única con esquemas lógicos, transacciones ACID nativas locales, depuración sencilla con trazas directas y métricas unificadas. | **Extrema:** Requiere resolver consistencia eventual, transacciones distribuidas (patrón Saga), service discovery, latencia de red en cada salto HTTP/gRPC, fallos parciales de red y trazas distribuidas complejas (OpenTelemetry/Jaeger). |

**¿En qué momento convendría migrar de Monolito Modular a Microservicios?**  
La migración solo se justifica cuando se cruzan los siguientes umbrales:
1. **Escala de Equipos (Ley de Conway):** Cuando la organización crece a más de 3 o 4 equipos de desarrollo independientes (más de 25 ingenieros) y el despliegue del monolito genera cuellos de botella organizacionales.
2. **Crecimiento Asimétrico de Carga:** Cuando un módulo específico (por ejemplo, el procesamiento de coordenadas espaciales o la compresión de video) demanda el 95% del consumo de cómputo y se vuelve económicamente inviable escalar el monolito completo, requiriendo extraer únicamente ese componente como un microservicio elástico independiente.
3. **Requisitos de Disponibilidad Aislada:** Si una falla en el módulo de mapas bajo ninguna circunstancia debe comprometer el ciclo de vida del módulo de ingesta y recepción de emergencias.

---

### 5. ¿Qué ventajas ofrece Diagram as Code frente a herramientas de dibujo como PowerPoint? Mencione al menos tres.
1. **Control de Versiones y Trazabilidad en Git:**  
   Al ser archivos de texto plano (`.mmd`, `.puml`, `.py`), los diagramas se versionan en el mismo repositorio que el código de la aplicación. Es posible inspeccionar diferencias línea por línea (`git diff`), entender exactamente qué componente o conexión fue modificada en cada commit y asociar cambios arquitectónicos a Pull Requests específicos, lo cual es imposible con archivos binarios `.pptx` o `.drawio`.
2. **Revisión Colaborativa por Pares (Code Review) y CI/CD:**  
   Los cambios en la arquitectura se discuten de forma rigurosa en GitHub mediante revisiones de código de Pull Requests. Además, se integran en pipelines automatizados de CI/CD (GitHub Actions) que validan la sintaxis y renderizan automáticamente las imágenes oficiales sin intervención manual.
3. **Sinergia Óptima con Asistentes de IA y Mantenibilidad:**  
   Los Modelos de Lenguaje (LLMs) procesan, generan y corrigen texto con facilidad, pero carecen de la capacidad de manipular elementos gráficos de interfaz de usuario de PowerPoint. *Diagram as Code* permite solicitar a la IA la adición de un nuevo módulo o la refactorización de dependencias directamente en código, manteniendo la fuente de verdad siempre actualizada.

---

### 6. ¿Qué elementos debe contener un ADR y por qué es importante registrar también las alternativas descartadas?
Un **Architecture Decision Record (ADR)** formal (siguiendo el estándar de Michael Nygard y la plantilla del laboratorio) debe contener:
* **Título y Numeración:** Identificador único y resumen declarativo (ej. *ADR-001: Adopción de Monolito Modular*).
* **Metadatos:** Estado (*Propuesto*, *Aceptado*, *Rechazado*, *Reemplazado*), Fecha de aprobación y Decisores involucrados.
* **Contexto:** El problema técnico o de negocio que motiva la decisión, citando explícitamente los drivers arquitectónicos (Requisitos Funcionales, Atributos de Calidad y Restricciones del proyecto).
* **Alternativas Consideradas:** Relación comparativa de las opciones evaluadas con sus trade-offs y puntajes de decisión.
* **Decisión:** Enunciado en voz activa (*"Adoptaremos...", "Usaremos..."*) que detalla la solución elegida y sus lineamientos de implementación.
* **Consecuencias:** Análisis honesto y transparente de los impactos positivos (beneficios) y los impactos negativos / riesgos introducidos, junto con sus estrategias de mitigación.

**¿Por qué es importante registrar también las alternativas descartadas?**  
Registrar lo que **no** se eligió previene la amnesia colectiva en los equipos de ingeniería. Cuando nuevos desarrolladores se incorporan al proyecto o transcurren los meses, es común que surja la duda: *"¿Por qué no usamos microservicios o MongoDB aquí?"*. Si la alternativa descartada está documentada con su justificación técnica (demostrando que se descartó por el plazo de 1 mes y el presupuesto bajo de VPS), se evita reabrir debates ya zanjados, se respeta el diseño original y se comprende bajo qué condiciones futuras sí sería válido reconsiderar esa alternativa.

---

### 7. Describa un caso de esta práctica en el que la IA haya generado una propuesta incorrecta o sesgada. ¿Cómo lo detectaron?
**Caso Real (Interacción 4 de la Bitácora de IA):**  
Al consultar a la IA (*ChatGPT / Claude*) sobre la viabilidad de utilizar la **Background Sync API** de los Service Workers en Progressive Web Apps (PWA) para garantizar que los reportes de sismos guardados en IndexedDB se transmitieran automáticamente en segundo plano cuando el celular recuperara señal, la IA afirmó con total seguridad que la API funcionaba de forma homogénea, nativa e ininterrumpida tanto en Android como en iOS (Safari/WebKit).

**¿Cómo lo detectamos?**  
El equipo auditó la respuesta contrastándola con la documentación oficial de compatibilidad en **MDN Web Docs** y los reportes de estatus del motor WebKit de Apple. Se constató que iOS Safari tiene un soporte nulo o altamente restringido para Background Sync fuera de foco por políticas agresivas de ahorro de batería de Apple. Si hubiésemos aceptado ciegamente la respuesta de la IA, los usuarios de iPhone habrían perdido la sincronización automática una vez cerrada la PWA.  
*Corrección implementada:* Modificamos el diseño arquitectónico y el [ADR-002](docs/architecture/adr/002-estrategia-offline-pwa.md) para añadir manejadores de eventos en `visibilitychange` y `focus`, asegurando que al reabrir la app se dispare el vaciado forzado de la cola local sin depender exclusivamente de la API nativa de background.

---

### 8. ¿Qué riesgos éticos y de confidencialidad existen al usar asistentes de IA para diseñar la arquitectura de un sistema real?
1. **Fuga y Exposición de Información Confidencial / Privacidad (Ley 29733):**  
   Al redactar prompts describiendo la arquitectura o casos de uso, existe el grave riesgo de incluir credenciales, direcciones IP privadas de servidores, topologías confidenciales de red o información personal de usuarios reales (DNI, teléfonos, geolocalizaciones sensibles). Muchas plataformas de IA utilizan los datos de entrada para reentrenar modelos comerciales, lo que podría exponer vulnerabilidades del sistema a terceros o violar leyes de protección de datos personales.
2. **Alucinaciones y Falsa Sensación de Seguridad en Sistemas Críticos:**  
   En sistemas de protección civil y gestión de desastres donde hay vidas humanas en juego, una sugerencia de la IA que asuma falsamente que una biblioteca tiene capacidades transaccionales seguras o que una API resistirá ráfagas extremas puede provocar caídas catastróficas durante una emergencia real si no es validada experimentalmente por ingenieros humanos.
3. **Sesgos hacia la Complejidad Innecesaria y Consumo Energético:**  
   Los modelos están sesgados hacia arquitecturas corporativas complejas de las que abunda literatura en internet (Kubernetes, clusters en AWS, microservicios sobredimensionados). Fomentar este sobre-diseño (*over-engineering*) encarece innecesariamente los proyectos públicos, retrasa los tiempos de respuesta ante emergencias y genera un consumo energético y huella de carbono innecesarios.
4. **Dilución de la Responsabilidad Profesional y Legal:**  
   La responsabilidad civil y ética por el fallo de un sistema de emergencias recae siempre en los ingenieros colegiados y decisores humanos, nunca en un algoritmo de IA generativa. Subordinar el criterio arquitectónico a la máquina sin auditoría rigurosa constituye una falta grave a la ética profesional de la ingeniería de sistemas.
