import re
from datetime import datetime


def validar_nit(nit):
    """Valida formato de NIT: números-dígito (0-9 o K)"""
    patron = r"^\d+-[0-9Kk]$"
    return re.match(patron, nit) is not None


def normalizar_nit(nit):
    """Normaliza el NIT a mayúsculas"""
    return nit.upper() if nit else nit


def extraer_fecha(texto):
    """Extrae la primera fecha válida en formato dd/mm/yyyy"""
    patron = r"(\d{2})/(\d{2})/(\d{4})"
    match = re.search(patron, texto)

    if match:
        dia, mes, anio = match.groups()
        try:
            fecha = datetime(int(anio), int(mes), int(dia))
            return f"{dia}/{mes}/{anio}"
        except ValueError:
            return None
    return None


def extraer_fecha_hora(texto):
    """Extrae la primera fecha y hora válida en formato dd/mm/yyyy hh:mi"""
    patron = r"(\d{2})/(\d{2})/(\d{4})\s+(\d{2}):(\d{2})"
    match = re.search(patron, texto)

    if match:
        dia, mes, anio, hora, minuto = match.groups()
        try:
            fecha = datetime(int(anio), int(mes), int(dia), int(hora), int(minuto))
            return f"{dia}/{mes}/{anio} {hora}:{minuto}"
        except ValueError:
            return None
    return None


def validar_tipo_recurso(tipo):
    """Valida que el tipo sea Hardware o Software (case insensitive)"""
    return tipo.lower() in ["hardware", "software"]


def validar_estado_instancia(estado):
    """Valida que el estado sea Vigente o Cancelada (case insensitive)"""
    return estado.lower() in ["vigente", "cancelada"]
