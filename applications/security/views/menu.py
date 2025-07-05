
from django.contrib import messages
from django.urls import reverse_lazy
from django.db import models
from django.http import HttpResponseRedirect
from applications.security.components.mixin_crud import CreateViewMixin, DeleteViewMixin, ListViewMixin, PermissionMixin, UpdateViewMixin
from applications.security.forms.menu import MenuForm
from applications.security.forms.module import ModuleForm
from applications.security.models import Menu, Module
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.db.models import Q


class MenuListView(PermissionMixin, ListViewMixin, ListView):
    template_name = 'security/menus/list.html'
    model = Menu
    context_object_name = 'menus'
    permission_required = 'view_menu'

    def get_queryset(self):
        q1 = self.request.GET.get('q')
        if q1 is not None:
            self.query.add(Q(name__icontains=q1), Q.OR)
           
        return self.model.objects.filter(self.query).order_by('id')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['create_url'] = reverse_lazy('security:menu_create')
        print(context['permissions'])
        return context


class MenuCreateView(PermissionMixin, CreateViewMixin, CreateView):
    model = Menu
    template_name = 'security/menus/form.html'
    form_class = MenuForm
    success_url = reverse_lazy('security:menu_list')
    permission_required = 'add_menu'

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        context['grabar'] = 'Grabar Menu'
        context['back_url'] = self.success_url
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        menu = self.object
        messages.success(self.request, f"Éxito al crear el menu {menu.name}.")
        return response


class MenuUpdateView(PermissionMixin, UpdateViewMixin, UpdateView):
    model = Menu
    template_name = 'security/menus/form.html'
    form_class = MenuForm
    success_url = reverse_lazy('security:menu_list')
    permission_required = 'change_menu'

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        context['grabar'] = 'Actualizar Menu'
        context['back_url'] = self.success_url
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        menu = self.object
        messages.success(self.request, f"Éxito al actualizar el menu {menu.name}.")
        return response


class MenuDeleteView(PermissionMixin, DeleteViewMixin, DeleteView):
    model = Menu
    template_name = 'core/delete.html'
    success_url = reverse_lazy('security:menu_list')
    permission_required = 'delete_menu'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['grabar'] = 'Eliminar Menu'
        
        # Verificar si el menú tiene dependencias
        menu = self.object
        dependencies_info = self._get_menu_dependencies(menu)
        
        if dependencies_info['has_dependencies']:
            context['description'] = f"""
            <div class="mb-4">
                <h4 class="text-lg font-semibold text-red-600 mb-2">
                    <i class="fas fa-exclamation-triangle mr-2"></i>
                    No se puede eliminar el menú: {menu.name}
                </h4>
                <p class="text-gray-700 mb-3">
                    Este menú está siendo utilizado por otros elementos del sistema y no puede ser eliminado.
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
                    <li>Elimina o cambia el menú de los módulos asociados</li>
                    <li>Luego podrás eliminar este menú sin problemas</li>
                </ul>
            </div>
            """
            context['cannot_delete'] = True
        else:
            context['description'] = f"""
            <div class="mb-4">
                <h4 class="text-lg font-semibold text-gray-800 mb-2">
                    <i class="fas fa-trash mr-2"></i>
                    ¿Desea eliminar el menú: {menu.name}?
                </h4>
                <p class="text-gray-600">
                    Esta acción eliminará permanentemente el menú y no se puede deshacer.
                </p>
            </div>
            
            <div class="bg-yellow-50 border-l-4 border-yellow-400 p-4">
                <p class="text-yellow-700">
                    <i class="fas fa-warning mr-1"></i>
                    <strong>Advertencia:</strong> Al eliminar este menú, también se eliminarán todas sus configuraciones.
                </p>
            </div>
            """
            context['cannot_delete'] = False
        
        context['back_url'] = self.success_url
        return context
    
    def _get_menu_dependencies(self, menu):
        """Obtiene información sobre las dependencias del menú"""
        dependencies = []
        has_dependencies = False
        
        try:
            # Verificar Módulos que usan este menú
            modules = Module.objects.filter(menu=menu)
            if modules.exists():
                has_dependencies = True
                modules_names = [mod.name for mod in modules[:3]]
                modules_text = ', '.join(modules_names)
                if modules.count() > 3:
                    modules_text += f" y {modules.count() - 3} más"
                dependencies.append(f"<strong>{modules.count()} módulo(s)</strong>: <em>{modules_text}</em>")
            
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
        dependencies_info = self._get_menu_dependencies(self.object)
        if dependencies_info['has_dependencies']:
            messages.error(
                request,
                f"No se puede eliminar el menú '{self.object.name}' porque está siendo utilizado por otros elementos del sistema. "
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
                f"❌ No se puede eliminar el menú '{self.object.name}' porque está siendo utilizado por:\n\n"
                f"📋 {'; '.join(error_details)}\n\n"
                f"💡 Para eliminar este menú, primero debes:\n"
                f"   • Eliminar o cambiar el menú de los módulos asociados\n"
                f"   • Luego podrás eliminar el menú sin problemas"
            )
            
            messages.error(request, error_message)
            return HttpResponseRedirect(self.success_url)
    
    def form_valid(self, form):
        # Guardar info antes de eliminar
        menu_name = self.object.name
        
        try:
            # Llamar al delete del padre
            response = super().form_valid(form)
            
            # Agregar mensaje de éxito
            messages.success(self.request, f"✅ Menú '{menu_name}' eliminado exitosamente.")
            
            return response
            
        except models.ProtectedError:
            # Esto no debería pasar porque ya verificamos en post(), pero por seguridad
            messages.error(
                self.request, 
                f"❌ No se pudo eliminar el menú '{menu_name}' debido a dependencias del sistema."
            )
            return HttpResponseRedirect(self.success_url)