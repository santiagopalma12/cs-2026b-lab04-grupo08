"""Simulación de eventos discretos del flujo de ingesta masiva de SismoReporta AQP.

Modela la API de ingesta como una cola M/G/c (procesos de llegada Poisson con 'c' workers concurrentes).
Evalúa el comportamiento del tiempo de respuesta del endpoint de sincronización diferida
ante el escenario de crecimiento: Simulacro nacional con 20,000 reportes en 1 hora.
Compara la arquitectura síncrona monolítica frente a tácticas de desempeño (Buffer Redis, Índices GiST).
"""
import heapq
import pathlib
import random
import statistics
from typing import Callable, Dict, List, Tuple

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


def simular(
    lam: float,
    workers: int,
    servicio: Callable[[random.Random], float],
    segundos: float = 120.0,
    semilla: int = 42
) -> Dict[str, float]:
    """Ejecuta una simulación de eventos discretos M/G/c durante un lapso de tiempo."""
    rnd = random.Random(semilla)
    t = 0.0
    llegadas: List[float] = []
    while t < segundos:
        t += rnd.expovariate(lam)
        llegadas.append(t)

    libres = [0.0] * workers
    heapq.heapify(libres)
    respuestas: List[float] = []

    for llegada in llegadas:
        libre = heapq.heappop(libres)
        inicio = max(llegada, libre)
        fin = inicio + servicio(rnd)
        heapq.heappush(libres, fin)
        respuestas.append((fin - llegada) * 1000.0)  # Convertir a milisegundos

    respuestas.sort()
    n = len(respuestas)
    if n == 0:
        return {"n": 0, "p50": 0.0, "p95": 0.0, "p99": 0.0, "media": 0.0}

    def percentil(q: float) -> float:
        return respuestas[int(q * (n - 1))]

    return {
        "n": n,
        "p50": percentil(0.50),
        "p95": percentil(0.95),
        "p99": percentil(0.99),
        "media": statistics.mean(respuestas),
    }


# ==============================================================================
# Modelos de Tiempo de Servicio por Táctica Arquitectónica (segundos)
# ==============================================================================

def bd_sincrona_sin_indices(r: random.Random) -> float:
    """Sin tácticas: persistencia síncrona en PostgreSQL y clustering sin índices (~380 ms)."""
    return r.lognormvariate(-0.95, 0.40)


def bd_con_indices_gist(r: random.Random) -> float:
    """Táctica 'Optimizar consultas': índices espaciales GiST en PostGIS (~110 ms)."""
    return r.lognormvariate(-2.20, 0.35)


def buffer_redis_fast_ack(r: random.Random) -> float:
    """Táctica 'Gestionar tasa de eventos': buffer en memoria Redis con Fast ACK HTTP 202 (~15 ms)."""
    return r.lognormvariate(-4.20, 0.25)


def buffer_redis_con_indices(r: random.Random) -> float:
    """Táctica combinada: buffer Redis + worker con índices GiST (~12 ms)."""
    return r.lognormvariate(-4.45, 0.20)


# Niveles de carga para el simulacro nacional
CARGAS: List[Tuple[str, float]] = [
    ("Normal post-sismo (6 req/s)", 6.0),
    ("Hora pico / réplica (18 req/s)", 18.0),
    ("Simulacro nacional (28 req/s)", 28.0),
]

PRESUPUESTO_P95_MS = 1500.0  # QA-01: p95 <= 1.5 s


