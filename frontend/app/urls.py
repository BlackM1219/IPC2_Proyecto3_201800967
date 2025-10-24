from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("configuracion/", views.enviar_configuracion, name="configuracion"),
    path("consumo/", views.enviar_consumo, name="consumo"),
    path("inicializar/", views.inicializar_sistema, name="inicializar"),
    path("consultar/", views.consultar_datos, name="consultar"),
    path("crear/", views.crear_datos, name="crear"),
    path("facturar/", views.facturar, name="facturar"),
    path(
        "pdf/factura/<int:numero_factura>/",
        views.generar_pdf_factura,
        name="pdf_factura",
    ),
    path("pdf/analisis/", views.generar_pdf_analisis, name="pdf_analisis"),
    path("ayuda/", views.ayuda, name="ayuda"),
]
