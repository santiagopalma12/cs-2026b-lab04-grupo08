# Detección de Olores de Código y Decisión de Patrones — SismoReporta AQP

**Asignatura:** Construcción de Software (2026-B)  
**Grupo:** 08 — SismoReporta AQP  
**Entregable:** E1 (Red de seguridad y catálogo de olores)  
**Módulo analizado:** `src/sismoreporta/antes/servicio.py`

---

## 1. Contexto y Diagnóstico Inicial

Previo al proceso de refactorización, se analizó el flujo crítico `"Envío Offline y Sincronización Diferida de Reportes Post-Sismo"` (diseñado en el diagrama de secuencia del Laboratorio 05). La versión ingenua (`antes/servicio.py`) reúne en un único método monolítico la validación de estados del reporte, la verificación geográfica, la negociación de protocolos heterogéneos de red (Redis, RabbitMQ, SMS Satelital), la lógica de reintentos ante timeouts, la emisión de alertas al COE y la clasificación con IA.

### Salida oficial de `radon cc -s -a src/sismoreporta/antes/servicio.py`
```text
src/sismoreporta/antes/servicio.py
    M 63:4 ServicioSincronizacion.sincronizar_reporte - D (22)
    C 48:0 ServicioSincronizacion - C (11)
    M 50:4 ServicioSincronizacion.__init__ - A (5)
    C 26:0 Coordenadas - A (3)
    M 130:4 ServicioSincronizacion.clasificar_severidad_con_ia - A (3)
    M 31:4 Coordenadas.esta_dentro_de_geocerca - A (2)
    C 38:0 Reporte - A (1)

7 blocks (classes, functions, methods) analyzed.
Average complexity: B (6.714285714285714)
```

> **Diagnóstico:** El método `sincronizar_reporte` posee **Complejidad Ciclomática 22 (Rango D)**, superando holgadamente el umbral crítico de mantenibilidad ($CC \le 10$). Cualquier incorporación de un nuevo canal de transmisión o cambio de proveedor de IA obliga a reescribir y recompilar el servicio central.

---

## 2. Catálogo de Olores Detectados y Decisiones Arquitectónicas

Se aplicó el **Prompt IA 1 (Detector de olores)** al código fuente y a las métricas de Radon. La tabla a continuación consolida los olores identificados, el patrón GoF correspondiente, el principio SOLID beneficiado, el costo arquitectónico y la decisión razonada del equipo:

| Líneas | Olor de Código (Fowler, 2018) | Patrón GoF Propuesto | Principio SOLID | Costo / Consecuencia | Decisión del Equipo |
| :--- | :--- | :--- | :--- | :--- | :---: |
| **63–128** | **Método Largo y Complejidad Ciclomática (CC=22):** `if/elif` por canal (`"REDIS"`, `"RABBITMQ"`, `"SMS_SATELITAL"`) que crece con cada medio de transmisión. | **Strategy + Factory (Registro)** | **O (Abierto/Cerrado)** / **S (Responsabilidad Única)** | Introduce interfaz común (`ICanalDespacho`) y clase factoría. | **ACEPTADO:** Permite agregar nuevos canales (ej. Mesh LoRa, Telegram) sin alterar el servicio orquestador. |
| **80–112** | **Conocimiento de SDKs ajenos en Dominio:** El servicio serializa JSON para Redis, convierte a `bytes` para AMQP y calcula tramas `hex` para SMS. | **Adapter** | **D (Inversión de Dependencias)** / **I (Segregación)** | Requiere una clase adaptadora por cada SDK externo. | **ACEPTADO:** Aísla la infraestructura detrás del puerto `ICanalDespacho`; los cambios en las APIs de terceros no tocan el dominio. |
| **77–111** | **Código Duplicado Transversal:** Bloque `for intento in range(3): try ... except TimeoutError` repetido idénticamente en cada canal. | **Decorator (`ConReintentos`)** | **S (Responsabilidad Única)** / **O (Abierto/Cerrado)** | Agrega un nivel de indirección al envolver el canal en ejecución. | **ACEPTADO:** Centraliza la política de reintentos y tolerancia a fallas sin contaminar los adaptadores de transporte. |
| **65–74, 116–126** | **Condicionales sobre Atributo Estado:** Evaluaciones anidadas sobre cadenas (`reporte.estado == "BORRADOR"`, `"ATENDIDO"`, `"DESCARTADO"`). | **State** | **O (Abierto/Cerrado)** / **L (Sustitución de Liskov)** | Crea una jerarquía de clases de estado (`EstadoReporteState`). | **ACEPTADO:** Materializa formalmente la máquina de estados del Lab 05 (`estados-reporte.mmd`); transiciones ilegales prohibidas por diseño. |
| **120–123** | **Notificaciones Acopladas Manualmente:** El servicio formatea y concatena cadenas directas para alertas COE y registros de auditoría. | **Observer** | **S (Responsabilidad Única)** / **O (Abierto/Cerrado)** | Añade `PublicadorEventos` y suscriptores desacoplados. | **ACEPTADO:** Nuevos interesados (tableros GIS, auditoría fiscal, SMS masivo) se suscriben sin modificar el flujo de ingesta. |
| **130–148** | **IA No Determinista sin Protección:** LLM invocado directamente sin caché (costo/latencia reiterada) y sin validación de alucinaciones. | **Strategy + Adapter + Decorator (Caché) + Chain of Responsibility (Guardrails)** | **S (Responsabilidad Única)** / **D (Inversión de Dependencias)** | Múltiples clases para aislar proveedor, almacenar respuestas y encadenar filtros. | **ACEPTADO:** Crítico para emergencias: la salida del LLM no es confiable; los guardrails filtran datos no verificados antes de llegar al COE. |
| *Propuesto por IA* | *"FabricaCanales debe ser un Singleton estático global para no reinicializar el registro."* | **Singleton** | Ninguno (acopla al estado global) | Dificulta pruebas unitarias aisladas, crea estado mutable global e impide inyectar dobles. | **RECHAZADO:** Anti-patrón en entornos modernos de pruebas. Se prefiere instanciar e inyectar la factoría como dependencia explícita. |
| *Propuesto por IA* | *"Implementar Abstract Factory para instanciar familias completas de transportes y notificadores."* | **Abstract Factory** | Inversión de Dependencias | Multiplica la cantidad de interfaces y fábricas abstractas innecesariamente. | **RECHAZADO:** Sobreingeniería evidente (*Patternitis*). No existen familias cohesivas de productos variantes; una Factory por registro satisface plenamente el caso. |

---

## 3. Verificación de la Red de Seguridad (Checkpoint E1)

Se ejecutó la suite de 12 pruebas de caracterización sobre la versión antes:
- **Resultados:** `12 passed in 0.05s`.
- **Cobertura observable:** Pruebas de integración con brokers simulados (éxito), tolerancia a fallas ante timeouts (reintentos), descarte por geocerca provincial, rechazo de estados inconsistentes y validación básica de IA.
- **Independencia de red:** Ninguna prueba consume servicios reales ni requiere credenciales de API.
