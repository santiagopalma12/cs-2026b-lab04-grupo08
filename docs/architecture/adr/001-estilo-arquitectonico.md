# ADR-001: Adopción de Monolito Modular Asíncrono con Colas en Memoria para SismoReporta AQP
- **Estado:** Aceptado
- **Fecha:** 2026-09-29
- **Decisores:** Santiago Palma (`santiagopalma12`), Dario Rafael Cornejo Hurtado (`darich1010`)

## Contexto
El sistema **SismoReporta AQP** debe procesar reportes ciudadanos de daños y coordinar brigadas de rescate tras un terremoto en la región Arequipa. Este dominio impone drivers altamente exigentes:
- **RF-01 / RF-02:** Ingesta de reportes con fotos geolocalizadas y tolerancia a sincronizaciones masivas diferidas.
- **QA-01 (Crítico):** Disponibilidad extrema ante picos de 20,000 reportes en la primera hora post-sismo bajo redes móviles congestionadas.
- **QA-02:** Desempeño de ingesta con latencia de respuesta $p95 \le 1.5\text{ s}$ para liberar rápidamente las conexiones intermitentes de los celulares.
- **R-01:** Plazo estricto de entrega del MVP en producción en 1 mes.
- **R-02:** Equipo de desarrollo reducido compuesto por 2 ingenieros de software.
- **R-03:** Presupuesto limitado a un único VPS de \$10 a \$20 USD/mes.

Un monolito tradicional síncrono colapsaría ante las 20,000 peticiones concurrentes debido a la saturación de conexiones en la base de datos relacional y el tiempo de compresión de imágenes. Por otro lado, una arquitectura de microservicios distribuidos excede por completo la capacidad operativa y el plazo de entrega del equipo.

## Alternativas consideradas
1. **Monolito en Capas Tradicional (N-Tier) [Puntaje: 3.15]:**  
   Implementación clásica en un solo proceso con capas acopladas. Fácil de desarrollar inicialmente, pero las peticiones HTTP bloquean los hilos del servidor mientras se procesan las fotos y los cálculos espaciales, generando fallos en cascada (HTTP 504 Gateway Timeout) durante el pico del sismo.
2. **Microservicios Distribuidos con Apache Kafka y Kubernetes [Puntaje: 3.20]:**  
   Servicios independientes desplegados en contenedores con colas Kafka. Proporciona excelente escalabilidad horizontal y aislamiento de fallos, pero introduce una sobrecarga operativa inmanejable (observabilidad distribuida, múltiples bases de datos, service mesh) que haría imposible cumplir el plazo de 1 mes con 2 desarrolladores.
3. **Monolito Modular Asíncrono con Redis y Workers en Segundo Plano [Puntaje: 4.15]:**  
   Un único artefacto desplegable en Python (FastAPI/Django) estructurado internamente en módulos de dominio desacoplados (*Ingesta*, *Triaje*, *Brigadas*, *GIS*, *Notificaciones*). Emplea Redis como broker de mensajes volátil en memoria y workers (Celery/arq) para desacoplar la ingesta HTTP inmediata del procesamiento computacionalmente costoso.

## Decisión
**Adoptaremos una arquitectura de Monolito Modular Asíncrono** ejecutada en un único servidor VPS.
- La capa de presentación recibirá las peticiones de los ciudadanos, validará la firma sintáctica y encolará de inmediato el payload en Redis, respondiendo al cliente con código `HTTP 202 Accepted` en menos de 100 ms.
- Un conjunto de workers asíncronos en background consumirá los eventos de la cola para ejecutar la compresión de fotos, el triaje geoespacial y la persistencia en esquemas dedicados de PostgreSQL + PostGIS.
- Los módulos de dominio se comunicarán exclusivamente a través de interfaces de servicio públicas en código, prohibiendo consultas cruzadas directas entre esquemas o módulos.

## Consecuencias
- **Positivas:**
  - **Entrega ágil (R-01):** Un único pipeline de CI/CD, un solo repositorio y una única base de datos facilitan el despliegue del MVP en 1 mes.
  - **Absorción de picos (QA-01, QA-02):** Redis absorbe las 20,000 peticiones concurrentes como un buffer de choque (*shock-absorber*), protegiendo la base de datos relacional contra saturación de conexiones.
  - **Bajo costo (R-03):** Toda la solución opera holgadamente dentro de un único VPS de 4 vCPUs y 8 GB de RAM.
  - **Evolución limpia:** Si en el futuro el módulo GIS o el de Ingesta requieren escalado independiente, sus límites modulares permiten extraerlos como microservicios sin reescribir la lógica de negocio.
- **Negativas y Riesgos mitigados:**
  - **Riesgo de punto único de falla (SPOF):** Al residir en un único VPS, una caída del servidor inhabilita el sistema.  
    *Mitigación:* Se configurará reinicio automático de servicios con `systemd`/`Docker Compose restart: always`, snapshots diarios del VPS y la PWA preservará todos los reportes en el almacenamiento local del cliente (IndexedDB) hasta que el servidor responda.
  - **Disciplina modular:** Riesgo de acoplamiento accidental entre módulos en el código fuente.  
    *Mitigación:* Se configurará un linter arquitectónico (`import-linter` o `pytest-archon`) en la integración continua para bloquear automáticamente commits que violen los límites entre módulos.
