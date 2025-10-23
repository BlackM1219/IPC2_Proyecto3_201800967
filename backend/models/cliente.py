import xml.etree.ElementTree as etree


class Cliente:
    def __init__(self, nit, nombre, usuario, clave, direccion, correo):
        self.nit = nit
        self.nombre = nombre
        self.usuario = usuario
        self.clave = clave
        self.direccion = direccion
        self.correo = correo
        self.instancias = []

    def agregar_instancia(self, instancia):
        self.instancias.append(instancia)

    def to_dict(self):
        return {
            "nit": self.nit,
            "nombre": self.nombre,
            "usuario": self.usuario,
            "clave": self.clave,
            "direccion": self.direccion,
            "correo": self.correo,
            "instancias": [i.to_dict() for i in self.instancias],
        }

    def to_xml_element(self, parent):
        cliente = etree.SubElement(parent, "cliente", nit=self.nit)

        nombre = etree.SubElement(cliente, "nombre")
        nombre.text = self.nombre

        usuario = etree.SubElement(cliente, "usuario")
        usuario.text = self.usuario

        clave = etree.SubElement(cliente, "clave")
        clave.text = self.clave

        direccion = etree.SubElement(cliente, "direccion")
        direccion.text = self.direccion

        correo = etree.SubElement(cliente, "correoElectronico")
        correo.text = self.correo

        lista_inst = etree.SubElement(cliente, "listaInstancias")
        for inst in self.instancias:
            inst.to_xml_element(lista_inst)

        return cliente


class Instancia:
    def __init__(
        self,
        id_instancia,
        id_configuracion,
        nombre,
        fecha_inicio,
        estado,
        fecha_final=None,
    ):
        self.id = id_instancia
        self.id_configuracion = id_configuracion
        self.nombre = nombre
        self.fecha_inicio = fecha_inicio
        self.estado = estado  # Vigente o Cancelada
        self.fecha_final = fecha_final
        self.consumos = []

    def agregar_consumo(self, consumo):
        self.consumos.append(consumo)

    def to_dict(self):
        return {
            "id": self.id,
            "id_configuracion": self.id_configuracion,
            "nombre": self.nombre,
            "fecha_inicio": self.fecha_inicio,
            "estado": self.estado,
            "fecha_final": self.fecha_final,
            "consumos": [c.to_dict() for c in self.consumos],
        }

    def to_xml_element(self, parent):
        instancia = etree.SubElement(parent, "instancia", id=str(self.id))

        id_config = etree.SubElement(instancia, "idConfiguracion")
        id_config.text = str(self.id_configuracion)

        nombre = etree.SubElement(instancia, "nombre")
        nombre.text = self.nombre

        fecha_ini = etree.SubElement(instancia, "fechaInicio")
        fecha_ini.text = self.fecha_inicio

        estado = etree.SubElement(instancia, "estado")
        estado.text = self.estado

        if self.fecha_final:
            fecha_fin = etree.SubElement(instancia, "fechaFinal")
            fecha_fin.text = self.fecha_final

        return instancia
