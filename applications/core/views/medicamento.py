from django.shortcuts import render, redirect
from django.urls import reverse_lazy, reverse
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.db.models import ProtectedError
from applications.core.models import Medicamento, TipoMedicamento, MarcaMedicamento
from applications.core.forms import MedicamentoForm, TipoMedicamentoForm, MarcaMedicamentoForm
from applications.security.components.mixin_crud import CreateViewMixin, DeleteViewMixin, ListViewMixin, PermissionMixin, UpdateViewMixin
from django.db.models import Q


# ==================== VISTAS DE MEDICAMENTO ====================
class MedicamentoListView(PermissionMixin, ListViewMixin, ListView):
    model = Medicamento
    template_name = 'core/medicamento/list.html'
    context_object_name = 'medicamentos'
    permission_required = 'view_medicamento'

    def get_queryset(self):
        q1 = self.request.GET.get('q')
        if q1 is not None:
            self.query.add(Q(nombre__icontains=q1), Q.OR)
            self.query.add(Q(concentracion__icontains=q1), Q.OR)
            self.query.add(Q(descripcion__icontains=q1), Q.OR)

        return self.model.objects.select_related('marca_medicamento', 'tipo').filter(self.query).order_by('nombre')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['create_url'] = reverse_lazy('core:medicamento_create')
        return context


class MedicamentoCreateView(PermissionMixin, CreateViewMixin, CreateView):
    model = Medicamento
    form_class = MedicamentoForm
    template_name = 'core/medicamento/form.html'
    success_url = reverse_lazy('core:medicamento_list')
    permission_required = 'add_medicamento'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['grabar'] = 'Guardar Medicamento'
        context['back_url'] = self.success_url
        return context

    def get_initial(self):
        """Pre-llenar formulario con parámetros GET del chatbot"""
        initial = super().get_initial()
        
        # Campos para medicamentos
        campos_medicamento = ['nombre', 'tipo', 'marca', 'dosis', 'precio', 'stock', 'descripcion']
        
        for field_name in campos_medicamento:
            value = self.request.GET.get(field_name)
            if value:
                initial[field_name] = value
        
        return initial

    def form_valid(self, form):
        form.instance.activo = True
        return super().form_valid(form)


class MedicamentoUpdateView(PermissionMixin, UpdateViewMixin, UpdateView):
    model = Medicamento
    form_class = MedicamentoForm
    template_name = 'core/medicamento/form.html'
    success_url = reverse_lazy('core:medicamento_list')
    permission_required = 'change_medicamento'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['grabar'] = 'Actualizar Medicamento'
        context['back_url'] = self.success_url
        return context


class MedicamentoDeleteView(PermissionMixin, DeleteViewMixin, DeleteView):
    model = Medicamento
    template_name = 'core/delete.html'
    success_url = reverse_lazy('core:medicamento_list')
    permission_required = 'delete_medicamento'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Eliminar Medicamento'
        context['back_url'] = self.success_url
        
        # Detectar dependencias
        prescripciones = self.object.prescripciones.all()
        
        if prescripciones.exists():
            # Hay prescripciones que bloquean la eliminación
            context['warning'] = True
            context['warning_title'] = 'No se puede eliminar este medicamento'
            context['warning_message'] = f'El medicamento "{self.object.nombre}" no puede ser eliminado porque está siendo utilizado en {prescripciones.count()} prescripción(es) médica(s).'
            
            # Mostrar detalles de las prescripciones
            context['dependencies'] = []
            for prescripcion in prescripciones[:5]:  # Mostrar máximo 5
                context['dependencies'].append({
                    'icon': 'fas fa-prescription-bottle-alt',
                    'text': f'Prescripción para {prescripcion.atencion.paciente.nombre_completo} ({prescripcion.atencion.fecha_atencion.strftime("%d/%m/%Y")})',
                    'subtext': f'Cantidad: {prescripcion.cantidad} - {prescripcion.prescripcion}'
                })
            
            if prescripciones.count() > 5:
                context['dependencies'].append({
                    'icon': 'fas fa-ellipsis-h',
                    'text': f'Y {prescripciones.count() - 5} prescripción(es) más...',
                    'subtext': ''
                })
            
            # Sugerencias para el usuario
            context['suggestions'] = [
                'Marque el medicamento como "Inactivo" en lugar de eliminarlo',
                'Revise si las prescripciones pueden ser actualizadas con medicamentos alternativos',
                'Consulte con el equipo médico antes de realizar cambios en medicamentos prescritos'
            ]
            
            context['show_delete_button'] = False
        else:
            # No hay dependencias, se puede eliminar
            context['question'] = f'¿Está seguro de eliminar el medicamento "{self.object.nombre}"?'
            context['warning_message'] = 'Esta acción no se puede deshacer.'
            context['show_delete_button'] = True
        
        return context
    
    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        
        # Verificar dependencias antes de eliminar
        prescripciones = self.object.prescripciones.all()
        
        if prescripciones.exists():
            messages.error(
                request,
                f'No se puede eliminar el medicamento "{self.object.nombre}" porque está siendo utilizado en {prescripciones.count()} prescripción(es) médica(s).'
            )
            return HttpResponseRedirect(self.success_url)
        
        try:
            messages.success(request, f'Medicamento "{self.object.nombre}" eliminado correctamente.')
            return super().post(request, *args, **kwargs)
        except Exception as e:
            messages.error(request, f'Error al eliminar el medicamento: {str(e)}')
            return HttpResponseRedirect(self.success_url)


