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
    """Guarda los datos en el archivo XML"""
    db_writer.guardar_datos(recursos, categorias, clientes, consumos, facturas)


# =============== ENDPOINTS GENERALES ===============


@app.route("/health", methods=["GET"])
def health():
    """Verificar estado de la API"""
    return (
        jsonify(
            {
                "status": "OK",
                "message": "API funcionando correctamente",
                "recursos": len(recursos),
                "categorias": len(categorias),
                "clientes": len(clientes),
                "consumos": len(consumos),
                "facturas": len(facturas),
            }
        ),
        200,
    )


@app.route("/inicializar", methods=["POST"])
def inicializar():
    """Elimina todos los datos del sistema"""
    global recursos, categorias, clientes, consumos, facturas
    recursos = {}
    categorias = {}
    clientes = {}
    consumos = []
    facturas = {}
    Factura.contador_facturas = 1
    guardar_datos()
    return jsonify({"mensaje": "Sistema inicializado correctamente"}), 200


# =============== CARGA DE ARCHIVOS XML ===============


@app.route("/cargar_configuracion", methods=["POST"])
def cargar_configuracion():
    """Procesa el XML de configuración"""
    try:
        xml_data = request.data.decode("utf-8")
        resultado = XMLParser.parsear_configuracion(xml_data)

        nuevos_recursos = 0
        nuevas_categorias = 0
        nuevos_clientes = 0
        nuevas_instancias = 0

        # Agregar recursos
        for recurso in resultado["recursos"]:
            if recurso.id not in recursos:
                nuevos_recursos += 1
            recursos[recurso.id] = recurso

        # Agregar categorías
        for categoria in resultado["categorias"]:
            if categoria.id not in categorias:
                nuevas_categorias += 1
            categorias[categoria.id] = categoria

        # Agregar clientes
        for cliente in resultado["clientes"]:
            if cliente.nit not in clientes:
                nuevos_clientes += 1
            nuevas_instancias += len(cliente.instancias)
            clientes[cliente.nit] = cliente

        guardar_datos()

        return (
            jsonify(
                {
                    "mensaje": "Configuración cargada exitosamente",
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
    """Procesa el XML de consumos"""
    try:
        xml_data = request.data.decode("utf-8")
        nuevos_consumos = XMLParser.parsear_consumos(xml_data)

        procesados = 0
        for consumo in nuevos_consumos:
            consumos.append(consumo)
            procesados += 1

        guardar_datos()

        return (
            jsonify(
                {
                    "mensaje": "Consumos cargados exitosamente",
                    "consumos_procesados": procesados,
                }
            ),
            200,
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 400


# =============== RECURSOS ===============


@app.route("/recursos", methods=["GET"])
def listar_recursos():
    """Lista todos los recursos"""
    return jsonify([r.to_dict() for r in recursos.values()]), 200


@app.route("/recursos/<id_recurso>", methods=["GET"])
def obtener_recurso(id_recurso):
    """Obtiene un recurso específico"""
    if id_recurso in recursos:
        return jsonify(recursos[id_recurso].to_dict()), 200
    return jsonify({"error": "Recurso no encontrado"}), 404


@app.route("/recursos", methods=["POST"])
def crear_recurso():
    """Crea un nuevo recurso"""
    try:
        data = request.json

        # Validar datos requeridos
        if not all(
            k in data
            for k in ["id", "nombre", "abreviatura", "metrica", "tipo", "valor_hora"]
        ):
            return jsonify({"error": "Faltan campos requeridos"}), 400

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
        return jsonify({"mensaje": "Recurso creado", "recurso": recurso.to_dict()}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route("/recursos/<id_recurso>", methods=["PUT"])
def actualizar_recurso(id_recurso):
    """Actualiza un recurso existente"""
    try:
        if id_recurso not in recursos:
            return jsonify({"error": "Recurso no encontrado"}), 404

        data = request.json
        recurso = recursos[id_recurso]

        if "nombre" in data:
            recurso.nombre = data["nombre"]
        if "abreviatura" in data:
            recurso.abreviatura = data["abreviatura"]
        if "metrica" in data:
            recurso.metrica = data["metrica"]
        if "tipo" in data:
            recurso.tipo = data["tipo"]
        if "valor_hora" in data:
            recurso.valor_hora = float(data["valor_hora"])

        guardar_datos()
        return (
            jsonify({"mensaje": "Recurso actualizado", "recurso": recurso.to_dict()}),
            200,
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route("/recursos/<id_recurso>", methods=["DELETE"])
def eliminar_recurso(id_recurso):
    """Elimina un recurso"""
    try:
        if id_recurso in recursos:
            del recursos[id_recurso]
            guardar_datos()
            return jsonify({"mensaje": "Recurso eliminado"}), 200
        return jsonify({"error": "Recurso no encontrado"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 400


# =============== CATEGORÍAS ===============


@app.route("/categorias", methods=["GET"])
def listar_categorias():
    """Lista todas las categorías"""
    return jsonify([c.to_dict() for c in categorias.values()]), 200


@app.route("/categorias/<id_categoria>", methods=["GET"])
def obtener_categoria(id_categoria):
    """Obtiene una categoría específica"""
    if id_categoria in categorias:
        return jsonify(categorias[id_categoria].to_dict()), 200
    return jsonify({"error": "Categoría no encontrada"}), 404


@app.route("/categorias", methods=["POST"])
def crear_categoria():
    """Crea una nueva categoría"""
    try:
        data = request.json

        if not all(k in data for k in ["id", "nombre", "descripcion", "carga_trabajo"]):
            return jsonify({"error": "Faltan campos requeridos"}), 400

        categoria = Categoria(
            data["id"], data["nombre"], data["descripcion"], data["carga_trabajo"]
        )
        categorias[categoria.id] = categoria
        guardar_datos()
        return (
            jsonify({"mensaje": "Categoría creada", "categoria": categoria.to_dict()}),
            201,
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route("/categorias/<id_categoria>", methods=["DELETE"])
def eliminar_categoria(id_categoria):
    """Elimina una categoría"""
    try:
        if id_categoria in categorias:
            del categorias[id_categoria]
            guardar_datos()
            return jsonify({"mensaje": "Categoría eliminada"}), 200
        return jsonify({"error": "Categoría no encontrada"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 400


# =============== CONFIGURACIONES ===============


@app.route("/configuraciones/<id_categoria>", methods=["POST"])
def crear_configuracion(id_categoria):
    """Crea una nueva configuración en una categoría"""
    try:
        if id_categoria not in categorias:
            return jsonify({"error": "Categoría no encontrada"}), 404

        data = request.json

        if not all(k in data for k in ["id", "nombre", "descripcion"]):
            return jsonify({"error": "Faltan campos requeridos"}), 400

        config = Configuracion(data["id"], data["nombre"], data["descripcion"])

        # Agregar recursos a la configuración
        if "recursos" in data:
            for id_rec, cant in data["recursos"].items():
                if id_rec in recursos:
                    config.agregar_recurso(id_rec, cant)

        categorias[id_categoria].agregar_configuracion(config)
        guardar_datos()
        return (
            jsonify(
                {"mensaje": "Configuración creada", "configuracion": config.to_dict()}
            ),
            201,
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 400


# =============== CLIENTES ===============


@app.route("/clientes", methods=["GET"])
def listar_clientes():
    """Lista todos los clientes"""
    return jsonify([c.to_dict() for c in clientes.values()]), 200


@app.route("/clientes/<nit>", methods=["GET"])
def obtener_cliente(nit):
    """Obtiene un cliente específico"""
    # Normalizar NIT para búsqueda
    nit = nit.upper()
    if nit in clientes:
        return jsonify(clientes[nit].to_dict()), 200
    return jsonify({"error": "Cliente no encontrado"}), 404


@app.route("/clientes", methods=["POST"])
def crear_cliente():
    """Crea un nuevo cliente"""
    try:
        data = request.json

        if not all(
            k in data
            for k in ["nit", "nombre", "usuario", "clave", "direccion", "correo"]
        ):
            return jsonify({"error": "Faltan campos requeridos"}), 400

        # Normalizar NIT
        nit = data["nit"].upper()

        cliente = Cliente(
            nit,
            data["nombre"],
            data["usuario"],
            data["clave"],
            data["direccion"],
            data["correo"],
        )
        clientes[cliente.nit] = cliente
        guardar_datos()
        return jsonify({"mensaje": "Cliente creado", "cliente": cliente.to_dict()}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route("/clientes/<nit>", methods=["PUT"])
def actualizar_cliente(nit):
    """Actualiza un cliente existente"""
    try:
        # Normalizar NIT
        nit = nit.upper()

        if nit not in clientes:
            return jsonify({"error": "Cliente no encontrado"}), 404

        data = request.json
        cliente = clientes[nit]

        if "nombre" in data:
            cliente.nombre = data["nombre"]
        if "usuario" in data:
            cliente.usuario = data["usuario"]
        if "clave" in data:
            cliente.clave = data["clave"]
        if "direccion" in data:
            cliente.direccion = data["direccion"]
        if "correo" in data:
            cliente.correo = data["correo"]

        guardar_datos()
        return (
            jsonify({"mensaje": "Cliente actualizado", "cliente": cliente.to_dict()}),
            200,
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route("/clientes/<nit>", methods=["DELETE"])
def eliminar_cliente(nit):
    """Elimina un cliente"""
    try:
        # Normalizar NIT
        nit = nit.upper()

        if nit in clientes:
            del clientes[nit]
            guardar_datos()
            return jsonify({"mensaje": "Cliente eliminado"}), 200
        return jsonify({"error": "Cliente no encontrado"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 400


# =============== INSTANCIAS ===============


@app.route("/instancias/<nit_cliente>", methods=["GET"])
def listar_instancias_cliente(nit_cliente):
    """Lista todas las instancias de un cliente"""
    # Normalizar NIT
    nit_cliente = nit_cliente.upper()

    if nit_cliente in clientes:
        return jsonify([i.to_dict() for i in clientes[nit_cliente].instancias]), 200
    return jsonify({"error": "Cliente no encontrado"}), 404


@app.route("/instancias/<nit_cliente>", methods=["POST"])
def crear_instancia(nit_cliente):
    """Crea una nueva instancia para un cliente"""
    try:
        # Normalizar NIT
        nit_cliente = nit_cliente.upper()

        if nit_cliente not in clientes:
            return jsonify({"error": "Cliente no encontrado"}), 404

        data = request.json

        if not all(
            k in data for k in ["id", "id_configuracion", "nombre", "fecha_inicio"]
        ):
            return jsonify({"error": "Faltan campos requeridos"}), 400

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
        return (
            jsonify({"mensaje": "Instancia creada", "instancia": instancia.to_dict()}),
            201,
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route("/instancias/<nit_cliente>/<id_instancia>/cancelar", methods=["PUT"])
def cancelar_instancia(nit_cliente, id_instancia):
    """Cancela una instancia"""
    try:
        # Normalizar NIT
        nit_cliente = nit_cliente.upper()

        if nit_cliente not in clientes:
            return jsonify({"error": "Cliente no encontrado"}), 404

        cliente = clientes[nit_cliente]
        for instancia in cliente.instancias:
            if instancia.id == id_instancia:
                instancia.estado = "Cancelada"
                data = request.json
                instancia.fecha_final = data.get(
                    "fecha_final", datetime.now().strftime("%d/%m/%Y")
                )
                guardar_datos()
                return (
                    jsonify(
                        {
                            "mensaje": "Instancia cancelada",
                            "instancia": instancia.to_dict(),
                        }
                    ),
                    200,
                )

        return jsonify({"error": "Instancia no encontrada"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 400


# =============== CONSUMOS ===============


@app.route("/consumos", methods=["GET"])
def listar_consumos():
    """Lista todos los consumos"""
    return jsonify([c.to_dict() for c in consumos]), 200


@app.route("/consumos/cliente/<nit_cliente>", methods=["GET"])
def listar_consumos_cliente(nit_cliente):
    """Lista consumos de un cliente específico"""
    # Normalizar NIT
    nit_cliente = nit_cliente.upper()

    consumos_cliente = [
        c.to_dict() for c in consumos if c.nit_cliente.upper() == nit_cliente
    ]
    return jsonify(consumos_cliente), 200


@app.route("/consumos/no_facturados/<nit_cliente>", methods=["GET"])
def consumos_no_facturados(nit_cliente):
    """Lista consumos no facturados de un cliente"""
    # Normalizar NIT
    nit_cliente = nit_cliente.upper()

    consumos_cliente = [
        c.to_dict()
        for c in consumos
        if c.nit_cliente.upper() == nit_cliente and not c.facturado
    ]
    return jsonify(consumos_cliente), 200


@app.route("/consumos", methods=["POST"])
def crear_consumo():
    """Crea un nuevo consumo"""
    try:
        data = request.json

        if not all(
            k in data for k in ["nit_cliente", "id_instancia", "tiempo", "fecha_hora"]
        ):
            return jsonify({"error": "Faltan campos requeridos"}), 400

        # Normalizar NIT
        nit_cliente = data["nit_cliente"].upper()

        consumo = Consumo(
            nit_cliente,
            data["id_instancia"],
            data["tiempo"],
            data["fecha_hora"],
        )
        consumos.append(consumo)
        guardar_datos()
        return (
            jsonify({"mensaje": "Consumo registrado", "consumo": consumo.to_dict()}),
            201,
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 400


# =============== FACTURACIÓN ===============


@app.route("/facturar", methods=["POST"])
def facturar():
    """Genera facturas para consumos no facturados"""
    try:
        data = request.json
        fecha_inicio = data.get("fecha_inicio")
        fecha_final = data.get("fecha_final")

        print(f"\n{'='*60}")
        print(f"🔍 Iniciando facturación: {fecha_inicio} a {fecha_final}")
        print(f"{'='*60}")
        print(f"📊 Total consumos en sistema: {len(consumos)}")
        print(f"👥 Total clientes en sistema: {len(clientes)}")
        print(f"🔧 Total recursos en sistema: {len(recursos)}")
        print(f"📁 Total categorías en sistema: {len(categorias)}")

        # Agrupar consumos por cliente (con NIT normalizado)
        consumos_por_cliente = {}
        consumos_procesados = 0

        for consumo in consumos:
            if not consumo.facturado:
                # Normalizar NIT del consumo
                nit_normalizado = consumo.nit_cliente.upper()

                if nit_normalizado not in consumos_por_cliente:
                    consumos_por_cliente[nit_normalizado] = []
                consumos_por_cliente[nit_normalizado].append(consumo)
                consumos_procesados += 1

        print(f"✅ Consumos no facturados encontrados: {consumos_procesados}")
        print(f"👤 Clientes con consumos pendientes: {len(consumos_por_cliente)}")
        print(f"   NITs de clientes con consumos: {list(consumos_por_cliente.keys())}")
        print(f"   NITs de clientes en sistema: {list(clientes.keys())}")

        if consumos_procesados == 0:
            print("⚠️ No hay consumos pendientes de facturar")
            return (
                jsonify(
                    {
                        "mensaje": "No hay consumos pendientes de facturar",
                        "facturas_creadas": 0,
                        "facturas": [],
                    }
                ),
                200,
            )

        facturas_creadas = []

        # Crear factura por cada cliente
        for nit, consumos_cliente in consumos_por_cliente.items():
            print(f"\n{'='*60}")
            print(f"💼 Procesando cliente NIT: {nit}")
            print(f"   Consumos del cliente: {len(consumos_cliente)}")

            # Buscar cliente (con NIT normalizado)
            cliente = None
            for nit_cliente in clientes.keys():
                if nit_cliente.upper() == nit:
                    cliente = clientes[nit_cliente]
                    break

            if not cliente:
                print(f"   ❌ Cliente no encontrado para NIT: {nit}")
                print(f"   NITs disponibles: {list(clientes.keys())}")
                continue

            print(f"   ✓ Cliente encontrado: {cliente.nombre}")
            print(f"   Instancias del cliente: {len(cliente.instancias)}")

            monto_total = 0
            detalles = []
            consumos_facturados = 0

            for idx, consumo in enumerate(consumos_cliente, 1):
                print(f"\n   📝 [{idx}/{len(consumos_cliente)}] Procesando consumo:")
                print(f"      • ID Instancia: {consumo.id_instancia}")
                print(f"      • Tiempo: {consumo.tiempo} horas")
                print(f"      • Fecha: {consumo.fecha_hora}")

                # Buscar instancia
                instancia = None
                for inst in cliente.instancias:
                    if inst.id == consumo.id_instancia:
                        instancia = inst
                        break

                if not instancia:
                    print(f"      ❌ Instancia no encontrada: {consumo.id_instancia}")
                    print(
                        f"      IDs de instancias disponibles: {[i.id for i in cliente.instancias]}"
                    )
                    continue

                print(f"      ✓ Instancia encontrada: {instancia.nombre}")
                print(f"      • ID Configuración: {instancia.id_configuracion}")
                print(f"      • Estado: {instancia.estado}")

                # Buscar configuración
                configuracion = None
                for cat in categorias.values():
                    for conf in cat.configuraciones:
                        if conf.id == instancia.id_configuracion:
                            configuracion = conf
                            print(
                                f"      ✓ Configuración encontrada: {conf.nombre} (Categoría: {cat.nombre})"
                            )
                            break
                    if configuracion:
                        break

                if not configuracion:
                    print(
                        f"      ❌ Configuración no encontrada: {instancia.id_configuracion}"
                    )
                    # Mostrar configuraciones disponibles
                    print(f"      Configuraciones disponibles:")
                    for cat in categorias.values():
                        for conf in cat.configuraciones:
                            print(f"         - {conf.id}: {conf.nombre}")
                    continue

                print(
                    f"      • Recursos en configuración: {len(configuracion.recursos)}"
                )

                # Calcular costo
                costo_consumo = 0
                for id_rec, cantidad in configuracion.recursos.items():
                    recurso = recursos.get(id_rec)
                    if recurso:
                        costo = float(cantidad) * recurso.valor_hora * consumo.tiempo
                        costo_consumo += costo
                        print(f"         ✓ Recurso {recurso.nombre} ({id_rec}):")
                        print(
                            f"            {cantidad} x ${recurso.valor_hora}/hora x {consumo.tiempo}h = ${costo:.2f}"
                        )
                    else:
                        print(f"         ❌ Recurso no encontrado: {id_rec}")
                        print(f"         Recursos disponibles: {list(recursos.keys())}")

                if costo_consumo > 0:
                    monto_total += costo_consumo
                    consumo.facturado = True
                    consumos_facturados += 1

                    detalles.append(
                        {
                            "id_instancia": consumo.id_instancia,
                            "tiempo": consumo.tiempo,
                            "fecha_hora": consumo.fecha_hora,
                            "costo": round(costo_consumo, 2),
                        }
                    )
                    print(f"      💰 Costo del consumo: ${costo_consumo:.2f}")
                else:
                    print(f"      ⚠️ Costo del consumo = $0.00 (no se facturará)")

            print(f"\n   📊 Resumen del cliente:")
            print(f"      • Consumos procesados: {len(consumos_cliente)}")
            print(f"      • Consumos facturados: {consumos_facturados}")
            print(f"      • Monto total: ${monto_total:.2f}")

            if monto_total > 0:
                factura = Factura(nit, fecha_final, round(monto_total, 2))
                factura.detalles = detalles
                facturas[factura.numero] = factura
                facturas_creadas.append(factura.to_dict())
                print(f"   ✅ Factura #{factura.numero:06d} creada exitosamente")
            else:
                print(f"   ⚠️ No se generó factura (monto total = $0.00)")

        guardar_datos()

        print(f"\n{'='*60}")
        print(f"🎉 FACTURACIÓN COMPLETADA")
        print(f"{'='*60}")
        print(f"✓ Facturas generadas: {len(facturas_creadas)}")
        print(
            f"✓ Total facturado: ${sum(f['monto_total'] for f in facturas_creadas):.2f}"
        )
        print(f"{'='*60}\n")

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
        print(f"\n{'='*60}")
        print(f"❌ ERROR EN FACTURACIÓN: {str(e)}")
        print(f"{'='*60}")
        import traceback

        traceback.print_exc()
        return jsonify({"error": str(e)}), 400


@app.route("/facturas", methods=["GET"])
def listar_facturas():
    """Lista todas las facturas"""
    return jsonify([f.to_dict() for f in facturas.values()]), 200


@app.route("/facturas/<int:numero>", methods=["GET"])
def obtener_factura(numero):
    """Obtiene el detalle de una factura"""
    if numero in facturas:
        return jsonify(facturas[numero].to_dict()), 200
    return jsonify({"error": "Factura no encontrada"}), 404


@app.route("/facturas/cliente/<nit_cliente>", methods=["GET"])
def listar_facturas_cliente(nit_cliente):
    """Lista facturas de un cliente específico"""
    # Normalizar NIT
    nit_cliente = nit_cliente.upper()

    facturas_cliente = [
        f.to_dict() for f in facturas.values() if f.nit_cliente.upper() == nit_cliente
    ]
    return jsonify(facturas_cliente), 200


# =============== AUTENTICACIÓN ===============


@app.route("/login", methods=["POST"])
def login():
    """Endpoint de autenticación"""
    try:
        data = request.json
        usuario = data.get("usuario")
        clave = data.get("clave")

        # Buscar cliente
        for cliente in clientes.values():
            if cliente.usuario == usuario and cliente.clave == clave:
                return (
                    jsonify(
                        {
                            "success": True,
                            "mensaje": "Autenticación exitosa",
                            "cliente": {
                                "nit": cliente.nit,
                                "nombre": cliente.nombre,
                                "usuario": cliente.usuario,
                                "correo": cliente.correo,
                            },
                        }
                    ),
                    200,
                )

        return jsonify({"success": False, "error": "Credenciales incorrectas"}), 401

    except Exception as e:
        return jsonify({"error": str(e)}), 400


# =============== ESTADÍSTICAS ===============


@app.route("/estadisticas", methods=["GET"])
def estadisticas():
    """Obtiene estadísticas generales del sistema"""
    total_consumos = len(consumos)
    consumos_facturados = sum(1 for c in consumos if c.facturado)
    consumos_pendientes = total_consumos - consumos_facturados

    monto_total_facturado = sum(f.monto_total for f in facturas.values())

    return (
        jsonify(
            {
                "recursos": len(recursos),
                "categorias": len(categorias),
                "clientes": len(clientes),
                "instancias": sum(len(c.instancias) for c in clientes.values()),
                "consumos_total": total_consumos,
                "consumos_facturados": consumos_facturados,
                "consumos_pendientes": consumos_pendientes,
                "facturas": len(facturas),
                "monto_total_facturado": round(monto_total_facturado, 2),
            }
        ),
        200,
    )


# =============== DEBUG (TEMPORAL) ===============


@app.route("/debug", methods=["GET"])
def debug():
    """Endpoint de diagnóstico para ver todos los datos del sistema"""
    return (
        jsonify(
            {
                "consumos": [c.to_dict() for c in consumos],
                "consumos_no_facturados": [
                    c.to_dict() for c in consumos if not c.facturado
                ],
                "clientes": {
                    "total": len(clientes),
                    "nits": list(clientes.keys()),
                    "detalles": [
                        {
                            "nit": c.nit,
                            "nombre": c.nombre,
                            "instancias": len(c.instancias),
                            "ids_instancias": [i.id for i in c.instancias],
                        }
                        for c in clientes.values()
                    ],
                },
                "recursos": {
                    "total": len(recursos),
                    "ids": list(recursos.keys()),
                    "detalles": [r.to_dict() for r in recursos.values()],
                },
                "categorias": [
                    {
                        "id": cat.id,
                        "nombre": cat.nombre,
                        "configuraciones": [
                            {
                                "id": conf.id,
                                "nombre": conf.nombre,
                                "recursos": conf.recursos,
                            }
                            for conf in cat.configuraciones
                        ],
                    }
                    for cat in categorias.values()
                ],
                "facturas": [f.to_dict() for f in facturas.values()],
            }
        ),
        200,
    )


# =============== INICIO DEL SERVIDOR ===============

if __name__ == "__main__":
    print("=" * 60)
    print("🚀 API de Tecnologías Chapinas S.A.")
    print("=" * 60)
    print(f"📍 Servidor iniciado en: http://localhost:5000")
    print(f"📊 Recursos cargados: {len(recursos)}")
    print(f"📁 Categorías cargadas: {len(categorias)}")
    print(f"👥 Clientes cargados: {len(clientes)}")
    print(f"📈 Consumos cargados: {len(consumos)}")
    print(f"💰 Facturas cargadas: {len(facturas)}")
    print("=" * 60)
    print("✅ Endpoints disponibles:")
    print("   - GET  /health")
    print("   - POST /inicializar")
    print("   - POST /cargar_configuracion")
    print("   - POST /cargar_consumos")
    print("   - GET  /recursos")
    print("   - GET  /categorias")
    print("   - GET  /clientes")
    print("   - POST /facturar")
    print("   - GET  /facturas")
    print("   - GET  /estadisticas")
    print("   - GET  /debug (⚠️ temporal)")
    print("=" * 60)

    app.run(debug=True, port=5000, host="0.0.0.0")
