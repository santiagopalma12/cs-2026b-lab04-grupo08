# Bitácora de Uso Crítico de Inteligencia Artificial (E7)

**Curso:** Construcción de Software · EPIS-UNSA · 2026-B  
**Laboratorio 05:** Diagramas de Diseño UML 2.5.1  
**Caso de Estudio:** Caso 8 — SismoReporta AQP  
**Equipo:** Santiago Palma (`santiagopalma12`), Dario Rafael Cornejo Hurtado (`darich1010`)  

---

## Principio Metodológico
> **Regla de oro:** *La IA propone, el equipo decide y verifica.*  
> Ninguna propuesta de código o diagrama generada por modelos generativos se incorporó al proyecto sin contrastación previa contra las reglas de consistencia C1–C5, el ADR-001 y las restricciones de conectividad y hardware del entorno Arequipa post-sismo.

---

## Registro de Interacciones

### Interacción 1: Generación del Diagrama de Clases Estructural (E1)
* **Fecha:** 2026-10-06
* **Herramienta:** Anthropic Claude 3.5 Sonnet
* **Prompt IA:**  
  ```text
  Actúa como arquitecto de software orientado a objetos. Contexto: Sistema de emergencias
  SismoReporta AQP (monolito modular con puertos y adaptadores según ADR-001).
  Historia de usuario: [pegar HU-08 con criterios de aceptación Dado/Cuando/Entonces].
  Tarea: Genera un diagrama de clases en PlantUML que modele la entidad Reporte,
  geolocalización, evidencias y puertos hacia el broker de mensajería Redis y repositorio PostGIS.
  Incluye visibilidad, atributos tipados, multiplicidades en todos los extremos y operaciones.
  ```
* **Propuesta de la IA:**  
  Generó un modelo con 7 clases. Sin embargo:
  1. Incluyó atributos como `dniCompleto` y `nombreCompleto` en la clase `Ciudadano`.
  2. Definió `FotoEvidencia` con multiplicidad `0..*` ilimitada.
  3. Modeló la pasarela de Redis como herencia directa de una clase concreta `RedisConnection`.
* **Verificación Crítica:**  
  1. Almacenar el DNI completo y nombres viola la privacidad y las recomendaciones del checklist (no almacenar datos sensibles innecesarios durante emergencias anónimas).
  2. Permitir fotos ilimitadas colapsaría la red móvil 3G/4G degradada (restricción ADR-002).
  3. La conexión directa a Redis violaba la inversión de dependencias y el patrón Puertos y Adaptadores del ADR-001.
* **Decisión Adoptada:**  
  **Modificada sustancialmente.** Se anonimizó `identificadorAnonimo`, se restringió la multiplicidad de fotos a `0..3` con compresión forzada, y se definió la interfaz `IBrokerCola` con su adaptador desacoplado `RedisBrokerAdapter`.

---

### Interacción 2: Diagrama de Secuencia del Flujo de Sincronización (E2)
* **Fecha:** 2026-10-07
* **Herramienta:** OpenAI GPT-4o
* **Prompt IA:**  
  ```text
  Genera un diagrama de secuencia en PlantUML para el flujo "Sincronización de lote de reportes
  offline desde PWA hacia el backend". Debe incluir al menos 5 líneas de vida, fragmentos alt
  para éxito y rechazo por geocerca, un bucle loop para procesar la lista, y al menos un mensaje
  asíncrono. Asegura que cada mensaje coincida con las operaciones del diagrama de clases adjunto.
  ```
* **Propuesta de la IA:**  
  El diagrama planteó un flujo síncrono donde el backend esperaba que PostGIS ejecutara la clusterización y el triaje antes de responder con `HTTP 200` al celular del ciudadano.
* **Verificación Crítica:**  
  Esperar el triaje síncrono bloquea la conexión HTTP por más de 800 ms. Con 20,000 conexiones concurrentes, Nginx agotaría su pool de sockets (violando el driver de latencia $p95 \le 1.5\text{ s}$).
* **Decisión Adoptada:**  
  **Corregida.** Se transformó la respuesta HTTP en un inmediato `HTTP 202 Accepted` tan pronto como el reporte se persiste y se envía asíncronamente (`->>`) al broker Redis, delegando el triaje a los workers en background.

