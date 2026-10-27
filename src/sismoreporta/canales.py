"""Módulo de canales de despacho y transporte de reportes de emergencia.

Implementa los patrones Strategy, Adapter, Decorator y Factory Method (Registro):
- ICanalDespacho (Strategy): Interfaz común (puerto) para cualquier canal de transporte.
- Adapters: Traducen las llamadas del dominio a los SDKs de Redis, RabbitMQ y SMS Satelital.
- ConReintentos (Decorator): Agrega tolerancia a fallas transparentemente.
- FabricaCanales (Factory Registro): Resuelve la estrategia adecuada desacoplando el dominio.
"""
from __future__ import annotations

import json
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Callable, Dict, Optional

from sismoreporta.externos import (
    RedisBrokerSDK,
    RabbitMQSDK,
    SmsSatelitalGatewaySDK,
)


@dataclass(frozen=True)
class ResultadoDespacho:
    """Value object que normaliza la respuesta de cualquier canal de transporte."""
    exitoso: bool
    mensaje_id: Optional[str] = None
    canal_usado: str = ""


class ICanalDespacho(ABC):
    """Puerto de dominio (STRATEGY): todas las estrategias de despacho se invocan igual."""
    @abstractmethod
    def despachar(self, reporte_id: str, descripcion: str) -> ResultadoDespacho:
        """Despacha el reporte hacia el buffer o medio de telecomunicaciones correspondiente."""
        ...


# ==============================================================================
# ADAPTERS: Traducen cada SDK externo específico al puerto ICanalDespacho
# ==============================================================================

class RedisCanalAdapter(ICanalDespacho):
    """ADAPTER: traduce las operaciones de dominio hacia RedisBrokerSDK."""
    def __init__(self, sdk: Optional[RedisBrokerSDK] = None) -> None:
        self._sdk = sdk or RedisBrokerSDK()

    def despachar(self, reporte_id: str, descripcion: str) -> ResultadoDespacho:
        payload = json.dumps({"id": reporte_id, "desc": descripcion})
        respuesta = self._sdk.rpush("cola:triaje", payload)
        return ResultadoDespacho(
            exitoso=bool(respuesta.get("queued", False)),
            mensaje_id=str(respuesta.get("id")),
            canal_usado="REDIS"
        )


class RabbitMQCanalAdapter(ICanalDespacho):
    """ADAPTER: traduce las operaciones hacia RabbitMQSDK (AMQP binario)."""
    def __init__(self, sdk: Optional[RabbitMQSDK] = None) -> None:
        self._sdk = sdk or RabbitMQSDK()

    def despachar(self, reporte_id: str, descripcion: str) -> ResultadoDespacho:
        body = json.dumps({"id": reporte_id, "desc": descripcion}).encode("utf-8")
        codigo, delivery_tag = self._sdk.basic_publish("", "cola:triaje", body)
        return ResultadoDespacho(
            exitoso=(codigo == 200),
            mensaje_id=delivery_tag,
            canal_usado="RABBITMQ"
        )


class SmsSatelitalCanalAdapter(ICanalDespacho):
    """ADAPTER: traduce hacia SmsSatelitalGatewaySDK para contingencia extrema."""
    def __init__(self, sdk: Optional[SmsSatelitalGatewaySDK] = None) -> None:
        self._sdk = sdk or SmsSatelitalGatewaySDK()

    def despachar(self, reporte_id: str, descripcion: str) -> ResultadoDespacho:
        trama_hex = f"REP:{reporte_id}:{descripcion[:20]}".encode("utf-8").hex()
        ok = self._sdk.transmitir_trama("+51954000111", trama_hex)
        return ResultadoDespacho(
            exitoso=ok,
            mensaje_id=f"sms-{reporte_id[:8]}",
            canal_usado="SMS_SATELITAL"
        )


# ==============================================================================
# DECORATOR: Agrega reintentos transparentemente a cualquier ICanalDespacho
# ==============================================================================

class ConReintentos(ICanalDespacho):
    """DECORATOR: envuelve una estrategia para reintentar solo ante TimeoutError."""
    def __init__(self, canal_interno: ICanalDespacho, intentos: int = 3) -> None:
        self._interno = canal_interno
        self._intentos = intentos

    def despachar(self, reporte_id: str, descripcion: str) -> ResultadoDespacho:
        for _ in range(self._intentos):
            try:
                return self._interno.despachar(reporte_id, descripcion)
            except TimeoutError:
                continue
        return ResultadoDespacho(exitoso=False, canal_usado="TIMEOUT_FALLIDO")


# ==============================================================================
# FACTORY (Registro): Resuelve la estrategia adecuada por nombre
# ==============================================================================

class FabricaCanales:
    """FACTORY METHOD / REGISTRO: crea la estrategia de transporte sin acoplamiento."""
    def __init__(self) -> None:
        self._creadores: Dict[str, Callable[[], ICanalDespacho]] = {}

    def registrar(self, nombre_canal: str, creador: Callable[[], ICanalDespacho]) -> None:
        """Registra un nuevo canal dinámicamente cumpliendo el principio Abierto/Cerrado."""
        self._creadores[nombre_canal.upper()] = creador

    def crear(self, nombre_canal: str) -> ICanalDespacho:
        """Instancia la estrategia registrada envuelta en tolerancia a fallas."""
        clave = nombre_canal.upper()
        if clave not in self._creadores:
            raise ValueError(f"Canal de despacho no soportado: {nombre_canal}")
        canal_base = self._creadores[clave]()
        return ConReintentos(canal_base)
