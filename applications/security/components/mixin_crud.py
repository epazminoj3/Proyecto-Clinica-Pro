from django.db.models import Q

#
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.utils.decorators import method_decorator

from applications.security.components.group_permission import GroupPermission
from applications.security.components.group_session import UserGroupSession
from applications.security.components.menu_module import MenuModule

# configuracion de contexto generico y permisos de botones
class ListViewMixin(object):
    query = None
    paginate_by = 5
  
    
    def dispatch(self, request, *args, **kwargs):
        self.query = Q()
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'{self.model._meta.verbose_name_plural}'
        context['title1'] = f'Consulta de {self.model._meta.verbose_name_plural}'
        # añade los permisos del grupo activo(add_pais, view_ciudad)
        # print("estoy en el mixing..")
        # print(self.request.session.get('group_id'))
        MenuModule(self.request).fill(context)
        userGroupSession=UserGroupSession(self.request)
        group = userGroupSession.get_group_session()
        context['permissions'] = GroupPermission.get_permission_dict_of_group(self.request.user,group)
        # crear la data y la session con los menus y modulos del usuario 
        return context

   

class CreateViewMixin(object):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'{self.model._meta.verbose_name}'
        context['title1'] = f'Ingresar {self.model._meta.verbose_name_plural}'
        MenuModule(self.request).fill(context)
        userGroupSession=UserGroupSession(self.request)
        group = userGroupSession.get_group_session()
        context['permissions'] = GroupPermission.get_permission_dict_of_group(self.request.user,group)
        return context


class UpdateViewMixin(object):
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'{self.model._meta.verbose_name_plural}'
        context['title1'] = f'Ingresar {self.model._meta.verbose_name_plural}'
        MenuModule(self.request).fill(context)
        userGroupSession=UserGroupSession(self.request)
        group = userGroupSession.get_group_session()
        context['permissions'] = GroupPermission.get_permission_dict_of_group(self.request.user,group)
        return context

     
class DeleteViewMixin(object):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        print("entro al deleteMixin")
        context['title'] = f'{self.model._meta.verbose_name_plural}'
        MenuModule(self.request).fill(context)
        userGroupSession=UserGroupSession(self.request)
        group = userGroupSession.get_group_session()
        context['permissions'] = GroupPermission.get_permission_dict_of_group(self.request.user,group)
        return context

      
         
# Permisos de urls o modulos
class PermissionMixin(object):
    permission_required = ''

    @method_decorator(login_required)
    def get(self, request, *args, **kwargs):
        try:
            user = request.user
            user_session=UserGroupSession(request)
            user_session.set_group_session()

            if 'group_id' not in request.session:
                return redirect('home')

            if user.is_superuser:
                return super().get(request, *args, **kwargs)

           
            group = user_session.get_group_session()
            permissions = self._get_permissions_to_validate() 
            print("permissions", permissions)
            if not permissions.__len__():
                print("entro permisos vacios")
                return super().get(request, *args, **kwargs)

            if not group.module_permissions.filter(
                    permissions__codename__in=permissions
            ).exists():
                print("no tengo permiso")
                messages.error(request, 'No tiene permiso para ingresar a este módulo')
                return redirect('home')

            return super().get(request, *args, **kwargs)

        except Exception as ex:
            messages.error(
                request,
                'A ocurrido un error al ingresar al modulo, error para el admin es : {}'.format(ex))

        if request.user.is_authenticated:
            return redirect('home')

        return redirect('security:auth_login')

    def _get_permissions_to_validate(self):

        if self.permission_required == '':
            return ()

        if isinstance(self.permission_required, str):
            return self.permission_required, 

        return tuple(self.permission_required) 
    