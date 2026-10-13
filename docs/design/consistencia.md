# Auditoría de Consistencia entre Diagramas UML (E7)

**Caso de Estudio:** Caso 8 — SismoReporta AQP  
**Documento:** Verificación Formal de Reglas C1 – C5  
**Auditores:** Santiago Palma (`santiagopalma12`), Dario Rafael Cornejo Hurtado (`darich1010`)  

---

## 1. Reglas de Consistencia Evaluadas

| Regla | Criterio de Consistencia Evaluado |
| :---: | :--- |
| **C1** | Cada mensaje del diagrama de secuencia dirigido a un objeto corresponde a una operación explícita en su clase dentro del diagrama de clases. |
| **C2** | Cada transición del diagrama de estados está provocada por una operación o un evento identificable de la clase en el diagrama estructural. |
| **C3** | Las multiplicidades reflejan con precisión las reglas del dominio y los criterios de aceptación (ej. fotos por reporte $\le 3$, coordenadas obligatorias 1..1). |
| **C4** | Las dependencias entre paquetes respetan estrictamente el ADR-001 y forman un grafo acíclico sin dependencias circulares. |
| **C5** | La nomenclatura emplea unívocamente el lenguaje ubicuo del dominio de emergencias sísmicas en historias, diagramas y código fuente. |

---

## 2. Matriz de Hallazgos y Dictamen de Auditoría

| Regla | Elemento Auditado | Hallazgo Sugerido por la IA | Verificación Crítica del Equipo | Estado / Dictamen |
| :---: | :--- | :--- | :--- | :---: |
| **C1** | Mensaje `sincronizar(fecha)` en Secuencia hacia `Reporte` | La IA reportó que el mensaje `sincronizar(fecha)` no recibía el parámetro de fecha en la primera versión del diagrama de clases. | **Válido:** En el borrador inicial de `clases.puml`, el método figuraba como `sincronizar(): void` sin argumentos. Se actualizó la firma a `sincronizar(fecha: DateTime): void` para registrar la estampa temporal de recepción. | **Corregido** |
| **C1** | Mensaje `encolarReporte(...)` hacia `IBrokerCola` | La IA alertó que el canal de encolamiento no estaba definido en la interfaz del puerto. | **Válido:** Se refinó la firma en `IBrokerCola` a `encolarReporte(canal: String, payloadJson: String): bool` garantizando acoplamiento por contrato. | **Corregido** |
| **C2** | Transición `RECIBIDO --> VERIFICADO` en Estados | La IA sugirió que la guarda `[scorePrioridad >= 0.70]` exigía una operación separada `evaluarScore()` en `Reporte`. | **FALSO POSITIVO IDENTIFICADO:** La evaluación del score analítico no es responsabilidad de la entidad `Reporte` (eso violaría el principio de responsabilidad única SRP), sino del `MotorTriaje`. La operación `verificarTriaje(scorePrioridad: Decimal)` en `Reporte` recibe el resultado calculado y ejecuta la transición interna. Se rechazó el cambio propuesto por la IA. | **Rechazado (Falso Positivo)** |
| **C3** | Multiplicidad `Reporte` – `FotoEvidencia` | La IA propuso una multiplicidad `1 -- 0..*` argumentando que no deberían limitarse las fotos adjuntas. | **Rechazado:** La historia y el ADR-002 establecen una restricción estricta de ancho de banda móvil post-sismo: máximo 3 fotos comprimidas ($< 500\text{ KB}$ cada una) para no saturar el canal de sincronización. Se mantuvo la multiplicidad normativa `1 *-- 0..3`. | **Rechazado por Regla de Negocio** |
| **C4** | Dependencia `INGESTA ..> TRIAJE` | La IA advirtió una supuesta dependencia cíclica entre Ingesta y Triaje al observar que ambos manipulan objetos `Reporte`. | **FALSO POSITIVO IDENTIFICADO:** La IA confundió la dependencia compartida hacia la entidad `Reporte` (ubicada en el paquete `compartido`) con una dependencia directa circular. Ingesta delega a Redis y no conoce a Triaje; Triaje consume de Redis de forma desacoplada. El grafo es estrictamente acíclico. | **Rechazado (Falso Positivo)** |
| **C5** | Identificadores en Código Python | La IA detectó discrepancia léxica entre `estaDentroDeGeocerca` (UML) y `esta_dentro_de_geocerca` (Python). | **Válido pero Convencional:** Se confirmó que corresponde al mapeo canónico entre la especificación UML y la guía PEP 8 de Python. Ambos reflejan exactamente el mismo término del lenguaje ubicuo. | **Homologado y Aceptado** |

---

## 3. Balance de la Revisión
* Se detectaron y subsanaron 2 inconsistencias reales de signaturas entre secuencia y clases (Regla C1).
* Se neutralizaron 2 falsos positivos generados por la IA causados por falta de comprensión del patrón Arquitectura Limpia / Puertos y Adaptadores y de las restricciones de recursos del dominio de catástrofe.
