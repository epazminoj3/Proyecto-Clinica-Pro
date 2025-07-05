from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import datetime, time, date, timedelta
from applications.doctor.models import CitaMedica
from applications.core.models import Paciente
from applications.doctor.utils.cita_medica import EstadoCitaChoices


class Command(BaseCommand):
    help = 'Agrega citas de prueba para testear el calendario'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Elimina todas las citas existentes antes de crear las nuevas',
        )

    def handle(self, *args, **options):
        self.stdout.write('📅 Agregando citas de prueba al calendario...')
        
        if options['reset']:
            self.stdout.write('🗑️  Eliminando citas existentes...')
            CitaMedica.objects.all().delete()
            self.stdout.write('   ✅ Citas eliminadas')
        
        # Obtener pacientes existentes
        pacientes = list(Paciente.objects.all()[:6])
        if len(pacientes) < 6:
            self.stdout.write('   ❌ Se necesitan al menos 6 pacientes en el sistema')
            return
        
        # Obtener fecha actual para determinar citas pasadas y futuras
        today = date.today()
        
        # Crear citas tanto pasadas como futuras para probar diferentes escenarios
        citas_prueba = []
        
        # === CITAS PASADAS (estado "atendido") ===
        # Hace 2 semanas
        past_date = today - timedelta(days=14)
        citas_prueba.extend([
            {'fecha': past_date, 'hora': time(8, 0), 'paciente': pacientes[0], 'estado': EstadoCitaChoices.ATENDIDO},
            {'fecha': past_date, 'hora': time(10, 0), 'paciente': pacientes[1], 'estado': EstadoCitaChoices.ATENDIDO},
            {'fecha': past_date, 'hora': time(15, 0), 'paciente': pacientes[2], 'estado': EstadoCitaChoices.ATENDIDO},
        ])
        
        # Hace 1 semana
        past_date = today - timedelta(days=7)
        citas_prueba.extend([
            {'fecha': past_date, 'hora': time(9, 0), 'paciente': pacientes[3], 'estado': EstadoCitaChoices.ATENDIDO},
            {'fecha': past_date, 'hora': time(11, 0), 'paciente': pacientes[4], 'estado': EstadoCitaChoices.ATENDIDO},
            {'fecha': past_date, 'hora': time(14, 0), 'paciente': pacientes[5], 'estado': EstadoCitaChoices.ATENDIDO},
            {'fecha': past_date, 'hora': time(16, 0), 'paciente': pacientes[0], 'estado': EstadoCitaChoices.ATENDIDO},
        ])
        
        # Hace 3 días
        past_date = today - timedelta(days=3)
        citas_prueba.extend([
            {'fecha': past_date, 'hora': time(8, 0), 'paciente': pacientes[1], 'estado': EstadoCitaChoices.ATENDIDO},
            {'fecha': past_date, 'hora': time(9, 0), 'paciente': pacientes[2], 'estado': EstadoCitaChoices.ATENDIDO},
            {'fecha': past_date, 'hora': time(10, 0), 'paciente': pacientes[3], 'estado': EstadoCitaChoices.ATENDIDO},
            {'fecha': past_date, 'hora': time(15, 0), 'paciente': pacientes[4], 'estado': EstadoCitaChoices.ATENDIDO},
        ])
        
        # === CITAS FUTURAS (estados "ocupado" y "disponible") ===
        # Mañana
        future_date = today + timedelta(days=1)
        citas_prueba.extend([
            {'fecha': future_date, 'hora': time(8, 0), 'paciente': pacientes[5], 'estado': EstadoCitaChoices.OCUPADO},
            {'fecha': future_date, 'hora': time(10, 0), 'paciente': pacientes[0], 'estado': EstadoCitaChoices.OCUPADO},
            {'fecha': future_date, 'hora': time(15, 0), 'paciente': pacientes[1], 'estado': EstadoCitaChoices.OCUPADO},
        ])
        
        # En 3 días
        future_date = today + timedelta(days=3)
        citas_prueba.extend([
            {'fecha': future_date, 'hora': time(9, 0), 'paciente': pacientes[2], 'estado': EstadoCitaChoices.OCUPADO},
            {'fecha': future_date, 'hora': time(11, 0), 'paciente': pacientes[3], 'estado': EstadoCitaChoices.DISPONIBLE},
        ])
        
        # En 5 días
        future_date = today + timedelta(days=5)
        citas_prueba.extend([
            {'fecha': future_date, 'hora': time(14, 0), 'paciente': pacientes[4], 'estado': EstadoCitaChoices.OCUPADO},
            {'fecha': future_date, 'hora': time(16, 0), 'paciente': pacientes[5], 'estado': EstadoCitaChoices.OCUPADO},
        ])
        
        # En 1 semana - Día completo (8 citas)
        future_date = today + timedelta(days=7)
        citas_prueba.extend([
            {'fecha': future_date, 'hora': time(8, 0), 'paciente': pacientes[0], 'estado': EstadoCitaChoices.OCUPADO},
            {'fecha': future_date, 'hora': time(9, 0), 'paciente': pacientes[1], 'estado': EstadoCitaChoices.OCUPADO},
            {'fecha': future_date, 'hora': time(10, 0), 'paciente': pacientes[2], 'estado': EstadoCitaChoices.OCUPADO},
            {'fecha': future_date, 'hora': time(11, 0), 'paciente': pacientes[3], 'estado': EstadoCitaChoices.OCUPADO},
            {'fecha': future_date, 'hora': time(14, 0), 'paciente': pacientes[4], 'estado': EstadoCitaChoices.OCUPADO},
            {'fecha': future_date, 'hora': time(15, 0), 'paciente': pacientes[5], 'estado': EstadoCitaChoices.OCUPADO},
            {'fecha': future_date, 'hora': time(16, 0), 'paciente': pacientes[0], 'estado': EstadoCitaChoices.OCUPADO},
            {'fecha': future_date, 'hora': time(17, 0), 'paciente': pacientes[1], 'estado': EstadoCitaChoices.OCUPADO},
        ])
        
        # En 10 días - Pocas citas
        future_date = today + timedelta(days=10)
        citas_prueba.extend([
            {'fecha': future_date, 'hora': time(8, 0), 'paciente': pacientes[2], 'estado': EstadoCitaChoices.OCUPADO},
            {'fecha': future_date, 'hora': time(14, 0), 'paciente': pacientes[3], 'estado': EstadoCitaChoices.DISPONIBLE},
        ])
        
        # En 2 semanas - Mix de estados
        future_date = today + timedelta(days=14)
        citas_prueba.extend([
            {'fecha': future_date, 'hora': time(9, 0), 'paciente': pacientes[4], 'estado': EstadoCitaChoices.OCUPADO},
            {'fecha': future_date, 'hora': time(11, 0), 'paciente': pacientes[5], 'estado': EstadoCitaChoices.DISPONIBLE},
            {'fecha': future_date, 'hora': time(15, 0), 'paciente': pacientes[0], 'estado': EstadoCitaChoices.OCUPADO},
        ])
        
        # En 3 semanas
        future_date = today + timedelta(days=21)
        citas_prueba.extend([
            {'fecha': future_date, 'hora': time(8, 0), 'paciente': pacientes[1], 'estado': EstadoCitaChoices.OCUPADO},
            {'fecha': future_date, 'hora': time(16, 0), 'paciente': pacientes[2], 'estado': EstadoCitaChoices.DISPONIBLE},
        ])
        
        # Crear las citas
        citas_creadas = 0
        for cita_data in citas_prueba:
            # Verificar que no exista ya una cita en esa fecha y hora
            existe = CitaMedica.objects.filter(
                fecha=cita_data['fecha'],
                hora_cita=cita_data['hora']
            ).exists()
            
            if not existe:
                cita = CitaMedica.objects.create(
                    paciente=cita_data['paciente'],
                    fecha=cita_data['fecha'],
                    hora_cita=cita_data['hora'],
                    estado=cita_data['estado'],
                    observaciones=f'Cita de prueba para calendario'
                )
                citas_creadas += 1
                
                # Mostrar información de la cita creada
                dia_semana = cita.fecha.strftime('%A')
                fecha_str = cita.fecha.strftime('%d/%m/%Y')
                self.stdout.write(
                    f'   ✅ {dia_semana} {fecha_str} {cita.hora_cita} - {cita.paciente.nombre_completo} ({cita.estado})'
                )
            else:
                fecha_str = cita_data['fecha'].strftime('%d/%m/%Y')
                self.stdout.write(
                    f'   ⚠️  Ya existe cita el {fecha_str} a las {cita_data["hora"]} - omitiendo'
                )
        
        self.stdout.write()
        self.stdout.write('📊 Resumen de citas creadas:')
        
        # Mostrar resumen agrupado por fecha
        fechas_con_citas = CitaMedica.objects.values('fecha').distinct().order_by('fecha')
        
        citas_pasadas = 0
        citas_futuras = 0
        
        for fecha_info in fechas_con_citas:
            fecha = fecha_info['fecha']
            citas_del_dia = CitaMedica.objects.filter(fecha=fecha)
            total_citas = citas_del_dia.count()
            
            # Contar por estados
            atendidas = citas_del_dia.filter(estado=EstadoCitaChoices.ATENDIDO).count()
            ocupadas = citas_del_dia.filter(estado=EstadoCitaChoices.OCUPADO).count() 
            disponibles = citas_del_dia.filter(estado=EstadoCitaChoices.DISPONIBLE).count()
            
            fecha_str = fecha.strftime('%d/%m/%Y')
            dia_semana = fecha.strftime('%A')
            
            # Determinar si es pasada o futura
            if fecha < today:
                tipo = "📅 PASADA"
                citas_pasadas += total_citas
            elif fecha == today:
                tipo = "📍 HOY"
            else:
                tipo = "🔮 FUTURA"
                citas_futuras += total_citas
            
            # Crear descripción de estados
            estados_desc = []
            if atendidas > 0:
                estados_desc.append(f"{atendidas} atendidas")
            if ocupadas > 0:
                estados_desc.append(f"{ocupadas} ocupadas")
            if disponibles > 0:
                estados_desc.append(f"{disponibles} disponibles")
            
            estados_str = ", ".join(estados_desc)
            
            self.stdout.write(
                f'   {tipo} {dia_semana} {fecha_str}: {total_citas} citas ({estados_str})'
            )
        
        self.stdout.write()
        self.stdout.write(f'🎉 ¡{citas_creadas} citas de prueba agregadas exitosamente!')
        self.stdout.write(f'   📅 {citas_pasadas} citas pasadas (estado: atendido)')
        self.stdout.write(f'   � {citas_futuras} citas futuras (estados: ocupado/disponible)')
        self.stdout.write()
        self.stdout.write('📋 Estados utilizados:')
        self.stdout.write(f'   • {EstadoCitaChoices.ATENDIDO} - Para citas pasadas ya completadas')
        self.stdout.write(f'   • {EstadoCitaChoices.OCUPADO} - Para citas futuras confirmadas')
        self.stdout.write(f'   • {EstadoCitaChoices.DISPONIBLE} - Para horarios reservados pero disponibles')
        self.stdout.write()
        self.stdout.write('🔍 Para probar el calendario:')
        self.stdout.write('   • Las citas pasadas aparecerán en gris (atendidas)')
        self.stdout.write('   • Las citas futuras se mostrarán según disponibilidad')
        self.stdout.write('   • Los días sin citas quedarán disponibles para agendar')
