"""Pruebas unitarias que demuestran la efectividad de cada patrón GoF (E2–E5).

Verifica de forma aislada:
- E2: Strategy + Adapter + Factory (Open/Closed Principle con nueva variante).
- E3: State (Transiciones válidas e invalidación por construcción).
- E4: Observer, Decorator y Command (Suscripción desacoplada, reintentos y cola offline).
- E5: IA aislada con Decorator (caché) y Chain of Responsibility (Guardrails).
"""
from decimal import Decimal
import pytest

from sismoreporta.canales import (
    FabricaCanales,
    ICanalDespacho,
    ResultadoDespacho,
    RedisCanalAdapter,
    RabbitMQCanalAdapter,
    SmsSatelitalCanalAdapter,
    ConReintentos,
)
from sismoreporta.estados import (
    BorradorState,
    EncoladoState,
    RecibidoState,
    VerificadoState,
    AtendidoState,
    DescartadoState,
)
from sismoreporta.eventos import (
    PublicadorEventos,
    Suscriptor,
    TableroOperacionesMapa,
)
from sismoreporta.comandos import (
    ComandoSincronizarReporte,
    ColaComandosOffline,
)
from sismoreporta.ia import (
    ClienteLLMAdapter,
    ConCacheLLM,
    ClasificadorSeveridadIA,
    SinAlucinacionMagnitud,
    SinPanicoSocial,
    FormatoSeveridadValido,
)
from sismoreporta.externos import (
    RedisBrokerSDK,
    RabbitMQSDK,
    SmsSatelitalGatewaySDK,
    ClienteLLMSimulado,
)
from sismoreporta.servicio import Coordenadas, Reporte, ServicioSincronizacion


# ==============================================================================
# E2: STRATEGY + ADAPTER + FACTORY (Principio Abierto/Cerrado)
# ==============================================================================

class MeshLoraCanalAdapter(ICanalDespacho):
    """Nueva estrategia agregada para contingencia por radio Mesh LoRa."""
    def __init__(self) -> None:
        self.paquetes_enviados = []

    def despachar(self, reporte_id: str, descripcion: str) -> ResultadoDespacho:
        self.paquetes_enviados.append((reporte_id, descripcion))
        return ResultadoDespacho(exitoso=True, mensaje_id=f"lora-{reporte_id[:6]}", canal_usado="MESH_LORA")


def test_open_closed_nuevo_canal_sin_modificar_servicio():
    """Demuestra OCP: se registra una nueva variante de canal sin tocar ServicioSincronizacion."""
    fabrica = FabricaCanales()
    lora_adapter = MeshLoraCanalAdapter()
    
    # Se registra la nueva estrategia en la fábrica
    fabrica.registrar("MESH_LORA", lambda: lora_adapter)
    
    servicio = ServicioSincronizacion(fabrica=fabrica)
    reporte = Reporte(
        descripcion="Colapso de puente peatonal en Socabaya",
        coordenadas=Coordenadas(latitud=Decimal("-16.42"), longitud=Decimal("-71.52"))
    )
    
    estado = servicio.sincronizar_reporte(reporte, canal="MESH_LORA")
    
    assert estado == "RECIBIDO"
    assert len(lora_adapter.paquetes_enviados) == 1
    assert lora_adapter.paquetes_enviados[0][0] == str(reporte.id)


def test_adapter_aisla_llamadas_especificas_del_sdk():
    """Verifica que los adaptadores normalicen las interfaces dispares de los SDKs."""
    redis_sdk = RedisBrokerSDK()
    rabbit_sdk = RabbitMQSDK()
    
    adapter_redis = RedisCanalAdapter(redis_sdk)
    adapter_rabbit = RabbitMQCanalAdapter(rabbit_sdk)
    
    res_redis = adapter_redis.despachar("id-1", "Grieta grave")
    res_rabbit = adapter_rabbit.despachar("id-2", "Derrumbe")
    
    assert res_redis.exitoso and res_redis.canal_usado == "REDIS"
    assert res_rabbit.exitoso and res_rabbit.canal_usado == "RABBITMQ"
    assert len(redis_sdk.cola) == 1
    assert len(rabbit_sdk.mensajes) == 1


# ==============================================================================
# E3: PATRÓN STATE (Ciclo de Vida de la Entidad Reporte)
# ==============================================================================

def test_state_impide_transiciones_invalidas():
    """Verifica que el patrón State impida por diseño transiciones fuera de la máquina de estados."""
    reporte = Reporte(
        descripcion="Techo colapsado en Miraflores",
        coordenadas=Coordenadas(latitud=Decimal("-16.38"), longitud=Decimal("-71.51")),
        estado="ATENDIDO"
    )
    
    # Un reporte ATENDIDO no puede volver a encolarse ni sincronizarse
    with pytest.raises(ValueError, match=r"(?i)atendido"):
        reporte.sincronizar(fecha=None)
    
    with pytest.raises(ValueError, match=r"(?i)atendido"):
        reporte.encolar_offline()
    
    with pytest.raises(ValueError, match=r"(?i)atendido"):
        reporte.descartar("motivo")


def test_state_ciclo_de_vida_completo_y_triaje():
    """Verifica la transición fluida a través de todos los estados válidos."""
    reporte = Reporte(
        descripcion="Casa inhabitable con fisuras estructurales en Paucarpata",
        coordenadas=Coordenadas(latitud=Decimal("-16.41"), longitud=Decimal("-71.50")),
        estado="BORRADOR"
    )
    
    # Borrador -> Encolado
    reporte.encolar_offline()
    assert reporte.estado == "ENCOLADO"
    
    # Encolado -> Recibido
    from datetime import datetime, timezone
    reporte.sincronizar(datetime.now(timezone.utc))
    assert reporte.estado == "RECIBIDO"
    
    # Recibido -> Verificado (con score alto promueve a CATASTROFICA)
    reporte.verificar_triaje(Decimal("0.85"))
    assert reporte.estado == "VERIFICADO"
    assert reporte.severidad == "CATASTROFICA"
    
    # Verificado -> Atendido
    reporte.atender_incidente()
    assert reporte.estado == "ATENDIDO"


