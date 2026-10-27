"""Módulo de Servicio de SismoReporta AQP (Versión DESPUÉS del Refactor).

Orquesta el flujo crítico de sincronización integrando los patrones GoF aplicados:
- Strategy, Adapter y Factory (canales.py): Eliminan if/elif de transporte e infraestructura.
- State (estados.py): Encapsula el ciclo de vida de la entidad Reporte.
- Observer (eventos.py): Desacopla las alertas y logs de auditoría.
- Chain of Responsibility y Decorator (ia.py): Protegen y optimizan las llamadas al LLM.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Optional
from uuid import UUID, uuid4

from sismoreporta.canales import (
    FabricaCanales,
    ICanalDespacho,
    RedisCanalAdapter,
    RabbitMQCanalAdapter,
    SmsSatelitalCanalAdapter,
)
from sismoreporta.estados import (
    EstadoReporteState,
    BorradorState,
    EncoladoState,
    RecibidoState,
    AtendidoState,
    DescartadoState,
)
from sismoreporta.eventos import (
    PublicadorEventos,
    NotificadorCOE,
    AuditorEventosSismicos,
)
from sismoreporta.ia import ClasificadorSeveridadIA, ClienteLLMAdapter
from sismoreporta.externos import (
    RedisBrokerSDK,
    RabbitMQSDK,
    SmsSatelitalGatewaySDK,
    ClienteLLMSimulado,
)


@dataclass(frozen=True)
class Coordenadas:
    """Value object que representa la localización GPS de la emergencia."""
    latitud: Decimal
    longitud: Decimal

    def esta_dentro_de_geocerca(self) -> bool:
        """Verifica si el incidente se ubica en el radio provincial de Arequipa."""
        return (Decimal("-16.60") <= self.latitud <= Decimal("-16.20")) and \
               (Decimal("-71.70") <= self.longitud <= Decimal("-71.30"))


class Reporte:
    """Entidad principal que delega su ciclo de vida en el patrón STATE."""
    def __init__(
        self,
        descripcion: str,
        coordenadas: Coordenadas,
        severidad: str = "MODERADA",
        estado: str = "BORRADOR",
        id: Optional[UUID] = None,
    ) -> None:
        self.descripcion = descripcion
        self.coordenadas = coordenadas
        self.severidad = severidad
        self.id = id or uuid4()
        self.fecha_sincronizacion: Optional[datetime] = None

        # Mapeo inicial de string a clase State concreta
        estado_map = {
            "BORRADOR": BorradorState,
            "ENCOLADO": EncoladoState,
            "RECIBIDO": RecibidoState,
            "ATENDIDO": AtendidoState,
            "DESCARTADO": DescartadoState,
        }
        state_cls = estado_map.get(estado.upper(), BorradorState)
        self._estado: EstadoReporteState = state_cls()

    @property
    def estado(self) -> str:
        """Propiedad pública para compatibilidad con la interfaz observable."""
        return self._estado.nombre

    def cambiar_estado(self, nuevo_estado: EstadoReporteState) -> None:
        """Transición interna hacia un nuevo objeto de estado."""
        self._estado = nuevo_estado

    def encolar_offline(self) -> None:
        self._estado.encolar_offline(self)

    def sincronizar(self, fecha: datetime) -> None:
        self._estado.sincronizar(self, fecha)

    def verificar_triaje(self, score_prioridad: Decimal) -> None:
        self._estado.verificar_triaje(self, score_prioridad)

    def atender_incidente(self) -> None:
        self._estado.atender_incidente(self)

    def descartar(self, motivo: str) -> None:
        self._estado.descartar(self, motivo)


class ServicioSincronizacion:
    """Servicio orquestador refactorizado con complejidad ciclomática mínima (Rango A)."""
    def __init__(
        self,
        fabrica: Optional[FabricaCanales] = None,
        publicador: Optional[PublicadorEventos] = None,
        clasificador_ia: Optional[ClasificadorSeveridadIA] = None,
        redis: Optional[RedisBrokerSDK] = None,
        rabbit: Optional[RabbitMQSDK] = None,
        sms: Optional[SmsSatelitalGatewaySDK] = None,
        llm: Optional[ClienteLLMSimulado] = None,
    ) -> None:
        self.eventos: List[str] = []

        # 1. Configuración de la Factory de Canales (Strategy + Adapter + Decorator)
        self.fabrica = fabrica or FabricaCanales()
        self.fabrica.registrar("REDIS", lambda: RedisCanalAdapter(redis))
        self.fabrica.registrar("RABBITMQ", lambda: RabbitMQCanalAdapter(rabbit))
        self.fabrica.registrar("SMS_SATELITAL", lambda: SmsSatelitalCanalAdapter(sms))

        # 2. Configuración del Publicador de Eventos (Observer)
        self.publicador = publicador or PublicadorEventos()
        self.publicador.suscribir("reporte_recibido", NotificadorCOE(self.eventos))
        self.publicador.suscribir("reporte_recibido", AuditorEventosSismicos(self.eventos))

        # 3. Configuración del Componente de IA (Strategy + Adapter + Guardrails)
        self.clasificador_ia = clasificador_ia or ClasificadorSeveridadIA(
            proveedor=ClienteLLMAdapter(llm)
        )

    def sincronizar_reporte(self, reporte: Reporte, canal: str = "REDIS") -> str:
        """Flujo limpio de sincronización: complejidad ciclomática = 3 (A)."""
        # Se valida primero la existencia del canal antes de cualquier mutación
        canal_transporte = self.fabrica.crear(canal)

        # Validación geográfica
        if not reporte.coordenadas.esta_dentro_de_geocerca():
            reporte.descartar("Coordenadas fuera de la geocerca de Arequipa")
            return reporte.estado

        # Transmisión resiliente delegada en la Strategy/Adapter/Decorator
        resultado = canal_transporte.despachar(str(reporte.id), reporte.descripcion)

        if resultado.exitoso:
            reporte.sincronizar(datetime.now(timezone.utc))
            self.publicador.publicar("reporte_recibido", {
                "reporte_id": str(reporte.id),
                "canal": canal,
                "coordenadas": (reporte.coordenadas.latitud, reporte.coordenadas.longitud),
                "severidad": reporte.severidad,
            })
        else:
            reporte.descartar("Agotados reintentos de conexión con broker")

        return reporte.estado

    def clasificar_severidad_con_ia(self, descripcion: str, proveedor: str = "MOCK") -> str:
        """Invoca el clasificador de IA desacoplado con caché y guardrails."""
        if proveedor not in ("MOCK", "GEMINI"):
            raise ValueError(f"Proveedor de IA no soportado: {proveedor}")
        return self.clasificador_ia.clasificar(descripcion)
