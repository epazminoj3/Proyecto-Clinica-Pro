from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.contrib import messages
from django.http import JsonResponse
from django.forms import modelformset_factory
from django.db import transaction
from django.db.models import ProtectedError, Q
from applications.doctor.models import Pago, DetallePago
from applications.doctor.forms import PagoForm, DetallePagoForm
from applications.security.components.mixin_crud import ListViewMixin, CreateViewMixin, UpdateViewMixin, DeleteViewMixin, PermissionMixin


# ==================== VISTAS DE PAGO ====================
class PagoListView(PermissionMixin, ListViewMixin, ListView):
    model = Pago
    template_name = 'doctor/pago/list.html'
    context_object_name = 'pagos'
    paginate_by = 10
    permission_required = 'doctor.view_pago'

    def get_queryset(self):
        queryset = Pago.objects.filter(activo=True).select_related('atencion__paciente').order_by('-fecha_creacion')
        
        # Filtros
        atencion = self.request.GET.get('atencion')
        if atencion:
            queryset = queryset.filter(
                Q(atencion__id__icontains=atencion) |
                Q(atencion__paciente__nombres__icontains=atencion) |
                Q(atencion__paciente__apellidos__icontains=atencion)
            )
        
        metodo_pago = self.request.GET.get('metodo_pago')
        if metodo_pago:
            queryset = queryset.filter(metodo_pago=metodo_pago)
        
        estado = self.request.GET.get('estado')
        if estado:
            queryset = queryset.filter(estado=estado)
        
        return queryset


class PagoCreateView(PermissionMixin, CreateViewMixin, CreateView):
    model = Pago
    form_class = PagoForm
    template_name = 'doctor/pago/form.html'
    success_url = reverse_lazy('doctor:pago_list')
    permission_required = 'doctor.add_pago'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

    @transaction.atomic
    def form_valid(self, form):
        # Guardar el pago
        form.instance.activo = True
        response = super().form_valid(form)
        
        # Aquí se pueden procesar los detalles de pago si se envían
        # Por ahora, el procesamiento de detalles se maneja con JavaScript
        
        return response


class PagoUpdateView(PermissionMixin, UpdateViewMixin, UpdateView):
    model = Pago
    form_class = PagoForm
    template_name = 'doctor/pago/form.html'
    success_url = reverse_lazy('doctor:pago_list')
    permission_required = 'doctor.change_pago'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

    @transaction.atomic
    def form_valid(self, form):
        # Guardar el pago
        response = super().form_valid(form)
        
        # Aquí se pueden procesar los detalles de pago si se envían
        # Por ahora, el procesamiento de detalles se maneja con JavaScript
        
        return response


class PagoDeleteView(PermissionMixin, DeleteViewMixin, DeleteView):
    model = Pago
    template_name = 'core/delete.html'
    success_url = reverse_lazy('doctor:pago_list')
    permission_required = 'doctor.delete_pago'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Eliminar Pago'
        context['cancel_url'] = self.success_url
        context['entity_name'] = 'pago'
        
        # Verificar dependencias antes de mostrar el formulario
        dependencias = []
        
        # Verificar si hay detalles de pago asociados
        detalles_count = self.object.detalles.count()
        if detalles_count > 0:
            dependencias.append(f"{detalles_count} detalle{'s' if detalles_count != 1 else ''} de pago")
        
        if dependencias:
            context['has_dependencies'] = True
            context['dependencies'] = dependencias
            context['dependencies_message'] = f"No se puede eliminar el pago #{self.object.id} porque tiene:"
            context['next_steps'] = [
                "Eliminar primero todos los detalles de pago asociados",
                "Contactar al administrador del sistema para más opciones"
            ]
        else:
            context['has_dependencies'] = False
            pago = self.object
            fecha_formateada = pago.fecha_creacion.strftime('%d/%m/%Y')
            context['question'] = f'¿Está seguro de eliminar el pago #{pago.id} por ${pago.monto_total} del {fecha_formateada}?'
            context['warning'] = 'Esta acción eliminará permanentemente el registro de pago del sistema.'
            context['details'] = [
                f"ID del pago: #{pago.id}",
                f"Monto total: ${pago.monto_total}",
                f"Fecha de creación: {fecha_formateada}",
                f"Estado: {'Activo' if pago.activo else 'Inactivo'}",
                f"Método de pago: {pago.get_metodo_pago_display()}" if hasattr(pago, 'metodo_pago') else None
            ]
            # Filtrar valores None
            context['details'] = [detail for detail in context['details'] if detail is not None]
        
        return context

    def delete(self, request, *args, **kwargs):
        """Override delete to handle protected foreign key relationships"""
        try:
            # Verificar dependencias antes de eliminar
            detalles_count = self.object.detalles.count()
            if detalles_count > 0:
                messages.error(
                    request,
                    f"No se puede eliminar el pago #{self.object.id} porque tiene {detalles_count} detalle{'s' if detalles_count != 1 else ''} de pago asociado{'s' if detalles_count != 1 else ''}."
                )
                return redirect(self.success_url)
            
            # Si no hay dependencias, proceder con la eliminación
            pago_id = self.object.id
            monto_total = self.object.monto_total
            response = super().delete(request, *args, **kwargs)
            messages.success(request, f"El pago #{pago_id} por ${monto_total} ha sido eliminado exitosamente.")
            return response
            
        except ProtectedError as e:
            # Si Django detecta relaciones protegidas que no capturamos
            messages.error(
                request,
                f"No se puede eliminar el pago #{self.object.id} porque está siendo utilizado por otros elementos del sistema."
            )
            return redirect(self.success_url)
        except Exception as e:
            # Capturar cualquier otro error
            messages.error(
                request,
                f"Error al intentar eliminar el pago: {str(e)}"
            )
            return redirect(self.success_url)


