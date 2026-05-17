from django.db import models
from django.contrib.auth.models import Group, Permission
import os
from django.contrib.contenttypes.models import ContentType
from applications.security.models import GroupModulePermission, Menu, Module, User
from applications.core.models import (
    Paciente, Doctor, Especialidad, Diagnostico, TipoSangre,
    Medicamento, TipoMedicamento, MarcaMedicamento,
    Empleado, Cargo, TipoGasto, GastoMensual
)
from applications.doctor.models import (
    HorarioAtencion, CitaMedica, Atencion, DetalleAtencion,
    ServiciosAdicionales, Pago, DetallePago
)

# ==================== CREAR MENÚS PRINCIPALES ====================

menu_clinico = Menu.objects.create(
    name='Sistema Clínico',
    icon='bi bi-hospital',
    order=1
)

menu_consultas_medicas = Menu.objects.create(
    name='Consultas Médicas',
    icon='bi bi-calendar-heart',
    order=2
)

menu_inventario = Menu.objects.create(
    name='Inventario',
    icon='bi bi-box',
    order=3
)

menu_auditores = Menu.objects.create(
    name='Auditores',
    icon='bi bi-gear',
    order=4
)

menu_personal = Menu.objects.create(
    name='Personal',
    icon='bi bi-people-fill',
    order=5
)

menu_finanzas = Menu.objects.create(
    name='Finanzas',
    icon='bi bi-currency-dollar',
    order=6
)

menu_servicios_adicionales = Menu.objects.create(
    name='Servicios y Pagos',
    icon='bi bi-credit-card',
    order=7
)

# ==================== CREAR MÓDULOS DE CORE ====================

modules_core = [
    # Módulos del Sistema Clínico
    Module(url='core/pacientes/', name='Gestión de Pacientes', menu=menu_clinico,
           description='Registro y gestión de pacientes', icon='bi bi-person-plus', order=1),
    Module(url='core/doctores/', name='Gestión de Doctores', menu=menu_clinico,
           description='Registro y gestión de doctores', icon='bi bi-person-badge', order=2),
    Module(url='core/especialidades/', name='Especialidades Médicas', menu=menu_clinico,
           description='Gestión de especialidades médicas', icon='bi bi-mortarboard', order=3),
    Module(url='core/diagnosticos/', name='Catálogo de Diagnósticos', menu=menu_clinico,
           description='Gestión de diagnósticos médicos', icon='bi bi-clipboard-pulse', order=4),
    Module(url='core/tipo_sangre/', name='Tipos de Sangre', menu=menu_clinico,
           description='Gestión de tipos de sangre', icon='bi bi-droplet', order=5),
    
    # Módulos de Inventario
    Module(url='core/medicamentos/', name='Medicamentos', menu=menu_inventario,
           description='Gestión de medicamentos', icon='bi bi-capsule', order=1),
    Module(url='core/tipo_medicamento/', name='Tipos de Medicamento', menu=menu_inventario,
           description='Clasificación de medicamentos', icon='bi bi-tags', order=2),
    Module(url='core/marca_medicamento/', name='Marcas de Medicamento', menu=menu_inventario,
           description='Gestión de marcas farmacéuticas', icon='bi bi-award', order=3),
    
    # Módulos de Personal
    Module(url='core/empleados/', name='Empleados', menu=menu_personal,
           description='Gestión de empleados', icon='bi bi-person-workspace', order=1),
    Module(url='core/cargos/', name='Cargos', menu=menu_personal,
           description='Gestión de cargos y roles', icon='bi bi-briefcase', order=2),
    
    # Módulos de Finanzas
    Module(url='core/tipo_gasto/', name='Tipos de Gasto', menu=menu_finanzas,
           description='Clasificación de gastos', icon='bi bi-list-ul', order=1),
    Module(url='core/gasto_mensual/', name='Gastos Mensuales', menu=menu_finanzas,
           description='Registro de gastos mensuales', icon='bi bi-receipt', order=2),
]

