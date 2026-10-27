"""Servicios externos simulados para SismoReporta AQP.

Simula SDKs de terceros con interfaces disímiles e incompatibles entre sí:
- RedisBrokerSDK: interfaz basada en diccionarios y strings.
- RabbitMQSDK: interfaz binaria AMQP con tuplas de código y entrega.
- SmsSatelitalGatewaySDK: interfaz de telecomunicaciones por trama hexadecimal.
- ClienteLLMSimulado: motor generativo para clasificación de daños.
"""
from __future__ import annotations

import json
from typing import Dict, Tuple, Optional
from uuid import uuid4


class RedisBrokerSDK:
    """SDK simulado de Redis (canal en memoria de alta velocidad)."""
    def __init__(self, fallas: int = 0) -> None:
        self.fallas = fallas
        self.llamadas = 0
        self.cola: list[dict] = []

    def rpush(self, canal: str, payload_json: str) -> Dict[str, str | bool]:
        self.llamadas += 1
        if self.fallas > 0:
            self.fallas -= 1
            raise TimeoutError("Error de conexión al socket de Redis (timeout).")
        data = json.loads(payload_json)
        msg_id = f"redis-msg-{uuid4().hex[:8]}"
        self.cola.append({"canal": canal, "id": msg_id, "data": data})
        return {"status": "OK", "id": msg_id, "queued": True}


class RabbitMQSDK:
    """SDK simulado de RabbitMQ (broker AMQP empresarial)."""
    def __init__(self, fallas: int = 0) -> None:
        self.fallas = fallas
        self.llamadas = 0
        self.mensajes: list[Tuple[str, str, bytes]] = []

    def basic_publish(self, exchange: str, routing_key: str, body_bytes: bytes) -> Tuple[int, str]:
        self.llamadas += 1
        if self.fallas > 0:
            self.fallas -= 1
            raise TimeoutError("Conexión con broker RabbitMQ interrumpida por timeout.")
        delivery_tag = f"amqp-tag-{uuid4().hex[:6]}"
        self.mensajes.append((exchange, routing_key, body_bytes))
        return (200, delivery_tag)


class SmsSatelitalGatewaySDK:
    """SDK simulado de Gateway Satelital (comunicaciones de emergencia COE)."""
    def __init__(self, fallas: int = 0) -> None:
        self.fallas = fallas
        self.llamadas = 0
        self.tramas: list[Tuple[str, str]] = []

    def transmitir_trama(self, numero_terminal: str, trama_hex: str) -> bool:
        self.llamadas += 1
        if self.fallas > 0:
            self.fallas -= 1
            raise TimeoutError("Enlace satelital fuera de cobertura o timeout de acuse.")
        self.tramas.append((numero_terminal, trama_hex))
        return True


class ClienteLLMSimulado:
    """SDK simulado de modelo de lenguaje (LLM) para clasificación de severidad."""
    def __init__(self, respuesta_predefinida: Optional[str] = None) -> None:
        self.respuesta_predefinida = respuesta_predefinida
        self.llamadas = 0
        self.prompts_recibidos: list[str] = []

    def generate_text(self, prompt: str) -> Dict[str, str]:
        self.llamadas += 1
        self.prompts_recibidos.append(prompt)
        if self.respuesta_predefinida is not None:
            return {"text": self.respuesta_predefinida, "model": "mock-llm-v1"}

        # Heurística simulada por defecto si no se especificó respuesta
        prompt_lower = prompt.lower()
        if "colapso" in prompt_lower or "atrapad" in prompt_lower or "muertos" in prompt_lower:
            resp = "CATASTROFICA: Colapso estructural severo con riesgo vital inminente."
        elif "grietas" in prompt_lower or "muro" in prompt_lower:
            resp = "GRAVE: Daños estructurales con compromiso de estabilidad."
        elif "vidrio" in prompt_lower or "fachada" in prompt_lower:
            resp = "MODERADA: Fisuras superficiales y desprendimiento no estructural."
        else:
            resp = "LEVE: Incidente menor sin riesgo estructural aparente."
        return {"text": resp, "model": "mock-llm-v1"}
