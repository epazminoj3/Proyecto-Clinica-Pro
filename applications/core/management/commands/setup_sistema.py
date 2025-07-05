#!/usr/bin/env python
# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.db import transaction
from decimal import Decimal
from datetime import datetime, timedelta, date, time
import random

# Importar todos los modelos necesarios
from applications.core.models import (
    TipoSangre, Paciente, Especialidad, Doctor, Cargo, Empleado,
    TipoMedicamento, MarcaMedicamento, Medicamento, Diagnostico,
    TipoGasto, GastoMensual
)
from applications.doctor.models import (
    HorarioAtencion, CitaMedica, Atencion, DetalleAtencion,
    ServiciosAdicionales, Pago, DetallePago
)
from applications.security.models import Module, GroupModulePermission, User, Menu
from django.contrib.auth.models import Permission, Group
from django.contrib.contenttypes.models import ContentType

# Importar choices
from applications.doctor.utils.cita_medica import EstadoCitaChoices
from applications.doctor.utils.doctor import DiaSemanaChoices
from applications.doctor.utils.pago import MetodoPagoChoices, EstadoPagoChoices
from applications.core.utils.medicamento import ViaAdministracion
from applications.core.utils.paciente import EstadoCivilChoices, SexoChoices
from django.utils import timezone


