workspace "SismoReporta AQP" "Modelo de arquitectura C4 para la plataforma de gestión de emergencias y rescate sísmico en Arequipa." {

    !identifiers hierarchical

    model {
        // =====================================================================
        // Actores (Personas)
        // =====================================================================
        ciudadano = person "Ciudadano Afectado" "Habitante de la región Arequipa que reporta daños estructurales, personas atrapadas o vías colapsadas mediante fotografías y GPS." "Persona"
        brigadista = person "Brigadista en Campo" "Personal de rescate (Bomberos, Cruz Roja, Defensa Civil) que recibe órdenes de auxilio y actualiza la atención de víctimas en tiempo real." "Persona"
        coordinador = person "Coordinador del COE" "Operador de Defensa Civil y COE que evalúa el mapa de calor de incidentes, prioriza severidades críticas y despacha brigadas de rescate." "Persona"

        // =====================================================================
        // Sistemas Externos
        // =====================================================================
        servicioMapas = softwareSystem "Servicio de Mapas y Teselas" "Servicio externo de cartografía base y geocodificación (OpenStreetMap / Mapbox Tiles)." "Externo"
        pasarelaSms = softwareSystem "Pasarela de Alertas SMS / Broadcast" "Servicio externo de telecomunicaciones para difusión masiva de alertas tempranas y órdenes de evacuación." "Externo"

        // =====================================================================
        // Sistema de Software: SismoReporta AQP
        // =====================================================================
        sismoReporta = softwareSystem "SismoReporta AQP" "Plataforma ciudadana y de coordinación de emergencias post-sismo con soporte de funcionamiento sin conexión y sincronización diferida masiva." {
            
            pwaCliente = container "PWA Cliente Offline" "Aplicación Web Progresiva para smartphones con persistencia local en IndexedDB y compresión de fotos en el cliente." "TypeScript, React, PWA, IndexedDB" "Web Browser,Mobile App"
            tableroCoe = container "Tablero Web COE" "Panel de mando web para operadores del COE con visualización cartográfica en tiempo real y consola de asignación de brigadas." "TypeScript, React, Leaflet, WebSockets" "Web Browser"
            proxyNginx = container "Proxy Perimetral Nginx" "Reverse proxy perimetral con terminación TLS, compresión HTTP y rate limiting para protección contra sobrecarga." "Nginx, Linux" "Web Server"
            
            apiBackend = container "API Backend Monolítico" "Núcleo monolítico modular en Python que procesa endpoints REST, gestiona conexiones WebSocket y orquesta la ingesta rápida." "Python, FastAPI, Pydantic, Uvicorn" "Application" {
                compIngesta = component "Componente de Ingesta y Sincronización" "Controlador REST y servicio de ingesta que valida geocercas, esquemas sintácticos y emite confirmaciones HTTP 202 inmediatas." "FastAPI, Pydantic"
                compTriaje = component "Componente de Triaje y Severidad" "Motor analítico de evaluación de gravedad estructural, colapsos y clasificación de criticidad." "Python"
                compDespacho = component "Componente de Despacho y Brigadas" "Algoritmo de asignación geodésica de brigadas de auxilio según proximidad espacial y disponibilidad." "Python"
                compGis = component "Componente de Servicios GIS" "Servicio geoespacial para cálculo de distancias geodésicas, clustering y mapa de calor con funciones PostGIS." "Python, GeoAlchemy2"
                compNotificaciones = component "Componente de Notificaciones" "Emisor de alertas en tiempo real vía WebSockets al COE y despachador de eventos a la pasarela de difusión masiva." "Python, WebSockets"
                compCompartido = component "Dominio Compartido y Tipos Base" "Entidades nucleares de dominio (Reporte, Coordenadas, FotoEvidencia, Severidad) e interfaces de abstracción." "Python, Pydantic"
            }

            brokerRedis = container "Buffer y Broker de Colas" "Buffer volátil en memoria para absorber picos extremos de ingesta y broker de colas para tareas en background." "Redis 7" "Queue,Database"
            workerAsincrono = container "Worker de Procesamiento Asíncrono" "Procesos en segundo plano (Celery) que ejecutan compresión de fotos, triaje diferido y deduplicación espacial." "Python, Celery" "Application"
            bdPostgis = container "Base de Datos Geoespacial" "Motor de base de datos relacional con extensión geoespacial para almacenamiento persistente y consultas espaciales." "PostgreSQL 16, PostGIS" "Database"
            almacenFotos = container "Almacén de Objetos Multimedia" "Servicio de almacenamiento compatible con S3 para custodia de fotografías de colapsos estructurales optimizadas." "MinIO S3" "Database"
        }

        // =====================================================================
        // Relaciones a Nivel de Contexto
        // =====================================================================
        ciudadano -> sismoReporta "Registra reportes de daños estructurales y personas atrapadas en"
        brigadista -> sismoReporta "Consulta órdenes de auxilio y actualiza estado de rescate en"
        coordinador -> sismoReporta "Monitorea mapa de calor y despacha cuadrillas de rescate desde"
        sismoReporta -> servicioMapas "Descarga teselas y capas cartográficas base desde" "HTTPS/Tiles"
        sismoReporta -> pasarelaSms "Emite órdenes de evacuación y alertas masivas a través de" "HTTPS/REST"

        // =====================================================================
        // Relaciones a Nivel de Contenedores
        // =====================================================================
        ciudadano -> sismoReporta.pwaCliente "Registra incidentes con fotos y GPS localmente en" "GUI táctil"
        brigadista -> sismoReporta.pwaCliente "Consulta asignaciones y actualiza progreso de atención en" "GUI táctil"
        coordinador -> sismoReporta.tableroCoe "Supervisa incidentes georreferenciados y coordina brigadas en" "GUI web"

        sismoReporta.pwaCliente -> sismoReporta.proxyNginx "Sincroniza reportes diferidos y consulta avisos de emergencia vía" "HTTPS/JSON"
        sismoReporta.tableroCoe -> sismoReporta.proxyNginx "Consume endpoints analíticos y recibe incidentes en vivo vía" "HTTPS/WSS"
        sismoReporta.proxyNginx -> sismoReporta.apiBackend "Redirige peticiones validadas e interconexión de sockets hacia" "HTTP/ReverseProxy"

        sismoReporta.apiBackend -> sismoReporta.brokerRedis "Encola eventos de triaje diferido y almacena caché de mapa de calor en" "Redis Protocol (RESP)"
        sismoReporta.apiBackend -> sismoReporta.bdPostgis "Lee y persiste incidentes, usuarios y metadatos geoespaciales en" "SQL/TCP"

        sismoReporta.workerAsincrono -> sismoReporta.brokerRedis "Consume tareas de la cola de triaje y procesamiento diferido desde" "Redis Protocol (RESP)"
        sismoReporta.workerAsincrono -> sismoReporta.bdPostgis "Ejecuta clustering espacial de reportes y actualiza severidades en" "SQL/TCP"
        sismoReporta.workerAsincrono -> sismoReporta.almacenFotos "Almacena fotografías comprimidas de evidencias en" "S3 API (HTTPS)"
        sismoReporta.workerAsincrono -> pasarelaSms "Solicita emisión masiva de alertas zonales a" "HTTPS/REST"

        sismoReporta.pwaCliente -> servicioMapas "Carga capas de mapas vectoriales y teselas desde" "HTTPS/Tiles"
        sismoReporta.tableroCoe -> servicioMapas "Carga mapas base satelitales y capas urbanas desde" "HTTPS/Tiles"

        // =====================================================================
        // Relaciones a Nivel de Componentes (Dentro de apiBackend)
        // =====================================================================
        sismoReporta.apiBackend.compIngesta -> sismoReporta.apiBackend.compCompartido "Instancia y valida entidades Reporte y Coordenadas usando" "In-process"
        sismoReporta.apiBackend.compTriaje -> sismoReporta.apiBackend.compCompartido "Evalúa severidad sobre entidades Reporte usando" "In-process"
        sismoReporta.apiBackend.compDespacho -> sismoReporta.apiBackend.compCompartido "Gestiona estados de Brigada y asignaciones usando" "In-process"
        sismoReporta.apiBackend.compGis -> sismoReporta.apiBackend.compCompartido "Procesa entidades Coordenadas y geometrías espaciales con" "In-process"
        sismoReporta.apiBackend.compNotificaciones -> sismoReporta.apiBackend.compCompartido "Estructura cargas de alerta según tipos de" "In-process"

        sismoReporta.apiBackend.compIngesta -> sismoReporta.brokerRedis "Encola ráfagas de incidentes para fast ACK en" "Redis Protocol (RESP)"
        sismoReporta.apiBackend.compIngesta -> sismoReporta.bdPostgis "Persiste incidentes iniciales con estado RECIBIDO en" "SQL/TCP"
        
        sismoReporta.apiBackend.compTriaje -> sismoReporta.apiBackend.compGis "Consulta proximidad espacial y deduplicación de incidentes a" "In-process"
        sismoReporta.apiBackend.compTriaje -> sismoReporta.apiBackend.compDespacho "Solicita despacho inmediato ante incidentes catastróficos a" "In-process"
        sismoReporta.apiBackend.compDespacho -> sismoReporta.apiBackend.compGis "Consulta distancias geodésicas de brigadas disponibles a" "In-process"
        sismoReporta.apiBackend.compDespacho -> sismoReporta.apiBackend.compNotificaciones "Notifica asignación de brigada a través de" "In-process"
        sismoReporta.apiBackend.compNotificaciones -> pasarelaSms "Emite mensajes de difusión masiva ante alertas extremas vía" "HTTPS/REST"

        // =====================================================================
        // Entorno de Despliegue: Producción
        // =====================================================================
        deploymentEnvironment "Producción" {
            
            dispositivoCiudadano = deploymentNode "Smartphone del Ciudadano" "Dispositivo móvil Android / iOS de ciudadanos afectados en Arequipa." "Terminal Móvil" {
                navegadorMovil = deploymentNode "Navegador Web Móvil" "Chrome Mobile, Firefox Mobile o Safari con soporte PWA." "Motor Web" {
                    containerInstance sismoReporta.pwaCliente
                }
            }

            dispositivoBrigadista = deploymentNode "Terminal de Campo del Brigadista" "Smartphone o tablet Android rugerizada con antena GPS de rescate." "Terminal Móvil" {
                navegadorBrigada = deploymentNode "Navegador Web / PWA Runtime" "Navegador web con geolocalización de alta precisión." "Motor Web" {
                    containerInstance sismoReporta.pwaCliente
                }
            }

            estacionCoe = deploymentNode "Estación de Mando del COE" "Computador de escritorio en la sala de crisis de Defensa Civil Arequipa." "Estación de Trabajo PC" {
                navegadorEscritorio = deploymentNode "Navegador Web de Escritorio" "Google Chrome / Mozilla Firefox actualizado." "Motor Web" {
                    containerInstance sismoReporta.tableroCoe
                }
            }

            servidorCloud = deploymentNode "Servidor Cloud VPS" "Instancia en la nube (Hetzner Cloud CX32 / DigitalOcean Droplet, 4 vCPUs, 8 GB RAM, 80 GB NVMe SSD, coste estimado: $15 USD/mes acorde a drivers.md R-03)." "Ubuntu Linux 24.04 LTS" {
                
                motorDocker = deploymentNode "Docker Engine" "Entorno de ejecución de contenedores gestionado con Docker Compose." "Docker 26.x" {
                    
                    nodoProxy = deploymentNode "Contenedor: Proxy Nginx" "Servidor perimetral reverse proxy y terminación SSL." "Docker Container" {
                        containerInstance sismoReporta.proxyNginx
                    }

                    nodoApi = deploymentNode "Contenedor: Monolito Backend" "Servidor de aplicación FastAPI gestionado con 4 workers Gunicorn." "Docker Container" {
                        containerInstance sismoReporta.apiBackend
                    }

                    nodoWorker = deploymentNode "Contenedor: Workers Celery" "Procesos en segundo plano para tareas asíncronas y triaje." "Docker Container" {
                        containerInstance sismoReporta.workerAsincrono
                    }

                    nodoRedis = deploymentNode "Contenedor: Redis Cache/Queue" "Instancia de Redis optimizada en memoria con política de desalojo volátil." "Docker Container" {
                        containerInstance sismoReporta.brokerRedis
                    }

                    nodoPostgres = deploymentNode "Contenedor: PostgreSQL + PostGIS" "Motor relacional con índices espaciales GiST en volúmenes persistentes." "Docker Container" {
                        containerInstance sismoReporta.bdPostgis
                    }

                    nodoMinio = deploymentNode "Contenedor: MinIO S3" "Almacenamiento de objetos local en volumen SSD para imágenes de daños." "Docker Container" {
                        containerInstance sismoReporta.almacenFotos
                    }
                }
            }

            nubeExterna = deploymentNode "Servicios Externos / Red Pública" "Infraestructura externa de proveedores SaaS y telecomunicaciones." "Red Global" {
                nodoOsm = deploymentNode "CDN de OpenStreetMap / Mapbox" "Red de distribución de teselas cartográficas mundiales." "Infraestructura Cloud CDN" {
                    softwareSystemInstance servicioMapas
                }
                nodoSms = deploymentNode "Pasarela de Telecomunicaciones SMS" "Infraestructura de telecomunicaciones y difusión celular de emergencia." "Gateway Telecom" {
                    softwareSystemInstance pasarelaSms
                }
            }
        }
    }

    views {
        systemContext sismoReporta "Contexto" "Diagrama de Contexto de SismoReporta AQP (Nivel 1 C4) mostrando los actores y límites del sistema." {
            include *
            autoLayout lr
        }

        container sismoReporta "Contenedores" "Diagrama de Contenedores de SismoReporta AQP (Nivel 2 C4) detallando aplicaciones, bases de datos y protocolos de comunicación." {
            include *
            autoLayout lr
        }

        component sismoReporta.apiBackend "Componentes" "Diagrama de Componentes del API Backend Monolítico (Nivel 3 C4) coherente con los módulos de diseño del Lab 05." {
            include *
            autoLayout lr
        }

        dynamic sismoReporta "SincronizacionOffline" "Vista Dinámica C4 del flujo crítico de sincronización diferida masiva tras restablecimiento de red celular." {
            sismoReporta.pwaCliente -> sismoReporta.proxyNginx "Sincroniza reportes diferidos y consulta avisos de emergencia vía"
            sismoReporta.proxyNginx -> sismoReporta.apiBackend "Redirige peticiones validadas e interconexión de sockets hacia"
            sismoReporta.apiBackend -> sismoReporta.bdPostgis "Lee y persiste incidentes, usuarios y metadatos geoespaciales en"
            sismoReporta.apiBackend -> sismoReporta.brokerRedis "Encola eventos de triaje diferido y almacena caché de mapa de calor en"
            sismoReporta.workerAsincrono -> sismoReporta.brokerRedis "Consume tareas de la cola de triaje y procesamiento diferido desde"
            sismoReporta.workerAsincrono -> sismoReporta.bdPostgis "Ejecuta clustering espacial de reportes y actualiza severidades en"
            sismoReporta.workerAsincrono -> sismoReporta.almacenFotos "Almacena fotografías comprimidas de evidencias en"
            sismoReporta.workerAsincrono -> pasarelaSms "Solicita emisión masiva de alertas zonales a"
            autoLayout lr
        }

        deployment sismoReporta "Producción" "Despliegue" "Vista de Despliegue en Producción (Nivel 4 C4) detallando nodos físicos, contenedores Docker y servicios externos." {
            include *
            autoLayout lr
        }

        styles {
            element "Person" {
                shape Person
                background #08427B
                color #FFFFFF
            }
            element "Software System" {
                background #1168BD
                color #FFFFFF
            }
            element "Externo" {
                background #999999
                color #FFFFFF
            }
            element "Container" {
                background #438DD5
                color #FFFFFF
            }
            element "Web Browser" {
                shape WebBrowser
            }
            element "Mobile App" {
                shape MobileDevicePortrait
            }
            element "Database" {
                shape Cylinder
            }
            element "Queue" {
                shape Pipe
            }
            element "Component" {
                background #85BBF0
                color #000000
            }
        }
    }
}
