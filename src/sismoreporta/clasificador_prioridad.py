"""Módulo clasificador de prioridad de reportes ciudadanos usando prompts versionados (Lab 09 - Tarea B).

Se integra detrás del puerto ProveedorLLM (Strategy/Adapter del Lab 07).
Carga la plantilla desde prompts/prioridad/<version>.txt y valida la salida con esquema.json.
"""
from __future__ import annotations

import json
import pathlib
from typing import Any, Dict, Optional

from jsonschema import ValidationError, validate
from sismoreporta.generador_criterios import SalidaInvalida
from sismoreporta.ia import ProveedorLLM

RAIZ_PROYECTO = pathlib.Path(__file__).resolve().parent.parent.parent
DIR_PROMPTS_PRIORIDAD = RAIZ_PROYECTO / "prompts" / "prioridad"
RUTA_ESQUEMA_PRIORIDAD = DIR_PROMPTS_PRIORIDAD / "esquema.json"


class ClasificadorPrioridad:
    """Consume plantillas versionadas para clasificación de prioridad de reportes post-sismo."""

    def __init__(
        self,
        proveedor: ProveedorLLM,
        version: str = "v3",
        dir_prompts: Optional[pathlib.Path] = None,
        ruta_esquema: Optional[pathlib.Path] = None,
    ) -> None:
        self._proveedor = proveedor
        self.version = version
        self._dir_prompts = dir_prompts or DIR_PROMPTS_PRIORIDAD
        self._ruta_esquema = ruta_esquema or RUTA_ESQUEMA_PRIORIDAD

        archivo_plantilla = self._dir_prompts / f"{version}.txt"
        if not archivo_plantilla.exists():
            raise FileNotFoundError(f"Plantilla no encontrada: {archivo_plantilla}")
        self._plantilla = archivo_plantilla.read_text(encoding="utf-8")

        if not self._ruta_esquema.exists():
            raise FileNotFoundError(f"Esquema JSON no encontrado: {self._ruta_esquema}")
        self._esquema = json.loads(self._ruta_esquema.read_text(encoding="utf-8"))

    def clasificar(self, id_reporte: str, texto_reporte: str) -> Dict[str, Any]:
        """Sustituye variables en la plantilla, invoca al LLM y valida el contrato JSON Schema."""
        prompt = (
            self._plantilla.replace("{{id}}", id_reporte)
            .replace("{{reporte}}", texto_reporte)
        )
        texto = self._proveedor.completar(prompt)
        try:
            datos = json.loads(texto)
            validate(instance=datos, schema=self._esquema)
        except (json.JSONDecodeError, ValidationError) as err:
            raise SalidaInvalida(
                f"Fallo de contrato para versión {self.version} y reporte {id_reporte}: {err}"
            ) from err
        return datos
