"""Aislamiento del componente de Inteligencia Artificial post-sismo (E5).

Implementa Strategy, Adapter, Decorator y Chain of Responsibility:
- ProveedorLLM (Strategy): Interfaz desacoplada del proveedor de lenguaje.
- ClienteLLMAdapter (Adapter): Adapta el SDK simulado (o real) a la interfaz ProveedorLLM.
- ConCacheLLM (Decorator): Previene costos y latencia duplicados para prompts idénticos.
- Guardrail y subclases (Chain of Responsibility): Protege el sistema frente a respuestas
  no confiables del LLM (magnitudes sismológicas inventadas, pánico social o formatos inválidos).
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Dict, List, Optional

from sismoreporta.externos import ClienteLLMSimulado


# ==============================================================================
# STRATEGY & ADAPTER: Interfaz común y adaptador de LLM
# ==============================================================================

class ProveedorLLM(ABC):
    """Puerto de dominio (STRATEGY): desacopla al sistema de proveedores de IA."""
    @abstractmethod
    def completar(self, prompt: str) -> str:
        """Envía el prompt al modelo y devuelve el texto procesado."""
        ...


class ClienteLLMAdapter(ProveedorLLM):
    """ADAPTER: traduce las llamadas hacia el SDK del modelo generativo."""
    def __init__(self, sdk: Optional[ClienteLLMSimulado] = None) -> None:
        self._sdk = sdk or ClienteLLMSimulado()

    def completar(self, prompt: str) -> str:
        respuesta = self._sdk.generate_text(prompt)
        return respuesta.get("text", "")


# ==============================================================================
# DECORATOR: Almacenamiento en caché de inferencias
# ==============================================================================

class ConCacheLLM(ProveedorLLM):
    """DECORATOR: evita llamar y pagar reiteradamente por el mismo prompt."""
    def __init__(self, proveedor_interno: ProveedorLLM) -> None:
        self._interno = proveedor_interno
        self._cache: Dict[str, str] = {}

    def completar(self, prompt: str) -> str:
        if prompt not in self._cache:
            self._cache[prompt] = self._interno.completar(prompt)
        return self._cache[prompt]

    @property
    def total_en_cache(self) -> int:
        return len(self._cache)


# ==============================================================================
# CHAIN OF RESPONSIBILITY: Cadena de guardrails de validación de salida
# ==============================================================================

class Guardrail(ABC):
    """Manejador base de la cadena de responsabilidad para sanitizar la salida del LLM."""
    def __init__(self, siguiente: Optional[Guardrail] = None) -> None:
        self._siguiente = siguiente

    def validar(self, texto: str) -> str:
        """Aplica la regla actual y delega en el siguiente eslabón de la cadena."""
        texto_procesado = self._aplicar(texto)
        if self._siguiente:
            return self._siguiente.validar(texto_procesado)
        return texto_procesado

    @abstractmethod
    def _aplicar(self, texto: str) -> str:
        """Regla de validación o transformación específica del eslabón."""
        ...


class SinAlucinacionMagnitud(Guardrail):
    """CHAIN: prohíbe que el LLM invente magnitudes sismológicas no oficiales (solo IGP)."""
    TERMINOS_PROHIBIDOS = ["richter", "magnitud 8", "magnitud 7", "magnitud 9", "grados mw"]

    def _aplicar(self, texto: str) -> str:
        texto_lower = texto.lower()
        for termino in self.TERMINOS_PROHIBIDOS:
            if termino in texto_lower:
                raise ValueError(f"Guardrail: la IA inventó una magnitud sismológica no oficial ('{termino}')")
        return texto


class SinPanicoSocial(Guardrail):
    """CHAIN: prohíbe frases sensacionalistas o alarmistas que desaten el caos ciudadano."""
    FRASES_PANICO = ["evacúen arequipa", "evacuen arequipa", "saqueos inminentes", "tsunami en la ciudad", "caos total"]

    def _aplicar(self, texto: str) -> str:
        texto_lower = texto.lower()
        for frase in self.FRASES_PANICO:
            if frase in texto_lower:
                raise ValueError(f"Guardrail: afirmación alarmista no permitida ('{frase}')")
        return texto


class FormatoSeveridadValido(Guardrail):
    """CHAIN: asegura que la clasificación contenga una severidad del catálogo oficial."""
    SEVERIDADES_VALIDAS = ["LEVE", "MODERADA", "GRAVE", "CATASTROFICA"]

    def _aplicar(self, texto: str) -> str:
        texto_upper = texto.upper()
        if not any(sev in texto_upper for sev in self.SEVERIDADES_VALIDAS):
            raise ValueError(f"Guardrail: severidad no reconocida en la respuesta del LLM ('{texto[:40]}...')")
        return texto


# ==============================================================================
# SERVICIO CLASIFICADOR INTEGRADO
# ==============================================================================

class ClasificadorSeveridadIA:
    """Componente que orquesta la IA aislada con caché y cadena de guardrails."""
    def __init__(self, proveedor: Optional[ProveedorLLM] = None, guardrails: Optional[Guardrail] = None) -> None:
        self.proveedor = ConCacheLLM(proveedor or ClienteLLMAdapter())
        self.guardrails = guardrails or SinAlucinacionMagnitud(
            SinPanicoSocial(FormatoSeveridadValido())
        )

    def clasificar(self, descripcion: str) -> str:
        """Clasifica la severidad del daño garantizando validación estricta."""
        prompt = f"Evaluar daños post-sismo: {descripcion}"
        salida_cruda = self.proveedor.completar(prompt)
        return self.guardrails.validar(salida_cruda)
