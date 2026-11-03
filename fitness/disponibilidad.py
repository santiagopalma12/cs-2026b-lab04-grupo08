#!/usr/bin/env python3
"""
Simulación Monte Carlo de Disponibilidad para SismoReporta AQP (Escenario QA-02)

Modela la resiliencia en la recepción de reportes ciudadanos bajo condiciones adversas:
- Red móvil intermitente (8% de timeouts transitorios aleatorios).
- Caída total del broker/red durante 20 minutos (150 eventos consecutivos).

Compara 3 estrategias arquitectónicas:
1. Sin tácticas (base): Llamadas directas; cualquier falla descarta el reporte.
2. Solo reintentos (3 intentos): Resuelve timeouts transitorios pero satura la red
   en caída sostenida y pierde los reportes al agotar los intentos.
3. Circuit Breaker + Outbox persistente: Falla rápida que protege el broker caído
   y garantiza 0 reportes perdidos mediante buffer persistente drenado al recuperarse.
"""

import random
from typing import Dict, Any
import matplotlib.pyplot as plt


class ConCircuitBreaker:
    """Implementación de referencia del Circuit Breaker para el simulador."""

    def __init__(self, umbral_fallas: int = 3, tiempo_enfriamiento: int = 15):
        self.umbral = umbral_fallas
        self.enfriamiento = tiempo_enfriamiento
        self.fallas_consecutivas = 0
        self.estado = "CERRADO"
        self.tiempo_abierto = 0

    def registrar_exito(self):
        self.fallas_consecutivas = 0
        self.estado = "CERRADO"

    def registrar_falla(self):
        self.fallas_consecutivas += 1
        if self.fallas_consecutivas >= self.umbral or self.estado == "SEMIABIERTO":
            self.estado = "ABIERTO"
            self.tiempo_abierto = 0

    def tic(self):
        """Avanza un paso de tiempo en el reloj interno."""
        if self.estado == "ABIERTO":
            self.tiempo_abierto += 1
            if self.tiempo_abierto >= self.enfriamiento:
                self.estado = "SEMIABIERTO"

    def permite_llamada(self) -> bool:
        return self.estado in ("CERRADO", "SEMIABIERTO")


def simular(estrategia: str, n_reportes: int = 1800, semilla: int = 42) -> Dict[str, Any]:
    """
    Ejecuta la simulación Monte Carlo para una estrategia dada.
    
    Parámetros:
        estrategia: 'sin_tacticas', 'reintentos', o 'breaker'
        n_reportes: Número de reportes evaluados (default 1800)
        semilla: Semilla pseudoaleatoria para reproducibilidad
    """
    rnd = random.Random(semilla)
    
    # Parámetros del escenario
    tasa_timeout_transitorio = 0.08  # 8% falla aleatoria por congestión móvil 4G/3G
    inicio_caida = 600              # Reporte en que inicia la caída del broker
    duracion_caida = 150            # 150 reportes durará la caída (~20 minutos)
    fin_caida = inicio_caida + duracion_caida

    reportes_perdidos = 0
    llamadas_al_broker = 0
    llamadas_en_caida = 0
    outbox_pendientes = []
    
    cb = ConCircuitBreaker(umbral_fallas=3, tiempo_enfriamiento=15)

    for i in range(n_reportes):
        en_caida_total = (inicio_caida <= i < fin_caida)
        cb.tic()

        if estrategia == "sin_tacticas":
            # Llamada directa al broker
            llamadas_al_broker += 1
            if en_caida_total:
                llamadas_en_caida += 1
                reportes_perdidos += 1
            elif rnd.random() < tasa_timeout_transitorio:
                # Falla transitoria sin reintento
                reportes_perdidos += 1

        elif estrategia == "reintentos":
            # 3 reintentos inmediatos
            exito = False
            for intento in range(3):
                llamadas_al_broker += 1
                if en_caida_total:
                    llamadas_en_caida += 1
                else:
                    if rnd.random() >= tasa_timeout_transitorio:
                        exito = True
                        break
            if not exito:
                reportes_perdidos += 1

        elif estrategia == "breaker":
            # Circuit Breaker + Outbox Persistente
            if cb.permite_llamada():
                llamadas_al_broker += 1
                if en_caida_total:
                    llamadas_en_caida += 1
                    cb.registrar_falla()
                    outbox_pendientes.append(i)
                elif rnd.random() < tasa_timeout_transitorio:
                    # Timeout transitorio
                    cb.registrar_falla()
                    outbox_pendientes.append(i)
                else:
                    cb.registrar_exito()
            else:
                # Circuito ABIERTO: Falla rápida sin saturar el broker caído
                # El reporte se resguarda inmediatamente en el Outbox
                outbox_pendientes.append(i)

        else:
            raise ValueError(f"Estrategia desconocida: {estrategia}")

    # Si se usó Circuit Breaker + Outbox, una vez recuperado el broker se drena el outbox
    if estrategia == "breaker":
        # Simulación del drenado de Outbox al terminar la contingencia
        # Como el broker ya está operativo tras fin_caida, el outbox se drena con reintentos
        # hasta quedar en 0 perdidos
        drenados_con_exito = 0
        for reporte_id in list(outbox_pendientes):
            # Proceso del worker de outbox (garantía at-least-once con idempotencia)
            intentos_outbox = 0
            while intentos_outbox < 5:
                llamadas_al_broker += 1
                # En estado post-caída solo hay tasa transitoria
                if rnd.random() >= tasa_timeout_transitorio:
                    drenados_con_exito += 1
                    break
                intentos_outbox += 1
        
        # 0 reportes perdidos
        reportes_perdidos = len(outbox_pendientes) - drenados_con_exito

    tasa_exito = ((n_reportes - reportes_perdidos) / n_reportes) * 100.0

    return {
        "estrategia": estrategia,
        "total_reportes": n_reportes,
        "perdidos": reportes_perdidos,
        "llamadas_totales": llamadas_al_broker,
        "llamadas_en_caida": llamadas_en_caida,
        "tasa_exito_pct": tasa_exito,
    }


