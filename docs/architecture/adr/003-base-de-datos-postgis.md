# ADR-003: Selección de PostgreSQL con Extensión Espacial PostGIS para Persistencia y Análisis Geoespacial
- **Estado:** Aceptado
- **Fecha:** 2026-09-29
- **Decisores:** Santiago Palma (`santiagopalma12`), Dario Rafael Cornejo Hurtado (`darich1010`)

## Contexto
El núcleo de la toma de decisiones durante un desastre sísmico en Arequipa reside en el procesamiento espacial de incidentes y brigadas:
- **RF-03:** Representación cartográfica interactiva con cálculo dinámico de clústeres por proximidad y mapas de calor.
- **RF-04 / RF-05:** Triaje por zonas de impacto y asignación de brigadas de rescate en función de la menor distancia geodésica (`ST_Distance`) respecto a los puntos críticos.
- **QA-03:** Detección de duplicados espaciales (agrupar reportes a menos de 50 metros emitidos en una ventana de 15 minutos) y validación inmediata de geocercas dentro del polígono departamental de Arequipa (`ST_Contains`).
- **QA-02:** Ejecución de consultas espaciales complejas en menos de 50 ms aun con decenas de miles de registros acumulados.
- **R-02 / R-03:** Dominio tecnológico del equipo en SQL relacional y necesidad de operar eficientemente con recursos limitados en un único VPS.

## Alternativas consideradas
1. **Base de Datos NoSQL Documental (MongoDB con índices 2dsphere):**  
   Permite guardar documentos JSON flexibles y soporta consultas geoespaciales básicas como `$near` o `$geoWithin`. Sin embargo, carece de funciones espaciales analíticas avanzadas (cálculo de densidad en tiempo real, unión de polígonos complejos, clustering espacial con DBSCAN) y las transacciones ACID entre múltiples colecciones son complejas de gestionar, arriesgando la consistencia en el estado de despacho de brigadas.
2. **Base de Datos Relacional Estándar (MySQL / MariaDB con funciones espaciales básicas):**  
   Familiar para el equipo, pero el soporte para cálculos de distancias geodésicas en el esferoide terrestre (WGS84 / SRID 4326) es limitado, y su rendimiento con índices espaciales bajo alta concurrencia es inferior al estándar industrial de la geomática.
3. **PostgreSQL con Extensión Espacial PostGIS e Índices Espaciales GiST (R-Tree):**  
   El estándar indiscutido de la industria para sistemas de información geográfica (SIG). Ofrece tipos de datos geométricos y geográficos nativos, funciones optimizadas de validación (`ST_Contains`), cálculo de distancias exactas (`ST_DWithin`, `ST_DistanceSphere`), agrupamiento espacial (`ST_ClusterDBSCAN`) y un robusto soporte transaccional ACID con esquemas separados para garantizar el aislamiento modular.

## Decisión
**Adoptaremos PostgreSQL 16+ con la extensión PostGIS.**
- Todo reporte almacenará las coordenadas del incidente utilizando el tipo `GEOGRAPHY(Point, 4326)` indexado mediante un índice espacial **GiST** (Generalized Search Tree / R-Tree), lo que garantiza búsquedas por proximidad y delimitación en tiempo logarítmico $\mathcal{O}(\log N)$.
- La validación perimetral de Arequipa se ejecutará directamente en base de datos comparando el punto con el polígono oficial de la provincia de Arequipa antes de la inserción definitiva.
- Para evitar consultas repetitivas a la base de datos durante la visualización del mapa por parte de múltiples brigadas y coordinadores, las capas agregadas de calor (*GeoJSON Tiles*) se precalcularán en tareas programadas y se mantendrán cacheadas en **Redis** con un tiempo de expiración (TTL) de 10 segundos.

## Consecuencias
- **Positivas:**
  - **Potencia analítica (QA-03):** Funciones nativas de PostGIS permiten resolver la deduplicación de incidentes y la asignación de brigadas en una sola sentencia SQL optimizada, sin necesidad de calcular distancias matemáticas en la capa de aplicación.
  - **Rendimiento predecible (QA-02):** Con índices GiST, las consultas espaciales en Arequipa toman menos de 10 milisegundos para 50,000 puntos.
  - **Integridad y esquemas:** PostgreSQL permite crear esquemas lógicos separados (`ingesta`, `triaje`, `brigadas`, `gis`) dentro de una misma base de datos, reforzando la arquitectura de monolito modular sin incurrir en costes de múltiples servidores.
  - **Ecosistema Open Source (R-03):** Completamente gratuito, sin licenciamiento y con excelente integración con librerías Python (`GeoAlchemy2`, `Shapely`, `asyncpg`).
- **Negativas y Riesgos mitigados:**
  - **Consumo de memoria RAM:** PostGIS e índices GiST requieren memoria compartida adecuada para mantener páginas de índice en caché.  
    *Mitigación:* Se configurarán parámetros del kernel y PostgreSQL (`shared_buffers = 2GB`, `work_mem = 64MB`) adaptados al perfil del VPS de 8 GB RAM para prevenir saturación (*Out-Of-Memory*).
