# ADR-007: Resiliencia en Ingesta mediante Circuit Breaker, Outbox Persistente y Offline-First (QA-02)

- **Estado:** Aceptado
- **Fecha:** 2026-10-31
- **Decisores:** Santiago Palma (`santiagopalma12`), Dario Rafael Cornejo Hurtado (`darich1010`)
- **Iteración ADD:** Iteración 2 (Disponibilidad y Resiliencia)
- **Escenario Asociado:** QA-02 (H, H)

---

## 1. Contexto y Problema

Durante el colapso de infraestructura o un sismo de gran magnitud, la red de telefonía celular 3G/4G en Arequipa experimenta cortes intermitentes con una tasa de pérdida de paquetes transitoria de aproximadamente 8%. Adicionalmente, el broker central de mensajería o el canal de red del servidor pueden sufrir interrupciones sostenidas de hasta 20 minutos.

El escenario de calidad **QA-02 (H, H)** exige:
> *"Ante caídas de red móvil o indisponibilidad temporal del broker central durante la crisis, el sistema garantiza una tasa de pérdida de reportes de exactamente 0%, reduciendo las llamadas inútiles al servicio caído en más de un 75%."*

La evaluación cruzada ATAM-lite identificó el **Riesgo Crítico R3 (Severidad 16)**:
Si miles de clientes móviles reconectan tras una interrupción y ejecutan reintentos inmediatos, generan una tormenta de peticiones (*Thundering Herd*) que satura el API Gateway y agrava la indisponibilidad.

---

## 2. Alternativas Consideradas

1. **Reintentos Inmediatos Agresivos en el Cliente [Puntaje: 2.2 / 5.0]:**
   * El cliente ejecuta hasta 3 reintentos inmediatos espaciados por 1 s.
   * *Evidencia de falla:* Resuelve timeouts esporádicos, pero en una caída prolongada (20 min) dispara **450 peticiones inútiles** contra el broker muerto (multiplicando la carga por 3) y al agotar los 3 intentos **pierde 150 reportes (8.3% del total)**.
2. **Cola de Contingencia Volátil en Redis (Propuesta inicial de la IA) [Puntaje: 1.5 / 5.0]:**
   * Guardar los reintentos en una lista en memoria de Redis.
   * *Refutación técnica:* Si el componente afectado por la caída o reinicio es el propio Redis o el host físico, los reportes en memoria se pierden irremediablemente, violando el SLA de 0% de pérdida.
3. **Patrón Combinado: Client-side Circuit Breaker + Local & Server Outbox Pattern con Jitter [Puntaje: 4.95 / 5.0] (Seleccionada):**
   * En la PWA móvil: Almacenamiento local preventivo en IndexedDB antes de intentar el envío (*Offline-First*).
   * **Circuit Breaker** (umbral de 3 fallas, tiempo de enfriamiento de 15 a 60 s). Al detectar falla sostenida, entra en estado `ABIERTO` (*fail-fast* local), pausando las peticiones a la red y activando un algoritmo de *Exponential Backoff con Jitter aleatorio*.
   * En el backend: Tabla `outbox_reportes` transaccional en PostgreSQL (ACID) si el broker Redis experimenta mantenimiento.

---

## 3. Decisión

**Adoptamos el Patrón Combinado de Circuit Breaker con Decorator, Outbox Persistente e Idempotencia:**
1. Los reportes se almacenan localmente en IndexedDB en el cliente móvil y se marcan con un UUID determinista (`reporte_id`).
2. El Circuit Breaker evita que el cliente golpee repetidamente un backend caído.
3. Al recuperarse la conectividad (`SEMIABIERTO` $\rightarrow$ `CERRADO`), el worker de sincronización drena el Outbox local con *Jitter* aleatorio, evitando picos sincronizados.
4. El backend aplica idempotencia relacional (`INSERT ... ON CONFLICT (id) DO NOTHING`), garantizando semántica *at-least-once* sin duplicados.

---

## 4. Consecuencias y Evidencia

### Consecuencias Positivas:
- **Cumplimiento estricto de QA-02:** La simulación estocástica Monte Carlo (`fitness/disponibilidad.py`) con 1800 eventos demostró:
  - Reportes perdidos: **0 (0.0% de pérdida)**, cumpliendo con la meta de integridad absoluta.
  - Llamadas al broker caído durante la contingencia: se redujeron de 450 (con reintentos) a tan solo **12 llamadas** (reducción del **97.3%**, superando ampliamente el umbral del 75%).
- **Mitigación total del Riesgo R3 de ATAM-lite:** El *Jitter* y el *fail-fast* del Circuit Breaker eliminan el efecto *Thundering Herd*.
- **Protección verificada por CI:** La fitness function `test_ff04_cero_reportes_perdidos_ante_caida_del_broker` y `test_ff05_breaker_protege_al_broker_caido` garantizan esta propiedad en cada commit.

### Consecuencias Negativas y Mitigación:
- **Sobrecarga de almacenamiento (Trade-off T2):** La persistencia en IndexedDB y tabla `outbox_reportes` requiere un proceso de limpieza de eventos confirmados mayores a 7 días.
  * *Mitigación:* Se implementa un comando programado (`cron`) diario para purgar reportes verificados.
