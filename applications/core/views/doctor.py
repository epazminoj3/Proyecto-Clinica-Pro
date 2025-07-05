from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from applications.core.models import Doctor, Especialidad
from applications.core.forms import DoctorForm, EspecialidadForm
from applications.security.components.mixin_crud import CreateViewMixin, DeleteViewMixin, ListViewMixin, PermissionMixin, UpdateViewMixin
from django.db.models import Q
from django.contrib import messages
from django.db import models
from django.http import HttpResponseRedirect


# ==================== VISTAS DE DOCTOR ====================
class DoctorListView(PermissionMixin, ListViewMixin, ListView):
    model = Doctor
    template_name = 'core/doctor/list.html'
    context_object_name = 'doctores'
    permission_required = 'view_doctor'

    def get_queryset(self):
        q1 = self.request.GET.get('q')
        if q1 is not None:
            self.query.add(Q(nombres__icontains=q1), Q.OR)
            self.query.add(Q(apellidos__icontains=q1), Q.OR)
            self.query.add(Q(codigo_unico_doctor__icontains=q1), Q.OR)
            self.query.add(Q(telefonos__icontains=q1), Q.OR)
            self.query.add(Q(email__icontains=q1), Q.OR)
            self.query.add(Q(ruc__icontains=q1), Q.OR)

        return self.model.objects.prefetch_related('especialidad').filter(self.query).order_by('nombres')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['create_url'] = reverse_lazy('core:doctor_create')
        return context


class DoctorCreateView(PermissionMixin, CreateViewMixin, CreateView):
    model = Doctor
    form_class = DoctorForm
    template_name = 'core/doctor/form.html'
    success_url = reverse_lazy('core:doctor_list')
    permission_required = 'add_doctor'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['grabar'] = 'Guardar Doctor'
        context['back_url'] = self.success_url
        return context

    def get_initial(self):
        """Pre-llenar formulario con parámetros GET del chatbot"""
        initial = super().get_initial()
        
        # Campos para doctores
        campos_doctor = ['nombres', 'apellidos', 'cedula_ecuatoriana', 'telefono', 'email', 
                        'direccion', 'especialidad', 'licencia_medica']
        
        for field_name in campos_doctor:
            value = self.request.GET.get(field_name)
            if value:
                initial[field_name] = value
        
        return initial

    def form_valid(self, form):
        form.instance.activo = True
        return super().form_valid(form)


class DoctorUpdateView(PermissionMixin, UpdateViewMixin, UpdateView):
    model = Doctor
    form_class = DoctorForm
    template_name = 'core/doctor/form.html'
    success_url = reverse_lazy('core:doctor_list')
    permission_required = 'change_doctor'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['grabar'] = 'Actualizar Doctor'
        context['back_url'] = self.success_url
        return context


