from django.db import models
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from applications.security.models import GroupModulePermission, Menu, Module, User
from applications.core.models import (
    Paciente, Doctor, Especialidad, Diagnostico, TipoSangre,
    Medicamento, TipoMedicamento, MarcaMedicamento,
    Empleado, Cargo, TipoGasto, GastoMensual
)

# ==================== NUEVOS MODULOS DEL CORE ====================

# Crear Menus adicionales para el sistema clinico
menu_clinico = Menu.objects.create(
    name='Sistema Clinico',
    icon='bi bi-hospital',
    order=1
)

menu_inventario = Menu.objects.create(
    name='Inventario',
    icon='bi bi-box',
    order=3
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

# Crear Modulos del Sistema Clinico usando bulk_create
modules_core = [
    # Modulos del Sistema Clinico
    Module(url='core/pacientes/', name='Gestion de Pacientes', menu=menu_clinico,
           description='Registro y gestion de pacientes', icon='bi bi-person-plus', order=1),
    Module(url='core/doctores/', name='Gestion de Doctores', menu=menu_clinico,
           description='Registro y gestion de doctores', icon='bi bi-person-badge', order=2),
    Module(url='core/especialidades/', name='Especialidades Medicas', menu=menu_clinico,
           description='Gestion de especialidades medicas', icon='bi bi-mortarboard', order=3),
    Module(url='core/diagnosticos/', name='Catalogo de Diagnosticos', menu=menu_clinico,
           description='Gestion de diagnosticos medicos', icon='bi bi-clipboard-pulse', order=4),
    Module(url='core/tipo_sangre/', name='Tipos de Sangre', menu=menu_clinico,
           description='Gestion de tipos de sangre', icon='bi bi-droplet', order=5),
    
    # Modulos de Inventario
    Module(url='core/medicamentos/', name='Medicamentos', menu=menu_inventario,
           description='Gestion de medicamentos', icon='bi bi-capsule', order=1),
    Module(url='core/tipo_medicamento/', name='Tipos de Medicamento', menu=menu_inventario,
           description='Clasificacion de medicamentos', icon='bi bi-tags', order=2),
    Module(url='core/marca_medicamento/', name='Marcas de Medicamento', menu=menu_inventario,
           description='Gestion de marcas farmaceuticas', icon='bi bi-award', order=3),
    
    # Modulos de Personal
    Module(url='core/empleados/', name='Empleados', menu=menu_personal,
           description='Gestion de empleados', icon='bi bi-person-workspace', order=1),
    Module(url='core/cargos/', name='Cargos', menu=menu_personal,
           description='Gestion de cargos y roles', icon='bi bi-briefcase', order=2),
    
    # Modulos de Finanzas
    Module(url='core/tipo_gasto/', name='Tipos de Gasto', menu=menu_finanzas,
           description='Clasificacion de gastos', icon='bi bi-list-ul', order=1),
    Module(url='core/gasto_mensual/', name='Gastos Mensuales', menu=menu_finanzas,
           description='Registro de gastos mensuales', icon='bi bi-receipt', order=2),
]

created_core_modules = Module.objects.bulk_create(modules_core)

# Asignar modulos a variables para facilitar el manejo
(mod_pacientes, mod_doctores, mod_especialidades, mod_diagnosticos, mod_tipo_sangre,
 mod_medicamentos, mod_tipo_medicamento, mod_marca_medicamento,
 mod_empleados, mod_cargos, mod_tipo_gasto, mod_gasto_mensual) = created_core_modules

# Crear Grupo de Administradores Clinicos
group_admin_clinico = Group.objects.create(name='Administradores Clinicos')
group_admin_inventario = Group.objects.create(name='Administradores de Inventario')
group_admin_personal = Group.objects.create(name='Administradores de Personal')
group_admin_finanzas = Group.objects.create(name='Administradores Financieros')

# Content Types
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

# ==================== PERMISOS PARA PACIENTES ====================
paciente_perms = []
for action in ['view', 'add', 'change', 'delete']:
    perm, created = Permission.objects.get_or_create(
        codename=f'{action}_paciente',
        name=f'Can {action} Paciente',
        content_type=paciente_ct
    )
    paciente_perms.append(perm)

# ==================== PERMISOS PARA DOCTORES ====================
doctor_perms = []
for action in ['view', 'add', 'change', 'delete']:
    perm, created = Permission.objects.get_or_create(
        codename=f'{action}_doctor',
        name=f'Can {action} Doctor',
        content_type=doctor_ct
    )
    doctor_perms.append(perm)

# ==================== PERMISOS PARA ESPECIALIDADES ====================
especialidad_perms = []
for action in ['view', 'add', 'change', 'delete']:
    perm, created = Permission.objects.get_or_create(
        codename=f'{action}_especialidad',
        name=f'Can {action} Especialidad',
        content_type=especialidad_ct
    )
    especialidad_perms.append(perm)

# ==================== PERMISOS PARA DIAGNOSTICOS ====================
diagnostico_perms = []
for action in ['view', 'add', 'change', 'delete']:
    perm, created = Permission.objects.get_or_create(
        codename=f'{action}_diagnostico',
        name=f'Can {action} Diagnostico',
        content_type=diagnostico_ct
    )
    diagnostico_perms.append(perm)

# ==================== PERMISOS PARA TIPOS DE SANGRE ====================
tipo_sangre_perms = []
for action in ['view', 'add', 'change', 'delete']:
    perm, created = Permission.objects.get_or_create(
        codename=f'{action}_tiposangre',
        name=f'Can {action} Tipo de Sangre',
        content_type=tipo_sangre_ct
    )
    tipo_sangre_perms.append(perm)

# ==================== PERMISOS PARA MEDICAMENTOS ====================
medicamento_perms = []
for action in ['view', 'add', 'change', 'delete']:
    perm, created = Permission.objects.get_or_create(
        codename=f'{action}_medicamento',
        name=f'Can {action} Medicamento',
        content_type=medicamento_ct
    )
    medicamento_perms.append(perm)

# ==================== PERMISOS PARA TIPOS DE MEDICAMENTO ====================
tipo_medicamento_perms = []
for action in ['view', 'add', 'change', 'delete']:
    perm, created = Permission.objects.get_or_create(
        codename=f'{action}_tipomedicamento',
        name=f'Can {action} Tipo de Medicamento',
        content_type=tipo_medicamento_ct
    )
    tipo_medicamento_perms.append(perm)

# ==================== PERMISOS PARA MARCAS DE MEDICAMENTO ====================
marca_medicamento_perms = []
for action in ['view', 'add', 'change', 'delete']:
    perm, created = Permission.objects.get_or_create(
        codename=f'{action}_marcamedicamento',
        name=f'Can {action} Marca de Medicamento',
        content_type=marca_medicamento_ct
    )
    marca_medicamento_perms.append(perm)

# ==================== PERMISOS PARA EMPLEADOS ====================
empleado_perms = []
for action in ['view', 'add', 'change', 'delete']:
    perm, created = Permission.objects.get_or_create(
        codename=f'{action}_empleado',
        name=f'Can {action} Empleado',
        content_type=empleado_ct
    )
    empleado_perms.append(perm)

# ==================== PERMISOS PARA CARGOS ====================
cargo_perms = []
for action in ['view', 'add', 'change', 'delete']:
    perm, created = Permission.objects.get_or_create(
        codename=f'{action}_cargo',
        name=f'Can {action} Cargo',
        content_type=cargo_ct
    )
    cargo_perms.append(perm)

# ==================== PERMISOS PARA TIPOS DE GASTO ====================
tipo_gasto_perms = []
for action in ['view', 'add', 'change', 'delete']:
    perm, created = Permission.objects.get_or_create(
        codename=f'{action}_tipogasto',
        name=f'Can {action} Tipo de Gasto',
        content_type=tipo_gasto_ct
    )
    tipo_gasto_perms.append(perm)

# ==================== PERMISOS PARA GASTOS MENSUALES ====================
gasto_mensual_perms = []
for action in ['view', 'add', 'change', 'delete']:
    perm, created = Permission.objects.get_or_create(
        codename=f'{action}_gastomensual',
        name=f'Can {action} Gasto Mensual',
        content_type=gasto_mensual_ct
    )
    gasto_mensual_perms.append(perm)

# ==================== ASIGNAR PERMISOS A MODULOS ====================
# Modulos Clinicos
mod_pacientes.permissions.add(*paciente_perms)
mod_doctores.permissions.add(*doctor_perms)
mod_especialidades.permissions.add(*especialidad_perms)
mod_diagnosticos.permissions.add(*diagnostico_perms)
mod_tipo_sangre.permissions.add(*tipo_sangre_perms)

# Modulos de Inventario
mod_medicamentos.permissions.add(*medicamento_perms)
mod_tipo_medicamento.permissions.add(*tipo_medicamento_perms)
mod_marca_medicamento.permissions.add(*marca_medicamento_perms)

# Modulos de Personal
mod_empleados.permissions.add(*empleado_perms)
mod_cargos.permissions.add(*cargo_perms)

# Modulos de Finanzas
mod_tipo_gasto.permissions.add(*tipo_gasto_perms)
mod_gasto_mensual.permissions.add(*gasto_mensual_perms)

# ==================== CREAR GroupModulePermission PARA ADMINISTRADORES ====================

# Administradores Clinicos - acceso completo a modulos clinicos
gmp_admin_pacientes = GroupModulePermission.objects.create(group=group_admin_clinico, module=mod_pacientes)
gmp_admin_pacientes.permissions.add(*paciente_perms)

gmp_admin_doctores = GroupModulePermission.objects.create(group=group_admin_clinico, module=mod_doctores)
gmp_admin_doctores.permissions.add(*doctor_perms)

gmp_admin_especialidades = GroupModulePermission.objects.create(group=group_admin_clinico, module=mod_especialidades)
gmp_admin_especialidades.permissions.add(*especialidad_perms)

gmp_admin_diagnosticos = GroupModulePermission.objects.create(group=group_admin_clinico, module=mod_diagnosticos)
gmp_admin_diagnosticos.permissions.add(*diagnostico_perms)

gmp_admin_tipo_sangre = GroupModulePermission.objects.create(group=group_admin_clinico, module=mod_tipo_sangre)
gmp_admin_tipo_sangre.permissions.add(*tipo_sangre_perms)

# Administradores de Inventario - acceso completo a modulos de inventario
gmp_admin_medicamentos = GroupModulePermission.objects.create(group=group_admin_inventario, module=mod_medicamentos)
gmp_admin_medicamentos.permissions.add(*medicamento_perms)

gmp_admin_tipo_medicamento = GroupModulePermission.objects.create(group=group_admin_inventario, module=mod_tipo_medicamento)
gmp_admin_tipo_medicamento.permissions.add(*tipo_medicamento_perms)

gmp_admin_marca_medicamento = GroupModulePermission.objects.create(group=group_admin_inventario, module=mod_marca_medicamento)
gmp_admin_marca_medicamento.permissions.add(*marca_medicamento_perms)

# Administradores de Personal - acceso completo a modulos de personal
gmp_admin_empleados = GroupModulePermission.objects.create(group=group_admin_personal, module=mod_empleados)
gmp_admin_empleados.permissions.add(*empleado_perms)

gmp_admin_cargos = GroupModulePermission.objects.create(group=group_admin_personal, module=mod_cargos)
gmp_admin_cargos.permissions.add(*cargo_perms)

# Administradores Financieros - acceso completo a modulos financieros
gmp_admin_tipo_gasto = GroupModulePermission.objects.create(group=group_admin_finanzas, module=mod_tipo_gasto)
gmp_admin_tipo_gasto.permissions.add(*tipo_gasto_perms)

gmp_admin_gasto_mensual = GroupModulePermission.objects.create(group=group_admin_finanzas, module=mod_gasto_mensual)
gmp_admin_gasto_mensual.permissions.add(*gasto_mensual_perms)

print("ORMs para modulos del core creados exitosamente!")
print("Menus creados: Sistema Clinico, Inventario, Personal, Finanzas")
print("Grupos creados: Administradores Clinicos, de Inventario, Personal y Financieros")
print("Permisos asignados correctamente a cada grupo segun su especialidad")
