from django.http import JsonResponse
from django.db.models import Q
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from applications.core.models import Paciente

"""  Vista para buscar pacientes mediante AJAX. Por nombres, apellidos, cédula o teléfono. """


@login_required
@require_http_methods(["GET"])
def paciente_find(request):
    try:
        # Obtener el parámetro de búsqueda
        query = request.GET.get('q', '').strip()

        # Validar que se proporcione al menos 3 caracteres
        if len(query) < 3:
            return JsonResponse({
                'success': False,
                'message': 'Debe proporcionar al menos 3 caracteres para la búsqueda',
                'pacientes': []
            })

        # Construir la consulta de búsqueda
        # Buscar en nombres, apellidos, cédula, DNI y teléfono
        pacientes_query = Paciente.objects.filter(
            Q(activo=True) & (
                    Q(nombres__icontains=query) |
                    Q(apellidos__icontains=query) |
                    Q(cedula_ecuatoriana__icontains=query) |
                    Q(dni__icontains=query) |
                    Q(telefono__icontains=query)
            )
        ).select_related('tipo_sangre').prefetch_related(
            'atenciones__diagnostico',
            'atenciones__detalles__medicamento'
        ).order_by('apellidos', 'nombres')

        # Limitar resultados para mejorar rendimiento
        pacientes_query = pacientes_query[:20]

        # Convertir a lista de diccionarios
        pacientes_data = []
        for paciente in pacientes_query:
            # Calcular edad
            edad = paciente.edad

            # Obtener atenciones anteriores (últimas 10)
            atenciones = []
            for atencion in paciente.atenciones.all()[:10]:
                # Obtener prescripciones/detalles de esta atención
                detalles = []
                for detalle in atencion.detalles.all():
                    detalle_dict = {
                        'medicamento': detalle.medicamento.nombre if detalle.medicamento else None,
                        'cantidad': detalle.cantidad,
                        'prescripcion': detalle.prescripcion,
                        'duracion_tratamiento': detalle.duracion_tratamiento,
                        'frecuencia_diaria': detalle.frecuencia_diaria,
                    }
                    detalles.append(detalle_dict)

                # Obtener diagnósticos
                diagnosticos = [d.descripcion for d in atencion.diagnostico.all()]

                # Determinar tipo de consulta
                tipo_consulta = "Chequeo"
                if atencion.es_control:
                    tipo_consulta = "Control"
                elif "urgencia" in atencion.motivo_consulta.lower() or "dolor" in atencion.motivo_consulta.lower():
                    tipo_consulta = "Urgencia"

                atencion_dict = {
                    'id': atencion.id,
                    'fecha_atencion': atencion.fecha_atencion.isoformat(),
                    'tipo_consulta': tipo_consulta,

                    # Signos vitales
                    'presion_arterial': atencion.presion_arterial,
                    'pulso': atencion.pulso,
                    'temperatura': float(atencion.temperatura) if atencion.temperatura else None,
                    'frecuencia_respiratoria': atencion.frecuencia_respiratoria,
                    'saturacion_oxigeno': float(atencion.saturacion_oxigeno) if atencion.saturacion_oxigeno else None,
                    'peso': float(atencion.peso) if atencion.peso else None,
                    'altura': float(atencion.altura) if atencion.altura else None,
                    'imc': atencion.calcular_imc,

                    # Contenido de la atención
                    'motivo_consulta': atencion.motivo_consulta,
                    'sintomas': atencion.sintomas,
                    'tratamiento': atencion.tratamiento,
                    'diagnosticos': diagnosticos,
                    'examen_fisico': atencion.examen_fisico,
                    'examenes_enviados': atencion.examenes_enviados,
                    'comentario_adicional': atencion.comentario_adicional,
                    'es_control': atencion.es_control,

                    # Prescripciones
                    'prescripciones': detalles
                }
                atenciones.append(atencion_dict)

            paciente_dict = {
                'id': paciente.id,
                'nombres': paciente.nombres,
                'apellidos': paciente.apellidos,
                'cedula_ecuatoriana': paciente.cedula_ecuatoriana,
                'dni': paciente.dni,
                'fecha_nacimiento': paciente.fecha_nacimiento.isoformat() if paciente.fecha_nacimiento else None,
                'edad': edad,
                'telefono': paciente.telefono,
                'email': paciente.email,
                'sexo': paciente.sexo,
                'estado_civil': paciente.estado_civil,
                'direccion': paciente.direccion,
                'latitud': float(paciente.latitud) if paciente.latitud else None,
                'longitud': float(paciente.longitud) if paciente.longitud else None,
                'tipo_sangre': paciente.tipo_sangre.tipo if paciente.tipo_sangre else None,
                'foto_url': paciente.get_image,

                # Historia clínica
                'antecedentes_personales': paciente.antecedentes_personales,
                'antecedentes_quirurgicos': paciente.antecedentes_quirurgicos,
                'antecedentes_familiares': paciente.antecedentes_familiares,
                'alergias': paciente.alergias,
                'medicamentos_actuales': paciente.medicamentos_actuales,
                'habitos_toxicos': paciente.habitos_toxicos,
                'vacunas': paciente.vacunas,
                'antecedentes_gineco_obstetricos': paciente.antecedentes_gineco_obstetricos,

                # Atenciones anteriores
                'atenciones': atenciones,
                'total_atenciones': paciente.atenciones.count()
            }
            pacientes_data.append(paciente_dict)
        print(pacientes_data)
        return JsonResponse({
            'success': True,
            'pacientes': pacientes_data,
            'total': len(pacientes_data),
            'query': query
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error en la búsqueda: {str(e)}',
            'pacientes': []
        }, status=500)


