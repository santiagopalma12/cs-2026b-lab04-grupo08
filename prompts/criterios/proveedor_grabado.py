"""Proveedor personalizado de promptfoo que devuelve respuestas grabadas (fixtures).

Permite evaluar los prompts de manera determinista, repetible y sin requerir claves de API.
"""
import pathlib
import re

BASE = pathlib.Path(__file__).parent / "grabaciones"


def call_api(prompt, options, context):
    etiqueta = context["prompt"]["label"]
    # Extrae la version limpia (v1, v2, v3, v3.1, etc.)
    match = re.search(r"(v\d+(?:\.\d+)?)", etiqueta)
    version = match.group(1) if match else "v1"
    caso = context["vars"]["id"]
    archivo = BASE / version / f"{caso}.txt"
    if not archivo.exists():
        return {"error": f"Sin grabacion para {version}/{caso} en {archivo}"}
    return {"output": archivo.read_text(encoding="utf-8").strip()}
