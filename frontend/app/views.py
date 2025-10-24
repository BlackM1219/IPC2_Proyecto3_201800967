from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponse
import requests
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from io import BytesIO

API_URL = "http://localhost:5000"

# =============== SISTEMA DE LOGIN ===============


def login_view(request):
    """Vista de login"""
    if request.method == "POST":
        usuario = request.POST.get("usuario")
        clave = request.POST.get("clave")

        try:
            # Obtener todos los clientes
            response = requests.get(f"{API_URL}/clientes")
            if response.status_code == 200:
                clientes = response.json()

                # Buscar cliente con credenciales
                for cliente in clientes:
                    if cliente["usuario"] == usuario and cliente["clave"] == clave:
                        # Guardar sesión
                        request.session["usuario"] = usuario
                        request.session["nit"] = cliente["nit"]
                        request.session["nombre"] = cliente["nombre"]
                        return redirect("index")

                return render(
                    request, "login.html", {"error": "Credenciales incorrectas"}
                )
            else:
                return render(
                    request,
                    "login.html",
                    {"error": "Error al conectar con el servidor"},
                )
        except Exception as e:
            return render(
                request, "login.html", {"error": f"Error de conexión: {str(e)}"}
            )

    return render(request, "login.html")


def logout_view(request):
    """Cerrar sesión"""
    request.session.flush()
    return redirect("login")


def verificar_sesion(request):
    """Middleware manual para verificar sesión"""
    if "usuario" not in request.session:
        return redirect("login")
    return None


# =============== VISTAS PRINCIPALES ===============


def index(request):
    """Página principal"""
    verificacion = verificar_sesion(request)
    if verificacion:
        return verificacion

    return render(
        request,
        "index.html",
        {"usuario": request.session.get("nombre"), "nit": request.session.get("nit")},
    )


def enviar_configuracion(request):
    """Envía archivo XML de configuración"""
    verificacion = verificar_sesion(request)
    if verificacion:
        return verificacion

    if request.method == "POST":
        try:
            archivo = request.FILES.get("archivo_xml")
            if not archivo:
                return JsonResponse(
                    {"success": False, "error": "No se recibió archivo"}, status=400
                )

            xml_data = archivo.read()
            response = requests.post(f"{API_URL}/cargar_configuracion", data=xml_data)

            if response.status_code == 200:
                resultado = response.json()
                return JsonResponse(
                    {
                        "success": True,
                        "mensaje": resultado["mensaje"],
                        "detalles": f"{resultado['recursos_creados']} recursos, "
                        f"{resultado['categorias_creadas']} categorías, "
                        f"{resultado['clientes_creados']} clientes, "
                        f"{resultado['instancias_creadas']} instancias",
                    }
                )
            else:
                error_msg = response.json().get("error", "Error desconocido")
                return JsonResponse({"success": False, "error": error_msg}, status=400)

        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)}, status=500)

    return render(request, "configuracion.html")


def enviar_consumo(request):
    """Envía archivo XML de consumos"""
    verificacion = verificar_sesion(request)
    if verificacion:
        return verificacion

    if request.method == "POST":
        try:
            archivo = request.FILES.get("archivo_xml")
            if not archivo:
                return JsonResponse(
                    {"success": False, "error": "No se recibió archivo"}, status=400
                )

            xml_data = archivo.read()
            response = requests.post(f"{API_URL}/cargar_consumos", data=xml_data)

            if response.status_code == 200:
                resultado = response.json()
                return JsonResponse(
                    {
                        "success": True,
                        "mensaje": resultado["mensaje"],
                        "detalles": f"{resultado['consumos_procesados']} consumos procesados",
                    }
                )
            else:
                error_msg = response.json().get("error", "Error desconocido")
                return JsonResponse({"success": False, "error": error_msg}, status=400)

        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)}, status=500)

    return render(request, "consumo.html")


