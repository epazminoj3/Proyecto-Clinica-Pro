from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from applications.security.models import GroupModulePermission, Menu, Module
from applications.core.models import (
    Paciente, Doctor, Especialidad, Diagnostico, TipoSangre,
    Medicamento, TipoMedicamento, MarcaMedicamento,
    Empleado, Cargo, TipoGasto, GastoMensual
)


class Command(BaseCommand):
    help = 'Crea menus, modulos y permisos para las funcionalidades del core'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Iniciando creacion de ORMs para modulos del core...'))

        # Crear Menus adicionales para el sistema clinico
        menu_clinico, created = Menu.objects.get_or_create(
            name='Sistema Clinico',
            defaults={'icon': 'bi bi-hospital', 'order': 1}
        )

        menu_inventario, created = Menu.objects.get_or_create(
            name='Inventario',
            defaults={'icon': 'bi bi-box', 'order': 3}
        )

        menu_personal, created = Menu.objects.get_or_create(
            name='Personal',
            defaults={'icon': 'bi bi-people-fill', 'order': 5}
        )

        menu_finanzas, created = Menu.objects.get_or_create(
            name='Finanzas',
            defaults={'icon': 'bi bi-currency-dollar', 'order': 6}
        )

        # Crear modulos del core
        modules_data = [
            # Modulos del Sistema Clinico
            ('core/pacientes/', 'Gestion de Pacientes', menu_clinico, 'Registro y gestion de pacientes', 'bi bi-person-plus', 1),
            ('core/doctores/', 'Gestion de Doctores', menu_clinico, 'Registro y gestion de doctores', 'bi bi-person-badge', 2),
            ('core/especialidades/', 'Especialidades Medicas', menu_clinico, 'Gestion de especialidades medicas', 'bi bi-mortarboard', 3),
            ('core/diagnosticos/', 'Catalogo de Diagnosticos', menu_clinico, 'Gestion de diagnosticos medicos', 'bi bi-clipboard-pulse', 4),
            ('core/tipo_sangre/', 'Tipos de Sangre', menu_clinico, 'Gestion de tipos de sangre', 'bi bi-droplet', 5),
            
            # Modulos de Inventario
            ('core/medicamentos/', 'Medicamentos', menu_inventario, 'Gestion de medicamentos', 'bi bi-capsule', 1),
            ('core/tipo_medicamento/', 'Tipos de Medicamento', menu_inventario, 'Clasificacion de medicamentos', 'bi bi-tags', 2),
            ('core/marca_medicamento/', 'Marcas de Medicamento', menu_inventario, 'Gestion de marcas farmaceuticas', 'bi bi-award', 3),
            
            # Modulos de Personal
            ('core/empleados/', 'Empleados', menu_personal, 'Gestion de empleados', 'bi bi-person-workspace', 1),
            ('core/cargos/', 'Cargos', menu_personal, 'Gestion de cargos y roles', 'bi bi-briefcase', 2),
            
            # Modulos de Finanzas
            ('core/tipo_gasto/', 'Tipos de Gasto', menu_finanzas, 'Clasificacion de gastos', 'bi bi-list-ul', 1),
            ('core/gasto_mensual/', 'Gastos Mensuales', menu_finanzas, 'Registro de gastos mensuales', 'bi bi-receipt', 2),
        ]

        modules = {}
        for url, name, menu, description, icon, order in modules_data:
            module, created = Module.objects.get_or_create(
                url=url,
                defaults={
                    'name': name,
                    'menu': menu,
                    'description': description,
                    'icon': icon,
                    'order': order
                }
            )
            modules[url] = module
            if created:
                self.stdout.write(f'✓ Modulo creado: {name}')

        # Crear grupos de administradores
        groups_data = [
            ('Administradores Clinicos', 'Acceso completo a modulos clinicos'),
            ('Administradores de Inventario', 'Acceso completo a inventario'),
            ('Administradores de Personal', 'Acceso completo a personal'),
            ('Administradores Financieros', 'Acceso completo a finanzas'),
        ]

        groups = {}
        for group_name, description in groups_data:
            group, created = Group.objects.get_or_create(name=group_name)
            groups[group_name] = group
            if created:
                self.stdout.write(f'✓ Grupo creado: {group_name}')

        # Mapeo de modelos a Content Types
        models_ct = {
            'paciente': ContentType.objects.get_for_model(Paciente),
            'doctor': ContentType.objects.get_for_model(Doctor),
            'especialidad': ContentType.objects.get_for_model(Especialidad),
            'diagnostico': ContentType.objects.get_for_model(Diagnostico),
            'tiposangre': ContentType.objects.get_for_model(TipoSangre),
            'medicamento': ContentType.objects.get_for_model(Medicamento),
            'tipomedicamento': ContentType.objects.get_for_model(TipoMedicamento),
            'marcamedicamento': ContentType.objects.get_for_model(MarcaMedicamento),
            'empleado': ContentType.objects.get_for_model(Empleado),
            'cargo': ContentType.objects.get_for_model(Cargo),
            'tipogasto': ContentType.objects.get_for_model(TipoGasto),
            'gastomensual': ContentType.objects.get_for_model(GastoMensual),
        }

        # Crear permisos para todos los modelos
        permissions_by_model = {}
        for model_name, ct in models_ct.items():
            permissions_by_model[model_name] = []
            for action in ['view', 'add', 'change', 'delete']:
                perm, created = Permission.objects.get_or_create(
                    codename=f'{action}_{model_name}',
                    defaults={
                        'name': f'Can {action} {model_name}',
                        'content_type': ct
                    }
                )
                permissions_by_model[model_name].append(perm)

        self.stdout.write('✓ Permisos creados/verificados para todos los modelos')

        # Asignar permisos a modulos
        module_permissions_map = {
            'core/pacientes/': permissions_by_model['paciente'],
            'core/doctores/': permissions_by_model['doctor'],
            'core/especialidades/': permissions_by_model['especialidad'],
            'core/diagnosticos/': permissions_by_model['diagnostico'],
            'core/tipo_sangre/': permissions_by_model['tiposangre'],
            'core/medicamentos/': permissions_by_model['medicamento'],
            'core/tipo_medicamento/': permissions_by_model['tipomedicamento'],
            'core/marca_medicamento/': permissions_by_model['marcamedicamento'],
            'core/empleados/': permissions_by_model['empleado'],
            'core/cargos/': permissions_by_model['cargo'],
            'core/tipo_gasto/': permissions_by_model['tipogasto'],
            'core/gasto_mensual/': permissions_by_model['gastomensual'],
        }

        for url, perms in module_permissions_map.items():
            if url in modules:
                modules[url].permissions.set(perms)

        # Crear GroupModulePermission para administradores
        group_module_map = {
            'Administradores Clinicos': [
                'core/pacientes/', 'core/doctores/', 'core/especialidades/',
                'core/diagnosticos/', 'core/tipo_sangre/'
            ],
            'Administradores de Inventario': [
                'core/medicamentos/', 'core/tipo_medicamento/', 'core/marca_medicamento/'
            ],
            'Administradores de Personal': [
                'core/empleados/', 'core/cargos/'
            ],
            'Administradores Financieros': [
                'core/tipo_gasto/', 'core/gasto_mensual/'
            ],
        }

        for group_name, module_urls in group_module_map.items():
            group = groups[group_name]
            for module_url in module_urls:
                if module_url in modules:
                    module = modules[module_url]
                    gmp, created = GroupModulePermission.objects.get_or_create(
                        group=group,
                        module=module
                    )
                    if created:
                        # Asignar todos los permisos del modulo al grupo
                        gmp.permissions.set(module.permissions.all())
                        self.stdout.write(f'✓ Permisos asignados: {group_name} -> {module.name}')

        self.stdout.write(
            self.style.SUCCESS(
                '\n🎉 ORMs para modulos del core creados exitosamente!\n'
                '📋 Menus: Sistema Clinico, Inventario, Personal, Finanzas\n'
                '👥 Grupos: Administradores especializados por area\n'
                '🔐 Permisos: Asignados correctamente a cada grupo\n'
            )
        )
