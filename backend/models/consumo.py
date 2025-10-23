import xml.etree.ElementTree as etree


class Consumo:
    def __init__(self, nit_cliente, id_instancia, tiempo, fecha_hora):
        self.nit_cliente = nit_cliente
        self.id_instancia = id_instancia
        self.tiempo = float(tiempo)  # En horas
        self.fecha_hora = fecha_hora
        self.facturado = False

    def to_dict(self):
        return {
            "nit_cliente": self.nit_cliente,
            "id_instancia": self.id_instancia,
            "tiempo": self.tiempo,
            "fecha_hora": self.fecha_hora,
            "facturado": self.facturado,
        }

    def to_xml_element(self, parent):
        consumo = etree.SubElement(
            parent,
            "consumo",
            nitCliente=self.nit_cliente,
            idInstancia=str(self.id_instancia),
        )

        tiempo = etree.SubElement(consumo, "tiempo")
        tiempo.text = str(self.tiempo)

        fecha = etree.SubElement(consumo, "fechaHora")
        fecha.text = self.fecha_hora

        facturado = etree.SubElement(consumo, "facturado")
        facturado.text = str(self.facturado)

        return consumo
