"""Patrón Observer para la publicación y suscripción de eventos de emergencia.

Permite desacoplar las notificaciones del flujo transaccional:
- PublicadorEventos (Sujeto): Gestiona la lista de observadores por tipo de evento.
- Suscriptor (Interfaz Observer): Define el contrato de actualización.
- NotificadorCOE, AuditorEventosSismicos, TableroOperacionesMapa (Suscriptores concretos).
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List


class Suscriptor(ABC):
    """Interfaz observadora (OBSERVER) para reaccionar a eventos del sistema."""
    @abstractmethod
    def actualizar(self, tipo_evento: str, datos: Dict[str, Any]) -> None:
        """Maneja el evento recibido de forma desacoplada."""
        ...


class PublicadorEventos:
    """Sujeto concreto (OBSERVER) que difunde eventos a suscriptores registrados."""
    def __init__(self) -> None:
        self._suscriptores: Dict[str, List[Suscriptor]] = {}

    def suscribir(self, tipo_evento: str, suscriptor: Suscriptor) -> None:
        """Registra un observador interesado en un tipo de evento específico."""
        self._suscriptores.setdefault(tipo_evento, []).append(suscriptor)

    def desuscribir(self, tipo_evento: str, suscriptor: Suscriptor) -> None:
        """Elimina un observador del registro de eventos."""
        if tipo_evento in self._suscriptores and suscriptor in self._suscriptores[tipo_evento]:
            self._suscriptores[tipo_evento].remove(suscriptor)

    def publicar(self, tipo_evento: str, datos: Dict[str, Any]) -> None:
        """Notifica a todos los suscriptores suscritos al tipo de evento emitido."""
        for suscriptor in self._suscriptores.get(tipo_evento, []):
            suscriptor.actualizar(tipo_evento, datos)


# ==============================================================================
# SUSCRIPTORES CONCRETOS (Observadores)
# ==============================================================================

class NotificadorCOE(Suscriptor):
    """Observador que emite despachos radiales y consolas al COE de Arequipa."""
    def __init__(self, bandeja_registro: List[str]) -> None:
        self.bandeja = bandeja_registro

    def actualizar(self, tipo_evento: str, datos: Dict[str, Any]) -> None:
        rep_id = datos.get("reporte_id", "SIN_ID")
        self.bandeja.append(f"coe:alerta:Reporte {rep_id} recibido en Arequipa")


class AuditorEventosSismicos(Suscriptor):
    """Observador que registra pistas de auditoría forense post-desastre."""
    def __init__(self, bandeja_registro: List[str]) -> None:
        self.bandeja = bandeja_registro

    def actualizar(self, tipo_evento: str, datos: Dict[str, Any]) -> None:
        rep_id = datos.get("reporte_id", "SIN_ID")
        canal = datos.get("canal", "DESCONOCIDO")
        self.bandeja.append(f"auditoria:{rep_id}:{canal}")


class TableroOperacionesMapa(Suscriptor):
    """Observador que actualiza las capas GIS y mapas de calor en tiempo real."""
    def __init__(self) -> None:
        self.puntos_actualizados: List[Dict[str, Any]] = []

    def actualizar(self, tipo_evento: str, datos: Dict[str, Any]) -> None:
        self.puntos_actualizados.append({
            "reporte_id": datos.get("reporte_id"),
            "coords": datos.get("coordenadas"),
            "severidad": datos.get("severidad"),
        })