# ==================== VISTAS DE DETALLE PAGO ====================
class DetallePagoListView(PermissionMixin, ListViewMixin, ListView):
    model = DetallePago
    template_name = 'doctor/detalle_pago/list.html'
    context_object_name = 'detalles'
    paginate_by = 10
    permission_required = 'doctor.view_detallepago'

    def get_queryset(self):
        return DetallePago.objects.all().order_by('-pago__fecha_creacion')


class DetallePagoCreateView(PermissionMixin, CreateViewMixin, CreateView):
    model = DetallePago
    form_class = DetallePagoForm
    template_name = 'doctor/detalle_pago/form.html'
    success_url = reverse_lazy('doctor:detalle_pago_list')
    permission_required = 'doctor.add_detallepago'


class DetallePagoUpdateView(PermissionMixin, UpdateViewMixin, UpdateView):
    model = DetallePago
    form_class = DetallePagoForm
    template_name = 'doctor/detalle_pago/form.html'
    success_url = reverse_lazy('doctor:detalle_pago_list')
    permission_required = 'doctor.change_detallepago'


class DetallePagoDeleteView(PermissionMixin, DeleteViewMixin, DeleteView):
    model = DetallePago
    template_name = 'core/delete.html'
    success_url = reverse_lazy('doctor:detalle_pago_list')
    permission_required = 'doctor.delete_detallepago'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Eliminar Detalle de Pago'
        context['cancel_url'] = self.success_url
        context['entity_name'] = 'detalle de pago'
        
        # Los detalles de pago normalmente no tienen dependencias bloqueantes
        # Son registros específicos de servicios dentro de un pago
        dependencias = []
        
        # No hay dependencias bloqueantes típicas para detalles de pago
        
        if dependencias:
            context['has_dependencies'] = True
            context['dependencies'] = dependencias
            context['dependencies_message'] = f"No se puede eliminar este detalle de pago porque:"
            context['next_steps'] = [
                "Contactar al administrador del sistema para más opciones"
            ]
        else:
            context['has_dependencies'] = False
            detalle = self.object
            fecha_pago = detalle.pago.fecha_creacion.strftime('%d/%m/%Y')
            context['question'] = f'¿Está seguro de eliminar el detalle "{detalle.servicio_adicional.nombre}" del pago #{detalle.pago.id}?'
            context['warning'] = 'Esta acción eliminará permanentemente este servicio del registro de pago.'
            context['details'] = [
                f"Pago ID: #{detalle.pago.id}",
                f"Servicio: {detalle.servicio_adicional.nombre}",
                f"Cantidad: {detalle.cantidad}",
                f"Precio unitario: ${detalle.precio_unitario}",
                f"Subtotal: ${detalle.subtotal}",
                f"Fecha del pago: {fecha_pago}"
            ]
        
        return context

    def delete(self, request, *args, **kwargs):
        """Override delete to handle any potential errors and provide user feedback"""
        try:
            detalle = self.object
            servicio_nombre = detalle.servicio_adicional.nombre
            pago_id = detalle.pago.id
            
            # Proceder con la eliminación
            response = super().delete(request, *args, **kwargs)
            messages.success(
                request,
                f"El detalle '{servicio_nombre}' del pago #{pago_id} ha sido eliminado exitosamente."
            )
            return response
            
        except ProtectedError as e:
            # Si Django detecta relaciones protegidas
            messages.error(
                request,
                f"No se puede eliminar este detalle de pago porque está siendo utilizado por otros elementos del sistema."
            )
            return redirect(self.success_url)
        except Exception as e:
            # Capturar cualquier otro error
            messages.error(
                request,
                f"Error al intentar eliminar el detalle de pago: {str(e)}"
            )
            return redirect(self.success_url)
