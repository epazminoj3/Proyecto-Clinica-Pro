from django.shortcuts import render
from django.contrib import messages
from django.urls import reverse_lazy
from django.db import models
from django.http import HttpResponseRedirect
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.db.models import Q
from applications.core.models import (
    Empleado, Cargo, Diagnostico, TipoGasto, 
    GastoMensual, TipoSangre
)
from applications.core.forms import (
    EmpleadoForm, CargoForm, DiagnosticoForm, 
    TipoGastoForm, GastoMensualForm, TipoSangreForm
)
from applications.security.components.mixin_crud import CreateViewMixin, DeleteViewMixin, ListViewMixin, PermissionMixin, UpdateViewMixin


# ==================== VISTAS DE EMPLEADO ====================
class EmpleadoListView(PermissionMixin, ListViewMixin, ListView):
    model = Empleado
    template_name = 'core/empleado/list.html'
    context_object_name = 'empleados'
    permission_required = 'view_empleado'

    def get_queryset(self):
        q1 = self.request.GET.get('q')
        if q1 is not None:
            self.query.add(Q(nombres__icontains=q1), Q.OR)
            self.query.add(Q(apellidos__icontains=q1), Q.OR)
            self.query.add(Q(cedula_ecuatoriana__icontains=q1), Q.OR)
            self.query.add(Q(telefono__icontains=q1), Q.OR)
            self.query.add(Q(email__icontains=q1), Q.OR)

        return self.model.objects.select_related('cargo').filter(self.query).order_by('nombres')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['create_url'] = reverse_lazy('core:empleado_create')
        return context


class EmpleadoCreateView(PermissionMixin, CreateViewMixin, CreateView):
    model = Empleado
    form_class = EmpleadoForm
    template_name = 'core/empleado/form.html'
    success_url = reverse_lazy('core:empleado_list')
    permission_required = 'add_empleado'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['grabar'] = 'Guardar Empleado'
        context['back_url'] = self.success_url
        return context

    def form_valid(self, form):
        form.instance.activo = True
        return super().form_valid(form)


class EmpleadoUpdateView(PermissionMixin, UpdateViewMixin, UpdateView):
    model = Empleado
    form_class = EmpleadoForm
    template_name = 'core/empleado/form.html'
    success_url = reverse_lazy('core:empleado_list')
    permission_required = 'change_empleado'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['grabar'] = 'Actualizar Empleado'
        context['back_url'] = self.success_url
        return context


class EmpleadoDeleteView(PermissionMixin, DeleteViewMixin, DeleteView):
    model = Empleado
    template_name = 'core/delete.html'
    success_url = reverse_lazy('core:empleado_list')
    permission_required = 'delete_empleado'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        empleado = self.object
        dependencias = []
        
        # Verificar dependencias - Los empleados pueden no tener dependencias bloqueantes
        # pero podemos verificar si tienen datos asociados
        
        # Por ahora, los empleados no tienen dependencias bloqueantes conocidas
        # pero podemos agregar verificaciones aquí en el futuro
        
        if dependencias:
            context['cannot_delete'] = True
            context['question'] = f'No se puede eliminar al empleado {empleado.nombres} {empleado.apellidos}'
            context['description'] = self._get_delete_blocked_message(empleado, dependencias)
        else:
            context['cannot_delete'] = False
            context['question'] = f'¿Está seguro de eliminar al empleado {empleado.nombres} {empleado.apellidos}?'
            context['description'] = self._get_delete_warning_message(empleado)
        
        return context
    
    def _get_delete_warning_message(self, empleado):
        """Genera mensaje de advertencia para eliminación de empleado"""
        cargo_info = f" ({empleado.cargo.nombre})" if empleado.cargo else ""
        
        return f"""
        <div class="mb-4">
            <h4 class="text-lg font-semibold text-orange-600 mb-2">
                <i class="fas fa-exclamation-triangle mr-2"></i>
                Eliminar Empleado: {empleado.nombres} {empleado.apellidos}{cargo_info}
            </h4>
            <p class="text-gray-700 mb-3">
                Esta acción eliminará permanentemente al empleado y toda su información personal.
            </p>
        </div>
        
        <div class="bg-orange-50 border-l-4 border-orange-400 p-4 mb-4">
            <h5 class="font-medium text-orange-800 mb-2">Se eliminará la siguiente información:</h5>
            <ul class="list-disc list-inside text-orange-700 space-y-1">
                <li>Datos personales (nombres, apellidos, cédula, teléfono, email)</li>
                <li>Información laboral (cargo, fecha de contratación)</li>
                <li>Foto de perfil (si existe)</li>
                <li>Toda la información asociada al empleado</li>
            </ul>
        </div>
        
        <div class="bg-blue-50 border-l-4 border-blue-400 p-4">
            <h5 class="font-medium text-blue-800 mb-2">
                <i class="fas fa-info-circle mr-1"></i>
                Información importante
            </h5>
            <ul class="list-disc list-inside text-blue-700 space-y-1">
                <li>Esta acción no se puede deshacer</li>
                <li>Los archivos asociados se eliminarán del sistema</li>
                <li>El cargo del empleado permanecerá disponible para otros empleados</li>
                <li>Considere desactivar el empleado en lugar de eliminarlo si necesita mantener el historial</li>
            </ul>
        </div>
        """
    
    def _get_delete_blocked_message(self, empleado, dependencias):
        """Genera mensaje cuando la eliminación está bloqueada"""
        cargo_info = f" ({empleado.cargo.nombre})" if empleado.cargo else ""
        
        return f"""
        <div class="mb-4">
            <h4 class="text-lg font-semibold text-red-600 mb-2">
                <i class="fas fa-exclamation-triangle mr-2"></i>
                No se puede eliminar al empleado: {empleado.nombres} {empleado.apellidos}{cargo_info}
            </h4>
            <p class="text-gray-700 mb-3">
                Este empleado tiene registros asociados en el sistema y no puede ser eliminado.
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
                <li>Elimina o transfiere los registros asociados primero</li>
                <li>O considera desactivar el empleado en lugar de eliminarlo</li>
                <li>Luego podrás eliminar el empleado sin problemas</li>
            </ul>
        </div>
        """

    def delete(self, request, *args, **kwargs):
        """Override del método delete para manejar eliminación con mensajes informativos"""
        self.object = self.get_object()
        nombre_completo = f"{self.object.nombres} {self.object.apellidos}"
        success_url = self.get_success_url()
        
        try:
            # Intentar eliminar el objeto
            self.object.delete()
            
            # Agregar mensaje de éxito
            messages.success(request, f'El empleado "{nombre_completo}" ha sido eliminado exitosamente.')
            
        except models.ProtectedError as e:
            # Manejar error de protección por clave foránea
            messages.error(request, f'No se puede eliminar al empleado "{nombre_completo}" porque tiene registros protegidos asociados que no pueden eliminarse.')
            
        except Exception as e:
            # Manejar cualquier otro error
            messages.error(request, f'Ocurrió un error al eliminar al empleado "{nombre_completo}": {str(e)}')
            
        return HttpResponseRedirect(success_url)


