import xml.etree.ElementTree as etree


class Factura:
    contador_facturas = 1

    def __init__(self, nit_cliente, fecha_factura, monto_total):
        self.numero = Factura.contador_facturas
        Factura.contador_facturas += 1
        self.nit_cliente = nit_cliente
        self.fecha_factura = fecha_factura
        self.monto_total = monto_total
        self.detalles = []  # Lista de consumos facturados

    def agregar_detalle(self, detalle):
        self.detalles.append(detalle)

    def to_dict(self):
        return {
            "numero": self.numero,
            "nit_cliente": self.nit_cliente,
            "fecha_factura": self.fecha_factura,
            "monto_total": self.monto_total,
            "detalles": self.detalles,
        }

    def to_xml_element(self, parent):
        factura = etree.SubElement(parent, "factura", numero=str(self.numero))

        nit = etree.SubElement(factura, "nitCliente")
        nit.text = self.nit_cliente

        fecha = etree.SubElement(factura, "fecha")
        fecha.text = self.fecha_factura

        monto = etree.SubElement(factura, "montoTotal")
        monto.text = str(self.monto_total)

        detalles_elem = etree.SubElement(factura, "detalles")
        for detalle in self.detalles:
            det = etree.SubElement(detalles_elem, "detalle")
            for key, value in detalle.items():
                elem = etree.SubElement(det, key)
                elem.text = str(value)

        return factura