created_core_modules = Module.objects.bulk_create(modules_core)

# Asignar módulos de core a variables
(mod_pacientes, mod_doctores, mod_especialidades, mod_diagnosticos, mod_tipo_sangre,
 mod_medicamentos, mod_tipo_medicamento, mod_marca_medicamento,
 mod_empleados, mod_cargos, mod_tipo_gasto, mod_gasto_mensual) = created_core_modules

# ==================== CREAR MÓDULOS DE DOCTOR ====================

modules_doctor = [
    # Módulos de Consultas Médicas
    Module(url='doctor/horario/', name='Horarios de Atención', menu=menu_consultas_medicas,
           description='Gestión de horarios de atención médica', icon='bi bi-clock', order=1),
    Module(url='doctor/cita_medica/', name='Citas Médicas', menu=menu_consultas_medicas,
           description='Programación y gestión de citas médicas', icon='bi bi-calendar-check', order=2),
    Module(url='doctor/atenciones/', name='Atenciones Médicas', menu=menu_consultas_medicas,
           description='Registro de atenciones y consultas médicas', icon='bi bi-heart-pulse', order=3),
    Module(url='doctor/detalle_atencion/', name='Detalles de Atención', menu=menu_consultas_medicas,
           description='Prescripciones y detalles de tratamiento', icon='bi bi-prescription2', order=4),
    
    # Módulos de Servicios y Pagos
    Module(url='doctor/servicios_adicionales/', name='Servicios Adicionales', menu=menu_servicios_adicionales,
           description='Gestión de servicios adicionales y exámenes', icon='bi bi-plus-circle', order=1),
    Module(url='doctor/pago/', name='Pagos', menu=menu_servicios_adicionales,
           description='Control de pagos y facturación', icon='bi bi-credit-card', order=2),
    Module(url='doctor/detalle_pago/', name='Detalles de Pago', menu=menu_servicios_adicionales,
           description='Detalles y conceptos de facturación', icon='bi bi-receipt', order=3),
]

created_doctor_modules = Module.objects.bulk_create(modules_doctor)

# Asignar módulos de doctor a variables
(mod_horario, mod_cita_medica, mod_atenciones, mod_detalle_atencion,
 mod_servicios_adicionales, mod_pago, mod_detalle_pago) = created_doctor_modules

# ==================== CREAR USUARIOS Y GRUPOS ====================

# Crear Usuarios
user1 = User.objects.create_user(
    username='drgomez2',
    email='drgomezz@clinica.med',
    password=os.environ.get('SEED_USER1_PASSWORD', 'secure123!'),
    first_name='Carlos',
    last_name='Gómez',
    dni='0912345678',
    direction='Av. Principal 123, Guayaquil',
    phone='0991234567',
    is_staff=True
)

user2 = User.objects.create_user(
    username='asistente',
    email='asistente@clinica.med',
    password=os.environ.get('SEED_USER2_PASSWORD', 'asist2025!'),
    first_name='María',
    last_name='Sánchez',
    dni='0923456789',
    direction='Calle Secundaria 456, Guayaquil',
    phone='0982345678',
    is_staff=False
)

# Crear Grupos principales
group_medicos = Group.objects.create(name='Médicos')
group_asistentes = Group.objects.create(name='Asistentes')

# Crear Grupos de administradores
group_admin_clinico = Group.objects.create(name='Administradores Clínicos')
group_admin_inventario = Group.objects.create(name='Administradores de Inventario')
group_admin_personal = Group.objects.create(name='Administradores de Personal')
group_admin_finanzas = Group.objects.create(name='Administradores Financieros')
group_admin_consultas = Group.objects.create(name='Administradores de Consultas')
group_admin_servicios = Group.objects.create(name='Administradores de Servicios y Pagos')

