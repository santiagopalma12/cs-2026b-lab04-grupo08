"""Módulo de sincronización y procesamiento post-sismo (Versión ANTES).

Implementación ingenua y monolítica previa a la aplicación de patrones de diseño GoF.
Presenta múltiples olores de código: método largo, alta complejidad ciclomática,
condicionales anidados sobre estados y canales, duplicación de lógica de reintentos,
notificaciones manuales y componente de IA sin aislamiento ni guardrails.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Optional
from uuid import UUID, uuid4

from sismoreporta.externos import (
    RedisBrokerSDK,
    RabbitMQSDK,
    SmsSatelitalGatewaySDK,
    ClienteLLMSimulado,
)


@dataclass(frozen=True)
class Coordenadas:
    """Coordenadas geográficas GPS de emergencia."""
    latitud: Decimal
    longitud: Decimal

    def esta_dentro_de_geocerca(self) -> bool:
        # Delimitación provincial aproximada de Arequipa
        return (Decimal("-16.60") <= self.latitud <= Decimal("-16.20")) and \
               (Decimal("-71.70") <= self.longitud <= Decimal("-71.30"))


@dataclass
class Reporte:
    """Entidad de reporte de daño estructural por sismo."""
    descripcion: str
    coordenadas: Coordenadas
    severidad: str = "MODERADA"
    estado: str = "BORRADOR"
    id: UUID = field(default_factory=uuid4)
    fecha_sincronizacion: Optional[datetime] = None


class ServicioSincronizacion:
    """Servicio ingenuo con alta complejidad ciclomática y olores de código."""
    def __init__(
        self,
        redis: Optional[RedisBrokerSDK] = None,
        rabbit: Optional[RabbitMQSDK] = None,
        sms: Optional[SmsSatelitalGatewaySDK] = None,
        llm: Optional[ClienteLLMSimulado] = None,
    ) -> None:
        self.redis = redis or RedisBrokerSDK()
        self.rabbit = rabbit or RabbitMQSDK()
        self.sms = sms or SmsSatelitalGatewaySDK()
        self.llm = llm or ClienteLLMSimulado()
        self.eventos: List[str] = []

    def sincronizar_reporte(self, reporte: Reporte, canal: str = "REDIS") -> str:
        """Flujo crítico monolítico: valida estado, geocerca, despacha y notifica."""
        # Olor 1: Condicionales anidados sobre el estado
        if reporte.estado != "BORRADOR" and reporte.estado != "ENCOLADO":
            if reporte.estado == "ATENDIDO":
                raise ValueError("El reporte ya fue atendido")
            elif reporte.estado == "DESCARTADO":
                raise ValueError("El reporte fue descartado previamente")
            elif reporte.estado == "RECIBIDO":
                raise ValueError("El reporte ya fue recibido y sincronizado")
            else:
                raise ValueError(f"Estado no válido para sincronización: {reporte.estado}")

        if not reporte.descripcion or not reporte.descripcion.strip():
            raise ValueError("El reporte no tiene descripción válida")

        # Validación geográfica
        if not reporte.coordenadas.esta_dentro_de_geocerca():
            reporte.estado = "DESCARTADO"
            return reporte.estado

        # Olor 2 y 3: if/elif por canal de despacho y reintentos duplicados con conocimiento de SDKs
        aprobado = False
        if canal == "REDIS":
            for intento in range(3):
                try:
                    payload = json.dumps({"id": str(reporte.id), "desc": reporte.descripcion})
                    r = self.redis.rpush("cola:triaje", payload)
                    aprobado = bool(r.get("queued", False))
                    break
                except TimeoutError:
                    if intento == 2:
                        aprobado = False
        elif canal == "RABBITMQ":
            for intento in range(3):
                try:
                    body = json.dumps({"id": str(reporte.id), "desc": reporte.descripcion}).encode("utf-8")
                    codigo, _ = self.rabbit.basic_publish("", "cola:triaje", body)
                    aprobado = (codigo == 200)
                    break
                except TimeoutError:
                    if intento == 2:
                        aprobado = False
        elif canal == "SMS_SATELITAL":
            for intento in range(3):
                try:
                    trama = f"REP:{reporte.id}:{reporte.descripcion[:20]}".encode("utf-8").hex()
                    aprobado = self.sms.transmitir_trama("+51954000111", trama)
                    break
                except TimeoutError:
                    if intento == 2:
                        aprobado = False
        else:
            raise ValueError(f"Canal de despacho no soportado: {canal}")

        # Transición y eventos manuales
        if aprobado:
            reporte.estado = "RECIBIDO"
            reporte.fecha_sincronizacion = datetime.now(timezone.utc)
            # Olor 4: Notificaciones manuales acopladas a mano
            self.eventos.append(f"coe:alerta:Reporte {reporte.id} recibido en Arequipa")
            self.eventos.append(f"auditoria:{reporte.id}:{canal}")
        else:
            reporte.estado = "DESCARTADO"

        return reporte.estado

    def clasificar_severidad_con_ia(self, descripcion: str, proveedor: str = "MOCK") -> str:
        """Clasificación ingenua de IA sin caché, sin guardrails y acoplada a proveedores."""
        # Olor 5: if/elif por proveedor de IA sin desacoplamiento ni guardrails
        if proveedor == "MOCK":
            resp = self.llm.generate_text(f"Evaluar daños post-sismo: {descripcion}")
            texto = resp["text"]
        elif proveedor == "GEMINI":
            resp = self.llm.generate_text(f"[GEMINI-SYSTEM] Evaluar daños: {descripcion}")
            texto = resp["text"]
        else:
            raise ValueError(f"Proveedor de IA no soportado: {proveedor}")

        # Sin caché (se paga por cada llamada duplicada)
        # Sin guardrails (acepta cualquier respuesta, incluso alucinaciones de magnitud o pánico)
        return texto
