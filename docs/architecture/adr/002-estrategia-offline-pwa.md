# ADR-002: Estrategia de Cliente Offline-First mediante PWA con Service Workers e IndexedDB
- **Estado:** Aceptado
- **Fecha:** 2026-09-29
- **Decisores:** Santiago Palma (`santiagopalma12`), Dario Rafael Cornejo Hurtado (`darich1010`)

## Contexto
Durante y después de un sismo de magnitud en Arequipa, las radiobases celulares sufren cortes de fluido eléctrico y saturación extrema. Los ciudadanos necesitan registrar daños de manera inmediata sin perder la información digitada ni las fotografías capturadas:
- **RF-01 / RF-02:** Registro de reportes de emergencia con foto y coordenadas, requiriendo persistencia local inmediata y transmisión asíncrona diferida.
- **QA-01:** Garantizar **0 reportes perdidos** aun cuando el smartphone permanezca sin señal durante horas post-sismo.
- **R-01:** Lanzamiento en 1 mes (no hay margen temporal para procesos de aprobación burocrática en tiendas de aplicaciones de Google Play o Apple App Store).
- **R-05:** Diversidad de dispositivos de gama media y baja con espacio de almacenamiento limitado y navegadores basados en Chromium.

Si el cliente dependiera de una conexión HTTP en tiempo real, el 80% de los intentos de reporte fallarían por *Network Timeout*, frustrando al usuario y privando a Defensa Civil de datos vitales de rescate.

## Alternativas consideradas
1. **Aplicación Móvil Nativa Multiplataforma (Flutter / React Native):**  
   Permite acceso a APIs nativas y persistencia con SQLite. Sin embargo, requiere empaquetado, firma de binarios y someterse a revisiones de Google Play Store y Apple App Store (las cuales demoran de 3 a 14 días), retrasando el cumplimiento de **R-01**. Además, exige que el ciudadano descargue una app de 30-50 MB durante la emergencia, lo cual es inviable sin red.
2. **Aplicación Web Tradicional (Server-Rendered o SPA sin Service Worker):**  
   Fácil de desplegar, pero carece de capacidades offline. Si la señal se corta durante el envío del formulario, el navegador muestra la pantalla de error ("Sin conexión") y los datos ingresados por el usuario se pierden definitivamente, violando **QA-01**.
3. **Progressive Web App (PWA) con Arquitectura Offline-First (Service Worker + IndexedDB):**  
   Acceso instantáneo mediante enlace web o código QR sin instalación previa obligatoria. Emplea un *Service Worker* para cachear la interfaz gráfica y *IndexedDB* como almacén transaccional local en el navegador para resguardar reportes y fotos en formato Blob. Utiliza la *Background Sync API* (con fallback a listeners de eventos `online`/`offline`) para reintentar la transmisión de reportes encolados tan pronto como el dispositivo detecte conectividad celular o Wi-Fi.

## Decisión
**Implementaremos una Progressive Web App (PWA) Offline-First.**
- Al abrir la PWA, los activos estáticos (HTML, CSS, JS, iconos) se almacenarán en la *Cache Storage* del navegador mediante una estrategia *Cache-First*.
- Cuando el ciudadano pulsa "Enviar Reporte", la aplicación comprime la fotografía en el cliente (usando el Canvas API para reducirla a $< 500\text{ KB}$), genera un UUID v4 local y almacena el registro en una base de datos local **IndexedDB** en la tabla `pending_reports` con estado `ENCOLADO`.
- Si el dispositivo cuenta con red, se intenta la transmisión inmediata; si la red falla o no existe señal, el usuario recibe confirmación visual inmediata en pantalla: *"Reporte guardado en su dispositivo. Se transmitirá automáticamente cuando se recupere la señal"*.
- El Service Worker interceptará la recuperación de conexión (mediante `navigator.onLine` y `sync`) y disparará una rutina de vaciado de cola con reintentos exponenciales y jitter, garantizando que ningún reporte se pierda.

## Consecuencias
- **Positivas:**
  - **Cero pérdida de datos (QA-01):** La persistencia en IndexedDB es tolerante a cierres accidentales del navegador o reinicios del teléfono.
  - **Adopción inmediata:** El ciudadano no necesita descargar gigabytes de una tienda; solo abre un enlace ligero (< 1.5 MB en primera carga).
  - **Velocidad de entrega (R-01):** Se construye en HTML5/TypeScript estándar sin duplicar código para iOS y Android.
  - **Ahorro de ancho de banda:** La compresión en cliente reduce el tamaño de imágenes de 8 MB a 400 KB antes de la transmisión, aliviando la saturación de la red móvil arequipeña.
- **Negativas y Riesgos mitigados:**
  - **Restricciones de Background Sync en iOS Safari:** WebKit en dispositivos Apple impone limitaciones al Background Sync cuando la app no está en primer plano.  
    *Mitigación:* Se implementa un listener en el evento `visibilitychange` y `focus` de la página para reanudar el envío en cuanto el usuario vuelve a abrir la PWA.
  - **Capacidad de almacenamiento local:** IndexedDB puede ser purgada por el sistema operativo si el smartphone se queda sin espacio de almacenamiento.  
    *Mitigación:* Se solicita almacenamiento persistente mediante `navigator.storage.persist()`, lo que impide que el navegador elimine la base de datos local ante limpiezas automáticas de memoria.
  - **Prevención de tormentas de reconexión (*Thundering Herd*):** Si miles de dispositivos intentan reconectarse en el mismo segundo exacto, podrían saturar Nginx.  
    *Mitigación:* El Service Worker aplicará una política de reintentos con retroceso exponencial y variación aleatoria (*Full Jitter*): $T_{\text{espera}} = \text{random}(0, \min(M, T_0 \cdot 2^{\text{intento}}))$, dispersando la carga de sincronización en una ventana suave de 3 minutos.
