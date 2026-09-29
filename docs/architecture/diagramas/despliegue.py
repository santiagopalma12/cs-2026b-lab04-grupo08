"""
SismoReporta AQP — Vista de Despliegue Físico de Infraestructura
Construcción de Software · EPIS-UNSA · 2026-B · Grupo 08
Integrantes: Santiago Palma, Dario Rafael Cornejo Hurtado

Requiere: pip install diagrams (y Graphviz instalado en el sistema)
Para ejecutar: python despliegue.py
"""

import os
from diagrams import Diagram, Cluster, Edge
from diagrams.onprem.client import Users
from diagrams.generic.device import Mobile
from diagrams.generic.compute import Rack
from diagrams.onprem.network import Nginx, Internet
from diagrams.programming.framework import FastAPI
from diagrams.onprem.queue import Celery
from diagrams.onprem.inmemory import Redis
from diagrams.onprem.database import PostgreSQL
from diagrams.onprem.storage import Minio
from diagrams.onprem.monitoring import Grafana, Prometheus
from diagrams.saas.alerting import Pushover

# Configuración global del gráfico
graph_attr = {
    "fontsize": "22",
    "bgcolor": "white",
    "pad": "0.5",
    "splines": "spline",
    "nodesep": "0.8",
    "ranksep": "1.0",
}

with Diagram(
    "SismoReporta AQP - Vista de Despliegue de Infraestructura",
    filename="docs/architecture/diagramas/img/despliegue",
    show=False,
    direction="LR",
    graph_attr=graph_attr,
    outformat="png",
) as diag:

    # 1. Capa de Clientes / Dispositivos en Campo
    with Cluster("Dispositivos de Usuarios en Campo (Arequipa)"):
        with Cluster("Ciudadanos Afectados"):
            ciudadano_dev = Mobile("Smartphone Ciudadano\n(PWA + IndexedDB Offline)")
            ciudadanos = Users("20,000 Ciudadanos\n(Pico post-sismo)")
            ciudadanos >> ciudadano_dev

        with Cluster("Personal de Emergencia"):
            brigadista_dev = Mobile("Terminal Brigadista\n(PWA Campo + GPS)")
            coordinador_pc = Users("Puesto de Mando COE\n(Dashboard Cartográfico)")

    # 2. Servidor Único VPS en la Nube (Hetzner / DigitalOcean)
    with Cluster("Servidor VPS Cloud (4 vCPU / 8GB RAM / Ubuntu Linux)"):
        # Proxy Perimetral
        proxy = Nginx("Nginx Proxy\n(SSL / Rate-Limit / Gzip)")

        # Monolito Modular
        with Cluster("Contenedor Docker: Monolito Modular Python"):
            app = FastAPI("API SismoReporta\n(FastAPI / 4 Workers Gunicorn)")

        # Procesamiento en Background
        with Cluster("Cola de Tareas Asíncronas"):
            worker = Celery("Workers Celery\n(Compresión fotos / Triaje)")

        # Capa de Datos y Almacenamiento Local
        with Cluster("Almacenamiento y Estado"):
            cache_queue = Redis("Redis 7\n(Buffer de Ingesta & Caché)")
            db = PostgreSQL("PostgreSQL 16\n+ Extensión PostGIS")
            storage = Minio("MinIO S3 Local\n(Fotos Daños Estructurales)")

        # Observabilidad
        with Cluster("Monitoreo del Sistema"):
            prom = Prometheus("Prometheus\n(Métricas RPS y Latencia)")
            graf = Grafana("Grafana\n(Dashboard COE)")

    # 3. Servicios Externos y Red
    with Cluster("Servicios Externos / Red Pública"):
        osm = Internet("OpenStreetMap / Mapbox\n(Tiles Cartográficos)")
        sms_api = Pushover("Gateway SMS Masivo / Push\n(Alertas de Evacuación)")

    # Flujos de red e interconexiones
    ciudadano_dev >> Edge(label="1. POST /reportes (Sync)", color="#1565C0") >> proxy
    brigadista_dev >> Edge(label="Actualiza estado de rescate", color="#2E7D32") >> proxy
    coordinador_pc >> Edge(label="Consulta mapa y despacha", color="#C62828") >> proxy

    proxy >> Edge(label="Reverse Proxy (Unix Socket)", color="#37474F") >> app

    # Ingesta Asíncrona (Fast ACK)
    app >> Edge(label="2. Encola ráfaga (LPUSH)", color="#E65100", style="bold") >> cache_queue
    cache_queue >> Edge(label="3. Consume eventos", color="#E65100") >> worker

    # Persistencia y GIS
    worker >> Edge(label="4. Persiste incidente & GIS", color="#4A148C") >> db
    worker >> Edge(label="5. Guarda foto reducida", color="#00838F") >> storage
    app >> Edge(label="Lectura de incidentes", style="dashed") >> db
    app >> Edge(label="Lectura de caché GeoJSON", style="dashed") >> cache_queue

    # Monitoreo
    app >> Edge(style="dotted", color="#546E7A") >> prom
    prom >> Edge(style="dotted", color="#546E7A") >> graf

    # Salida a servicios externos
    worker >> Edge(label="Dispara SMS de evacuación", style="dashed", color="#D84315") >> sms_api
    app >> Edge(label="Carga capas de mapa", style="dashed", color="#00695C") >> osm

if __name__ == "__main__":
    print("Script de despliegue generado con éxito.")
