"""Pruebas de caracterización para el flujo crítico de SismoReporta AQP.

Red de seguridad (Paso 2 / E1): describen el comportamiento observable del sistema
(éxito, error, límites, reintentos y geocerca) utilizando un fixture parametrizado.
Garantizan que el refactor conserve exactamente el comportamiento preexistente.
"""
import importlib
from decimal import Decimal
import pytest

from sismoreporta.externos import (
    RedisBrokerSDK,
    RabbitMQSDK,
    SmsSatelitalGatewaySDK,
    ClienteLLMSimulado,
)

# Descubrimiento dinámico de implementaciones (antes y refactorizada)
MODULOS_A_PROBAR = ["sismoreporta.antes.servicio"]
try:
    importlib.import_module("sismoreporta.servicio")
    MODULOS_A_PROBAR.append("sismoreporta.servicio")
except (ImportError, ModuleNotFoundError):
    pass


@pytest.fixture(params=MODULOS_A_PROBAR)
def m(request):
    """Fixture parametrizado que inyecta el módulo antes o después."""
    return importlib.import_module(request.param)


def crear_reporte(m, desc: str = "Colapso parcial de muro perimétrico en Yanahuara",
                  lat: str = "-16.3988", lon: str = "-71.5369", estado: str = "BORRADOR"):
    """Crea una entidad Reporte con coordenadas válidas en Arequipa."""
    coords = m.Coordenadas(latitud=Decimal(lat), longitud=Decimal(lon))
    return m.Reporte(descripcion=desc, coordenadas=coords, estado=estado)


def test_sincronizacion_redis_exitosa_cambia_a_recibido(m):
    """Verifica que el despacho por Redis registre el reporte y publique alertas."""
    redis = RedisBrokerSDK()
    s = m.ServicioSincronizacion(redis=redis)
    r = crear_reporte(m)
    
    estado = s.sincronizar_reporte(r, canal="REDIS")
    
    assert estado == "RECIBIDO"
    assert r.estado == "RECIBIDO"
    assert r.fecha_sincronizacion is not None
    assert len(redis.cola) == 1
    assert any(f"coe:alerta:Reporte {r.id}" in e for e in s.eventos)
    assert any(f"auditoria:{r.id}:REDIS" in e for e in s.eventos)


def test_sincronizacion_rabbitmq_exitosa(m):
    """Verifica sincronización a través del broker RabbitMQ."""
    rabbit = RabbitMQSDK()
    s = m.ServicioSincronizacion(rabbit=rabbit)
    r = crear_reporte(m)
    
    estado = s.sincronizar_reporte(r, canal="RABBITMQ")
    
    assert estado == "RECIBIDO"
    assert r.estado == "RECIBIDO"
    assert len(rabbit.mensajes) == 1


def test_sincronizacion_sms_satelital_exitosa(m):
    """Verifica sincronización por canal satelital de contingencia."""
    sms = SmsSatelitalGatewaySDK()
    s = m.ServicioSincronizacion(sms=sms)
    r = crear_reporte(m)
    
    estado = s.sincronizar_reporte(r, canal="SMS_SATELITAL")
    
    assert estado == "RECIBIDO"
    assert r.estado == "RECIBIDO"
    assert len(sms.tramas) == 1


def test_reintenta_ante_dos_timeouts_y_logra_sincronizar(m):
    """Verifica tolerancia a fallas transitorias de red con reintentos."""
    redis = RedisBrokerSDK(fallas=2)
    s = m.ServicioSincronizacion(redis=redis)
    r = crear_reporte(m)
    
    estado = s.sincronizar_reporte(r, canal="REDIS")
    
    assert estado == "RECIBIDO"
    assert redis.llamadas == 3


def test_falla_tras_tres_timeouts_descarta_reporte(m):
    """Verifica que tras agotar los 3 reintentos el reporte se descarte."""
    redis = RedisBrokerSDK(fallas=3)
    s = m.ServicioSincronizacion(redis=redis)
    r = crear_reporte(m)
    
    estado = s.sincronizar_reporte(r, canal="REDIS")
    
    assert estado == "DESCARTADO"
    assert r.estado == "DESCARTADO"
    assert redis.llamadas == 3


def test_reporte_fuera_de_geocerca_se_descarta_sin_despacho(m):
    """Verifica que incidentes fuera de Arequipa (ej. Mollendo/Lima) sean descartados."""
    redis = RedisBrokerSDK()
    s = m.ServicioSincronizacion(redis=redis)
    r = crear_reporte(m, lat="-12.0464", lon="-77.0428")  # Lima
    
    estado = s.sincronizar_reporte(r, canal="REDIS")
    
    assert estado == "DESCARTADO"
    assert r.estado == "DESCARTADO"
    assert redis.llamadas == 0  # No consume ancho de banda del broker


def test_reporte_sin_descripcion_lanza_error(m):
    """Verifica rechazo inmediato si el reporte carece de descripción del daño."""
    s = m.ServicioSincronizacion()
    r = crear_reporte(m, desc="   ")
    
    with pytest.raises(ValueError, match="descripción"):
        s.sincronizar_reporte(r, canal="REDIS")


def test_canal_no_soportado_lanza_error(m):
    """Verifica excepción si se solicita un medio o canal de transporte desconocido."""
    s = m.ServicioSincronizacion()
    r = crear_reporte(m)
    
    with pytest.raises(ValueError, match="no soportado"):
        s.sincronizar_reporte(r, canal="CANAL_DESCONOCIDO")


def test_reporte_en_estado_invalido_atendido_lanza_error(m):
    """Verifica que reportes ya atendidos no puedan volver a sincronizarse."""
    s = m.ServicioSincronizacion()
    r = crear_reporte(m, estado="ATENDIDO")
    
    with pytest.raises(ValueError, match="atendido"):
        s.sincronizar_reporte(r, canal="REDIS")


def test_reporte_en_estado_invalido_descartado_lanza_error(m):
    """Verifica que reportes descartados no puedan volver a sincronizarse."""
    s = m.ServicioSincronizacion()
    r = crear_reporte(m, estado="DESCARTADO")
    
    with pytest.raises(ValueError, match="descartado"):
        s.sincronizar_reporte(r, canal="REDIS")


def test_clasificacion_ia_basica_retorna_texto(m):
    """Verifica invocación del componente de IA para clasificación de severidad."""
    llm = ClienteLLMSimulado()
    s = m.ServicioSincronizacion(llm=llm)
    
    resultado = s.clasificar_severidad_con_ia("Colapso total de viviendas en Cayma", proveedor="MOCK")
    
    assert "CATASTROFICA" in resultado
    assert llm.llamadas == 1


def test_clasificacion_ia_proveedor_no_soportado_lanza_error(m):
    """Verifica excepción si se invoca un proveedor de IA no soportado."""
    s = m.ServicioSincronizacion()
    
    with pytest.raises(ValueError, match="no soportado"):
        s.clasificar_severidad_con_ia("Grietas leves", proveedor="PROVEEDOR_INEXISTENTE")
