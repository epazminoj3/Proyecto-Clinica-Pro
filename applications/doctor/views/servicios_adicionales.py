from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.contrib import messages
from django.db.models import Q, ProtectedError
from applications.doctor.models import ServiciosAdicionales
from applications.doctor.forms import ServiciosAdicionalesForm
from applications.security.components.mixin_crud import (
    PermissionMixin, ListViewMixin, CreateViewMixin, UpdateViewMixin, DeleteViewMixin
)


# ==================== VISTAS DE SERVICIOS ADICIONALES ====================
class ServiciosAdicionalesListView(PermissionMixin, ListViewMixin, ListView):
    model = ServiciosAdicionales
    template_name = 'doctor/servicios_adicionales/list.html'
    context_object_name = 'servicios'
    permission_required = 'doctor.view_serviciosadicionales'

    def get_queryset(self):
        q1 = self.request.GET.get('q')
        
        if q1 is not None:
            self.query.add(Q(nombre_servicio__icontains=q1), Q.OR)
            self.query.add(Q(descripcion__icontains=q1), Q.OR)
        
        return (self.model.objects.filter(self.query)
                .filter(activo=True)
                .order_by('nombre_servicio'))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['create_url'] = reverse_lazy('doctor:servicios_create')
        return context


class ServiciosAdicionalesCreateView(PermissionMixin, CreateViewMixin, CreateView):
    model = ServiciosAdicionales
    form_class = ServiciosAdicionalesForm
    template_name = 'doctor/servicios_adicionales/form.html'
    success_url = reverse_lazy('doctor:servicios_list')
    permission_required = 'doctor.add_serviciosadicionales'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['grabar'] = 'Grabar Servicio Adicional'
        context['back_url'] = self.success_url
        return context

    def form_valid(self, form):
        form.instance.activo = True
        return super().form_valid(form)


class ServiciosAdicionalesUpdateView(PermissionMixin, UpdateViewMixin, UpdateView):
    model = ServiciosAdicionales
    form_class = ServiciosAdicionalesForm
    template_name = 'doctor/servicios_adicionales/form.html'
    success_url = reverse_lazy('doctor:servicios_list')
    permission_required = 'doctor.change_serviciosadicionales'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['grabar'] = 'Actualizar Servicio Adicional'
        context['back_url'] = self.success_url
        return context


class ServiciosAdicionalesDeleteView(PermissionMixin, DeleteViewMixin, DeleteView):
    model = ServiciosAdicionales
    template_name = 'core/delete.html'
    success_url = reverse_lazy('doctor:servicios_list')
    permission_required = 'doctor.delete_serviciosadicionales'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Eliminar Servicio Adicional'
        context['cancel_url'] = self.success_url
        context['entity_name'] = 'servicio adicional'
        
        # Verificar dependencias antes de mostrar el formulario
        dependencias = []
        
        # Verificar si hay detalles de pago usando este servicio
        detalles_pago_count = self.object.detalles_pago.count()
        if detalles_pago_count > 0:
            dependencias.append(f"{detalles_pago_count} detalle{'s' if detalles_pago_count != 1 else ''} de pago")
        
        if dependencias:
            context['has_dependencies'] = True
            context['dependencies'] = dependencias
            context['dependencies_message'] = f"No se puede eliminar el servicio '{self.object.nombre_servicio}' porque está siendo utilizado por:"
            context['next_steps'] = [
                "Revisar los pagos que incluyen este servicio",
                "Reasignar los detalles de pago a otro servicio",
                "Contactar al administrador del sistema para más opciones"
            ]
        else:
            context['has_dependencies'] = False
            servicio = self.object
            context['question'] = f'¿Está seguro de eliminar el servicio "{servicio.nombre_servicio}"?'
            context['warning'] = 'Esta acción eliminará permanentemente el servicio adicional del sistema.'
            context['details'] = [
                f"Nombre: {servicio.nombre_servicio}",
                f"Costo: ${servicio.costo_servicio}",
                f"Estado: {'Activo' if servicio.activo else 'Inactivo'}",
                f"Descripción: {servicio.descripcion[:100] + '...' if servicio.descripcion and len(servicio.descripcion) > 100 else servicio.descripcion or 'Sin descripción'}"
            ]
        
        return context

    def delete(self, request, *args, **kwargs):
        """Override delete to handle protected foreign key relationships"""
        try:
            # Verificar dependencias antes de eliminar
            detalles_pago_count = self.object.detalles_pago.count()
            if detalles_pago_count > 0:
                messages.error(
                    request,
                    f"No se puede eliminar el servicio '{self.object.nombre_servicio}' porque está siendo utilizado por {detalles_pago_count} detalle{'s' if detalles_pago_count != 1 else ''} de pago."
                )
                return redirect(self.success_url)
            
            # Si no hay dependencias, proceder con la eliminación
            servicio_nombre = self.object.nombre_servicio
            response = super().delete(request, *args, **kwargs)
            messages.success(request, f"El servicio '{servicio_nombre}' ha sido eliminado exitosamente.")
            return response
            
        except ProtectedError as e:
            # Si Django detecta relaciones protegidas que no capturamos
            messages.error(
                request,
                f"No se puede eliminar el servicio '{self.object.nombre_servicio}' porque está siendo utilizado por otros elementos del sistema."
            )
            return redirect(self.success_url)
        except Exception as e:
            # Capturar cualquier otro error
            messages.error(
                request,
                f"Error al intentar eliminar el servicio: {str(e)}"
            )
            return redirect(self.success_url)
