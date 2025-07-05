from django.urls import path
from applications.core.views import (
    # Pacientes
    PacienteListView, PacienteCreateView, PacienteUpdateView, PacienteDeleteView,
    
    # Doctores
    DoctorListView, DoctorCreateView, DoctorUpdateView, DoctorDeleteView,
    EspecialidadListView, EspecialidadCreateView, EspecialidadUpdateView, 
    EspecialidadDeleteView,
    
    # Medicamentos
    MedicamentoListView, MedicamentoCreateView, MedicamentoUpdateView, MedicamentoDeleteView,
    TipoMedicamentoListView, TipoMedicamentoCreateView, TipoMedicamentoUpdateView, 
    TipoMedicamentoDeleteView,
    MarcaMedicamentoListView, MarcaMedicamentoCreateView, MarcaMedicamentoUpdateView, 
    MarcaMedicamentoDeleteView,
    
    # Empleados y otros
    EmpleadoListView, EmpleadoCreateView, EmpleadoUpdateView, EmpleadoDeleteView,
    CargoListView, CargoCreateView, CargoUpdateView, CargoDeleteView,
    DiagnosticoListView, DiagnosticoCreateView, DiagnosticoUpdateView, 
    DiagnosticoDeleteView,
    TipoGastoListView, TipoGastoCreateView, TipoGastoUpdateView, 
    TipoGastoDeleteView,
    GastoMensualListView, GastoMensualCreateView, GastoMensualUpdateView, 
    GastoMensualDeleteView,
    TipoSangreListView, TipoSangreCreateView, TipoSangreUpdateView, 
    TipoSangreDeleteView,
)

app_name = 'core'  # define un espacio de nombre para la aplicacion

