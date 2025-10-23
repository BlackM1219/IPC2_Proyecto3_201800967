from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
import requests
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from io import BytesIO

API_URL = "http://localhost:5000"


def index(request):
    return render(request, "index.html")


def enviar_configuracion(request):
    if request.method == "POST":
        try:
            archivo = request.FILES.get("archivo_xml")
            if not archivo:
                return JsonResponse({"error": "No se recibió archivo"}, status=400)

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
                return JsonResponse(
                    {"success": False, "error": response.json().get("error")},
                    status=400,
                )
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)}, status=500)

    return render(request, "configuracion.html")


def enviar_consumo(request):
    if request.method == "POST":
        try:
            archivo = request.FILES.get("archivo_xml")
            if not archivo:
                return JsonResponse({"error": "No se recibió archivo"}, status=400)

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
                return JsonResponse(
                    {"success": False, "error": response.json().get("error")},
                    status=400,
                )
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)}, status=500)

    return render(request, "consumo.html")


def inicializar_sistema(request):
    try:
        response = requests.post(f"{API_URL}/inicializar")
        if response.status_code == 200:
            return JsonResponse({"success": True, "mensaje": "Sistema inicializado"})
        else:
            return JsonResponse(
                {"success": False, "error": "Error al inicializar"}, status=400
            )
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)


def consultar_datos(request):
    try:
        recursos = requests.get(f"{API_URL}/recursos").json()
        categorias = requests.get(f"{API_URL}/categorias").json()
        clientes = requests.get(f"{API_URL}/clientes").json()

        return render(
            request,
            "consultar.html",
            {"recursos": recursos, "categorias": categorias, "clientes": clientes},
        )
    except Exception as e:
        return render(request, "consultar.html", {"error": str(e)})


def crear_datos(request):
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
                return JsonResponse(
                    {"success": False, "error": response.json().get("error")},
                    status=400,
                )
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)}, status=500)

    return render(request, "crear.html")


def facturar(request):
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
                return JsonResponse(
                    {"success": False, "error": response.json().get("error")},
                    status=400,
                )
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)}, status=500)

    try:
        response = requests.get(f"{API_URL}/facturas")
        facturas = response.json() if response.status_code == 200 else []
        return render(request, "facturar.html", {"facturas": facturas})
    except:
        return render(request, "facturar.html", {"facturas": []})


def generar_pdf_factura(request, numero_factura):
    try:
        response = requests.get(f"{API_URL}/facturas/{numero_factura}")
        if response.status_code != 200:
            return HttpResponse("Factura no encontrada", status=404)

        factura = response.json()

        buffer = BytesIO()
        p = canvas.Canvas(buffer, pagesize=letter)
        width, height = letter

        p.setFont("Helvetica-Bold", 18)
        p.drawString(1 * inch, height - 1 * inch, "DETALLE DE FACTURA")

        p.setFont("Helvetica-Bold", 12)
        p.drawString(1 * inch, height - 1.5 * inch, f"Factura No: {factura['numero']}")
        p.drawString(
            1 * inch, height - 1.8 * inch, f"NIT Cliente: {factura['nit_cliente']}"
        )
        p.drawString(
            1 * inch, height - 2.1 * inch, f"Fecha: {factura['fecha_factura']}"
        )
        p.drawString(
            1 * inch, height - 2.4 * inch, f"Monto Total: ${factura['monto_total']:.2f}"
        )

        p.setFont("Helvetica-Bold", 14)
        p.drawString(1 * inch, height - 3 * inch, "Detalles:")

        y = height - 3.3 * inch
        p.setFont("Helvetica", 10)

        for i, det in enumerate(factura.get("detalles", []), 1):
            texto = f"{i}. Instancia: {det.get('id_instancia')} - Tiempo: {det.get('tiempo')}h - Costo: ${float(det.get('costo', 0)):.2f}"
            p.drawString(1 * inch, y, texto)
            y -= 0.25 * inch
            if y < 1 * inch:
                p.showPage()
                y = height - 1 * inch

        p.save()
        buffer.seek(0)

        response = HttpResponse(buffer, content_type="application/pdf")
        response["Content-Disposition"] = (
            f'attachment; filename="factura_{numero_factura}.pdf"'
        )
        return response
    except Exception as e:
        return HttpResponse(f"Error: {str(e)}", status=500)


def ayuda(request):
    return render(request, "ayuda.html")