# ==================== VISTAS DE CARGO ====================
class CargoListView(PermissionMixin, ListViewMixin, ListView):
    model = Cargo
    template_name = 'core/cargo/list.html'
    context_object_name = 'cargos'
    permission_required = 'view_cargo'

    def get_queryset(self):
        q1 = self.request.GET.get('q')
        if q1 is not None:
            self.query.add(Q(nombre__icontains=q1), Q.OR)
            self.query.add(Q(descripcion__icontains=q1), Q.OR)

        return self.model.objects.filter(self.query).order_by('nombre')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['create_url'] = reverse_lazy('core:cargo_create')
        return context


class CargoCreateView(PermissionMixin, CreateViewMixin, CreateView):
    model = Cargo
    form_class = CargoForm
    template_name = 'core/cargo/form.html'
    success_url = reverse_lazy('core:cargo_list')
    permission_required = 'add_cargo'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['grabar'] = 'Guardar Cargo'
        context['back_url'] = self.success_url
        return context

    def form_valid(self, form):
        form.instance.activo = True
        return super().form_valid(form)


class CargoUpdateView(PermissionMixin, UpdateViewMixin, UpdateView):
    model = Cargo
    form_class = CargoForm
    template_name = 'core/cargo/form.html'
    success_url = reverse_lazy('core:cargo_list')
    permission_required = 'change_cargo'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['grabar'] = 'Actualizar Cargo'
        context['back_url'] = self.success_url
        return context


