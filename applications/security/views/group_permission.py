from django.contrib import messages
from django.urls import reverse_lazy
from django.db import models
from django.http import HttpResponseRedirect
from applications.security.components.mixin_crud import CreateViewMixin, DeleteViewMixin, ListViewMixin, PermissionMixin, UpdateViewMixin
from applications.security.forms.group_permission import GroupModulePermissionForm
from applications.security.models import Menu, Module, User, GroupModulePermission
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.db.models import Q
from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login

# ================================
# VISTAS PARA GROUP MODULE PERMISSION
# ================================

class GroupModulePermissionListView(PermissionMixin, ListViewMixin, ListView):
    template_name = 'security/group_permissions/list.html'
    model = GroupModulePermission
    context_object_name = 'group_permissions'
    permission_required = 'view_groupmodulepermission'

    def get_queryset(self):
        q1 = self.request.GET.get('q')
        if q1 is not None:
            self.query.add(Q(group__name__icontains=q1), Q.OR)
            self.query.add(Q(module__name__icontains=q1), Q.OR)
            self.query.add(Q(module__menu__name__icontains=q1), Q.OR)

        return self.model.objects.select_related('group', 'module', 'module__menu').filter(self.query).order_by('module__menu__order', 'module__order', 'group__name')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['create_url'] = reverse_lazy('security:group_permission_dynamic')  # Usar gestión dinámica por defecto
        context['create_traditional_url'] = reverse_lazy('security:group_permission_create')  # Opción tradicional
        return context


class GroupModulePermissionCreateView(PermissionMixin, CreateViewMixin, CreateView):
    model = GroupModulePermission
    template_name = 'security/group_permissions/form_traditional.html'
    form_class = GroupModulePermissionForm
    success_url = reverse_lazy('security:group_permission_list')
    permission_required = 'add_groupmodulepermission'

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        context['grabar'] = 'Grabar Permisos de Grupo'
        context['back_url'] = self.success_url
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        group_permission = self.object
        messages.success(self.request, f"Éxito al crear los permisos para {group_permission.group.name} - {group_permission.module.name}.")
        return response


class GroupModulePermissionUpdateView(PermissionMixin, UpdateViewMixin, UpdateView):
    model = GroupModulePermission
    template_name = 'security/group_permissions/form_traditional.html'
    form_class = GroupModulePermissionForm
    success_url = reverse_lazy('security:group_permission_list')
    permission_required = 'change_groupmodulepermission'

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        context['grabar'] = 'Actualizar Permisos de Grupo'
        context['back_url'] = self.success_url
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        group_permission = self.object
        messages.success(self.request, f"Éxito al actualizar los permisos para {group_permission.group.name} - {group_permission.module.name}.")
        return response


