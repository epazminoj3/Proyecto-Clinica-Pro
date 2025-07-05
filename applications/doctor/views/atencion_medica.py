import json
from decimal import Decimal

from django.contrib import messages
from django.db import transaction
from django.http import JsonResponse
from django.urls import reverse_lazy
from django.utils import timezone
from django.views import View
from django.db.models import Q

from applications.core.models import Paciente, Medicamento, Diagnostico, TipoSangre, TipoMedicamento, MarcaMedicamento
from applications.core.forms.paciente import PacienteForm
from applications.core.forms.medicamento import MedicamentoForm
from applications.core.utils.medicamento import ViaAdministracion
from applications.doctor.forms.atencion import AtencionForm
from applications.doctor.models import Atencion, DetalleAtencion
from applications.security.components.mixin_crud import CreateViewMixin, DeleteViewMixin, ListViewMixin, \
    PermissionMixin, UpdateViewMixin
from django.views.generic import ListView, CreateView, UpdateView, DeleteView

from proy_clinico.util import save_audit
from applications.core.forms.medicamento import MedicamentoForm


class AtencionListView(PermissionMixin, ListViewMixin, ListView):
    template_name = 'doctor/atenciones/list.html'
    model = Atencion
    context_object_name = 'atenciones'
    permission_required = 'view_atencion'

    def get_queryset(self):
        q1 = self.request.GET.get('q')

        if q1  is not None:
               self.query.add(Q(paciente__nombres__icontains=q1), Q.OR)
               self.query.add(Q(paciente__apellidos__icontains=q1), Q.OR)
               self.query.add(Q(motivo_consulta__icontains=q1), Q.OR)
        return (self.model.objects.filter(self.query)
                .select_related('paciente')
                .prefetch_related('pagos', 'diagnostico')
                .order_by('-fecha_atencion'))


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['create_url'] = reverse_lazy('doctor:atencion_create')

        return context