class CargoDeleteView(PermissionMixin, DeleteViewMixin, DeleteView):
    model = Cargo
    template_name = 'core/delete.html'
    success_url = reverse_lazy('core:cargo_list')
    permission_required = 'delete_cargo'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['grabar'] = 'Eliminar Cargo'
        
        # Verificar si el cargo tiene dependencias
        cargo = self.object
        dependencies_info = self._get_cargo_dependencies(cargo)
        
        if dependencies_info['has_dependencies']:
            context['description'] = f"""
            <div class="mb-4">
                <h4 class="text-lg font-semibold text-red-600 mb-2">
                    <i class="fas fa-exclamation-triangle mr-2"></i>
                    No se puede eliminar el cargo: {cargo.nombre}
                </h4>
                <p class="text-gray-700 mb-3">
                    Este cargo está siendo utilizado por otros elementos del sistema y no puede ser eliminado.
                </p>
            </div>
            
            <div class="bg-red-50 border-l-4 border-red-400 p-4 mb-4">
                <h5 class="font-medium text-red-800 mb-2">Dependencias encontradas:</h5>
                <ul class="list-disc list-inside text-red-700 space-y-1">
                    {dependencies_info['details']}
                </ul>
            </div>
            
            <div class="bg-blue-50 border-l-4 border-blue-400 p-4">
                <h5 class="font-medium text-blue-800 mb-2">
                    <i class="fas fa-info-circle mr-1"></i>
                    ¿Qué puedes hacer?
                </h5>
                <ul class="list-disc list-inside text-blue-700 space-y-1">
                    <li>Cambia el cargo de los empleados que lo tienen asignado</li>
                    <li>O elimina los empleados asociados a este cargo</li>
                    <li>Luego podrás eliminar este cargo sin problemas</li>
                </ul>
            </div>
            """
            context['cannot_delete'] = True
        else:
            context['description'] = f"""
            <div class="mb-4">
                <h4 class="text-lg font-semibold text-gray-800 mb-2">
                    <i class="fas fa-trash mr-2"></i>
                    ¿Desea eliminar el cargo: {cargo.nombre}?
                </h4>
                <p class="text-gray-600">
                    Esta acción eliminará permanentemente el cargo y no se puede deshacer.
                </p>
            </div>
            
            <div class="bg-yellow-50 border-l-4 border-yellow-400 p-4">
                <p class="text-yellow-700">
                    <i class="fas fa-warning mr-1"></i>
                    <strong>Advertencia:</strong> Al eliminar este cargo, también se eliminarán todas sus configuraciones.
                </p>
            </div>
            """
            context['cannot_delete'] = False
        
        context['back_url'] = self.success_url
        return context
    
    def _get_cargo_dependencies(self, cargo):
        """Obtiene información sobre las dependencias del cargo"""
        dependencies = []
        has_dependencies = False
        
        try:
            # Verificar Empleados que tienen este cargo
            empleados = Empleado.objects.filter(cargo=cargo)
            if empleados.exists():
                has_dependencies = True
                empleados_names = [emp.nombres for emp in empleados[:3]]
                empleados_text = ', '.join(empleados_names)
                if empleados.count() > 3:
                    empleados_text += f" y {empleados.count() - 3} más"
                dependencies.append(f"<strong>{empleados.count()} empleado(s)</strong>: <em>{empleados_text}</em>")
            
        except Exception as e:
            dependencies.append(f"Error al verificar dependencias: {str(e)}")
        
        details_html = ""
        if dependencies:
            for dep in dependencies:
                details_html += f"<li>{dep}</li>"
        
        return {
            'has_dependencies': has_dependencies,
            'details': details_html,
            'count': len(dependencies)
        }

    def post(self, request, *args, **kwargs):
        """Override del método post para manejar ProtectedError"""
        self.object = self.get_object()
        
        # Verificar dependencias antes de intentar eliminar
        dependencies_info = self._get_cargo_dependencies(self.object)
        if dependencies_info['has_dependencies']:
            messages.error(
                request,
                f"No se puede eliminar el cargo '{self.object.nombre}' porque está siendo utilizado por otros elementos del sistema. "
                f"Elimina primero las dependencias mostradas en la página anterior."
            )
            return HttpResponseRedirect(self.success_url)
        
        try:
            return super().post(request, *args, **kwargs)
        except models.ProtectedError as e:
            # Capturar el error de protección y mostrar mensaje amigable
            protected_objects = e.protected_objects
            
            # Analizar qué tipo de objetos están protegiendo
            object_types = {}
            for obj in protected_objects:
                obj_type = obj._meta.verbose_name_plural
                if obj_type not in object_types:
                    object_types[obj_type] = []
                object_types[obj_type].append(str(obj))
            
            # Crear mensaje detallado
            error_details = []
            for obj_type, objects in object_types.items():
                count = len(objects)
                if count <= 3:
                    objects_list = ", ".join(objects)
                    error_details.append(f"{count} {obj_type}: {objects_list}")
                else:
                    objects_list = ", ".join(objects[:3])
                    error_details.append(f"{count} {obj_type}: {objects_list} y {count-3} más")
            
            error_message = (
                f"❌ No se puede eliminar el cargo '{self.object.nombre}' porque está siendo utilizado por:\n\n"
                f"📋 {'; '.join(error_details)}\n\n"
                f"💡 Para eliminar este cargo, primero debes:\n"
                f"   • Cambiar el cargo de los empleados que lo tienen asignado\n"
                f"   • O eliminar los empleados asociados\n"
                f"   • Luego podrás eliminar el cargo sin problemas"
            )
            
            messages.error(request, error_message)
            return HttpResponseRedirect(self.success_url)
    
    def form_valid(self, form):
        # Guardar info antes de eliminar
        cargo_name = self.object.nombre
        
        try:
            # Llamar al delete del padre
            response = super().form_valid(form)
            
            # Agregar mensaje de éxito
            messages.success(self.request, f"✅ Cargo '{cargo_name}' eliminado exitosamente.")
            
            return response
            
        except models.ProtectedError:
            # Esto no debería pasar porque ya verificamos en post(), pero por seguridad
            messages.error(
                self.request, 
                f"❌ No se pudo eliminar el cargo '{cargo_name}' debido a dependencias del sistema."
            )
            return HttpResponseRedirect(self.success_url)


