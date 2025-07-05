import re
from django import forms
from django.forms import ModelForm
from django.contrib.auth.models import Group
from applications.security.models import GroupModulePermission, Module

class GroupModulePermissionForm(ModelForm):
    class Meta:
        model = GroupModulePermission
        fields = ['group', 'module', 'permissions']
        widgets = {
            "group": forms.Select(attrs={
                "id": "id_group",
                "class": "shadow-sm bg-gray-50 border border-gray-300 text-gray-900 rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full p-2.5 pr-12 dark:bg-principal dark:border-gray-600 dark:placeholder-gray-400 dark:text-gray-400 dark:focus:ring-blue-500 dark:focus:border-blue-500 dark:shadow-sm-light",
            }),
            "module": forms.Select(attrs={
                "id": "id_module",
                "class": "shadow-sm bg-gray-50 border border-gray-300 text-gray-900 rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full p-2.5 pr-12 dark:bg-principal dark:border-gray-600 dark:placeholder-gray-400 dark:text-gray-400 dark:focus:ring-blue-500 dark:focus:border-blue-500 dark:shadow-sm-light",
            }),
            "permissions": forms.CheckboxSelectMultiple(attrs={
                "class": "rounded border-gray-300 text-blue-600 shadow-sm focus:border-blue-300 focus:ring focus:ring-blue-200 focus:ring-opacity-50 dark:border-gray-600 dark:bg-gray-700",
            })
        }
        labels = {
            "group": "Grupo",
            "module": "Módulo", 
            "permissions": "Permisos",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Configurar queryset para módulos activos
        self.fields['module'].queryset = Module.objects.filter(is_active=True).select_related('menu').order_by('menu__name', 'name')
        
        # Configurar empty labels
        if not self.fields['module'].queryset.exists():
            self.fields['module'].empty_label = "⚠️ No hay módulos disponibles"
        else:
            self.fields['module'].empty_label = "Seleccione un módulo"
            
        if not Group.objects.exists():
            self.fields['group'].empty_label = "⚠️ No hay grupos disponibles"
        else:
            self.fields['group'].empty_label = "Seleccione un grupo"

    def clean(self):
        cleaned_data = super().clean()
        group = cleaned_data.get('group')
        module = cleaned_data.get('module')
        
        # Verificar que se seleccionaron ambos campos
        if not group:
            raise forms.ValidationError("Debe seleccionar un grupo.")
            
        if not module:
            raise forms.ValidationError("Debe seleccionar un módulo.")
        
        # Verificar combinación única (excluyendo la instancia actual en edición)
        existing = GroupModulePermission.objects.filter(group=group, module=module)
        if self.instance.pk:
            existing = existing.exclude(pk=self.instance.pk)
            
        if existing.exists():
            raise forms.ValidationError(
                f"Ya existe una configuración de permisos para el grupo '{group.name}' y el módulo '{module.name}'."
            )
        
        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # Verificar que los campos requeridos estén presentes
        if not instance.group:
            raise ValueError("El grupo es requerido")
        if not instance.module:
            raise ValueError("El módulo es requerido")
            
        if commit:
            instance.save()
            self.save_m2m()  # Guardar relaciones many-to-many (permisos)
            
        return instance