class AtencionCreateView(PermissionMixin, CreateViewMixin, CreateView):
    model = Atencion
    template_name = 'doctor/atenciones/form.html'
    form_class = AtencionForm
    success_url = reverse_lazy('doctor:atencion_list')
    permission_required = 'add_atencion'

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        context['grabar'] = 'Grabar Atención'
        context['back_url'] = self.success_url
        context['diagnosticos']= Diagnostico.objects.filter(activo=True)
        context['medicamentos'] = (Medicamento.objects.filter(activo=True)
            .select_related('tipo', 'marca_medicamento')
            .only('id', 'nombre', 'concentracion', 'via_administracion',
                  'precio', 'cantidad', 'tipo__nombre', 'marca_medicamento__nombre'
                  ).order_by('nombre'))
        
        # Agregar tipos de sangre para el modal de agregar paciente
        context['tipos_sangre'] = TipoSangre.objects.all().order_by('tipo')
        
        # Agregar datos para el modal de agregar medicamento
        context['tipos_medicamento'] = TipoMedicamento.objects.filter(activo=True).order_by('nombre')
        context['marcas_medicamento'] = MarcaMedicamento.objects.filter(activo=True).order_by('nombre')
        context['vias_administracion'] = ViaAdministracion.choices

        context['paciente_json'] = 'null'
        context['medicamentos_json'] = '[]'  # Array vacío
        context['modo_edicion'] = False
        
        # Información de la cita de referencia
        cita_id = self.request.GET.get('cita_id')
        if cita_id:
            try:
                from applications.doctor.models import CitaMedica
                cita = CitaMedica.objects.select_related('paciente').get(pk=cita_id)
                context['cita_referencia'] = cita
                context['viene_de_cita'] = True
            except CitaMedica.DoesNotExist:
                context['viene_de_cita'] = False
        else:
            context['viene_de_cita'] = False
            
        return context


    def post(self, request, *args, **kwargs):
        # Convertir el cuerpo de la solicitud a un diccionario Python
        data = json.loads(request.body)

        # Extraer los objetos anidados
        signos_vitales = data.get('signosVitales', {})
        evaluacion_clinica = data.get('evaluacionClinica', {})
        plan_terapeutico = data.get('planTerapeutico', {})
        medicamentos = data.get('medicamentos', [])

        # Conversiones simples (el frontend ya validó)
        def to_int(value):
            return int(value) if value is not None and value != '' else None

        def to_decimal(value):
            return Decimal(str(value)) if value is not None and value != '' else None

        try:
            with transaction.atomic():
                # Crear la instancia del modelo Atencion
                atencion = Atencion.objects.create(
                    # Datos básicos
                    paciente_id=to_int(data.get('paciente')),

                    # Signos vitales
                    presion_arterial=signos_vitales.get('presionArterial'),
                    pulso=to_int(signos_vitales.get('pulso')),
                    temperatura=to_decimal(signos_vitales.get('temperatura')),
                    frecuencia_respiratoria=to_int(signos_vitales.get('frecuenciaRespiratoria')),
                    saturacion_oxigeno=to_decimal(signos_vitales.get('saturacionOxigeno')),
                    peso=to_decimal(signos_vitales.get('peso')),
                    altura=to_decimal(signos_vitales.get('altura')),
                    es_control=bool(signos_vitales.get('consultaControl', False)),

                    # Evaluación clínica
                    motivo_consulta=evaluacion_clinica.get('motivoConsulta', ''),
                    sintomas=evaluacion_clinica.get('sintomas', ''),
                    examen_fisico=evaluacion_clinica.get('examenFisico'),

                    # Plan terapéutico
                    tratamiento=plan_terapeutico.get('tratamiento', ''),
                    examenes_enviados=plan_terapeutico.get('examenesEnviados'),
                    comentario_adicional=plan_terapeutico.get('comentarioAdicional'),

                    # Fecha automática
                    fecha_atencion=timezone.now()
                )

                # Procesar diagnósticos
                diagnostico_ids = evaluacion_clinica.get('diagnostico', [])
                if diagnostico_ids:
                    diagnosticos = Diagnostico.objects.filter(id__in=diagnostico_ids)
                    atencion.diagnostico.set(diagnosticos)

                # Procesar medicamentos
                for medicamento in medicamentos:
                    DetalleAtencion.objects.create(
                        atencion=atencion,
                        medicamento_id=to_int(medicamento.get('id')),
                        cantidad=to_int(medicamento.get('cantidad')),
                        prescripcion=medicamento.get('prescripcion'),
                        duracion_tratamiento=to_int(medicamento.get('duracion')),
                        frecuencia_diaria=to_int(medicamento.get('frecuencia'))
                    )

                # Guardar auditoría
                save_audit(request, atencion, "ADICION")

                # Marcar la cita como atendida si viene de una cita
                cita_id = self.request.GET.get('cita_id')
                if cita_id:
                    try:
                        from applications.doctor.models import CitaMedica
                        from applications.doctor.utils.cita_medica import EstadoCitaChoices
                        cita = CitaMedica.objects.get(pk=cita_id)
                        cita.estado = EstadoCitaChoices.ATENDIDO
                        cita.save()
                        messages.success(request, f"La cita médica también ha sido marcada como atendida")
                    except CitaMedica.DoesNotExist:
                        pass

                # Mensaje de éxito
                messages.success(request, f"Éxito al registrar la atención médica #{atencion.id}")

                # Respuesta exitosa
                return JsonResponse({
                    "msg": "Atención médica registrada exitosamente",
                    "id": atencion.id,
                    "fecha": atencion.fecha_atencion.strftime('%Y-%m-%d %H:%M:%S'),
                    "paciente": str(atencion.paciente)
                }, status=200)

        except Exception as e:
            messages.error(request, f"Error al registrar la atención médica")
            return JsonResponse({
                "msg": f"Error al registrar la atención médica: {str(e)}"
            }, status=500)