# Agregar usuarios a grupos
user1.groups.add(group_medicos)
user2.groups.add(group_asistentes)

# ==================== OBTENER CONTENT TYPES ====================

# Content Types de Core
paciente_ct = ContentType.objects.get_for_model(Paciente)
doctor_ct = ContentType.objects.get_for_model(Doctor)
especialidad_ct = ContentType.objects.get_for_model(Especialidad)
diagnostico_ct = ContentType.objects.get_for_model(Diagnostico)
tipo_sangre_ct = ContentType.objects.get_for_model(TipoSangre)
medicamento_ct = ContentType.objects.get_for_model(Medicamento)
tipo_medicamento_ct = ContentType.objects.get_for_model(TipoMedicamento)
marca_medicamento_ct = ContentType.objects.get_for_model(MarcaMedicamento)
empleado_ct = ContentType.objects.get_for_model(Empleado)
cargo_ct = ContentType.objects.get_for_model(Cargo)
tipo_gasto_ct = ContentType.objects.get_for_model(TipoGasto)
gasto_mensual_ct = ContentType.objects.get_for_model(GastoMensual)

# Content Types de Doctor
horario_ct = ContentType.objects.get_for_model(HorarioAtencion)
cita_medica_ct = ContentType.objects.get_for_model(CitaMedica)
atencion_ct = ContentType.objects.get_for_model(Atencion)
detalle_atencion_ct = ContentType.objects.get_for_model(DetalleAtencion)
servicios_adicionales_ct = ContentType.objects.get_for_model(ServiciosAdicionales)
pago_ct = ContentType.objects.get_for_model(Pago)
detalle_pago_ct = ContentType.objects.get_for_model(DetallePago)

# ==================== CREAR PERMISOS PARA CORE ====================

def create_permissions_for_model(model_name, content_type):
    """Función para crear permisos estándar para un modelo"""
    perms = []
    for action in ['view', 'add', 'change', 'delete']:
        perm, created = Permission.objects.get_or_create(
            codename=f'{action}_{model_name.lower()}',
            name=f'Can {action} {model_name}',
            content_type=content_type
        )
        perms.append(perm)
    return perms

# Crear permisos para todos los modelos de Core
paciente_perms = create_permissions_for_model('Paciente', paciente_ct)
doctor_perms = create_permissions_for_model('Doctor', doctor_ct)
especialidad_perms = create_permissions_for_model('Especialidad', especialidad_ct)
diagnostico_perms = create_permissions_for_model('Diagnóstico', diagnostico_ct)
tipo_sangre_perms = create_permissions_for_model('TipoSangre', tipo_sangre_ct)
medicamento_perms = create_permissions_for_model('Medicamento', medicamento_ct)
tipo_medicamento_perms = create_permissions_for_model('TipoMedicamento', tipo_medicamento_ct)
marca_medicamento_perms = create_permissions_for_model('MarcaMedicamento', marca_medicamento_ct)
empleado_perms = create_permissions_for_model('Empleado', empleado_ct)
cargo_perms = create_permissions_for_model('Cargo', cargo_ct)
tipo_gasto_perms = create_permissions_for_model('TipoGasto', tipo_gasto_ct)
gasto_mensual_perms = create_permissions_for_model('GastoMensual', gasto_mensual_ct)

# ==================== CREAR PERMISOS PARA DOCTOR ====================

horario_perms = create_permissions_for_model('HorarioAtencion', horario_ct)
cita_medica_perms = create_permissions_for_model('CitaMedica', cita_medica_ct)
atencion_perms = create_permissions_for_model('Atencion', atencion_ct)
detalle_atencion_perms = create_permissions_for_model('DetalleAtencion', detalle_atencion_ct)
servicios_adicionales_perms = create_permissions_for_model('ServiciosAdicionales', servicios_adicionales_ct)
pago_perms = create_permissions_for_model('Pago', pago_ct)
detalle_pago_perms = create_permissions_for_model('DetallePago', detalle_pago_ct)

