from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.contrib import messages
from django.db.models import Q, ProtectedError
from applications.doctor.models import DetalleAtencion
from applications.doctor.forms import DetalleAtencionForm
from applications.security.components.mixin_crud import (
    PermissionMixin, ListViewMixin, CreateViewMixin, UpdateViewMixin, DeleteViewMixin
)


# ==================== VISTAS DE DETALLE ATENCION ====================
class DetalleAtencionListView(PermissionMixin, ListViewMixin, ListView):
    model = DetalleAtencion
    template_name = 'doctor/detalle_atencion/list.html'
    context_object_name = 'detalles'
    permission_required = 'doctor.view_detalleatencion'

    def get_queryset(self):
        q1 = self.request.GET.get('q')
        
        if q1 is not None:
            self.query.add(Q(medicamento__nombre__icontains=q1), Q.OR)
            self.query.add(Q(atencion__paciente__nombres__icontains=q1), Q.OR)
            self.query.add(Q(atencion__paciente__apellidos__icontains=q1), Q.OR)
            self.query.add(Q(prescripcion__icontains=q1), Q.OR)
        
        return (self.model.objects.filter(self.query)
                .select_related('atencion__paciente', 'medicamento')
                .order_by('-atencion__fecha_atencion'))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['create_url'] = reverse_lazy('doctor:detalle_atencion_create')
        return context


class DetalleAtencionCreateView(PermissionMixin, CreateViewMixin, CreateView):
    model = DetalleAtencion
    form_class = DetalleAtencionForm
    template_name = 'doctor/detalle_atencion/form.html'
    success_url = reverse_lazy('doctor:detalle_atencion_list')
    permission_required = 'doctor.add_detalleatencion'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['grabar'] = 'Grabar Detalle de Atención'
        context['back_url'] = self.success_url
        return context


class DetalleAtencionUpdateView(PermissionMixin, UpdateViewMixin, UpdateView):
    model = DetalleAtencion
    form_class = DetalleAtencionForm
    template_name = 'doctor/detalle_atencion/form.html'
    success_url = reverse_lazy('doctor:detalle_atencion_list')
    permission_required = 'doctor.change_detalleatencion'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['grabar'] = 'Actualizar Detalle de Atención'
        context['back_url'] = self.success_url
        return context


class DetalleAtencionDeleteView(PermissionMixin, DeleteViewMixin, DeleteView):
    model = DetalleAtencion
    template_name = 'core/delete.html'
    success_url = reverse_lazy('doctor:detalle_atencion_list')
    permission_required = 'doctor.delete_detalleatencion'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Eliminar Detalle de Atención'
        context['cancel_url'] = self.success_url
        context['entity_name'] = 'detalle de atención'
        
        # Los detalles de atención normalmente no tienen dependencias bloqueantes
        # Son registros de prescripciones específicas dentro de una atención médica
        dependencias = []
        
        # No hay dependencias bloqueantes típicas para detalles de atención
        # (son registros de prescripción que pueden eliminarse sin afectar otros datos)
        
        if dependencias:
            context['has_dependencies'] = True
            context['dependencies'] = dependencias
            context['dependencies_message'] = f"No se puede eliminar este detalle de atención porque:"
            context['next_steps'] = [
                "Contactar al administrador del sistema para más opciones"
            ]
        else:
            context['has_dependencies'] = False
            detalle = self.object
            fecha_atencion = detalle.atencion.fecha_atencion.strftime('%d/%m/%Y')
            context['question'] = f'¿Está seguro de eliminar la prescripción de "{detalle.medicamento.nombre}" de la atención del paciente {detalle.atencion.paciente.nombre_completo} del {fecha_atencion}?'
            context['warning'] = 'Esta acción eliminará permanentemente la prescripción médica del registro de atención.'
            context['details'] = [
                f"Paciente: {detalle.atencion.paciente.nombre_completo}",
                f"Medicamento: {detalle.medicamento.nombre}",
                f"Cantidad prescrita: {detalle.cantidad}",
                f"Fecha de atención: {fecha_atencion}",
                f"Prescripción: {detalle.prescripcion[:100]}{'...' if len(detalle.prescripcion) > 100 else ''}"
            ]
        
        return context

    def delete(self, request, *args, **kwargs):
        """Override delete to handle any potential errors and provide user feedback"""
        try:
            detalle = self.object
            medicamento_nombre = detalle.medicamento.nombre
            paciente_nombre = detalle.atencion.paciente.nombre_completo
            
            # Proceder con la eliminación
            response = super().delete(request, *args, **kwargs)
            messages.success(
                request,
                f"La prescripción de '{medicamento_nombre}' para {paciente_nombre} ha sido eliminada exitosamente."
            )
            return response
            
        except ProtectedError as e:
            # Si Django detecta relaciones protegidas
            messages.error(
                request,
                f"No se puede eliminar este detalle de atención porque está siendo utilizado por otros elementos del sistema."
            )
            return redirect(self.success_url)
        except Exception as e:
            # Capturar cualquier otro error
            messages.error(
                request,
                f"Error al intentar eliminar el detalle de atención: {str(e)}"
            )
            return redirect(self.success_url)