class AtencionUpdateView(PermissionMixin, UpdateViewMixin, UpdateView):
    model = Atencion
    template_name = 'doctor/atenciones/form.html'
    form_class = AtencionForm
    success_url = reverse_lazy('doctor:atencion_list')
    permission_required = 'change_atencion'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['grabar'] = 'Actualizar Atención'
        context['back_url'] = self.success_url

        # Contextos iguales al CreateView
        context['diagnosticos'] = Diagnostico.objects.filter(activo=True)
        context['medicamentos'] = (Medicamento.objects.filter(activo=True)
                                   .select_related('tipo', 'marca_medicamento')
                                   .only('id', 'nombre', 'concentracion', 'via_administracion',
                                         'precio', 'cantidad', 'tipo__nombre', 'marca_medicamento__nombre'
                                         ).order_by('nombre'))
        
        # Agregar tipos de sangre para el modal de agregar paciente
        context['tipos_sangre'] = TipoSangre.objects.all().order_by('tipo')

        # Contexto específico para el update: detalles de atención actual
        atencion = self.get_object()

        # Obtener contexto completo del paciente para edición
        contexto_paciente = obtener_contexto_paciente(atencion.paciente.id)
        context['paciente_json'] = contexto_paciente['paciente_json']
        context['paciente_data'] = contexto_paciente['paciente_data']
        context['modo_edicion'] = True

        # Datos de la atención actual para usar directamente en el HTML
        context['atencion'] = atencion
        print("atenciones")
        print(atencion.temperatura)
        print(type(atencion.temperatura))
        # Solo los medicamentos para cargar dinámicamente con JavaScript
        medicamentos = []
        for detalle in atencion.detalles.select_related('medicamento').all():
            medicamento_dict = {
                'id': detalle.medicamento.id,
                'nombre': detalle.medicamento.nombre,
                'concentracion': detalle.medicamento.concentracion,
                'via_administracion': detalle.medicamento.via_administracion,
                'cantidad': detalle.cantidad,
                'prescripcion': detalle.prescripcion,
                'duracion': detalle.duracion_tratamiento,
                'frecuencia': detalle.frecuencia_diaria,
                'precio': float(detalle.medicamento.precio) if detalle.medicamento.precio else 0
            }
            medicamentos.append(medicamento_dict)

        # Solo los medicamentos en JSON para JavaScript
        context['medicamentos_json'] = json.dumps(medicamentos)

        return context

    def post(self, request, *args, **kwargs):
        # Obtener la instancia actual que se va a actualizar
        atencion = self.get_object()

        # Convertir el cuerpo de la solicitud a un diccionario Python
        data = json.loads(request.body)

        # Extraer los objetos anidados
        signos_vitales = data.get('signosVitales', {})
        evaluacion_clinica = data.get('evaluacionClinica', {})
        plan_terapeutico = data.get('planTerapeutico', {})
        medicamentos = data.get('medicamentos', [])

        # Conversiones simples (el frontend ya validó)
        def to_int(value):
            return int(value) if value is not None and value != '' else None

        def to_decimal(value):
            return Decimal(str(value)) if value is not None and value != '' else None

        try:
            with transaction.atomic():
                # Actualizar la instancia existente de Atencion
                atencion.paciente_id = to_int(data.get('paciente'))

                # Signos vitales
                atencion.presion_arterial = signos_vitales.get('presionArterial')
                atencion.pulso = to_int(signos_vitales.get('pulso'))
                atencion.temperatura = to_decimal(signos_vitales.get('temperatura'))
                atencion.frecuencia_respiratoria = to_int(signos_vitales.get('frecuenciaRespiratoria'))
                atencion.saturacion_oxigeno = to_decimal(signos_vitales.get('saturacionOxigeno'))
                atencion.peso = to_decimal(signos_vitales.get('peso'))
                atencion.altura = to_decimal(signos_vitales.get('altura'))
                atencion.es_control = bool(signos_vitales.get('consultaControl', False))

                # Evaluación clínica
                atencion.motivo_consulta = evaluacion_clinica.get('motivoConsulta', '')
                atencion.sintomas = evaluacion_clinica.get('sintomas', '')
                atencion.examen_fisico = evaluacion_clinica.get('examenFisico')

                # Plan terapéutico
                atencion.tratamiento = plan_terapeutico.get('tratamiento', '')
                atencion.examenes_enviados = plan_terapeutico.get('examenesEnviados')
                atencion.comentario_adicional = plan_terapeutico.get('comentarioAdicional')

                # Guardar los cambios en la atención
                atencion.save()

                # Procesar diagnósticos
                diagnostico_ids = evaluacion_clinica.get('diagnostico', [])
                if diagnostico_ids:
                    diagnosticos = Diagnostico.objects.filter(id__in=diagnostico_ids)
                    atencion.diagnostico.set(diagnosticos)
                else:
                    # Si no hay diagnósticos, limpiar la relación
                    atencion.diagnostico.clear()

                # Procesar medicamentos: borrar existentes y crear nuevos
                DetalleAtencion.objects.filter(atencion=atencion).delete()

                for medicamento in medicamentos:
                    DetalleAtencion.objects.create(
                        atencion=atencion,
                        medicamento_id=to_int(medicamento.get('id')),
                        cantidad=to_int(medicamento.get('cantidad')),
                        prescripcion=medicamento.get('prescripcion'),
                        duracion_tratamiento=to_int(medicamento.get('duracion')),
                        frecuencia_diaria=to_int(medicamento.get('frecuencia'))
                    )

                # Guardar auditoría para modificación
                save_audit(request, atencion, "MODIFICACION")

                # Mensaje de éxito
                messages.success(request, f"Éxito al actualizar la atención médica #{atencion.id}")

                # Respuesta exitosa
                return JsonResponse({
                    "msg": "Atención médica actualizada exitosamente",
                    "id": atencion.id,
                    "fecha": atencion.fecha_atencion.strftime('%Y-%m-%d %H:%M:%S'),
                    "paciente": str(atencion.paciente)
                }, status=200)

        except Exception as e:
            messages.error(request, f"Error al actualizar la atención médica")
            return JsonResponse({
                "msg": f"Error al actualizar la atención médica: {str(e)}"
            }, status=500)