class DoctorDeleteView(PermissionMixin, DeleteViewMixin, DeleteView):
    model = Doctor
    template_name = 'core/delete.html'
    success_url = reverse_lazy('core:doctor_list')
    permission_required = 'delete_doctor'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Eliminar Doctor'
        context['cancel_url'] = self.success_url
        
        # Verificar dependencias antes de mostrar el formulario
        doctor = self.object
        dependencias = []
        
        # Verificar especialidades (relación ManyToMany)
        especialidades = doctor.especialidad.all()
        if especialidades.exists():
            especialidades_nombres = [esp.nombre for esp in especialidades[:3]]
            especialidades_text = ', '.join(especialidades_nombres)
            if especialidades.count() > 3:
                especialidades_text += f" y {especialidades.count() - 3} más"
            dependencias.append(f"• Especialidades asociadas: {especialidades_text}")
        
        # Por ahora, las especialidades no bloquean la eliminación ya que es ManyToMany
        # El doctor simplemente se desasociará de las especialidades
        
        # Verificar si tiene archivos asociados que deberían ser mencionados
        archivos_asociados = []
        if doctor.curriculum:
            archivos_asociados.append("currículum")
        if doctor.firma_digital:
            archivos_asociados.append("firma digital")
        if doctor.foto:
            archivos_asociados.append("foto")
        if doctor.imagen_receta:
            archivos_asociados.append("imagen de receta")
        
        if archivos_asociados:
            archivos_text = ', '.join(archivos_asociados)
            dependencias.append(f"• Archivos asociados: {archivos_text}")
        
        if dependencias:
            # Para doctores, actualmente no hay dependencias que bloqueen eliminación
            # Solo mostramos información sobre lo que se eliminará
            context['cannot_delete'] = False
            context['question'] = f'¿Está seguro de eliminar al doctor {doctor.nombres} {doctor.apellidos}?'
            context['description'] = self._get_delete_warning_message(doctor, dependencias)
        else:
            context['cannot_delete'] = False
            context['question'] = f'¿Está seguro de eliminar al doctor {doctor.nombres} {doctor.apellidos}?'
            context['description'] = self._get_delete_warning_message(doctor, [])
        
        return context

    def _get_delete_warning_message(self, doctor, dependencias):
        """Genera mensaje de advertencia para eliminación de doctor"""
        mensaje = f"""
        <div class="mb-4">
            <h4 class="text-lg font-semibold text-orange-600 mb-2">
                <i class="fas fa-exclamation-triangle mr-2"></i>
                Eliminar Doctor: {doctor.nombres} {doctor.apellidos}
            </h4>
            <p class="text-gray-700 mb-3">
                Esta acción eliminará permanentemente al doctor y toda la información asociada.
            </p>
        </div>
        """
        
        if dependencias:
            mensaje += f"""
            <div class="bg-orange-50 border-l-4 border-orange-400 p-4 mb-4">
                <h5 class="font-medium text-orange-800 mb-2">Se eliminarán también:</h5>
                <ul class="list-disc list-inside text-orange-700 space-y-1">
                    {''.join(f'<li>{dep}</li>' for dep in dependencias)}
                </ul>
            </div>
            """
        
        mensaje += f"""
        <div class="bg-blue-50 border-l-4 border-blue-400 p-4">
            <h5 class="font-medium text-blue-800 mb-2">
                <i class="fas fa-info-circle mr-1"></i>
                Información importante
            </h5>
            <ul class="list-disc list-inside text-blue-700 space-y-1">
                <li>Los archivos (fotos, currículum, firmas) se eliminarán del sistema</li>
                <li>Las asociaciones con especialidades se removerán automáticamente</li>
                <li>Esta acción no se puede deshacer</li>
                <li>Considere desactivar el doctor en lugar de eliminarlo si es necesario mantener el historial</li>
            </ul>
        </div>
        """
        
        return mensaje

    def delete(self, request, *args, **kwargs):
        """Override del método delete para manejar eliminación con mensajes informativos"""
        self.object = self.get_object()
        nombre_completo = f"{self.object.nombres} {self.object.apellidos}"
        success_url = self.get_success_url()
        
        try:
            # Intentar eliminar el objeto
            self.object.delete()
            
            # Agregar mensaje de éxito
            messages.success(request, f'El doctor "{nombre_completo}" ha sido eliminado exitosamente.')
            
        except models.ProtectedError as e:
            # Manejar error de protección por clave foránea
            messages.error(request, f'No se puede eliminar al doctor "{nombre_completo}" porque tiene registros protegidos asociados que no pueden eliminarse.')
            
        except Exception as e:
            # Manejar cualquier otro error
            messages.error(request, f'Ocurrió un error al eliminar al doctor "{nombre_completo}": {str(e)}')
        
        # Retornar respuesta
        return HttpResponseRedirect(success_url)

    def post(self, request, *args, **kwargs):
        """Override del método post para manejar ProtectedError"""
        self.object = self.get_object()
        
        try:
            return self.delete(request, *args, **kwargs)
        except models.ProtectedError as e:
            # Capturar el error de protección y mostrar mensaje amigable
            protected_objects = e.protected_objects
            
            # Analizar qué tipo de objetos están protegiendo
            object_types = {}
            for obj in protected_objects:
                obj_type = obj._meta.verbose_name_plural
                if obj_type not in object_types:
                    object_types[obj_type] = 0
                object_types[obj_type] += 1
            
            # Crear mensaje detallado
            obj_details = []
            for obj_type, count in object_types.items():
                obj_details.append(f"{count} {obj_type}")
            
            error_message = (
                f"❌ No se puede eliminar al doctor '{self.object.nombres} {self.object.apellidos}' porque tiene "
                f"registros relacionados que están protegidos: {', '.join(obj_details)}.\n\n"
                f"💡 Para eliminar este doctor, primero debes:\n"
                f"   • Eliminar o reasignar todos los registros relacionados\n"
                f"   • O considerar desactivar el doctor en lugar de eliminarlo\n"
                f"   • Luego podrás eliminar el doctor sin problemas"
            )
            
            messages.error(request, error_message)
            return HttpResponseRedirect(self.success_url)