urlpatterns = [
    # ==================== URLs DE PACIENTES ====================
    path('pacientes/', PacienteListView.as_view(), name='paciente_list'),
    path('pacientes/crear/', PacienteCreateView.as_view(), name='paciente_create'),
    path('pacientes/<int:pk>/editar/', PacienteUpdateView.as_view(), name='paciente_update'),
    path('pacientes/<int:pk>/eliminar/', PacienteDeleteView.as_view(), name='paciente_delete'),
    
    # ==================== URLs DE DOCTORES ====================
    path('doctores/', DoctorListView.as_view(), name='doctor_list'),
    path('doctores/crear/', DoctorCreateView.as_view(), name='doctor_create'),
    path('doctores/<int:pk>/editar/', DoctorUpdateView.as_view(), name='doctor_update'),
    path('doctores/<int:pk>/eliminar/', DoctorDeleteView.as_view(), name='doctor_delete'),
    
    # URLs de especialidades
    path('especialidades/', EspecialidadListView.as_view(), name='especialidad_list'),
    path('especialidades/crear/', EspecialidadCreateView.as_view(), name='especialidad_create'),
    path('especialidades/<int:pk>/editar/', EspecialidadUpdateView.as_view(), name='especialidad_update'),
    path('especialidades/<int:pk>/eliminar/', EspecialidadDeleteView.as_view(), name='especialidad_delete'),
    
    # ==================== URLs DE MEDICAMENTOS ====================
    path('medicamentos/', MedicamentoListView.as_view(), name='medicamento_list'),
    path('medicamentos/crear/', MedicamentoCreateView.as_view(), name='medicamento_create'),
    path('medicamentos/<int:pk>/editar/', MedicamentoUpdateView.as_view(), name='medicamento_update'),
    path('medicamentos/<int:pk>/eliminar/', MedicamentoDeleteView.as_view(), name='medicamento_delete'),
    
    # URLs de tipos de medicamento
    path('tipo_medicamento/', TipoMedicamentoListView.as_view(), name='tipo_medicamento_list'),
    path('tipo_medicamento/crear/', TipoMedicamentoCreateView.as_view(), name='tipo_medicamento_create'),
    path('tipo_medicamento/<int:pk>/editar/', TipoMedicamentoUpdateView.as_view(), name='tipo_medicamento_update'),
    path('tipo_medicamento/<int:pk>/eliminar/', TipoMedicamentoDeleteView.as_view(), name='tipo_medicamento_delete'),
    
    # URLs de marcas de medicamento
    path('marca_medicamento/', MarcaMedicamentoListView.as_view(), name='marca_medicamento_list'),
    path('marca_medicamento/crear/', MarcaMedicamentoCreateView.as_view(), name='marca_medicamento_create'),
    path('marca_medicamento/<int:pk>/editar/', MarcaMedicamentoUpdateView.as_view(), name='marca_medicamento_update'),
    path('marca_medicamento/<int:pk>/eliminar/', MarcaMedicamentoDeleteView.as_view(), name='marca_medicamento_delete'),
    
    # ==================== URLs DE EMPLEADOS ====================
    path('empleados/', EmpleadoListView.as_view(), name='empleado_list'),
    path('empleados/crear/', EmpleadoCreateView.as_view(), name='empleado_create'),
    path('empleados/<int:pk>/editar/', EmpleadoUpdateView.as_view(), name='empleado_update'),
    path('empleados/<int:pk>/eliminar/', EmpleadoDeleteView.as_view(), name='empleado_delete'),
    
    # URLs de cargos
    path('cargos/', CargoListView.as_view(), name='cargo_list'),
    path('cargos/crear/', CargoCreateView.as_view(), name='cargo_create'),
    path('cargos/<int:pk>/editar/', CargoUpdateView.as_view(), name='cargo_update'),
    path('cargos/<int:pk>/eliminar/', CargoDeleteView.as_view(), name='cargo_delete'),
    
    # ==================== URLs DE DIAGNÓSTICOS ====================
    path('diagnosticos/', DiagnosticoListView.as_view(), name='diagnostico_list'),
    path('diagnosticos/crear/', DiagnosticoCreateView.as_view(), name='diagnostico_create'),
    path('diagnosticos/<int:pk>/editar/', DiagnosticoUpdateView.as_view(), name='diagnostico_update'),
    path('diagnosticos/<int:pk>/eliminar/', DiagnosticoDeleteView.as_view(), name='diagnostico_delete'),
    
    # ==================== URLs DE GASTOS ====================
    path('tipo_gasto/', TipoGastoListView.as_view(), name='tipo_gasto_list'),
    path('tipo_gasto/crear/', TipoGastoCreateView.as_view(), name='tipo_gasto_create'),
    path('tipo_gasto/<int:pk>/editar/', TipoGastoUpdateView.as_view(), name='tipo_gasto_update'),
    path('tipo_gasto/<int:pk>/eliminar/', TipoGastoDeleteView.as_view(), name='tipo_gasto_delete'),
    
    path('gasto_mensual/', GastoMensualListView.as_view(), name='gasto_mensual_list'),
    path('gasto_mensual/crear/', GastoMensualCreateView.as_view(), name='gasto_mensual_create'),
    path('gasto_mensual/<int:pk>/editar/', GastoMensualUpdateView.as_view(), name='gasto_mensual_update'),
    path('gasto_mensual/<int:pk>/eliminar/', GastoMensualDeleteView.as_view(), name='gasto_mensual_delete'),
    
    # ==================== URLs DE TIPOS DE SANGRE ====================
    path('tipo_sangre/', TipoSangreListView.as_view(), name='tipo_sangre_list'),
    path('tipo_sangre/crear/', TipoSangreCreateView.as_view(), name='tipo_sangre_create'),
    path('tipo_sangre/<int:pk>/editar/', TipoSangreUpdateView.as_view(), name='tipo_sangre_update'),
    path('tipo_sangre/<int:pk>/eliminar/', TipoSangreDeleteView.as_view(), name='tipo_sangre_delete'),
]