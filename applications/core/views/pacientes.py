from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.db.models import Q
from django.utils import timezone
from applications.core.models import Paciente
from applications.core.forms import PacienteForm
from applications.security.components.mixin_crud import CreateViewMixin, DeleteViewMixin, ListViewMixin, PermissionMixin, UpdateViewMixin
import string


class PacienteListView(PermissionMixin, ListViewMixin, ListView):
    model = Paciente
    template_name = 'core/paciente/list.html'
    context_object_name = 'pacientes'
    permission_required = 'view_paciente'

    def get_queryset(self):
        # Obtener parámetros de búsqueda y filtrado
        search_query = self.request.GET.get('q', '')
        tipo_sangre_filter = self.request.GET.get('tipo_sangre', '')
        sexo_filter = self.request.GET.get('sexo', '')
        activo_filter = self.request.GET.get('activo', '')
        nombre_filter = self.request.GET.get('nombre_letra', 'todos')
        apellido_filter = self.request.GET.get('apellido_letra', 'todos')
        sort_by = self.request.GET.get('sort', 'nombre')
        direction = self.request.GET.get('direction', 'asc')
        
        # Aplicar filtro de búsqueda por texto
        if search_query:
            self.query.add(Q(nombres__icontains=search_query), Q.OR)
            self.query.add(Q(apellidos__icontains=search_query), Q.OR)
            self.query.add(Q(cedula_ecuatoriana__icontains=search_query), Q.OR)
            self.query.add(Q(telefono__icontains=search_query), Q.OR)
            self.query.add(Q(email__icontains=search_query), Q.OR)
        
        # Aplicar filtro por tipo de sangre
        if tipo_sangre_filter:
            self.query.add(Q(tipo_sangre__tipo=tipo_sangre_filter), Q.AND)
        
        # Aplicar filtro por sexo
        if sexo_filter:
            self.query.add(Q(sexo=sexo_filter), Q.AND)
        
        # Aplicar filtro por estado activo
        if activo_filter:
            if activo_filter == 'true':
                self.query.add(Q(activo=True), Q.AND)
            elif activo_filter == 'false':
                self.query.add(Q(activo=False), Q.AND)
        
        # Aplicar filtros alfabéticos
        if nombre_filter != 'todos':
            self.query.add(Q(nombres__istartswith=nombre_filter), Q.AND)
        
        if apellido_filter != 'todos':
            self.query.add(Q(apellidos__istartswith=apellido_filter), Q.AND)
        
        # Aplicar ordenamiento
        if sort_by == 'nombre':
            order_field = 'apellidos' if direction == 'asc' else '-apellidos'
        elif sort_by == 'cedula':
            order_field = 'cedula_ecuatoriana' if direction == 'asc' else '-cedula_ecuatoriana'
        elif sort_by == 'email':
            order_field = 'email' if direction == 'asc' else '-email'
        elif sort_by == 'sexo':
            order_field = 'sexo' if direction == 'asc' else '-sexo'
        elif sort_by == 'estado_civil':
            order_field = 'estado_civil' if direction == 'asc' else '-estado_civil'
        elif sort_by == 'tipo_sangre':
            order_field = 'tipo_sangre__tipo' if direction == 'asc' else '-tipo_sangre__tipo'
        elif sort_by == 'activo':
            order_field = 'activo' if direction == 'asc' else '-activo'
        else:
            order_field = 'apellidos'
        
        return self.model.objects.filter(self.query).order_by(order_field, 'nombres')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Añadir parámetros de búsqueda al contexto
        context['search_query'] = self.request.GET.get('q', '')
        context['tipo_sangre_filter'] = self.request.GET.get('tipo_sangre', '')
        context['sexo_filter'] = self.request.GET.get('sexo', '')
        context['activo_filter'] = self.request.GET.get('activo', '')
        context['nombre_filter'] = self.request.GET.get('nombre_letra', 'todos')
        context['apellido_filter'] = self.request.GET.get('apellido_letra', 'todos')
        context['current_sort'] = self.request.GET.get('sort', 'nombre')
        context['current_direction'] = self.request.GET.get('direction', 'asc')
        context['create_url'] = reverse_lazy('core:paciente_create')
        
        # Añadir alfabeto para filtros
        context['alfabeto'] = list(string.ascii_uppercase)
        
        return context


class PacienteCreateView(PermissionMixin, CreateViewMixin, CreateView):
    model = Paciente
    form_class = PacienteForm
    template_name = 'core/paciente/create.html'
    success_url = reverse_lazy('core:paciente_list')
    permission_required = 'add_paciente'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['grabar'] = 'Guardar Paciente'
        context['back_url'] = self.success_url
        return context

    def get_initial(self):
        """Pre-llenar formulario con parámetros GET del chatbot"""
        initial = super().get_initial()
        
        # Obtener parámetros GET para pre-llenar el formulario
        for field_name in ['nombres', 'apellidos', 'cedula_ecuatoriana', 'telefono', 'email', 'direccion']:
            value = self.request.GET.get(field_name)
            if value:
                initial[field_name] = value
        
        return initial

    def form_valid(self, form):
        form.instance.activo = True
        return super().form_valid(form)


