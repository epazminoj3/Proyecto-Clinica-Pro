# -*- coding: utf-8 -*-
from django.urls import path
from . import views

app_name = 'chatbot'

urlpatterns = [
    # Interfaz principal del chat
    path('', views.chat_interface, name='chat_interface'),
    
    # API endpoints
    path('api/mensaje/', views.procesar_mensaje, name='procesar_mensaje'),
    path('api/estado/', views.estado_ia, name='estado_ia'),
    path('api/formulario/', views.generar_formulario, name='generar_formulario'),
    
    # Administración del sistema multi-key
    path('admin/panel/', views.admin_panel_multikey, name='admin_panel'),
    path('api/admin/status/', views.api_status_multikey, name='api_status_multikey'),
    path('api/admin/cambiar-key/', views.cambiar_api_key, name='cambiar_api_key'),
]
