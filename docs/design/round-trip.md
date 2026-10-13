# Round-Trip: Ingeniería Directa e Inversa (E6)

**Caso de Estudio:** Caso 8 — SismoReporta AQP  
**Módulo:** Dominio e Ingesta de Reportes (`src/sismoreporta`)  

---

## 1. Proceso de Round-Trip Ejecutado

1. **Ingeniería Directa (Diagrama a Código):**  
   A partir del diagrama de diseño de clases (`clases.puml`), se generó la implementación en Python 3.10+ estructurada en `src/sismoreporta/dominio.py` utilizando `@dataclass`, `abc.ABC`, `Enum`, `Decimal` y tipado estático estricto (`typing`).
2. **Ingeniería Inversa (Código a Diagrama):**  
   Se ejecutó la herramienta `pyreverse` del paquete `pylint` sobre el código fuente generado:
   ```bash
   pyreverse -o puml -p sismoreporta src/sismoreporta
   java -jar plantuml.jar -tpng classes_sismoreporta.puml -o docs/design/img/
   ```
3. **Análisis Comparativo:**  
   Se contrastó el diagrama de diseño conceptual frente al diagrama derivado del AST del código ejecutable.

---

## 2. Matriz Comparativa de Diferencias

| N.° | Elemento / Diferencia Observada | Diagrama de Diseño (`clases.puml`) | Diagrama Inverso (`classes_sismoreporta.puml`) | Causa Técnica | Acción Tomada |
| :---: | :--- | :--- | :--- | :--- | :--- |
| **1** | **Composición y Multiplicidad** (`Reporte` – `FotoEvidencia`, `Coordenadas`) | Composición explícita con rombo relleno (`*--`) y multiplicidades exactas (`1 *-- 0..3`, `1 *-- 1`). | Figuran únicamente como atributos de tipo `List[FotoEvidencia]` o `ubicacion_actual`, sin multiplicidad ni rombos. | `pyreverse` analiza el AST de Python a nivel de atributos y no infiere relaciones de agregación/composición ni límites numéricos desde listas tipadas. | **Documentar limitación de herramienta:** Se mantiene el diagrama de diseño como modelo normativo y se garantiza la regla en el código mediante validación explícita (`if len(self.fotos) >= 3: raise ValueError`). |
| **2** | **Puertos e Interfaces** (`IBrokerCola`, `IRepositorioReportes`, `INotificadorEmergencias`) | Modeladas con estereotipo `interface <<puerto>>` y realización discontinua (`<|..`). | Aparecen como clases con estereotipo `{abstract}` y relación de herencia sólida (`<|--`). | Python no cuenta con palabra clave nativa `interface` y materializa contratos mediante clases abstractas con `abc.ABC`. | **Aceptada por convención de lenguaje:** Se documenta la equivalencia semántica entre `<<puerto>>` en UML y `ABC` en Python sin alterar el diseño arquitectónico. |
| **3** | **Convención de Nomenclatura** (camelCase vs. snake_case) | Notación estándar UML / Java en camelCase: `sincronizarReporte()`, `guardarBorrador()`, `tamanioBytes`. | Notación estándar Python (PEP 8) en snake_case: `sincronizar_reporte()`, `guardar_borrador()`, `tamanio_bytes`. | Convención canónica del ecosistema Python exigida por linters y guías de estilo oficiales. | **Aceptada según Regla C5:** Se homologan los identificadores en el diccionario de términos del proyecto, validando que ambos representan unívocamente la misma operación del dominio. |
| **4** | **Value Objects y Atributos Inmutables** (`Coordenadas`) | Modelado con estereotipo `<<ValueObject>>` y métodos de dominio puro (`distanciaHacia`, `estaDentroDeGeocerca`). | Renderizado como clase estándar `sismoreporta.dominio.Coordenadas`. | `pyreverse` no reconoce estereotipos de Domain-Driven Design (DDD) a partir del decorador `@dataclass(frozen=True)`. | **Alineación en código:** Se preservó el atributo `frozen=True` en Python para garantizar inmutabilidad en memoria y se conservó el estereotipo en el diagrama de diseño. |

---

## 3. Conclusiones del Proceso Round-Trip
* El código generado en Python respeta con precisión quirúrgica todas las operaciones, parámetros y tipos del diseño preliminar.
* Las discrepancias detectadas se deben a las características semánticas de los lenguajes dinámicos tipados y a las limitaciones intrínsecas de los analizadores de código estático basados en AST.
* El modelo UML funciona exitosamente como **plano de construcción** para el desarrollo ágil del MVP en 1 mes.
