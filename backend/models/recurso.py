import xml.etree.ElementTree as etree

class Recurso:
    def __init__(self, id_recurso, nombre, abreviatura, metrica, tipo, valor_hora):
        self.id = id_recurso
        self.nombre = nombre
        self.abreviatura = abreviatura
        self.metrica = metrica
        self.tipo = tipo  # Hardware o Software
        self.valor_hora = float(valor_hora)
    
    def to_dict(self):
        return {
            'id': self.id,
            'nombre': self.nombre,
            'abreviatura': self.abreviatura,
            'metrica': self.metrica,
            'tipo': self.tipo,
            'valor_hora': self.valor_hora
        }
    
    def to_xml_element(self, parent):
        recurso = etree.SubElement(parent, 'recurso', id=str(self.id))
        
        nombre = etree.SubElement(recurso, 'nombre')
        nombre.text = self.nombre
        
        abreviatura = etree.SubElement(recurso, 'abreviatura')
        abreviatura.text = self.abreviatura
        
        metrica = etree.SubElement(recurso, 'metrica')
        metrica.text = self.metrica
        
        tipo = etree.SubElement(recurso, 'tipo')
        tipo.text = self.tipo
        
        valor = etree.SubElement(recurso, 'valorXhora')
        valor.text = str(self.valor_hora)
        
        return recurso