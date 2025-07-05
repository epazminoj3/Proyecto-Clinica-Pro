# Importar todas las vistas para disponibilizarlas en el paquete
from .atencion_medica import *
from .medicamento import MedicamentoCreateApiView
from .horario import (
    HorarioAtencionListView, HorarioAtencionCreateView, 
    HorarioAtencionUpdateView, HorarioAtencionDeleteView,
    HorarioAjaxDayView, HorarioAjaxSaveAllView, HorarioGestionView
)
from .cita_medica import (
    CitaMedicaListView, CitaMedicaCreateView,
    CitaMedicaUpdateView, CitaMedicaDeleteView, CitaMedicaDetailView,
    CitaMedicaConfirmacionView, EnviarCorreoCitaView,
    VerificarDisponibilidadView
)
from .detalle_atencion import (
    DetalleAtencionListView, DetalleAtencionCreateView,
    DetalleAtencionUpdateView, DetalleAtencionDeleteView
)
from .servicios_adicionales import (
    ServiciosAdicionalesListView, ServiciosAdicionalesCreateView,
    ServiciosAdicionalesUpdateView, ServiciosAdicionalesDeleteView
)
from .pago import (
    PagoListView, PagoCreateView, PagoUpdateView, PagoDeleteView,
    DetallePagoListView, DetallePagoCreateView, DetallePagoUpdateView, DetallePagoDeleteView
)
from .calendar_api import (
    CalendarDataView, CalendarAvailabilityView, UpdateAppointmentStatusView, MarcarCitaAtendidaView
)
from .api import (
    CalendarDataAPI, TodayAppointmentsAPI, UpcomingAppointmentsAPI
)