# ==================== VISTAS DE DIAGNOSTICO ====================
class DiagnosticoListView(PermissionMixin, ListViewMixin, ListView):
    model = Diagnostico
    template_name = 'core/diagnostico/list.html'
    context_object_name = 'diagnosticos'
    permission_required = 'view_diagnostico'

    def get_queryset(self):
        q1 = self.request.GET.get('q')
        if q1 is not None:
            self.query.add(Q(codigo__icontains=q1), Q.OR)
            self.query.add(Q(descripcion__icontains=q1), Q.OR)

        return self.model.objects.filter(self.query).order_by('codigo')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['create_url'] = reverse_lazy('core:diagnostico_create')
        return context


class DiagnosticoCreateView(PermissionMixin, CreateViewMixin, CreateView):
    model = Diagnostico
    form_class = DiagnosticoForm
    template_name = 'core/diagnostico/form.html'
    success_url = reverse_lazy('core:diagnostico_list')
    permission_required = 'add_diagnostico'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['grabar'] = 'Guardar Diagnóstico'
        context['back_url'] = self.success_url
        return context

    def form_valid(self, form):
        form.instance.activo = True
        return super().form_valid(form)


class DiagnosticoUpdateView(PermissionMixin, UpdateViewMixin, UpdateView):
    model = Diagnostico
    form_class = DiagnosticoForm
    template_name = 'core/diagnostico/form.html'
    success_url = reverse_lazy('core:diagnostico_list')
    permission_required = 'change_diagnostico'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['grabar'] = 'Actualizar Diagnóstico'
        context['back_url'] = self.success_url
        return context


class DiagnosticoDeleteView(PermissionMixin, DeleteViewMixin, DeleteView):
    model = Diagnostico
    template_name = 'core/delete.html'
    success_url = reverse_lazy('core:diagnostico_list')
    permission_required = 'delete_diagnostico'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        diagnostico = self.object
        dependencias = []
        
        # Verificar dependencias - Los diagnósticos pueden estar referenciados en atenciones médicas
        # Verificar si hay atenciones que usan este diagnóstico
        try:
            from applications.doctor.models import Atencion
            atenciones = Atencion.objects.filter(diagnostico=diagnostico)
            if atenciones.exists():
                atenciones_count = atenciones.count()
                atenciones_info = [f"{atencion.paciente.nombres} {atencion.paciente.apellidos}" for atencion in atenciones[:3]]
                atenciones_text = ', '.join(atenciones_info)
                if atenciones_count > 3:
                    atenciones_text += f" y {atenciones_count - 3} más"
                dependencias.append(f"• {atenciones_count} atención(es) médica(s): {atenciones_text}")
        except ImportError:
            # Si no existe el modelo Atencion, continuar sin verificar
            pass
        except Exception as e:
            # Manejar cualquier otro error silenciosamente
            pass
        
        if dependencias:
            context['cannot_delete'] = True
            context['question'] = f'No se puede eliminar el diagnóstico {diagnostico.codigo}'
            context['description'] = self._get_delete_blocked_message(diagnostico, dependencias)
        else:
            context['cannot_delete'] = False
            context['question'] = f'¿Está seguro de eliminar el diagnóstico {diagnostico.codigo}?'
            context['description'] = self._get_delete_warning_message(diagnostico)
        
        return context
    
    def _get_delete_warning_message(self, diagnostico):
        """Genera mensaje de advertencia para eliminación de diagnóstico"""
        return f"""
        <div class="mb-4">
            <h4 class="text-lg font-semibold text-orange-600 mb-2">
                <i class="fas fa-exclamation-triangle mr-2"></i>
                Eliminar Diagnóstico: {diagnostico.codigo}
            </h4>
            <p class="text-gray-700 mb-3">
                <strong>Descripción:</strong> {diagnostico.descripcion}
            </p>
            <p class="text-gray-700 mb-3">
                Esta acción eliminará permanentemente el diagnóstico del sistema.
            </p>
        </div>
        
        <div class="bg-orange-50 border-l-4 border-orange-400 p-4 mb-4">
            <h5 class="font-medium text-orange-800 mb-2">Se eliminará la siguiente información:</h5>
            <ul class="list-disc list-inside text-orange-700 space-y-1">
                <li>Código del diagnóstico: <strong>{diagnostico.codigo}</strong></li>
                <li>Descripción: {diagnostico.descripcion}</li>
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
                <li>Asegúrese de que ninguna atención médica use este diagnóstico</li>
                <li>El diagnóstico será eliminado de todas las listas de selección</li>
                <li>Considere desactivar el diagnóstico en lugar de eliminarlo</li>
            </ul>
        </div>
        """
    
    def _get_delete_blocked_message(self, diagnostico, dependencias):
        """Genera mensaje cuando la eliminación está bloqueada"""
        return f"""
        <div class="mb-4">
            <h4 class="text-lg font-semibold text-red-600 mb-2">
                <i class="fas fa-exclamation-triangle mr-2"></i>
                No se puede eliminar el diagnóstico: {diagnostico.codigo}
            </h4>
            <p class="text-gray-700 mb-3">
                <strong>Descripción:</strong> {diagnostico.descripcion}
            </p>
            <p class="text-gray-700 mb-3">
                Este diagnóstico está siendo utilizado en atenciones médicas y no puede ser eliminado.
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
                <li>Cambia el diagnóstico en las atenciones médicas que lo usan</li>
                <li>O elimina las atenciones médicas que usan este diagnóstico</li>
                <li>Luego podrás eliminar el diagnóstico sin problemas</li>
                <li>Alternativamente, considera desactivar el diagnóstico</li>
            </ul>
        </div>
        """

    def delete(self, request, *args, **kwargs):
        """Override del método delete para manejar eliminación con mensajes informativos"""
        self.object = self.get_object()
        codigo_diagnostico = self.object.codigo
        success_url = self.get_success_url()
        
        try:
            # Intentar eliminar el objeto
            self.object.delete()
            
            # Agregar mensaje de éxito
            messages.success(request, f'El diagnóstico "{codigo_diagnostico}" ha sido eliminado exitosamente.')
            
        except models.ProtectedError as e:
            # Manejar error de protección por clave foránea
            messages.error(request, f'No se puede eliminar el diagnóstico "{codigo_diagnostico}" porque está siendo utilizado en atenciones médicas.')
            
        except Exception as e:
            # Manejar cualquier otro error
            messages.error(request, f'Ocurrió un error al eliminar el diagnóstico "{codigo_diagnostico}": {str(e)}')
            
        return HttpResponseRedirect(success_url)