def generar_grafico_rendimiento(ruta_salida: str = "rendimiento.png") -> None:
    """Genera visualización gráfica comparativa del impacto de las tácticas."""
    RED = "#C8310E"
    NAVY = "#1A3A5C"
    GREEN = "#1E7B34"
    GRAY = "#8C8C8C"
    ORG = "#E39B2D"
    BLUE = "#2E75B6"

    escenarios = [
        ("Sin tácticas (4 workers)", lambda l: simular(l, 4, bd_sincrona_sin_indices), RED),
        ("Escalar a 8 workers (síncrono)", lambda l: simular(l, 8, bd_sincrona_sin_indices), GRAY),
        ("Índices espaciales GiST", lambda l: simular(l, 4, bd_con_indices_gist), ORG),
        ("Buffer Redis (Fast ACK 202)", lambda l: simular(l, 4, buffer_redis_fast_ack), BLUE),
        ("Buffer Redis + GiST (Solución)", lambda l: simular(l, 4, buffer_redis_con_indices), GREEN),
    ]

    fig, axs = plt.subplots(1, 2, figsize=(13, 4.8), gridspec_kw={"width_ratios": [1.5, 1]})

    # Gráfico 1: Barras comparativas de p95 por nivel de carga
    ax1 = axs[0]
    x = np.arange(len(CARGAS))
    w = 0.16
    for i, (nombre, func, color) in enumerate(escenarios):
        valores = [func(lam)["p95"] for _, lam in CARGAS]
        barras = ax1.bar(x + (i - 2) * w, valores, w, color=color, label=nombre)
        for b, val in zip(barras, valores):
            txt = f"{val/1000.0:.1f} s" if val >= 1000.0 else f"{val:.0f} ms"
            ax1.text(
                b.get_x() + b.get_width() / 2,
                val * 1.15,
                txt,
                ha="center",
                fontsize=7.2,
                rotation=90,
                weight="bold"
            )

    ax1.set_yscale("log")
    ax1.set_ylim(5.0, 95000.0)
    ax1.axhline(PRESUPUESTO_P95_MS, ls="--", color="#333333", lw=1.2)
    ax1.text(2.45, 1800.0, f"Presupuesto QA-01: p95 ≤ {PRESUPUESTO_P95_MS/1000:.1f} s", ha="right", fontsize=9, color="#222222")
    ax1.set_xticks(x)
    ax1.set_xticklabels([f"Normal\n6 req/s", f"Hora pico\n18 req/s", f"Simulacro nacional\n28 req/s"], fontsize=9.5)
    ax1.set_ylabel("Latencia p95 (ms, escala logarítmica)")
    ax1.set_title("SismoReporta AQP: Tácticas de rendimiento ante el simulacro", fontsize=11.5, weight="bold", color=NAVY)
    ax1.legend(fontsize=8.0, frameon=False, ncol=2, loc="upper left")
    for s in ["top", "right"]:
        ax1.spines[s].set_visible(False)

    # Gráfico 2: Punto de sensibilidad frente a la tasa de llegada (congestión)
    ax2 = axs[1]
    tasa_llegada = np.linspace(4.0, 36.0, 18)
    p95_sincrono = [simular(l, 4, bd_sincrona_sin_indices)["p95"] for l in tasa_llegada]
    p95_redis = [simular(l, 4, buffer_redis_fast_ack)["p95"] for l in tasa_llegada]
    p95_solucion = [simular(l, 4, buffer_redis_con_indices)["p95"] for l in tasa_llegada]

    ax2.plot(tasa_llegada, p95_sincrono, "-o", color=RED, ms=3.0, label="Sin tácticas (Síncrono)")
    ax2.plot(tasa_llegada, p95_redis, "-s", color=BLUE, ms=3.0, label="Buffer Redis (Fast ACK)")
    ax2.plot(tasa_llegada, p95_solucion, "-^", color=GREEN, ms=3.0, label="Buffer Redis + GiST")

    ax2.axhline(PRESUPUESTO_P95_MS, ls="--", color="#333333", lw=1.2)
    ax2.set_yscale("log")
    ax2.set_ylim(5.0, 95000.0)
    ax2.set_xlabel("Tasa de llegada de reportes (req/s)")
    ax2.set_ylabel("Latencia p95 (ms, log)")
    ax2.set_title("Punto de sensibilidad: Saturación por ráfagas", fontsize=11.5, weight="bold", color=NAVY)
    ax2.legend(frameon=False, fontsize=8.5)
    for s in ["top", "right"]:
        ax2.spines[s].set_visible(False)

    plt.tight_layout()
    plt.savefig(ruta_salida, dpi=200, bbox_inches="tight")
    plt.close()
    print(f"Gráfico de rendimiento exportado exitosamente a: {ruta_salida}")


if __name__ == "__main__":
    print("=" * 75)
    print("SIMULACIÓN DE RENDIMIENTO: SISMOREPORTA AQP (SIMULACRO NACIONAL)")
    print("=" * 75)
    for carga_nombre, lam in CARGAS:
        print(f"\n--- Escenario de Carga: {carga_nombre} (4 workers) ---")
        for nombre, serv in [
            ("Sin tácticas (Síncrono)", bd_sincrona_sin_indices),
            ("Escalar a 8 workers", lambda r: bd_sincrona_sin_indices(r)),
            ("Índices GiST en PostGIS", bd_con_indices_gist),
            ("Buffer Redis (Fast ACK)", buffer_redis_fast_ack),
            ("Buffer Redis + GiST", buffer_redis_con_indices),
        ]:
            w = 8 if "8 workers" in nombre else 4
            res = simular(lam, w, serv)
            cumple = "CUMPLE" if res["p95"] <= PRESUPUESTO_P95_MS else "VIOLA PRESUPUESTO"
            print(f"  {nombre:30s} | p50={res['p50']:7.1f} ms | p95={res['p95']:7.1f} ms | [{cumple}]")

    # Generar visualización en PNG
    directorio_img = pathlib.Path("docs/architecture/diagramas/img")
    directorio_img.mkdir(parents=True, exist_ok=True)
    generar_grafico_rendimiento(str(directorio_img / "rendimiento.png"))
