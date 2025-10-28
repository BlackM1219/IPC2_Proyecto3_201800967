import xml.etree.ElementTree as etree
from models.recurso import Recurso
from models.categoria import Categoria, Configuracion
from models.cliente import Cliente, Instancia
from models.consumo import Consumo
from services.validaciones import *


class XMLParser:

    @staticmethod
    def parsear_configuracion(xml_string):
        """Parsea el XML de configuración y retorna los objetos creados"""
        root = etree.fromstring(xml_string)

        recursos = []
        categorias = []
        clientes = []

        # Parsear recursos
        lista_recursos = root.find("listaRecursos")
        if lista_recursos is not None:
            for rec in lista_recursos.findall("recurso"):
                id_rec = rec.get("id")
                nombre = rec.find("nombre").text.strip()
                abrev = rec.find("abreviatura").text.strip()
                metrica = rec.find("metrica").text.strip()
                tipo = rec.find("tipo").text.strip()
                valor = rec.find("valorXhora").text.strip()

                if validar_tipo_recurso(tipo):
                    recurso = Recurso(id_rec, nombre, abrev, metrica, tipo, valor)
                    recursos.append(recurso)

        # Parsear categorías
        lista_categorias = root.find("listaCategorias")
        if lista_categorias is not None:
            for cat in lista_categorias.findall("categoria"):
                id_cat = cat.get("id")
                nombre = cat.find("nombre").text.strip()
                desc = cat.find("descripcion").text.strip()
                carga = cat.find("cargaTrabajo").text.strip()

                categoria = Categoria(id_cat, nombre, desc, carga)

                # Parsear configuraciones de la categoría
                lista_configs = cat.find("listaConfiguraciones")
                if lista_configs is not None:
                    for conf in lista_configs.findall("configuracion"):
                        id_conf = conf.get("id")
                        nombre_conf = conf.find("nombre").text.strip()
                        desc_conf = conf.find("descripcion").text.strip()

                        configuracion = Configuracion(id_conf, nombre_conf, desc_conf)

                        # Parsear recursos de la configuración
                        recursos_conf = conf.find("recursosConfiguracion")
                        if recursos_conf is not None:
                            for rec_conf in recursos_conf.findall("recurso"):
                                id_rec = rec_conf.get("id")
                                cantidad = rec_conf.text.strip()
                                configuracion.agregar_recurso(id_rec, cantidad)

                        categoria.agregar_configuracion(configuracion)

                categorias.append(categoria)

        # Parsear clientes
        lista_clientes = root.find("listaClientes")
        if lista_clientes is not None:
            for cli in lista_clientes.findall("cliente"):
                nit = cli.get("nit")
                # ⭐ NORMALIZAR NIT A MAYÚSCULAS
                nit = nit.upper()

                if not validar_nit(nit):
                    continue

                nombre = cli.find("nombre").text.strip()
                usuario = cli.find("usuario").text.strip()
                clave = cli.find("clave").text.strip()
                direccion = cli.find("direccion").text.strip()
                correo = cli.find("correoElectronico").text.strip()

                cliente = Cliente(nit, nombre, usuario, clave, direccion, correo)

                # Parsear instancias del cliente
                lista_instancias = cli.find("listaInstancias")
                if lista_instancias is not None:
                    for inst in lista_instancias.findall("instancia"):
                        id_inst = inst.get("id")
                        id_conf = inst.find("idConfiguracion").text.strip()
                        nombre_inst = inst.find("nombre").text.strip()
                        fecha_inicio_text = inst.find("fechaInicio").text.strip()
                        estado = inst.find("estado").text.strip()

                        fecha_inicio = extraer_fecha(fecha_inicio_text)
                        if not fecha_inicio:
                            continue

                        if not validar_estado_instancia(estado):
                            continue

                        fecha_final = None
                        elem_fecha_final = inst.find("fechaFinal")
                        if elem_fecha_final is not None and elem_fecha_final.text:
                            fecha_final = extraer_fecha(elem_fecha_final.text.strip())

                        instancia = Instancia(
                            id_inst,
                            id_conf,
                            nombre_inst,
                            fecha_inicio,
                            estado,
                            fecha_final,
                        )
                        cliente.agregar_instancia(instancia)

                clientes.append(cliente)

        return {"recursos": recursos, "categorias": categorias, "clientes": clientes}

    @staticmethod
    def parsear_consumos(xml_string):
        """Parsea el XML de consumos y retorna lista de objetos Consumo"""
        root = etree.fromstring(xml_string)
        consumos = []

        for cons in root.findall("consumo"):
            nit = cons.get("nitCliente")
            # ⭐ NORMALIZAR NIT A MAYÚSCULAS
            nit = nit.upper()

            id_inst = cons.get("idInstancia")
            tiempo = cons.find("tiempo").text.strip()
            fecha_hora_text = cons.find("fechaHora").text.strip()

            fecha_hora = extraer_fecha_hora(fecha_hora_text)
            if not fecha_hora:
                continue

            if validar_nit(nit):
                consumo = Consumo(nit, id_inst, tiempo, fecha_hora)
                consumos.append(consumo)

        return consumos