class GroupModulePermissionDeleteView(PermissionMixin, DeleteViewMixin, DeleteView):
    model = GroupModulePermission
    template_name = 'core/delete.html'
    success_url = reverse_lazy('security:group_permission_list')
    permission_required = 'delete_groupmodulepermission'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['grabar'] = 'Eliminar Permisos de Grupo'
        
        # Verificar si los permisos tienen dependencias
        group_permission = self.object
        dependencies_info = self._get_permission_dependencies(group_permission)
        
        if dependencies_info['has_dependencies']:
            context['description'] = f"""
            <div class="mb-4">
                <h4 class="text-lg font-semibold text-red-600 mb-2">
                    <i class="fas fa-exclamation-triangle mr-2"></i>
                    No se puede eliminar los permisos: {group_permission.group.name} - {group_permission.module.name}
                </h4>
                <p class="text-gray-700 mb-3">
                    Estos permisos están siendo utilizados por otros elementos del sistema y no pueden ser eliminados.
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
                    <li>Revisa si hay usuarios activos dependiendo de estos permisos</li>
                    <li>Quita los usuarios del grupo antes de eliminar los permisos</li>
                    <li>O cambia los usuarios a otros grupos con permisos similares</li>
                    <li>Luego podrás eliminar estos permisos sin problemas</li>
                </ul>
            </div>
            """
            context['cannot_delete'] = True
        else:
            context['description'] = f"""
            <div class="mb-4">
                <h4 class="text-lg font-semibold text-gray-800 mb-2">
                    <i class="fas fa-trash mr-2"></i>
                    ¿Desea eliminar los permisos: {group_permission.group.name} - {group_permission.module.name}?
                </h4>
                <p class="text-gray-600">
                    Esta acción eliminará permanentemente estos permisos del grupo y no se puede deshacer.
                </p>
            </div>
            
            <div class="bg-yellow-50 border-l-4 border-yellow-400 p-4">
                <p class="text-yellow-700">
                    <i class="fas fa-warning mr-1"></i>
                    <strong>Advertencia:</strong> Los usuarios en el grupo "{group_permission.group.name}" perderán acceso al módulo "{group_permission.module.name}".
                </p>
            </div>
            """
            context['cannot_delete'] = False
        
        context['back_url'] = self.success_url
        return context
    
    def _get_permission_dependencies(self, group_permission):
        """Obtiene información sobre las dependencias de los permisos"""
        dependencies = []
        has_dependencies = False
        
        try:
            # Verificar usuarios activos en el grupo
            active_users = group_permission.group.user_set.filter(is_active=True)
            if active_users.exists():
                # Solo marcamos como dependencia si hay usuarios activos
                # Los permisos pueden eliminarse, pero es importante advertir sobre el impacto
                users_names = [user.username for user in active_users[:3]]
                users_text = ', '.join(users_names)
                if active_users.count() > 3:
                    users_text += f" y {active_users.count() - 3} más"
                
                # Dependencia informativa (no bloquea eliminación)
                dependencies.append(f"<strong>{active_users.count()} usuario(s) activo(s)</strong> en el grupo: <em>{users_text}</em>")
                dependencies.append(f"Estos usuarios perderán acceso al módulo <strong>{group_permission.module.name}</strong>")
            
            # Verificar si es el único permiso del grupo para este módulo
            module_permissions_count = GroupModulePermission.objects.filter(
                group=group_permission.group,
                module=group_permission.module
            ).count()
            
            if module_permissions_count == 1 and active_users.exists():
                # Es el único permiso y hay usuarios activos - podría ser crítico
                dependencies.append(f"Este es el <strong>único conjunto de permisos</strong> del grupo para el módulo <em>{group_permission.module.name}</em>")
            
            # Los permisos generalmente se pueden eliminar, pero mostramos el impacto
            # Solo bloqueamos en casos muy específicos (por ejemplo, si es un permiso crítico del sistema)
            
            # Ejemplo: bloquear eliminación de permisos críticos del sistema
            if (group_permission.group.name.lower() in ['administrador', 'admin', 'superadmin'] and 
                group_permission.module.name.lower() in ['usuarios', 'permisos', 'seguridad']):
                has_dependencies = True
                dependencies.append(f"<strong>Permiso crítico del sistema</strong>: No se puede eliminar permisos de administración del grupo {group_permission.group.name}")
            
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
        dependencies_info = self._get_permission_dependencies(self.object)
        if dependencies_info['has_dependencies']:
            messages.error(
                request,
                f"No se puede eliminar los permisos '{self.object.group.name} - {self.object.module.name}' porque son críticos para el sistema. "
                f"Revisa las dependencias mostradas en la página anterior."
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
                f"❌ No se puede eliminar los permisos '{self.object.group.name} - {self.object.module.name}' porque están siendo utilizados por:\n\n"
                f"📋 {'; '.join(error_details)}\n\n"
                f"💡 Para eliminar estos permisos, primero debes:\n"
                f"   • Quitar los usuarios del grupo\n"
                f"   • O cambiar los usuarios a otros grupos\n"
                f"   • Luego podrás eliminar los permisos sin problemas"
            )
            
            messages.error(request, error_message)
            return HttpResponseRedirect(self.success_url)
    
    def form_valid(self, form):
        # Guardar info antes de eliminar
        group_name = self.object.group.name
        module_name = self.object.module.name
        
        try:
            # Llamar al delete del padre
            response = super().form_valid(form)
            
            # Agregar mensaje de éxito
            messages.success(self.request, f"✅ Permisos '{group_name} - {module_name}' eliminados exitosamente.")
            
            return response
            
        except models.ProtectedError:
            # Esto no debería pasar porque ya verificamos en post(), pero por seguridad
            messages.error(
                self.request, 
                f"❌ No se pudieron eliminar los permisos '{group_name} - {module_name}' debido a dependencias del sistema."
            )
            return HttpResponseRedirect(self.success_url)