# ==================== VISTAS DE ESPECIALIDAD ====================
class EspecialidadListView(PermissionMixin, ListViewMixin, ListView):
    model = Especialidad
    template_name = 'core/especialidad/list.html'
    context_object_name = 'especialidades'
    permission_required = 'view_especialidad'

    def get_queryset(self):
        q1 = self.request.GET.get('q')
        if q1 is not None:
            self.query.add(Q(nombre__icontains=q1), Q.OR)
            self.query.add(Q(descripcion__icontains=q1), Q.OR)

        # Filtrar solo especialidades activas
        self.query.add(Q(activo=True), Q.AND)
        return self.model.objects.filter(self.query).order_by('nombre')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['create_url'] = reverse_lazy('core:especialidad_create')
        return context


class EspecialidadCreateView(PermissionMixin, CreateViewMixin, CreateView):
    model = Especialidad
    form_class = EspecialidadForm
    template_name = 'core/especialidad/form.html'
    success_url = reverse_lazy('core:especialidad_list')
    permission_required = 'add_especialidad'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['grabar'] = 'Guardar Especialidad'
        context['back_url'] = self.success_url
        return context

    def form_valid(self, form):
        form.instance.activo = True
        return super().form_valid(form)


class EspecialidadUpdateView(PermissionMixin, UpdateViewMixin, UpdateView):
    model = Especialidad
    form_class = EspecialidadForm
    template_name = 'core/especialidad/form.html'
    success_url = reverse_lazy('core:especialidad_list')
    permission_required = 'change_especialidad'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['grabar'] = 'Actualizar Especialidad'
        context['back_url'] = self.success_url
        return context


