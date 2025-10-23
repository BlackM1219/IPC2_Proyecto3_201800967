import xml.etree.ElementTree as etree


class Categoria:
    def __init__(self, id_categoria, nombre, descripcion, carga_trabajo):
        self.id = id_categoria
        self.nombre = nombre
        self.descripcion = descripcion
        self.carga_trabajo = carga_trabajo
        self.configuraciones = []

    def agregar_configuracion(self, configuracion):
        self.configuraciones.append(configuracion)

    def to_dict(self):
        return {
            "id": self.id,
            "nombre": self.nombre,
            "descripcion": self.descripcion,
            "carga_trabajo": self.carga_trabajo,
            "configuraciones": [c.to_dict() for c in self.configuraciones],
        }

    def to_xml_element(self, parent):
        categoria = etree.SubElement(parent, "categoria", id=str(self.id))

        nombre = etree.SubElement(categoria, "nombre")
        nombre.text = self.nombre

        descripcion = etree.SubElement(categoria, "descripcion")
        descripcion.text = self.descripcion

        carga = etree.SubElement(categoria, "cargaTrabajo")
        carga.text = self.carga_trabajo

        lista_configs = etree.SubElement(categoria, "listaConfiguraciones")
        for config in self.configuraciones:
            config.to_xml_element(lista_configs)

        return categoria


class Configuracion:
    def __init__(self, id_config, nombre, descripcion):
        self.id = id_config
        self.nombre = nombre
        self.descripcion = descripcion
        self.recursos = {}  # {id_recurso: cantidad}

    def agregar_recurso(self, id_recurso, cantidad):
        self.recursos[id_recurso] = float(cantidad)

    def to_dict(self):
        return {
            "id": self.id,
            "nombre": self.nombre,
            "descripcion": self.descripcion,
            "recursos": self.recursos,
        }

    def to_xml_element(self, parent):
        config = etree.SubElement(parent, "configuracion", id=str(self.id))

        nombre = etree.SubElement(config, "nombre")
        nombre.text = self.nombre

        descripcion = etree.SubElement(config, "descripcion")
        descripcion.text = self.descripcion

        recursos_config = etree.SubElement(config, "recursosConfiguracion")
        for id_rec, cant in self.recursos.items():
            recurso = etree.SubElement(recursos_config, "recurso", id=str(id_rec))
            recurso.text = str(cant)

        return config