class Command(BaseCommand):
    help = 'Instala el sistema completo con módulos, grupos, permisos y datos de ejemplo'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Elimina todos los datos existentes antes de crear nuevos',
        )
        parser.add_argument(
            '--hard-reset',
            action='store_true',
            help='Reset completo incluyendo IDs desde 1 (ELIMINA TODO)',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🏥 INSTALANDO SISTEMA CLÍNICO COMPLETO'))
        self.stdout.write('=' * 60)
        
        try:
            with transaction.atomic():
                if options['reset'] or options['hard_reset']:
                    self.limpiar_datos()
                
                if options['hard_reset']:
                    self.stdout.write(self.style.WARNING('⚠️  REALIZANDO RESET COMPLETO DE IDs'))
                
                # 1. Crear módulos y estructura de seguridad
                self.crear_menus()
                self.crear_modulos()
                self.crear_grupos()
                self.asignar_permisos()
                
                # 2. Crear datos base
                self.crear_tipos_sangre()
                self.crear_especialidades()
                self.crear_cargos()
                self.crear_tipos_medicamentos()
                self.crear_marcas_medicamentos()
                self.crear_medicamentos()
                self.crear_diagnosticos()
                self.crear_tipos_gastos()
                
                # 3. Crear personas
                self.crear_doctores()
                self.crear_empleados()
                self.crear_pacientes()
                
                # 4. Crear datos operativos
                self.crear_gastos_mensuales()
                self.crear_horarios_atencion()
                self.crear_servicios_adicionales()
                
                # 5. Crear datos médicos
                self.crear_citas_medicas()
                self.crear_atenciones()
                self.crear_detalles_atencion()
                self.crear_pagos()
                self.crear_detalles_pago()
                
                self.mostrar_resumen()
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error: {str(e)}'))
            raise

    def limpiar_datos(self):
        """Limpia datos existentes"""
        self.stdout.write('🧹 Limpiando datos existentes...')
        
        # Limpiar en orden inverso de dependencias
        DetallePago.objects.all().delete()
        Pago.objects.all().delete()
        DetalleAtencion.objects.all().delete()
        Atencion.objects.all().delete()
        CitaMedica.objects.all().delete()
        HorarioAtencion.objects.all().delete()
        
        GastoMensual.objects.all().delete()
        Empleado.objects.all().delete()
        Doctor.objects.filter(ruc__startswith='17').delete()
        Paciente.objects.filter(cedula_ecuatoriana__startswith='17').delete()
        
        # Limpiar también security
        GroupModulePermission.objects.all().delete()
        Module.objects.all().delete()
        Menu.objects.all().delete()
        Group.objects.all().delete()
        
        # Limpiar logs del admin de Django para evitar conflictos de ID
        from django.contrib.admin.models import LogEntry
        LogEntry.objects.all().delete()
        
        # Resetear secuencias de ID para que empiecen desde 1
        self.resetear_secuencias_id()
        
        self.stdout.write(self.style.SUCCESS('✅ Datos limpiados'))

    def resetear_secuencias_id(self):
        """Resetea las secuencias de ID para que empiecen desde 1"""
        self.stdout.write('🔄 Reseteando IDs...')
        
        from django.db import connection
        
        with connection.cursor() as cursor:
            # Para SQLite
            if connection.vendor == 'sqlite':
                self.stdout.write('  💾 Detectado SQLite - Reseteando secuencias...')
                try:
                    # Limpiar completamente la tabla sqlite_sequence
                    cursor.execute("DELETE FROM sqlite_sequence")
                    self.stdout.write('  ✅ Secuencias SQLite reseteadas')
                except Exception as e:
                    self.stdout.write(f'  ❌ Error reseteando SQLite: {e}')
            
            # Para PostgreSQL
            elif connection.vendor == 'postgresql':
                self.stdout.write('  🐘 Detectado PostgreSQL - Reseteando secuencias...')
                try:
                    # Obtener TODAS las secuencias que terminan en _id_seq (incluye Django admin)
                    cursor.execute("""
                        SELECT sequencename 
                        FROM pg_sequences 
                        WHERE sequencename LIKE %s
                        ORDER BY sequencename
                    """, ['%_id_seq'])
                    
                    secuencias = cursor.fetchall()
                    self.stdout.write(f'  📋 Encontradas {len(secuencias)} secuencias')
                    
                    # También resetear secuencias específicas de Django que no terminan en _id_seq
                    secuencias_adicionales = [
                        'django_admin_log_id_seq',
                        'django_content_type_id_seq', 
                        'auth_permission_id_seq',
                        'django_migrations_id_seq',
                        'django_session_session_key_seq'  # si existe
                    ]
                    
                    # Verificar y resetear secuencias adicionales
                    for seq_adicional in secuencias_adicionales:
                        cursor.execute("""
                            SELECT sequencename 
                            FROM pg_sequences 
                            WHERE sequencename = %s
                        """, [seq_adicional])
                        
                        if cursor.fetchone():
                            secuencias.append((seq_adicional,))
                    
                    # Resetear todas las secuencias encontradas
                    for (seq_name,) in secuencias:
                        try:
                            cursor.execute(f"ALTER SEQUENCE {seq_name} RESTART WITH 1")
                            self.stdout.write(f'  ✅ {seq_name} → reseteada a 1')
                        except Exception as e:
                            self.stdout.write(f'  ❌ Error en {seq_name}: {e}')
                            
                    if not secuencias:
                        self.stdout.write('  ⚠️  No se encontraron secuencias para resetear')
                        
                except Exception as e:
                    self.stdout.write(f'  ❌ Error obteniendo secuencias PostgreSQL: {e}')
            
            # Para MySQL
            elif connection.vendor == 'mysql':
                self.stdout.write('  🐬 Detectado MySQL - Reseteando AUTO_INCREMENT...')
                # Lista de tablas principales
                tablas_mysql = [
                    'auth_user', 'auth_group', 'security_module', 'security_menu',
                    'core_tiposangre', 'core_especialidad', 'core_cargo', 'core_empleado',
                    'core_doctor', 'core_paciente', 'core_tipomedicamento', 'core_marcamedicamento',
                    'core_medicamento', 'core_tipogasto', 'core_gastomensual', 'core_diagnostico',
                    'doctor_serviciosadicionales', 'doctor_horarioatencion', 'doctor_citamedica',
                    'doctor_detalleatencion', 'doctor_detallepago', 'doctor_pago', 'doctor_atencion'
                ]
                
                for tabla in tablas_mysql:
                    try:
                        cursor.execute(f"ALTER TABLE {tabla} AUTO_INCREMENT = 1")
                        self.stdout.write(f'  ✅ {tabla} → reseteada a 1')
                    except Exception as e:
                        continue
            
            else:
                self.stdout.write(f'  ❌ Base de datos no soportada: {connection.vendor}')
        
        self.stdout.write(self.style.SUCCESS('✅ IDs reseteados - empezarán desde 1'))

    def reset_completo_base_datos(self):
        """Reset más agresivo eliminando completamente las tablas (CUIDADO!)"""
        self.stdout.write(self.style.WARNING('⚠️  RESET COMPLETO DE BASE DE DATOS'))
        
        from django.core.management import call_command
        from django.db import connection
        
        try:
            # Eliminar todas las migraciones aplicadas (excepto la inicial)
            with connection.cursor() as cursor:
                if connection.vendor == 'sqlite':
                    # Para SQLite, simplemente eliminamos el archivo de base de datos
                    self.stdout.write('🗑️  Para SQLite: elimine manualmente el archivo db.sqlite3')
                else:
                    # Para otras bases de datos, eliminamos las tablas
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                    tablas = cursor.fetchall()
                    for tabla in tablas:
                        if tabla[0] != 'sqlite_sequence':
                            cursor.execute(f"DROP TABLE IF EXISTS {tabla[0]}")
            
            # Recrear migraciones
            self.stdout.write('🔄 Recreando migraciones...')
            call_command('migrate', verbosity=0)
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error en reset completo: {str(e)}'))
            self.stdout.write('💡 Ejecute manualmente: rm db.sqlite3 && python manage.py migrate')

    def crear_menus(self):
        """Crear menús del sistema"""
        self.stdout.write('📂 Creando menús...')
        
        menus = [
            {'name': 'Core', 'icon': 'fas fa-heart', 'order': 1},
            {'name': 'Doctor', 'icon': 'fas fa-user-md', 'order': 2},
            {'name': 'Security', 'icon': 'fas fa-shield-alt', 'order': 3},
        ]
        
        for data in menus:
            Menu.objects.get_or_create(
                name=data['name'],
                defaults=data
            )
        
        self.stdout.write(self.style.SUCCESS(f'✅ Creados {len(menus)} menús'))

    def crear_modulos(self):
        """Crear módulos del sistema"""
        self.stdout.write('📦 Creando módulos...')
        
        # Obtener menús
        menu_core = Menu.objects.get(name='Core')
        menu_doctor = Menu.objects.get(name='Doctor')
        menu_security = Menu.objects.get(name='Security')
        
        modulos = [
            # CORE
            {'name': 'Pacientes', 'url': '/core/pacientes/', 'icon': 'fas fa-user-injured', 'menu': menu_core, 'order': 1},
            {'name': 'Doctores', 'url': '/core/doctores/', 'icon': 'fas fa-user-md', 'menu': menu_core, 'order': 2},
            {'name': 'Empleados', 'url': '/core/empleados/', 'icon': 'fas fa-users', 'menu': menu_core, 'order': 3},
            {'name': 'Especialidades', 'url': '/core/especialidades/', 'icon': 'fas fa-stethoscope', 'menu': menu_core, 'order': 4},
            {'name': 'Cargos', 'url': '/core/cargos/', 'icon': 'fas fa-id-badge', 'menu': menu_core, 'order': 5},
            {'name': 'Medicamentos', 'url': '/core/medicamentos/', 'icon': 'fas fa-pills', 'menu': menu_core, 'order': 6},
            {'name': 'Tipos de Medicamento', 'url': '/core/tipo_medicamento/', 'icon': 'fas fa-prescription-bottle', 'menu': menu_core, 'order': 7},
            {'name': 'Marcas de Medicamento', 'url': '/core/marca_medicamento/', 'icon': 'fas fa-industry', 'menu': menu_core, 'order': 8},
            {'name': 'Diagnósticos', 'url': '/core/diagnosticos/', 'icon': 'fas fa-diagnoses', 'menu': menu_core, 'order': 9},
            {'name': 'Tipos de Sangre', 'url': '/core/tipo_sangre/', 'icon': 'fas fa-tint', 'menu': menu_core, 'order': 10},
            {'name': 'Tipos de Gasto', 'url': '/core/tipo_gasto/', 'icon': 'fas fa-tags', 'menu': menu_core, 'order': 11},
            {'name': 'Gastos Mensuales', 'url': '/core/gasto_mensual/', 'icon': 'fas fa-money-bill-wave', 'menu': menu_core, 'order': 12},
            
            # DOCTOR
            {'name': 'Horarios de Atención', 'url': '/doctor/horario/', 'icon': 'fas fa-clock', 'menu': menu_doctor, 'order': 1},
            {'name': 'Citas Médicas', 'url': '/doctor/cita_medica/', 'icon': 'fas fa-calendar-check', 'menu': menu_doctor, 'order': 2},
            {'name': 'Atenciones', 'url': '/doctor/atenciones/', 'icon': 'fas fa-notes-medical', 'menu': menu_doctor, 'order': 3},
            {'name': 'Detalles de Atención', 'url': '/doctor/detalle_atencion/', 'icon': 'fas fa-prescription', 'menu': menu_doctor, 'order': 4},
            {'name': 'Servicios Adicionales', 'url': '/doctor/servicios_adicionales/', 'icon': 'fas fa-plus-square', 'menu': menu_doctor, 'order': 5},
            {'name': 'Pagos', 'url': '/doctor/pago/', 'icon': 'fas fa-credit-card', 'menu': menu_doctor, 'order': 6},
            {'name': 'Detalles de Pago', 'url': '/doctor/detalle_pago/', 'icon': 'fas fa-receipt', 'menu': menu_doctor, 'order': 7},
            
            # SECURITY
            {'name': 'Usuarios', 'url': '/security/usuarios_list/', 'icon': 'fas fa-users-cog', 'menu': menu_security, 'order': 1},
            {'name': 'Grupos', 'url': '/security/group_list/', 'icon': 'fas fa-user-friends', 'menu': menu_security, 'order': 2},
            {'name': 'Permisos', 'url': '/security/group_permission_list/', 'icon': 'fas fa-shield-alt', 'menu': menu_security, 'order': 3},
            {'name': 'Módulos', 'url': '/security/module_list/', 'icon': 'fas fa-cubes', 'menu': menu_security, 'order': 4},
            {'name': 'Menús', 'url': '/security/menu_list/', 'icon': 'fas fa-list', 'menu': menu_security, 'order': 5},
        ]
        
        for data in modulos:
            Module.objects.get_or_create(
                name=data['name'],
                defaults={
                    'url': data['url'],
                    'icon': data['icon'],
                    'menu': data['menu'],
                    'order': data['order'],
                    'is_active': True
                }
            )
        
        self.stdout.write(self.style.SUCCESS(f'✅ Creados {len(modulos)} módulos'))

    def crear_grupos(self):
        """Crear grupos de usuarios"""
        self.stdout.write('👥 Creando grupos...')
        
        grupos = [
            'Administradores',
            'Médicos', 
            'Asistentes',
            'Recepcionistas'
        ]
        
        for nombre in grupos:
            Group.objects.get_or_create(name=nombre)
        
        self.stdout.write(self.style.SUCCESS(f'✅ Creados {len(grupos)} grupos'))

    def asignar_permisos(self):
        """Asignar permisos a grupos"""
        self.stdout.write('🔐 Asignando permisos...')
        
        # Primero asignar permisos específicos a módulos
        self.asignar_permisos_a_modulos()
        
        # Luego asignar permisos de Django a grupos
        self.asignar_permisos_a_grupos()
        
        # Finalmente asignar módulos a grupos
        self.asignar_modulos_a_grupos()
        
        self.stdout.write(self.style.SUCCESS('✅ Permisos asignados'))

    def asignar_permisos_a_modulos(self):
        """Asignar permisos específicos de Django a cada módulo"""
        self.stdout.write('📋 Asignando permisos a módulos...')
        
        # Mapeo de módulos con sus permisos específicos
        modulos_permisos = {
            # CORE - Pacientes
            'Pacientes': [
                'core.add_paciente', 'core.change_paciente', 'core.delete_paciente', 'core.view_paciente'
            ],
            'Doctores': [
                'core.add_doctor', 'core.change_doctor', 'core.delete_doctor', 'core.view_doctor'
            ],
            'Empleados': [
                'core.add_empleado', 'core.change_empleado', 'core.delete_empleado', 'core.view_empleado'
            ],
            'Especialidades': [
                'core.add_especialidad', 'core.change_especialidad', 'core.delete_especialidad', 'core.view_especialidad'
            ],
            'Cargos': [
                'core.add_cargo', 'core.change_cargo', 'core.delete_cargo', 'core.view_cargo'
            ],
            'Medicamentos': [
                'core.add_medicamento', 'core.change_medicamento', 'core.delete_medicamento', 'core.view_medicamento'
            ],
            'Tipos de Medicamento': [
                'core.add_tipomedicamento', 'core.change_tipomedicamento', 'core.delete_tipomedicamento', 'core.view_tipomedicamento'
            ],
            'Marcas de Medicamento': [
                'core.add_marcamedicamento', 'core.change_marcamedicamento', 'core.delete_marcamedicamento', 'core.view_marcamedicamento'
            ],
            'Diagnósticos': [
                'core.add_diagnostico', 'core.change_diagnostico', 'core.delete_diagnostico', 'core.view_diagnostico'
            ],
            'Tipos de Sangre': [
                'core.add_tiposangre', 'core.change_tiposangre', 'core.delete_tiposangre', 'core.view_tiposangre'
            ],
            'Tipos de Gasto': [
                'core.add_tipogasto', 'core.change_tipogasto', 'core.delete_tipogasto', 'core.view_tipogasto'
            ],
            'Gastos Mensuales': [
                'core.add_gastomensual', 'core.change_gastomensual', 'core.delete_gastomensual', 'core.view_gastomensual'
            ],
            
            # DOCTOR
            'Horarios de Atención': [
                'doctor.add_horarioatencion', 'doctor.change_horarioatencion', 'doctor.delete_horarioatencion', 'doctor.view_horarioatencion'
            ],
            'Citas Médicas': [
                'doctor.add_citamedica', 'doctor.change_citamedica', 'doctor.delete_citamedica', 'doctor.view_citamedica'
            ],
            'Atenciones': [
                'doctor.add_atencion', 'doctor.change_atencion', 'doctor.delete_atencion', 'doctor.view_atencion'
            ],
            'Detalles de Atención': [
                'doctor.add_detalleatencion', 'doctor.change_detalleatencion', 'doctor.delete_detalleatencion', 'doctor.view_detalleatencion'
            ],
            'Servicios Adicionales': [
                'doctor.add_serviciosadicionales', 'doctor.change_serviciosadicionales', 'doctor.delete_serviciosadicionales', 'doctor.view_serviciosadicionales'
            ],
            'Pagos': [
                'doctor.add_pago', 'doctor.change_pago', 'doctor.delete_pago', 'doctor.view_pago'
            ],
            'Detalles de Pago': [
                'doctor.add_detallepago', 'doctor.change_detallepago', 'doctor.delete_detallepago', 'doctor.view_detallepago'
            ],
            
            # SECURITY
            'Usuarios': [
                'auth.add_user', 'auth.change_user', 'auth.delete_user', 'auth.view_user'
            ],
            'Grupos': [
                'auth.add_group', 'auth.change_group', 'auth.delete_group', 'auth.view_group'
            ],
            'Permisos': [
                'auth.add_permission', 'auth.change_permission', 'auth.delete_permission', 'auth.view_permission',
                'security.add_groupmodulepermission', 'security.change_groupmodulepermission', 'security.delete_groupmodulepermission', 'security.view_groupmodulepermission'
            ],
            'Módulos': [
                'security.add_module', 'security.change_module', 'security.delete_module', 'security.view_module'
            ],
            'Menús': [
                'security.add_menu', 'security.change_menu', 'security.delete_menu', 'security.view_menu'
            ],
        }
        
        # Asignar permisos a cada módulo
        for nombre_modulo, permisos_codenames in modulos_permisos.items():
            modulo = Module.objects.filter(name=nombre_modulo).first()
            if modulo:
                permisos_validos = []
                for perm_codename in permisos_codenames:
                    try:
                        app_label, codename = perm_codename.split('.')
                        permission = Permission.objects.get(
                            content_type__app_label=app_label,
                            codename=codename
                        )
                        permisos_validos.append(permission)
                    except Permission.DoesNotExist:
                        self.stdout.write(
                            self.style.WARNING(f'⚠️  Permiso no encontrado: {perm_codename}')
                        )
                        continue
                
                # Asignar permisos al módulo
                modulo.permissions.set(permisos_validos)
                self.stdout.write(f'   ✅ {nombre_modulo}: {len(permisos_validos)} permisos asignados')

    def asignar_permisos_a_grupos(self):
        """Asignar permisos específicos de Django a cada grupo"""
        self.stdout.write('👥 Asignando permisos a grupos...')
        
        # Obtener grupos
        admin_group = Group.objects.get(name='Administradores')
        medicos_group = Group.objects.get(name='Médicos')
        asistentes_group = Group.objects.get(name='Asistentes')
        recepcionistas_group = Group.objects.get(name='Recepcionistas')
        
        # ADMINISTRADORES - Acceso completo
        all_permissions = Permission.objects.all()
        admin_group.permissions.set(all_permissions)
        self.stdout.write(f'   ✅ Administradores: {all_permissions.count()} permisos (TODOS)')
        
        # MÉDICOS - Permisos específicos para atención médica
        permisos_medicos = [
            # Core - Solo lectura y modificación de algunos
            'core.view_paciente', 'core.change_paciente', 'core.add_paciente',
            'core.view_doctor', 'core.change_doctor',
            'core.view_especialidad',
            'core.view_medicamento', 'core.add_medicamento', 'core.change_medicamento',
            'core.view_diagnostico', 'core.add_diagnostico', 'core.change_diagnostico',
            'core.view_tiposangre',
            'core.view_tipomedicamento',
            'core.view_marcamedicamento',
            
            # Doctor - Acceso completo a módulos médicos
            'doctor.add_horarioatencion', 'doctor.change_horarioatencion', 'doctor.view_horarioatencion',
            'doctor.add_citamedica', 'doctor.change_citamedica', 'doctor.view_citamedica',
            'doctor.add_atencion', 'doctor.change_atencion', 'doctor.view_atencion',
            'doctor.add_detalleatencion', 'doctor.change_detalleatencion', 'doctor.view_detalleatencion',
            'doctor.view_serviciosadicionales', 'doctor.add_serviciosadicionales', 'doctor.change_serviciosadicionales',
            'doctor.view_pago', 'doctor.add_pago', 'doctor.change_pago',
            'doctor.view_detallepago', 'doctor.add_detallepago', 'doctor.change_detallepago',
        ]
        
        medicos_perms = []
        for perm_codename in permisos_medicos:
            try:
                app_label, codename = perm_codename.split('.')
                permission = Permission.objects.get(
                    content_type__app_label=app_label,
                    codename=codename
                )
                medicos_perms.append(permission)
            except Permission.DoesNotExist:
                continue
        
        medicos_group.permissions.set(medicos_perms)
        self.stdout.write(f'   ✅ Médicos: {len(medicos_perms)} permisos asignados')
        
        # ASISTENTES - Permisos limitados
        permisos_asistentes = [
            'core.view_paciente', 'core.add_paciente', 'core.change_paciente',
            'doctor.view_citamedica', 'doctor.add_citamedica', 'doctor.change_citamedica',
            'doctor.view_atencion',
            'doctor.view_pago', 'doctor.add_pago',
            'doctor.view_serviciosadicionales',
        ]
        
        asistentes_perms = []
        for perm_codename in permisos_asistentes:
            try:
                app_label, codename = perm_codename.split('.')
                permission = Permission.objects.get(
                    content_type__app_label=app_label,
                    codename=codename
                )
                asistentes_perms.append(permission)
            except Permission.DoesNotExist:
                continue
        
        asistentes_group.permissions.set(asistentes_perms)
        self.stdout.write(f'   ✅ Asistentes: {len(asistentes_perms)} permisos asignados')
        
        # RECEPCIONISTAS - Solo citas y pagos
        permisos_recepcionistas = [
            'core.view_paciente', 'core.add_paciente', 'core.change_paciente',
            'doctor.view_citamedica', 'doctor.add_citamedica', 'doctor.change_citamedica',
            'doctor.view_pago', 'doctor.add_pago', 'doctor.change_pago',
            'doctor.view_detallepago', 'doctor.add_detallepago', 'doctor.change_detallepago',
        ]
        
        recepcionistas_perms = []
        for perm_codename in permisos_recepcionistas:
            try:
                app_label, codename = perm_codename.split('.')
                permission = Permission.objects.get(
                    content_type__app_label=app_label,
                    codename=codename
                )
                recepcionistas_perms.append(permission)
            except Permission.DoesNotExist:
                continue
        
        recepcionistas_group.permissions.set(recepcionistas_perms)
        self.stdout.write(f'   ✅ Recepcionistas: {len(recepcionistas_perms)} permisos asignados')

    def asignar_modulos_a_grupos(self):
        """Asignar módulos a grupos usando GroupModulePermission"""
        self.stdout.write('🏗️  Asignando módulos a grupos...')
        
        # Obtener grupos
        admin_group = Group.objects.get(name='Administradores')
        medicos_group = Group.objects.get(name='Médicos')
        asistentes_group = Group.objects.get(name='Asistentes')
        recepcionistas_group = Group.objects.get(name='Recepcionistas')
        
        # Obtener módulos
        modulos = Module.objects.all()
        
        # Asignar todos los módulos a administradores
        for modulo in modulos:
            GroupModulePermission.objects.get_or_create(
                group=admin_group,
                module=modulo,
                defaults={}
            )
        
        # Módulos para médicos
        modulos_medicos = [
            'Pacientes', 'Doctores', 'Especialidades', 'Medicamentos', 'Diagnósticos',
            'Tipos de Medicamento', 'Marcas de Medicamento', 'Tipos de Sangre',
            'Horarios de Atención', 'Citas Médicas', 'Atenciones', 'Detalles de Atención',
            'Servicios Adicionales', 'Pagos', 'Detalles de Pago'
        ]
        
        for nombre_modulo in modulos_medicos:
            modulo = Module.objects.filter(name=nombre_modulo).first()
            if modulo:
                GroupModulePermission.objects.get_or_create(
                    group=medicos_group,
                    module=modulo,
                    defaults={}
                )
        
        # Permisos para asistentes
        modulos_asistentes = [
            'Pacientes', 'Citas Médicas', 'Atenciones', 'Pagos', 'Servicios Adicionales'
        ]
        
        for nombre_modulo in modulos_asistentes:
            modulo = Module.objects.filter(name=nombre_modulo).first()
            if modulo:
                GroupModulePermission.objects.get_or_create(
                    group=asistentes_group,
                    module=modulo,
                    defaults={}
                )
        
        # Permisos para recepcionistas
        modulos_recepcionistas = [
            'Pacientes', 'Citas Médicas', 'Pagos', 'Detalles de Pago'
        ]
        
        for nombre_modulo in modulos_recepcionistas:
            modulo = Module.objects.filter(name=nombre_modulo).first()
            if modulo:
                GroupModulePermission.objects.get_or_create(
                    group=recepcionistas_group,
                    module=modulo,
                    defaults={}
                )
        
        self.stdout.write(self.style.SUCCESS('✅ Permisos asignados'))

    def crear_tipos_sangre(self):
        """Crear tipos de sangre"""
        self.stdout.write('🩸 Creando tipos de sangre...')
        
        tipos = [
            ('O+', 'Tipo O positivo - Donante universal de glóbulos rojos'),
            ('O-', 'Tipo O negativo - Donante universal'),
            ('A+', 'Tipo A positivo'),
            ('A-', 'Tipo A negativo'),
            ('B+', 'Tipo B positivo'),
            ('B-', 'Tipo B negativo'),
            ('AB+', 'Tipo AB positivo - Receptor universal'),
            ('AB-', 'Tipo AB negativo'),
        ]
        
        for tipo, desc in tipos:
            TipoSangre.objects.get_or_create(
                tipo=tipo,
                defaults={'descripcion': desc}
            )
        
        self.stdout.write(self.style.SUCCESS(f'✅ Creados {len(tipos)} tipos de sangre'))

    def crear_especialidades(self):
        """Crear especialidades médicas"""
        self.stdout.write('👨‍⚕️ Creando especialidades...')
        
        especialidades = [
            ('Medicina General', 'Atención médica integral y primaria'),
            ('Cardiología', 'Especialidad del corazón y sistema cardiovascular'),
            ('Pediatría', 'Atención médica especializada en niños y adolescentes'),
            ('Ginecología', 'Salud reproductiva femenina'),
            ('Dermatología', 'Enfermedades de la piel'),
            ('Traumatología', 'Lesiones del sistema musculoesquelético'),
            ('Neurología', 'Enfermedades del sistema nervioso'),
            ('Psiquiatría', 'Trastornos mentales y del comportamiento'),
            ('Oftalmología', 'Enfermedades de los ojos'),
            ('Otorrinolaringología', 'Enfermedades del oído, nariz y garganta'),
        ]
        
        for nombre, desc in especialidades:
            Especialidad.objects.get_or_create(
                nombre=nombre,
                defaults={'descripcion': desc}
            )
        
        self.stdout.write(self.style.SUCCESS(f'✅ Creadas {len(especialidades)} especialidades'))

    def crear_cargos(self):
        """Crear cargos"""
        self.stdout.write('💼 Creando cargos...')
        
        cargos = [
            ('Médico Especialista', 'Médico con especialización'),
            ('Médico General', 'Médico de atención primaria'),
            ('Enfermero/a', 'Personal de enfermería'),
            ('Auxiliar de Enfermería', 'Asistente de enfermería'),
            ('Recepcionista', 'Atención al cliente y citas'),
            ('Administrador', 'Gestión administrativa'),
            ('Contador', 'Gestión contable y financiera'),
            ('Limpieza', 'Personal de limpieza y mantenimiento'),
            ('Seguridad', 'Personal de seguridad'),
            ('Farmaceuta', 'Gestión de medicamentos'),
        ]
        
        for nombre, desc in cargos:
            Cargo.objects.get_or_create(
                nombre=nombre,
                defaults={'descripcion': desc}
            )
        
        self.stdout.write(self.style.SUCCESS(f'✅ Creados {len(cargos)} cargos'))

    def crear_tipos_medicamentos(self):
        """Crear tipos de medicamentos"""
        self.stdout.write('💊 Creando tipos de medicamentos...')
        
        tipos = [
            ('Analgésico', 'Medicamentos para aliviar el dolor'),
            ('Antibiótico', 'Medicamentos contra infecciones bacterianas'),
            ('Antiinflamatorio', 'Reduce inflamación y dolor'),
            ('Antihipertensivo', 'Control de presión arterial'),
            ('Antidiabético', 'Control de diabetes'),
            ('Vitaminas', 'Suplementos vitamínicos'),
            ('Antihistamínico', 'Tratamiento de alergias'),
            ('Antidepresivo', 'Tratamiento de depresión'),
            ('Ansiolítico', 'Tratamiento de ansiedad'),
            ('Broncodilatador', 'Tratamiento de asma y EPOC'),
        ]
        
        for nombre, desc in tipos:
            TipoMedicamento.objects.get_or_create(
                nombre=nombre,
                defaults={'descripcion': desc}
            )
        
        self.stdout.write(self.style.SUCCESS(f'✅ Creados {len(tipos)} tipos'))

    def crear_marcas_medicamentos(self):
        """Crear marcas de medicamentos"""
        self.stdout.write('🏭 Creando marcas...')
        
        marcas = [
            ('Pfizer', 'Farmacéutica multinacional'),
            ('Bayer', 'Empresa farmacéutica alemana'),
            ('Novartis', 'Farmacéutica suiza'),
            ('Roche', 'Empresa farmacéutica suiza'),
            ('Johnson & Johnson', 'Corporación farmacéutica estadounidense'),
            ('Abbott', 'Empresa de salud global'),
            ('Merck', 'Farmacéutica alemana'),
            ('GSK', 'GlaxoSmithKline'),
            ('Sanofi', 'Farmacéutica francesa'),
            ('Genérico', 'Medicamentos genéricos'),
        ]
        
        for nombre, desc in marcas:
            MarcaMedicamento.objects.get_or_create(
                nombre=nombre,
                defaults={'descripcion': desc}
            )
        
        self.stdout.write(self.style.SUCCESS(f'✅ Creadas {len(marcas)} marcas'))

    def crear_medicamentos(self):
        """Crear medicamentos"""
        self.stdout.write('💉 Creando medicamentos...')
        
        tipos = {t.nombre: t for t in TipoMedicamento.objects.all()}
        marcas = {m.nombre: m for m in MarcaMedicamento.objects.all()}
        
        medicamentos = [
            ('Paracetamol', tipos['Analgésico'], marcas['Genérico'], '500mg', ViaAdministracion.ORAL, 100, 0.50, True),
            ('Ibuprofeno', tipos['Antiinflamatorio'], marcas['Bayer'], '400mg', ViaAdministracion.ORAL, 80, 0.75, True),
            ('Aspirina', tipos['Analgésico'], marcas['Bayer'], '100mg', ViaAdministracion.ORAL, 120, 0.30, True),
            ('Amoxicilina', tipos['Antibiótico'], marcas['GSK'], '500mg', ViaAdministracion.ORAL, 60, 2.50, True),
            ('Azitromicina', tipos['Antibiótico'], marcas['Pfizer'], '250mg', ViaAdministracion.ORAL, 30, 8.00, True),
            ('Cefalexina', tipos['Antibiótico'], marcas['Genérico'], '500mg', ViaAdministracion.ORAL, 40, 3.20, True),
            ('Losartán', tipos['Antihipertensivo'], marcas['Merck'], '50mg', ViaAdministracion.ORAL, 90, 1.80, True),
            ('Enalapril', tipos['Antihipertensivo'], marcas['Genérico'], '10mg', ViaAdministracion.ORAL, 100, 1.20, True),
            ('Metformina', tipos['Antidiabético'], marcas['Sanofi'], '850mg', ViaAdministracion.ORAL, 70, 2.10, True),
            ('Glibenclamida', tipos['Antidiabético'], marcas['Genérico'], '5mg', ViaAdministracion.ORAL, 50, 1.50, True),
            ('Complejo B', tipos['Vitaminas'], marcas['Abbott'], '100mg', ViaAdministracion.ORAL, 150, 5.00, True),
            ('Vitamina C', tipos['Vitaminas'], marcas['Bayer'], '1g', ViaAdministracion.ORAL, 200, 3.50, True),
            ('Loratadina', tipos['Antihistamínico'], marcas['Johnson & Johnson'], '10mg', ViaAdministracion.ORAL, 60, 4.20, True),
            ('Cetirizina', tipos['Antihistamínico'], marcas['GSK'], '10mg', ViaAdministracion.ORAL, 45, 5.80, True),
            ('Salbutamol', tipos['Broncodilatador'], marcas['GSK'], '100mcg', ViaAdministracion.INHALATORIA, 25, 12.50, True),
        ]
        
        for nombre, tipo, marca, conc, via, cant, precio, comercial in medicamentos:
            Medicamento.objects.get_or_create(
                nombre=nombre,
                defaults={
                    'tipo': tipo,
                    'marca_medicamento': marca,
                    'concentracion': conc,
                    'via_administracion': via,
                    'cantidad': cant,
                    'precio': Decimal(str(precio)),
                    'comercial': comercial
                }
            )
        
        self.stdout.write(self.style.SUCCESS(f'✅ Creados {len(medicamentos)} medicamentos'))

    def crear_diagnosticos(self):
        """Crear diagnósticos"""
        self.stdout.write('🩺 Creando diagnósticos...')
        
        diagnosticos = [
            ('J00', 'Rinofaringitis aguda [resfriado común]', 'Infección viral del tracto respiratorio superior'),
            ('K59.0', 'Estreñimiento', 'Dificultad para evacuar'),
            ('R50.9', 'Fiebre no especificada', 'Elevación de temperatura corporal'),
            ('M25.5', 'Dolor articular', 'Dolor en articulaciones'),
            ('R51', 'Cefalea', 'Dolor de cabeza'),
            ('K30', 'Dispepsia funcional', 'Indigestión'),
            ('I10', 'Hipertensión esencial', 'Presión arterial elevada'),
            ('E11.9', 'Diabetes mellitus tipo 2 sin complicaciones', 'Diabetes tipo 2'),
            ('F32.9', 'Episodio depresivo sin especificar', 'Depresión'),
            ('J20.9', 'Bronquitis aguda no especificada', 'Inflamación de bronquios'),
            ('L20.9', 'Dermatitis atópica no especificada', 'Eczema'),
            ('N39.0', 'Infección de vías urinarias', 'ITU'),
            ('M54.5', 'Lumbago', 'Dolor lumbar'),
            ('R06.02', 'Dificultad respiratoria', 'Disnea'),
            ('K21.9', 'Enfermedad por reflujo gastroesofágico', 'ERGE'),
        ]
        
        for codigo, desc, datos in diagnosticos:
            Diagnostico.objects.get_or_create(
                codigo=codigo,
                defaults={
                    'descripcion': desc,
                    'datos_adicionales': datos
                }
            )
        
        self.stdout.write(self.style.SUCCESS(f'✅ Creados {len(diagnosticos)} diagnósticos'))

    def crear_tipos_gastos(self):
        """Crear tipos de gastos"""
        self.stdout.write('💰 Creando tipos de gastos...')
        
        tipos_gastos = [
            ('Arriendo', 'Alquiler del local del consultorio'),
            ('Luz', 'Servicio de energía eléctrica'),
            ('Agua', 'Servicio de agua potable'),
            ('Internet', 'Servicio de internet y telecomunicaciones'),
            ('Teléfono', 'Servicio telefónico'),
            ('Insumos Médicos', 'Material médico y de oficina'),
            ('Medicamentos', 'Compra de medicamentos para stock'),
            ('Equipos Médicos', 'Mantenimiento y compra de equipos'),
            ('Limpieza', 'Productos y servicios de limpieza'),
            ('Seguros', 'Pólizas de seguro'),
            ('Marketing', 'Publicidad y marketing'),
            ('Capacitación', 'Cursos y entrenamientos'),
        ]
        
        for nombre, desc in tipos_gastos:
            TipoGasto.objects.get_or_create(
                nombre=nombre,
                defaults={'descripcion': desc}
            )
        
        self.stdout.write(self.style.SUCCESS(f'✅ Creados {len(tipos_gastos)} tipos de gastos'))

    def crear_doctores(self):
        """Crear doctores"""
        self.stdout.write('👨‍⚕️ Creando doctores...')
        
        especialidades = list(Especialidad.objects.all())
        
        doctores_data = [
            {
                'nombres': 'Carlos Eduardo',
                'apellidos': 'González Vásquez',
                'ruc': '1712345678001',
                'fecha_nacimiento': date(1975, 3, 15),
                'direccion': 'Av. 6 de Diciembre N24-253 y Lizardo García, Quito',
                'codigo_unico_doctor': 'DOC001',
                'telefonos': '0987654321',
                'email': 'carlos.gonzalez@clinica.com',
                'horario_atencion': 'Lunes a Viernes: 08:00 - 17:00, Sábados: 08:00 - 12:00',
                'duracion_atencion': 30,
                'especialidades': ['Medicina General', 'Cardiología']
            },
            {
                'nombres': 'María Fernanda',
                'apellidos': 'López Herrera',
                'ruc': '1723456789001',
                'fecha_nacimiento': date(1980, 7, 22),
                'direccion': 'Av. República del Salvador N34-377 y Moscú, Quito',
                'codigo_unico_doctor': 'DOC002',
                'telefonos': '0976543210',
                'email': 'maria.lopez@clinica.com',
                'horario_atencion': 'Lunes a Viernes: 14:00 - 20:00',
                'duracion_atencion': 45,
                'especialidades': ['Pediatría']
            },
            {
                'nombres': 'Roberto Carlos',
                'apellidos': 'Martínez Silva',
                'ruc': '1734567890001',
                'fecha_nacimiento': date(1978, 11, 8),
                'direccion': 'Av. Amazonas N39-123 y Arízaga, Quito',
                'codigo_unico_doctor': 'DOC003',
                'telefonos': '0965432109',
                'email': 'roberto.martinez@clinica.com',
                'horario_atencion': 'Martes a Sábado: 09:00 - 16:00',
                'duracion_atencion': 30,
                'especialidades': ['Dermatología']
            },
            {
                'nombres': 'Ana Lucía',
                'apellidos': 'Rodríguez Morales',
                'ruc': '1745678901001',
                'fecha_nacimiento': date(1982, 5, 18),
                'direccion': 'Av. Eloy Alfaro N32-650 y Rusia, Quito',
                'codigo_unico_doctor': 'DOC004',
                'telefonos': '0954321098',
                'email': 'ana.rodriguez@clinica.com',
                'horario_atencion': 'Lunes a Viernes: 07:00 - 15:00',
                'duracion_atencion': 40,
                'especialidades': ['Ginecología']
            },
        ]
        
        for data in doctores_data:
            especialidades_nombres = data.pop('especialidades')
            doctor, created = Doctor.objects.get_or_create(
                ruc=data['ruc'],
                defaults=data
            )
            
            if created:
                for esp_nombre in especialidades_nombres:
                    especialidad = Especialidad.objects.filter(nombre=esp_nombre).first()
                    if especialidad:
                        doctor.especialidad.add(especialidad)
        
        self.stdout.write(self.style.SUCCESS(f'✅ Creados {len(doctores_data)} doctores'))

    def crear_empleados(self):
        """Crear empleados"""
        self.stdout.write('👥 Creando empleados...')
        
        cargos = {c.nombre: c for c in Cargo.objects.all()}
        
        empleados_data = [
            {
                'nombres': 'Carmen Rosa',
                'apellidos': 'Jiménez Pérez',
                'cedula_ecuatoriana': '1756789012',
                'fecha_nacimiento': date(1985, 9, 12),
                'cargo': cargos['Recepcionista'],
                'sueldo': Decimal('450.00'),
                'fecha_ingreso': date(2023, 1, 15),
                'direccion': 'Sector La Magdalena, Quito'
            },
            {
                'nombres': 'Luis Miguel',
                'apellidos': 'Vargas Torres',
                'cedula_ecuatoriana': '1767890123',
                'fecha_nacimiento': date(1990, 2, 28),
                'cargo': cargos['Auxiliar de Enfermería'],
                'sueldo': Decimal('520.00'),
                'fecha_ingreso': date(2023, 3, 10),
                'direccion': 'Sector Solanda, Quito'
            },
            {
                'nombres': 'Patricia Elena',
                'apellidos': 'Moreno Castro',
                'cedula_ecuatoriana': '1778901234',
                'fecha_nacimiento': date(1988, 6, 14),
                'cargo': cargos['Enfermero/a'],
                'sueldo': Decimal('680.00'),
                'fecha_ingreso': date(2022, 8, 20),
                'direccion': 'Sector El Condado, Quito'
            },
            {
                'nombres': 'Gabriel Andrés',
                'apellidos': 'Ruiz Sandoval',
                'cedula_ecuatoriana': '1789012345',
                'fecha_nacimiento': date(1987, 12, 3),
                'cargo': cargos['Administrador'],
                'sueldo': Decimal('850.00'),
                'fecha_ingreso': date(2022, 4, 5),
                'direccion': 'Sector La Carolina, Quito'
            },
        ]
        
        for data in empleados_data:
            Empleado.objects.get_or_create(
                cedula_ecuatoriana=data['cedula_ecuatoriana'],
                defaults=data
            )
        
        self.stdout.write(self.style.SUCCESS(f'✅ Creados {len(empleados_data)} empleados'))

    def crear_pacientes(self):
        """Crear pacientes"""
        self.stdout.write('🏥 Creando pacientes...')
        
        tipos_sangre = list(TipoSangre.objects.all())
        
        pacientes_data = [
            {
                'nombres': 'José Antonio',
                'apellidos': 'Pérez Morales',
                'cedula_ecuatoriana': '1712345679',
                'fecha_nacimiento': date(1975, 8, 20),
                'telefono': '0987654321',
                'email': 'jose.perez@email.com',
                'sexo': SexoChoices.MASCULINO,
                'estado_civil': EstadoCivilChoices.CASADO,
                'direccion': 'Av. Mariscal Sucre N45-120 y Toledo, Quito',
                'antecedentes_personales': 'Hipertensión arterial diagnosticada hace 5 años, controlada con medicamentos',
                'medicamentos_actuales': 'Losartán 50mg cada 12 horas',
                'alergias': 'Penicilina',
                'habitos_toxicos': 'Ex fumador (dejó hace 3 años)',
            },
            {
                'nombres': 'María Elena',
                'apellidos': 'García Vásquez',
                'cedula_ecuatoriana': '1723456780',
                'fecha_nacimiento': date(1988, 3, 15),
                'telefono': '0976543210',
                'email': 'maria.garcia@email.com',
                'sexo': SexoChoices.FEMENINO,
                'estado_civil': EstadoCivilChoices.SOLTERO,
                'direccion': 'Calle Guayaquil N8-55 y Esmeraldas, Quito',
                'antecedentes_familiares': 'Madre con diabetes tipo 2, padre con hipertensión',
                'antecedentes_gineco_obstetricos': 'Menarquia a los 13 años, ciclos regulares, G0P0A0',
                'alergias': 'Mariscos',
                'habitos_toxicos': 'Ninguno',
            },
            {
                'nombres': 'Carlos Andrés',
                'apellidos': 'Rodríguez Luna',
                'cedula_ecuatoriana': '1734567891',
                'fecha_nacimiento': date(1992, 11, 8),
                'telefono': '0965432109',
                'email': 'carlos.rodriguez@email.com',
                'sexo': SexoChoices.MASCULINO,
                'estado_civil': EstadoCivilChoices.SOLTERO,
                'direccion': 'Sector La Floresta, Calle Andalucía N24-03',
                'antecedentes_quirurgicos': 'Apendicectomía en 2015',
                'habitos_toxicos': 'Alcohol ocasional (fines de semana)',
                'vacunas': 'COVID-19 completa, influenza anual',
            },
            {
                'nombres': 'Ana Sofía',
                'apellidos': 'Martínez Silva',
                'cedula_ecuatoriana': '1745678902',
                'fecha_nacimiento': date(1995, 6, 25),
                'telefono': '0954321098',
                'email': 'ana.martinez@email.com',
                'sexo': SexoChoices.FEMENINO,
                'estado_civil': EstadoCivilChoices.UNION_LIBRE,
                'direccion': 'Sector Cumbayá, Calle de las Orquídeas N14-25',
                'antecedentes_gineco_obstetricos': 'G1P1A0, parto eutócico hace 2 años',
                'medicamentos_actuales': 'Anticonceptivos orales',
                'alergias': 'Polen',
                'habitos_toxicos': 'Ninguno',
            },
            {
                'nombres': 'Roberto Miguel',
                'apellidos': 'López Herrera',
                'cedula_ecuatoriana': '1756789013',
                'fecha_nacimiento': date(1960, 1, 12),
                'telefono': '0943210987',
                'email': 'roberto.lopez@email.com',
                'sexo': SexoChoices.MASCULINO,
                'estado_civil': EstadoCivilChoices.CASADO,
                'direccion': 'Av. de Los Shyris N36-188 y Naciones Unidas',
                'antecedentes_personales': 'Diabetes tipo 2 desde hace 8 años, dislipidemia',
                'medicamentos_actuales': 'Metformina 850mg c/12h, Atorvastatina 20mg/noche',
                'habitos_toxicos': 'Ex fumador (dejó hace 10 años)',
                'antecedentes_familiares': 'Padre falleció por infarto, madre con diabetes',
            },
            {
                'nombres': 'Lucía Fernanda',
                'apellidos': 'Torres Morales',
                'cedula_ecuatoriana': '1767890124',
                'fecha_nacimiento': date(2010, 9, 18),
                'telefono': '0932109876',
                'email': None,
                'sexo': SexoChoices.FEMENINO,
                'estado_civil': EstadoCivilChoices.SOLTERO,
                'direccion': 'Sector El Bosque, Calle de los Cipreses N12-34',
                'antecedentes_familiares': 'Sin antecedentes patológicos familiares relevantes',
                'vacunas': 'Esquema completo para la edad, COVID-19 pediátrica',
                'habitos_toxicos': 'Ninguno',
            },
        ]
        
        for i, data in enumerate(pacientes_data):
            data['tipo_sangre'] = random.choice(tipos_sangre)
            Paciente.objects.get_or_create(
                cedula_ecuatoriana=data['cedula_ecuatoriana'],
                defaults=data
            )
        
        self.stdout.write(self.style.SUCCESS(f'✅ Creados {len(pacientes_data)} pacientes'))

    def crear_gastos_mensuales(self):
        """Crear gastos mensuales"""
        self.stdout.write('💸 Creando gastos mensuales...')
        
        tipos_gastos = list(TipoGasto.objects.all())
        base_date = date.today().replace(day=1)
        
        gastos_data = [
            ('Arriendo', 800.00),
            ('Luz', 45.50),
            ('Agua', 25.30),
            ('Internet', 35.00),
            ('Teléfono', 20.00),
            ('Seguros', 120.00),
            ('Insumos Médicos', 150.75),
            ('Medicamentos', 220.40),
            ('Limpieza', 40.25),
            ('Marketing', 80.00),
        ]
        
        for mes_offset in range(3):
            fecha_gasto = base_date - timedelta(days=mes_offset * 30)
            
            for tipo_nombre, valor_base in gastos_data:
                tipo_gasto = TipoGasto.objects.filter(nombre=tipo_nombre).first()
                if tipo_gasto:
                    variacion = random.uniform(0.9, 1.1)
                    valor_final = round(valor_base * variacion, 2)
                    
                    GastoMensual.objects.get_or_create(
                        tipo_gasto=tipo_gasto,
                        fecha=fecha_gasto,
                        defaults={
                            'valor': Decimal(str(valor_final)),
                            'observacion': f'Gasto mensual de {fecha_gasto.strftime("%B %Y")}'
                        }
                    )
        
        self.stdout.write(self.style.SUCCESS('✅ Creados gastos mensuales'))

    def crear_horarios_atencion(self):
        """Crear horarios de atención"""
        self.stdout.write('⏰ Creando horarios...')
        
        horarios = [
            (DiaSemanaChoices.LUNES, time(8, 0), time(12, 0), None, None),
            (DiaSemanaChoices.MARTES, time(8, 0), time(12, 0), None, None),
            (DiaSemanaChoices.MIERCOLES, time(8, 0), time(12, 0), None, None),
            (DiaSemanaChoices.JUEVES, time(8, 0), time(12, 0), None, None),
            (DiaSemanaChoices.VIERNES, time(8, 0), time(12, 0), None, None),
            (DiaSemanaChoices.LUNES, time(14, 0), time(18, 0), None, None),
            (DiaSemanaChoices.MARTES, time(14, 0), time(18, 0), None, None),
            (DiaSemanaChoices.MIERCOLES, time(14, 0), time(18, 0), None, None),
            (DiaSemanaChoices.JUEVES, time(14, 0), time(18, 0), None, None),
            (DiaSemanaChoices.VIERNES, time(14, 0), time(18, 0), None, None),
            (DiaSemanaChoices.SABADO, time(8, 0), time(12, 0), None, None),
        ]
        
        for dia, inicio, fin, int_desde, int_hasta in horarios:
            HorarioAtencion.objects.get_or_create(
                dia_semana=dia,
                hora_inicio=inicio,
                hora_fin=fin,
                defaults={
                    'intervalo_desde': int_desde,
                    'intervalo_hasta': int_hasta
                }
            )
        
        self.stdout.write(self.style.SUCCESS(f'✅ Creados {len(horarios)} horarios'))

    def crear_servicios_adicionales(self):
        """Crear servicios adicionales"""
        self.stdout.write('🏥 Creando servicios...')
        
        servicios = [
            ('Consulta Médica General', 25.00, 'Consulta médica de medicina general'),
            ('Consulta Especializada', 40.00, 'Consulta con médico especialista'),
            ('Electrocardiograma', 15.00, 'ECG de 12 derivaciones'),
            ('Radiografía Simple', 20.00, 'Radiografía simple de una proyección'),
            ('Ecografía Abdominal', 35.00, 'Ecografía del abdomen completo'),
            ('Laboratorio Básico', 12.00, 'Exámenes de laboratorio básicos'),
            ('Hemograma Completo', 8.00, 'Conteo sanguíneo completo'),
            ('Glicemia', 3.00, 'Medición de glucosa en sangre'),
            ('Curaciones', 5.00, 'Curación de heridas menores'),
            ('Inyecciones', 2.00, 'Aplicación de medicamentos inyectables'),
            ('Nebulizaciones', 4.00, 'Terapia respiratoria con nebulizador'),
            ('Control de Presión', 3.00, 'Medición y control de presión arterial'),
            ('Certificado Médico', 10.00, 'Emisión de certificado médico'),
            ('Papanicolaou', 18.00, 'Citología cervical'),
            ('Vacunación', 15.00, 'Aplicación de vacunas'),
        ]
        
        for nombre, costo, desc in servicios:
            ServiciosAdicionales.objects.get_or_create(
                nombre_servicio=nombre,
                defaults={
                    'costo_servicio': Decimal(str(costo)),
                    'descripcion': desc
                }
            )
        
        self.stdout.write(self.style.SUCCESS(f'✅ Creados {len(servicios)} servicios'))

    def crear_citas_medicas(self):
        """Crear citas médicas"""
        self.stdout.write('📅 Creando citas...')
        
        pacientes = list(Paciente.objects.all())
        base_date = date.today()
        
        citas_data = []
        for day_offset in range(7):
            fecha_cita = base_date + timedelta(days=day_offset)
            
            if fecha_cita.weekday() == 6:  # Skip domingos
                continue
                
            horarios = [
                time(8, 0), time(8, 30), time(9, 0), time(9, 30), time(10, 0),
                time(10, 30), time(11, 0), time(11, 30), time(14, 0), time(14, 30),
                time(15, 0), time(15, 30), time(16, 0), time(16, 30), time(17, 0)
            ]
            
            num_citas = random.randint(3, min(5, len(pacientes)))
            horarios_seleccionados = random.sample(horarios, num_citas)
            pacientes_seleccionados = random.sample(pacientes, num_citas)
            
            for hora, paciente in zip(horarios_seleccionados, pacientes_seleccionados):
                estado = random.choice([
                    EstadoCitaChoices.DISPONIBLE,
                    EstadoCitaChoices.OCUPADO,
                    EstadoCitaChoices.ATENDIDO if day_offset < 2 else EstadoCitaChoices.OCUPADO
                ])
                
                citas_data.append({
                    'paciente': paciente,
                    'fecha': fecha_cita,
                    'hora_cita': hora,
                    'estado': estado,
                    'observaciones': f'Cita programada para {paciente.nombre_completo}'
                })
        
        for data in citas_data:
            try:
                CitaMedica.objects.get_or_create(
                    paciente=data['paciente'],
                    fecha=data['fecha'],
                    hora_cita=data['hora_cita'],
                    defaults={
                        'estado': data['estado'],
                        'observaciones': data['observaciones']
                    }
                )
            except:
                continue
        
        self.stdout.write(self.style.SUCCESS(f'✅ Creadas citas médicas'))

    def crear_atenciones(self):
        """Crear atenciones médicas"""
        self.stdout.write('🩺 Creando atenciones...')
        
        pacientes = list(Paciente.objects.all())
        diagnosticos = list(Diagnostico.objects.all())
        base_datetime = timezone.now()
        
        atenciones_data = [
            {
                'paciente': pacientes[0],
                'dias_atras': 5,
                'motivo': 'Control de presión arterial y renovación de receta',
                'sintomas': 'Paciente asintomático, acude para control rutinario',
                'tratamiento': 'Continuar con Losartán 50mg c/12h. Control en 3 meses',
                'presion_arterial': '140/85',
                'pulso': 78,
                'peso': Decimal('78.5'),
                'altura': Decimal('1.72'),
                'diagnosticos': ['I10']
            },
            {
                'paciente': pacientes[1],
                'dias_atras': 3,
                'motivo': 'Dolor abdominal y náuseas',
                'sintomas': 'Dolor epigástrico, náuseas ocasionales, acidez',
                'tratamiento': 'Omeprazol 20mg en ayunas x 14 días. Dieta blanda',
                'presion_arterial': '110/70',
                'pulso': 82,
                'temperatura': Decimal('36.8'),
                'peso': Decimal('58.2'),
                'altura': Decimal('1.62'),
                'diagnosticos': ['K21.9']
            },
            {
                'paciente': pacientes[2],
                'dias_atras': 10,
                'motivo': 'Dolor de cabeza recurrente',
                'sintomas': 'Cefalea frontal, intensidad moderada, relacionada con estrés',
                'tratamiento': 'Paracetamol 500mg c/8h PRN, técnicas de relajación',
                'presion_arterial': '125/80',
                'pulso': 75,
                'peso': Decimal('72.0'),
                'altura': Decimal('1.75'),
                'diagnosticos': ['R51']
            },
        ]
        
        for data in atenciones_data:
            fecha_atencion = base_datetime - timedelta(days=data['dias_atras'])
            
            atencion = Atencion.objects.create(
                paciente=data['paciente'],
                fecha_atencion=fecha_atencion,
                motivo_consulta=data['motivo'],
                sintomas=data['sintomas'],
                tratamiento=data['tratamiento'],
                presion_arterial=data.get('presion_arterial'),
                pulso=data.get('pulso'),
                temperatura=data.get('temperatura'),
                peso=data.get('peso'),
                altura=data.get('altura'),
                examen_fisico='Examen físico dentro de parámetros normales',
                comentario_adicional='Paciente colaborador, comprende indicaciones'
            )
            
            for codigo_diag in data.get('diagnosticos', []):
                diagnostico = Diagnostico.objects.filter(codigo=codigo_diag).first()
                if diagnostico:
                    atencion.diagnostico.add(diagnostico)
        
        self.stdout.write(self.style.SUCCESS(f'✅ Creadas {len(atenciones_data)} atenciones'))

    def crear_detalles_atencion(self):
        """Crear detalles de atención"""
        self.stdout.write('💊 Creando detalles de atención...')
        
        atenciones = list(Atencion.objects.all())
        medicamentos = list(Medicamento.objects.all())
        
        if atenciones and medicamentos:
            for atencion in atenciones[:3]:
                medicamento = random.choice(medicamentos)
                DetalleAtencion.objects.get_or_create(
                    atencion=atencion,
                    medicamento=medicamento,
                    defaults={
                        'cantidad': random.randint(7, 30),
                        'prescripcion': f'Tomar según indicaciones médicas',
                        'duracion_tratamiento': random.randint(7, 30),
                        'frecuencia_diaria': random.randint(1, 3)
                    }
                )
        
        self.stdout.write(self.style.SUCCESS('✅ Creados detalles de atención'))

    def crear_pagos(self):
        """Crear pagos"""
        self.stdout.write('💳 Creando pagos...')
        
        atenciones = list(Atencion.objects.all())
        servicios = list(ServiciosAdicionales.objects.all())
        
        for i, atencion in enumerate(atenciones):
            metodo = random.choice([
                MetodoPagoChoices.EFECTIVO,
                MetodoPagoChoices.TARJETA,
                MetodoPagoChoices.TRANSFERENCIA
            ])
            
            estado = EstadoPagoChoices.PAGADO if i < 2 else EstadoPagoChoices.PENDIENTE
            
            servicio_consulta = ServiciosAdicionales.objects.filter(
                nombre_servicio__icontains='Consulta'
            ).first()
            
            monto = servicio_consulta.costo_servicio if servicio_consulta else Decimal('25.00')
            
            Pago.objects.create(
                atencion=atencion,
                metodo_pago=metodo,
                monto_total=monto,
                estado=estado,
                fecha_pago=atencion.fecha_atencion if estado == EstadoPagoChoices.PAGADO else None,
                nombre_pagador=atencion.paciente.nombre_completo,
                observaciones=f'Pago por consulta médica - {atencion.paciente.nombre_completo}'
            )
        
        self.stdout.write(self.style.SUCCESS('✅ Creados pagos'))

    def crear_detalles_pago(self):
        """Crear detalles de pago"""
        self.stdout.write('🧾 Creando detalles de pago...')
        
        pagos = list(Pago.objects.all())
        servicios = list(ServiciosAdicionales.objects.all())
        
        from django.db.models import Sum
        
        for pago in pagos:
            servicio = random.choice(servicios)
            
            DetallePago.objects.create(
                pago=pago,
                servicio_adicional=servicio,
                cantidad=1,
                precio_unitario=servicio.costo_servicio,
                descuento_porcentaje=Decimal('0.00'),
                aplica_seguro=False
            )
            
            # Recalcular total
            total = pago.detalles.aggregate(
                total=Sum('subtotal')
            )['total'] or Decimal('0.00')
            
            pago.monto_total = total
            pago.save()
        
        self.stdout.write(self.style.SUCCESS('✅ Creados detalles de pago'))

    def mostrar_resumen(self):
        """Mostrar resumen de datos creados"""
        self.stdout.write('=' * 60)
        self.stdout.write(self.style.SUCCESS('🎉 ¡SISTEMA INSTALADO EXITOSAMENTE!'))
        self.stdout.write('')
        self.stdout.write('📊 RESUMEN DE DATOS CREADOS:')
        self.stdout.write(f'   • Módulos: {Module.objects.count()}')
        self.stdout.write(f'   • Grupos: {Group.objects.count()}')
        self.stdout.write(f'   • Permisos asignados: {GroupModulePermission.objects.count()}')
        self.stdout.write(f'   • Pacientes: {Paciente.objects.count()}')
        self.stdout.write(f'   • Doctores: {Doctor.objects.count()}')
        self.stdout.write(f'   • Empleados: {Empleado.objects.count()}')
        self.stdout.write(f'   • Medicamentos: {Medicamento.objects.count()}')
        self.stdout.write(f'   • Diagnósticos: {Diagnostico.objects.count()}')
        self.stdout.write(f'   • Servicios: {ServiciosAdicionales.objects.count()}')
        self.stdout.write(f'   • Citas médicas: {CitaMedica.objects.count()}')
        self.stdout.write(f'   • Atenciones: {Atencion.objects.count()}')
        self.stdout.write(f'   • Pagos: {Pago.objects.count()}')
        self.stdout.write(f'   • Gastos mensuales: {GastoMensual.objects.count()}')
        self.stdout.write('')
        self.stdout.write('🌟 El sistema está completamente configurado')
        self.stdout.write('🚀 Ejecute: python manage.py runserver')
        self.stdout.write('🌐 Visite: http://127.0.0.1:8000/')