# ==================== VISTAS DE TIPO MEDICAMENTO ====================
class TipoMedicamentoListView(PermissionMixin, ListViewMixin, ListView):
    model = TipoMedicamento
    template_name = 'core/tipo_medicamento/list.html'
    context_object_name = 'tipos'
    permission_required = 'view_tipomedicamento'

    def get_queryset(self):
        q1 = self.request.GET.get('q')
        if q1 is not None:
            self.query.add(Q(nombre__icontains=q1), Q.OR)
            self.query.add(Q(descripcion__icontains=q1), Q.OR)

        return self.model.objects.filter(self.query).order_by('nombre')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['create_url'] = reverse_lazy('core:tipo_medicamento_create')
        return context


class TipoMedicamentoCreateView(PermissionMixin, CreateViewMixin, CreateView):
    model = TipoMedicamento
    form_class = TipoMedicamentoForm
    template_name = 'core/tipo_medicamento/form.html'
    success_url = reverse_lazy('core:tipo_medicamento_list')
    permission_required = 'add_tipomedicamento'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['grabar'] = 'Guardar Tipo de Medicamento'
        context['back_url'] = self.success_url
        return context

    def form_valid(self, form):
        form.instance.activo = True
        return super().form_valid(form)


class TipoMedicamentoUpdateView(PermissionMixin, UpdateViewMixin, UpdateView):
    model = TipoMedicamento
    form_class = TipoMedicamentoForm
    template_name = 'core/tipo_medicamento/form.html'
    success_url = reverse_lazy('core:tipo_medicamento_list')
    permission_required = 'change_tipomedicamento'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['grabar'] = 'Actualizar Tipo de Medicamento'
        context['back_url'] = self.success_url
        return context


class TipoMedicamentoDeleteView(PermissionMixin, DeleteViewMixin, DeleteView):
    model = TipoMedicamento
    template_name = 'core/delete.html'
    success_url = reverse_lazy('core:tipo_medicamento_list')
    permission_required = 'delete_tipomedicamento'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Eliminar Tipo de Medicamento'
        context['cancel_url'] = self.success_url
        
        # Verificar dependencias antes de permitir eliminación
        tipo_medicamento = self.get_object()
        
        # Contar medicamentos que usan este tipo
        medicamentos_count = tipo_medicamento.medicamentos_por_tipo.count()
        
        if medicamentos_count > 0:
            context['error'] = True
            context['error_title'] = 'No se puede eliminar el tipo de medicamento'
            context['error_message'] = f'No se puede eliminar "{tipo_medicamento.nombre}" porque está siendo utilizado por {medicamentos_count} medicamento{"s" if medicamentos_count != 1 else ""}.'
            context['error_details'] = [
                f'Medicamentos que usan este tipo: {medicamentos_count}',
                'Para eliminar este tipo de medicamento, primero debe:',
                '1. Cambiar el tipo de los medicamentos que lo usan',
                '2. O eliminar los medicamentos que lo referencian'
            ]
            context['suggestions'] = [
                {
                    'text': 'Ver medicamentos que usan este tipo',
                    'url': reverse('core:medicamento_list') + f'?tipo={tipo_medicamento.id}'
                },
                {
                    'text': 'Gestionar medicamentos',
                    'url': reverse('core:medicamento_list')
                }
            ]
        else:
            # Si no hay dependencias, permitir eliminación
            context['question'] = f'¿Está seguro de eliminar el tipo de medicamento "{tipo_medicamento.nombre}"?'
            context['warning_message'] = 'Esta acción no se puede deshacer.'
            context['object_info'] = [
                f'Tipo: {tipo_medicamento.nombre}',
                f'Descripción: {tipo_medicamento.descripcion or "Sin descripción"}',
                f'Estado: {"Activo" if tipo_medicamento.activo else "Inactivo"}'
            ]
        
        return context

    def delete(self, request, *args, **kwargs):
        try:
            tipo_medicamento = self.get_object()
            
            # Verificar nuevamente las dependencias antes de eliminar
            medicamentos_count = tipo_medicamento.medicamentos_por_tipo.count()
            
            if medicamentos_count > 0:
                messages.error(
                    request, 
                    f'No se puede eliminar el tipo de medicamento "{tipo_medicamento.nombre}" porque está siendo utilizado por {medicamentos_count} medicamento{"s" if medicamentos_count != 1 else ""}.'
                )
                return HttpResponseRedirect(self.get_success_url())
            
            # Si no hay dependencias, proceder con la eliminación
            nombre_tipo = tipo_medicamento.nombre
            response = super().delete(request, *args, **kwargs)
            
            messages.success(
                request, 
                f'El tipo de medicamento "{nombre_tipo}" ha sido eliminado exitosamente.'
            )
            return response
            
        except ProtectedError as e:
            # Manejar error de protección de Django
            messages.error(
                request, 
                f'No se puede eliminar el tipo de medicamento porque está siendo utilizado por otros registros del sistema.'
            )
            return HttpResponseRedirect(self.get_success_url())
        except Exception as e:
            # Manejar otros errores
            messages.error(
                request, 
                f'Error inesperado al eliminar el tipo de medicamento: {str(e)}'
            )
            return HttpResponseRedirect(self.get_success_url())


