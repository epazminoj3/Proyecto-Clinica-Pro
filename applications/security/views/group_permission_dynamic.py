# security/views/group_permission_dynamic.py
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.models import Group, Permission
from django.db import transaction
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import permission_required
from applications.security.models import Module, GroupModulePermission
from django.contrib import messages
import json

class GroupPermissionDynamicView:
    """
    Vista principal para la gestión dinámica de permisos por grupo.
    Permite seleccionar un grupo y asignar permisos módulo por módulo.
    """
    
    @permission_required('security.view_groupmodulepermission', raise_exception=True)
    def main_view(request):
        """Vista principal que renderiza el formulario dinámico"""
        groups = Group.objects.all().order_by('name')
        
        context = {
            'title': 'Gestión Dinámica de Permisos por Grupo',
            'groups': groups,
            'create_url': '#',  # Se maneja dinámicamente
            'back_url': '/security/group-permissions/',
        }
        
        return render(request, 'security/group_permissions/form.html', context)
    
    @require_http_methods(["GET"])
    def get_group_modules(request, group_id):
        """
        AJAX: Obtiene solo los módulos asignados a un grupo específico.
        Incluye información sobre qué módulos ya tienen permisos configurados.
        """
        try:
            group = get_object_or_404(Group, id=group_id)
            
            # Obtener solo los módulos que están asignados a este grupo
            group_module_permissions = GroupModulePermission.objects.filter(
                group=group
            ).select_related('module', 'module__menu').prefetch_related('permissions')
            
            modules_data = []
            for gmp in group_module_permissions:
                module = gmp.module
                permissions_count = gmp.permissions.count()
                
                modules_data.append({
                    'id': module.id,
                    'name': module.name,
                    'url': module.url,
                    'menu_name': module.menu.name,
                    'description': module.description or '',
                    'icon': module.icon,
                    'has_permissions': permissions_count > 0,
                    'permissions_count': permissions_count,
                })
            
            return JsonResponse({
                'success': True,
                'group_name': group.name,
                'modules': modules_data
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)
    
    @require_http_methods(["GET"])
    def get_module_permissions(request, group_id, module_id):
        """
        AJAX: Obtiene los permisos disponibles para un módulo específico
        y los permisos actualmente asignados al grupo para ese módulo.
        """
        try:
            group = get_object_or_404(Group, id=group_id)
            module = get_object_or_404(Module, id=module_id)
            
            # Obtener todos los permisos asociados al módulo
            module_permissions = module.permissions.all().order_by('content_type__model', 'codename')
            
            # Obtener permisos actualmente asignados al grupo para este módulo
            assigned_permissions = []
            try:
                group_module_perm = GroupModulePermission.objects.get(group=group, module=module)
                assigned_permissions = list(group_module_perm.permissions.values_list('id', flat=True))
            except GroupModulePermission.DoesNotExist:
                assigned_permissions = []
            
            permissions_data = []
            for permission in module_permissions:
                permissions_data.append({
                    'id': permission.id,
                    'name': permission.name,
                    'codename': permission.codename,
                    'content_type': permission.content_type.model,
                    'is_assigned': permission.id in assigned_permissions,
                })
            
            return JsonResponse({
                'success': True,
                'group_name': group.name,
                'module_name': module.name,
                'module_description': module.description or '',
                'permissions': permissions_data,
                'has_existing_assignment': len(assigned_permissions) > 0
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)
    
    @csrf_exempt
    @require_http_methods(["POST"])
    @permission_required('security.change_groupmodulepermission', raise_exception=True)
    def save_module_permissions(request, group_id, module_id):
        """
        AJAX: Guarda los permisos seleccionados para un grupo-módulo específico.
        """
        try:
            with transaction.atomic():
                group = get_object_or_404(Group, id=group_id)
                module = get_object_or_404(Module, id=module_id)
                
                # Obtener los IDs de permisos del request
                data = json.loads(request.body)
                permission_ids = data.get('permission_ids', [])
                
                # Obtener o crear el GroupModulePermission
                group_module_perm, created = GroupModulePermission.objects.get_or_create(
                    group=group,
                    module=module
                )
                
                # Limpiar permisos actuales y asignar los nuevos
                group_module_perm.permissions.clear()
                
                if permission_ids:
                    # Validar que los permisos pertenezcan al módulo
                    valid_permissions = module.permissions.filter(id__in=permission_ids)
                    group_module_perm.permissions.set(valid_permissions)
                
                # NO eliminar la relación GroupModulePermission, solo limpiar permisos
                # Esto mantiene el módulo visible en el grupo incluso sin permisos
                
                action = 'created' if created else 'updated'
                permission_count = len(permission_ids) if permission_ids else 0
                
                return JsonResponse({
                    'success': True,
                    'message': f'Permisos {"asignados" if permission_count > 0 else "eliminados"} para {group.name} - {module.name}. Total: {permission_count} permisos',
                    'action': action,
                    'permission_count': permission_count
                })
                
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)
    
    @require_http_methods(["GET"])
    def get_group_summary(request, group_id):
        """
        AJAX: Obtiene un resumen de todos los módulos y permisos asignados a un grupo.
        """
        try:
            group = get_object_or_404(Group, id=group_id)
            
            # Obtener todas las asignaciones de módulos para este grupo
            group_modules = GroupModulePermission.objects.filter(
                group=group
            ).select_related('module', 'module__menu').prefetch_related('permissions')
            
            summary_data = []
            total_permissions = 0
            
            for gmp in group_modules:
                permissions_list = []
                for perm in gmp.permissions.all():
                    permissions_list.append({
                        'id': perm.id,
                        'name': perm.name,
                        'codename': perm.codename
                    })
                
                total_permissions += len(permissions_list)
                
                summary_data.append({
                    'module_id': gmp.module.id,
                    'module_name': gmp.module.name,
                    'menu_name': gmp.module.menu.name,
                    'permissions_count': len(permissions_list),
                    'permissions': permissions_list
                })
            
            return JsonResponse({
                'success': True,
                'group_name': group.name,
                'modules_count': len(summary_data),
                'total_permissions': total_permissions,
                'modules': summary_data
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)


# Funciones de vista standalone para uso en URLs
@permission_required('security.view_groupmodulepermission', raise_exception=True)
def group_permission_dynamic_main(request):
    return GroupPermissionDynamicView.main_view(request)

def group_modules_ajax(request, group_id):
    return GroupPermissionDynamicView.get_group_modules(request, group_id)

def module_permissions_ajax(request, group_id, module_id):
    return GroupPermissionDynamicView.get_module_permissions(request, group_id, module_id)

def save_module_permissions_ajax(request, group_id, module_id):
    return GroupPermissionDynamicView.save_module_permissions(request, group_id, module_id)

def group_summary_ajax(request, group_id):
    return GroupPermissionDynamicView.get_group_summary(request, group_id)