def inicializar_sistema(request):
    """Elimina todos los datos del sistema"""
    verificacion = verificar_sesion(request)
    if verificacion:
        return verificacion

    try:
        response = requests.post(f"{API_URL}/inicializar")
        if response.status_code == 200:
            return JsonResponse(
                {"success": True, "mensaje": "Sistema inicializado correctamente"}
            )
        else:
            return JsonResponse(
                {"success": False, "error": "Error al inicializar"}, status=400
            )
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)


def consultar_datos(request):
    """Muestra los datos del sistema"""
    verificacion = verificar_sesion(request)
    if verificacion:
        return verificacion

    try:
        recursos = requests.get(f"{API_URL}/recursos").json()
        categorias = requests.get(f"{API_URL}/categorias").json()
        clientes = requests.get(f"{API_URL}/clientes").json()

        context = {"recursos": recursos, "categorias": categorias, "clientes": clientes}
        return render(request, "consultar.html", context)

    except Exception as e:
        return render(request, "consultar.html", {"error": str(e)})


def crear_datos(request):
    """Formulario para crear nuevos datos"""
    verificacion = verificar_sesion(request)
    if verificacion:
        return verificacion

    if request.method == "POST":
        try:
            tipo = request.POST.get("tipo")

            if tipo == "recurso":
                data = {
                    "id": request.POST.get("id"),
                    "nombre": request.POST.get("nombre"),
                    "abreviatura": request.POST.get("abreviatura"),
                    "metrica": request.POST.get("metrica"),
                    "tipo": request.POST.get("tipo_recurso"),
                    "valor_hora": float(request.POST.get("valor_hora")),
                }
                response = requests.post(f"{API_URL}/recursos", json=data)

            elif tipo == "categoria":
                data = {
                    "id": request.POST.get("id"),
                    "nombre": request.POST.get("nombre"),
                    "descripcion": request.POST.get("descripcion"),
                    "carga_trabajo": request.POST.get("carga_trabajo"),
                }
                response = requests.post(f"{API_URL}/categorias", json=data)

            elif tipo == "cliente":
                data = {
                    "nit": request.POST.get("nit"),
                    "nombre": request.POST.get("nombre"),
                    "usuario": request.POST.get("usuario"),
                    "clave": request.POST.get("clave"),
                    "direccion": request.POST.get("direccion"),
                    "correo": request.POST.get("correo"),
                }
                response = requests.post(f"{API_URL}/clientes", json=data)

            elif tipo == "instancia":
                nit = request.POST.get("nit_cliente")
                data = {
                    "id": request.POST.get("id"),
                    "id_configuracion": request.POST.get("id_configuracion"),
                    "nombre": request.POST.get("nombre"),
                    "fecha_inicio": request.POST.get("fecha_inicio"),
                    "estado": request.POST.get("estado", "Vigente"),
                }
                response = requests.post(f"{API_URL}/instancias/{nit}", json=data)

            if response.status_code in [200, 201]:
                return JsonResponse(
                    {"success": True, "mensaje": "Dato creado exitosamente"}
                )
            else:
                error_msg = response.json().get("error", "Error desconocido")
                return JsonResponse({"success": False, "error": error_msg}, status=400)

        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)}, status=500)

    return render(request, "crear.html")


def facturar(request):
    """Genera facturas por rango de fechas"""
    verificacion = verificar_sesion(request)
    if verificacion:
        return verificacion

    if request.method == "POST":
        try:
            data = {
                "fecha_inicio": request.POST.get("fecha_inicio"),
                "fecha_final": request.POST.get("fecha_final"),
            }
            response = requests.post(f"{API_URL}/facturar", json=data)

            if response.status_code == 200:
                resultado = response.json()
                return JsonResponse(
                    {
                        "success": True,
                        "mensaje": resultado["mensaje"],
                        "detalles": f"{resultado['facturas_creadas']} facturas generadas",
                        "facturas": resultado.get("facturas", []),
                    }
                )
            else:
                error_msg = response.json().get("error", "Error desconocido")
                return JsonResponse({"success": False, "error": error_msg}, status=400)

        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)}, status=500)

    # GET: Mostrar facturas existentes
    try:
        response = requests.get(f"{API_URL}/facturas")
        facturas = response.json() if response.status_code == 200 else []
        return render(request, "facturar.html", {"facturas": facturas})
    except:
        return render(request, "facturar.html", {"facturas": []})


