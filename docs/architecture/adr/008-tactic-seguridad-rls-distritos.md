# ADR-008: Aislamiento Multidistrital mediante PostgreSQL Row-Level Security y Arquitectura Hexagonal (QA-04 y QA-05)

- **Estado:** Aceptado
- **Fecha:** 2026-10-31
- **Decisores:** Santiago Palma (`santiagopalma12`), Dario Rafael Cornejo Hurtado (`darich1010`)
- **Iteración ADD:** Iteración 3 (Seguridad y Modificabilidad)
- **Escenarios Asociados:** QA-04 (H, M) y QA-05 (M, M)

---

## 1. Contexto y Problema

SismoReporta AQP debe dar soporte a los **29 distritos de la provincia de Arequipa** (Cercado, Yanahuara, Cayma, Paucarpata, Cerro Colorado, Socabaya, etc.), además de las autoridades supradistritales como el Centro de Operaciones de Emergencia Regional (COER) e INDECI.

Los escenarios prioritarios exigen:
- **QA-04 (H, M) — Seguridad / Segregación Distrital:**
  > *"Un operador municipal solo puede visualizar y gestionar los reportes de incidentes correspondientes a su distrito geográfico, impidiendo fugas de datos sensibles hacia otras municipalidades con 100% de eficacia, mientras que las autoridades regionales (COER) pueden auditar la totalidad del mapa."*
- **QA-05 (M, M) — Modificabilidad / Nuevos Proveedores:**
  > *"Integrar un nuevo proveedor de mapas satelitales o sensor telemétrico sísmico debe realizarse en un esfuerzo menor o igual a 16 horas-persona sin modificar la lógica nuclear del dominio."*

La evaluación ATAM-lite identificó el **Riesgo R4 (Severidad 8)**:
Si la segregación depende exclusivamente de cláusulas `WHERE distrito_id = :id` escritas a mano por desarrolladores en la capa de FastAPI, un error u omisión de un programador junior expondría reportes confidenciales entre municipalidades vecinas.

---

## 2. Alternativas Consideradas para Multitenencia

1. **Una Base de Datos Física por Distrito [Puntaje: 2.67 / 5.0]:**
   * Crear 29 bases de datos PostgreSQL independientes en el servidor.
   * *Refutación técnica:* Requiere 29 buffer pools de PostgreSQL y pools de conexión masivos, saturando por completo la memoria RAM de 4 GB del VPS. Crear un nuevo distrito requiere scripts DDL manuales y aprovisionamiento lento (~45 min).
2. **Un Esquema (Schema) por Distrito [Puntaje: 3.23 / 5.0]:**
   * Un esquema por distrito (`yanahuara.*`, `cayma.*`, etc.).
   * *Refutación técnica:* Complejidad extrema en el pipeline de CI/CD para ejecutar migraciones de Alembic en bucle sobre 29 esquemas, elevando el riesgo de discrepancias estructurales.
3. **Columna `distrito_id` + PostgreSQL Row-Level Security (RLS) con Claims JWT [Puntaje: 4.85 / 5.0] (Seleccionada):**
   * Una única base de datos y esquema estándar. Se activa la directiva nativa del motor relacional `ENABLE ROW LEVEL SECURITY` sobre la tabla de reportes.
   * El middleware de FastAPI inyecta las variables de sesión `app.current_distrito_id` y `app.es_admin_regional` en la transacción SQL a partir del token JWT criptográficamente verificado.
   * El motor de PostgreSQL impone la política a nivel de kernel; incluso ante un `SELECT * FROM reportes` descuidado en código, PostgreSQL filtra las filas antes de devolverlas a la memoria.

---

## 3. Decisión

**Adoptamos la Táctica de Row-Level Security (RLS) en PostgreSQL combinada con Arquitectura Hexagonal:**
1. **Seguridad Nativa (QA-04):** Se define la política RLS:
   ```sql
   ALTER TABLE reportes ENABLE ROW LEVEL SECURITY;
   CREATE POLICY aislamiento_distrito_reportes ON reportes
       FOR ALL
       USING (
           current_setting('app.es_admin_regional', true) = 'true'
           OR distrito_id = current_setting('app.current_distrito_id', true)::INTEGER
       );
   ```
2. **Modificabilidad Hexagonal (QA-05):** Se desacoplan los proveedores de cartografía (`ProveedorCartografiaPort`) y acelerómetros sísmicos (`SensorSismicoPort`) mediante interfaces de puertos en el dominio y adaptadores intercambiables en la infraestructura.

---

## 4. Consecuencias y Evidencia

### Consecuencias Positivas:
- **Aislamiento invulnerable a errores de aplicación (QA-04):** El filtro reside en el motor de base de datos relacional. Si un desarrollador omite un filtro en FastAPI, la política RLS intercepta la consulta automáticamente.
- **Alta de distritos instantánea:** Agregar un nuevo distrito insume $< 1\text{ segundo}$ (`INSERT INTO distritos ...`) sin DDL ni reinicio de servicios.
- **Eficiencia en VPS:** Un solo pool de conexiones optimizado consume $< 150\text{ MB}$ de RAM en el servidor.
- **Extensibilidad rápida (QA-05):** Adaptar un nuevo proveedor de mapas toma $< 8\text{ horas-persona}$ implementando una clase que herede de `ProveedorCartografiaPort`.
- **Verificación en CI:** La fitness function `test_ff06_aislamiento_rls_distrital` verifica automáticamente en cada Pull Request que ningún usuario distrital reciba reportes ajenos.

### Consecuencias Negativas y Mitigación:
- **Trade-off T3 (Overhead de planificación):** El motor añade una condición a cada plan de ejecución.
  * *Mitigación:* Se añadió un índice compuesto `(distrito_id, fecha_registro DESC)`, manteniendo el overhead por debajo del 3.8% en pruebas de carga.