# ==============================================================================
# E4: OBSERVER, DECORATOR Y COMMAND
# ==============================================================================

def test_observer_nuevo_suscriptor_sin_tocar_servicio():
    """Demuestra la extensibilidad del Observer agregando un mapa GIS en tiempo real."""
    publicador = PublicadorEventos()
    mapa = TableroOperacionesMapa()
    
    # Registro dinámico del nuevo observador
    publicador.suscribir("reporte_recibido", mapa)
    
    servicio = ServicioSincronizacion(publicador=publicador)
    reporte = Reporte(
        descripcion="Vía bloqueada por deslizamiento en Cayma",
        coordenadas=Coordenadas(latitud=Decimal("-16.37"), longitud=Decimal("-71.55"))
    )
    
    servicio.sincronizar_reporte(reporte)
    
    # El mapa fue notificado sin acoplarse al servicio
    assert len(mapa.puntos_actualizados) == 1
    assert mapa.puntos_actualizados[0]["reporte_id"] == str(reporte.id)


def test_command_cola_offline_encola_y_procesa_en_lote():
    """Demuestra el patrón Command + Cola para almacenar reportes sin señal y enviarlos juntos."""
    servicio = ServicioSincronizacion()
    cola = ColaComandosOffline()
    
    r1 = Reporte(descripcion="Daño 1 en Chiguata", coordenadas=Coordenadas(Decimal("-16.40"), Decimal("-71.40")))
    r2 = Reporte(descripcion="Daño 2 en Tiabaya", coordenadas=Coordenadas(Decimal("-16.42"), Decimal("-71.58")))
    
    # Cliente offline encola comandos
    cmd1 = ComandoSincronizarReporte(servicio, r1, canal="REDIS")
    cmd2 = ComandoSincronizarReporte(servicio, r2, canal="REDIS")
    cola.encolar(cmd1)
    cola.encolar(cmd2)
    
    assert cola.pendientes == 2
    
    # Llega la conectividad: se vacía la cola
    procesados = cola.procesar_lote()
    
    assert procesados == 2
    assert cola.pendientes == 0
    assert r1.estado == "RECIBIDO"
    assert r2.estado == "RECIBIDO"


# ==============================================================================
# E5: IA AISLADA: CACHÉ (DECORATOR) Y GUARDRAILS (CHAIN OF RESPONSIBILITY)
# ==============================================================================

def test_decorator_cache_evita_llamadas_repetidas_al_llm():
    """Verifica que el Decorator ConCacheLLM evite costos y latencia para prompts idénticos."""
    mock_sdk = ClienteLLMSimulado()
    adaptador = ClienteLLMAdapter(mock_sdk)
    cache = ConCacheLLM(adaptador)
    
    prompt = "Evaluar daños: Muro caído en Cerro Colorado"
    r1 = cache.completar(prompt)
    r2 = cache.completar(prompt)
    
    assert r1 == r2
    assert mock_sdk.llamadas == 1  # Solo 1 llamada real al modelo generativo
    assert cache.total_en_cache == 1


def test_guardrail_bloquea_alucinacion_de_magnitud():
    """Verifica que el Guardrail rechace afirmaciones no certificadas sobre grados sismológicos."""
    mock_sdk = ClienteLLMSimulado(respuesta_predefinida="CATASTROFICA: Terremoto grado 8.2 Richter inminente")
    clasificador = ClasificadorSeveridadIA(proveedor=ClienteLLMAdapter(mock_sdk))
    
    with pytest.raises(ValueError, match="magnitud sismológica"):
        clasificador.clasificar("Fisuras en el suelo de Sachaca")


def test_guardrail_bloquea_panico_social():
    """Verifica que el Guardrail censure mensajes que inciten a la desesperación y el caos."""
    mock_sdk = ClienteLLMSimulado(respuesta_predefinida="GRAVE: Colapso en el centro, evacúen Arequipa de inmediato")
    clasificador = ClasificadorSeveridadIA(proveedor=ClienteLLMAdapter(mock_sdk))
    
    with pytest.raises(ValueError, match="afirmación alarmista"):
        clasificador.clasificar("Ruptura de tubería de agua")


def test_guardrail_bloquea_severidad_no_reconocida():
    """Verifica que la salida deba contener una severidad oficial del dominio."""
    mock_sdk = ClienteLLMSimulado(respuesta_predefinida="El reporte parece algo preocupante y peligroso.")
    clasificador = ClasificadorSeveridadIA(proveedor=ClienteLLMAdapter(mock_sdk))
    
    with pytest.raises(ValueError, match="severidad no reconocida"):
        clasificador.clasificar("Vidrios rotos")


def test_guardrail_permite_respuesta_valida():
    """Verifica que respuestas coherentes y conformes pasen exitosamente toda la cadena."""
    mock_sdk = ClienteLLMSimulado(respuesta_predefinida="MODERADA: Fisuras no estructurales en fachada de sillar")
    clasificador = ClasificadorSeveridadIA(proveedor=ClienteLLMAdapter(mock_sdk))
    
    resultado = clasificador.clasificar("Grieta menor en portal de la Plaza de Armas")
    
    assert "MODERADA" in resultado
