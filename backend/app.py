from flask import Flask, request, jsonify
from flask_cors import CORS
from services.xml_parser import XMLParser
from services.xml_writer import XMLWriter
from models.recurso import Recurso
from models.categoria import Categoria, Configuracion
from models.cliente import Cliente, Instancia
from models.consumo import Consumo
from models.factura import Factura
from datetime import datetime

app = Flask(__name__)
CORS(app)

# Base de datos en memoria
db_writer = XMLWriter()
datos = db_writer.cargar_datos()

recursos = datos["recursos"]
categorias = datos["categorias"]
clientes = datos["clientes"]
consumos = datos["consumos"]
facturas = datos["facturas"]


def guardar_datos():
    db_writer.guardar_datos(recursos, categorias, clientes, consumos, facturas)


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "OK", "message": "API funcionando"}), 200


@app.route("/inicializar", methods=["POST"])
def inicializar():
    global recursos, categorias, clientes, consumos, facturas
    recursos = {}
    categorias = {}
    clientes = {}
    consumos = []
    facturas = {}
    Factura.contador_facturas = 1
    guardar_datos()
    return jsonify({"mensaje": "Sistema inicializado"}), 200


@app.route("/cargar_configuracion", methods=["POST"])
def cargar_configuracion():
    try:
        xml_data = request.data.decode("utf-8")
        resultado = XMLParser.parsear_configuracion(xml_data)

        nuevos_recursos = 0
        nuevas_categorias = 0
        nuevos_clientes = 0
        nuevas_instancias = 0

        for recurso in resultado["recursos"]:
            if recurso.id not in recursos:
                nuevos_recursos += 1
            recursos[recurso.id] = recurso

        for categoria in resultado["categorias"]:
            if categoria.id not in categorias:
                nuevas_categorias += 1
            categorias[categoria.id] = categoria

        for cliente in resultado["clientes"]:
            if cliente.nit not in clientes:
                nuevos_clientes += 1
            nuevas_instancias += len(cliente.instancias)
            clientes[cliente.nit] = cliente

        guardar_datos()

        return (
            jsonify(
                {
                    "mensaje": "Configuración cargada",
                    "recursos_creados": nuevos_recursos,
                    "categorias_creadas": nuevas_categorias,
                    "clientes_creados": nuevos_clientes,
                    "instancias_creadas": nuevas_instancias,
                }
            ),
            200,
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route("/cargar_consumos", methods=["POST"])
def cargar_consumos():
    try:
        xml_data = request.data.decode("utf-8")
        nuevos_consumos = XMLParser.parsear_consumos(xml_data)

        for consumo in nuevos_consumos:
            consumos.append(consumo)

        guardar_datos()

        return (
            jsonify(
                {
                    "mensaje": "Consumos cargados",
                    "consumos_procesados": len(nuevos_consumos),
                }
            ),
            200,
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route("/recursos", methods=["GET"])
def listar_recursos():
    return jsonify([r.to_dict() for r in recursos.values()]), 200


@app.route("/recursos", methods=["POST"])
def crear_recurso():
    try:
        data = request.json
        recurso = Recurso(
            data["id"],
            data["nombre"],
            data["abreviatura"],
            data["metrica"],
            data["tipo"],
            data["valor_hora"],
        )
        recursos[recurso.id] = recurso
        guardar_datos()
        return jsonify({"mensaje": "Recurso creado"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route("/categorias", methods=["GET"])
def listar_categorias():
    return jsonify([c.to_dict() for c in categorias.values()]), 200


@app.route("/categorias", methods=["POST"])
def crear_categoria():
    try:
        data = request.json
        categoria = Categoria(
            data["id"], data["nombre"], data["descripcion"], data["carga_trabajo"]
        )
        categorias[categoria.id] = categoria
        guardar_datos()
        return jsonify({"mensaje": "Categoría creada"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route("/clientes", methods=["GET"])
def listar_clientes():
    return jsonify([c.to_dict() for c in clientes.values()]), 200


@app.route("/clientes", methods=["POST"])
def crear_cliente():
    try:
        data = request.json
        cliente = Cliente(
            data["nit"],
            data["nombre"],
            data["usuario"],
            data["clave"],
            data["direccion"],
            data["correo"],
        )
        clientes[cliente.nit] = cliente
        guardar_datos()
        return jsonify({"mensaje": "Cliente creado"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route("/instancias/<nit_cliente>", methods=["POST"])
def crear_instancia(nit_cliente):
    try:
        if nit_cliente not in clientes:
            return jsonify({"error": "Cliente no encontrado"}), 404

        data = request.json
        instancia = Instancia(
            data["id"],
            data["id_configuracion"],
            data["nombre"],
            data["fecha_inicio"],
            data.get("estado", "Vigente"),
            data.get("fecha_final"),
        )

        clientes[nit_cliente].agregar_instancia(instancia)
        guardar_datos()
        return jsonify({"mensaje": "Instancia creada"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route("/facturar", methods=["POST"])
def facturar():
    try:
        data = request.json
        fecha_final = data.get("fecha_final")

        consumos_por_cliente = {}
        for consumo in consumos:
            if not consumo.facturado:
                if consumo.nit_cliente not in consumos_por_cliente:
                    consumos_por_cliente[consumo.nit_cliente] = []
                consumos_por_cliente[consumo.nit_cliente].append(consumo)

        facturas_creadas = []

        for nit, consumos_cliente in consumos_por_cliente.items():
            monto_total = 0
            detalles = []

            for consumo in consumos_cliente:
                cliente = clientes.get(nit)
                if not cliente:
                    continue

                instancia = None
                for inst in cliente.instancias:
                    if inst.id == consumo.id_instancia:
                        instancia = inst
                        break

                if not instancia:
                    continue

                configuracion = None
                for cat in categorias.values():
                    for conf in cat.configuraciones:
                        if conf.id == instancia.id_configuracion:
                            configuracion = conf
                            break

                if not configuracion:
                    continue

                costo_consumo = 0
                for id_rec, cantidad in configuracion.recursos.items():
                    recurso = recursos.get(id_rec)
                    if recurso:
                        costo = float(cantidad) * recurso.valor_hora * consumo.tiempo
                        costo_consumo += costo

                monto_total += costo_consumo
                consumo.facturado = True

                detalles.append(
                    {
                        "id_instancia": consumo.id_instancia,
                        "tiempo": consumo.tiempo,
                        "costo": costo_consumo,
                    }
                )

            if monto_total > 0:
                factura = Factura(nit, fecha_final, monto_total)
                factura.detalles = detalles
                facturas[factura.numero] = factura
                facturas_creadas.append(factura.to_dict())

        guardar_datos()

        return (
            jsonify(
                {
                    "mensaje": "Facturación completada",
                    "facturas_creadas": len(facturas_creadas),
                    "facturas": facturas_creadas,
                }
            ),
            200,
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route("/facturas", methods=["GET"])
def listar_facturas():
    return jsonify([f.to_dict() for f in facturas.values()]), 200


@app.route("/facturas/<int:numero>", methods=["GET"])
def obtener_factura(numero):
    if numero in facturas:
        return jsonify(facturas[numero].to_dict()), 200
    return jsonify({"error": "Factura no encontrada"}), 404


if __name__ == "__main__":
    print("🚀 API iniciada en http://localhost:5000")
    app.run(debug=True, port=5000)
