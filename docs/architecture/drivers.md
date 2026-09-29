# Drivers Arquitectónicos — SismoReporta AQP
**Sistema de Reporte Ciudadano de Daños Post-Sismo y Coordinación de Emergencias**  
**Construcción de Software · EPIS-UNSA · 2026-B · Grupo 08**  
**Integrantes:** Santiago Palma (`santiagopalma12`), Dario Rafael Cornejo Hurtado (`darich1010`)

---

## 1. Requisitos Funcionales Clave
| ID | Requisito | Actor | Prioridad |
| :--- | :--- | :--- | :--- |
| **RF-01** | **Reporte de Daños con Geolocalización y Multimedia:** El usuario registra incidentes categorizados (colapso estructural, heridos, vía bloqueada, fuga de gas) adjuntando foto comprimida, coordenadas GPS automáticas y descripción textual. | Ciudadano | Alta |
| **RF-02** | **Almacenamiento Local Offline y Sincronización Diferida:** El sistema almacena reportes de forma persistente en el dispositivo cuando no hay conexión de red celular y los sincroniza automáticamente con reintentos exponenciales al recuperar señal. | Ciudadano / PWA | Alta |
| **RF-03** | **Tablero y Mapa de Calor Geoespacial en Tiempo Real:** Visualización interactiva cartográfica con capas de severidad (rojo/amarillo/verde), clústeres por proximidad y filtros por tipo de daño y cuadrante urbano. | Coordinador COE / Defensa Civil | Alta |
| **RF-04** | **Motor de Triaje y Priorización Automática:** Cálculo de puntaje de severidad de incidentes basado en riesgo a la vida humana, colapso de infraestructura vital y número de personas afectadas para ordenar la atención de emergencias. | Coordinador COE | Alta |
| **RF-05** | **Despacho y Asignación de Brigadas:** Asignación de incidentes priorizados a brigadas de auxilio (Bomberos, Cruz Roja, Serenazgo) considerando proximidad geográfica y disponibilidad operativa. | Coordinador COE | Alta |
| **RF-06** | **Gestión de Intervención en Campo:** Consulta de hoja de ruta de incidentes asignados, reporte de llegada al punto y actualización de estado (En camino, En atención, Resuelto, Derivado). | Brigadista | Media |
| **RF-07** | **Emisión de Alertas Zonales:** Difusión de mensajes de evacuación y advertencias de peligro geolocalizadas a ciudadanos y brigadas dentro de un perímetro crítico. | Coordinador COE | Media |

---

## 2. Atributos de Calidad (Ordenados por Prioridad)
1. **QA-01: Disponibilidad y Resiliencia en Picos Extremos (Fault Tolerance & Offline-First):** Es el atributo más crítico del sistema. Tras un sismo severo en Arequipa, las redes móviles colapsan o sufren sobrecarga masiva. El sistema no puede depender de conectividad continua ni perder reportes ciudadanos; debe operar de forma autónoma en el cliente y sincronizarse asíncronamente al restablecerse el enlace.
2. **QA-02: Eficiencia de Desempeño (Rendimiento e Ingesta de Ráfagas):** El backend debe absorber ráfagas masivas de hasta 20,000 reportes en la primera hora sin degradar el tiempo de respuesta de aceptación ($ACK$), desacoplando la ingesta rápida del procesamiento pesado en segundo plano.
3. **QA-03: Seguridad e Integridad de la Información:** Debe mitigarse el spam, la duplicidad maliciosa o involuntaria de incidentes y garantizarse la protección de los datos de contacto del ciudadano según la Ley Peruana N° 29733, asegurando la trazabilidad de los despachos de auxilio.
4. **QA-04: Modificabilidad e Interoperabilidad:** La arquitectura debe permitir integrar adaptadores para servicios de mensajería (SMS masivo, push notifications) y sistemas externos gubernamentales (INDECI, SINAGERD, Bomberos) con mínimo esfuerzo de desarrollo ($\le 3$ días-persona) y sin modificar el núcleo de dominio.

---