class AtencionDeleteView(PermissionMixin, DeleteViewMixin, DeleteView):
    model = Atencion
    template_name = 'core/delete.html'
    success_url = reverse_lazy('doctor:atencion_list')
    permission_required = 'delete_atencion'

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        context['grabar'] = 'Eliminar Atención'
        context['description'] = f"¿Desea eliminar la atención de: {self.object.paciente}?"
        context['back_url'] = self.success_url
        return context

    def form_valid(self, form):
        paciente_nombre = self.object.paciente
        response = super().form_valid(form)
        messages.success(self.request, f"Éxito al eliminar lógicamente la atención de {paciente_nombre}.")
        return response


class BuscarPacientesView(PermissionMixin, View):
    """Vista para buscar pacientes mediante AJAX"""
    permission_required = 'core.view_paciente'
    
    def get(self, request):
        query = request.GET.get('q', '').strip()
        
        if len(query) < 3:
            return JsonResponse({
                'pacientes': [],
                'mensaje': 'Escriba al menos 3 caracteres para buscar'
            })
        
        # Buscar pacientes por nombre, apellido o cédula
        pacientes = Paciente.objects.filter(
            Q(nombres__icontains=query) |
            Q(apellidos__icontains=query) |
            Q(cedula_ecuatoriana__icontains=query) |
            Q(dni__icontains=query),
            activo=True
        ).select_related().order_by('nombres', 'apellidos')[:10]
        
        # Formatear resultados
        resultados = []
        for paciente in pacientes:
            resultados.append({
                'id': paciente.id,
                'nombre_completo': paciente.nombre_completo,
                'cedula': paciente.cedula_ecuatoriana or paciente.dni or '',
                'cedula_ecuatoriana': paciente.cedula_ecuatoriana or '',
                'telefono': paciente.telefono or '',
                'email': paciente.email or '',
                'edad': paciente.edad if paciente.edad else '',
                'direccion': paciente.direccion or '',
                'foto_url': paciente.get_image,
                'antecedentes_personales': paciente.antecedentes_personales or '',
                'antecedentes_quirurgicos': paciente.antecedentes_quirurgicos or '',
                'antecedentes_familiares': paciente.antecedentes_familiares or '',
                'alergias': paciente.alergias or '',
                'medicamentos_actuales': paciente.medicamentos_actuales or '',
                'habitos_toxicos': paciente.habitos_toxicos or '',
                'vacunas': paciente.vacunas or '',
                'antecedentes_gineco_obstetricos': paciente.antecedentes_gineco_obstetricos or '',
            })
        
        return JsonResponse({
            'pacientes': resultados,
            'total': len(resultados)
        })


