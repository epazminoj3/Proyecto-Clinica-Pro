from django.http import JsonResponse
from django.views.generic import View
from django.shortcuts import render
from django.urls import reverse_lazy
from django.contrib import messages

from applications.security.components.mixin_crud import PermissionMixin, CreateViewMixin
from applications.core.models import Medicamento, TipoMedicamento, MarcaMedicamento
from applications.core.utils.medicamento import ViaAdministracion


class MedicamentoCreateApiView(PermissionMixin, CreateViewMixin, View):
    """Vista para crear medicamentos vía AJAX desde el formulario de atención médica"""
    model = Medicamento
    permission_required = 'core.add_medicamento'
    
    def get(self, request, *args, **kwargs):
        """Renderiza el formulario de creación de medicamento"""
        context = self.get_context_data()
        context.update({
            'tipos_medicamento': TipoMedicamento.objects.filter(activo=True),
            'marcas_medicamento': MarcaMedicamento.objects.filter(activo=True),
            'vias_administracion': ViaAdministracion.choices,
        })
        return render(request, 'fragments/modal_medicamento.html', context)

    def post(self, request, *args, **kwargs):
        """Crea un nuevo medicamento vía AJAX"""
        try:
            # Validar datos requeridos
            required_fields = ['nombre', 'tipo', 'via_administracion', 'cantidad', 'precio']
            for field in required_fields:
                if not request.POST.get(field):
                    return JsonResponse({
                        'success': False,
                        'error': f'El campo {field} es requerido'
                    }, status=400)

            # Obtener datos del formulario
            nombre = request.POST.get('nombre').strip()
            tipo_id = request.POST.get('tipo')
            marca_id = request.POST.get('marca') or None
            descripcion = request.POST.get('descripcion', '').strip()
            concentracion = request.POST.get('concentracion', '').strip()
            via_administracion = request.POST.get('via_administracion')
            cantidad = int(request.POST.get('cantidad'))
            precio = float(request.POST.get('precio'))
            comercial = request.POST.get('comercial') == 'on'

            # Validar que no exista un medicamento con el mismo nombre
            if Medicamento.objects.filter(nombre=nombre, activo=True).exists():
                return JsonResponse({
                    'success': False,
                    'error': 'Ya existe un medicamento con ese nombre'
                }, status=400)

            # Obtener tipo de medicamento
            try:
                tipo_medicamento = TipoMedicamento.objects.get(id=tipo_id, activo=True)
            except TipoMedicamento.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'error': 'Tipo de medicamento no válido'
                }, status=400)

            # Obtener marca de medicamento (opcional)
            marca_medicamento = None
            if marca_id:
                try:
                    marca_medicamento = MarcaMedicamento.objects.get(id=marca_id, activo=True)
                except MarcaMedicamento.DoesNotExist:
                    return JsonResponse({
                        'success': False,
                        'error': 'Marca de medicamento no válida'
                    }, status=400)

            # Crear el medicamento
            medicamento = Medicamento.objects.create(
                nombre=nombre,
                tipo=tipo_medicamento,
                marca_medicamento=marca_medicamento,
                descripcion=descripcion,
                concentracion=concentracion,
                via_administracion=via_administracion,
                cantidad=cantidad,
                precio=precio,
                comercial=comercial,
                activo=True
            )

            # Preparar datos para la respuesta
            medicamento_data = {
                'id': medicamento.id,
                'nombre': medicamento.nombre,
                'tipo': medicamento.tipo.nombre,
                'marca': medicamento.marca_medicamento.nombre if medicamento.marca_medicamento else 'Sin marca',
                'concentracion': medicamento.concentracion or '',
                'via_administracion': medicamento.get_via_administracion_display(),
                'cantidad': medicamento.cantidad,
                'precio': float(medicamento.precio),
                'comercial': medicamento.comercial,
                'descripcion': medicamento.descripcion or '',
                'display_name': f"{medicamento.nombre} {medicamento.concentracion or ''} - {medicamento.tipo.nombre} ({medicamento.marca_medicamento.nombre if medicamento.marca_medicamento else 'Sin marca'}) - ${medicamento.precio} - Stock: {medicamento.cantidad}"
            }

            return JsonResponse({
                'success': True,
                'message': 'Medicamento creado exitosamente',
                'medicamento': medicamento_data
            })

        except ValueError as e:
            return JsonResponse({
                'success': False,
                'error': 'Error en los datos numéricos proporcionados'
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f'Error interno del servidor: {str(e)}'
            }, status=500)

    def get_context_data(self, **kwargs):
        """Agregar contexto adicional"""
        context = super().get_context_data(**kwargs)
        context['title'] = 'Crear Nuevo Medicamento'
        context['action'] = 'create'
        return context
