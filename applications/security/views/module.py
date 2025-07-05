
from django.contrib import messages
from django.urls import reverse_lazy
from django.db import models
from django.http import HttpResponseRedirect
from applications.security.components.mixin_crud import CreateViewMixin, DeleteViewMixin, ListViewMixin, PermissionMixin, UpdateViewMixin
from applications.security.forms.module import ModuleForm
from applications.security.models import Module
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.db.models import Q

class ModuleListView(PermissionMixin, ListViewMixin, ListView):
    template_name = 'security/modules/list.html'
    model = Module
    context_object_name = 'modules'
    permission_required = 'view_module'

    def get_queryset(self):
        q1 = self.request.GET.get('q')
        if q1 is not None:
            self.query.add(Q(name__icontains=q1), Q.OR)
            self.query.add(Q(menu__name__icontains=q1), Q.OR)
        return self.model.objects.filter(self.query).order_by('id')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['create_url'] = reverse_lazy('security:module_create')
        print(context['permissions'])
        return context


class ModuleCreateView(PermissionMixin, CreateViewMixin, CreateView):
    model = Module
    template_name = 'security/modules/form.html'
    form_class = ModuleForm
    success_url = reverse_lazy('security:module_list')
    permission_required = 'add_module'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['grabar'] = 'Grabar Módulo'
        context['back_url'] = self.success_url
        # Debug: imprimir form.permissions
        if 'form' in context:
            print("=== DEBUG FORM PERMISSIONS ===")
            print(f"Form: {context['form']}")
            print(f"Form.permissions: {context['form']['permissions']}")
            print(f"Form.permissions.field: {context['form']['permissions'].field}")
            print(f"Form.permissions.field.queryset: {context['form']['permissions'].field.queryset}")
            for choice in context['form']['permissions']:
                print(f"Choice: {choice}")
                print(f"Choice.tag: {choice.tag}")
                print(f"Choice.choice_label: {choice.choice_label}")
            print("=== END DEBUG ===")
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        module = self.object
        messages.success(self.request, f"Éxito al crear el módulo {module.name}.")
        return response


class ModuleUpdateView(PermissionMixin, UpdateViewMixin, UpdateView):
    model = Module
    template_name = 'security/modules/form.html'
    form_class = ModuleForm
    success_url = reverse_lazy('security:module_list')
    permission_required = 'change_module'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['grabar'] = 'Actualizar Módulo'
        context['back_url'] = self.success_url
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        module = self.object
        messages.success(self.request, f"Éxito al actualizar el módulo {module.name}.")
        return response


class ModuleDeleteView(PermissionMixin, DeleteViewMixin, DeleteView):
    model = Module
    template_name = 'core/delete.html'
    success_url = reverse_lazy('security:module_list')
    permission_required = 'delete_module'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['grabar'] = 'Eliminar Módulo'
        
        # Verificar si el módulo tiene dependencias
        module = self.object
        dependencies_info = self._get_module_dependencies(module)
        
        if dependencies_info['has_dependencies']:
            context['description'] = f"""
            <div class="mb-4">
                <h4 class="text-lg font-semibold text-red-600 mb-2">
                    <i class="fas fa-exclamation-triangle mr-2"></i>
                    No se puede eliminar el módulo: {module.name}
                </h4>
                <p class="text-gray-700 mb-3">
                    Este módulo está siendo utilizado por otros elementos del sistema y no puede ser eliminado.
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
                    <li>Elimina primero los grupos que tienen permisos de este módulo</li>
                    <li>O quita los permisos de este módulo de los grupos que los tienen</li>
                    <li>Luego podrás eliminar este módulo sin problemas</li>
                </ul>
            </div>
            """
            context['cannot_delete'] = True
        else:
            context['description'] = f"""
            <div class="mb-4">
                <h4 class="text-lg font-semibold text-gray-800 mb-2">
                    <i class="fas fa-trash mr-2"></i>
                    ¿Desea eliminar el módulo: {module.name}?
                </h4>
                <p class="text-gray-600">
                    Esta acción eliminará permanentemente el módulo y no se puede deshacer.
                </p>
            </div>
            
            <div class="bg-yellow-50 border-l-4 border-yellow-400 p-4">
                <p class="text-yellow-700">
                    <i class="fas fa-warning mr-1"></i>
                    <strong>Advertencia:</strong> Al eliminar este módulo, también se eliminarán todos sus permisos asociados.
                </p>
            </div>
            """
            context['cannot_delete'] = False
        
        context['back_url'] = self.success_url
        return context
    
    def _get_module_dependencies(self, module):
        """Obtiene información sobre las dependencias del módulo"""
        dependencies = []
        has_dependencies = False
        
        try:
            # Verificar GroupModulePermission
            from applications.security.models import GroupModulePermission
            group_permissions = GroupModulePermission.objects.filter(module=module)
            
            if group_permissions.exists():
                has_dependencies = True
                groups = [gmp.group.name for gmp in group_permissions.distinct('group')]
                groups_text = ', '.join(groups[:3])  # Mostrar máximo 3 grupos
                if len(groups) > 3:
                    groups_text += f" y {len(groups) - 3} más"
                
                dependencies.append(f"<strong>{group_permissions.count()} permisos</strong> asignados a los grupos: <em>{groups_text}</em>")
            
            # Aquí puedes agregar más verificaciones de dependencias si existen otros modelos relacionados
            # Por ejemplo: verificar si hay usuarios que dependen directamente del módulo, etc.
            
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
        dependencies_info = self._get_module_dependencies(self.object)
        if dependencies_info['has_dependencies']:
            messages.error(
                request,
                f"No se puede eliminar el módulo '{self.object.name}' porque está siendo utilizado por otros elementos del sistema. "
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
                f"❌ No se puede eliminar el módulo '{self.object.name}' porque está siendo utilizado por:\n\n"
                f"📋 {'; '.join(error_details)}\n\n"
                f"💡 Para eliminar este módulo, primero debes:\n"
                f"   • Eliminar o modificar los grupos que tienen permisos de este módulo\n"
                f"   • Quitar los permisos de este módulo de todos los grupos\n"
                f"   • Luego podrás eliminar el módulo sin problemas"
            )
            
            messages.error(request, error_message)
            return HttpResponseRedirect(self.success_url)
    
    def form_valid(self, form):
        # Guardar info antes de eliminar
        module_name = self.object.name
        
        try:
            # Llamar al delete del padre
            response = super().form_valid(form)
            
            # Agregar mensaje de éxito
            messages.success(self.request, f"✅ Módulo '{module_name}' eliminado exitosamente.")
            
            return response
            
        except models.ProtectedError:
            # Esto no debería pasar porque ya verificamos en post(), pero por seguridad
            messages.error(
                self.request, 
                f"❌ No se pudo eliminar el módulo '{module_name}' debido a dependencias del sistema."
            )
            return HttpResponseRedirect(self.success_url)