# ==================== ASIGNAR PERMISOS A MÓDULOS ====================

# Módulos de Core
mod_pacientes.permissions.add(*paciente_perms)
mod_doctores.permissions.add(*doctor_perms)
mod_especialidades.permissions.add(*especialidad_perms)
mod_diagnosticos.permissions.add(*diagnostico_perms)
mod_tipo_sangre.permissions.add(*tipo_sangre_perms)
mod_medicamentos.permissions.add(*medicamento_perms)
mod_tipo_medicamento.permissions.add(*tipo_medicamento_perms)
mod_marca_medicamento.permissions.add(*marca_medicamento_perms)
mod_empleados.permissions.add(*empleado_perms)
mod_cargos.permissions.add(*cargo_perms)
mod_tipo_gasto.permissions.add(*tipo_gasto_perms)
mod_gasto_mensual.permissions.add(*gasto_mensual_perms)

# Módulos de Doctor
mod_horario.permissions.add(*horario_perms)
mod_cita_medica.permissions.add(*cita_medica_perms)
mod_atenciones.permissions.add(*atencion_perms)
mod_detalle_atencion.permissions.add(*detalle_atencion_perms)
mod_servicios_adicionales.permissions.add(*servicios_adicionales_perms)
mod_pago.permissions.add(*pago_perms)
mod_detalle_pago.permissions.add(*detalle_pago_perms)

# ==================== CREAR GroupModulePermission PARA ADMINISTRADORES ====================

def create_admin_permissions(group, modules_perms_list):
    """Función para crear permisos de administrador para una lista de módulos"""
    for module, perms in modules_perms_list:
        gmp = GroupModulePermission.objects.create(group=group, module=module)
        gmp.permissions.add(*perms)

# Administradores Clínicos - acceso completo a módulos clínicos
create_admin_permissions(group_admin_clinico, [
    (mod_pacientes, paciente_perms),
    (mod_doctores, doctor_perms),
    (mod_especialidades, especialidad_perms),
    (mod_diagnosticos, diagnostico_perms),
    (mod_tipo_sangre, tipo_sangre_perms),
])

# Administradores de Inventario - acceso completo a módulos de inventario
create_admin_permissions(group_admin_inventario, [
    (mod_medicamentos, medicamento_perms),
    (mod_tipo_medicamento, tipo_medicamento_perms),
    (mod_marca_medicamento, marca_medicamento_perms),
])

# Administradores de Personal - acceso completo a módulos de personal
create_admin_permissions(group_admin_personal, [
    (mod_empleados, empleado_perms),
    (mod_cargos, cargo_perms),
])

# Administradores Financieros - acceso completo a módulos financieros
create_admin_permissions(group_admin_finanzas, [
    (mod_tipo_gasto, tipo_gasto_perms),
    (mod_gasto_mensual, gasto_mensual_perms),
])

# Administradores de Consultas - acceso completo a módulos de consultas
create_admin_permissions(group_admin_consultas, [
    (mod_horario, horario_perms),
    (mod_cita_medica, cita_medica_perms),
    (mod_atenciones, atencion_perms),
    (mod_detalle_atencion, detalle_atencion_perms),
])

# Administradores de Servicios y Pagos - acceso completo a módulos de servicios y pagos
create_admin_permissions(group_admin_servicios, [
    (mod_servicios_adicionales, servicios_adicionales_perms),
    (mod_pago, pago_perms),
    (mod_detalle_pago, detalle_pago_perms),
])

# ==================== PERMISOS PARA MÉDICOS ====================

# Los médicos necesitan acceso completo a varios módulos para su trabajo
create_admin_permissions(group_medicos, [
    # Acceso completo a pacientes y diagnósticos
    (mod_pacientes, paciente_perms),
    (mod_diagnosticos, diagnostico_perms),
    # Acceso completo a consultas médicas
    (mod_horario, horario_perms),
    (mod_cita_medica, cita_medica_perms),
    (mod_atenciones, atencion_perms),
    (mod_detalle_atencion, detalle_atencion_perms),
])

