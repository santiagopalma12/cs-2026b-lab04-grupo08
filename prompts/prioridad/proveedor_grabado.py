"""Proveedor personalizado de promptfoo para Tarea B (clasificación de prioridad)."""
import pathlib
import re

BASE = pathlib.Path(__file__).parent / "grabaciones"


def call_api(prompt, options, context):
    etiqueta = context["prompt"]["label"]
    match = re.search(r"(v\d+(?:\.\d+)?)", etiqueta)
    version = match.group(1) if match else "v1"
    caso = context["vars"]["id"]
    archivo = BASE / version / f"{caso}.txt"
    if not archivo.exists():
        return {"error": f"Sin grabacion para {version}/{caso} en {archivo}"}
    return {"output": archivo.read_text(encoding="utf-8").strip()}
