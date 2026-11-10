"""Módulo generador de criterios de aceptación en Gherkin usando prompts versionados (Lab 09 - Tarea A).

Se integra detrás del puerto ProveedorLLM (Strategy/Adapter del Lab 07).
Carga la plantilla desde prompts/criterios/<version>.txt y valida la salida con esquema.json.
"""
from __future__ import annotations

import json
import pathlib
from typing import Any, Dict, Optional

from jsonschema import ValidationError, validate
from sismoreporta.ia import ProveedorLLM

RAIZ_PROYECTO = pathlib.Path(__file__).resolve().parent.parent.parent
DIR_PROMPTS = RAIZ_PROYECTO / "prompts" / "criterios"
RUTA_ESQUEMA = DIR_PROMPTS / "esquema.json"


class SalidaInvalida(Exception):
    """Excepción lanzada cuando la respuesta del LLM no es un JSON válido o viola el esquema."""
    pass


class GeneradorCriterios:
    """Consume plantillas versionadas de criterios de aceptación detrás de ProveedorLLM."""

    def __init__(
        self,
        proveedor: ProveedorLLM,
        version: str = "v3.1",
        dir_prompts: Optional[pathlib.Path] = None,
        ruta_esquema: Optional[pathlib.Path] = None,
    ) -> None:
        self._proveedor = proveedor
        self.version = version
        self._dir_prompts = dir_prompts or DIR_PROMPTS
        self._ruta_esquema = ruta_esquema or RUTA_ESQUEMA

        archivo_plantilla = self._dir_prompts / f"{version}.txt"
        if not archivo_plantilla.exists():
            raise FileNotFoundError(f"Plantilla no encontrada: {archivo_plantilla}")
        self._plantilla = archivo_plantilla.read_text(encoding="utf-8")

        if not self._ruta_esquema.exists():
            raise FileNotFoundError(f"Esquema JSON no encontrado: {self._ruta_esquema}")
        self._esquema = json.loads(self._ruta_esquema.read_text(encoding="utf-8"))

    def generar(self, id_historia: str, historia: str) -> Dict[str, Any]:
        """Sustituye variables en la plantilla, invoca al LLM y valida el contrato JSON Schema."""
        prompt = (
            self._plantilla.replace("{{id}}", id_historia)
            .replace("{{historia}}", historia)
        )
        texto = self._proveedor.completar(prompt)
        try:
            datos = json.loads(texto)
            validate(instance=datos, schema=self._esquema)
        except (json.JSONDecodeError, ValidationError) as err:
            raise SalidaInvalida(
                f"Fallo de contrato para versión {self.version} e historia {id_historia}: {err}"
            ) from err
        return datos