class PacienteUpdateView(PermissionMixin, UpdateViewMixin, UpdateView):
    model = Paciente
    form_class = PacienteForm
    template_name = 'core/paciente/create.html'
    success_url = reverse_lazy('core:paciente_list')
    permission_required = 'change_paciente'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['grabar'] = 'Actualizar Paciente'
        context['back_url'] = self.success_url
        return context


class PacienteDeleteView(PermissionMixin, DeleteViewMixin, DeleteView):
    model = Paciente
    template_name = 'core/delete.html'
    success_url = reverse_lazy('core:paciente_list')
    permission_required = 'delete_paciente'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Eliminar Paciente'
        context['cancel_url'] = self.success_url
        
        # Verificar dependencias antes de mostrar el formulario
        paciente = self.object
        dependencias = []
        
        # Verificar atenciones médicas
        atenciones = paciente.atenciones.all()
        if atenciones.exists():
            count_atenciones = atenciones.count()
            # Verificar si alguna atención tiene pagos
            atenciones_con_pagos = []
            for atencion in atenciones:
                if atencion.pagos.exists():
                    atenciones_con_pagos.append(atencion)
            
            if atenciones_con_pagos:
                dependencias.append(f"• {count_atenciones} atención(es) médica(s), de las cuales {len(atenciones_con_pagos)} tiene(n) pagos asociados")
            else:
                dependencias.append(f"• {count_atenciones} atención(es) médica(s)")
        
        # Verificar citas médicas
        citas = paciente.citas.all()
        if citas.exists():
            count_citas = citas.count()
            citas_futuras = citas.filter(fecha__gte=timezone.now().date())
            if citas_futuras.exists():
                dependencias.append(f"• {count_citas} cita(s) médica(s) programada(s), de las cuales {citas_futuras.count()} son futuras")
            else:
                dependencias.append(f"• {count_citas} cita(s) médica(s) programada(s)")
        
        # Verificar fotos del paciente
        fotos = paciente.fotos.all()
        if fotos.exists():
            dependencias.append(f"• {fotos.count()} foto(s) del paciente")
        
        if dependencias:
            context['cannot_delete'] = True
            context['title'] = 'No se puede eliminar el paciente'
            context['description'] = self._get_delete_blocked_message(paciente, dependencias)
        else:
            context['cannot_delete'] = False
            context['question'] = f'¿Está seguro de eliminar al paciente {paciente.nombres} {paciente.apellidos}?'
            context['description'] = self._get_delete_warning_message(paciente)
        
        return context
    
    def _get_delete_blocked_message(self, paciente, dependencias):
        """Genera el mensaje cuando no se puede eliminar el paciente"""
        mensaje = f'No se puede eliminar al paciente <strong>{paciente.nombres} {paciente.apellidos}</strong> porque tiene los siguientes registros asociados:<br><br>'
        
        mensaje += '<br>'.join(dependencias)
        
        mensaje += '<br><br><strong>¿Qué puede hacer?</strong><br>'
        mensaje += '• Para eliminar este paciente, primero debe eliminar o reasignar todos los registros relacionados<br>'
        mensaje += '• Las atenciones médicas con pagos no pueden eliminarse por razones de auditoría<br>'
        mensaje += '• Puede desactivar el paciente en lugar de eliminarlo si ya no lo necesita<br>'
        mensaje += '• Contacte al administrador del sistema si necesita ayuda con este proceso'
        
        return mensaje
    
    def _get_delete_warning_message(self, paciente):
        """Genera el mensaje de advertencia cuando se puede eliminar el paciente"""
        mensaje = f'Se eliminará permanentemente al paciente <strong>{paciente.nombres} {paciente.apellidos}</strong>.<br><br>'
        mensaje += '<strong>⚠️ Esta acción no se puede deshacer</strong><br><br>'
        mensaje += 'Se recomienda desactivar el paciente en lugar de eliminarlo para mantener la integridad de los datos históricos.'
        
        return mensaje
    
    def delete(self, request, *args, **kwargs):
        from django.contrib import messages
        from django.db import IntegrityError
        from django.db.models import ProtectedError
        
        self.object = self.get_object()
        nombre_completo = f"{self.object.nombres} {self.object.apellidos}"
        success_url = self.get_success_url()
        
        try:
            # Intentar eliminar el objeto
            self.object.delete()
            
            # Agregar mensaje de éxito
            messages.success(request, f'El paciente "{nombre_completo}" ha sido eliminado exitosamente.')
            
        except ProtectedError as e:
            # Manejar error de protección por clave foránea
            messages.error(request, f'No se puede eliminar al paciente "{nombre_completo}" porque tiene registros médicos asociados que deben conservarse por razones de auditoría.')
            
        except IntegrityError as e:
            # Manejar otros errores de integridad
            messages.error(request, f'No se puede eliminar al paciente "{nombre_completo}" debido a restricciones de integridad de datos.')
        
        except Exception as e:
            # Manejar cualquier otro error
            messages.error(request, f'Ocurrió un error al eliminar al paciente "{nombre_completo}": {str(e)}')
        
        # Retornar respuesta
        from django.http import HttpResponseRedirect
        return HttpResponseRedirect(success_url)