# ==================== VISTAS DE TIPO GASTO ====================
class TipoGastoListView(PermissionMixin, ListViewMixin, ListView):
    model = TipoGasto
    template_name = 'core/tipo_gasto/list.html'
    context_object_name = 'tipos'
    permission_required = 'view_tipogasto'

    def get_queryset(self):
        q1 = self.request.GET.get('q')
        if q1 is not None:
            self.query.add(Q(nombre__icontains=q1), Q.OR)
            self.query.add(Q(descripcion__icontains=q1), Q.OR)

        return self.model.objects.filter(self.query).order_by('nombre')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['create_url'] = reverse_lazy('core:tipo_gasto_create')
        return context


class TipoGastoCreateView(PermissionMixin, CreateViewMixin, CreateView):
    model = TipoGasto
    form_class = TipoGastoForm
    template_name = 'core/tipo_gasto/form.html'
    success_url = reverse_lazy('core:tipo_gasto_list')
    permission_required = 'add_tipogasto'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['grabar'] = 'Guardar Tipo de Gasto'
        context['back_url'] = self.success_url
        return context

    def form_valid(self, form):
        form.instance.activo = True
        return super().form_valid(form)


class TipoGastoUpdateView(PermissionMixin, UpdateViewMixin, UpdateView):
    model = TipoGasto
    form_class = TipoGastoForm
    template_name = 'core/tipo_gasto/form.html'
    success_url = reverse_lazy('core:tipo_gasto_list')
    permission_required = 'change_tipogasto'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['grabar'] = 'Actualizar Tipo de Gasto'
        context['back_url'] = self.success_url
        return context


