"""Patrón State para el ciclo de vida del Reporte de Emergencia Sísmica.

Implementa formalmente el diagrama de estados de Lab 05 (estados-reporte.mmd):
- EstadoReporteState (Base): Prohíbe todas las transiciones por defecto con excepciones explícitas.
- BorradorState, EncoladoState, RecibidoState, VerificadoState, AtendidoState, DescartadoState.
Cada estado encapsula sus transiciones válidas eliminando los condicionales anidados.
"""
from __future__ import annotations

from abc import ABC
from datetime import datetime
from decimal import Decimal
from typing import Any

Reporte = Any  # Tipo desacoplado para satisfacer firmas sin acoplarse a la capa de servicio


class EstadoReporteState(ABC):
    """Clase base abstracta (STATE) que prohíbe transiciones por defecto."""
    nombre: str = "DESCONOCIDO"

    def encolar_offline(self, reporte: Any) -> None:
        raise ValueError(f"No se puede encolar un reporte en estado {self.nombre}")

    def sincronizar(self, reporte: Reporte, fecha: datetime) -> None:
        if self.nombre == "ATENDIDO":
            raise ValueError("El reporte ya fue atendido")
        elif self.nombre == "DESCARTADO":
            raise ValueError("El reporte fue descartado previamente")
        raise ValueError(f"No se puede sincronizar un reporte en estado {self.nombre}")

    def verificar_triaje(self, reporte: Reporte, score_prioridad: Decimal) -> None:
        raise ValueError(f"No se puede verificar triaje en un reporte en estado {self.nombre}")

    def atender_incidente(self, reporte: Reporte) -> None:
        raise ValueError(f"No se puede atender un reporte en estado {self.nombre}")

    def descartar(self, reporte: Reporte, motivo: str) -> None:
        raise ValueError(f"No se puede descartar un reporte en estado {self.nombre}")

    def __repr__(self) -> str:
        return self.nombre


class BorradorState(EstadoReporteState):
    """Estado inicial de creación local."""
    nombre = "BORRADOR"

    def encolar_offline(self, reporte: Reporte) -> None:
        if not reporte.descripcion or not reporte.descripcion.strip():
            raise ValueError("El reporte no tiene descripción válida")
        reporte.cambiar_estado(EncoladoState())

    def sincronizar(self, reporte: Reporte, fecha: datetime) -> None:
        if not reporte.descripcion or not reporte.descripcion.strip():
            raise ValueError("El reporte no tiene descripción válida")
        reporte.fecha_sincronizacion = fecha
        reporte.cambiar_estado(RecibidoState())

    def descartar(self, reporte: Reporte, motivo: str) -> None:
        reporte.cambiar_estado(DescartadoState())


class EncoladoState(EstadoReporteState):
    """Estado persistido en el cliente (IndexedDB) a la espera de conectividad."""
    nombre = "ENCOLADO"

    def sincronizar(self, reporte: Reporte, fecha: datetime) -> None:
        if not reporte.descripcion or not reporte.descripcion.strip():
            raise ValueError("El reporte no tiene descripción válida")
        reporte.fecha_sincronizacion = fecha
        reporte.cambiar_estado(RecibidoState())

    def descartar(self, reporte: Reporte, motivo: str) -> None:
        reporte.cambiar_estado(DescartadoState())


class RecibidoState(EstadoReporteState):
    """Estado persistido en el servidor tras conexión exitosa."""
    nombre = "RECIBIDO"

    def verificar_triaje(self, reporte: Reporte, score_prioridad: Decimal) -> None:
        if score_prioridad >= Decimal("0.70"):
            reporte.severidad = "CATASTROFICA"
        reporte.cambiar_estado(VerificadoState())

    def descartar(self, reporte: Reporte, motivo: str) -> None:
        reporte.cambiar_estado(DescartadoState())


class VerificadoState(EstadoReporteState):
    """Estado priorizado y listo para despacho de brigadas."""
    nombre = "VERIFICADO"

    def atender_incidente(self, reporte: Reporte) -> None:
        reporte.cambiar_estado(AtendidoState())

    def descartar(self, reporte: Reporte, motivo: str) -> None:
        reporte.cambiar_estado(DescartadoState())


class AtendidoState(EstadoReporteState):
    """Estado terminal de cierre de misión en campo."""
    nombre = "ATENDIDO"
    # No admite transiciones salientes: prohíbe todas


class DescartadoState(EstadoReporteState):
    """Estado terminal de descarte (fuera de geocerca o duplicado)."""
    nombre = "DESCARTADO"
    # No admite transiciones salientes: prohíbe todas
