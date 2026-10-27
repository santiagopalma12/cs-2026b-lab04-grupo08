"""Patrón Command para sincronización diferida y encolamiento offline post-sismo.

Cumple la sugerencia formal de la Tabla 7 (Caso 8: SismoReporta AQP):
"Reporte sin señal -> Command + cola".
Encapsula cada solicitud de sincronización como un objeto comando independiente,
permitiendo encolar operaciones durante apagones de red y ejecutarlas por lote al volver la señal.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, List, Optional


class IComando(ABC):
    """Interfaz COMMAND para acciones diferidas de emergencia."""
    @abstractmethod
    def ejecutar(self) -> bool:
        """Ejecuta la acción encapsulada sobre el receptor."""
        ...


class ComandoSincronizarReporte(IComando):
    """Comando concreto que encapsula la sincronización de un reporte individual."""
    def __init__(self, receptor_servicio: Any, reporte: Any, canal: str = "REDIS") -> None:
        self._servicio = receptor_servicio
        self._reporte = reporte
        self._canal = canal
        self.ejecutado = False
        self.resultado_estado: Optional[str] = None

    def ejecutar(self) -> bool:
        """Ejecuta la sincronización delegando en el servicio orquestador."""
        self.resultado_estado = self._servicio.sincronizar_reporte(self._reporte, self._canal)
        self.ejecutado = True
        return self.resultado_estado == "RECIBIDO"


class ColaComandosOffline:
    """Invocador (INVOKER) que almacena comandos acumulados offline y los procesa en lote."""
    def __init__(self) -> None:
        self._cola: List[IComando] = []
        self._historial: List[IComando] = []

    def encolar(self, comando: IComando) -> None:
        """Registra un nuevo comando pendiente de transmisión."""
        self._cola.append(comando)

    @property
    def pendientes(self) -> int:
        return len(self._cola)

    def procesar_lote(self) -> int:
        """Procesa todos los comandos acumulados cuando se restablece la conectividad."""
        exitosos = 0
        while self._cola:
            cmd = self._cola.pop(0)
            if cmd.ejecutar():
                exitosos += 1
            self._historial.append(cmd)
        return exitosos