class TipoGastoDeleteView(PermissionMixin, DeleteViewMixin, DeleteView):
    model = TipoGasto
    template_name = 'core/delete.html'
    success_url = reverse_lazy('core:tipo_gasto_list')
    permission_required = 'delete_tipogasto'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tipo_gasto = self.object
        dependencias = []
        
        # Verificar dependencias - Los tipos de gasto pueden estar referenciados en gastos mensuales
        try:
            gastos = GastoMensual.objects.filter(tipo_gasto=tipo_gasto)
            if gastos.exists():
                gastos_count = gastos.count()
                gastos_info = [f"{gasto.observacion[:30]}..." if len(gasto.observacion) > 30 else gasto.observacion for gasto in gastos[:3]]
                gastos_text = ', '.join(gastos_info)
                if gastos_count > 3:
                    gastos_text += f" y {gastos_count - 3} más"
                dependencias.append(f"• {gastos_count} gasto(s) mensual(es): {gastos_text}")
        except Exception as e:
            # Manejar cualquier error silenciosamente
            pass
        
        if dependencias:
            context['cannot_delete'] = True
            context['question'] = f'No se puede eliminar el tipo de gasto {tipo_gasto.nombre}'
            context['description'] = self._get_delete_blocked_message(tipo_gasto, dependencias)
        else:
            context['cannot_delete'] = False
            context['question'] = f'¿Está seguro de eliminar el tipo de gasto {tipo_gasto.nombre}?'
            context['description'] = self._get_delete_warning_message(tipo_gasto)
        
        return context
    
    def _get_delete_warning_message(self, tipo_gasto):
        """Genera mensaje de advertencia para eliminación de tipo de gasto"""
        return f"""
        <div class="mb-4">
            <h4 class="text-lg font-semibold text-orange-600 mb-2">
                <i class="fas fa-exclamation-triangle mr-2"></i>
                Eliminar Tipo de Gasto: {tipo_gasto.nombre}
            </h4>
            <p class="text-gray-700 mb-3">
                <strong>Descripción:</strong> {tipo_gasto.descripcion}
            </p>
            <p class="text-gray-700 mb-3">
                Esta acción eliminará permanentemente el tipo de gasto del sistema.
            </p>
        </div>
        
        <div class="bg-orange-50 border-l-4 border-orange-400 p-4 mb-4">
            <h5 class="font-medium text-orange-800 mb-2">Se eliminará la siguiente información:</h5>
            <ul class="list-disc list-inside text-orange-700 space-y-1">
                <li>Nombre del tipo: <strong>{tipo_gasto.nombre}</strong></li>
                <li>Descripción: {tipo_gasto.descripcion}</li>
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
                <li>Asegúrese de que ningún gasto mensual use este tipo</li>
                <li>El tipo será eliminado de todas las listas de selección</li>
                <li>Considere desactivar el tipo en lugar de eliminarlo</li>
            </ul>
        </div>
        """
    
    def _get_delete_blocked_message(self, tipo_gasto, dependencias):
        """Genera mensaje cuando la eliminación está bloqueada"""
        return f"""
        <div class="mb-4">
            <h4 class="text-lg font-semibold text-red-600 mb-2">
                <i class="fas fa-exclamation-triangle mr-2"></i>
                No se puede eliminar el tipo de gasto: {tipo_gasto.nombre}
            </h4>
            <p class="text-gray-700 mb-3">
                <strong>Descripción:</strong> {tipo_gasto.descripcion}
            </p>
            <p class="text-gray-700 mb-3">
                Este tipo de gasto está siendo utilizado en gastos mensuales y no puede ser eliminado.
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
                <li>Cambia el tipo de gasto en los gastos mensuales que lo usan</li>
                <li>O elimina los gastos mensuales que usan este tipo</li>
                <li>Luego podrás eliminar el tipo de gasto sin problemas</li>
                <li>Alternativamente, considera desactivar el tipo</li>
            </ul>
        </div>
        """

    def delete(self, request, *args, **kwargs):
        """Override del método delete para manejar eliminación con mensajes informativos"""
        self.object = self.get_object()
        nombre_tipo = self.object.nombre
        success_url = self.get_success_url()
        
        try:
            # Intentar eliminar el objeto
            self.object.delete()
            
            # Agregar mensaje de éxito
            messages.success(request, f'El tipo de gasto "{nombre_tipo}" ha sido eliminado exitosamente.')
            
        except models.ProtectedError as e:
            # Manejar error de protección por clave foránea
            messages.error(request, f'No se puede eliminar el tipo de gasto "{nombre_tipo}" porque está siendo utilizado en gastos mensuales.')
            
        except Exception as e:
            # Manejar cualquier otro error
            messages.error(request, f'Ocurrió un error al eliminar el tipo de gasto "{nombre_tipo}": {str(e)}')
            
        return HttpResponseRedirect(success_url)


# ==================== VISTAS DE GASTO MENSUAL ====================
class GastoMensualListView(PermissionMixin, ListViewMixin, ListView):
    model = GastoMensual
    template_name = 'core/gasto_mensual/list.html'
    context_object_name = 'gastos'
    permission_required = 'view_gastomensual'

    def get_queryset(self):
        q1 = self.request.GET.get('q')
        if q1 is not None:
            self.query.add(Q(observacion__icontains=q1), Q.OR)
            self.query.add(Q(tipo_gasto__nombre__icontains=q1), Q.OR)

        return self.model.objects.select_related('tipo_gasto').filter(self.query).order_by('-fecha')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['create_url'] = reverse_lazy('core:gasto_mensual_create')
        return context


class GastoMensualCreateView(PermissionMixin, CreateViewMixin, CreateView):
    model = GastoMensual
    form_class = GastoMensualForm
    template_name = 'core/gasto_mensual/form.html'
    success_url = reverse_lazy('core:gasto_mensual_list')
    permission_required = 'add_gastomensual'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['grabar'] = 'Guardar Gasto'
        context['back_url'] = self.success_url
        return context


class GastoMensualUpdateView(PermissionMixin, UpdateViewMixin, UpdateView):
    model = GastoMensual
    form_class = GastoMensualForm
    template_name = 'core/gasto_mensual/form.html'
    success_url = reverse_lazy('core:gasto_mensual_list')
    permission_required = 'change_gastomensual'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['grabar'] = 'Actualizar Gasto'
        context['back_url'] = self.success_url
        return context


