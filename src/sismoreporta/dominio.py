"""Módulo de Dominio de SismoReporta AQP.

Implementación de clases de dominio, value objects, enumeraciones
e interfaces portuarias para el sistema de reporte de emergencias sísmicas.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import List, Optional
from uuid import UUID, uuid4


class EstadoReporte(str, Enum):
    """Ciclo de vida del reporte de emergencia ciudadana."""
    BORRADOR = "BORRADOR"
    ENCOLADO = "ENCOLADO"
    RECIBIDO = "RECIBIDO"
    VERIFICADO = "VERIFICADO"
    ATENDIDO = "ATENDIDO"
    DESCARTADO = "DESCARTADO"


class Severidad(str, Enum):
    """Nivel de severidad técnica del incidente reportado."""
    LEVE = "LEVE"
    MODERADA = "MODERADA"
    GRAVE = "GRAVE"
    CATASTROFICA = "CATASTROFICA"


@dataclass(frozen=True)
class Coordenadas:
    """Value Object inmutable que representa la ubicación geográfica GPS."""
    latitud: Decimal
    longitud: Decimal
    precision_metros: Decimal = Decimal("5.0")

    def esta_dentro_de_geocerca(self, poligono_arequipa: str) -> bool:
        """Verifica si el punto se encuentra dentro de la geocerca de Arequipa."""
        # Polígono aproximado de delimitación provincial de Arequipa
        lat_min, lat_max = Decimal("-16.60"), Decimal("-16.20")
        lon_min, lon_max = Decimal("-71.70"), Decimal("-71.30")
        return (lat_min <= self.latitud <= lat_max) and (lon_min <= self.longitud <= lon_max)

    def distancia_hacia(self, otra: Coordenadas) -> Decimal:
        """Cálculo euclidiano aproximado de distancia entre coordenadas."""
        d_lat = self.latitud - otra.latitud
        d_lon = self.longitud - otra.longitud
        return (d_lat**2 + d_lon**2).sqrt()


@dataclass
class FotoEvidencia:
    """Entidad que encapsula una imagen comprimida de daño estructural."""
    hash_sha256: str
    tamanio_bytes: int
    comprimida: bool = True
    id: UUID = field(default_factory=uuid4)

    def validar_tamanio_maximo(self, limite_bytes: int = 500 * 1024) -> bool:
        """Asegura que la imagen no exceda el límite de compresión PWA (500 KB)."""
        return self.tamanio_bytes <= limite_bytes

    def obtener_ruta_almacenamiento(self) -> str:
        """Genera la URI en el sistema de almacenamiento de objetos."""
        return f"evidencias/sismos/{self.id}_{self.hash_sha256[:12]}.jpg"


@dataclass
class Reporte:
    """Entidad raíz del agregado de reporte ciudadano."""
    descripcion: str
    coordenadas: Coordenadas
    severidad: Severidad = Severidad.MODERADA
    estado: EstadoReporte = EstadoReporte.BORRADOR
    fotos: List[FotoEvidencia] = field(default_factory=list)
    reintentos_sync: int = 0
    brigada_id: Optional[UUID] = None
    fecha_creacion: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    fecha_sincronizacion: Optional[datetime] = None
    id: UUID = field(default_factory=uuid4)

    def guardar_borrador(self) -> None:
        """Marca el reporte como borrador local."""
        self.estado = EstadoReporte.BORRADOR

    def encolar_offline(self) -> None:
        """Transición a encolado en IndexedDB ante falta de conectividad."""
        if not self.descripcion.strip():
            raise ValueError("El reporte requiere una descripción del daño.")
        self.estado = EstadoReporte.ENCOLADO

    def sincronizar(self, fecha: datetime) -> None:
        """Confirma la recepción en el servidor tras conexión exitosa."""
        if self.estado not in (EstadoReporte.BORRADOR, EstadoReporte.ENCOLADO):
            raise ValueError(f"No se puede sincronizar un reporte en estado {self.estado.value}")
        self.estado = EstadoReporte.RECIBIDO
        self.fecha_sincronizacion = fecha

    def verificar_triaje(self, score_prioridad: Decimal) -> None:
        """Verificación analítica en el módulo de Triaje post-ingesta."""
        if self.estado != EstadoReporte.RECIBIDO:
            raise ValueError("Solo reportes recibidos pueden ser triados.")
        if score_prioridad >= Decimal("0.70"):
            self.severidad = Severidad.CATASTROFICA
        self.estado = EstadoReporte.VERIFICADO

    def asignar_brigada(self, brigada_id: UUID) -> None:
        """Vincula una brigada de rescate al incidente."""
        if self.estado != EstadoReporte.VERIFICADO:
            raise ValueError("El reporte debe estar verificado antes de asignar brigada.")
        self.brigada_id = brigada_id

    def atender_incidente(self) -> None:
        """Cierre de atención en campo tras rescate efectivo."""
        if self.estado != EstadoReporte.VERIFICADO:
            raise ValueError("Solo incidentes verificados pueden ser marcados como atendidos.")
        self.estado = EstadoReporte.ATENDIDO

    def descartar(self, motivo: str) -> None:
        """Descarte por duplicado espacial o fuera de geocerca."""
        self.estado = EstadoReporte.DESCARTADO

    def adjuntar_foto(self, foto: FotoEvidencia) -> None:
        """Adjunta hasta un máximo de 3 fotografías comprimidas."""
        if len(self.fotos) >= 3:
            raise ValueError("Máximo 3 fotografías por reporte de emergencia.")
        self.fotos.append(foto)


@dataclass
class Ciudadano:
    """Actor que reporta el incidente post-sismo."""
    identificador_anonimo: str
    telefono_contacto: str
    id: UUID = field(default_factory=uuid4)

    def registrar_reporte(self, descripcion: str, coords: Coordenadas, sev: Severidad) -> Reporte:
        """Crea un nuevo reporte ciudadano."""
        return Reporte(descripcion=descripcion, coordenadas=coords, severidad=sev)


@dataclass
class Brigada:
    """Equipo de rescate y auxilio en campo."""
    codigo_indicativo: str
    especialidad: str
    ubicacion_actual: Coordenadas
    disponible: bool = True
    mision_actual_id: Optional[UUID] = None
    id: UUID = field(default_factory=uuid4)

    def asignar_mision(self, reporte_id: UUID) -> None:
        """Asigna una misión de auxilio."""
        if not self.disponible:
            raise ValueError("La brigada se encuentra ocupada.")
        self.disponible = False
        self.mision_actual_id = reporte_id

    def finalizar_atencion(self) -> None:
        """Libera la brigada tras completar la misión."""
        self.disponible = True
        self.mision_actual_id = None

    def actualizar_ubicacion(self, coords: Coordenadas) -> None:
        """Actualiza telemetría GPS de la unidad."""
        self.ubicacion_actual = coords


@dataclass
class ZonaImpacto:
    """Agrupación territorial por polígono distrital."""
    nombre_distrito: str
    geocerca_poligono: str
    nivel_riesgo: Severidad = Severidad.MODERADA
    reportes: List[Reporte] = field(default_factory=list)
    id: UUID = field(default_factory=uuid4)

    def registrar_reporte_en_zona(self, r: Reporte) -> None:
        self.reportes.append(r)

    def calcular_indice_criticidad(self) -> Decimal:
        """Calcula el índice ponderado en función del volumen de reportes."""
        return Decimal(len(self.reportes)) * Decimal("1.25")


# ==============================================================================
# PUERTOS / INTERFACES (Patrón Puertos y Adaptadores - ADR-001)
# ==============================================================================

class IBrokerCola(ABC):
    """Puerto hacia el broker de mensajería asíncrona en memoria (Redis)."""
    @abstractmethod
    def encolar_reporte(self, canal: str, payload_json: str) -> bool:
        """Encola el reporte para procesamiento asíncrono sin bloquear HTTP."""
        pass


class IRepositorioReportes(ABC):
    """Puerto hacia la persistencia relacional y espacial (PostgreSQL + PostGIS)."""
    @abstractmethod
    def buscar_por_id(self, id: UUID) -> Optional[Reporte]:
        pass

    @abstractmethod
    def guardar(self, reporte: Reporte) -> None:
        pass

    @abstractmethod
    def listar_por_estado(self, estado: EstadoReporte) -> List[Reporte]:
        pass


class INotificadorEmergencias(ABC):
    """Puerto hacia el subsistema de alertas masivas y despacho radial."""
    @abstractmethod
    def enviar_alerta_zonal(self, distrito: str, mensaje: str) -> None:
        pass

    @abstractmethod
    def notificar_despacho_brigada(self, brigada_id: UUID, reporte_id: UUID) -> None:
        pass


# ==============================================================================
# ADAPTADORES SECUNDARIOS (Infraestructura)
# ==============================================================================

class RedisBrokerAdapter(IBrokerCola):
    """Adaptador de infraestructura hacia el broker Redis."""
    def __init__(self, host: str = "localhost", puerto: int = 6379) -> None:
        self.host = host
        self.puerto = puerto

    def encolar_reporte(self, canal: str, payload_json: str) -> bool:
        # En producción: redis_client.rpush(canal, payload_json)
        raise NotImplementedError("Integración con Redis Broker pendiente en entorno de despliegue.")


class PostgresReporteAdapter(IRepositorioReportes):
    """Adaptador de persistencia sobre PostgreSQL y PostGIS."""
    def __init__(self, connection_string: str) -> None:
        self.connection_string = connection_string

    def buscar_por_id(self, id: UUID) -> Optional[Reporte]:
        raise NotImplementedError("Consulta SQL sobre tabla reportes pendiente de migración.")

    def guardar(self, reporte: Reporte) -> None:
        raise NotImplementedError("Operación INSERT/UPDATE sobre esquema ingesta pendiente.")

    def listar_por_estado(self, estado: EstadoReporte) -> List[Reporte]:
        raise NotImplementedError("Consulta SELECT filtrada por estado pendiente.")


# ==============================================================================
# SERVICIO DE APLICACIÓN
# ==============================================================================

class ServicioSincronizacion:
    """Servicio orquestador del caso de uso de ingesta offline."""
    def __init__(
        self,
        repo: IRepositorioReportes,
        broker: IBrokerCola,
        notificador: INotificadorEmergencias
    ) -> None:
        self.repo = repo
        self.broker = broker
        self.notificador = notificador

    def sincronizar_reporte(self, reporte: Reporte) -> bool:
        """Sincroniza un reporte individual validando geocerca."""
        if not reporte.coordenadas.esta_dentro_de_geocerca("AREQUIPA_PROVINCIA"):
            reporte.descartar("Coordenadas fuera del área provincial de Arequipa")
            return False

        reporte.sincronizar(datetime.now(timezone.utc))
        self.repo.guardar(reporte)
        self.broker.encolar_reporte("cola:triaje", str(reporte.id))
        return True

    def procesar_lote_offline(self, reportes: List[Reporte]) -> int:
        """Procesa una lista de reportes transmitidos por la PWA."""
        exitosos = 0
        for r in reportes:
            if self.sincronizar_reporte(r):
                exitosos += 1
        return exitosos
