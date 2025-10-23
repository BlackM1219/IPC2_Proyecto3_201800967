import xml.etree.ElementTree as etree
import os


class XMLWriter:
    def __init__(self, archivo="database/datos.xml"):
        self.archivo = archivo
        self.asegurar_directorio()

    def asegurar_directorio(self):
        """Asegura que exista el directorio de la base de datos"""
        directorio = os.path.dirname(self.archivo)
        if directorio and not os.path.exists(directorio):
            os.makedirs(directorio)

    def _indent(self, elem, level=0):
        """Añade indentación al XML para que sea legible"""
        i = "\n" + level * "  "
        if len(elem):
            if not elem.text or not elem.text.strip():
                elem.text = i + "  "
            if not elem.tail or not elem.tail.strip():
                elem.tail = i
            for child in elem:
                self._indent(child, level + 1)
            if not child.tail or not child.tail.strip():
                child.tail = i
        else:
            if level and (not elem.tail or not elem.tail.strip()):
                elem.tail = i

    def guardar_datos(self, recursos, categorias, clientes, consumos, facturas):
        """Guarda todos los datos en el archivo XML"""
        root = etree.Element("baseDatos")

        # Guardar recursos
        lista_recursos = etree.SubElement(root, "listaRecursos")
        for recurso in recursos.values():
            recurso.to_xml_element(lista_recursos)

        # Guardar categorías
        lista_categorias = etree.SubElement(root, "listaCategorias")
        for categoria in categorias.values():
            categoria.to_xml_element(lista_categorias)

        # Guardar clientes
        lista_clientes = etree.SubElement(root, "listaClientes")
        for cliente in clientes.values():
            cliente.to_xml_element(lista_clientes)

        # Guardar consumos
        lista_consumos = etree.SubElement(root, "listaConsumos")
        for consumo in consumos:
            consumo.to_xml_element(lista_consumos)

        # Guardar facturas
        lista_facturas = etree.SubElement(root, "listaFacturas")
        for factura in facturas.values():
            factura.to_xml_element(lista_facturas)

        # Formatear XML
        self._indent(root)

        # Escribir archivo
        tree = etree.ElementTree(root)
        tree.write(self.archivo, encoding="UTF-8", xml_declaration=True)

    def cargar_datos(self):
        """Carga los datos desde el archivo XML"""
        if not os.path.exists(self.archivo):
            return {
                "recursos": {},
                "categorias": {},
                "clientes": {},
                "consumos": [],
                "facturas": {},
            }

        try:
            tree = etree.parse(self.archivo)
            root = tree.getroot()

            from models.recurso import Recurso
            from models.categoria import Categoria, Configuracion
            from models.cliente import Cliente, Instancia
            from models.consumo import Consumo
            from models.factura import Factura

            recursos = {}
            categorias = {}
            clientes = {}
            consumos = []
            facturas = {}

            # Cargar recursos
            lista_recursos = root.find("listaRecursos")
            if lista_recursos is not None:
                for rec in lista_recursos.findall("recurso"):
                    id_rec = rec.get("id")
                    nombre = rec.find("nombre").text
                    abrev = rec.find("abreviatura").text
                    metrica = rec.find("metrica").text
                    tipo = rec.find("tipo").text
                    valor = rec.find("valorXhora").text

                    recurso = Recurso(id_rec, nombre, abrev, metrica, tipo, valor)
                    recursos[id_rec] = recurso

            # Cargar categorías
            lista_categorias = root.find("listaCategorias")
            if lista_categorias is not None:
                for cat in lista_categorias.findall("categoria"):
                    id_cat = cat.get("id")
                    nombre = cat.find("nombre").text
                    desc = cat.find("descripcion").text
                    carga = cat.find("cargaTrabajo").text

                    categoria = Categoria(id_cat, nombre, desc, carga)

                    lista_configs = cat.find("listaConfiguraciones")
                    if lista_configs is not None:
                        for conf in lista_configs.findall("configuracion"):
                            id_conf = conf.get("id")
                            nombre_conf = conf.find("nombre").text
                            desc_conf = conf.find("descripcion").text

                            configuracion = Configuracion(
                                id_conf, nombre_conf, desc_conf
                            )

                            recursos_conf = conf.find("recursosConfiguracion")
                            if recursos_conf is not None:
                                for rec_conf in recursos_conf.findall("recurso"):
                                    id_rec = rec_conf.get("id")
                                    cantidad = rec_conf.text
                                    configuracion.agregar_recurso(id_rec, cantidad)

                            categoria.agregar_configuracion(configuracion)

                    categorias[id_cat] = categoria

            # Cargar clientes
            lista_clientes = root.find("listaClientes")
            if lista_clientes is not None:
                for cli in lista_clientes.findall("cliente"):
                    nit = cli.get("nit")
                    nombre = cli.find("nombre").text
                    usuario = cli.find("usuario").text
                    clave = cli.find("clave").text
                    direccion = cli.find("direccion").text
                    correo = cli.find("correoElectronico").text

                    cliente = Cliente(nit, nombre, usuario, clave, direccion, correo)

                    lista_instancias = cli.find("listaInstancias")
                    if lista_instancias is not None:
                        for inst in lista_instancias.findall("instancia"):
                            id_inst = inst.get("id")
                            id_conf = inst.find("idConfiguracion").text
                            nombre_inst = inst.find("nombre").text
                            fecha_inicio = inst.find("fechaInicio").text
                            estado = inst.find("estado").text

                            fecha_final = None
                            elem_final = inst.find("fechaFinal")
                            if elem_final is not None:
                                fecha_final = elem_final.text

                            instancia = Instancia(
                                id_inst,
                                id_conf,
                                nombre_inst,
                                fecha_inicio,
                                estado,
                                fecha_final,
                            )
                            cliente.agregar_instancia(instancia)

                    clientes[nit] = cliente

            # Cargar consumos
            lista_consumos = root.find("listaConsumos")
            if lista_consumos is not None:
                for cons in lista_consumos.findall("consumo"):
                    nit = cons.get("nitCliente")
                    id_inst = cons.get("idInstancia")
                    tiempo = cons.find("tiempo").text
                    fecha_hora = cons.find("fechaHora").text

                    consumo = Consumo(nit, id_inst, tiempo, fecha_hora)

                    facturado_elem = cons.find("facturado")
                    if facturado_elem is not None:
                        consumo.facturado = facturado_elem.text == "True"

                    consumos.append(consumo)

            # Cargar facturas
            lista_facturas = root.find("listaFacturas")
            if lista_facturas is not None:
                for fact in lista_facturas.findall("factura"):
                    numero = int(fact.get("numero"))
                    nit = fact.find("nitCliente").text
                    fecha = fact.find("fecha").text
                    monto = float(fact.find("montoTotal").text)

                    factura = Factura.__new__(Factura)
                    factura.numero = numero
                    factura.nit_cliente = nit
                    factura.fecha_factura = fecha
                    factura.monto_total = monto
                    factura.detalles = []

                    detalles_elem = fact.find("detalles")
                    if detalles_elem is not None:
                        for det in detalles_elem.findall("detalle"):
                            detalle = {}
                            for child in det:
                                detalle[child.tag] = child.text
                            factura.detalles.append(detalle)

                    facturas[numero] = factura
                    if numero >= Factura.contador_facturas:
                        Factura.contador_facturas = numero + 1

            return {
                "recursos": recursos,
                "categorias": categorias,
                "clientes": clientes,
                "consumos": consumos,
                "facturas": facturas,
            }

        except Exception as e:
            print(f"Error cargando datos: {e}")
            return {
                "recursos": {},
                "categorias": {},
                "clientes": {},
                "consumos": [],
                "facturas": {},
            }