# =============== GENERACIÓN DE PDFs ===============


def generar_pdf_factura(request, numero_factura):
    """Genera PDF detallado de factura"""
    verificacion = verificar_sesion(request)
    if verificacion:
        return verificacion

    try:
        # Obtener datos de factura
        response = requests.get(f"{API_URL}/facturas/{numero_factura}")
        if response.status_code != 200:
            return HttpResponse("Factura no encontrada", status=404)

        factura = response.json()

        # Obtener datos del cliente
        nit_cliente = factura["nit_cliente"]
        cliente_response = requests.get(f"{API_URL}/clientes")
        clientes = cliente_response.json()
        cliente = next((c for c in clientes if c["nit"] == nit_cliente), None)

        # Crear PDF
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=30, bottomMargin=30)
        elements = []
        styles = getSampleStyleSheet()

        # Título
        title = Paragraph("<b>FACTURA</b>", styles["Title"])
        elements.append(title)
        elements.append(Spacer(1, 12))

        # Número de factura
        factura_num = Paragraph(
            f"<b>No. {factura['numero']:06d}</b>", styles["Heading2"]
        )
        elements.append(factura_num)
        elements.append(Spacer(1, 20))

        # Información de la empresa
        company_info = [
            ["<b>TECNOLOGÍAS CHAPINAS S.A.</b>", ""],
            ["NIT: 12345678-9", ""],
            ["Zona 10, Ciudad de Guatemala", ""],
            ["Tel: 2345-6789 | Email: info@tecchapinas.com", ""],
        ]
        company_table = Table(company_info, colWidths=[300, 200])
        company_table.setStyle(
            TableStyle(
                [
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("FONTNAME", (0, 0), (0, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 10),
                    ("TEXTCOLOR", (0, 0), (-1, -1), colors.HexColor("#2c3e50")),
                ]
            )
        )
        elements.append(company_table)
        elements.append(Spacer(1, 20))

        # Información del cliente
        if cliente:
            client_info = [
                ["<b>FACTURAR A:</b>", ""],
                ["Cliente:", cliente["nombre"]],
                ["NIT:", cliente["nit"]],
                ["Dirección:", cliente["direccion"]],
                ["Email:", cliente["correo"]],
                ["", ""],
                ["Fecha de Emisión:", factura["fecha_factura"]],
            ]
            client_table = Table(client_info, colWidths=[150, 350])
            client_table.setStyle(
                TableStyle(
                    [
                        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                        ("FONTNAME", (0, 0), (0, 0), "Helvetica-Bold"),
                        ("FONTSIZE", (0, 0), (-1, -1), 10),
                        ("BACKGROUND", (0, 0), (1, 0), colors.HexColor("#ecf0f1")),
                        ("BOX", (0, 0), (-1, -1), 1, colors.grey),
                        ("LINEBELOW", (0, 0), (-1, 0), 2, colors.HexColor("#34495e")),
                    ]
                )
            )
            elements.append(client_table)
            elements.append(Spacer(1, 30))

        # Encabezado de detalle
        detail_header = Paragraph("<b>DETALLE DE SERVICIOS</b>", styles["Heading3"])
        elements.append(detail_header)
        elements.append(Spacer(1, 12))

        # Detalle de consumos
        detail_data = [["No.", "ID Instancia", "Tiempo Consumido", "Costo"]]

        for i, det in enumerate(factura.get("detalles", []), 1):
            detail_data.append(
                [
                    str(i),
                    str(det.get("id_instancia", "N/A")),
                    f"{float(det.get('tiempo', 0)):.2f} hrs",
                    f"${float(det.get('costo', 0)):,.2f}",
                ]
            )

        detail_table = Table(detail_data, colWidths=[50, 150, 150, 150])
        detail_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#34495e")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, 0), 11),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                    ("TOPPADDING", (0, 0), (-1, 0), 12),
                    ("BACKGROUND", (0, 1), (-1, -1), colors.white),
                    ("GRID", (0, 0), (-1, -1), 1, colors.grey),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ]
            )
        )
        elements.append(detail_table)
        elements.append(Spacer(1, 30))

        # Subtotal y total
        total_data = [
            ["", "", "<b>SUBTOTAL:</b>", f"${factura['monto_total']:,.2f}"],
            ["", "", "<b>IVA (12%):</b>", f"${factura['monto_total'] * 0.12:,.2f}"],
            ["", "", "<b>TOTAL A PAGAR:</b>", f"${factura['monto_total'] * 1.12:,.2f}"],
        ]
        total_table = Table(total_data, colWidths=[50, 150, 150, 150])
        total_table.setStyle(
            TableStyle(
                [
                    ("ALIGN", (2, 0), (-1, -1), "RIGHT"),
                    ("FONTNAME", (2, 0), (-1, -1), "Helvetica-Bold"),
                    ("FONTSIZE", (2, 0), (2, 1), 11),
                    ("FONTSIZE", (2, 2), (-1, 2), 13),
                    ("BACKGROUND", (2, 2), (-1, 2), colors.HexColor("#27ae60")),
                    ("TEXTCOLOR", (2, 2), (-1, 2), colors.whitesmoke),
                    ("BOX", (2, 2), (-1, 2), 2, colors.HexColor("#27ae60")),
                    ("TOPPADDING", (2, 0), (-1, -1), 8),
                    ("BOTTOMPADDING", (2, 0), (-1, -1), 8),
                ]
            )
        )
        elements.append(total_table)
        elements.append(Spacer(1, 40))

        # Notas
        notes = Paragraph(
            "<b>Notas:</b><br/>"
            "• Factura generada electrónicamente por el sistema de Tecnologías Chapinas S.A.<br/>"
            "• Los servicios facturados corresponden al uso de infraestructura en la nube.<br/>"
            "• Para consultas: soporte@tecchapinas.com",
            styles["Normal"],
        )
        elements.append(notes)

        # Construir PDF
        doc.build(elements)
        buffer.seek(0)

        response = HttpResponse(buffer, content_type="application/pdf")
        response["Content-Disposition"] = (
            f'attachment; filename="Factura_{factura['numero']:06d}.pdf"'
        )
        return response

    except Exception as e:
        return HttpResponse(f"Error generando PDF: {str(e)}", status=500)


