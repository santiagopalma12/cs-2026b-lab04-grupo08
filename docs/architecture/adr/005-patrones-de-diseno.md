# ADR-005: Adopción de Patrones de Diseño GoF y Aislamiento de IA en SismoReporta AQP
- **Estado:** Aceptado
- **Fecha:** 2026-10-24
- **Decisores:** Santiago Palma (`santiagopalma12`), Dario Rafael Cornejo Hurtado (`darich1010`)

## Contexto
Durante la implementación del flujo crítico de ingesta y sincronización diferida post-sismo (diseñado en el Laboratorio 05), la versión ingenua (`antes/servicio.py`) alcanzó una **complejidad ciclomática de 22 (Rango D)** en el método `sincronizar_reporte()`, con un promedio de clase de 6.71 (B). Este diseño monolítico presentaba serios olores de código:
1. Condicionales anidados sobre estados y canales de transmisión que violaban el Principio Abierto/Cerrado (OCP).
2. Alto acoplamiento a los SDKs de terceros (Redis, RabbitMQ y SMS Satelital), obligando al servicio de dominio a manipular formatos de serialización y tramas binarias/hexadecimales.
3. Lógica de reintentos ante timeouts duplicada proceduralmente en cada canal.
4. Notificaciones acopladas a mano para el COE y los registros de auditoría.
5. Invocación de un componente de IA no determinista (LLM) sin caché (costos y latencias repetidas) y vulnerable a alucinaciones de magnitudes sismológicas o frases alarmistas que podrían generar pánico ciudadano durante el desastre.

El atributo crítico de calidad **QA-01** (disponibilidad ante picos de 20,000 reportes) y la restricción **R-01** (MVP en 1 mes) exigen que el código sea testeable de forma determinista, extensible ante nuevos canales de telecomunicaciones (ej. radios Mesh LoRa) y seguro frente a salidas erróneas de la IA.

## Alternativas consideradas
1. **Conservar la Arquitectura Procedural Monolítica [Puntaje: 2.10]:**  
   Mantener los bloques `if/elif` dentro del método principal. No agrega clases ni indirección, pero cada nuevo medio de transporte o regla de estado eleva el riesgo de regresiones y bloquea las pruebas unitarias independientes.
2. **Aplicación Máxima de Patrones sin Filtro de Olores ("Patternitis") [Puntaje: 2.80]:**  
   Introducir Abstract Factory para familias de transportes y notificadores, Singleton para las fábricas, Visitor para la validación de entidades y bibliotecas reactivas pesadas (RxPY). Introduce estado global oculto, eleva el volumen de código innecesariamente y sobrecarga la curva de mantenimiento para un equipo de 2 desarrolladores.
3. **Refactorización Guiada por Olores hacia Patrones Clásicos GoF [Puntaje: 4.85]:**  
   Aplicar exclusivamente los patrones que resuelven olores concretos respaldados por pruebas de caracterización: **Strategy + Adapter + Factory** para desacoplar el transporte, **Decorator** para reintentos y caché, **State** para la máquina de estados del reporte, **Observer** para las alertas del COE, **Command** para la cola offline, y **Chain of Responsibility** para los guardrails de la IA.

## Decisión
**Adoptaremos la Alternativa 3**, refactorizando el flujo crítico hacia los siguientes patrones de diseño GoF:
1. **Strategy + Adapter (`ICanalDespacho`):** Se crea un puerto de dominio unificado. Cada medio de transporte (`RedisCanalAdapter`, `RabbitMQCanalAdapter`, `SmsSatelitalCanalAdapter`) adapta su SDK específico a la interfaz de dominio.
2. **Factory Method por Registro (`FabricaCanales`):** Permite registrar e instanciar dinámicamente nuevas estrategias por nombre cumpliendo OCP, sin usar estado global ni Singleton.
3. **Decorator (`ConReintentos` y `ConCacheLLM`):** Agrega responsabilidades transversales transparentemente: reintentos controlados solo ante `TimeoutError` en los canales, y caché de inferencias para evitar invocar al LLM por descripciones idénticas.
4. **State (`EstadoReporteState`):** Implementa la máquina de estados del Lab 05 (`Borrador`, `Encolado`, `Recibido`, `Verificado`, `Atendido`, `Descartado`), prohibiendo transiciones ilegales por construcción.
5. **Observer (`PublicadorEventos` y `Suscriptor`):** Emite eventos de dominio hacia interesados desacoplados (`NotificadorCOE`, `AuditorEventosSismicos`, `TableroOperacionesMapa`).
6. **Command (`ComandoSincronizarReporte` y `ColaComandosOffline`):** Encapsula solicitudes de sincronización ciudadana para retenerlas en cola local y procesarlas en lote cuando se restablece la cobertura celular.
7. **Chain of Responsibility (`Guardrail`):** Trata la respuesta del LLM como dato no confiable, pasándola por una cadena de filtros deterministas (`SinAlucinacionMagnitud`, `SinPanicoSocial`, `FormatoSeveridadValido`).

**Patrones explícitamente rechazados:**  
- **Singleton:** Rechazado para `FabricaCanales` por introducir estado global mutable y dificultar pruebas unitarias aisladas.
- **Abstract Factory:** Rechazado por sobreingeniería (*patternitis*); los canales y observadores evolucionan de forma independiente.

## Consecuencias
- **Positivas:**
  - **Reducción de Complejidad (QA-01):** La complejidad ciclomática máxima del flujo cayó de 22 a 3 (-86.4%), y el promedio de clase bajó a 1.93 (Rango A).
  - **Extensibilidad Abierto/Cerrado:** Agregar una nueva estrategia de transporte (ej. `MeshLoraCanalAdapter`) o un nuevo suscriptor GIS requiere 0 modificaciones en el código de `ServicioSincronizacion`.
  - **Seguridad en IA:** Las respuestas alucinadas del modelo de lenguaje son bloqueadas antes de propagarse al COE o a la ciudadanía.
  - **Testeabilidad 100% Determinista:** La suite completa de 35 pruebas unitarias y de caracterización se ejecuta en 0.08 s sin requerir conexiones reales ni claves de API de LLM.
- **Negativas y Mitigaciones:**
  - **Incremento de Volumen e Indirección:** El código del módulo pasó de 106 a 480 SLOC y de 1 a 6 archivos independientes.  
    *Mitigación:* Se documentó la arquitectura con diagramas PlantUML explícitos (`docs/design/patrones/`) y se normalizó la estructura del repositorio.
  - **Riesgo de Patternitis:** Tentación de seguir agregando patrones innecesarios.  
    *Mitigación:* Se estableció la regla de que ningún patrón entra sin un olor cuantificable en Radon y una prueba en verde que demuestre su beneficio.
