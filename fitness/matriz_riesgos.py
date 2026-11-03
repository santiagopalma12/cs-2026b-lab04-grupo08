#!/usr/bin/env python3
"""
Generador de la Matriz de Probabilidad e Impacto de Riesgos ATAM-lite (Lab 08).
Grafica los riesgos R1-R5 clasificados en Zona Crítica, Zona de Atención y Zona Aceptable.
"""

import matplotlib.pyplot as plt
import numpy as np

def generar_matriz_riesgos(ruta_salida: str = "docs/architecture/diagramas/img/riesgos.png"):
    fig, ax = plt.subplots(figsize=(8.5, 7.5), dpi=200)

    # Definir grilla de 5x5
    # Severidad = Probabilidad * Impacto
    # x: Impacto (1 a 5), y: Probabilidad (1 a 5)
    
    # Crear fondo por zonas según severidad (P x I)
    # Verde: Severidad < 8 (Zona Aceptable)
    # Amarillo/Naranja: 8 <= Severidad < 12 (Zona de Atención)
    # Rojo: Severidad >= 12 (Zona Crítica)
    x = np.linspace(0.5, 5.5, 100)
    y = np.linspace(0.5, 5.5, 100)
    X, Y = np.meshgrid(x, y)
    Z = X * Y

    # Mapa de colores para fondo
    cmap = plt.cm.RdYlGn_r
    # Definir niveles de contorno
    levels = [0, 7.99, 11.99, 25]
    colors = ["#d4edda", "#fff3cd", "#f8d7da"] # Verde suave, amarillo suave, rojo suave
    ax.contourf(X, Y, Z, levels=levels, colors=colors, alpha=0.85)

    # Líneas de cuadrícula
    for i in range(1, 6):
        ax.axvline(i + 0.5, color="#ced4da", linestyle="--", linewidth=1.0)
        ax.axhline(i + 0.5, color="#ced4da", linestyle="--", linewidth=1.0)

    # Definición de riesgos de SismoReporta AQP
    riesgos = [
        {
            "id": "R1",
            "nombre": "R1: Desborde RAM Redis\n(caída workers)",
            "p": 2, "i": 5, "sev": 10,
            "zona": "Atención",
            "color": "#d35400",
            "offset": (15, -10)
        },
        {
            "id": "R2",
            "nombre": "R2: SPOF en único VPS/PostgreSQL\n(QA-03)",
            "p": 3, "i": 4, "sev": 12,
            "zona": "Crítica",
            "color": "#c0392b",
            "offset": (-20, 15)
        },
        {
            "id": "R3",
            "nombre": "R3: Tormenta de reintentos\nThundering Herd (QA-02)",
            "p": 4, "i": 4, "sev": 16,
            "zona": "Crítica",
            "color": "#900c3f",
            "offset": (15, 12)
        },
        {
            "id": "R4",
            "nombre": "R4: Fuga multidistrital\npor error en query RLS",
            "p": 2, "i": 4, "sev": 8,
            "zona": "Atención",
            "color": "#e67e22",
            "offset": (15, -15)
        },
        {
            "id": "R5",
            "nombre": "R5: 'Celery no escala'\n(Falso Positivo IA refutado)",
            "p": 1, "i": 2, "sev": 2,
            "zona": "Descartado",
            "color": "#27ae60",
            "offset": (15, 10)
        },
    ]

    # Graficar puntos
    for r in riesgos:
        ax.scatter(r["i"], r["p"], s=260, color=r["color"], edgecolors="#2c3e50", linewidth=1.8, zorder=5)
        ax.annotate(
            f"{r['nombre']}\n[P×I = {r['sev']}]",
            xy=(r["i"], r["p"]),
            xytext=r["offset"],
            textcoords="offset points",
            fontsize=9.5,
            fontweight="bold",
            bbox=dict(boxstyle="round,pad=0.3", fc="white", ec=r["color"], lw=1.2, alpha=0.92),
            zorder=6
        )

    # Configuración de ejes
    ax.set_xlim(0.5, 5.5)
    ax.set_ylim(0.5, 5.5)
    ax.set_xticks(range(1, 6))
    ax.set_yticks(range(1, 6))
    ax.set_xticklabels(["1 (Insignificante)", "2 (Menor)", "3 (Moderado)", "4 (Mayor)", "5 (Catastrófico)"], fontsize=9.5)
    ax.set_yticklabels(["1 (Rara)", "2 (Poco probable)", "3 (Posible)", "4 (Probable)", "5 (Casi segura)"], fontsize=9.5)

    ax.set_xlabel("Impacto Técnico y Operativo", fontsize=11, fontweight="bold", labelpad=8)
    ax.set_ylabel("Probabilidad de Ocurrencia", fontsize=11, fontweight="bold", labelpad=8)
    ax.set_title("SismoReporta AQP — Matriz de Probabilidad e Impacto de Riesgos ATAM-lite", fontsize=12, fontweight="bold", pad=12)

    # Leyenda de Zonas
    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor="#f8d7da", edgecolor="#c0392b", label="Zona Crítica (Severidad ≥ 12) — Mitigación obligatoria"),
        Patch(facecolor="#fff3cd", edgecolor="#f39c12", label="Zona de Atención (8 ≤ Severidad < 12) — Monitoreo y control"),
        Patch(facecolor="#d4edda", edgecolor="#27ae60", label="Zona Aceptable / Descartada (Severidad < 8) — Riesgo asumido / Refutado"),
    ]
    ax.legend(handles=legend_elements, loc="upper left", fontsize=8.8, framealpha=0.95)

    plt.tight_layout()
    plt.savefig(ruta_salida, bbox_inches="tight")
    plt.close()
    print(f"Matriz de riesgos generada en: {ruta_salida}")

if __name__ == "__main__":
    generar_matriz_riesgos()