## 3. Restricciones
| ID | Tipo | Restricción |
| :--- | :--- | :--- |
| **R-01** | **Plazo** | **MVP en producción en 1 mes:** Mandatorio para el semestre 2026-B. Obliga a seleccionar tecnologías conocidas, evitar sobredimensionamiento operativo y priorizar la simplicidad arquitectónica. |
| **R-02** | **Equipo** | **2 desarrolladores** (Santiago Palma y Dario Rafael Cornejo Hurtado) con experiencia en Python (FastAPI/Django), TypeScript, desarrollo web (PWA, Service Workers) y bases de datos relacionales SQL. |
| **R-03** | **Presupuesto** | **Presupuesto reducido:** Infraestructura basada en un único VPS en la nube (ej. Hetzner Cloud / DigitalOcean de \$10-\$20 USD/mes). Quedan descartados clústeres administrados de Kubernetes o servicios PaaS/SaaS con tarificación por consumo imprevisto. |
| **R-04** | **Normativa y Legal** | Cumplimiento estricto de la **Ley N° 29733** (Ley de Protección de Datos Personales en el Perú) y alineación con los lineamientos del **SINAGERD** (Sistema Nacional de Gestión del Riesgo de Desastres). |
| **R-05** | **Entorno de Usuario** | Los ciudadanos utilizan smartphones heterogéneos (gama media/baja Android) con planes de datos limitados y cobertura móvil inestable o nula durante los primeros minutos post-evento telúrico. |

---

## 4. Escenarios de Atributos de Calidad
| ID | Atributo | Fuente | Estímulo | Entorno | Artefacto | Respuesta | Medida |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **QA-01** | **Disponibilidad / Resiliencia Offline** | 20,000 ciudadanos en distritos afectados de Arequipa (Cercado, Cayma, Paucarpata, Cerro Colorado, Miraflores). | Envían reportes de daños tras un sismo de 6.5 Mw con la red celular colapsada o intermitente. | Primera hora post-sismo, congestión extrema de red (pérdida de paquetes $> 80\%$). | PWA en smartphone (Service Worker + IndexedDB) y módulo de sincronización. | La app captura el reporte, almacena los datos y la foto comprimida en IndexedDB, emite un acuse de recibo visual local al usuario e intenta la sincronización en background en cuanto detecte enlace de red. | **0 reportes perdidos (100% preservación local)**. Al reconectarse a la red, el **98% de reportes encolados se transmiten exitosamente en $\le 3$ minutos**. |
| **QA-02** | **Eficiencia de Desempeño (Ingesta)** | Ráfaga masiva de 300 reportes concurrentes por segundo transmitidos al backend cuando las radiobases móviles recuperan enlace. | Peticiones HTTP POST con payload JSON georreferenciado e identificador de imagen. | Pico de sincronización en servidor central bajo operación normal de emergencia. | Nginx Reverse Proxy + API Gateway + Cola en memoria Redis + Workers de Ingesta. | Nginx y la API validan formato y encolan de inmediato el evento en Redis devolviendo HTTP 202 Accepted, delegando el triaje y persistencia a workers asíncronos. | **Latencia $p95 \le 1.5$ segundos** en la entrega del HTTP 202 al cliente; **tasa de errores HTTP 5xx $< 0.05\%$**. |
| **QA-03** | **Seguridad e Integridad (Anti-duplicación)** | Ciudadanos múltiples reportando un mismo colapso o atacantes simulando incidentes fuera de la región. | Envío de 40 reportes para una misma ubicación en un radio de 40 metros, y reportes con coordenadas fuera del departamento de Arequipa. | Operación activa de triaje post-sismo en el servidor. | Módulo de Validación y Motor Geoespacial PostGIS. | Se rechazan de plano coordenadas fuera del polígono geográfico de Arequipa y se agrupan reportes espacio-temporales en un único clúster (*Super-Incidente*) consolidando severidad. | **100% de coordenadas inválidas rechazadas en $\le 50$ ms**; reducción del ruido de duplicados en el mapa de despacho en **más del 70%**. |

---
### Lista de Verificación (E1)
- [x] Ninguna medida usa términos vagos: todas son números verificables (0 pérdidas, 98% en $\le 3$ min, $p95 \le 1.5$ s, errores $< 0.05\%$, reducción $> 70\%$).
- [x] Cada escenario cuenta con protocolo de verificación medible.
- [x] Restricciones reales y personalizadas para el equipo de 2 integrantes y tecnologías dominadas.