# ==================== VISTAS DE MARCA MEDICAMENTO ====================
class MarcaMedicamentoListView(PermissionMixin, ListViewMixin, ListView):
    model = MarcaMedicamento
    template_name = 'core/marca_medicamento/list.html'
    context_object_name = 'marcas'
    permission_required = 'view_marcamedicamento'

    def get_queryset(self):
        q1 = self.request.GET.get('q')
        if q1 is not None:
            self.query.add(Q(nombre__icontains=q1), Q.OR)
            self.query.add(Q(descripcion__icontains=q1), Q.OR)

        return self.model.objects.filter(self.query).order_by('nombre')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['create_url'] = reverse_lazy('core:marca_medicamento_create')
        return context


class MarcaMedicamentoCreateView(PermissionMixin, CreateViewMixin, CreateView):
    model = MarcaMedicamento
    form_class = MarcaMedicamentoForm
    template_name = 'core/marca_medicamento/form.html'
    success_url = reverse_lazy('core:marca_medicamento_list')
    permission_required = 'add_marcamedicamento'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['grabar'] = 'Guardar Marca de Medicamento'
        context['back_url'] = self.success_url
        return context

    def form_valid(self, form):
        form.instance.activo = True
        return super().form_valid(form)


class MarcaMedicamentoUpdateView(PermissionMixin, UpdateViewMixin, UpdateView):
    model = MarcaMedicamento
    form_class = MarcaMedicamentoForm
    template_name = 'core/marca_medicamento/form.html'
    success_url = reverse_lazy('core:marca_medicamento_list')
    permission_required = 'change_marcamedicamento'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['grabar'] = 'Actualizar Marca de Medicamento'
        context['back_url'] = self.success_url
        return context


class MarcaMedicamentoDeleteView(PermissionMixin, DeleteViewMixin, DeleteView):
    model = MarcaMedicamento
    template_name = 'core/delete.html'
    success_url = reverse_lazy('core:marca_medicamento_list')
    permission_required = 'delete_marcamedicamento'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Eliminar Marca de Medicamento'
        context['cancel_url'] = self.success_url
        context['entity_name'] = 'marca de medicamento'
        
        # Verificar dependencias antes de mostrar el formulario
        dependencias = []
        
        # Verificar si hay medicamentos usando esta marca
        medicamentos_count = self.object.medicamentos_por_marca.count()
        if medicamentos_count > 0:
            dependencias.append(f"{medicamentos_count} medicamento{'s' if medicamentos_count != 1 else ''}")
        
        if dependencias:
            context['has_dependencies'] = True
            context['dependencies'] = dependencias
            context['dependencies_message'] = f"No se puede eliminar la marca '{self.object.nombre}' porque está siendo utilizada por:"
            context['next_steps'] = [
                "Reasignar los medicamentos a otra marca",
                "Contactar al administrador del sistema para más opciones"
            ]
        else:
            context['has_dependencies'] = False
            context['question'] = f'¿Está seguro de eliminar la marca "{self.object.nombre}"?'
            context['warning'] = 'Esta acción no se puede deshacer.'
        
        return context

    def delete(self, request, *args, **kwargs):
        """Override delete to handle protected foreign key relationships"""
        try:
            # Verificar dependencias antes de eliminar
            medicamentos_count = self.object.medicamentos_por_marca.count()
            if medicamentos_count > 0:
                messages.error(
                    request,
                    f"No se puede eliminar la marca '{self.object.nombre}' porque está siendo utilizada por {medicamentos_count} medicamento{'s' if medicamentos_count != 1 else ''}."
                )
                return redirect(self.success_url)
            
            # Si no hay dependencias, proceder con la eliminación
            marca_nombre = self.object.nombre
            response = super().delete(request, *args, **kwargs)
            messages.success(request, f"La marca '{marca_nombre}' ha sido eliminada exitosamente.")
            return response
            
        except ProtectedError as e:
            # Si Django detecta relaciones protegidas que no capturamos
            messages.error(
                request,
                f"No se puede eliminar la marca '{self.object.nombre}' porque está siendo utilizada por otros elementos del sistema."
            )
            return redirect(self.success_url)
        except Exception as e:
            # Capturar cualquier otro error
            messages.error(
                request,
                f"Error al intentar eliminar la marca: {str(e)}"
            )
            return redirect(self.success_url)