def generar_pdf_analisis(request):
    """Genera PDF con análisis de ventas"""
    verificacion = verificar_sesion(request)
    if verificacion:
        return verificacion

    try:
        tipo = request.GET.get("tipo", "categorias")
        fecha_inicio = request.GET.get("fecha_inicio", "01/01/2025")
        fecha_final = request.GET.get("fecha_final", "31/12/2025")

        # Obtener datos
        facturas_response = requests.get(f"{API_URL}/facturas")
        facturas = (
            facturas_response.json() if facturas_response.status_code == 200 else []
        )

        categorias_response = requests.get(f"{API_URL}/categorias")
        categorias = (
            categorias_response.json() if categorias_response.status_code == 200 else []
        )

        recursos_response = requests.get(f"{API_URL}/recursos")
        recursos = (
            recursos_response.json() if recursos_response.status_code == 200 else []
        )

        # Crear PDF
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=30, bottomMargin=30)
        elements = []
        styles = getSampleStyleSheet()

        # Título
        title = Paragraph("<b>ANÁLISIS DE VENTAS</b>", styles["Title"])
        elements.append(title)
        elements.append(Spacer(1, 12))

        subtitle = Paragraph(
            f"<b>Período:</b> {fecha_inicio} - {fecha_final}", styles["Heading3"]
        )
        elements.append(subtitle)
        elements.append(Spacer(1, 20))

        # Estadísticas generales
        total_facturas = len(facturas)
        total_monto = sum(f["monto_total"] for f in facturas)

        stats_data = [
            ["<b>ESTADÍSTICAS GENERALES</b>", ""],
            ["Total de Facturas:", str(total_facturas)],
            ["Monto Total Facturado:", f"${total_monto:,.2f}"],
            [
                "Promedio por Factura:",
                f"${(total_monto/total_facturas if total_facturas > 0 else 0):,.2f}",
            ],
        ]
        stats_table = Table(stats_data, colWidths=[250, 250])
        stats_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (1, 0), colors.HexColor("#34495e")),
                    ("TEXTCOLOR", (0, 0), (1, 0), colors.whitesmoke),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 11),
                    ("GRID", (0, 0), (-1, -1), 1, colors.grey),
                    ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
                ]
            )
        )
        elements.append(stats_table)
        elements.append(Spacer(1, 30))

        if tipo == "categorias":
            # Análisis por categorías
            detail_title = Paragraph(
                "<b>INGRESOS POR CATEGORÍA</b>", styles["Heading3"]
            )
            elements.append(detail_title)
            elements.append(Spacer(1, 12))

            data = [["Categoría", "Descripción", "Ingresos ($)"]]

            for cat in categorias:
                # Cálculo simplificado (en producción calcularías real)
                ingresos = total_monto / len(categorias) if categorias else 0
                data.append(
                    [
                        cat["nombre"],
                        (
                            cat["descripcion"][:40] + "..."
                            if len(cat["descripcion"]) > 40
                            else cat["descripcion"]
                        ),
                        f"${ingresos:,.2f}",
                    ]
                )

            table = Table(data, colWidths=[150, 250, 100])

        else:
            # Análisis por recursos
            detail_title = Paragraph("<b>INGRESOS POR RECURSO</b>", styles["Heading3"])
            elements.append(detail_title)
            elements.append(Spacer(1, 12))

            data = [["Recurso", "Tipo", "Valor/Hora", "Ingresos ($)"]]

            for rec in recursos:
                # Cálculo simplificado
                ingresos = total_monto / len(recursos) if recursos else 0
                data.append(
                    [
                        rec["nombre"],
                        rec["tipo"],
                        f"${rec['valor_hora']:.2f}",
                        f"${ingresos:,.2f}",
                    ]
                )

            table = Table(data, colWidths=[150, 100, 100, 150])

        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2c3e50")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, 0), 11),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                    ("BACKGROUND", (0, 1), (-1, -1), colors.white),
                    ("GRID", (0, 0), (-1, -1), 1, colors.black),
                ]
            )
        )
        elements.append(table)
        elements.append(Spacer(1, 30))

        # Nota final
        note = Paragraph(
            "<i>Este reporte fue generado automáticamente por el Sistema de Facturación "
            "de Tecnologías Chapinas S.A.</i>",
            styles["Normal"],
        )
        elements.append(note)

        doc.build(elements)
        buffer.seek(0)

        response = HttpResponse(buffer, content_type="application/pdf")
        response["Content-Disposition"] = (
            f'attachment; filename="Analisis_Ventas_{tipo}.pdf"'
        )
        return response

    except Exception as e:
        return HttpResponse(f"Error: {str(e)}", status=500)


def ayuda(request):
    """Muestra información del estudiante y documentación"""
    verificacion = verificar_sesion(request)
    if verificacion:
        return verificacion

    return render(request, "ayuda.html")
