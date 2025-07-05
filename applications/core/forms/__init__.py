# Importar todos los formularios para disponibilizarlos en el paquete
from .paciente import PacienteForm, FotoPacienteForm
from .doctor import DoctorForm, EspecialidadForm
from .medicamento import MedicamentoForm, TipoMedicamentoForm, MarcaMedicamentoForm
from .general import (
    EmpleadoForm, CargoForm, DiagnosticoForm, 
    TipoGastoForm, GastoMensualForm, TipoSangreForm
)