class GastoMensualDeleteView(PermissionMixin, DeleteViewMixin, DeleteView):
    model = GastoMensual
    template_name = 'core/delete.html'
    success_url = reverse_lazy('core:gasto_mensual_list')
    permission_required = 'delete_gastomensual'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        gasto = self.object
        dependencias = []
        
        # Los gastos mensuales normalmente no tienen dependencias bloqueantes
        # Son registros de gastos específicos sin referencias desde otros modelos
        
        # No hay dependencias bloqueantes para gastos mensuales
        context['cannot_delete'] = False
        context['question'] = f'¿Está seguro de eliminar este gasto mensual?'
        context['description'] = self._get_delete_warning_message(gasto)
        
        return context
    
    def _get_delete_warning_message(self, gasto):
        """Genera mensaje de advertencia para eliminación de gasto mensual"""
        fecha_formateada = gasto.fecha.strftime('%d/%m/%Y')
        observacion_corta = gasto.observacion[:50] + "..." if len(gasto.observacion) > 50 else gasto.observacion
        
        return f"""
        <div class="mb-4">
            <h4 class="text-lg font-semibold text-orange-600 mb-2">
                <i class="fas fa-exclamation-triangle mr-2"></i>
                Eliminar Gasto Mensual
            </h4>
            <p class="text-gray-700 mb-3">
                Esta acción eliminará permanentemente el registro de gasto del sistema.
            </p>
        </div>
        
        <div class="bg-orange-50 border-l-4 border-orange-400 p-4 mb-4">
            <h5 class="font-medium text-orange-800 mb-2">Se eliminará la siguiente información:</h5>
            <ul class="list-disc list-inside text-orange-700 space-y-1">
                <li>Fecha: <strong>{fecha_formateada}</strong></li>
                <li>Tipo de gasto: <strong>{gasto.tipo_gasto.nombre}</strong></li>
                <li>Valor: <strong>${gasto.valor}</strong></li>
                <li>Observación: {observacion_corta}</li>
                <li>Toda la información asociada al gasto</li>
            </ul>
        </div>
        
        <div class="bg-blue-50 border-l-4 border-blue-400 p-4">
            <h5 class="font-medium text-blue-800 mb-2">
                <i class="fas fa-info-circle mr-1"></i>
                Información importante
            </h5>
            <ul class="list-disc list-inside text-blue-700 space-y-1">
                <li>Esta acción no se puede deshacer</li>
                <li>El registro será eliminado de los reportes financieros</li>
                <li>El tipo de gasto permanecerá disponible para otros registros</li>
                <li>Asegúrese de que no necesite este registro para auditorías</li>
            </ul>
        </div>
        """

    def delete(self, request, *args, **kwargs):
        """Override del método delete para manejar eliminación con mensajes informativos"""
        self.object = self.get_object()
        fecha_formateada = self.object.fecha.strftime('%d/%m/%Y')
        tipo_gasto = self.object.tipo_gasto.nombre
        valor = self.object.valor
        success_url = self.get_success_url()
        
        try:
            # Intentar eliminar el objeto
            self.object.delete()
            
            # Agregar mensaje de éxito
            messages.success(request, f'El gasto mensual del {fecha_formateada} ({tipo_gasto} - ${valor}) ha sido eliminado exitosamente.')
            
        except models.ProtectedError as e:
            # Manejar error de protección por clave foránea
            messages.error(request, f'No se puede eliminar el gasto mensual porque tiene registros protegidos asociados.')
            
        except Exception as e:
            # Manejar cualquier otro error
            messages.error(request, f'Ocurrió un error al eliminar el gasto mensual: {str(e)}')
            
        return HttpResponseRedirect(success_url)


# ==================== VISTAS DE TIPO SANGRE ====================
class TipoSangreListView(PermissionMixin, ListViewMixin, ListView):
    model = TipoSangre
    template_name = 'core/tipo_sangre/list.html'
    context_object_name = 'tipos'
    permission_required = 'view_tiposangre'

    def get_queryset(self):
        q1 = self.request.GET.get('q')
        if q1 is not None:
            self.query.add(Q(tipo__icontains=q1), Q.OR)

        return self.model.objects.filter(self.query).order_by('tipo')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['create_url'] = reverse_lazy('core:tipo_sangre_create')
        return context


class TipoSangreCreateView(PermissionMixin, CreateViewMixin, CreateView):
    model = TipoSangre
    form_class = TipoSangreForm
    template_name = 'core/tipo_sangre/form.html'
    success_url = reverse_lazy('core:tipo_sangre_list')
    permission_required = 'add_tiposangre'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['grabar'] = 'Guardar Tipo de Sangre'
        context['back_url'] = self.success_url
        return context


class TipoSangreUpdateView(PermissionMixin, UpdateViewMixin, UpdateView):
    model = TipoSangre
    form_class = TipoSangreForm
    template_name = 'core/tipo_sangre/form.html'
    success_url = reverse_lazy('core:tipo_sangre_list')
    permission_required = 'change_tiposangre'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['grabar'] = 'Actualizar Tipo de Sangre'
        context['back_url'] = self.success_url
        return context


