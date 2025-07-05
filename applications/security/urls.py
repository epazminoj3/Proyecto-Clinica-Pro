from django.urls import path

from applications.security.views.auth import signin, signout
from applications.security.views.user import signup
from applications.security.views.menu import MenuCreateView, MenuDeleteView, MenuListView, MenuUpdateView
from applications.security.views.module import ModuleCreateView, ModuleDeleteView, ModuleListView, ModuleUpdateView
from applications.security.views.group import GroupCreateView, GroupDeleteView, GroupListView, GroupUpdateView
from applications.security.views.user import UserCreateView, UserDeleteView, UserListView, UserUpdateView, profile_view, edit_profile_view
from applications.security.views.group_permission import GroupModulePermissionCreateView, GroupModulePermissionDeleteView, GroupModulePermissionListView, GroupModulePermissionUpdateView
from applications.security.views.group_permission_dynamic import (
    group_permission_dynamic_main, group_modules_ajax, module_permissions_ajax, 
    save_module_permissions_ajax, group_summary_ajax
)
from applications.security.views.dashboard_stats import dashboard_stats


app_name = 'security'  # define un espacio de nombre para la aplicación

urlpatterns = [
    # rutas de módulos
    path('module_list/', ModuleListView.as_view(), name="module_list"),
    path('module_create/', ModuleCreateView.as_view(), name="module_create"),
    path('module_update/<int:pk>/', ModuleUpdateView.as_view(), name='module_update'),
    path('module_delete/<int:pk>/', ModuleDeleteView.as_view(), name='module_delete'),

    # rutas de menús
    path('menu_list/', MenuListView.as_view(), name="menu_list"),
    path('menu_create/', MenuCreateView.as_view(), name="menu_create"),
    path('menu_update/<int:pk>/', MenuUpdateView.as_view(), name='menu_update'),
    path('menu_delete/<int:pk>/', MenuDeleteView.as_view(), name='menu_delete'),

    # rutas de grupos
    path('group_list/', GroupListView.as_view(), name="group_list"),
    path('group_create/', GroupCreateView.as_view(), name="group_create"),
    path('group_update/<int:pk>/', GroupUpdateView.as_view(), name='group_update'),
    path('group_delete/<int:pk>/', GroupDeleteView.as_view(), name='group_delete'),

    # rutas de autenticación
    path('signin/', signin, name='signin'),
    path('signout/', signout, name='signout'),
    path('signup/', signup, name='signup'),

    # rutas de usuario
    path('usuarios_list/', UserListView.as_view(), name="user_list"),
    path('usuarios_create/', UserCreateView.as_view(), name="user_create"),
    path('usuarios_update/<int:pk>/', UserUpdateView.as_view(), name='user_update'),
    path('usuarios_delete/<int:pk>/', UserDeleteView.as_view(), name='user_delete'),
    
    
    # rutas de permisos
    path('group_permission_list/', GroupModulePermissionListView.as_view(), name="group_permission_list"),
    path('group_permission_create/', GroupModulePermissionCreateView.as_view(), name="group_permission_create"),
    path('group_permission_update/<int:pk>/', GroupModulePermissionUpdateView.as_view(), name='group_permission_update'),
    path('group_permission_delete/<int:pk>/', GroupModulePermissionDeleteView.as_view(), name='group_permission_delete'),

    # rutas de gestión dinámica de permisos
    path('group-permissions/dynamic/', group_permission_dynamic_main, name="group_permission_dynamic"),
    path('group-permissions/ajax/group/<int:group_id>/modules/', group_modules_ajax, name="group_modules_ajax"),
    path('group-permissions/ajax/group/<int:group_id>/module/<int:module_id>/permissions/', module_permissions_ajax, name="module_permissions_ajax"),
    path('group-permissions/ajax/group/<int:group_id>/module/<int:module_id>/save/', save_module_permissions_ajax, name="save_module_permissions_ajax"),
    path('group-permissions/ajax/group/<int:group_id>/summary/', group_summary_ajax, name="group_summary_ajax"),

    path('profile/', profile_view, name='profile'),
    path('profile/edit/', edit_profile_view, name='edit_profile'),
    
    # API para estadísticas del dashboard
    path('api/dashboard-stats/', dashboard_stats, name='dashboard_stats'),
]