class ConsultasAnterioresView(PermissionMixin, View):
    """Vista para obtener las consultas anteriores de un paciente mediante AJAX"""
    permission_required = 'doctor.view_atencion'
    
    def get(self, request):
        paciente_id = request.GET.get('paciente_id', '').strip()
        
        if not paciente_id:
            return JsonResponse({
                'consultas': [],
                'mensaje': 'ID de paciente requerido'
            }, status=400)
        
        try:
            paciente = Paciente.objects.get(id=paciente_id, activo=True)
        except Paciente.DoesNotExist:
            return JsonResponse({
                'consultas': [],
                'mensaje': 'Paciente no encontrado'
            }, status=404)
        
        # Obtener atenciones anteriores (últimas 20, excluyendo la actual si existe)
        atenciones = paciente.atenciones.select_related().prefetch_related(
            'diagnostico',
            'detalles__medicamento'
        ).order_by('-fecha_atencion')[:20]
        
        # Formatear resultados
        consultas = []
        for atencion in atenciones:
            # Obtener diagnósticos
            diagnosticos = [d.descripcion for d in atencion.diagnostico.all()]
            
            # Obtener medicamentos/prescripciones
            prescripciones = []
            for detalle in atencion.detalles.all():
                prescripciones.append({
                    'medicamento': detalle.medicamento.nombre if detalle.medicamento else 'Medicamento eliminado',
                    'cantidad': detalle.cantidad,
                    'prescripcion': detalle.prescripcion,
                    'duracion': detalle.duracion_tratamiento,
                    'frecuencia': detalle.frecuencia_diaria,
                })
            
            # Determinar tipo de consulta
            tipo_consulta = "Chequeo"
            if atencion.es_control:
                tipo_consulta = "Control"
            elif any(palabra in atencion.motivo_consulta.lower() for palabra in ['urgencia', 'dolor', 'emergencia']):
                tipo_consulta = "Urgencia"
            
            consulta = {
                'id': atencion.id,
                'fecha_atencion': atencion.fecha_atencion.strftime('%Y-%m-%d %H:%M'),
                'fecha_formateada': atencion.fecha_atencion.strftime('%d/%m/%Y %H:%M'),
                'tipo_consulta': tipo_consulta,
                
                # Signos vitales
                'presion_arterial': atencion.presion_arterial or '',
                'pulso': atencion.pulso or '',
                'temperatura': str(atencion.temperatura) if atencion.temperatura else '',
                'frecuencia_respiratoria': atencion.frecuencia_respiratoria or '',
                'saturacion_oxigeno': str(atencion.saturacion_oxigeno) if atencion.saturacion_oxigeno else '',
                'peso': str(atencion.peso) if atencion.peso else '',
                'altura': str(atencion.altura) if atencion.altura else '',
                'imc': atencion.calcular_imc,
                
                # Contenido de la atención
                'motivo_consulta': atencion.motivo_consulta or '',
                'sintomas': atencion.sintomas or '',
                'examen_fisico': atencion.examen_fisico or '',
                'diagnosticos': diagnosticos,
                'tratamiento': atencion.tratamiento or '',
                'examenes_enviados': atencion.examenes_enviados or '',
                'comentario_adicional': atencion.comentario_adicional or '',
                'es_control': atencion.es_control,
                
                # Prescripciones
                'prescripciones': prescripciones
            }
            consultas.append(consulta)
        
        return JsonResponse({
            'consultas': consultas,
            'total': len(consultas),
            'paciente': {
                'id': paciente.id,
                'nombre_completo': paciente.nombre_completo,
                'total_atenciones': paciente.atenciones.count()
            }
        })
