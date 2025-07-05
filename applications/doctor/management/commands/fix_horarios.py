from django.core.management.base import BaseCommand
from applications.doctor.models import HorarioAtencion
from datetime import time


class Command(BaseCommand):
    help = 'Corrige los horarios de atención para usar intervalos de pausa en lugar de registros separados'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Elimina todos los horarios existentes antes de crear los nuevos',
        )

    def handle(self, *args, **options):
        self.stdout.write('🕐 Corrigiendo horarios de atención...')
        
        if options['reset']:
            self.stdout.write('🗑️  Eliminando horarios existentes...')
            HorarioAtencion.objects.all().delete()
            self.stdout.write('   ✅ Horarios eliminados')
        
        # Definir los horarios correctos con intervalos de pausa
        horarios_correctos = [
            {
                'dia_semana': 'lunes',
                'hora_inicio': time(8, 0),    # 8:00 AM
                'hora_fin': time(18, 0),      # 6:00 PM
                'intervalo_desde': time(12, 0),  # 12:00 PM (inicio pausa)
                'intervalo_hasta': time(14, 0),  # 2:00 PM (fin pausa)
            },
            {
                'dia_semana': 'martes',
                'hora_inicio': time(8, 0),
                'hora_fin': time(18, 0),
                'intervalo_desde': time(12, 0),
                'intervalo_hasta': time(14, 0),
            },
            {
                'dia_semana': 'miércoles',
                'hora_inicio': time(8, 0),
                'hora_fin': time(18, 0),
                'intervalo_desde': time(12, 0),
                'intervalo_hasta': time(14, 0),
            },
            {
                'dia_semana': 'jueves',
                'hora_inicio': time(8, 0),
                'hora_fin': time(18, 0),
                'intervalo_desde': time(12, 0),
                'intervalo_hasta': time(14, 0),
            },
            {
                'dia_semana': 'viernes',
                'hora_inicio': time(8, 0),
                'hora_fin': time(18, 0),
                'intervalo_desde': time(12, 0),
                'intervalo_hasta': time(14, 0),
            },
            {
                'dia_semana': 'sábado',
                'hora_inicio': time(8, 0),
                'hora_fin': time(12, 0),
                'intervalo_desde': None,  # Sin pausa los sábados
                'intervalo_hasta': None,
            },
        ]
        
        # Eliminar horarios duplicados y crear los correctos
        self.stdout.write('🔧 Procesando horarios por día...')
        
        for horario_data in horarios_correctos:
            dia = horario_data['dia_semana']
            
            # Eliminar todos los horarios existentes para este día
            HorarioAtencion.objects.filter(dia_semana=dia).delete()
            
            # Crear el horario correcto
            horario = HorarioAtencion.objects.create(
                dia_semana=horario_data['dia_semana'],
                hora_inicio=horario_data['hora_inicio'],
                hora_fin=horario_data['hora_fin'],
                intervalo_desde=horario_data['intervalo_desde'],
                intervalo_hasta=horario_data['intervalo_hasta'],
                activo=True
            )
            
            pausa_texto = ""
            if horario.intervalo_desde and horario.intervalo_hasta:
                pausa_texto = f" (pausa {horario.intervalo_desde} - {horario.intervalo_hasta})"
            
            self.stdout.write(
                f'   ✅ {dia.capitalize()}: {horario.hora_inicio} - {horario.hora_fin}{pausa_texto}'
            )
        
        self.stdout.write()
        self.stdout.write('📊 Resumen de horarios creados:')
        
        horarios = HorarioAtencion.objects.filter(activo=True).order_by('id')
        for h in horarios:
            slots_mañana = []
            slots_tarde = []
            
            # Calcular slots como lo hace la API
            from datetime import datetime, timedelta
            hora_actual = h.hora_inicio
            hora_fin = h.hora_fin
            
            while hora_actual < hora_fin:
                # Verificar si estamos en el intervalo de pausa
                if (h.intervalo_desde and h.intervalo_hasta and 
                    h.intervalo_desde <= hora_actual < h.intervalo_hasta):
                    # Saltar al final del intervalo de pausa
                    hora_actual = h.intervalo_hasta
                    if hora_actual >= hora_fin:
                        break
                    continue
                
                # Determinar si es mañana o tarde
                slot_time = hora_actual.strftime('%H:%M')
                if hora_actual < time(12, 0):
                    slots_mañana.append(slot_time)
                else:
                    slots_tarde.append(slot_time)
                
                # Sumar 1 hora
                hora_datetime = datetime.combine(datetime.today(), hora_actual)
                hora_datetime += timedelta(hours=1)
                hora_actual = hora_datetime.time()
            
            total_slots = len(slots_mañana) + len(slots_tarde)
            self.stdout.write(
                f'   📅 {h.dia_semana.capitalize()}: {total_slots} slots '
                f'(Mañana: {slots_mañana}, Tarde: {slots_tarde})'
            )
        
        self.stdout.write()
        self.stdout.write('🎉 ¡Horarios corregidos exitosamente!')
        self.stdout.write('💡 Ahora el calendario debería mostrar todos los horarios disponibles.')