# Médicos pueden ver doctores y especialidades (limitado)
gmp_medicos_doctores = GroupModulePermission.objects.create(group=group_medicos, module=mod_doctores)
gmp_medicos_doctores.permissions.add(doctor_perms[0])  # solo view

gmp_medicos_especialidades = GroupModulePermission.objects.create(group=group_medicos, module=mod_especialidades)
gmp_medicos_especialidades.permissions.add(*especialidad_perms[:2])  # view y add

# Médicos pueden ver medicamentos pero no modificar stock
gmp_medicos_medicamentos = GroupModulePermission.objects.create(group=group_medicos, module=mod_medicamentos)
gmp_medicos_medicamentos.permissions.add(medicamento_perms[0])  # solo view

# Médicos pueden ver servicios adicionales y pagos (para referencia)
gmp_medicos_servicios_adicionales = GroupModulePermission.objects.create(group=group_medicos, module=mod_servicios_adicionales)
gmp_medicos_servicios_adicionales.permissions.add(servicios_adicionales_perms[0])  # solo view

gmp_medicos_pago = GroupModulePermission.objects.create(group=group_medicos, module=mod_pago)
gmp_medicos_pago.permissions.add(pago_perms[0])  # solo view

# ==================== PERMISOS PARA ASISTENTES ====================

# Los asistentes pueden gestionar horarios y citas
gmp_asistentes_horario = GroupModulePermission.objects.create(group=group_asistentes, module=mod_horario)
gmp_asistentes_horario.permissions.add(*horario_perms[:3])  # view, add, change (no delete)

gmp_asistentes_cita_medica = GroupModulePermission.objects.create(group=group_asistentes, module=mod_cita_medica)
gmp_asistentes_cita_medica.permissions.add(*cita_medica_perms)  # acceso completo a citas

# Los asistentes pueden ver pacientes pero no modificar información médica crítica
gmp_asistentes_pacientes = GroupModulePermission.objects.create(group=group_asistentes, module=mod_pacientes)
gmp_asistentes_pacientes.permissions.add(*paciente_perms[:2])  # view y add

# Los asistentes pueden ver atenciones pero no modificar
gmp_asistentes_atenciones = GroupModulePermission.objects.create(group=group_asistentes, module=mod_atenciones)
gmp_asistentes_atenciones.permissions.add(atencion_perms[0])  # solo view

# Los asistentes pueden gestionar servicios adicionales y pagos completamente
create_admin_permissions(group_asistentes, [
    (mod_servicios_adicionales, servicios_adicionales_perms),
    (mod_pago, pago_perms),
    (mod_detalle_pago, detalle_pago_perms),
])

print("✅ ORMs completos creados exitosamente!")
print("📋 Menús creados:")
print("   - Sistema Clínico")
print("   - Consultas Médicas") 
print("   - Inventario")
print("   - Auditores")
print("   - Personal")
print("   - Finanzas")
print("   - Servicios y Pagos")
print()
print("👥 Grupos creados:")
print("   - Médicos")
print("   - Asistentes")
print("   - Administradores Clínicos")
print("   - Administradores de Inventario")
print("   - Administradores de Personal")
print("   - Administradores Financieros")
print("   - Administradores de Consultas")
print("   - Administradores de Servicios y Pagos")
print()
print("🔐 Permisos asignados correctamente:")
print("   - Administradores: acceso completo a sus módulos respectivos")
print("   - Médicos: acceso completo a consultas, vista limitada a otros módulos")
print("   - Asistentes: gestión de citas y servicios, acceso limitado a pacientes")
print()
print("📌 Módulos creados para Core: 12")
print("📌 Módulos creados para Doctor: 7")
print("📌 Total de módulos: 19")
