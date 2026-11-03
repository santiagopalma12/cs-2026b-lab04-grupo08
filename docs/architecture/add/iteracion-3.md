# ADD 3.0 — Iteración 3: Seguridad y Modificabilidad (QA-04 y QA-05)

**Proyecto:** SismoReporta AQP  
**Fecha:** 31 de Octubre de 2026  
**Autores:** Santiago Palma, Dario Rafael Cornejo Hurtado (Grupo 08)  
**Objetivo de la Iteración:** Diseñar el mecanismo de segregación y confidencialidad de reportes sísmicos entre los 29 distritos de la provincia de Arequipa (QA-04), mitigando el riesgo **R4** de ATAM-lite, y estructurar la extensibilidad para proveedores de mapas y sensores sísmicos externos (QA-05).

---

## 1. Paso 1: Revisar Entradas

* **Drivers y Restricciones:**
  * Cobertura de 29 municipalidades distritales en la provincia de Arequipa (Cercado, Yanahuara, Cayma, Paucarpata, Cerro Colorado, Bustamante y Rivero, etc.) más el Centro de Operaciones de Emergencia Regional (COER) e INDECI.
  * Presupuesto de infraestructura: Un único VPS de 2 vCPUs y 4 GB de RAM.
  * Plazo de implementación: 1 mes de adaptación.
  * Cumplimiento con la Ley de Protección de Datos Personales (Ley N.º 29733) y normativas de INDECI.
* **Decisiones Previas:**
  * ADR-001: Monolito modular con FastAPI.
  * ADR-005 (Lab 07): Puertos y adaptadores (Arquitectura Hexagonal).
  * Iteraciones 1 y 2: Buffer asíncrono con Redis y Circuit Breaker + Outbox Pattern.

---

## 2. Paso 2: Establecer el Objetivo de la Iteración

* **Escenarios Prioritarios:**
  * **QA-04 (H, M) — Seguridad / Aislamiento Multidistrital:**
    > *"Cuando un operador de emergencia o funcionario de un distrito (ej. Yanahuara) consulta la API de reportes ciudadanos y daños estructurales, el sistema garantiza que solo pueda acceder a los registros bajo su jurisdicción territorial distrital (salvo usuarios con rol COER/INDECI que tienen visión global), impidiendo fugas de datos entre distritos con una efectividad del 100% incluso ante errores de programación en las consultas SQL del backend."*
  * **QA-05 (M, M) — Modificabilidad / Nuevos Proveedores Externos:**
    > *"Cuando el equipo de desarrollo requiere sustituir o agregar un proveedor de cartografía satelital (OpenStreetMap por Instituto Geográfico Nacional o Mapbox) o un nuevo protocolo de acelerómetros sísmicos (IGP / CISMID), la modificación se realiza implementando un nuevo adaptador sin alterar el dominio, con un esfuerzo menor o igual a 16 horas-persona."*

---

## 3. Paso 3: Elegir Uno o Más Elementos del Sistema para Refinar

* **Elementos Refinados:**
  * Capa de Persistencia y Seguridad de Datos: Esquema de base de datos PostgreSQL y motor de control de acceso a nivel de fila.
  * Capa de Puertos y Adaptadores del Dominio: Interfaces `ProveedorCartografiaPort` y `ReceptorTelemetriaSismicaPort` en el módulo de infraestructura.

---

## 4. Paso 4: Elegir Uno o Más Conceptos de Diseño

Se evaluaron tres alternativas arquitectónicas para el soporte multidistrital:

### Tabla Comparativa de Alternativas Multidistritales

| Criterio de Evaluación | Alternativa 1: Base de Datos por Distrito | Alternativa 2: Esquema (Schema) por Distrito | Alternativa 3 (Seleccionada): Columna `distrito_id` + Row-Level Security (RLS) en PostgreSQL + Claims JWT |
| :--- | :--- | :--- | :--- |
| **Nivel de Aislamiento (QA-04)** | Muy Alto (separación física de archivos). | Alto (separación lógica por esquemas). | **Muy Alto:** El motor PostgreSQL impone la política a nivel de kernel de base de datos; las consultas omiten filas sin RLS activo. |
| **Alta de Nuevo Distrito (QA-05)** | Muy Lento: aprovisionar BD, crear usuarios y migrar (~45 min). | Lento: ejecutar scripts DDL de migración por esquema (~15 min). | **Inmediato:** Insertar una nueva fila en la tabla distritos (`< 1 segundo`). |
| **Consumo de Memoria en VPS** | Crítico: 29 bases de datos colapsan la RAM del VPS (buffer pools divididos). | Medio: 29 esquemas multiplican las conexiones y caché de metadatos. | **Mínimo:** Un solo pool de conexiones optimizado para PostgreSQL. |
| **Complejidad de Migraciones (CI/CD)** | Inmanejable con 2 desarrolladores (29 ejecuciones de Alembic). | Complejo: Alembic multitenant con bucles sobre schemas. | **Óptimo:** Migraciones estándar globales de Alembic en un único esquema. |
| **Vulnerabilidad a Errores de Código (Bypass de `WHERE`)** | Inmune (conexión a BD distinta). | Inmune si el search_path está fijado. | **Inmune:** Si un desarrollador olvida poner `WHERE distrito_id = ...` en FastAPI, PostgreSQL aplica la política RLS automáticamente en la lectura física. |
| **Decisión Técnica** | **Rechazada:** Inviable por restricciones de hardware en VPS. | **Rechazada:** Sobrecarga operativa innecesaria para 29 distritos. | **ACEPTADA (ADR-008):** Cumple estrictamente QA-04, QA-05 y restricciones de VPS. |

