from django.urls import path
from applications.doctor.views import (
    # Atenciones (ya existente)
    AtencionListView, AtencionCreateView, AtencionUpdateView, AtencionDeleteView,
    BuscarPacientesView, ConsultasAnterioresView, PacienteCreateApiView,
    MedicamentoCreateApiView,
    
    # Horarios
    HorarioAtencionListView, HorarioAtencionCreateView, 
    HorarioAtencionUpdateView, HorarioAtencionDeleteView,
    HorarioGestionView, HorarioAjaxDayView, HorarioAjaxSaveAllView,
    
    # Citas Médicas
    CitaMedicaListView, CitaMedicaCreateView,
    CitaMedicaUpdateView, CitaMedicaDeleteView, CitaMedicaDetailView,
    CitaMedicaConfirmacionView, EnviarCorreoCitaView,
    VerificarDisponibilidadView,
    
    # Detalles de Atención
    DetalleAtencionListView, DetalleAtencionCreateView,
    DetalleAtencionUpdateView, DetalleAtencionDeleteView,
    
    # Servicios Adicionales
    ServiciosAdicionalesListView, ServiciosAdicionalesCreateView,
    ServiciosAdicionalesUpdateView, ServiciosAdicionalesDeleteView,
    
    # Pagos
    PagoListView, PagoCreateView, PagoUpdateView, PagoDeleteView,
    DetallePagoListView, DetallePagoCreateView, DetallePagoUpdateView, DetallePagoDeleteView,
    
    # APIs del Calendario
    CalendarDataView, CalendarAvailabilityView,
    
    # APIs Dashboard
    CalendarDataAPI, TodayAppointmentsAPI, UpcomingAppointmentsAPI,
)

app_name='doctor' # define un espacio de nombre para la aplicacion

urlpatterns = [
    # ==================== URLs DE ATENCIONES (ya existente) ====================
    path('atenciones/', AtencionListView.as_view(), name="atencion_list"),
    path('atenciones/crear/', AtencionCreateView.as_view(), name="atencion_create"),
    path('atenciones/<int:pk>/editar/', AtencionUpdateView.as_view(), name="atencion_update"),
    path('atenciones/<int:pk>/eliminar/', AtencionDeleteView.as_view(), name="atencion_delete"),
    
    # ==================== AJAX APIs ====================
    path('api/buscar-pacientes/', BuscarPacientesView.as_view(), name="buscar_pacientes"),
    path('api/consultas-anteriores/', ConsultasAnterioresView.as_view(), name="consultas_anteriores"),
    path('api/crear-paciente/', PacienteCreateApiView.as_view(), name="crear_paciente"),
    path('api/crear-medicamento/', MedicamentoCreateApiView.as_view(), name="crear_medicamento"),
    
    # ==================== URLs DE HORARIOS ====================
    path('horario/', HorarioAtencionListView.as_view(), name="horario_list"),
    path('horario/crear/', HorarioAtencionCreateView.as_view(), name="horario_create"),
    path('horario/gestionar/', HorarioGestionView.as_view(), name="horario_gestionar"),
    path('horario/<int:pk>/editar/', HorarioAtencionUpdateView.as_view(), name="horario_update"),
    path('horario/<int:pk>/eliminar/', HorarioAtencionDeleteView.as_view(), name="horario_delete"),
    
    # URLs AJAX para horarios
    path('horario/ajax/day/<str:day_code>/', HorarioAjaxDayView.as_view(), name="horario_ajax_day"),
    path('horario/ajax/save-all/', HorarioAjaxSaveAllView.as_view(), name="horario_ajax_save_all"),
    
    # ==================== URLs DE CITAS MÉDICAS ====================
    path('cita_medica/', CitaMedicaListView.as_view(), name="cita_medica_list"),
    path('cita_medica/crear/', CitaMedicaCreateView.as_view(), name="cita_medica_create"),
    path('cita_medica/<int:pk>/', CitaMedicaDetailView.as_view(), name="cita_medica_detail"),
    path('cita_medica/<int:pk>/editar/', CitaMedicaUpdateView.as_view(), name="cita_medica_update"),
    path('cita_medica/<int:pk>/eliminar/', CitaMedicaDeleteView.as_view(), name="cita_medica_delete"),
    path('cita_medica/<int:pk>/confirmacion/', CitaMedicaConfirmacionView.as_view(), name="cita_medica_confirmacion"),
    path('cita_medica/<int:pk>/enviar-correo/', EnviarCorreoCitaView.as_view(), name="enviar_correo_cita"),
    path('cita_medica/verificar-disponibilidad/', VerificarDisponibilidadView.as_view(), name="verificar_disponibilidad"),
    
    # ==================== URLs DE DETALLES DE ATENCIÓN ====================
    path('detalle_atencion/', DetalleAtencionListView.as_view(), name="detalle_atencion_list"),
    path('detalle_atencion/crear/', DetalleAtencionCreateView.as_view(), name="detalle_atencion_create"),
    path('detalle_atencion/<int:pk>/editar/', DetalleAtencionUpdateView.as_view(), name="detalle_atencion_update"),
    path('detalle_atencion/<int:pk>/eliminar/', DetalleAtencionDeleteView.as_view(), name="detalle_atencion_delete"),
    
    # ==================== URLs DE SERVICIOS ADICIONALES ====================
    path('servicios_adicionales/', ServiciosAdicionalesListView.as_view(), name="servicios_adicionales_list"),
    path('servicios_adicionales/crear/', ServiciosAdicionalesCreateView.as_view(), name="servicios_adicionales_create"),
    path('servicios_adicionales/<int:pk>/editar/', ServiciosAdicionalesUpdateView.as_view(), name="servicios_adicionales_update"),
    path('servicios_adicionales/<int:pk>/eliminar/', ServiciosAdicionalesDeleteView.as_view(), name="servicios_adicionales_delete"),
    
    # ==================== URLs DE PAGOS ====================
    path('pago/', PagoListView.as_view(), name="pago_list"),
    path('pago/crear/', PagoCreateView.as_view(), name="pago_create"),
    path('pago/<int:pk>/editar/', PagoUpdateView.as_view(), name="pago_update"),
    path('pago/<int:pk>/eliminar/', PagoDeleteView.as_view(), name="pago_delete"),
    
    # URLs de detalles de pago
    path('detalle_pago/', DetallePagoListView.as_view(), name="detalle_pago_list"),
    path('detalle_pago/crear/', DetallePagoCreateView.as_view(), name="detalle_pago_create"),
    path('detalle_pago/<int:pk>/editar/', DetallePagoUpdateView.as_view(), name="detalle_pago_update"),
    path('detalle_pago/<int:pk>/eliminar/', DetallePagoDeleteView.as_view(), name="detalle_pago_delete"),
    
    # ==================== APIs DEL CALENDARIO ====================
    path('api/calendar/data/', CalendarDataView.as_view(), name="calendar_data"),
    path('api/calendar/availability/', CalendarAvailabilityView.as_view(), name="calendar_availability"),
    
    # ==================== APIs DASHBOARD ====================
    path('api/appointments/today/', TodayAppointmentsAPI.as_view(), name="today_appointments"),
    path('api/appointments/upcoming/', UpcomingAppointmentsAPI.as_view(), name="upcoming_appointments"),
    path('api/dashboard/calendar/', CalendarDataAPI.as_view(), name="dashboard_calendar"),
]