class TipoSangreDeleteView(PermissionMixin, DeleteViewMixin, DeleteView):
    model = TipoSangre
    template_name = 'core/delete.html'
    success_url = reverse_lazy('core:tipo_sangre_list')
    permission_required = 'delete_tiposangre'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tipo_sangre = self.object
        dependencias = []
        
        # Verificar dependencias - Los tipos de sangre pueden estar referenciados en pacientes
        try:
            from applications.core.models import Paciente
            pacientes = Paciente.objects.filter(tipo_sangre=tipo_sangre)
            if pacientes.exists():
                pacientes_count = pacientes.count()
                pacientes_info = [f"{paciente.nombres} {paciente.apellidos}" for paciente in pacientes[:3]]
                pacientes_text = ', '.join(pacientes_info)
                if pacientes_count > 3:
                    pacientes_text += f" y {pacientes_count - 3} más"
                dependencias.append(f"• {pacientes_count} paciente(s): {pacientes_text}")
        except Exception as e:
            # Manejar cualquier error silenciosamente
            pass
        
        if dependencias:
            context['cannot_delete'] = True
            context['question'] = f'No se puede eliminar el tipo de sangre {tipo_sangre.tipo}'
            context['description'] = self._get_delete_blocked_message(tipo_sangre, dependencias)
        else:
            context['cannot_delete'] = False
            context['question'] = f'¿Está seguro de eliminar el tipo de sangre {tipo_sangre.tipo}?'
            context['description'] = self._get_delete_warning_message(tipo_sangre)
        
        return context
    
    def _get_delete_warning_message(self, tipo_sangre):
        """Genera mensaje de advertencia para eliminación de tipo de sangre"""
        return f"""
        <div class="mb-4">
            <h4 class="text-lg font-semibold text-orange-600 mb-2">
                <i class="fas fa-exclamation-triangle mr-2"></i>
                Eliminar Tipo de Sangre: {tipo_sangre.tipo}
            </h4>
            <p class="text-gray-700 mb-3">
                <strong>Descripción:</strong> {tipo_sangre.descripcion}
            </p>
            <p class="text-gray-700 mb-3">
                Esta acción eliminará permanentemente el tipo de sangre del sistema.
            </p>
        </div>
        
        <div class="bg-orange-50 border-l-4 border-orange-400 p-4 mb-4">
            <h5 class="font-medium text-orange-800 mb-2">Se eliminará la siguiente información:</h5>
            <ul class="list-disc list-inside text-orange-700 space-y-1">
                <li>Tipo de sangre: <strong>{tipo_sangre.tipo}</strong></li>
                <li>Descripción: {tipo_sangre.descripcion}</li>
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
                <li>Asegúrese de que ningún paciente tenga asignado este tipo de sangre</li>
                <li>El tipo será eliminado de todas las listas de selección</li>
                <li>Los tipos de sangre son datos médicos críticos</li>
            </ul>
        </div>
        """
    
    def _get_delete_blocked_message(self, tipo_sangre, dependencias):
        """Genera mensaje cuando la eliminación está bloqueada"""
        return f"""
        <div class="mb-4">
            <h4 class="text-lg font-semibold text-red-600 mb-2">
                <i class="fas fa-exclamation-triangle mr-2"></i>
                No se puede eliminar el tipo de sangre: {tipo_sangre.tipo}
            </h4>
            <p class="text-gray-700 mb-3">
                <strong>Descripción:</strong> {tipo_sangre.descripcion}
            </p>
            <p class="text-gray-700 mb-3">
                Este tipo de sangre está siendo utilizado por pacientes y no puede ser eliminado.
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
                <li>Cambia el tipo de sangre en los pacientes que lo tienen asignado</li>
                <li>O elimina los pacientes que usan este tipo de sangre</li>
                <li>Luego podrás eliminar el tipo de sangre sin problemas</li>
                <li><strong>Precaución:</strong> Los tipos de sangre son datos médicos críticos</li>
            </ul>
        </div>
        """

    def delete(self, request, *args, **kwargs):
        """Override del método delete para manejar eliminación con mensajes informativos"""
        self.object = self.get_object()
        tipo_sangre = self.object.tipo
        success_url = self.get_success_url()
        
        try:
            # Intentar eliminar el objeto
            self.object.delete()
            
            # Agregar mensaje de éxito
            messages.success(request, f'El tipo de sangre "{tipo_sangre}" ha sido eliminado exitosamente.')
            
        except models.ProtectedError as e:
            # Manejar error de protección por clave foránea
            messages.error(request, f'No se puede eliminar el tipo de sangre "{tipo_sangre}" porque está siendo utilizado por pacientes.')
            
        except Exception as e:
            # Manejar cualquier otro error
            messages.error(request, f'Ocurrió un error al eliminar el tipo de sangre "{tipo_sangre}": {str(e)}')
            
        return HttpResponseRedirect(success_url)