---

### Interacción 3: Máquina de Estados del Reporte (E3)
* **Fecha:** 2026-10-08
* **Herramienta:** Google Gemini 1.5 Pro
* **Prompt IA:**  
  ```text
  Genera en Mermaid (stateDiagram-v2) la máquina de estados para la entidad Reporte de
  SismoReporta AQP. Estados obligatorios: BORRADOR, ENCOLADO, RECIBIDO, VERIFICADO, ATENDIDO.
  Incluye transiciones con operaciones explícitas, guardas entre corchetes, y tratamiento
  de reportes duplicados espaciales.
  ```
* **Propuesta de la IA:**  
  Mermaid diagram con los 5 estados solicitados más el estado `DESCARTADO`. No obstante, la transición entre `RECIBIDO` y `VERIFICADO` fue nombrada como `evaluarTriajeAutomatico()`.
* **Verificación Crítica:**  
  En el diagrama de clases (`clases.puml`), la entidad `Reporte` no posee el método `evaluarTriajeAutomatico()` porque el evaluador es un servicio externo del módulo `triaje`. La operación interna de la entidad es `verificarTriaje(scorePrioridad)`.
* **Decisión Adoptada:**  
  **Ajustada.** Se renombró la transición a `verificarTriaje(score)` cumpliendo la Regla de Consistencia C2.

---

### Interacción 4: Round-Trip y Generación de Código Esqueleto en Python (E6)
* **Fecha:** 2026-10-09
* **Herramienta:** GitHub Copilot / GPT-4o
* **Prompt IA:**  
  ```text
  Genera el esqueleto de dominio en Python 3.10 para SismoReporta AQP a partir del diagrama de
  clases PlantUML proporcionado. Usa @dataclass, typing estricto, Enums para estados,
  interfaces con abc.ABC y excepciones en las precondiciones. Los adaptadores deben lanzar
  NotImplementedError.
  ```
* **Propuesta de la IA:**  
  Código generado con dataclasses limpias. Sin embargo, omitió la validación de invariant de multiplicidad de 3 fotos y colocó los métodos de `Coordenadas` sin cálculo de geocerca provincial.
* **Verificación Crítica:**  
  El código permitía agregar fotos infinitas, lo cual violaba el criterio C3 verificado en la primera interacción.
* **Decisión Adoptada:**  
  **Modificada.** Se incorporaron validaciones defensivas en `adjuntar_foto()` (`if len(self.fotos) >= 3: raise ValueError`), inmutabilidad con `frozen=True` en `Coordenadas` y el cálculo de pertenencia al polígono provincial de Arequipa.

---

### Interacción 5: Auditoría Automatizada de Consistencia C1–C5 (E7)
* **Fecha:** 2026-10-10
* **Herramienta:** Anthropic Claude 3.5 Sonnet
* **Prompt IA:**  
  ```text
  Actúa como auditor de software. Revisa los 5 archivos UML adjuntos (clases.puml, secuencia.puml,
  estados.mmd, actividades.puml, paquetes.puml) y verifica las reglas de consistencia C1 a C5:
  C1 (mensajes son métodos), C2 (transiciones son métodos), C3 (multiplicidades de negocio),
  C4 (paquetes acíclicos), C5 (lenguaje ubicuo). Reporta hallazgos en formato tabla con línea
  y severidad.
  ```
* **Propuesta de la IA:**  
  Reportó 4 hallazgos. Entre ellos:
  1. Firma incompleta en `sincronizar()` en el borrador de secuencia vs clases.
  2. Afirmación de que "Ingesta depende circularmente de Triaje".
* **Verificación Crítica:**  
  1. El hallazgo 1 era verídico y se corrigió inmediatamente.
  2. El hallazgo 2 era un claro **falso positivo**: Ingesta se comunica con Triaje de forma asíncrona mediante el broker Redis del paquete `compartido`; no existe dependencia estática entre los módulos.
* **Decisión Adoptada:**  
  Se corrigió la signatura real y se documentó y fundamentó el rechazo del falso positivo en `consistencia.md`.
