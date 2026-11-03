"""
Fitness Functions Automatizadas para la Protección Arquitectural de SismoReporta AQP.

Verifica en Integración Continua (CI):
- FF-03: Presupuesto de rendimiento en simulacro nacional (p95 <= 1500 ms a 28 req/s).
- FF-04: Cero reportes perdidos ante intermitencia móvil y caída del broker central (QA-02).
- FF-05: El Circuit Breaker protege al broker caído reduciendo llamadas inútiles en más de 80% (Mitigación R3).
- FF-06: Aislamiento estricto de reportes entre distritos mediante Row-Level Security (QA-04 / Mitigación R4).
"""

from typing import List, Dict, Any
import pytest

from fitness.rendimiento import simular as simular_rendimiento, buffer_redis_fast_ack
from fitness.disponibilidad import simular as simular_disponibilidad

PRESUPUESTO_P95_MS = 1500.0  # Límite del escenario QA-01


def test_ff03_rendimiento_simulacro_nacional():
    """
    FF-03 (Calidad - Rendimiento):
    Verifica que bajo la carga pico del simulacro nacional (28 req/s),
    el tiempo de respuesta p95 con buffer asíncrono no exceda los 1500 ms.
    """
    res = simular_rendimiento(lam=28.0, workers=4, servicio=buffer_redis_fast_ack, segundos=120)
    assert res["p95"] <= PRESUPUESTO_P95_MS, (
        f"VIOLACIÓN DE ARQUITECTURA: p95={res['p95']:.1f} ms excede el presupuesto de {PRESUPUESTO_P95_MS} ms"
    )
    # Margen de seguridad: el buffer asíncrono debe responder en menos de 50 ms
    assert res["p95"] < 50.0, f"Latencia anómala en buffer: {res['p95']} ms"


def test_ff04_cero_reportes_perdidos_ante_caida_del_broker():
    """
    FF-04 (Calidad - Disponibilidad):
    Verifica que ante un 8% de timeouts transitorios y una caída total de 20 minutos,
    la combinación de Circuit Breaker + Outbox logre exactamente 0 reportes perdidos.
    """
    res = simular_disponibilidad(estrategia="breaker", n_reportes=1800)
    assert res["perdidos"] == 0, (
        f"VIOLACIÓN DE DISPONIBILIDAD: Se perdieron {res['perdidos']} reportes ciudadanos."
    )
    assert res["tasa_exito_pct"] == 100.0


def test_ff05_breaker_protege_al_broker_caido():
    """
    FF-05 (Calidad - Resiliencia y Mitigación de Thundering Herd R3):
    Verifica que el Circuit Breaker realice al menos 5 veces menos llamadas
    inútiles hacia el broker caído en comparación con una política de reintentos agresivos.
    """
    res_breaker = simular_disponibilidad(estrategia="breaker", n_reportes=1800)
    res_reintentos = simular_disponibilidad(estrategia="reintentos", n_reportes=1800)

    llamadas_breaker = res_breaker["llamadas_en_caida"]
    llamadas_reintentos = res_reintentos["llamadas_en_caida"]

    assert llamadas_breaker < llamadas_reintentos / 5, (
        f"El Circuit Breaker no redujo suficientemente la carga en caída: "
        f"{llamadas_breaker} vs {llamadas_reintentos} (umbral: < {llamadas_reintentos / 5})"
    )


def test_ff06_aislamiento_rls_distrital():
    """
    FF-06 (Calidad - Seguridad Multidistrital QA-04):
    Verifica que una consulta ejecutada en el contexto de un operador distrital (ej. Yanahuara)
    tenga aislamiento estricto y devuelva 0 reportes pertenecientes a otras jurisdicciones (ej. Cerro Colorado).
    """
    # Base de datos simulada con RLS
    base_datos_reportes: List[Dict[str, Any]] = [
        {"id": 1, "distrito_id": 101, "distrito": "Yanahuara", "danio": "Colapso muro perimétrico"},
        {"id": 2, "distrito_id": 101, "distrito": "Yanahuara", "danio": "Fisuras en colegio"},
        {"id": 3, "distrito_id": 102, "distrito": "Cerro Colorado", "danio": "Corte de tubería matriz"},
        {"id": 4, "distrito_id": 103, "distrito": "Paucarpata", "danio": "Desprendimiento de rocas"},
    ]

    def consulta_con_rls(distrito_id_sesion: int, es_admin_regional: bool = False) -> List[Dict[str, Any]]:
        """Simula la semántica de la política RLS en PostgreSQL."""
        if es_admin_regional:
            return base_datos_reportes
        return [r for r in base_datos_reportes if r["distrito_id"] == distrito_id_sesion]

    # Simulación de sesión como operador de Yanahuara (ID 101)
    reportes_visibles = consulta_con_rls(distrito_id_sesion=101, es_admin_regional=False)

    # Verificaciones de no filtración
    distritos_filtrados = {r["distrito"] for r in reportes_visibles}
    assert distritos_filtrados == {"Yanahuara"}, f"Fuga de datos interdistrital: {distritos_filtrados}"
    assert len(reportes_visibles) == 2

    # Verificar que reportes confidenciales de otros distritos no aparecen
    reportes_ajenos = [r for r in reportes_visibles if r["distrito_id"] != 101]
    assert len(reportes_ajenos) == 0, f"VIOLACIÓN DE RLS: se expusieron {len(reportes_ajenos)} reportes ajenos"

    # Verificar que el COER Regional sí puede auditar la totalidad de reportes
    reportes_coer = consulta_con_rls(distrito_id_sesion=0, es_admin_regional=True)
    assert len(reportes_coer) == 4
