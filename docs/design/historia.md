# Historia de Usuario HU-08: Envío y Sincronización Offline de Reportes de Emergencia

**Caso de Estudio:** Caso 8 — SismoReporta AQP  
**Módulo:** Ingesta y Sincronización Diferida  
**Épica:** Registro Ciudadano Resiliente ante Desastres  

---

## Declaración de la Historia
> **Como** ciudadano afectado por un sismo en la región Arequipa,  
> **quiero** registrar reportes de incidentes (daños estructurales, colapsos, heridos) con geolocalización GPS y fotografías comprimidas aun cuando mi teléfono no tenga señal celular ni conexión a internet,  
> **para que** los datos se resguarden en mi dispositivo y se transmitan automáticamente a la central de Defensa Civil / COE en cuanto se recupere la conectividad.

---

## Criterios de Aceptación (Formato Gherkin / Dado-Cuando-Entonces)

### Criterio 1: Registro offline exitoso y sincronización automática diferida (Caso de Éxito)
* **Dado** que el ciudadano se encuentra en una zona sin cobertura celular post-sismo y completa el formulario de reporte con una descripción, nivel de severidad estimado, coordenadas GPS capturadas por el sensor y una fotografía de evidencia comprimida en el cliente,
* **Cuando** el usuario pulsa "Registrar Reporte de Emergencia",
* **Entonces** el sistema persiste el reporte localmente en IndexedDB asignándole un identificador único (UUID v4) y estado `ENCOLADO`, mostrando una notificación en pantalla confirmando el resguardo local;  
* **Y cuando** el dispositivo detecta el restablecimiento de conectividad de red (evento `online` o Background Sync), la PWA transmite el lote de reportes al endpoint `/api/v1/ingesta/sync` del backend;
* **Entonces** el servidor valida la firma e integridad, almacena el reporte en la base de datos central con estado `RECIBIDO`, encola el identificador en Redis para el triaje analítico y retorna un acuse de recibo (`HTTP 202 Accepted`), provocando que la PWA actualice el estado local a `RECIBIDO` y libere el espacio de almacenamiento temporal.

### Criterio 2: Falla de red durante la transmisión y reintento con retroceso exponencial (Caso de Error de Transmisión)
* **Dado** que la PWA tiene uno o más reportes en estado `ENCOLADO` e inicia una sincronización por detección de señal intermitente,
* **Cuando** la petición HTTP sufre un corte de conexión o *timeout* de red ($> 3000\text{ ms}$) antes de recibir la confirmación del servidor,
* **Entonces** la PWA aborta la transacción sin eliminar los registros de IndexedDB, preserva el estado `ENCOLADO`, e incrementa el contador de reintentos programando una nueva sincronización aplicando retroceso exponencial con jitter aleatorio para prevenir saturación de la red.

### Criterio 3: Detección y rechazo de reporte con coordenadas fuera de la geocerca de Arequipa (Caso de Validación)
* **Dado** que un reporte offline contiene coordenadas GPS anómalas o fuera de los límites provinciales de Arequipa,
* **Cuando** el servidor procesa el paquete de sincronización en el módulo de Ingesta,
* **Entonces** el sistema rechaza la inserción en la cola operativa, responde con código `HTTP 422 Unprocessable Entity` indicando "Coordenadas fuera del área de cobertura operativa de Arequipa", y marca el reporte como `RECHAZADO` en la bitácora de auditoría.
