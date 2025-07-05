from django.contrib import messages
from django.urls import reverse_lazy
from django.db import models
from django.http import HttpResponseRedirect
from applications.security.components.mixin_crud import CreateViewMixin, DeleteViewMixin, ListViewMixin, PermissionMixin, UpdateViewMixin
from applications.security.forms.user import UserForm, UserCreateForm
from applications.security.forms.module import ModuleForm
from applications.security.models import Menu, Module, User
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.db.models import Q
from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator


class UserListView(PermissionMixin, ListViewMixin, ListView):
    template_name = 'security/users/list.html'
    model = User
    context_object_name = 'users'
    permission_required = 'view_user'

    def get_queryset(self):
        q1 = self.request.GET.get('q')
        if q1 is not None:
            self.query.add(Q(username__icontains=q1), Q.OR)

        return self.model.objects.filter(self.query).order_by('id')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['create_url'] = reverse_lazy('security:user_create')
        print(context['permissions'])
        return context


class UserCreateView(PermissionMixin, CreateViewMixin, CreateView):
    model = User
    template_name = 'security/users/form.html'
    form_class = UserCreateForm
    success_url = reverse_lazy('security:user_list')
    permission_required = 'add_user'

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        context['grabar'] = 'Grabar Usuario'
        context['back_url'] = self.success_url
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        user = self.object
        messages.success(self.request, f"Éxito al crear el usuario {user.username}.")
        return response
        return response


class UserUpdateView(PermissionMixin, UpdateViewMixin, UpdateView):
    model = User
    template_name = 'security/users/form.html'
    form_class = UserForm
    success_url = reverse_lazy('security:user_list')
    permission_required = 'change_user'

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        context['grabar'] = 'Actualizar Usuario'
        context['back_url'] = self.success_url
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        user = self.object
        messages.success(self.request, f"Éxito al actualizar el usuario {user.username}.")
        return response