class EspecialidadDeleteView(PermissionMixin, DeleteViewMixin, DeleteView):
    model = Especialidad
    template_name = 'core/delete.html'
    success_url = reverse_lazy('core:especialidad_list')
    permission_required = 'delete_especialidad'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Eliminar Especialidad'
        context['cancel_url'] = self.success_url
        
        # Verificar dependencias antes de mostrar el formulario
        especialidad = self.object
        dependencias = []
        
        # Verificar doctores que tienen esta especialidad (relación ManyToMany)
        # El related_name en el modelo Doctor es "especialidades"
        doctores = especialidad.especialidades.all()
        if doctores.exists():
            doctores_count = doctores.count()
            doctores_nombres = [f"{doc.nombres} {doc.apellidos}" for doc in doctores[:3]]
            doctores_text = ', '.join(doctores_nombres)
            if doctores_count > 3:
                doctores_text += f" y {doctores_count - 3} más"
            dependencias.append(f"• {doctores_count} doctor(es): {doctores_text}")
        
        if dependencias:
            context['cannot_delete'] = True
            context['question'] = f'No se puede eliminar la especialidad {especialidad.nombre}'
            context['description'] = self._get_delete_blocked_message(especialidad, dependencias)
        else:
            context['cannot_delete'] = False
            context['question'] = f'¿Está seguro de eliminar la especialidad {especialidad.nombre}?'
            context['description'] = self._get_delete_warning_message(especialidad)
        
        return context

    def _get_delete_blocked_message(self, especialidad, dependencias):
        """Genera mensaje cuando la eliminación está bloqueada"""
        return f"""
        <div class="mb-4">
            <h4 class="text-lg font-semibold text-red-600 mb-2">
                <i class="fas fa-exclamation-triangle mr-2"></i>
                No se puede eliminar la especialidad: {especialidad.nombre}
            </h4>
            <p class="text-gray-700 mb-3">
                <strong>Descripción:</strong> {especialidad.descripcion or 'Sin descripción'}
            </p>
            <p class="text-gray-700 mb-3">
                Esta especialidad está siendo utilizada por doctores y no puede ser eliminada.
            </p>
        </div>
        
        <div class="bg-red-50 border-l-4 border-red-400 p-4 mb-4">
            <h5 class="font-medium text-red-800 mb-2">Dependencias encontradas:</h5>
            <ul class="list-disc list-inside text-red-700 space-y-1">
                {''.join(f'<li>{dep}</li>' for dep in dependencias)}
            </ul>
        </div>
        
        <div class="bg-blue-50 border-l-4 border-blue-400 p-4">
            <h5 class="font-medium text-blue-800 mb-2">
                <i class="fas fa-info-circle mr-1"></i>
                ¿Qué puedes hacer?
            </h5>
            <ul class="list-disc list-inside text-blue-700 space-y-1">
                <li>Quita esta especialidad de los doctores que la tienen asignada</li>
                <li>O asigna otras especialidades a los doctores antes de eliminar esta</li>
                <li>Considera desactivar la especialidad en lugar de eliminarla</li>
                <li>Luego podrás eliminar la especialidad sin problemas</li>
            </ul>
        </div>
        """

    def _get_delete_warning_message(self, especialidad):
        """Genera mensaje de advertencia para eliminación de especialidad"""
        return f"""
        <div class="mb-4">
            <h4 class="text-lg font-semibold text-orange-600 mb-2">
                <i class="fas fa-exclamation-triangle mr-2"></i>
                Eliminar Especialidad: {especialidad.nombre}
            </h4>
            <p class="text-gray-700 mb-3">
                <strong>Descripción:</strong> {especialidad.descripcion or 'Sin descripción'}
            </p>
            <p class="text-gray-700 mb-3">
                Esta acción eliminará permanentemente la especialidad del sistema.
            </p>
        </div>
        
        <div class="bg-orange-50 border-l-4 border-orange-400 p-4 mb-4">
            <h5 class="font-medium text-orange-800 mb-2">Se eliminará la siguiente información:</h5>
            <ul class="list-disc list-inside text-orange-700 space-y-1">
                <li>Especialidad: <strong>{especialidad.nombre}</strong></li>
                <li>Descripción: {especialidad.descripcion or 'Sin descripción'}</li>
                <li>Toda la configuración asociada</li>
            </ul>
        </div>
        
        <div class="bg-blue-50 border-l-4 border-blue-400 p-4">
            <h5 class="font-medium text-blue-800 mb-2">
                <i class="fas fa-info-circle mr-1"></i>
                Información importante
            </h5>
            <ul class="list-disc list-inside text-blue-700 space-y-1">
                <li>Esta acción no se puede deshacer</li>
                <li>La especialidad será eliminada de todas las listas de selección</li>
                <li>Los doctores perderán esta especialidad de su perfil</li>
                <li>Considera desactivar en lugar de eliminar si planeas usarla en el futuro</li>
            </ul>
        </div>
        """

    def delete(self, request, *args, **kwargs):
        """Override del método delete para manejar eliminación con mensajes informativos"""
        self.object = self.get_object()
        nombre_especialidad = self.object.nombre
        success_url = self.get_success_url()
        
        try:
            # Intentar eliminar el objeto
            self.object.delete()
            
            # Agregar mensaje de éxito
            messages.success(request, f'La especialidad "{nombre_especialidad}" ha sido eliminada exitosamente.')
            
        except models.ProtectedError as e:
            # Manejar error de protección por clave foránea
            messages.error(request, f'No se puede eliminar la especialidad "{nombre_especialidad}" porque está siendo utilizada por doctores.')
            
        except Exception as e:
            # Manejar cualquier otro error
            messages.error(request, f'Ocurrió un error al eliminar la especialidad "{nombre_especialidad}": {str(e)}')
            
        return HttpResponseRedirect(success_url)

    def post(self, request, *args, **kwargs):
        """Override del método post para manejar ProtectedError"""
        self.object = self.get_object()
        
        # Verificar dependencias antes de intentar eliminar
        especialidad = self.object
        dependencias = []
        
        # Verificar doctores que tienen esta especialidad
        doctores = especialidad.especialidades.all()
        if doctores.exists():
            messages.error(
                request,
                f"No se puede eliminar la especialidad '{especialidad.nombre}' porque está siendo utilizada por {doctores.count()} doctor(es). "
                f"Quita primero esta especialidad de los doctores que la tienen asignada."
            )
            return HttpResponseRedirect(self.success_url)
        
        try:
            return self.delete(request, *args, **kwargs)
        except models.ProtectedError as e:
            # Capturar el error de protección y mostrar mensaje amigable
            protected_objects = e.protected_objects
            
            # Analizar qué tipo de objetos están protegiendo
            object_types = {}
            for obj in protected_objects:
                obj_type = obj._meta.verbose_name_plural
                if obj_type not in object_types:
                    object_types[obj_type] = 0
                object_types[obj_type] += 1
            
            # Crear mensaje detallado
            obj_details = []
            for obj_type, count in object_types.items():
                obj_details.append(f"{count} {obj_type}")
            
            error_message = (
                f"❌ No se puede eliminar la especialidad '{self.object.nombre}' porque tiene "
                f"registros relacionados que están protegidos: {', '.join(obj_details)}.\n\n"
                f"💡 Para eliminar esta especialidad, primero debes:\n"
                f"   • Quitar esta especialidad de todos los doctores que la tienen asignada\n"
                f"   • O considerar desactivar la especialidad en lugar de eliminarla\n"
                f"   • Luego podrás eliminar la especialidad sin problemas"
            )
            
            messages.error(request, error_message)
            return HttpResponseRedirect(self.success_url)