---

## 5. Paso 5: Instanciar Elementos Arquitectónicos y Asignar Responsabilidades

### 5.1 Implementación de Row-Level Security (RLS) en PostgreSQL
Se aplican las políticas RLS directamente en la tabla relacional de reportes:

```sql
-- 1. Habilitar RLS en la tabla central
ALTER TABLE reportes ENABLE ROW LEVEL SECURITY;

-- 2. Política de aislamiento distrital
CREATE POLICY aislamiento_distrito_reportes ON reportes
    FOR ALL
    USING (
        -- Si es administrador regional (COER / INDECI), accede a todo
        current_setting('app.es_admin_regional', true) = 'true'
        OR
        -- Si es operador municipal, solo ve los de su distrito
        distrito_id = current_setting('app.current_distrito_id', true)::INTEGER
    );
```

### 5.2 Inyección Segura de Contexto en FastAPI vía Middleware Transaccional
El backend extrae los claims validados criptográficamente del token JWT (emitido durante el login) e inyecta la variable de sesión dentro de la transacción SQL:

```python
# Middleware / Dependencia en FastAPI
async def get_db_contexto(db: Session = Depends(get_db), usuario = Depends(get_usuario_autenticado)):
    # Se inyectan las variables seguras a nivel de transacción
    db.execute(text("SET LOCAL app.current_distrito_id = :dist_id"), {"dist_id": usuario.distrito_id})
    db.execute(text("SET LOCAL app.es_admin_regional = :es_admin"), {"es_admin": str(usuario.es_coer).lower()})
    yield db
```

### 5.3 Extensibilidad Hexagonal (QA-05)
Para garantizar la modificabilidad (QA-05), los adaptadores externos de mapas y sensores sísmicos implementan contratos de interfaz abstractos:
* `PuertoCartografia`: Permite alternar entre `OpenStreetMapAdapter`, `MapboxAdapter` o mapas oficiales del `IGN`.
* `PuertoSensorSismico`: Permite recibir datos de la red sismológica del IGP o de acelerómetros locales mediante adaptadores desacoplados sin impactar el núcleo del dominio.

---

## 6. Paso 6: Definir Interfaces y Generar Evidencia

### 6.1 Matriz de Evaluación Multicriterio Ponderada

| Alternativa Evaluada | Aislamiento (Peso 35%) | Costo VPS (Peso 30%) | Mantenibilidad (Peso 20%) | Facilidad Extensión (Peso 15%) | Puntuación Total (1 a 5) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **BD por Distrito** | 5.0 | 1.0 | 2.0 | 1.5 | **2.67 / 5.0** |
| **Esquema por Distrito** | 4.2 | 2.5 | 2.8 | 3.0 | **3.23 / 5.0** |
| **Columna + RLS + JWT** | **4.8** | **5.0** | **4.6** | **5.0** | **4.85 / 5.0** |

### 6.2 Mitigación del Riesgo R4 de ATAM-lite
* **Riesgo ATAM-lite R4:** Fuga de datos confidenciales entre distritos por error humano en queries SQL de desarrolladores juniors.
* **Evidencia de Mitigación:** Al operar RLS en el motor de base de datos, incluso una consulta descuidada como `SELECT * FROM reportes` ejecutada bajo la sesión del operador de *Cayma* devolverá **estrictamente** los reportes de Cayma. El filtro reside en el motor relacional, eliminando la vulnerabilidad a nivel de aplicación.
* **Fitness Function FF-06:** En integración continua, se ejecuta una prueba de aislamiento cruzado que autentica al usuario como "Distrito Yanahuara" y exige formalmente que el resultado contenga $0$ filas pertenecientes a "Cerro Colorado" o "Paucarpata".

---

## 7. Paso 7: Revisar el Objetivo de la Iteración

* **¿Se cumple el escenario QA-04?** **SÍ.** La segregación es total y forzada a nivel de kernel relacional.
* **¿Se cumple el escenario QA-05?** **SÍ.** Agregar un nuevo distrito toma menos de 1 minuto (un `INSERT INTO distritos`), y agregar un nuevo adaptador cartográfico insume $< 12\text{ ph}$ gracias a los puertos desacoplados.
* **Registro de Decisión:** Formalizado en **ADR-008: Aislamiento Multidistrital mediante PostgreSQL Row-Level Security y Arquitectura Hexagonal**.