class UserDeleteView(PermissionMixin, DeleteViewMixin, DeleteView):
    model = User
    template_name = 'core/delete.html'
    success_url = reverse_lazy('security:user_list')
    permission_required = 'delete_user'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['grabar'] = 'Eliminar Usuario'
        
        # Verificar si el usuario tiene dependencias
        user = self.object
        dependencies_info = self._get_user_dependencies(user)
        
        if dependencies_info['has_dependencies']:
            context['description'] = f"""
            <div class="mb-4">
                <h4 class="text-lg font-semibold text-red-600 mb-2">
                    <i class="fas fa-exclamation-triangle mr-2"></i>
                    No se puede eliminar el usuario: {user.username}
                </h4>
                <p class="text-gray-700 mb-3">
                    Este usuario está siendo utilizado por otros elementos del sistema y no puede ser eliminado.
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
                    <li>Elimina o reasigna los empleados asociados a este usuario</li>
                    <li>Elimina o reasigna los doctores asociados a este usuario</li>
                    <li>Elimina o reasigna las citas médicas creadas por este usuario</li>
                    <li>Luego podrás eliminar este usuario sin problemas</li>
                </ul>
            </div>
            """
            context['cannot_delete'] = True
        else:
            context['description'] = f"""
            <div class="mb-4">
                <h4 class="text-lg font-semibold text-gray-800 mb-2">
                    <i class="fas fa-trash mr-2"></i>
                    ¿Desea eliminar el usuario: {user.username}?
                </h4>
                <p class="text-gray-600">
                    Esta acción eliminará permanentemente el usuario y no se puede deshacer.
                </p>
            </div>
            
            <div class="bg-yellow-50 border-l-4 border-yellow-400 p-4">
                <p class="text-yellow-700">
                    <i class="fas fa-warning mr-1"></i>
                    <strong>Advertencia:</strong> Al eliminar este usuario, también se eliminarán todas sus sesiones y configuraciones.
                </p>
            </div>
            """
            context['cannot_delete'] = False
        
        context['back_url'] = self.success_url
        return context
    
    def _get_user_dependencies(self, user):
        """Obtiene información sobre las dependencias del usuario"""
        dependencies = []
        has_dependencies = False
        
        try:
            # Verificar Empleados
            from applications.core.models import Empleado
            empleados = Empleado.objects.filter(user=user)
            if empleados.exists():
                has_dependencies = True
                empleados_names = [emp.nombres for emp in empleados[:3]]
                empleados_text = ', '.join(empleados_names)
                if empleados.count() > 3:
                    empleados_text += f" y {empleados.count() - 3} más"
                dependencies.append(f"<strong>{empleados.count()} empleado(s)</strong>: <em>{empleados_text}</em>")
            
            # Verificar Doctores
            from applications.core.models import Doctor
            doctores = Doctor.objects.filter(user=user)
            if doctores.exists():
                has_dependencies = True
                doctores_names = [doc.nombres for doc in doctores[:3]]
                doctores_text = ', '.join(doctores_names)
                if doctores.count() > 3:
                    doctores_text += f" y {doctores.count() - 3} más"
                dependencies.append(f"<strong>{doctores.count()} doctor(es)</strong>: <em>{doctores_text}</em>")
            
            # Verificar Citas Médicas
            try:
                from applications.doctor.models import CitaMedica
                citas = CitaMedica.objects.filter(created_by=user)
                if citas.exists():
                    has_dependencies = True
                    dependencies.append(f"<strong>{citas.count()} cita(s) médica(s)</strong> creadas por este usuario")
            except ImportError:
                pass
            
            # Verificar Grupos
            if user.groups.exists():
                has_dependencies = True
                groups_names = [group.name for group in user.groups.all()[:3]]
                groups_text = ', '.join(groups_names)
                if user.groups.count() > 3:
                    groups_text += f" y {user.groups.count() - 3} más"
                dependencies.append(f"<strong>Pertenece a {user.groups.count()} grupo(s)</strong>: <em>{groups_text}</em>")
            
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
        dependencies_info = self._get_user_dependencies(self.object)
        if dependencies_info['has_dependencies']:
            messages.error(
                request,
                f"No se puede eliminar el usuario '{self.object.username}' porque está siendo utilizado por otros elementos del sistema. "
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
                f"❌ No se puede eliminar el usuario '{self.object.username}' porque está siendo utilizado por:\n\n"
                f"📋 {'; '.join(error_details)}\n\n"
                f"💡 Para eliminar este usuario, primero debes:\n"
                f"   • Eliminar o reasignar los empleados asociados\n"
                f"   • Eliminar o reasignar los doctores asociados\n"
                f"   • Eliminar o reasignar las citas médicas creadas\n"
                f"   • Quitar el usuario de todos los grupos\n"
                f"   • Luego podrás eliminar el usuario sin problemas"
            )
            
            messages.error(request, error_message)
            return HttpResponseRedirect(self.success_url)
    
    def form_valid(self, form):
        # Guardar info antes de eliminar
        user_name = self.object.username
        
        try:
            # Llamar al delete del padre
            response = super().form_valid(form)
            
            # Agregar mensaje de éxito
            messages.success(self.request, f"✅ Usuario '{user_name}' eliminado exitosamente.")
            
            return response
            
        except models.ProtectedError:
            # Esto no debería pasar porque ya verificamos en post(), pero por seguridad
            messages.error(
                self.request, 
                f"❌ No se pudo eliminar el usuario '{user_name}' debido a dependencias del sistema."
            )
            return HttpResponseRedirect(self.success_url)


def signup(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f"¡Registro exitoso! Bienvenido, {user.username}.")
            return redirect('home')
    else:
        form = UserCreationForm()
    return render(request, "security/auth/signup.html", {"form": form, "title1": "Registro", "title2": "Crea tu cuenta"})


@login_required
def profile_view(request):
    return render(request, 'security/profile.html', {'user': request.user})

@login_required
def edit_profile_view(request):
    if request.method == 'POST':
        form = UserForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Perfil actualizado correctamente.')
            return redirect('security:profile')
    else:
        form = UserForm(instance=request.user)
    return render(request, 'security/edit_profile.html', {'form': form})