def obtener_contexto_paciente(id_paciente):
    try:
        paciente = Paciente.objects.select_related('tipo_sangre').prefetch_related(
            'atenciones__diagnostico',
            'atenciones__detalles__medicamento'
        ).get(id=id_paciente, activo=True)

        edad = paciente.edad
        # Obtener atenciones anteriores (últimas 10)
        atenciones = []
        for atencion in paciente.atenciones.all()[:10]:
            # Obtener prescripciones/detalles de esta atención
            detalles = []
            for detalle in atencion.detalles.all():
                detalle_dict = {
                    'medicamento': detalle.medicamento.nombre if detalle.medicamento else '',
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
                'temperatura': float(atencion.temperatura) if atencion.temperatura else '',
                'frecuencia_respiratoria': atencion.frecuencia_respiratoria,
                'saturacion_oxigeno': float(atencion.saturacion_oxigeno) if atencion.saturacion_oxigeno else '',
                'peso': float(atencion.peso) if atencion.peso else '',
                'altura': float(atencion.altura) if atencion.altura else '',
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

        # Crear diccionario del paciente
        paciente_data = {
            'id': paciente.id,
            'nombres': paciente.nombres,
            'apellidos': paciente.apellidos,
            'nombre_completo': f"{paciente.nombres} {paciente.apellidos}",
            'cedula': paciente.cedula_ecuatoriana or paciente.dni or '',
            'cedula_ecuatoriana': paciente.cedula_ecuatoriana,
            'dni': paciente.dni,
            'fecha_nacimiento': paciente.fecha_nacimiento.isoformat() if paciente.fecha_nacimiento else '',
            'edad': edad,
            'telefono': paciente.telefono,
            'email': paciente.email,
            'sexo': paciente.sexo,
            'estado_civil': paciente.estado_civil,
            'direccion': paciente.direccion,
            'latitud': float(paciente.latitud) if paciente.latitud else '',
            'longitud': float(paciente.longitud) if paciente.longitud else '',
            'tipo_sangre': paciente.tipo_sangre.tipo if paciente.tipo_sangre else '',
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

        return {
            'paciente_data': paciente_data,
            'paciente_json': json.dumps(paciente_data)
        }

    except Paciente.DoesNotExist:
        return {
            'paciente_data': '',
            'paciente_json': 'null'
        }

class PacienteCreateApiView(PermissionMixin, View):
    """Vista para crear pacientes vía AJAX desde el formulario de atención médica"""
    permission_required = 'core.add_paciente'

    def post(self, request, *args, **kwargs):
        """Crea un nuevo paciente vía AJAX"""
        try:
            # Crear formulario con los datos recibidos
            form = PacienteForm(request.POST, request.FILES)
            
            if form.is_valid():
                # Guardar el paciente
                paciente = form.save(commit=False)
                paciente.activo = True
                paciente.save()
                
                # Preparar datos para la respuesta
                paciente_data = {
                    'id': paciente.id,
                    'nombres': paciente.nombres,
                    'apellidos': paciente.apellidos,
                    'nombre_completo': paciente.nombre_completo,
                    'cedula_ecuatoriana': paciente.cedula_ecuatoriana,
                    'dni': paciente.dni,
                    'fecha_nacimiento': paciente.fecha_nacimiento.isoformat() if paciente.fecha_nacimiento else None,
                    'edad': paciente.edad,
                    'telefono': paciente.telefono,
                    'email': paciente.email,
                    'sexo': paciente.sexo,
                    'estado_civil': paciente.estado_civil,
                    'direccion': paciente.direccion,
                    'tipo_sangre': paciente.tipo_sangre.tipo if paciente.tipo_sangre else None,
                    'foto_url': paciente.get_image,
                    
                    # Historia clínica
                    'antecedentes_personales': paciente.antecedentes_personales or '',
                    'antecedentes_quirurgicos': paciente.antecedentes_quirurgicos or '',
                    'antecedentes_familiares': paciente.antecedentes_familiares or '',
                    'alergias': paciente.alergias or '',
                    'medicamentos_actuales': paciente.medicamentos_actuales or '',
                    'habitos_toxicos': paciente.habitos_toxicos or '',
                    'vacunas': paciente.vacunas or '',
                    'antecedentes_gineco_obstetricos': paciente.antecedentes_gineco_obstetricos or '',
                    'atenciones': []  # El paciente nuevo no tiene atenciones aún
                }

                return JsonResponse({
                    'success': True,
                    'message': 'Paciente creado exitosamente',
                    'paciente': paciente_data
                })
            else:
                # Hay errores en el formulario
                errors = {}
                for field, field_errors in form.errors.items():
                    errors[field] = field_errors[0]  # Tomar el primer error de cada campo
                
                return JsonResponse({
                    'success': False,
                    'message': 'Error en los datos del formulario',
                    'errors': errors
                }, status=400)

        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error interno del servidor: {str(e)}'
            }, status=500)

