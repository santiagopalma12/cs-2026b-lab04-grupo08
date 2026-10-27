# Análisis de Métricas de Código y Trade-off Arquitectónico (E6)

**Asignatura:** Construcción de Software (2026-B)  
**Grupo:** 08 — SismoReporta AQP  
**Entregable:** E6 (Métricas y evaluación de impacto del refactor)  
**Herramientas:** `radon` (v6.0.1) y `pytest` (v9.1.1)

---

## 1. Cuadro Comparativo de Complejidad Ciclomática y Tamaño

Se ejecutaron las mediciones objetivas de complejidad ciclomática de McCabe (`radon cc`), métricas de volumen (`radon raw`) e índice de mantenibilidad (`radon mi`) comparando la versión ingenua frente a la versión refactorizada hacia patrones GoF.

| Métrica / Elemento Evaluado | Versión ANTES (`antes/servicio.py`) | Versión DESPUÉS (`servicio.py` + módulos) | Variación Porcentual / Impacto |
| :--- | :---: | :---: | :---: |
| **Complejidad `sincronizar_reporte()`** | **22 (Rango D)** | **3 (Rango A)** | **-86.4% (Reducción crítica)** |
| **Complejidad `clasificar_severidad_con_ia()`** | **3 (Rango A)** | **2 (Rango A)** | -33.3% |
| **Complejidad `ServicioSincronizacion.__init__()`** | **5 (Rango A)** | **4 (Rango A)** | -20.0% |
| **Complejidad de Clase `ServicioSincronizacion`** | **11 (Rango C)** | **4 (Rango A)** | **-63.6% (Mejora sustancial)** |
| **Promedio Complejidad Ciclomática** | **6.71 (Rango B)** | **1.93 (Rango A)** | **-71.2% (Excelente)** |
| **Complejidad Promedio de todo el Sistema** | 6.71 (Rango B) | 2.04 (Rango A) | -69.6% |
| **Líneas de Código Lógicas (SLOC)** | 106 SLOC | 121 SLOC (`servicio.py`) / 480 SLOC (Total) | +352% (Mayor granularidad) |
| **Archivos de Código Fuente** | 1 archivo | 6 archivos modulares | Desacoplamiento modular |
| **Índice de Mantenibilidad (MI)** | 52.93 (Rango A) | 58.73 (Rango A) | +10.9% (Código más claro) |
| **Pruebas Automatizadas en Verde** | 12 pruebas | 35 pruebas unitarias y de caracterización | +191% cobertura |

---

## 2. Lectura Honesta del Trade-off Arquitectónico (5 a 8 líneas)

> El refactor hacia patrones GoF redujo drásticamente la complejidad ciclomática del flujo crítico de sincronización de **22 (D) a 3 (A)** y su promedio de **6.71 a 1.93**, aislando por completo los SDKs externos de transporte (Redis, RabbitMQ, SMS Satelital) y protegiendo el sistema de respuestas de IA no confiables mediante una cadena de guardrails. A cambio de esta flexibilidad y robustez, el volumen de código aumentó de 106 a 480 SLOC y se incrementó la indirección estructural al pasar de 1 a 6 archivos especializados, exigiendo que cualquier nuevo desarrollador domine el catálogo GoF para navegar el código. La versión previa habría sido perfectamente suficiente si SismoReporta AQP fuese únicamente un prototipo académico monolítico de una sola semana, con un único medio de red garantizado y sin requerimientos de extensibilidad ni integración de IA en producción. Los patrones se justificaron por los cambios previstos en el mundo real (contingencia ante colapso de antenas 4G en Arequipa y absorción de picos extremos), no por un capricho estético de sobreingeniería.

---

## 3. Patrones Rechazados y Justificación Antipatternitis

Durante las iteraciones de diseño asistidas por Inteligencia Artificial, el equipo evaluó críticamente y rechazó dos propuestas de patrones:

1. **Rechazo de `Singleton` en `FabricaCanales`:**
   - *Propuesta de la IA:* Implementar la factoría como una instancia estática global única para "evitar crear múltiples instancias del registro de canales".
   - *Justificación del rechazo:* El patrón Singleton introduce acoplamiento global encubierto, impide la ejecución de pruebas unitarias en paralelo con aislamiento estricto y bloquea la inyección de canales falsos o simulados (`MeshLoraCanalAdapter`). En su lugar, se adoptó inyección de dependencias explícita en el constructor de `ServicioSincronizacion`.

2. **Rechazo de `Abstract Factory` para familias de canales y notificadores:**
   - *Propuesta de la IA:* Crear una jerarquía de fábricas abstractas (`FabricaInfraestructuraProduccion`, `FabricaInfraestructuraSimulada`) que creen simultáneamente el canal y el notificador.
   - *Justificación del rechazo:* Síntoma clásico de *Patternitis* (sobreingeniería). En SismoReporta AQP los canales de transporte (Redis, AMQP, SMS) y los observadores de eventos (COE, Auditoría, Mapas) evolucionan de forma independiente y no forman familias de productos interdependientes. Una simple fábrica basada en registro resuelve la extensibilidad cumpliendo rigurosamente el Principio Abierto/Cerrado (OCP) sin añadir interfaces redundantes.
