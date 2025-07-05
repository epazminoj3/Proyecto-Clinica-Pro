# Importar todas las vistas desde los módulos correspondientes
from .pacientes import (
    PacienteListView,
    PacienteCreateView,
    PacienteUpdateView,
    PacienteDeleteView,
)

from .doctor import (
    DoctorListView,
    DoctorCreateView,
    DoctorUpdateView,
    DoctorDeleteView,
    EspecialidadListView,
    EspecialidadCreateView,
    EspecialidadUpdateView,
    EspecialidadDeleteView,
)

from .medicamento import (
    MedicamentoListView,
    MedicamentoCreateView,
    MedicamentoUpdateView,
    MedicamentoDeleteView,
    TipoMedicamentoListView,
    TipoMedicamentoCreateView,
    TipoMedicamentoUpdateView,
    TipoMedicamentoDeleteView,
    MarcaMedicamentoListView,
    MarcaMedicamentoCreateView,
    MarcaMedicamentoUpdateView,
    MarcaMedicamentoDeleteView,
)

from .general import (
    EmpleadoListView,
    EmpleadoCreateView,
    EmpleadoUpdateView,
    EmpleadoDeleteView,
    CargoListView,
    CargoCreateView,
    CargoUpdateView,
    CargoDeleteView,
    DiagnosticoListView,
    DiagnosticoCreateView,
    DiagnosticoUpdateView,
    DiagnosticoDeleteView,
    TipoGastoListView,
    TipoGastoCreateView,
    TipoGastoUpdateView,
    TipoGastoDeleteView,
    GastoMensualListView,
    GastoMensualCreateView,
    GastoMensualUpdateView,
    GastoMensualDeleteView,
    TipoSangreListView,
    TipoSangreCreateView,
    TipoSangreUpdateView,
    TipoSangreDeleteView,
)