class MedicamentoCreateApiView(PermissionMixin, View):
    """Vista para crear medicamentos vía AJAX desde el formulario de atención médica"""
    permission_required = 'core.add_medicamento'

    def post(self, request, *args, **kwargs):
        """Crea un nuevo medicamento vía AJAX"""
        try:
            # Crear formulario con los datos recibidos
            form = MedicamentoForm(request.POST, request.FILES)
            
            if form.is_valid():
                # Guardar el medicamento
                medicamento = form.save(commit=False)
                medicamento.activo = True
                medicamento.save()
                
                # Preparar datos para la respuesta
                medicamento_data = {
                    'id': medicamento.id,
                    'nombre': medicamento.nombre,
                    'descripcion': medicamento.descripcion or '',
                    'concentracion': medicamento.concentracion or '',
                    'via_administracion': medicamento.via_administracion,
                    'via_administracion_display': medicamento.get_via_administracion_display(),
                    'cantidad': medicamento.cantidad,
                    'precio': float(medicamento.precio) if medicamento.precio else 0.0,
                    'comercial': medicamento.comercial,
                    'tipo': {
                        'id': medicamento.tipo.id if medicamento.tipo else None,
                        'nombre': medicamento.tipo.nombre if medicamento.tipo else ''
                    },
                    'marca_medicamento': {
                        'id': medicamento.marca_medicamento.id if medicamento.marca_medicamento else None,
                        'nombre': medicamento.marca_medicamento.nombre if medicamento.marca_medicamento else ''
                    },
                    'foto_url': medicamento.get_image if hasattr(medicamento, 'get_image') else '',
                    'activo': medicamento.activo
                }

                # Guardar auditoría
                save_audit(request, medicamento, "ADICION")

                return JsonResponse({
                    'success': True,
                    'message': 'Medicamento creado exitosamente',
                    'medicamento': medicamento_data
                })
            else:
                # Hay errores en el formulario
                errors = {}
                for field, field_errors in form.errors.items():
                    errors[field] = field_errors[0]  # Tomar el primer error de cada campo
                
                return JsonResponse({
                    'success': False,
                    'message': 'Error en los datos del formulario',
                    'errors': errors
                }, status=400)

        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error interno del servidor: {str(e)}'
            }, status=500)

    def get_initial(self):
        """
        Prellenar datos del formulario si se viene desde una cita médica
        """
        initial = super().get_initial()
        
        # Obtener parámetros de la URL
        cita_id = self.request.GET.get('cita_id')
        paciente_id = self.request.GET.get('paciente_id')
        fecha = self.request.GET.get('fecha')
        hora = self.request.GET.get('hora')
        
        # Si hay un ID de paciente, preseleccionarlo
        if paciente_id:
            try:
                paciente = Paciente.objects.get(pk=paciente_id)
                initial['paciente'] = paciente
            except Paciente.DoesNotExist:
                pass
        
        # Si hay fecha, usarla como referencia para la fecha de atención
        if fecha:
            try:
                from datetime import datetime
                fecha_obj = datetime.strptime(fecha, '%Y-%m-%d').date()
                # La fecha de atención será la fecha actual, pero podemos usar la fecha de la cita como referencia
                # El campo fecha_atencion se autosetea, pero podemos agregar info contextual
            except ValueError:
                pass
        
        return initial