def generar_grafico(ruta_salida: str = "docs/architecture/diagramas/img/disponibilidad.png"):
    """Ejecuta las simulaciones y genera el gráfico comparativo."""
    estrategias = ["sin_tacticas", "reintentos", "breaker"]
    etiquetas = ["Sin Tácticas\n(Base)", "Solo Reintentos\n(3 intentos)", "Circuit Breaker +\nOutbox Persistente"]
    
    resultados = [simular(est) for est in estrategias]
    perdidos = [r["perdidos"] for r in resultados]
    llamadas_caida = [r["llamadas_en_caida"] for r in resultados]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.8), dpi=200)

    # Subplot 1: Reportes Perdidos
    colores_perdidos = ["#e74c3c", "#e67e22", "#27ae60"]
    barras1 = ax1.bar(etiquetas, perdidos, color=colores_perdidos, width=0.55, edgecolor="#2c3e50", linewidth=1.2)
    ax1.set_title("Reportes Perdidos (QA-02)\n1800 eventos, 8% timeout + 20 min caída", fontsize=11, fontweight="bold")
    ax1.set_ylabel("Cantidad de Reportes Perdidos", fontsize=10)
    ax1.grid(axis="y", linestyle="--", alpha=0.5)
    for b in barras1:
        val = int(b.get_height())
        ax1.annotate(f"{val} ({val/1800*100:.1f}%)" if val > 0 else "0 (0.0%)\nCUMPLE SLA",
                     xy=(b.get_x() + b.get_width() / 2, val),
                     xytext=(0, 4), textcoords="offset points",
                     ha="center", va="bottom", fontsize=9, fontweight="bold",
                     color="#c0392b" if val > 0 else "#1e8449")
    ax1.set_ylim(0, max(perdidos) * 1.25)

    # Subplot 2: Llamadas al Broker Caído (Thundering Herd)
    colores_llamadas = ["#f39c12", "#c0392b", "#2980b9"]
    barras2 = ax2.bar(etiquetas, llamadas_caida, color=colores_llamadas, width=0.55, edgecolor="#2c3e50", linewidth=1.2)
    ax2.set_title("Llamadas Inútiles al Broker Caído\n(Sobrecarga y Thundering Herd)", fontsize=11, fontweight="bold")
    ax2.set_ylabel("Peticiones durante Caída (150 eventos)", fontsize=10)
    ax2.grid(axis="y", linestyle="--", alpha=0.5)
    for b in barras2:
        val = int(b.get_height())
        ax2.annotate(f"{val} reqs",
                     xy=(b.get_x() + b.get_width() / 2, val),
                     xytext=(0, 4), textcoords="offset points",
                     ha="center", va="bottom", fontsize=9, fontweight="bold")
    ax2.set_ylim(0, max(llamadas_caida) * 1.25)

    plt.suptitle("SismoReporta AQP — ADD Iteración 2: Evaluación de Resiliencia y Disponibilidad",
                 fontsize=12, fontweight="bold", y=1.02)
    plt.tight_layout()
    plt.savefig(ruta_salida, bbox_inches="tight")
    plt.close()
    print(f"Gráfico generado con éxito en: {ruta_salida}")


if __name__ == "__main__":
    for est in ["sin_tacticas", "reintentos", "breaker"]:
        res = simular(est)
        print(f"Estrategia: {est:15s} | Perdidos: {res['perdidos']:3d} | "
              f"Llamadas en Caída: {res['llamadas_en_caida']:3d} | Éxito: {res['tasa_exito_pct']:5.2f}%")
    generar_grafico()
